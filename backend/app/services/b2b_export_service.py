"""
B2B Export Service for Revenue Optimization
Handles lead export to multiple B2B platforms with quality-based routing
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadExport
from app.models.b2b_platforms import B2BPlatform, B2BLeadMapping, B2BRevenueTransaction
from app.models.analytics import PlatformPerformance
from app.core.config import settings


class ExportPriority(Enum):
    """Export priority levels"""
    IMMEDIATE = "immediate"  # Premium leads
    HIGH = "high"           # Standard leads
    MEDIUM = "medium"       # Basic leads
    LOW = "low"            # Nurture leads


@dataclass
class ExportStrategy:
    """B2B export strategy configuration"""
    platform: str
    priority: ExportPriority
    min_lead_score: int
    max_lead_score: int
    price_tier: str
    exclusivity: bool = False
    max_daily_exports: int = 50
    revenue_share: float = 0.15


class B2BExportService:
    """Service for B2B lead export and revenue optimization"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Export strategies for different quality tiers
        self.export_strategies = {
            "premium": [
                ExportStrategy("solarreviews", ExportPriority.IMMEDIATE, 85, 100, "premium", True, 20, 0.18),
                ExportStrategy("modernize", ExportPriority.IMMEDIATE, 85, 100, "premium", False, 30, 0.15),
                ExportStrategy("energysage", ExportPriority.HIGH, 80, 100, "premium", False, 25, 0.20)
            ],
            "standard": [
                ExportStrategy("solarreviews", ExportPriority.HIGH, 70, 84, "standard", False, 40, 0.15),
                ExportStrategy("modernize", ExportPriority.HIGH, 70, 84, "standard", False, 50, 0.12),
                ExportStrategy("solarpowerworld", ExportPriority.MEDIUM, 65, 84, "standard", False, 30, 0.10)
            ],
            "basic": [
                ExportStrategy("modernize", ExportPriority.MEDIUM, 50, 69, "basic", False, 60, 0.10),
                ExportStrategy("solarpowerworld", ExportPriority.MEDIUM, 50, 69, "basic", False, 40, 0.08),
                ExportStrategy("solarreviews", ExportPriority.LOW, 55, 69, "basic", False, 30, 0.12)
            ]
        }
        
        # Platform performance tracking
        self.platform_performance = {}
    
    async def export_lead(
        self, 
        lead_id: str, 
        quality_tier: str, 
        lead_score: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export lead to appropriate B2B platforms based on quality tier"""
        
        try:
            # Get lead data
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                return {"success": False, "error": "Lead not found"}
            
            # Get export strategies for quality tier
            strategies = self.export_strategies.get(quality_tier, [])
            if not strategies:
                return {"success": False, "error": f"No export strategies for tier: {quality_tier}"}
            
            # Filter strategies based on lead score
            eligible_strategies = [
                s for s in strategies 
                if s.min_lead_score <= lead_score <= s.max_lead_score
            ]
            
            if not eligible_strategies:
                return {"success": False, "error": "No eligible export strategies"}
            
            # Select best strategy based on revenue optimization
            selected_strategy = await self._select_optimal_strategy(eligible_strategies, lead_score, context)
            
            # Export to selected platform
            export_result = await self._export_to_platform(lead, selected_strategy, context)
            
            # Update lead status
            if export_result["success"]:
                lead.export_status = "exported"
                lead.exported_at = datetime.utcnow()
                if not lead.exported_to_platforms:
                    lead.exported_to_platforms = []
                lead.exported_to_platforms.append(selected_strategy.platform)
                
                # Update export timestamps
                if not lead.export_timestamps:
                    lead.export_timestamps = {}
                lead.export_timestamps[selected_strategy.platform] = datetime.utcnow().isoformat()
                
                self.db.commit()
            
            return export_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _select_optimal_strategy(
        self, 
        strategies: List[ExportStrategy], 
        lead_score: int,
        context: Dict[str, Any]
    ) -> ExportStrategy:
        """Select optimal export strategy based on revenue and performance"""
        
        # Score each strategy
        strategy_scores = []
        
        for strategy in strategies:
            score = 0
            
            # Base score from lead score
            score += lead_score * 0.4
            
            # Revenue potential
            estimated_value = self._calculate_estimated_value(lead_score, strategy)
            score += estimated_value * 0.3
            
            # Platform performance
            platform_perf = await self._get_platform_performance(strategy.platform)
            score += platform_perf.get("acceptance_rate", 0) * 0.2
            
            # Exclusivity bonus
            if strategy.exclusivity:
                score += 20
            
            # NYC market bonus
            if context.get("nyc_data", {}).get("high_value_zip_code", False):
                score += 15
            
            strategy_scores.append((strategy, score))
        
        # Sort by score and select highest
        strategy_scores.sort(key=lambda x: x[1], reverse=True)
        return strategy_scores[0][0]
    
    def _calculate_estimated_value(self, lead_score: int, strategy: ExportStrategy) -> float:
        """Calculate estimated B2B value for strategy"""
        
        # Base value by price tier
        tier_values = {
            "premium": 250.0,
            "standard": 150.0,
            "basic": 100.0
        }
        
        base_value = tier_values.get(strategy.price_tier, 100.0)
        
        # Adjust based on lead score
        score_multiplier = lead_score / 100.0
        adjusted_value = base_value * score_multiplier
        
        # Apply revenue share
        net_value = adjusted_value * (1 - strategy.revenue_share)
        
        return net_value
    
    async def _get_platform_performance(self, platform: str) -> Dict[str, Any]:
        """Get platform performance metrics"""
        
        # Check cache first
        if platform in self.platform_performance:
            cached_data, timestamp = self.platform_performance[platform]
            if datetime.utcnow() - timestamp < timedelta(minutes=30):
                return cached_data
        
        try:
            # Get platform data
            platform_data = self.db.query(B2BPlatform).filter(
                B2BPlatform.platform_code == platform
            ).first()
            
            if not platform_data:
                return {"acceptance_rate": 0.5, "average_response_time": 5000}
            
            # Get recent performance data
            recent_performance = self.db.query(PlatformPerformance).filter(
                PlatformPerformance.platform_id == platform_data.id,
                PlatformPerformance.date >= datetime.utcnow() - timedelta(days=30)
            ).first()
            
            performance_data = {
                "acceptance_rate": platform_data.acceptance_rate or 0.5,
                "average_response_time": platform_data.average_response_time_ms or 5000,
                "total_exports": platform_data.total_leads_exported or 0,
                "successful_exports": platform_data.successful_exports or 0,
                "failed_exports": platform_data.failed_exports or 0,
                "health_status": platform_data.health_status or "unknown",
                "is_accepting_leads": platform_data.is_accepting_leads or False
            }
            
            # Cache the data
            self.platform_performance[platform] = (performance_data, datetime.utcnow())
            
            return performance_data
            
        except Exception as e:
            print(f"Error getting platform performance for {platform}: {e}")
            return {"acceptance_rate": 0.5, "average_response_time": 5000}
    
    async def _export_to_platform(
        self, 
        lead: Lead, 
        strategy: ExportStrategy, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export lead to specific B2B platform"""
        
        try:
            # Get platform configuration
            platform = self.db.query(B2BPlatform).filter(
                B2BPlatform.platform_code == strategy.platform
            ).first()
            
            if not platform:
                return {"success": False, "error": f"Platform {strategy.platform} not found"}
            
            if not platform.is_accepting_leads:
                return {"success": False, "error": f"Platform {strategy.platform} not accepting leads"}
            
            # Prepare export data
            export_data = await self._prepare_export_data(lead, strategy, context)
            
            # Create export record
            export_record = LeadExport(
                lead_id=lead.id,
                platform_id=platform.id,
                export_status="pending",
                export_priority=strategy.priority.value,
                export_data=export_data,
                export_format="json",
                export_version="v1",
                price_per_lead=strategy.price_tier,
                commission_rate=strategy.revenue_share
            )
            
            self.db.add(export_record)
            self.db.commit()
            
            # Simulate API call to platform (replace with actual API integration)
            api_result = await self._call_platform_api(platform, export_data)
            
            # Update export record with result
            if api_result["success"]:
                export_record.export_status = "success"
                export_record.platform_lead_id = api_result.get("platform_lead_id")
                export_record.response_data = api_result.get("response_data", {})
                export_record.exported_at = datetime.utcnow()
                export_record.commission_earned = self._calculate_commission(lead, strategy)
            else:
                export_record.export_status = "failed"
                export_record.error_message = api_result.get("error", "Unknown error")
                export_record.retry_count = 1
            
            self.db.commit()
            
            # Update platform performance metrics
            await self._update_platform_performance(platform.id, api_result["success"])
            
            return {
                "success": api_result["success"],
                "platform": strategy.platform,
                "export_id": str(export_record.id),
                "platform_lead_id": api_result.get("platform_lead_id"),
                "commission_earned": export_record.commission_earned,
                "estimated_value": self._calculate_estimated_value(lead.lead_score, strategy)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _prepare_export_data(
        self, 
        lead: Lead, 
        strategy: ExportStrategy, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare lead data for B2B platform export"""
        
        # Base lead data
        export_data = {
            "contact": {
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "phone": lead.phone
            },
            "property": {
                "address": lead.property_address,
                "city": lead.city,
                "state": lead.state,
                "zip_code": lead.zip_code,
                "borough": lead.borough,
                "property_type": lead.property_type,
                "square_footage": lead.square_footage
            },
            "solar_details": {
                "roof_type": lead.roof_type,
                "roof_condition": lead.roof_condition,
                "monthly_electric_bill": lead.monthly_electric_bill,
                "electric_provider": lead.electric_provider
            },
            "qualification": {
                "lead_score": lead.lead_score,
                "lead_quality": lead.lead_quality,
                "qualification_status": lead.qualification_status,
                "estimated_value": lead.estimated_value
            },
            "nyc_market": {
                "borough": lead.borough,
                "zip_code": lead.zip_code,
                "nyc_data": context.get("nyc_data", {}),
                "incentives_available": context.get("nyc_data", {}).get("state_incentives_available", True)
            },
            "metadata": {
                "source": lead.source,
                "created_at": lead.created_at.isoformat(),
                "aurum_lead_id": str(lead.id),
                "quality_tier": strategy.price_tier,
                "export_priority": strategy.priority.value
            }
        }
        
        # Add AI insights if available
        if lead.ai_insights:
            try:
                ai_insights = json.loads(lead.ai_insights)
                export_data["ai_insights"] = ai_insights
            except:
                pass
        
        return export_data
    
    async def _call_platform_api(self, platform: B2BPlatform, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call B2B platform API (simulated for now)"""
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Simulate success/failure based on platform health
        if platform.health_status == "healthy" and platform.is_accepting_leads:
            return {
                "success": True,
                "platform_lead_id": f"{platform.platform_code}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "response_data": {
                    "status": "accepted",
                    "estimated_value": export_data["qualification"]["estimated_value"],
                    "processing_time_ms": 150
                }
            }
        else:
            return {
                "success": False,
                "error": f"Platform {platform.platform_code} not accepting leads"
            }
    
    def _calculate_commission(self, lead: Lead, strategy: ExportStrategy) -> float:
        """Calculate commission earned from export"""
        
        estimated_value = lead.estimated_value or 0
        commission = estimated_value * strategy.revenue_share
        return commission
    
    async def _update_platform_performance(self, platform_id: str, success: bool):
        """Update platform performance metrics"""
        
        try:
            platform = self.db.query(B2BPlatform).filter(B2BPlatform.id == platform_id).first()
            if not platform:
                return
            
            # Update counters
            platform.total_leads_exported += 1
            if success:
                platform.successful_exports += 1
            else:
                platform.failed_exports += 1
            
            # Update acceptance rate
            if platform.total_leads_exported > 0:
                platform.acceptance_rate = platform.successful_exports / platform.total_leads_exported
            
            # Update health status
            if platform.acceptance_rate < 0.5:
                platform.health_status = "degraded"
            elif platform.acceptance_rate < 0.3:
                platform.health_status = "down"
            else:
                platform.health_status = "healthy"
            
            platform.last_export_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            print(f"Error updating platform performance: {e}")
            self.db.rollback()
    
    async def get_export_recommendations(
        self, 
        lead_score: int, 
        quality_tier: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get B2B export recommendations for a lead"""
        
        recommendations = []
        
        # Get strategies for quality tier
        strategies = self.export_strategies.get(quality_tier, [])
        
        for strategy in strategies:
            if strategy.min_lead_score <= lead_score <= strategy.max_lead_score:
                platform_perf = await self._get_platform_performance(strategy.platform)
                
                recommendation = {
                    "platform": strategy.platform,
                    "priority": strategy.priority.value,
                    "price_tier": strategy.price_tier,
                    "estimated_value": self._calculate_estimated_value(lead_score, strategy),
                    "commission_rate": strategy.revenue_share,
                    "acceptance_rate": platform_perf.get("acceptance_rate", 0.5),
                    "health_status": platform_perf.get("health_status", "unknown"),
                    "is_accepting": platform_perf.get("is_accepting_leads", False),
                    "exclusivity": strategy.exclusivity,
                    "max_daily_exports": strategy.max_daily_exports
                }
                
                recommendations.append(recommendation)
        
        # Sort by estimated value
        recommendations.sort(key=lambda x: x["estimated_value"], reverse=True)
        
        return recommendations
    
    async def get_revenue_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue analytics for B2B exports"""
        
        try:
            # Get export data for period
            start_date = datetime.utcnow() - timedelta(days=days)
            
            exports = self.db.query(LeadExport).filter(
                LeadExport.created_at >= start_date
            ).all()
            
            # Calculate metrics
            total_exports = len(exports)
            successful_exports = len([e for e in exports if e.export_status == "success"])
            failed_exports = len([e for e in exports if e.export_status == "failed"])
            
            total_revenue = sum([e.commission_earned or 0 for e in exports])
            average_commission = total_revenue / total_exports if total_exports > 0 else 0
            
            # Platform breakdown
            platform_breakdown = {}
            for export in exports:
                platform = export.platform.platform_code
                if platform not in platform_breakdown:
                    platform_breakdown[platform] = {
                        "total_exports": 0,
                        "successful_exports": 0,
                        "revenue": 0
                    }
                
                platform_breakdown[platform]["total_exports"] += 1
                if export.export_status == "success":
                    platform_breakdown[platform]["successful_exports"] += 1
                platform_breakdown[platform]["revenue"] += export.commission_earned or 0
            
            return {
                "period_days": days,
                "total_exports": total_exports,
                "successful_exports": successful_exports,
                "failed_exports": failed_exports,
                "success_rate": successful_exports / total_exports if total_exports > 0 else 0,
                "total_revenue": total_revenue,
                "average_commission": average_commission,
                "platform_breakdown": platform_breakdown
            }
            
        except Exception as e:
            print(f"Error getting revenue analytics: {e}")
            return {}
    
    async def optimize_export_strategies(self) -> Dict[str, Any]:
        """Optimize export strategies based on performance data"""
        
        try:
            # Get performance data for last 30 days
            start_date = datetime.utcnow() - timedelta(days=30)
            
            # Analyze platform performance
            platform_analysis = {}
            
            for strategy in self.export_strategies["premium"] + self.export_strategies["standard"] + self.export_strategies["basic"]:
                platform_perf = await self._get_platform_performance(strategy.platform)
                
                platform_analysis[strategy.platform] = {
                    "acceptance_rate": platform_perf.get("acceptance_rate", 0.5),
                    "total_exports": platform_perf.get("total_exports", 0),
                    "health_status": platform_perf.get("health_status", "unknown"),
                    "is_accepting": platform_perf.get("is_accepting_leads", False)
                }
            
            # Generate optimization recommendations
            recommendations = []
            
            for platform, perf in platform_analysis.items():
                if perf["acceptance_rate"] < 0.3:
                    recommendations.append({
                        "platform": platform,
                        "issue": "Low acceptance rate",
                        "recommendation": "Consider reducing export volume or improving lead quality"
                    })
                elif perf["acceptance_rate"] > 0.8:
                    recommendations.append({
                        "platform": platform,
                        "issue": "High acceptance rate",
                        "recommendation": "Consider increasing export volume or expanding to lower quality tiers"
                    })
                
                if not perf["is_accepting"]:
                    recommendations.append({
                        "platform": platform,
                        "issue": "Not accepting leads",
                        "recommendation": "Temporarily disable exports until platform is restored"
                    })
            
            return {
                "platform_analysis": platform_analysis,
                "recommendations": recommendations,
                "optimization_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error optimizing export strategies: {e}")
            return {}
