"""
Lead Scoring Service for B2B Qualification
Multi-tier scoring system aligned with B2B platform requirements
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadQualityHistory
from app.models.ai_models import AIAnalysis
from app.services.nyc_market_service import NYCMarketService


class ScoringFactor(Enum):
    """Lead scoring factors"""
    BILL_AMOUNT = "bill_amount"
    HOMEOWNER_STATUS = "homeowner_status"
    TIMELINE_URGENCY = "timeline_urgency"
    LOCATION_QUALITY = "location_quality"
    ENGAGEMENT_LEVEL = "engagement_level"
    CREDIT_SIGNALS = "credit_signals"
    OBJECTION_RESOLUTION = "objection_resolution"
    NYC_MARKET_FIT = "nyc_market_fit"


@dataclass
class ScoringWeights:
    """Scoring weights for different factors"""
    bill_amount: float = 0.25
    homeowner_status: float = 0.20
    timeline_urgency: float = 0.15
    location_quality: float = 0.15
    engagement_level: float = 0.10
    credit_signals: float = 0.10
    objection_resolution: float = 0.03
    nyc_market_fit: float = 0.02


class LeadScoringService:
    """Service for lead scoring and B2B qualification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.nyc_service = NYCMarketService(db)
        self.scoring_weights = ScoringWeights()
        
        # B2B platform requirements
        self.b2b_requirements = {
            "premium": {
                "min_score": 85,
                "min_bill": 250,
                "homeowner_required": True,
                "timeline_required": "2025",
                "min_engagement": 0.8
            },
            "standard": {
                "min_score": 70,
                "min_bill": 150,
                "homeowner_required": True,
                "timeline_required": "2025-2026",
                "min_engagement": 0.6
            },
            "basic": {
                "min_score": 50,
                "min_bill": 100,
                "homeowner_required": True,
                "timeline_required": "2025-2027",
                "min_engagement": 0.4
            }
        }
    
    async def calculate_lead_score(self, context) -> int:
        """Calculate comprehensive lead score based on conversation context"""
        
        try:
            # Initialize scoring components
            score_components = {}
            
            # Bill amount scoring (0-100)
            bill_score = await self._score_bill_amount(context.bill_amount, context.nyc_data)
            score_components[ScoringFactor.BILL_AMOUNT] = bill_score
            
            # Homeowner status scoring (0-100)
            homeowner_score = self._score_homeowner_status(context.homeowner_verified)
            score_components[ScoringFactor.HOMEOWNER_STATUS] = homeowner_score
            
            # Timeline urgency scoring (0-100)
            timeline_score = self._score_timeline_urgency(context.timeline)
            score_components[ScoringFactor.TIMELINE_URGENCY] = timeline_score
            
            # Location quality scoring (0-100)
            location_score = await self._score_location_quality(context.zip_code, context.nyc_data)
            score_components[ScoringFactor.LOCATION_QUALITY] = location_score
            
            # Engagement level scoring (0-100)
            engagement_score = self._score_engagement_level(context)
            score_components[ScoringFactor.ENGAGEMENT_LEVEL] = engagement_score
            
            # Credit signals scoring (0-100)
            credit_score = self._score_credit_signals(context)
            score_components[ScoringFactor.CREDIT_SIGNALS] = credit_score
            
            # Objection resolution scoring (0-100)
            objection_score = self._score_objection_resolution(context.objections_handled)
            score_components[ScoringFactor.OBJECTION_RESOLUTION] = objection_score
            
            # NYC market fit scoring (0-100)
            nyc_fit_score = await self._score_nyc_market_fit(context.nyc_data)
            score_components[ScoringFactor.NYC_MARKET_FIT] = nyc_fit_score
            
            # Calculate weighted total score
            total_score = 0
            for factor, score in score_components.items():
                weight = getattr(self.scoring_weights, factor.value, 0.0)
                total_score += score * weight
            
            # Apply bonus multipliers
            total_score = self._apply_bonus_multipliers(total_score, context)
            
            # Ensure score is within 0-100 range
            total_score = max(0, min(100, int(total_score)))
            
            # Store scoring analysis
            await self._store_scoring_analysis(context, score_components, total_score)
            
            return total_score
            
        except Exception as e:
            print(f"Error calculating lead score: {e}")
            return 0
    
    async def _score_bill_amount(self, bill_amount: Optional[float], nyc_data: Dict) -> int:
        """Score based on monthly electric bill amount"""
        
        if not bill_amount:
            return 0
        
        # Get NYC average for comparison
        nyc_avg_bill = nyc_data.get("average_monthly_bill", 200) if nyc_data else 200
        
        # Score based on bill amount relative to NYC average
        if bill_amount >= 400:
            return 100  # Premium tier
        elif bill_amount >= 300:
            return 85   # High standard tier
        elif bill_amount >= 200:
            return 70   # Standard tier
        elif bill_amount >= 150:
            return 55   # Basic tier
        elif bill_amount >= 100:
            return 40   # Low basic tier
        else:
            return 20   # Very low tier
    
    def _score_homeowner_status(self, is_homeowner: bool) -> int:
        """Score based on homeowner verification"""
        
        if is_homeowner:
            return 100
        else:
            return 0  # Must be homeowner for B2B qualification
    
    def _score_timeline_urgency(self, timeline: Optional[str]) -> int:
        """Score based on installation timeline urgency"""
        
        if not timeline:
            return 50  # Neutral if not specified
        
        timeline_lower = timeline.lower()
        
        if any(phrase in timeline_lower for phrase in ["immediately", "asap", "urgent", "2025", "this year"]):
            return 100  # High urgency
        elif any(phrase in timeline_lower for phrase in ["soon", "next few months", "early 2026"]):
            return 80   # Medium-high urgency
        elif any(phrase in timeline_lower for phrase in ["next year", "2026", "sometime soon"]):
            return 60   # Medium urgency
        elif any(phrase in timeline_lower for phrase in ["eventually", "maybe", "considering"]):
            return 30   # Low urgency
        else:
            return 50   # Neutral
    
    async def _score_location_quality(self, zip_code: Optional[str], nyc_data: Dict) -> int:
        """Score based on location quality and market potential"""
        
        if not zip_code or not nyc_data:
            return 50  # Neutral if no location data
        
        score = 50  # Base score
        
        # High-value zip code bonus
        if nyc_data.get("high_value_zip_code", False):
            score += 20
        
        # Solar adoption rate bonus
        adoption_rate = nyc_data.get("solar_adoption_rate", 0)
        if adoption_rate > 0.15:
            score += 15
        elif adoption_rate > 0.10:
            score += 10
        elif adoption_rate > 0.05:
            score += 5
        
        # Competition level adjustment
        competition = nyc_data.get("competition_intensity", "medium")
        if competition == "low":
            score += 10
        elif competition == "high":
            score -= 5
        
        # Borough-specific scoring
        borough = nyc_data.get("borough", "")
        if borough == "Manhattan":
            score += 10  # High-value area
        elif borough == "Brooklyn":
            score += 5   # Good market
        
        return min(100, max(0, score))
    
    def _score_engagement_level(self, context) -> int:
        """Score based on conversation engagement level"""
        
        engagement_score = 50  # Base score
        
        # Conversation length bonus
        conversation_count = getattr(context, 'conversation_count', 0)
        if conversation_count >= 5:
            engagement_score += 20
        elif conversation_count >= 3:
            engagement_score += 10
        
        # Question asking bonus
        if hasattr(context, 'qualification_factors') and context.qualification_factors:
            if any(factor in context.qualification_factors for factor in ["high_intent_phrases", "budget_indicators"]):
                engagement_score += 15
        
        # Urgency creation bonus
        if getattr(context, 'urgency_created', False):
            engagement_score += 10
        
        # Objection handling bonus
        objections_handled = getattr(context, 'objections_handled', [])
        if len(objections_handled) > 0:
            engagement_score += 10
        
        return min(100, max(0, engagement_score))
    
    def _score_credit_signals(self, context) -> int:
        """Score based on credit and financial signals"""
        
        credit_score = 50  # Base score
        
        # High bill amount indicates ability to pay
        if getattr(context, 'bill_amount', 0) >= 300:
            credit_score += 20
        elif getattr(context, 'bill_amount', 0) >= 200:
            credit_score += 10
        
        # Homeowner status indicates stability
        if getattr(context, 'homeowner_verified', False):
            credit_score += 15
        
        # High-value location indicates financial capacity
        if hasattr(context, 'nyc_data') and context.nyc_data:
            if context.nyc_data.get("high_value_zip_code", False):
                credit_score += 15
        
        # Timeline urgency indicates financial readiness
        timeline = getattr(context, 'timeline', '')
        if timeline and any(phrase in timeline.lower() for phrase in ["immediately", "asap", "urgent"]):
            credit_score += 10
        
        return min(100, max(0, credit_score))
    
    def _score_objection_resolution(self, objections_handled: List[str]) -> int:
        """Score based on objection resolution success"""
        
        if not objections_handled:
            return 50  # Neutral if no objections
        
        # Each resolved objection adds points
        objection_scores = {
            "cost": 20,
            "roof": 15,
            "aesthetics": 10,
            "process": 15,
            "timeline": 25,
            "other": 10
        }
        
        total_score = 50  # Base score
        for objection in objections_handled:
            total_score += objection_scores.get(objection, 5)
        
        return min(100, max(0, total_score))
    
    async def _score_nyc_market_fit(self, nyc_data: Optional[Dict]) -> int:
        """Score based on NYC market fit and solar potential"""
        
        if not nyc_data:
            return 50  # Neutral if no NYC data
        
        score = 50  # Base score
        
        # Solar potential score
        solar_potential = nyc_data.get("solar_potential_score", 50)
        score += (solar_potential - 50) * 0.3  # Scale to 0-15 points
        
        # Electric rate bonus (higher rates = better solar value)
        electric_rate = nyc_data.get("average_electric_rate_per_kwh", 0.25)
        if electric_rate >= 0.30:
            score += 15
        elif electric_rate >= 0.25:
            score += 10
        elif electric_rate >= 0.20:
            score += 5
        
        # Incentive availability bonus
        if nyc_data.get("state_incentives_available", False):
            score += 10
        if nyc_data.get("local_incentives_available", False):
            score += 5
        
        # Net metering availability
        if nyc_data.get("net_metering_available", False):
            score += 5
        
        return min(100, max(0, int(score)))
    
    def _apply_bonus_multipliers(self, base_score: int, context) -> int:
        """Apply bonus multipliers for exceptional factors"""
        
        score = base_score
        
        # High-value lead bonus
        if (getattr(context, 'bill_amount', 0) >= 400 and 
            getattr(context, 'homeowner_verified', False) and
            getattr(context, 'urgency_created', False)):
            score = min(100, int(score * 1.1))  # 10% bonus
        
        # NYC market fit bonus
        if hasattr(context, 'nyc_data') and context.nyc_data:
            if context.nyc_data.get("high_value_zip_code", False):
                score = min(100, int(score * 1.05))  # 5% bonus
        
        # Engagement bonus
        if getattr(context, 'conversation_count', 0) >= 8:
            score = min(100, int(score * 1.05))  # 5% bonus
        
        return score
    
    async def _store_scoring_analysis(
        self, 
        context, 
        score_components: Dict[ScoringFactor, int], 
        total_score: int
    ):
        """Store detailed scoring analysis in database"""
        
        if not context.lead_id:
            return
        
        try:
            # Create AI analysis record
            analysis_data = {
                "lead_score": total_score,
                "score_components": {factor.value: score for factor, score in score_components.items()},
                "scoring_weights": {
                    factor.value: getattr(self.scoring_weights, factor.value, 0.0)
                    for factor in ScoringFactor
                },
                "qualification_factors": getattr(context, 'qualification_factors', {}),
                "nyc_market_data": getattr(context, 'nyc_data', {}),
                "b2b_value_estimate": self._calculate_b2b_value_estimate(total_score, context),
                "quality_tier": self._determine_quality_tier(total_score)
            }
            
            ai_analysis = AIAnalysis(
                lead_id=context.lead_id,
                model_id=None,  # Will be set by AI model service
                analysis_type="lead_scoring",
                input_data=context.conversation_data or {},
                lead_score=total_score,
                lead_quality=self._determine_quality_tier(total_score),
                confidence_score=0.85,
                insights=analysis_data,
                key_factors=list(score_components.keys()),
                risk_factors=self._identify_risk_factors(score_components),
                opportunities=self._identify_opportunities(score_components, context),
                recommended_actions=self._get_recommended_actions(total_score, context),
                estimated_lead_value=self._calculate_b2b_value_estimate(total_score, context),
                priority_level=self._determine_priority_level(total_score)
            )
            
            self.db.add(ai_analysis)
            self.db.commit()
            
        except Exception as e:
            print(f"Error storing scoring analysis: {e}")
            self.db.rollback()
    
    def _calculate_b2b_value_estimate(self, score: int, context) -> float:
        """Calculate estimated B2B value based on lead score"""
        
        # Base value by score range
        if score >= 85:
            base_value = 250.0  # Premium tier
        elif score >= 70:
            base_value = 150.0  # Standard tier
        elif score >= 50:
            base_value = 100.0  # Basic tier
        else:
            base_value = 0.0    # Unqualified
        
        # Apply NYC market multipliers
        if hasattr(context, 'nyc_data') and context.nyc_data:
            if context.nyc_data.get("high_value_zip_code", False):
                base_value *= 1.2
            if context.nyc_data.get("solar_adoption_rate", 0) > 0.15:
                base_value *= 1.1
        
        # Apply urgency multiplier
        if getattr(context, 'urgency_created', False):
            base_value *= 1.1
        
        return base_value
    
    def _determine_quality_tier(self, score: int) -> str:
        """Determine quality tier based on score"""
        
        if score >= 85:
            return "premium"
        elif score >= 70:
            return "standard"
        elif score >= 50:
            return "basic"
        else:
            return "unqualified"
    
    def _identify_risk_factors(self, score_components: Dict[ScoringFactor, int]) -> List[str]:
        """Identify risk factors based on low scores"""
        
        risk_factors = []
        
        for factor, score in score_components.items():
            if score < 30:
                if factor == ScoringFactor.BILL_AMOUNT:
                    risk_factors.append("Low electric bill - limited savings potential")
                elif factor == ScoringFactor.HOMEOWNER_STATUS:
                    risk_factors.append("Not verified homeowner - B2B disqualification risk")
                elif factor == ScoringFactor.TIMELINE_URGENCY:
                    risk_factors.append("No urgency - may delay or cancel")
                elif factor == ScoringFactor.ENGAGEMENT_LEVEL:
                    risk_factors.append("Low engagement - conversion risk")
                elif factor == ScoringFactor.CREDIT_SIGNALS:
                    risk_factors.append("Weak credit signals - financing risk")
        
        return risk_factors
    
    def _identify_opportunities(self, score_components: Dict[ScoringFactor, int], context) -> List[str]:
        """Identify opportunities for improvement"""
        
        opportunities = []
        
        # High bill amount opportunity
        if score_components.get(ScoringFactor.BILL_AMOUNT, 0) >= 80:
            opportunities.append("High electric bill - excellent savings potential")
        
        # NYC market opportunity
        if hasattr(context, 'nyc_data') and context.nyc_data:
            if context.nyc_data.get("high_value_zip_code", False):
                opportunities.append("High-value NYC location - premium pricing potential")
            if context.nyc_data.get("solar_adoption_rate", 0) < 0.10:
                opportunities.append("Low solar adoption - market opportunity")
        
        # Urgency opportunity
        if getattr(context, 'urgency_created', False):
            opportunities.append("Urgency created - high conversion probability")
        
        return opportunities
    
    def _get_recommended_actions(self, score: int, context) -> List[str]:
        """Get recommended actions based on lead score and context"""
        
        actions = []
        
        if score >= 85:
            actions.extend([
                "Immediate B2B export to premium platforms",
                "Schedule consultation within 24 hours",
                "Prepare custom proposal with NYC incentives"
            ])
        elif score >= 70:
            actions.extend([
                "Export to standard B2B platforms",
                "Follow up within 48 hours",
                "Address any remaining objections"
            ])
        elif score >= 50:
            actions.extend([
                "Nurture with educational content",
                "Address specific concerns",
                "Create urgency around 2025 tax credit"
            ])
        else:
            actions.extend([
                "Continue qualification conversation",
                "Focus on bill amount and homeowner status",
                "Provide NYC-specific value proposition"
            ])
        
        return actions
    
    def _determine_priority_level(self, score: int) -> str:
        """Determine priority level based on score"""
        
        if score >= 85:
            return "high"
        elif score >= 70:
            return "medium"
        elif score >= 50:
            return "low"
        else:
            return "nurture"
    
    async def get_b2b_platform_recommendations(self, score: int, context) -> List[Dict[str, Any]]:
        """Get B2B platform recommendations based on lead quality"""
        
        recommendations = []
        
        # Determine eligible platforms based on score
        if score >= 85:
            tier = "premium"
            platforms = ["solarreviews", "modernize", "energysage"]
        elif score >= 70:
            tier = "standard"
            platforms = ["solarreviews", "modernize"]
        elif score >= 50:
            tier = "basic"
            platforms = ["modernize"]
        else:
            return recommendations
        
        # Get platform details and pricing
        for platform in platforms:
            platform_data = {
                "platform": platform,
                "tier": tier,
                "estimated_value": self._calculate_b2b_value_estimate(score, context),
                "priority": "high" if score >= 85 else "medium" if score >= 70 else "low",
                "requirements_met": self._check_platform_requirements(platform, score, context),
                "export_ready": score >= 70
            }
            recommendations.append(platform_data)
        
        return recommendations
    
    def _check_platform_requirements(self, platform: str, score: int, context) -> bool:
        """Check if lead meets platform-specific requirements"""
        
        requirements = self.b2b_requirements.get(platform, {})
        
        # Check minimum score
        if score < requirements.get("min_score", 50):
            return False
        
        # Check bill amount
        bill_amount = getattr(context, 'bill_amount', 0)
        if bill_amount < requirements.get("min_bill", 100):
            return False
        
        # Check homeowner status
        if requirements.get("homeowner_required", True) and not getattr(context, 'homeowner_verified', False):
            return False
        
        return True
