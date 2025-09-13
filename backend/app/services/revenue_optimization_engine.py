"""
Revenue Optimization Engine for Aurum Solar
Maximizes B2B lead value through real-time scoring, intelligent routing, and continuous improvement
"""

import json
import asyncio
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.lead import Lead, LeadQualityHistory
from app.models.b2b_models import B2BBuyer, B2BLeadExport
from app.services.lead_scoring_service import LeadScoringService
from app.services.b2b_export_service import B2BExportService


class LeadQualityTier(Enum):
    """Enhanced lead quality tiers with revenue optimization"""
    PREMIUM = "premium"  # $200+ B2B value
    STANDARD = "standard"  # $125 B2B value
    BASIC = "basic"  # $75 B2B value
    UNQUALIFIED = "unqualified"  # No B2B value


class B2BBuyerTier(Enum):
    """B2B buyer tiers based on pricing and capacity"""
    PREMIUM = "premium"  # $200+ per lead, exclusive
    STANDARD = "standard"  # $125 per lead, shared
    VOLUME = "volume"  # $75 per lead, high volume
    DIRECT = "direct"  # $150+ per lead, installer direct


@dataclass
class RevenueOptimizationConfig:
    """Revenue optimization configuration"""
    target_conversion_rate: float = 0.60
    target_avg_lead_value: float = 150.0
    premium_threshold: int = 85
    standard_threshold: int = 70
    basic_threshold: int = 50
    
    # Scoring weights
    base_qualification_weight: float = 0.40
    behavioral_scoring_weight: float = 0.30
    market_timing_weight: float = 0.20
    nyc_market_intelligence_weight: float = 0.10
    
    # Revenue optimization
    surge_pricing_threshold: float = 0.80  # 80% capacity utilization
    buyer_capacity_buffer: float = 0.10  # 10% buffer for capacity management
    min_conversation_time: int = 300  # 5 minutes minimum
    max_conversation_time: int = 1800  # 30 minutes maximum


@dataclass
class RealTimeLeadScore:
    """Real-time lead scoring data"""
    session_id: str
    lead_id: Optional[str]
    base_score: int
    behavioral_score: int
    market_timing_score: int
    nyc_intelligence_score: int
    total_score: int
    quality_tier: LeadQualityTier
    revenue_potential: float
    conversion_probability: float
    optimal_buyer_tier: B2BBuyerTier
    last_updated: datetime
    scoring_factors: Dict[str, Any]


@dataclass
class B2BBuyerCapacity:
    """B2B buyer capacity management"""
    buyer_id: str
    buyer_name: str
    tier: B2BBuyerTier
    daily_capacity: int
    current_daily_count: int
    weekly_capacity: int
    current_weekly_count: int
    price_per_lead: float
    acceptance_rate: float
    avg_lead_value: float
    is_available: bool
    surge_pricing_multiplier: float = 1.0


@dataclass
class ConversationRevenueMetrics:
    """Conversation revenue tracking"""
    session_id: str
    start_time: datetime
    current_duration: int  # seconds
    revenue_potential: float
    conversion_probability: float
    quality_tier: LeadQualityTier
    questions_asked: int
    objections_handled: int
    technical_engagement_score: float
    urgency_created: bool
    revenue_per_minute: float
    optimization_recommendations: List[str]


