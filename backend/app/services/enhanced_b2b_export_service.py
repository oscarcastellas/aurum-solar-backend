"""
Enhanced B2B Lead Export Service
Comprehensive system for formatting qualified leads for maximum B2B value
"""

import asyncio
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.lead import Lead, LeadConversation, LeadQualityHistory
from app.models.ai_models import AICalculation, AICalculationResult
from app.models.nyc_data import NYCZipCode, NYCIncentive
from app.services.nyc_market_service import NYCMarketService
from app.services.solar_calculation_engine import SolarCalculationEngine
from app.services.lead_scoring_service import LeadScoringService
from app.core.config import settings


class QualityTier(Enum):
    """B2B lead quality tiers with pricing"""
    PREMIUM = "premium"    # $200-300 per lead
    STANDARD = "standard"  # $125-175 per lead
    BASIC = "basic"        # $75-125 per lead
    UNQUALIFIED = "unqualified"  # No B2B value


class ExportFormat(Enum):
    """Export format types for different B2B platforms"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    XML = "xml"


@dataclass
class B2BPlatformConfig:
    """Configuration for B2B platform export requirements"""
    platform_name: str
    min_lead_score: int
    max_daily_exports: int
    price_per_lead: float
    required_fields: List[str]
    optional_fields: List[str]
    format_preference: ExportFormat
    exclusivity_required: bool
    quality_tiers_accepted: List[QualityTier]
    contact_method: str  # api, email, webhook
    api_endpoint: Optional[str] = None
    webhook_url: Optional[str] = None
    email_recipient: Optional[str] = None


@dataclass
class EnrichedLeadData:
    """Comprehensive lead data for B2B export"""
    # Basic lead information
    lead_id: str
    quality_tier: QualityTier
    estimated_value: float
    confidence_score: float
    
    # Customer information
    customer: Dict[str, Any]
    
    # Property information
    property: Dict[str, Any]
    
    # Solar profile and calculations
    solar_profile: Dict[str, Any]
    
    # Qualification data
    qualification_data: Dict[str, Any]
    
    # NYC market context
    nyc_market_context: Dict[str, Any]
    
    # Conversation summary
    conversation_summary: Dict[str, Any]
    
    # Export metadata
    export_metadata: Dict[str, Any]


class EnhancedB2BExportService:
    """Enhanced B2B lead export service with comprehensive lead enrichment"""
    
    def __init__(self, db: Session):
        self.db = db
        self.nyc_service = NYCMarketService(db)
        self.solar_calculator = SolarCalculationEngine(db)
        self.lead_scoring = LeadScoringService(db)
        
        # B2B platform configurations
        self.platform_configs = self._initialize_platform_configs()
        
        # Quality tier thresholds
        self.quality_thresholds = {
            QualityTier.PREMIUM: {"min_score": 85, "min_bill": 300, "min_timeline_urgency": 0.8},
            QualityTier.STANDARD: {"min_score": 70, "min_bill": 200, "min_timeline_urgency": 0.6},
            QualityTier.BASIC: {"min_score": 50, "min_bill": 150, "min_timeline_urgency": 0.4},
            QualityTier.UNQUALIFIED: {"min_score": 0, "min_bill": 0, "min_timeline_urgency": 0.0}
        }
    
    def _initialize_platform_configs(self) -> Dict[str, B2BPlatformConfig]:
        """Initialize B2B platform configurations"""
        
        return {
            "solarreviews": B2BPlatformConfig(
                platform_name="SolarReviews",
                min_lead_score=85,
                max_daily_exports=20,
                price_per_lead=250.0,
                required_fields=[
                    "customer.name", "customer.email", "customer.phone", "customer.address",
                    "property.homeowner_status", "property.roof_type", "solar_profile.monthly_bill",
                    "qualification_data.timeline", "qualification_data.credit_indication"
                ],
                optional_fields=[
                    "solar_profile.recommended_system_kw", "solar_profile.estimated_savings_annual",
                    "nyc_market_context.electric_rate", "conversation_summary.engagement_level"
                ],
                format_preference=ExportFormat.JSON,
                exclusivity_required=True,
                quality_tiers_accepted=[QualityTier.PREMIUM],
                contact_method="api",
                api_endpoint="https://api.solarreviews.com/leads"
            ),
            
            "modernize": B2BPlatformConfig(
                platform_name="Modernize",
                min_lead_score=70,
                max_daily_exports=50,
                price_per_lead=150.0,
                required_fields=[
                    "customer.name", "customer.email", "customer.phone",
                    "property.homeowner_status", "solar_profile.monthly_bill",
                    "qualification_data.timeline"
                ],
                optional_fields=[
                    "property.zip_code", "solar_profile.recommended_system_kw",
                    "nyc_market_context.borough", "qualification_data.engagement_level"
                ],
                format_preference=ExportFormat.CSV,
                exclusivity_required=False,
                quality_tiers_accepted=[QualityTier.PREMIUM, QualityTier.STANDARD],
                contact_method="email",
                email_recipient="leads@modernize.com"
            ),
            
            "regional_nyc": B2BPlatformConfig(
                platform_name="Regional NYC Platforms",
                min_lead_score=60,
                max_daily_exports=30,
                price_per_lead=125.0,
                required_fields=[
                    "customer.name", "customer.email", "customer.phone",
                    "property.zip_code", "property.borough", "solar_profile.monthly_bill",
                    "nyc_market_context.electric_rate"
                ],
                optional_fields=[
                    "property.property_type", "solar_profile.recommended_system_kw",
                    "nyc_market_context.competition_level", "qualification_data.timeline"
                ],
                format_preference=ExportFormat.JSON,
                exclusivity_required=False,
                quality_tiers_accepted=[QualityTier.PREMIUM, QualityTier.STANDARD, QualityTier.BASIC],
                contact_method="webhook",
                webhook_url="https://regional-nyc-solar.com/webhook/leads"
            )
        }
    
    async def enrich_lead_for_b2b_export(self, lead_id: str) -> Optional[EnrichedLeadData]:
        """Enrich lead data for comprehensive B2B export"""
        
        try:
            # Get lead with all related data
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                return None
            
            # Get conversation data
            conversations = self.db.query(LeadConversation).filter(
                LeadConversation.lead_id == lead_id
            ).order_by(LeadConversation.created_at.desc()).limit(20).all()
            
            # Get solar calculations
            solar_calculations = self.db.query(AICalculation).filter(
                AICalculation.lead_id == lead_id,
                AICalculation.calculation_type == "solar_recommendation"
            ).order_by(AICalculation.calculation_timestamp.desc()).first()
            
            # Get NYC market data
            nyc_data = await self.nyc_service.get_zip_code_data(lead.zip_code)
            
            # Determine quality tier
            quality_tier = self._determine_quality_tier(lead, conversations, solar_calculations)
            
            # Calculate estimated B2B value
            estimated_value = self._calculate_estimated_value(quality_tier, lead, nyc_data)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(lead, conversations, solar_calculations)
            
            # Build enriched lead data
            enriched_data = EnrichedLeadData(
                lead_id=str(lead.id),
                quality_tier=quality_tier,
                estimated_value=estimated_value,
                confidence_score=confidence_score,
                customer=self._build_customer_data(lead),
                property=self._build_property_data(lead, nyc_data),
                solar_profile=self._build_solar_profile(lead, solar_calculations, nyc_data),
                qualification_data=self._build_qualification_data(lead, conversations),
                nyc_market_context=self._build_nyc_market_context(lead, nyc_data),
                conversation_summary=self._build_conversation_summary(conversations),
                export_metadata=self._build_export_metadata(lead, quality_tier, estimated_value)
            )
            
            return enriched_data
            
        except Exception as e:
            print(f"Error enriching lead {lead_id}: {e}")
            return None
    
    def _determine_quality_tier(self, lead: Lead, conversations: List[LeadConversation], 
                               solar_calc: Optional[AICalculation]) -> QualityTier:
        """Determine lead quality tier based on comprehensive scoring"""
        
        # Base score from lead
        base_score = lead.lead_score or 0
        
        # Bill amount factor
        bill_score = 0
        if lead.monthly_electric_bill:
            if lead.monthly_electric_bill >= 400:
                bill_score = 30
            elif lead.monthly_electric_bill >= 300:
                bill_score = 25
            elif lead.monthly_electric_bill >= 200:
                bill_score = 20
            elif lead.monthly_electric_bill >= 150:
                bill_score = 10
        
        # Timeline urgency factor
        timeline_score = 0
        if conversations:
            recent_conversation = conversations[0]
            if recent_conversation.entities_extracted:
                timeline = recent_conversation.entities_extracted.get("timeline", "")
                if "2025" in timeline or "summer" in timeline or "soon" in timeline:
                    timeline_score = 20
                elif "2026" in timeline or "next year" in timeline:
                    timeline_score = 10
        
        # NYC location factor
        location_score = 0
        if lead.borough:
            if lead.borough in ["Manhattan", "Brooklyn"]:
                location_score = 15
            elif lead.borough in ["Queens", "Bronx"]:
                location_score = 10
            elif lead.borough == "Staten Island":
                location_score = 5
        
        # Solar calculation factor
        solar_score = 0
        if solar_calc and solar_calc.confidence_score:
            solar_score = int(solar_calc.confidence_score * 15)
        
        # Homeowner verification
        homeowner_score = 0
        if lead.qualification_status == "qualified":
            homeowner_score = 20
        
        # Total score
        total_score = base_score + bill_score + timeline_score + location_score + solar_score + homeowner_score
        total_score = min(total_score, 100)
        
        # Determine tier based on total score
        if total_score >= 85:
            return QualityTier.PREMIUM
        elif total_score >= 70:
            return QualityTier.STANDARD
        elif total_score >= 50:
            return QualityTier.BASIC
        else:
            return QualityTier.UNQUALIFIED
    
    def _calculate_estimated_value(self, quality_tier: QualityTier, lead: Lead, 
                                 nyc_data: Optional[Dict]) -> float:
        """Calculate estimated B2B value for the lead"""
        
        base_values = {
            QualityTier.PREMIUM: 250.0,
            QualityTier.STANDARD: 150.0,
            QualityTier.BASIC: 100.0,
            QualityTier.UNQUALIFIED: 0.0
        }
        
        base_value = base_values[quality_tier]
        
        # Adjust based on bill amount
        if lead.monthly_electric_bill:
            if lead.monthly_electric_bill >= 500:
                base_value *= 1.2
            elif lead.monthly_electric_bill >= 400:
                base_value *= 1.1
            elif lead.monthly_electric_bill >= 300:
                base_value *= 1.05
        
        # Adjust based on NYC location
        if lead.borough == "Manhattan":
            base_value *= 1.15
        elif lead.borough == "Brooklyn":
            base_value *= 1.1
        elif lead.borough == "Queens":
            base_value *= 1.05
        
        return round(base_value, 2)
    
    def _calculate_confidence_score(self, lead: Lead, conversations: List[LeadConversation], 
                                  solar_calc: Optional[AICalculation]) -> float:
        """Calculate confidence score for lead quality assessment"""
        
        confidence_factors = []
        
        # Lead data completeness
        data_completeness = 0
        required_fields = [lead.email, lead.phone, lead.property_address, 
                          lead.zip_code, lead.monthly_electric_bill]
        data_completeness = sum(1 for field in required_fields if field) / len(required_fields)
        confidence_factors.append(data_completeness * 0.3)
        
        # Conversation quality
        if conversations:
            conversation_quality = 0
            for conv in conversations[:5]:  # Recent conversations
                if conv.confidence_score:
                    conversation_quality += conv.confidence_score
            conversation_quality = conversation_quality / min(len(conversations), 5)
            confidence_factors.append(conversation_quality * 0.25)
        
        # Solar calculation confidence
        if solar_calc and solar_calc.confidence_score:
            confidence_factors.append(solar_calc.confidence_score * 0.25)
        
        # Lead score factor
        lead_score_factor = (lead.lead_score or 0) / 100
        confidence_factors.append(lead_score_factor * 0.2)
        
        return round(sum(confidence_factors), 2)
    
    def _build_customer_data(self, lead: Lead) -> Dict[str, Any]:
        """Build customer information for B2B export"""
        
        return {
            "name": f"{lead.first_name} {lead.last_name}".strip(),
            "email": lead.email,
            "phone": lead.phone,
            "address": {
                "street": lead.property_address,
                "city": lead.city or "New York",
                "state": lead.state or "NY",
                "zip_code": lead.zip_code,
                "borough": lead.borough
            },
            "contact_preference": "phone",  # Default preference
            "timezone": "America/New_York"
        }
    
    def _build_property_data(self, lead: Lead, nyc_data: Optional[Dict]) -> Dict[str, Any]:
        """Build property information for B2B export"""
        
        return {
            "homeowner_status": "owner" if lead.qualification_status == "qualified" else "unknown",
            "property_type": lead.property_type or "residential",
            "roof_type": lead.roof_type,
            "roof_condition": lead.roof_condition,
            "roof_age": lead.roof_age,
            "roof_orientation": lead.roof_orientation,
            "roof_slope": lead.roof_slope,
            "square_footage": lead.square_footage,
            "lot_size": lead.lot_size,
            "zip_code": lead.zip_code,
            "borough": lead.borough,
            "electric_provider": lead.electric_provider,
            "current_rate_per_kwh": lead.current_rate_per_kwh,
            "solar_potential_score": lead.solar_potential_score,
            "nyc_neighborhood": nyc_data.get("neighborhood") if nyc_data else None,
            "nyc_district": nyc_data.get("district") if nyc_data else None
        }
    
    def _build_solar_profile(self, lead: Lead, solar_calc: Optional[AICalculation], 
                           nyc_data: Optional[Dict]) -> Dict[str, Any]:
        """Build solar profile and calculations for B2B export"""
        
        profile = {
            "monthly_bill": lead.monthly_electric_bill,
            "annual_usage_kwh": lead.annual_electric_usage,
            "estimated_system_size_kw": lead.estimated_system_size,
            "estimated_annual_production_kwh": lead.estimated_annual_production,
            "estimated_savings_annual": lead.estimated_savings_annual,
            "estimated_payback_years": lead.estimated_payback_period,
            "solar_potential_score": lead.solar_potential_score,
            "urgency_factors": []
        }
        
        # Add solar calculation details if available
        if solar_calc and solar_calc.output_data:
            calc_data = solar_calc.output_data
            profile.update({
                "recommended_system_kw": calc_data.get("system_size_kw"),
                "panel_count": calc_data.get("panel_count"),
                "gross_cost": calc_data.get("gross_cost"),
                "net_cost": calc_data.get("net_cost"),
                "monthly_savings": calc_data.get("monthly_savings"),
                "annual_savings": calc_data.get("annual_savings"),
                "payback_years": calc_data.get("payback_years"),
                "roi_percentage": calc_data.get("roi_percentage"),
                "financing_options": calc_data.get("financing_options", []),
                "incentives": calc_data.get("incentives", {})
            })
        
        # Add urgency factors
        if lead.qualification_reason and "2025" in lead.qualification_reason:
            profile["urgency_factors"].append("2025_tax_credit_deadline")
        if lead.qualification_reason and "summer" in lead.qualification_reason:
            profile["urgency_factors"].append("summer_installation_preference")
        if nyc_data and nyc_data.get("competition_level") == "high":
            profile["urgency_factors"].append("high_competition_area")
        
        return profile
    
    def _build_qualification_data(self, lead: Lead, conversations: List[LeadConversation]) -> Dict[str, Any]:
        """Build qualification data for B2B export"""
        
        # Analyze conversations for qualification signals
        engagement_level = "low"
        objections_resolved = []
        timeline = "unknown"
        credit_indication = "unknown"
        
        if conversations:
            recent_conv = conversations[0]
            if recent_conv.entities_extracted:
                entities = recent_conv.entities_extracted
                timeline = entities.get("timeline", "unknown")
                credit_indication = entities.get("credit_score", "unknown")
            
            # Count conversation engagement
            if len(conversations) >= 5:
                engagement_level = "high"
            elif len(conversations) >= 3:
                engagement_level = "medium"
            
            # Analyze objections from conversation content
            for conv in conversations:
                if conv.content:
                    content_lower = conv.content.lower()
                    if "cost" in content_lower or "price" in content_lower:
                        objections_resolved.append("cost_concerns")
                    if "roof" in content_lower:
                        objections_resolved.append("roof_concerns")
                    if "aesthetic" in content_lower or "look" in content_lower:
                        objections_resolved.append("aesthetic_concerns")
        
        return {
            "conversation_quality_score": lead.lead_score or 0,
            "engagement_level": engagement_level,
            "objections_resolved": list(set(objections_resolved)),
            "timeline": timeline,
            "credit_indication": credit_indication,
            "qualification_confidence": (lead.lead_score or 0) / 100,
            "qualification_status": lead.qualification_status,
            "qualification_reason": lead.qualification_reason,
            "conversation_count": len(conversations),
            "last_conversation_at": conversations[0].created_at.isoformat() if conversations else None
        }
    
    def _build_nyc_market_context(self, lead: Lead, nyc_data: Optional[Dict]) -> Dict[str, Any]:
        """Build NYC market context for B2B export"""
        
        context = {
            "electric_rate": lead.current_rate_per_kwh or 0.31,
            "borough": lead.borough,
            "zip_code": lead.zip_code,
            "competition_level": "medium",
            "solar_adoption_rate": 0.15,
            "incentive_value": 0,
            "permit_timeline_days": 30,
            "special_considerations": []
        }
        
        if nyc_data:
            context.update({
                "electric_rate": nyc_data.get("electric_rate", 0.31),
                "competition_level": nyc_data.get("competition_level", "medium"),
                "solar_adoption_rate": nyc_data.get("solar_adoption_rate", 0.15),
                "incentive_value": nyc_data.get("total_incentive_value", 0),
                "permit_timeline_days": nyc_data.get("permit_timeline_days", 30),
                "special_considerations": nyc_data.get("special_considerations", [])
            })
        
        # Add borough-specific adjustments
        if lead.borough == "Manhattan":
            context["competition_level"] = "high"
            context["solar_adoption_rate"] = 0.12
        elif lead.borough == "Brooklyn":
            context["competition_level"] = "medium"
            context["solar_adoption_rate"] = 0.18
        
        return context
    
    def _build_conversation_summary(self, conversations: List[LeadConversation]) -> Dict[str, Any]:
        """Build conversation summary for B2B export"""
        
        if not conversations:
            return {
                "message_count": 0,
                "engagement_level": "none",
                "key_topics": [],
                "sentiment_score": 0.0,
                "last_interaction": None
            }
        
        # Analyze conversation content
        key_topics = []
        sentiment_scores = []
        
        for conv in conversations:
            if conv.sentiment_score:
                sentiment_scores.append(conv.sentiment_score)
            
            if conv.entities_extracted:
                entities = conv.entities_extracted
                for key, value in entities.items():
                    if key not in key_topics and value:
                        key_topics.append(key)
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        return {
            "message_count": len(conversations),
            "engagement_level": "high" if len(conversations) >= 5 else "medium" if len(conversations) >= 3 else "low",
            "key_topics": key_topics[:10],  # Limit to top 10 topics
            "sentiment_score": round(avg_sentiment, 2),
            "last_interaction": conversations[0].created_at.isoformat(),
            "conversation_quality": "high" if avg_sentiment > 0.5 else "medium" if avg_sentiment > 0 else "low"
        }
    
    def _build_export_metadata(self, lead: Lead, quality_tier: QualityTier, 
                             estimated_value: float) -> Dict[str, Any]:
        """Build export metadata for B2B export"""
        
        return {
            "lead_id": str(lead.id),
            "quality_tier": quality_tier.value,
            "estimated_value": estimated_value,
            "created_at": lead.created_at.isoformat(),
            "qualified_at": lead.qualified_at.isoformat() if lead.qualified_at else None,
            "export_ready_at": datetime.utcnow().isoformat(),
            "source": lead.source,
            "campaign": lead.source_campaign,
            "utm_source": lead.utm_source,
            "utm_medium": lead.utm_medium,
            "utm_campaign": lead.utm_campaign,
            "export_priority": self._get_export_priority(quality_tier, estimated_value),
            "recommended_platforms": self._get_recommended_platforms(quality_tier, estimated_value)
        }
    
    def _get_export_priority(self, quality_tier: QualityTier, estimated_value: float) -> str:
        """Get export priority based on quality and value"""
        
        if quality_tier == QualityTier.PREMIUM and estimated_value >= 250:
            return "immediate"
        elif quality_tier == QualityTier.PREMIUM:
            return "high"
        elif quality_tier == QualityTier.STANDARD:
            return "medium"
        else:
            return "low"
    
    def _get_recommended_platforms(self, quality_tier: QualityTier, estimated_value: float) -> List[str]:
        """Get recommended platforms based on quality tier"""
        
        platforms = []
        
        for platform_name, config in self.platform_configs.items():
            if (quality_tier in config.quality_tiers_accepted and 
                estimated_value >= config.price_per_lead * 0.8):
                platforms.append(platform_name)
        
        return platforms
    
    async def export_lead_to_platform(self, lead_id: str, platform_name: str, 
                                    format_type: ExportFormat = None) -> Dict[str, Any]:
        """Export enriched lead to specific B2B platform"""
        
        try:
            # Get enriched lead data
            enriched_data = await self.enrich_lead_for_b2b_export(lead_id)
            if not enriched_data:
                return {"success": False, "error": "Lead not found or enrichment failed"}
            
            # Get platform configuration
            platform_config = self.platform_configs.get(platform_name)
            if not platform_config:
                return {"success": False, "error": f"Platform {platform_name} not configured"}
            
            # Check if lead meets platform requirements
            if not self._meets_platform_requirements(enriched_data, platform_config):
                return {"success": False, "error": "Lead does not meet platform requirements"}
            
            # Generate export format
            export_format = format_type or platform_config.format_preference
            export_data = self._generate_export_format(enriched_data, export_format, platform_config)
            
            # Send to platform (simulate for now)
            export_result = await self._send_to_platform(export_data, platform_config, export_format)
            
            # Track export
            await self._track_export(lead_id, platform_name, export_result)
            
            return {
                "success": True,
                "platform": platform_name,
                "format": export_format.value,
                "lead_quality": enriched_data.quality_tier.value,
                "estimated_value": enriched_data.estimated_value,
                "export_data": export_data,
                "export_result": export_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _meets_platform_requirements(self, enriched_data: EnrichedLeadData, 
                                   platform_config: B2BPlatformConfig) -> bool:
        """Check if lead meets platform requirements"""
        
        # Check minimum lead score
        if enriched_data.estimated_value < platform_config.price_per_lead * 0.8:
            return False
        
        # Check quality tier acceptance
        if enriched_data.quality_tier not in platform_config.quality_tiers_accepted:
            return False
        
        # Check required fields (simplified check)
        # In a real implementation, you'd check each required field path
        return True
    
    def _generate_export_format(self, enriched_data: EnrichedLeadData, 
                              format_type: ExportFormat, 
                              platform_config: B2BPlatformConfig) -> Any:
        """Generate export data in specified format"""
        
        if format_type == ExportFormat.JSON:
            return self._generate_json_export(enriched_data, platform_config)
        elif format_type == ExportFormat.CSV:
            return self._generate_csv_export(enriched_data, platform_config)
        elif format_type == ExportFormat.PDF:
            return self._generate_pdf_export(enriched_data, platform_config)
        else:
            return self._generate_json_export(enriched_data, platform_config)
    
    def _generate_json_export(self, enriched_data: EnrichedLeadData, 
                            platform_config: B2BPlatformConfig) -> Dict[str, Any]:
        """Generate JSON export format"""
        
        return {
            "export_metadata": enriched_data.export_metadata,
            "customer": enriched_data.customer,
            "property": enriched_data.property,
            "solar_profile": enriched_data.solar_profile,
            "qualification_data": enriched_data.qualification_data,
            "nyc_market_context": enriched_data.nyc_market_context,
            "conversation_summary": enriched_data.conversation_summary,
            "platform_specific": {
                "platform": platform_config.platform_name,
                "exported_at": datetime.utcnow().isoformat(),
                "export_format": "json",
                "lead_value": enriched_data.estimated_value
            }
        }
    
    def _generate_csv_export(self, enriched_data: EnrichedLeadData, 
                           platform_config: B2BPlatformConfig) -> str:
        """Generate CSV export format"""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [
            "lead_id", "quality_tier", "estimated_value", "customer_name", "customer_email",
            "customer_phone", "property_address", "property_zip", "property_borough",
            "monthly_bill", "homeowner_status", "timeline", "engagement_level",
            "conversation_count", "exported_at"
        ]
        writer.writerow(headers)
        
        # Write data
        row = [
            enriched_data.lead_id,
            enriched_data.quality_tier.value,
            enriched_data.estimated_value,
            enriched_data.customer["name"],
            enriched_data.customer["email"],
            enriched_data.customer["phone"],
            enriched_data.property.get("address", {}).get("street", ""),
            enriched_data.property["zip_code"],
            enriched_data.property["borough"],
            enriched_data.solar_profile["monthly_bill"],
            enriched_data.property["homeowner_status"],
            enriched_data.qualification_data["timeline"],
            enriched_data.conversation_summary["engagement_level"],
            enriched_data.conversation_summary["message_count"],
            datetime.utcnow().isoformat()
        ]
        writer.writerow(row)
        
        return output.getvalue()
    
    def _generate_pdf_export(self, enriched_data: EnrichedLeadData, 
                           platform_config: B2BPlatformConfig) -> Dict[str, Any]:
        """Generate PDF export format (placeholder for PDF generation)"""
        
        return {
            "type": "pdf_export",
            "lead_summary": {
                "lead_id": enriched_data.lead_id,
                "quality_tier": enriched_data.quality_tier.value,
                "estimated_value": enriched_data.estimated_value,
                "customer_name": enriched_data.customer["name"],
                "property_address": enriched_data.property.get("address", {}).get("street", ""),
                "monthly_bill": enriched_data.solar_profile["monthly_bill"],
                "recommended_system_kw": enriched_data.solar_profile.get("recommended_system_kw"),
                "estimated_savings_annual": enriched_data.solar_profile.get("estimated_savings_annual"),
                "payback_years": enriched_data.solar_profile.get("payback_years")
            },
            "pdf_generation_required": True,
            "template": "premium_lead_summary"
        }
    
    async def _send_to_platform(self, export_data: Any, platform_config: B2BPlatformConfig, 
                              format_type: ExportFormat) -> Dict[str, Any]:
        """Send export data to platform (simulated)"""
        
        # Simulate platform sending
        return {
            "platform": platform_config.platform_name,
            "method": platform_config.contact_method,
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat(),
            "data_size": len(str(export_data)) if isinstance(export_data, (dict, str)) else 0,
            "format": format_type.value
        }
    
    async def _track_export(self, lead_id: str, platform_name: str, 
                          export_result: Dict[str, Any]) -> None:
        """Track export in database"""
        
        # Update lead export status
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            if not lead.exported_to_platforms:
                lead.exported_to_platforms = []
            if platform_name not in lead.exported_to_platforms:
                lead.exported_to_platforms.append(platform_name)
            
            if not lead.export_timestamps:
                lead.export_timestamps = {}
            lead.export_timestamps[platform_name] = datetime.utcnow().isoformat()
            
            lead.export_status = "exported"
            lead.exported_at = datetime.utcnow()
            
            self.db.commit()
    
    async def get_exportable_leads(self, quality_tier: Optional[QualityTier] = None, 
                                 limit: int = 50) -> List[Dict[str, Any]]:
        """Get leads ready for B2B export"""
        
        query = self.db.query(Lead).filter(
            Lead.qualification_status == "qualified",
            Lead.export_status != "exported",
            Lead.is_active == True
        )
        
        if quality_tier:
            min_score = self.quality_thresholds[quality_tier]["min_score"]
            query = query.filter(Lead.lead_score >= min_score)
        
        leads = query.order_by(Lead.lead_score.desc()).limit(limit).all()
        
        exportable_leads = []
        for lead in leads:
            enriched_data = await self.enrich_lead_for_b2b_export(str(lead.id))
            if enriched_data:
                exportable_leads.append({
                    "lead_id": str(lead.id),
                    "quality_tier": enriched_data.quality_tier.value,
                    "estimated_value": enriched_data.estimated_value,
                    "confidence_score": enriched_data.confidence_score,
                    "customer_name": enriched_data.customer["name"],
                    "monthly_bill": enriched_data.solar_profile["monthly_bill"],
                    "borough": enriched_data.property["borough"],
                    "recommended_platforms": enriched_data.export_metadata["recommended_platforms"],
                    "created_at": lead.created_at.isoformat()
                })
        
        return exportable_leads
    
    async def batch_export_leads(self, platform_name: str, quality_tier: Optional[QualityTier] = None,
                               max_leads: int = 20) -> Dict[str, Any]:
        """Batch export multiple leads to a platform"""
        
        try:
            platform_config = self.platform_configs.get(platform_name)
            if not platform_config:
                return {"success": False, "error": f"Platform {platform_name} not configured"}
            
            # Get exportable leads
            exportable_leads = await self.get_exportable_leads(quality_tier, max_leads)
            
            # Filter leads that meet platform requirements
            platform_leads = []
            for lead_data in exportable_leads:
                if lead_data["quality_tier"] in [tier.value for tier in platform_config.quality_tiers_accepted]:
                    platform_leads.append(lead_data)
            
            # Export leads
            export_results = []
            successful_exports = 0
            total_value = 0
            
            for lead_data in platform_leads[:platform_config.max_daily_exports]:
                export_result = await self.export_lead_to_platform(
                    lead_data["lead_id"], platform_name
                )
                export_results.append(export_result)
                
                if export_result["success"]:
                    successful_exports += 1
                    total_value += lead_data["estimated_value"]
            
            return {
                "success": True,
                "platform": platform_name,
                "leads_processed": len(platform_leads),
                "successful_exports": successful_exports,
                "total_estimated_value": total_value,
                "export_results": export_results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
