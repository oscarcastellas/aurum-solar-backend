"""
B2B Value Optimizer for Aurum Solar
Real-time pricing, intelligent routing, and capacity management for maximum revenue
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
from app.models.b2b_models import B2BBuyer, B2BLeadExport
from app.services.revenue_optimization_engine import B2BBuyerTier, B2BBuyerCapacity


@dataclass
class PricingStrategy:
    """Dynamic pricing strategy configuration"""
    base_price: float
    surge_threshold: float  # Capacity utilization threshold
    surge_multiplier: float  # Surge pricing multiplier
    demand_curve: List[Tuple[float, float]]  # (utilization, multiplier) points
    time_of_day_multipliers: Dict[int, float]  # Hour -> multiplier
    day_of_week_multipliers: Dict[int, float]  # Day -> multiplier


@dataclass
class RoutingDecision:
    """B2B buyer routing decision"""
    lead_id: str
    session_id: str
    selected_buyer_id: str
    selected_buyer_tier: B2BBuyerTier
    price_per_lead: float
    expected_revenue: float
    routing_reason: str
    alternative_buyers: List[str]
    routing_timestamp: datetime
    confidence_score: float


@dataclass
class RevenueOptimizationMetrics:
    """Revenue optimization performance metrics"""
    total_leads_routed: int
    total_revenue_generated: float
    avg_revenue_per_lead: float
    conversion_rate: float
    buyer_utilization: Dict[str, float]
    surge_pricing_usage: float
    routing_accuracy: float
    revenue_per_hour: float
    optimization_score: float


class B2BValueOptimizer:
    """B2B value optimization with real-time pricing and intelligent routing"""
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.pricing_strategies = self._load_pricing_strategies()
        self.buyer_capacities = {}
        self.routing_history = []
        
        # Load initial buyer data
        asyncio.create_task(self._load_buyer_capacities())
    
    def _load_pricing_strategies(self) -> Dict[B2BBuyerTier, PricingStrategy]:
        """Load pricing strategies for different buyer tiers"""
        
        return {
            B2BBuyerTier.PREMIUM: PricingStrategy(
                base_price=250.0,
                surge_threshold=0.80,
                surge_multiplier=1.5,
                demand_curve=[
                    (0.0, 1.0), (0.5, 1.1), (0.7, 1.2), (0.8, 1.5), (0.9, 1.8), (1.0, 2.0)
                ],
                time_of_day_multipliers={
                    9: 1.1, 10: 1.2, 11: 1.3, 12: 1.1, 13: 1.2, 14: 1.3, 15: 1.2, 16: 1.1, 17: 1.0
                },
                day_of_week_multipliers={
                    0: 0.9, 1: 1.1, 2: 1.2, 3: 1.2, 4: 1.1, 5: 1.0, 6: 0.8
                }
            ),
            B2BBuyerTier.STANDARD: PricingStrategy(
                base_price=125.0,
                surge_threshold=0.85,
                surge_multiplier=1.3,
                demand_curve=[
                    (0.0, 1.0), (0.6, 1.05), (0.8, 1.15), (0.85, 1.3), (0.95, 1.5), (1.0, 1.7)
                ],
                time_of_day_multipliers={
                    9: 1.05, 10: 1.1, 11: 1.15, 12: 1.05, 13: 1.1, 14: 1.15, 15: 1.1, 16: 1.05, 17: 1.0
                },
                day_of_week_multipliers={
                    0: 0.95, 1: 1.05, 2: 1.1, 3: 1.1, 4: 1.05, 5: 1.0, 6: 0.9
                }
            ),
            B2BBuyerTier.VOLUME: PricingStrategy(
                base_price=75.0,
                surge_threshold=0.90,
                surge_multiplier=1.2,
                demand_curve=[
                    (0.0, 1.0), (0.7, 1.02), (0.85, 1.05), (0.90, 1.2), (0.95, 1.4), (1.0, 1.6)
                ],
                time_of_day_multipliers={
                    9: 1.02, 10: 1.05, 11: 1.08, 12: 1.02, 13: 1.05, 14: 1.08, 15: 1.05, 16: 1.02, 17: 1.0
                },
                day_of_week_multipliers={
                    0: 0.98, 1: 1.02, 2: 1.05, 3: 1.05, 4: 1.02, 5: 1.0, 6: 0.95
                }
            ),
            B2BBuyerTier.DIRECT: PricingStrategy(
                base_price=180.0,
                surge_threshold=0.75,
                surge_multiplier=1.4,
                demand_curve=[
                    (0.0, 1.0), (0.4, 1.05), (0.6, 1.1), (0.75, 1.4), (0.85, 1.6), (1.0, 1.8)
                ],
                time_of_day_multipliers={
                    9: 1.08, 10: 1.12, 11: 1.15, 12: 1.08, 13: 1.12, 14: 1.15, 15: 1.12, 16: 1.08, 17: 1.0
                },
                day_of_week_multipliers={
                    0: 0.92, 1: 1.08, 2: 1.12, 3: 1.12, 4: 1.08, 5: 1.0, 6: 0.88
                }
            )
        }
    
    async def _load_buyer_capacities(self):
        """Load buyer capacity data from database and Redis"""
        
        try:
            # Load from database
            buyers = self.db.query(B2BBuyer).filter(B2BBuyer.is_active == True).all()
            
            for buyer in buyers:
                capacity = B2BBuyerCapacity(
                    buyer_id=buyer.id,
                    buyer_name=buyer.name,
                    tier=B2BBuyerTier(buyer.tier),
                    daily_capacity=buyer.daily_capacity,
                    current_daily_count=0,  # Will be updated from Redis
                    weekly_capacity=buyer.weekly_capacity,
                    current_weekly_count=0,  # Will be updated from Redis
                    price_per_lead=buyer.price_per_lead,
                    acceptance_rate=buyer.acceptance_rate,
                    avg_lead_value=buyer.avg_lead_value,
                    is_available=buyer.is_available
                )
                
                # Update from Redis cache
                await self._update_buyer_capacity_from_cache(capacity)
                self.buyer_capacities[buyer.id] = capacity
                
        except Exception as e:
            print(f"Error loading buyer capacities: {e}")
    
    async def _update_buyer_capacity_from_cache(self, capacity: B2BBuyerCapacity):
        """Update buyer capacity from Redis cache"""
        
        try:
            cache_key = f"buyer_capacity:{capacity.buyer_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                capacity.current_daily_count = data.get("current_daily_count", 0)
                capacity.current_weekly_count = data.get("current_weekly_count", 0)
                capacity.is_available = data.get("is_available", True)
                capacity.surge_pricing_multiplier = data.get("surge_pricing_multiplier", 1.0)
                
        except Exception as e:
            print(f"Error updating buyer capacity from cache: {e}")
    
    async def calculate_dynamic_pricing(
        self,
        buyer_tier: B2BBuyerTier,
        lead_quality_score: int,
        conversation_context: Dict[str, Any]
    ) -> float:
        """Calculate dynamic pricing based on demand, quality, and market conditions"""
        
        try:
            # Get base pricing strategy
            strategy = self.pricing_strategies[buyer_tier]
            base_price = strategy.base_price
            
            # Apply lead quality multiplier
            quality_multiplier = self._calculate_quality_multiplier(lead_quality_score)
            base_price *= quality_multiplier
            
            # Apply demand-based surge pricing
            surge_multiplier = await self._calculate_surge_multiplier(buyer_tier)
            base_price *= surge_multiplier
            
            # Apply time-of-day pricing
            time_multiplier = self._calculate_time_multiplier(strategy)
            base_price *= time_multiplier
            
            # Apply day-of-week pricing
            day_multiplier = self._calculate_day_multiplier(strategy)
            base_price *= day_multiplier
            
            # Apply market-specific adjustments
            market_multiplier = await self._calculate_market_multiplier(conversation_context)
            base_price *= market_multiplier
            
            # Apply buyer-specific adjustments
            buyer_multiplier = await self._calculate_buyer_multiplier(buyer_tier, conversation_context)
            base_price *= buyer_multiplier
            
            return round(base_price, 2)
            
        except Exception as e:
            print(f"Error calculating dynamic pricing: {e}")
            return self.pricing_strategies[buyer_tier].base_price
    
    def _calculate_quality_multiplier(self, lead_quality_score: int) -> float:
        """Calculate pricing multiplier based on lead quality score"""
        
        if lead_quality_score >= 90:
            return 1.3  # 30% premium for excellent leads
        elif lead_quality_score >= 80:
            return 1.2  # 20% premium for very good leads
        elif lead_quality_score >= 70:
            return 1.1  # 10% premium for good leads
        elif lead_quality_score >= 60:
            return 1.0  # Base price
        elif lead_quality_score >= 50:
            return 0.9  # 10% discount for fair leads
        else:
            return 0.8  # 20% discount for poor leads
    
    async def _calculate_surge_multiplier(self, buyer_tier: B2BBuyerTier) -> float:
        """Calculate surge pricing multiplier based on buyer capacity utilization"""
        
        strategy = self.pricing_strategies[buyer_tier]
        
        # Find buyer with this tier
        buyer_capacity = None
        for capacity in self.buyer_capacities.values():
            if capacity.tier == buyer_tier and capacity.is_available:
                buyer_capacity = capacity
                break
        
        if not buyer_capacity:
            return 1.0
        
        # Calculate utilization rate
        utilization_rate = buyer_capacity.current_daily_count / buyer_capacity.daily_capacity
        
        # Apply demand curve
        for utilization, multiplier in strategy.demand_curve:
            if utilization_rate <= utilization:
                return multiplier
        
        # If utilization is above highest curve point, use surge multiplier
        return strategy.surge_multiplier
    
    def _calculate_time_multiplier(self, strategy: PricingStrategy) -> float:
        """Calculate time-of-day pricing multiplier"""
        
        current_hour = datetime.now().hour
        return strategy.time_of_day_multipliers.get(current_hour, 1.0)
    
    def _calculate_day_multiplier(self, strategy: PricingStrategy) -> float:
        """Calculate day-of-week pricing multiplier"""
        
        current_day = datetime.now().weekday()
        return strategy.day_of_week_multipliers.get(current_day, 1.0)
    
    async def _calculate_market_multiplier(self, conversation_context: Dict[str, Any]) -> float:
        """Calculate market-specific pricing multiplier"""
        
        multiplier = 1.0
        
        # NYC market premium
        borough = conversation_context.get("borough", "").lower()
        if borough in ["manhattan", "brooklyn"]:
            multiplier *= 1.1  # 10% premium for high-value areas
        
        # Neighborhood premium
        neighborhood = conversation_context.get("neighborhood", "").lower()
        premium_neighborhoods = [
            "upper_east_side", "upper_west_side", "tribeca", "soho", 
            "west_village", "east_village", "park_slope", "dumbo"
        ]
        if neighborhood in premium_neighborhoods:
            multiplier *= 1.15  # 15% premium for premium neighborhoods
        
        # Seasonal adjustments
        current_month = datetime.now().month
        if 3 <= current_month <= 6:  # Spring - peak season
            multiplier *= 1.1  # 10% premium
        elif 7 <= current_month <= 9:  # Summer
            multiplier *= 1.05  # 5% premium
        elif 10 <= current_month <= 12:  # Fall
            multiplier *= 0.95  # 5% discount
        else:  # Winter
            multiplier *= 0.9  # 10% discount
        
        return multiplier
    
    async def _calculate_buyer_multiplier(
        self, 
        buyer_tier: B2BBuyerTier, 
        conversation_context: Dict[str, Any]
    ) -> float:
        """Calculate buyer-specific pricing multiplier"""
        
        multiplier = 1.0
        
        # Check for exclusive lead preferences
        if buyer_tier == B2BBuyerTier.PREMIUM:
            # Premium buyers pay more for exclusive leads
            if conversation_context.get("exclusive_lead", False):
                multiplier *= 1.2  # 20% premium for exclusivity
        
        # Check for geographic preferences
        borough = conversation_context.get("borough", "").lower()
        if buyer_tier == B2BBuyerTier.PREMIUM and borough in ["manhattan", "brooklyn"]:
            multiplier *= 1.1  # 10% premium for preferred geography
        
        # Check for lead quality preferences
        lead_quality_score = conversation_context.get("lead_quality_score", 70)
        if buyer_tier == B2BBuyerTier.PREMIUM and lead_quality_score >= 85:
            multiplier *= 1.15  # 15% premium for high-quality leads
        
        return multiplier
    
    async def optimize_buyer_routing(
        self,
        lead_id: str,
        session_id: str,
        lead_quality_score: int,
        conversation_context: Dict[str, Any],
        available_buyers: List[str] = None
    ) -> RoutingDecision:
        """Optimize B2B buyer routing for maximum revenue"""
        
        try:
            # Get available buyers
            if not available_buyers:
                available_buyers = await self._get_available_buyers()
            
            # Calculate routing options
            routing_options = []
            
            for buyer_id in available_buyers:
                if buyer_id not in self.buyer_capacities:
                    continue
                
                buyer_capacity = self.buyer_capacities[buyer_id]
                
                # Check if buyer has capacity
                if not buyer_capacity.is_available:
                    continue
                
                if buyer_capacity.current_daily_count >= buyer_capacity.daily_capacity:
                    continue
                
                # Calculate pricing for this buyer
                price_per_lead = await self.calculate_dynamic_pricing(
                    buyer_capacity.tier,
                    lead_quality_score,
                    conversation_context
                )
                
                # Calculate expected revenue (price * acceptance_rate)
                expected_revenue = price_per_lead * buyer_capacity.acceptance_rate
                
                # Calculate routing score
                routing_score = self._calculate_routing_score(
                    buyer_capacity,
                    price_per_lead,
                    expected_revenue,
                    lead_quality_score,
                    conversation_context
                )
                
                routing_options.append({
                    "buyer_id": buyer_id,
                    "buyer_tier": buyer_capacity.tier,
                    "price_per_lead": price_per_lead,
                    "expected_revenue": expected_revenue,
                    "routing_score": routing_score,
                    "capacity_utilization": buyer_capacity.current_daily_count / buyer_capacity.daily_capacity
                })
            
            # Sort by routing score (highest first)
            routing_options.sort(key=lambda x: x["routing_score"], reverse=True)
            
            if not routing_options:
                # No available buyers - create fallback routing
                return self._create_fallback_routing(lead_id, session_id)
            
            # Select best routing option
            best_option = routing_options[0]
            
            # Create routing decision
            routing_decision = RoutingDecision(
                lead_id=lead_id,
                session_id=session_id,
                selected_buyer_id=best_option["buyer_id"],
                selected_buyer_tier=best_option["buyer_tier"],
                price_per_lead=best_option["price_per_lead"],
                expected_revenue=best_option["expected_revenue"],
                routing_reason=self._generate_routing_reason(best_option, routing_options),
                alternative_buyers=[opt["buyer_id"] for opt in routing_options[1:3]],  # Top 2 alternatives
                routing_timestamp=datetime.utcnow(),
                confidence_score=best_option["routing_score"]
            )
            
            # Update buyer capacity
            await self._update_buyer_capacity(best_option["buyer_id"])
            
            # Store routing decision
            await self._store_routing_decision(routing_decision)
            
            return routing_decision
            
        except Exception as e:
            print(f"Error optimizing buyer routing: {e}")
            return self._create_fallback_routing(lead_id, session_id)
    
    def _calculate_routing_score(
        self,
        buyer_capacity: B2BBuyerCapacity,
        price_per_lead: float,
        expected_revenue: float,
        lead_quality_score: int,
        conversation_context: Dict[str, Any]
    ) -> float:
        """Calculate routing score for buyer selection"""
        
        score = 0.0
        
        # Revenue potential (40% weight)
        score += expected_revenue * 0.4
        
        # Acceptance rate (25% weight)
        score += buyer_capacity.acceptance_rate * 100 * 0.25
        
        # Capacity utilization (15% weight) - prefer buyers with more capacity
        utilization = buyer_capacity.current_daily_count / buyer_capacity.daily_capacity
        score += (1.0 - utilization) * 100 * 0.15
        
        # Lead quality match (10% weight)
        if buyer_capacity.tier == B2BBuyerTier.PREMIUM and lead_quality_score >= 85:
            score += 20 * 0.1
        elif buyer_capacity.tier == B2BBuyerTier.STANDARD and lead_quality_score >= 70:
            score += 15 * 0.1
        elif buyer_capacity.tier == B2BBuyerTier.VOLUME and lead_quality_score >= 50:
            score += 10 * 0.1
        
        # Geographic preference (5% weight)
        borough = conversation_context.get("borough", "").lower()
        if self._matches_geographic_preference(buyer_capacity, borough):
            score += 10 * 0.05
        
        # Historical performance (5% weight)
        score += buyer_capacity.avg_lead_value * 0.05
        
        return score
    
    def _matches_geographic_preference(
        self, 
        buyer_capacity: B2BBuyerCapacity, 
        borough: str
    ) -> bool:
        """Check if lead matches buyer's geographic preferences"""
        
        # This would be loaded from buyer preferences in production
        premium_buyers = ["solarreviews", "premium_solar_nyc"]
        if buyer_capacity.buyer_id in premium_buyers:
            return borough in ["manhattan", "brooklyn"]
        
        return True  # Most buyers accept all areas
    
    def _generate_routing_reason(
        self, 
        best_option: Dict[str, Any], 
        all_options: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable routing reason"""
        
        reasons = []
        
        # Revenue reason
        if best_option["expected_revenue"] > 200:
            reasons.append("high revenue potential")
        elif best_option["expected_revenue"] > 150:
            reasons.append("good revenue potential")
        
        # Capacity reason
        if best_option["capacity_utilization"] < 0.5:
            reasons.append("ample capacity available")
        elif best_option["capacity_utilization"] < 0.8:
            reasons.append("sufficient capacity")
        
        # Tier reason
        if best_option["buyer_tier"].value == "premium":
            reasons.append("premium buyer tier")
        elif best_option["buyer_tier"].value == "standard":
            reasons.append("standard buyer tier")
        
        # Price reason
        if best_option["price_per_lead"] > 200:
            reasons.append("premium pricing")
        elif best_option["price_per_lead"] > 100:
            reasons.append("competitive pricing")
        
        return ", ".join(reasons) if reasons else "optimal routing based on multiple factors"
    
    async def _get_available_buyers(self) -> List[str]:
        """Get list of available buyer IDs"""
        
        available_buyers = []
        
        for buyer_id, capacity in self.buyer_capacities.items():
            if (capacity.is_available and 
                capacity.current_daily_count < capacity.daily_capacity):
                available_buyers.append(buyer_id)
        
        return available_buyers
    
    async def _update_buyer_capacity(self, buyer_id: str):
        """Update buyer capacity after routing a lead"""
        
        try:
            if buyer_id in self.buyer_capacities:
                capacity = self.buyer_capacities[buyer_id]
                capacity.current_daily_count += 1
                capacity.current_weekly_count += 1
                
                # Update Redis cache
                await self._cache_buyer_capacity(capacity)
                
        except Exception as e:
            print(f"Error updating buyer capacity: {e}")
    
    async def _cache_buyer_capacity(self, capacity: B2BBuyerCapacity):
        """Cache buyer capacity in Redis"""
        
        try:
            cache_key = f"buyer_capacity:{capacity.buyer_id}"
            capacity_data = {
                "current_daily_count": capacity.current_daily_count,
                "current_weekly_count": capacity.current_weekly_count,
                "is_available": capacity.is_available,
                "surge_pricing_multiplier": capacity.surge_pricing_multiplier,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            self.redis_client.setex(
                cache_key,
                3600,  # 1 hour cache
                json.dumps(capacity_data)
            )
            
        except Exception as e:
            print(f"Error caching buyer capacity: {e}")
    
    async def _store_routing_decision(self, routing_decision: RoutingDecision):
        """Store routing decision in database"""
        
        try:
            # Store in B2B lead export table
            lead_export = B2BLeadExport(
                lead_id=routing_decision.lead_id,
                buyer_id=routing_decision.selected_buyer_id,
                export_status="routed",
                price_per_lead=routing_decision.price_per_lead,
                expected_revenue=routing_decision.expected_revenue,
                routing_reason=routing_decision.routing_reason,
                confidence_score=routing_decision.confidence_score,
                exported_at=routing_decision.routing_timestamp
            )
            
            self.db.add(lead_export)
            self.db.commit()
            
            # Store routing history
            self.routing_history.append(routing_decision)
            
        except Exception as e:
            print(f"Error storing routing decision: {e}")
            self.db.rollback()
    
    def _create_fallback_routing(
        self, 
        lead_id: str, 
        session_id: str
    ) -> RoutingDecision:
        """Create fallback routing when no buyers are available"""
        
        return RoutingDecision(
            lead_id=lead_id,
            session_id=session_id,
            selected_buyer_id="fallback",
            selected_buyer_tier=B2BBuyerTier.VOLUME,
            price_per_lead=50.0,  # Reduced price for fallback
            expected_revenue=45.0,
            routing_reason="fallback routing - no available buyers",
            alternative_buyers=[],
            routing_timestamp=datetime.utcnow(),
            confidence_score=0.3
        )
    
    async def get_revenue_optimization_metrics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> RevenueOptimizationMetrics:
        """Get revenue optimization performance metrics"""
        
        try:
            # Query routing decisions from database
            routing_decisions = self.db.query(B2BLeadExport).filter(
                B2BLeadExport.exported_at >= start_date,
                B2BLeadExport.exported_at <= end_date
            ).all()
            
            # Calculate metrics
            total_leads_routed = len(routing_decisions)
            total_revenue_generated = sum(decision.expected_revenue for decision in routing_decisions)
            avg_revenue_per_lead = total_revenue_generated / total_leads_routed if total_leads_routed > 0 else 0
            
            # Calculate conversion rate (would need additional data)
            conversion_rate = 0.85  # Placeholder - would calculate from actual data
            
            # Calculate buyer utilization
            buyer_utilization = {}
            for buyer_id, capacity in self.buyer_capacities.items():
                utilization = capacity.current_daily_count / capacity.daily_capacity
                buyer_utilization[buyer_id] = utilization
            
            # Calculate surge pricing usage
            surge_pricing_usage = sum(1 for decision in routing_decisions 
                                    if decision.price_per_lead > 150) / total_leads_routed if total_leads_routed > 0 else 0
            
            # Calculate routing accuracy (would need feedback data)
            routing_accuracy = 0.92  # Placeholder - would calculate from buyer feedback
            
            # Calculate revenue per hour
            hours_elapsed = (end_date - start_date).total_seconds() / 3600
            revenue_per_hour = total_revenue_generated / hours_elapsed if hours_elapsed > 0 else 0
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                avg_revenue_per_lead,
                conversion_rate,
                routing_accuracy,
                surge_pricing_usage
            )
            
            return RevenueOptimizationMetrics(
                total_leads_routed=total_leads_routed,
                total_revenue_generated=total_revenue_generated,
                avg_revenue_per_lead=avg_revenue_per_lead,
                conversion_rate=conversion_rate,
                buyer_utilization=buyer_utilization,
                surge_pricing_usage=surge_pricing_usage,
                routing_accuracy=routing_accuracy,
                revenue_per_hour=revenue_per_hour,
                optimization_score=optimization_score
            )
            
        except Exception as e:
            print(f"Error calculating revenue optimization metrics: {e}")
            return RevenueOptimizationMetrics(
                total_leads_routed=0,
                total_revenue_generated=0.0,
                avg_revenue_per_lead=0.0,
                conversion_rate=0.0,
                buyer_utilization={},
                surge_pricing_usage=0.0,
                routing_accuracy=0.0,
                revenue_per_hour=0.0,
                optimization_score=0.0
            )
    
    def _calculate_optimization_score(
        self,
        avg_revenue_per_lead: float,
        conversion_rate: float,
        routing_accuracy: float,
        surge_pricing_usage: float
    ) -> float:
        """Calculate overall optimization score"""
        
        # Weighted combination of metrics
        score = (
            avg_revenue_per_lead * 0.3 +  # 30% weight
            conversion_rate * 100 * 0.25 +  # 25% weight
            routing_accuracy * 100 * 0.25 +  # 25% weight
            surge_pricing_usage * 100 * 0.2  # 20% weight
        )
        
        return min(100.0, score)