class RealTimeLeadScoringEngine:
    """Real-time lead scoring with revenue optimization"""
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.config = RevenueOptimizationConfig()
        self.scoring_cache = {}
        
        # Load market intelligence data
        self.nyc_market_data = self._load_nyc_market_intelligence()
        self.buyer_preferences = self._load_buyer_preferences()
    
    def _load_nyc_market_intelligence(self) -> Dict[str, Any]:
        """Load NYC market intelligence for scoring"""
        
        return {
            "borough_scores": {
                "manhattan": {"base_score": 90, "adoption_rate": 0.08, "avg_income": 120000},
                "brooklyn": {"base_score": 85, "adoption_rate": 0.12, "avg_income": 85000},
                "queens": {"base_score": 80, "adoption_rate": 0.18, "avg_income": 75000},
                "bronx": {"base_score": 75, "adoption_rate": 0.15, "avg_income": 65000},
                "staten_island": {"base_score": 78, "adoption_rate": 0.20, "avg_income": 70000}
            },
            "neighborhood_premiums": {
                "upper_east_side": 15,
                "upper_west_side": 12,
                "park_slope": 10,
                "dumbo": 8,
                "west_village": 12,
                "east_village": 8,
                "tribeca": 15,
                "soho": 10
            },
            "seasonal_factors": {
                "spring": 1.1,  # 10% boost
                "summer": 1.0,  # baseline
                "fall": 0.9,   # 10% reduction
                "winter": 0.8   # 20% reduction
            }
        }
    
    def _load_buyer_preferences(self) -> Dict[str, Dict[str, Any]]:
        """Load B2B buyer preferences and requirements"""
        
        return {
            "solarreviews": {
                "tier": B2BBuyerTier.PREMIUM,
                "min_bill": 300,
                "preferred_boroughs": ["manhattan", "brooklyn"],
                "exclusive_leads": True,
                "price_per_lead": 250,
                "acceptance_rate": 0.85
            },
            "modernize": {
                "tier": B2BBuyerTier.STANDARD,
                "min_bill": 200,
                "preferred_boroughs": ["all"],
                "exclusive_leads": False,
                "price_per_lead": 125,
                "acceptance_rate": 0.92
            },
            "regional_platforms": {
                "tier": B2BBuyerTier.STANDARD,
                "min_bill": 250,
                "preferred_boroughs": ["queens", "bronx", "staten_island"],
                "exclusive_leads": True,
                "price_per_lead": 150,
                "acceptance_rate": 0.88
            },
            "installer_direct": {
                "tier": B2BBuyerTier.DIRECT,
                "min_bill": 200,
                "preferred_boroughs": ["all"],
                "exclusive_leads": False,
                "price_per_lead": 180,
                "acceptance_rate": 0.95
            }
        }
    
    async def calculate_real_time_score(
        self,
        session_id: str,
        conversation_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> RealTimeLeadScore:
        """Calculate real-time lead score with revenue optimization"""
        
        try:
            # Base qualification scoring (40% weight)
            base_score = await self._calculate_base_qualification_score(conversation_context)
            
            # Behavioral scoring (30% weight)
            behavioral_score = await self._calculate_behavioral_score(conversation_history)
            
            # Market timing scoring (20% weight)
            market_timing_score = await self._calculate_market_timing_score(conversation_context)
            
            # NYC market intelligence scoring (10% weight)
            nyc_intelligence_score = await self._calculate_nyc_intelligence_score(conversation_context)
            
            # Calculate weighted total score
            total_score = int(
                base_score * self.config.base_qualification_weight +
                behavioral_score * self.config.behavioral_scoring_weight +
                market_timing_score * self.config.market_timing_weight +
                nyc_intelligence_score * self.config.nyc_market_intelligence_weight
            )
            
            # Determine quality tier
            quality_tier = self._determine_quality_tier(total_score)
            
            # Calculate revenue potential
            revenue_potential = await self._calculate_revenue_potential(
                total_score, quality_tier, conversation_context
            )
            
            # Calculate conversion probability
            conversion_probability = await self._calculate_conversion_probability(
                total_score, conversation_context, conversation_history
            )
            
            # Determine optimal buyer tier
            optimal_buyer_tier = await self._determine_optimal_buyer_tier(
                quality_tier, conversation_context
            )
            
            # Create scoring factors breakdown
            scoring_factors = {
                "base_qualification": {
                    "score": base_score,
                    "weight": self.config.base_qualification_weight,
                    "factors": self._get_base_qualification_factors(conversation_context)
                },
                "behavioral": {
                    "score": behavioral_score,
                    "weight": self.config.behavioral_scoring_weight,
                    "factors": self._get_behavioral_factors(conversation_history)
                },
                "market_timing": {
                    "score": market_timing_score,
                    "weight": self.config.market_timing_weight,
                    "factors": self._get_market_timing_factors(conversation_context)
                },
                "nyc_intelligence": {
                    "score": nyc_intelligence_score,
                    "weight": self.config.nyc_market_intelligence_weight,
                    "factors": self._get_nyc_intelligence_factors(conversation_context)
                }
            }
            
            # Create real-time lead score
            lead_score = RealTimeLeadScore(
                session_id=session_id,
                lead_id=conversation_context.get("lead_id"),
                base_score=base_score,
                behavioral_score=behavioral_score,
                market_timing_score=market_timing_score,
                nyc_intelligence_score=nyc_intelligence_score,
                total_score=total_score,
                quality_tier=quality_tier,
                revenue_potential=revenue_potential,
                conversion_probability=conversion_probability,
                optimal_buyer_tier=optimal_buyer_tier,
                last_updated=datetime.utcnow(),
                scoring_factors=scoring_factors
            )
            
            # Cache the score
            await self._cache_lead_score(lead_score)
            
            return lead_score
            
        except Exception as e:
            print(f"Error calculating real-time lead score: {e}")
            # Return fallback score
            return RealTimeLeadScore(
                session_id=session_id,
                lead_id=conversation_context.get("lead_id"),
                base_score=50,
                behavioral_score=50,
                market_timing_score=50,
                nyc_intelligence_score=50,
                total_score=50,
                quality_tier=LeadQualityTier.UNQUALIFIED,
                revenue_potential=0.0,
                conversion_probability=0.1,
                optimal_buyer_tier=B2BBuyerTier.VOLUME,
                last_updated=datetime.utcnow(),
                scoring_factors={}
            )
    
    async def _calculate_base_qualification_score(self, context: Dict[str, Any]) -> int:
        """Calculate base qualification score (40% weight)"""
        
        score = 0
        
        # Homeowner status (required - binary)
        if context.get("homeowner_verified"):
            score += 40
        else:
            return 0  # Must be homeowner
        
        # Monthly bill amount
        bill_amount = context.get("bill_amount", 0)
        if bill_amount >= 400:
            score += 30
        elif bill_amount >= 300:
            score += 25
        elif bill_amount >= 200:
            score += 20
        elif bill_amount >= 100:
            score += 10
        
        # ZIP code quality
        zip_code = context.get("zip_code", "")
        if zip_code:
            # Check if premium NYC area
            borough = context.get("borough", "").lower()
            neighborhood = context.get("neighborhood", "").lower()
            
            if borough in self.nyc_market_data["borough_scores"]:
                borough_data = self.nyc_market_data["borough_scores"][borough]
                score += int(borough_data["base_score"] * 0.2)  # 20% of borough score
            
            if neighborhood in self.nyc_market_data["neighborhood_premiums"]:
                score += self.nyc_market_data["neighborhood_premiums"][neighborhood]
        
        # Property type
        home_type = context.get("home_type", "").lower()
        if home_type == "single_family":
            score += 10
        elif home_type == "condo":
            score += 8
        elif home_type == "co_op":
            score += 6
        elif home_type == "townhouse":
            score += 9
        
        return min(100, score)
    
    async def _calculate_behavioral_score(self, conversation_history: List[Dict[str, Any]]) -> int:
        """Calculate behavioral scoring (30% weight)"""
        
        if not conversation_history:
            return 50
        
        score = 50  # Base score
        
        # Session engagement time
        total_duration = len(conversation_history) * 2  # Rough estimate
        if total_duration >= 1800:  # 30+ minutes
            score += 20
        elif total_duration >= 900:  # 15+ minutes
            score += 15
        elif total_duration >= 300:  # 5+ minutes
            score += 10
        
        # Questions asked (technical engagement)
        technical_questions = sum(1 for msg in conversation_history 
                                if msg.get("intent") == "technical_question")
        score += min(20, technical_questions * 3)
        
        # Objection handling success
        objections_handled = sum(1 for msg in conversation_history 
                               if msg.get("objection_resolved"))
        score += min(15, objections_handled * 5)
        
        # Response sentiment
        avg_sentiment = np.mean([msg.get("sentiment", 0) for msg in conversation_history])
        if avg_sentiment > 0.5:
            score += 15
        elif avg_sentiment > 0:
            score += 10
        elif avg_sentiment > -0.5:
            score += 5
        
        # High intent signals
        high_intent_signals = sum(1 for msg in conversation_history 
                                if msg.get("high_intent_signal"))
        score += min(10, high_intent_signals * 2)
        
        return min(100, score)
    
    async def _calculate_market_timing_score(self, context: Dict[str, Any]) -> int:
        """Calculate market timing score (20% weight)"""
        
        score = 50  # Base score
        
        # 2025 installation timeline (critical for tax credit)
        timeline = context.get("timeline", "").lower()
        if "2025" in timeline or "spring" in timeline:
            score += 25
        elif "summer" in timeline or "fall" in timeline:
            score += 15
        elif "winter" in timeline:
            score += 5
        
        # Credit indicators
        credit_indicators = context.get("credit_indicators", [])
        if "financing" in str(credit_indicators).lower():
            score += 15
        if "pre_approved" in str(credit_indicators).lower():
            score += 20
        
        # Decision-maker status
        if context.get("decision_maker", False):
            score += 15
        elif context.get("influencer", False):
            score += 10
        
        # Competition awareness
        if context.get("comparing_options", False):
            score += 10
        elif context.get("urgent_decision", False):
            score += 15
        
        # Seasonal factors
        current_month = datetime.now().month
        if 3 <= current_month <= 6:  # Spring
            score += 10
        elif 7 <= current_month <= 9:  # Summer
            score += 5
        
        return min(100, score)
    
    async def _calculate_nyc_intelligence_score(self, context: Dict[str, Any]) -> int:
        """Calculate NYC market intelligence score (10% weight)"""
        
        score = 50  # Base score
        
        # Borough solar adoption rates
        borough = context.get("borough", "").lower()
        if borough in self.nyc_market_data["borough_scores"]:
            borough_data = self.nyc_market_data["borough_scores"][borough]
            adoption_rate = borough_data["adoption_rate"]
            score += int(adoption_rate * 30)  # Up to 30 points based on adoption
        
        # Neighborhood income demographics
        if borough in self.nyc_market_data["borough_scores"]:
            avg_income = self.nyc_market_data["borough_scores"][borough]["avg_income"]
            if avg_income >= 100000:
                score += 15
            elif avg_income >= 75000:
                score += 10
            elif avg_income >= 50000:
                score += 5
        
        # Local installer availability
        if context.get("local_installers_available", False):
            score += 10
        
        # Seasonal installation factors
        current_month = datetime.now().month
        if 3 <= current_month <= 6:  # Spring - peak season
            score += 15
        elif 7 <= current_month <= 9:  # Summer
            score += 10
        elif 10 <= current_month <= 12:  # Fall
            score += 5
        
        return min(100, score)
    
    def _determine_quality_tier(self, total_score: int) -> LeadQualityTier:
        """Determine lead quality tier based on total score"""
        
        if total_score >= self.config.premium_threshold:
            return LeadQualityTier.PREMIUM
        elif total_score >= self.config.standard_threshold:
            return LeadQualityTier.STANDARD
        elif total_score >= self.config.basic_threshold:
            return LeadQualityTier.BASIC
        else:
            return LeadQualityTier.UNQUALIFIED
    
    async def _calculate_revenue_potential(
        self, 
        total_score: int, 
        quality_tier: LeadQualityTier, 
        context: Dict[str, Any]
    ) -> float:
        """Calculate revenue potential based on score and market conditions"""
        
        # Base revenue by tier
        tier_revenue = {
            LeadQualityTier.PREMIUM: 250.0,
            LeadQualityTier.STANDARD: 125.0,
            LeadQualityTier.BASIC: 75.0,
            LeadQualityTier.UNQUALIFIED: 0.0
        }
        
        base_revenue = tier_revenue[quality_tier]
        
        # Apply surge pricing if high demand
        surge_multiplier = await self._get_surge_pricing_multiplier()
        base_revenue *= surge_multiplier
        
        # Apply buyer-specific bonuses
        buyer_bonus = await self._calculate_buyer_bonus(context)
        base_revenue += buyer_bonus
        
        # Apply NYC market premium
        nyc_premium = await self._calculate_nyc_premium(context)
        base_revenue *= nyc_premium
        
        return round(base_revenue, 2)
    
    async def _calculate_conversion_probability(
        self, 
        total_score: int, 
        context: Dict[str, Any], 
        conversation_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate conversion probability using historical data"""
        
        # Base probability from score
        base_probability = total_score / 100.0
        
        # Adjust based on conversation quality
        conversation_quality = len(conversation_history) / 20.0  # Normalize to 0-1
        base_probability *= (0.7 + 0.3 * conversation_quality)
        
        # Adjust based on urgency signals
        if context.get("urgency_created", False):
            base_probability *= 1.2
        
        # Adjust based on technical engagement
        technical_engagement = context.get("technical_questions_answered", 0)
        if technical_engagement > 0:
            base_probability *= (1.0 + 0.1 * technical_engagement)
        
        return min(1.0, base_probability)
    
    async def _determine_optimal_buyer_tier(
        self, 
        quality_tier: LeadQualityTier, 
        context: Dict[str, Any]
    ) -> B2BBuyerTier:
        """Determine optimal B2B buyer tier for routing"""
        
        # Check buyer capacity and preferences
        available_buyers = await self._get_available_buyers()
        
        if quality_tier == LeadQualityTier.PREMIUM:
            # Try premium buyers first
            for buyer in available_buyers:
                if (buyer.tier == B2BBuyerTier.PREMIUM and 
                    buyer.is_available and 
                    self._matches_buyer_preferences(buyer, context)):
                    return B2BBuyerTier.PREMIUM
            # Fallback to direct
            return B2BBuyerTier.DIRECT
        
        elif quality_tier == LeadQualityTier.STANDARD:
            # Try standard buyers
            for buyer in available_buyers:
                if (buyer.tier == B2BBuyerTier.STANDARD and 
                    buyer.is_available and 
                    self._matches_buyer_preferences(buyer, context)):
                    return B2BBuyerTier.STANDARD
            # Fallback to volume
            return B2BBuyerTier.VOLUME
        
        else:
            # Basic or unqualified - use volume
            return B2BBuyerTier.VOLUME
    
    async def _get_surge_pricing_multiplier(self) -> float:
        """Get surge pricing multiplier based on demand"""
        
        # Check current buyer capacity utilization
        total_capacity = 0
        total_used = 0
        
        for buyer_id, buyer in self.buyer_preferences.items():
            # This would be loaded from Redis in production
            total_capacity += 100  # Placeholder
            total_used += 50  # Placeholder
        
        utilization_rate = total_used / total_capacity if total_capacity > 0 else 0
        
        if utilization_rate >= self.config.surge_pricing_threshold:
            return 1.5  # 50% surge pricing
        elif utilization_rate >= 0.6:
            return 1.2  # 20% surge pricing
        else:
            return 1.0  # Normal pricing
    
    async def _calculate_buyer_bonus(self, context: Dict[str, Any]) -> float:
        """Calculate buyer-specific bonus based on preferences"""
        
        bonus = 0.0
        
        # Check for exclusive lead preferences
        for buyer_id, preferences in self.buyer_preferences.items():
            if preferences["exclusive_leads"] and self._matches_buyer_preferences(preferences, context):
                bonus += 25.0  # $25 bonus for exclusive leads
        
        # Check for geographic preferences
        borough = context.get("borough", "").lower()
        for buyer_id, preferences in self.buyer_preferences.items():
            if (preferences["preferred_boroughs"] == ["all"] or 
                borough in preferences["preferred_boroughs"]):
                bonus += 10.0  # $10 bonus for preferred geography
        
        return bonus
    
    async def _calculate_nyc_premium(self, context: Dict[str, Any]) -> float:
        """Calculate NYC market premium"""
        
        premium = 1.0
        
        # Borough premium
        borough = context.get("borough", "").lower()
        if borough in self.nyc_market_data["borough_scores"]:
            borough_data = self.nyc_market_data["borough_scores"][borough]
            if borough_data["avg_income"] >= 100000:
                premium *= 1.2  # 20% premium for high-income areas
        
        # Neighborhood premium
        neighborhood = context.get("neighborhood", "").lower()
        if neighborhood in self.nyc_market_data["neighborhood_premiums"]:
            neighborhood_premium = self.nyc_market_data["neighborhood_premiums"][neighborhood]
            premium *= (1.0 + neighborhood_premium / 100.0)
        
        return premium
    
    def _matches_buyer_preferences(self, buyer_preferences: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if lead matches buyer preferences"""
        
        # Check minimum bill requirement
        bill_amount = context.get("bill_amount", 0)
        if bill_amount < buyer_preferences.get("min_bill", 0):
            return False
        
        # Check borough preferences
        borough = context.get("borough", "").lower()
        preferred_boroughs = buyer_preferences.get("preferred_boroughs", [])
        if preferred_boroughs != ["all"] and borough not in preferred_boroughs:
            return False
        
        return True
    
    async def _get_available_buyers(self) -> List[B2BBuyerCapacity]:
        """Get available B2B buyers with capacity"""
        
        # This would load from Redis/database in production
        return [
            B2BBuyerCapacity(
                buyer_id="solarreviews",
                buyer_name="SolarReviews",
                tier=B2BBuyerTier.PREMIUM,
                daily_capacity=50,
                current_daily_count=35,
                weekly_capacity=300,
                current_weekly_count=200,
                price_per_lead=250.0,
                acceptance_rate=0.85,
                avg_lead_value=280.0,
                is_available=True
            ),
            B2BBuyerCapacity(
                buyer_id="modernize",
                buyer_name="Modernize",
                tier=B2BBuyerTier.STANDARD,
                daily_capacity=200,
                current_daily_count=150,
                weekly_capacity=1200,
                current_weekly_count=800,
                price_per_lead=125.0,
                acceptance_rate=0.92,
                avg_lead_value=135.0,
                is_available=True
            )
        ]
    
    def _get_base_qualification_factors(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get base qualification scoring factors"""
        
        return {
            "homeowner_verified": context.get("homeowner_verified", False),
            "bill_amount": context.get("bill_amount", 0),
            "zip_code": context.get("zip_code", ""),
            "borough": context.get("borough", ""),
            "neighborhood": context.get("neighborhood", ""),
            "home_type": context.get("home_type", "")
        }
    
    def _get_behavioral_factors(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get behavioral scoring factors"""
        
        return {
            "conversation_length": len(conversation_history),
            "technical_questions": sum(1 for msg in conversation_history 
                                    if msg.get("intent") == "technical_question"),
            "objections_handled": sum(1 for msg in conversation_history 
                                    if msg.get("objection_resolved")),
            "avg_sentiment": np.mean([msg.get("sentiment", 0) for msg in conversation_history]),
            "high_intent_signals": sum(1 for msg in conversation_history 
                                     if msg.get("high_intent_signal"))
        }
    
    def _get_market_timing_factors(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get market timing scoring factors"""
        
        return {
            "timeline": context.get("timeline", ""),
            "credit_indicators": context.get("credit_indicators", []),
            "decision_maker": context.get("decision_maker", False),
            "comparing_options": context.get("comparing_options", False),
            "urgent_decision": context.get("urgent_decision", False)
        }
    
    def _get_nyc_intelligence_factors(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get NYC intelligence scoring factors"""
        
        return {
            "borough": context.get("borough", ""),
            "neighborhood": context.get("neighborhood", ""),
            "local_installers_available": context.get("local_installers_available", False),
            "seasonal_factor": self._get_seasonal_factor()
        }
    
    def _get_seasonal_factor(self) -> float:
        """Get current seasonal factor"""
        
        current_month = datetime.now().month
        if 3 <= current_month <= 6:  # Spring
            return self.nyc_market_data["seasonal_factors"]["spring"]
        elif 7 <= current_month <= 9:  # Summer
            return self.nyc_market_data["seasonal_factors"]["summer"]
        elif 10 <= current_month <= 12:  # Fall
            return self.nyc_market_data["seasonal_factors"]["fall"]
        else:  # Winter
            return self.nyc_market_data["seasonal_factors"]["winter"]
    
    async def _cache_lead_score(self, lead_score: RealTimeLeadScore):
        """Cache lead score in Redis"""
        
        try:
            cache_key = f"lead_score:{lead_score.session_id}"
            score_data = asdict(lead_score)
            score_data["last_updated"] = lead_score.last_updated.isoformat()
            
            self.redis_client.setex(
                cache_key, 
                3600,  # 1 hour cache
                json.dumps(score_data)
            )
        except Exception as e:
            print(f"Error caching lead score: {e}")
    
    async def get_cached_lead_score(self, session_id: str) -> Optional[RealTimeLeadScore]:
        """Get cached lead score from Redis"""
        
        try:
            cache_key = f"lead_score:{session_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                data["last_updated"] = datetime.fromisoformat(data["last_updated"])
                return RealTimeLeadScore(**data)
        except Exception as e:
            print(f"Error getting cached lead score: {e}")
        
        return None
