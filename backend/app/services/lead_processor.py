"""
Lead Processing Pipeline
Handles lead qualification, scoring, and B2B routing with high performance
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lead import Lead, LeadConversation, LeadQualityHistory
from app.models.b2b_platforms import B2BPlatform, B2BLeadMapping, B2BRevenueTransaction
from app.services.lead_scoring_service import LeadScoringService
from app.services.b2b_export_service import B2BExportService
from app.services.nyc_market_service import NYCMarketService
from app.services.analytics_service import AnalyticsService
from app.core.redis import get_redis

logger = structlog.get_logger()

class LeadStatus(Enum):
    """Lead processing status"""
    NEW = "new"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    EXPORTED = "exported"
    CONVERTED = "converted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class QualityTier(Enum):
    """Lead quality tiers"""
    PREMIUM = "premium"  # $200+ B2B value
    STANDARD = "standard"  # $125 B2B value
    BASIC = "basic"  # $75 B2B value
    UNQUALIFIED = "unqualified"  # No B2B value

@dataclass
class LeadProcessingResult:
    """Result of lead processing"""
    lead_id: str
    status: LeadStatus
    quality_tier: QualityTier
    lead_score: int
    b2b_value: float
    export_recommendations: List[Dict[str, Any]]
    processing_time_ms: int
    errors: List[str]

class LeadProcessor:
    """High-performance lead processing pipeline"""
    
    def __init__(self):
        self.scoring_service = None
        self.b2b_export = None
        self.nyc_service = None
        self.analytics = None
        self.redis = None
        
        # Processing metrics
        self.processed_count = 0
        self.qualified_count = 0
        self.exported_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize services"""
        if not self.scoring_service:
            db = next(get_db())
            self.scoring_service = LeadScoringService(db)
            self.b2b_export = B2BExportService(db)
            self.nyc_service = NYCMarketService(db)
            self.analytics = AnalyticsService(db)
            self.redis = await get_redis()
    
    async def process_lead(
        self, 
        lead_id: str, 
        conversation_data: Dict[str, Any],
        force_reprocess: bool = False
    ) -> LeadProcessingResult:
        """Process a lead through the qualification pipeline"""
        
        start_time = datetime.utcnow()
        errors = []
        
        try:
            await self.initialize()
            
            # Get lead from database
            db = next(get_db())
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Check if already processed (unless force reprocess)
            if not force_reprocess and lead.status in ["qualified", "exported", "converted"]:
                return LeadProcessingResult(
                    lead_id=lead_id,
                    status=LeadStatus(lead.status),
                    quality_tier=QualityTier(lead.lead_quality),
                    lead_score=lead.lead_score,
                    b2b_value=lead.estimated_value or 0,
                    export_recommendations=[],
                    processing_time_ms=0,
                    errors=[]
                )
            
            # Step 1: Calculate lead score
            lead_score = await self._calculate_lead_score(lead, conversation_data)
            
            # Step 2: Determine quality tier
            quality_tier = self._determine_quality_tier(lead_score)
            
            # Step 3: Calculate B2B value
            b2b_value = await self._calculate_b2b_value(lead, lead_score, quality_tier)
            
            # Step 4: Update lead record
            await self._update_lead_record(lead, lead_score, quality_tier, b2b_value)
            
            # Step 5: Get B2B export recommendations
            export_recommendations = await self._get_export_recommendations(
                lead, lead_score, quality_tier
            )
            
            # Step 6: Determine processing status
            status = self._determine_processing_status(lead_score, quality_tier)
            
            # Step 7: Auto-export if qualified
            if status == LeadStatus.QUALIFIED and quality_tier != QualityTier.UNQUALIFIED:
                await self._auto_export_lead(lead, export_recommendations)
                status = LeadStatus.EXPORTED
            
            # Step 8: Update metrics
            await self._update_processing_metrics(status, quality_tier)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = LeadProcessingResult(
                lead_id=lead_id,
                status=status,
                quality_tier=quality_tier,
                lead_score=lead_score,
                b2b_value=b2b_value,
                export_recommendations=export_recommendations,
                processing_time_ms=int(processing_time),
                errors=errors
            )
            
            # Cache result
            await self._cache_processing_result(lead_id, result)
            
            logger.info(
                "Lead processed successfully",
                lead_id=lead_id,
                status=status.value,
                quality_tier=quality_tier.value,
                lead_score=lead_score,
                b2b_value=b2b_value,
                processing_time_ms=processing_time
            )
            
            return result
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"Error processing lead {lead_id}: {str(e)}"
            errors.append(error_msg)
            logger.error("Lead processing error", lead_id=lead_id, error=str(e))
            
            return LeadProcessingResult(
                lead_id=lead_id,
                status=LeadStatus.REJECTED,
                quality_tier=QualityTier.UNQUALIFIED,
                lead_score=0,
                b2b_value=0,
                export_recommendations=[],
                processing_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                errors=errors
            )
    
    async def _calculate_lead_score(self, lead: Lead, conversation_data: Dict[str, Any]) -> int:
        """Calculate comprehensive lead score"""
        try:
            # Create scoring context
            context = type('Context', (), {
                'lead_id': str(lead.id),
                'bill_amount': lead.monthly_electric_bill,
                'homeowner_verified': lead.property_type == 'single_family' or lead.property_type == 'condo',
                'zip_code': lead.zip_code,
                'timeline': conversation_data.get('timeline'),
                'urgency_created': conversation_data.get('urgency_created', False),
                'conversation_count': conversation_data.get('message_count', 0),
                'qualification_factors': conversation_data.get('qualification_factors', {}),
                'objections_handled': conversation_data.get('objections_handled', []),
                'nyc_data': conversation_data.get('nyc_data', {}),
                'conversation_data': conversation_data
            })()
            
            # Calculate score using scoring service
            score = await self.scoring_service.calculate_lead_score(context)
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error("Error calculating lead score", lead_id=lead.id, error=str(e))
            return 0
    
    def _determine_quality_tier(self, lead_score: int) -> QualityTier:
        """Determine quality tier based on lead score"""
        if lead_score >= 85:
            return QualityTier.PREMIUM
        elif lead_score >= 70:
            return QualityTier.STANDARD
        elif lead_score >= 50:
            return QualityTier.BASIC
        else:
            return QualityTier.UNQUALIFIED
    
    async def _calculate_b2b_value(self, lead: Lead, lead_score: int, quality_tier: QualityTier) -> float:
        """Calculate estimated B2B value"""
        try:
            # Base value by quality tier
            tier_values = {
                QualityTier.PREMIUM: 250.0,
                QualityTier.STANDARD: 150.0,
                QualityTier.BASIC: 100.0,
                QualityTier.UNQUALIFIED: 0.0
            }
            
            base_value = tier_values.get(quality_tier, 0.0)
            
            # Adjust based on lead score
            score_multiplier = lead_score / 100.0
            adjusted_value = base_value * score_multiplier
            
            # NYC market adjustments
            if lead.zip_code:
                nyc_data = await self.nyc_service.get_zip_code_data(lead.zip_code)
                if nyc_data:
                    if nyc_data.get("high_value_zip_code", False):
                        adjusted_value *= 1.2
                    if nyc_data.get("solar_adoption_rate", 0) > 0.15:
                        adjusted_value *= 1.1
            
            # Bill amount adjustment
            if lead.monthly_electric_bill and lead.monthly_electric_bill > 300:
                adjusted_value *= 1.15
            
            return round(adjusted_value, 2)
            
        except Exception as e:
            logger.error("Error calculating B2B value", lead_id=lead.id, error=str(e))
            return 0.0
    
    async def _update_lead_record(
        self, 
        lead: Lead, 
        lead_score: int, 
        quality_tier: QualityTier, 
        b2b_value: float
    ):
        """Update lead record with processing results"""
        try:
            db = next(get_db())
            
            # Update lead fields
            lead.lead_score = lead_score
            lead.lead_quality = quality_tier.value
            lead.estimated_value = b2b_value
            lead.updated_at = datetime.utcnow()
            
            # Update status based on quality
            if quality_tier != QualityTier.UNQUALIFIED:
                lead.status = "qualified"
                lead.qualification_status = "qualified"
                lead.qualification_reason = f"Lead scored {lead_score} - {quality_tier.value} tier"
                lead.qualified_at = datetime.utcnow()
            else:
                lead.status = "unqualified"
                lead.qualification_status = "unqualified"
                lead.qualification_reason = f"Lead scored {lead_score} - below qualification threshold"
            
            # Create quality history record
            quality_history = LeadQualityHistory(
                lead_id=lead.id,
                previous_score=lead.lead_score,
                new_score=lead_score,
                previous_quality=lead.lead_quality,
                new_quality=quality_tier.value,
                score_change=lead_score - (lead.lead_score or 0),
                quality_change_reason="Lead processing pipeline",
                factors_considered={
                    "bill_amount": lead.monthly_electric_bill,
                    "homeowner_status": lead.property_type,
                    "zip_code": lead.zip_code,
                    "timeline": "unknown"
                },
                ai_model_version="lead_processor_v1",
                confidence_score=0.85
            )
            
            db.add(quality_history)
            db.commit()
            
        except Exception as e:
            logger.error("Error updating lead record", lead_id=lead.id, error=str(e))
            db.rollback()
            raise
    
    async def _get_export_recommendations(
        self, 
        lead: Lead, 
        lead_score: int, 
        quality_tier: QualityTier
    ) -> List[Dict[str, Any]]:
        """Get B2B export recommendations"""
        try:
            if quality_tier == QualityTier.UNQUALIFIED:
                return []
            
            # Create context for export recommendations
            context = {
                "lead_score": lead_score,
                "quality_tier": quality_tier.value,
                "nyc_data": await self.nyc_service.get_zip_code_data(lead.zip_code) if lead.zip_code else {}
            }
            
            recommendations = await self.b2b_export.get_export_recommendations(
                lead_score, quality_tier.value, context
            )
            
            return recommendations
            
        except Exception as e:
            logger.error("Error getting export recommendations", lead_id=lead.id, error=str(e))
            return []
    
    def _determine_processing_status(self, lead_score: int, quality_tier: QualityTier) -> LeadStatus:
        """Determine processing status based on score and quality"""
        if quality_tier == QualityTier.UNQUALIFIED:
            return LeadStatus.REJECTED
        elif lead_score >= 70:
            return LeadStatus.QUALIFIED
        else:
            return LeadStatus.QUALIFYING
    
    async def _auto_export_lead(self, lead: Lead, export_recommendations: List[Dict[str, Any]]):
        """Automatically export qualified lead to B2B platforms"""
        try:
            if not export_recommendations:
                return
            
            # Select best recommendation
            best_recommendation = max(export_recommendations, key=lambda x: x.get("estimated_value", 0))
            
            # Export to selected platform
            export_result = await self.b2b_export.export_lead(
                str(lead.id),
                lead.lead_quality,
                lead.lead_score,
                {
                    "nyc_data": await self.nyc_service.get_zip_code_data(lead.zip_code) if lead.zip_code else {},
                    "conversation_data": {}
                }
            )
            
            if export_result.get("success"):
                lead.export_status = "exported"
                lead.exported_at = datetime.utcnow()
                lead.exported_to_platforms = [best_recommendation["platform"]]
                
                db = next(get_db())
                db.commit()
                
                self.exported_count += 1
                
                logger.info(
                    "Lead auto-exported successfully",
                    lead_id=lead.id,
                    platform=best_recommendation["platform"],
                    estimated_value=best_recommendation.get("estimated_value", 0)
                )
            
        except Exception as e:
            logger.error("Error auto-exporting lead", lead_id=lead.id, error=str(e))
    
    async def _update_processing_metrics(self, status: LeadStatus, quality_tier: QualityTier):
        """Update processing metrics"""
        self.processed_count += 1
        
        if status in [LeadStatus.QUALIFIED, LeadStatus.EXPORTED]:
            self.qualified_count += 1
        
        # Update Redis metrics
        if self.redis:
            await self.redis.hincrby("lead_processing_metrics", "total_processed", 1)
            await self.redis.hincrby("lead_processing_metrics", f"status_{status.value}", 1)
            await self.redis.hincrby("lead_processing_metrics", f"tier_{quality_tier.value}", 1)
    
    async def _cache_processing_result(self, lead_id: str, result: LeadProcessingResult):
        """Cache processing result for quick access"""
        if self.redis:
            cache_key = f"lead_processing_result:{lead_id}"
            cache_data = {
                "lead_id": result.lead_id,
                "status": result.status.value,
                "quality_tier": result.quality_tier.value,
                "lead_score": result.lead_score,
                "b2b_value": result.b2b_value,
                "processing_time_ms": result.processing_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis.hset(cache_key, mapping=cache_data)
            await self.redis.expire(cache_key, 3600)  # 1 hour TTL
    
    async def get_processing_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        metrics = {
            "processed_count": self.processed_count,
            "qualified_count": self.qualified_count,
            "exported_count": self.exported_count,
            "error_count": self.error_count,
            "uptime_seconds": uptime,
            "processing_rate_per_hour": self.processed_count / (uptime / 3600) if uptime > 0 else 0,
            "qualification_rate": self.qualified_count / self.processed_count if self.processed_count > 0 else 0,
            "export_rate": self.exported_count / self.qualified_count if self.qualified_count > 0 else 0,
            "error_rate": self.error_count / self.processed_count if self.processed_count > 0 else 0
        }
        
        # Add Redis metrics if available
        if self.redis:
            redis_metrics = await self.redis.hgetall("lead_processing_metrics")
            for key, value in redis_metrics.items():
                metrics[f"redis_{key}"] = int(value)
        
        return metrics
    
    async def reprocess_lead(self, lead_id: str) -> LeadProcessingResult:
        """Reprocess a lead with updated data"""
        return await self.process_lead(lead_id, {}, force_reprocess=True)
    
    async def batch_process_leads(self, lead_ids: List[str]) -> List[LeadProcessingResult]:
        """Process multiple leads in parallel"""
        tasks = [self.process_lead(lead_id, {}) for lead_id in lead_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(LeadProcessingResult(
                    lead_id=lead_ids[i],
                    status=LeadStatus.REJECTED,
                    quality_tier=QualityTier.UNQUALIFIED,
                    lead_score=0,
                    b2b_value=0,
                    export_recommendations=[],
                    processing_time_ms=0,
                    errors=[str(result)]
                ))
            else:
                processed_results.append(result)
        
        return processed_results
