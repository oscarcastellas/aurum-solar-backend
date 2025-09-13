"""
Lead Routing and Optimization Engine
Intelligent routing system for maximizing revenue and delivery reliability
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lead import Lead
from app.models.b2b_platforms import B2BPlatform, B2BLeadMapping
from app.core.redis import get_redis

logger = structlog.get_logger()

class RoutingStrategy(Enum):
    REVENUE_MAXIMIZATION = "revenue_maximization"
    CAPACITY_OPTIMIZATION = "capacity_optimization"
    QUALITY_MATCHING = "quality_matching"
    LOAD_BALANCING = "load_balancing"
    EXCLUSIVE_ROUTING = "exclusive_routing"

class LeadPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

@dataclass
class RoutingRule:
    id: str
    name: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    priority: int
    is_active: bool
    created_at: datetime

@dataclass
class RoutingDecision:
    platform_code: str
    confidence_score: float
    reasoning: List[str]
    estimated_revenue: float
    estimated_delivery_time: int
    risk_factors: List[str]
    alternative_platforms: List[str]

@dataclass
class PlatformCapacity:
    platform_code: str
    current_utilization: float
    max_capacity: int
    available_slots: int
    quality_requirements: Dict[str, Any]
    revenue_share: float
    avg_response_time: float
    success_rate: float
    health_status: str

class LeadRoutingEngine:
    """Intelligent lead routing and optimization engine"""
    
    def __init__(self):
        self.routing_rules: List[RoutingRule] = []
        self.platform_capacities: Dict[str, PlatformCapacity] = {}
        self.redis = None
        self.nyc_market_data = {}
        self.routing_history = []
        
        # Performance metrics
        self.total_routing_decisions = 0
        self.successful_routes = 0
        self.revenue_optimized = 0.0
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize the routing engine"""
        self.redis = await get_redis()
        await self._load_routing_rules()
        await self._load_platform_capacities()
        await self._load_nyc_market_data()
        await self._start_capacity_monitoring()
    
    async def _load_routing_rules(self):
        """Load routing rules from database"""
        try:
            db = next(get_db())
            # This would load from a routing_rules table
            # For now, we'll use hardcoded rules
            self.routing_rules = [
                RoutingRule(
                    id="rule_1",
                    name="Premium Lead Revenue Maximization",
                    condition={
                        "lead_quality": "premium",
                        "lead_score": {"min": 85},
                        "estimated_value": {"min": 200}
                    },
                    action={
                        "strategy": "revenue_maximization",
                        "preferred_platforms": ["solarreviews", "modernize"],
                        "min_revenue_threshold": 200
                    },
                    priority=1,
                    is_active=True,
                    created_at=datetime.utcnow()
                ),
                RoutingRule(
                    id="rule_2",
                    name="NYC High-Value Zip Code Routing",
                    condition={
                        "zip_code": {"in": ["10025", "11215", "11101", "10451", "10301"]},
                        "lead_score": {"min": 75}
                    },
                    action={
                        "strategy": "quality_matching",
                        "preferred_platforms": ["solarreviews", "homeadvisor"],
                        "nyc_optimization": True
                    },
                    priority=2,
                    is_active=True,
                    created_at=datetime.utcnow()
                ),
                RoutingRule(
                    id="rule_3",
                    name="Capacity Load Balancing",
                    condition={
                        "lead_quality": {"in": ["standard", "basic"]}
                    },
                    action={
                        "strategy": "load_balancing",
                        "max_utilization": 0.8,
                        "prefer_underutilized": True
                    },
                    priority=3,
                    is_active=True,
                    created_at=datetime.utcnow()
                ),
                RoutingRule(
                    id="rule_4",
                    name="Exclusive Platform Routing",
                    condition={
                        "exclusive_platform": True
                    },
                    action={
                        "strategy": "exclusive_routing",
                        "single_platform": True
                    },
                    priority=4,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
            ]
            
            logger.info("Loaded routing rules", count=len(self.routing_rules))
            
        except Exception as e:
            logger.error("Error loading routing rules", error=str(e))
    
    async def _load_platform_capacities(self):
        """Load current platform capacities and performance data"""
        try:
            db = next(get_db())
            platforms = db.query(B2BPlatform).filter(B2BPlatform.is_active == True).all()
            
            for platform in platforms:
                # Get current utilization from Redis or calculate
                daily_count = await self.redis.get(f"platform_daily_count:{platform.platform_code}") or 0
                daily_count = int(daily_count)
                
                self.platform_capacities[platform.platform_code] = PlatformCapacity(
                    platform_code=platform.platform_code,
                    current_utilization=daily_count / platform.max_daily_exports,
                    max_capacity=platform.max_daily_exports,
                    available_slots=platform.max_daily_exports - daily_count,
                    quality_requirements=platform.quality_requirements or {},
                    revenue_share=platform.revenue_share or 0.15,
                    avg_response_time=platform.avg_response_time or 0,
                    success_rate=platform.success_rate or 0.0,
                    health_status=platform.health_status or "unknown"
                )
            
            logger.info("Loaded platform capacities", count=len(self.platform_capacities))
            
        except Exception as e:
            logger.error("Error loading platform capacities", error=str(e))
    
    async def _load_nyc_market_data(self):
        """Load NYC market intelligence data"""
        try:
            # This would load from NYC market data tables
            self.nyc_market_data = {
                "high_value_zip_codes": ["10025", "11215", "11101", "10451", "10301"],
                "electric_rates": {
                    "10025": 0.35,  # Manhattan
                    "11215": 0.32,  # Brooklyn
                    "11101": 0.31,  # Queens
                    "10451": 0.29,  # Bronx
                    "10301": 0.30   # Staten Island
                },
                "solar_potential": {
                    "10025": 0.78,
                    "11215": 0.85,
                    "11101": 0.82,
                    "10451": 0.75,
                    "10301": 0.80
                },
                "borough_performance": {
                    "Manhattan": {"conversion_rate": 0.91, "avg_value": 248},
                    "Brooklyn": {"conversion_rate": 0.88, "avg_value": 198},
                    "Queens": {"conversion_rate": 0.84, "avg_value": 175},
                    "Bronx": {"conversion_rate": 0.78, "avg_value": 165},
                    "Staten Island": {"conversion_rate": 0.80, "avg_value": 180}
                }
            }
            
        except Exception as e:
            logger.error("Error loading NYC market data", error=str(e))
    
    async def _start_capacity_monitoring(self):
        """Start background monitoring of platform capacities"""
        async def monitor():
            while True:
                try:
                    await self._update_platform_capacities()
                    await asyncio.sleep(60)  # Update every minute
                except Exception as e:
                    logger.error("Error in capacity monitoring", error=str(e))
                    await asyncio.sleep(60)
        
        asyncio.create_task(monitor())
    
    async def _update_platform_capacities(self):
        """Update platform capacity data"""
        for platform_code, capacity in self.platform_capacities.items():
            try:
                # Get current daily count from Redis
                daily_count = await self.redis.get(f"platform_daily_count:{platform_code}") or 0
                daily_count = int(daily_count)
                
                # Update utilization
                capacity.current_utilization = daily_count / capacity.max_capacity
                capacity.available_slots = capacity.max_capacity - daily_count
                
            except Exception as e:
                logger.error("Error updating platform capacity", platform_code=platform_code, error=str(e))
    
    async def route_lead(
        self, 
        lead: Lead, 
        strategy: RoutingStrategy = RoutingStrategy.REVENUE_MAXIMIZATION,
        priority: LeadPriority = LeadPriority.NORMAL,
        constraints: Dict[str, Any] = None
    ) -> RoutingDecision:
        """Route a lead to the optimal B2B platform"""
        
        try:
            # Apply routing rules
            applicable_rules = self._get_applicable_rules(lead, strategy)
            
            # Get available platforms
            available_platforms = await self._get_available_platforms(lead, constraints)
            
            if not available_platforms:
                raise ValueError("No available platforms for lead routing")
            
            # Calculate routing scores for each platform
            platform_scores = []
            for platform_code in available_platforms:
                score = await self._calculate_routing_score(
                    lead, platform_code, strategy, applicable_rules
                )
                platform_scores.append((platform_code, score))
            
            # Sort by score (highest first)
            platform_scores.sort(key=lambda x: x[1]["total_score"], reverse=True)
            
            # Select best platform
            best_platform = platform_scores[0][0]
            best_score = platform_scores[0][1]
            
            # Create routing decision
            decision = RoutingDecision(
                platform_code=best_platform,
                confidence_score=best_score["total_score"],
                reasoning=best_score["reasoning"],
                estimated_revenue=best_score["estimated_revenue"],
                estimated_delivery_time=best_score["estimated_delivery_time"],
                risk_factors=best_score["risk_factors"],
                alternative_platforms=[p[0] for p in platform_scores[1:3]]  # Top 2 alternatives
            )
            
            # Update metrics
            self.total_routing_decisions += 1
            self.successful_routes += 1
            self.revenue_optimized += decision.estimated_revenue
            
            # Store routing history
            self.routing_history.append({
                "lead_id": str(lead.id),
                "platform": best_platform,
                "strategy": strategy.value,
                "confidence": decision.confidence_score,
                "revenue": decision.estimated_revenue,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(
                "Lead routed successfully",
                lead_id=str(lead.id),
                platform=best_platform,
                strategy=strategy.value,
                confidence=decision.confidence_score,
                estimated_revenue=decision.estimated_revenue
            )
            
            return decision
            
        except Exception as e:
            logger.error("Error routing lead", lead_id=str(lead.id), error=str(e))
            raise
    
    def _get_applicable_rules(self, lead: Lead, strategy: RoutingStrategy) -> List[RoutingRule]:
        """Get routing rules applicable to the lead"""
        applicable_rules = []
        
        for rule in self.routing_rules:
            if not rule.is_active:
                continue
            
            # Check if rule conditions match lead
            if self._evaluate_rule_condition(lead, rule.condition):
                applicable_rules.append(rule)
        
        # Sort by priority (highest first)
        applicable_rules.sort(key=lambda x: x.priority, reverse=True)
        
        return applicable_rules
    
    def _evaluate_rule_condition(self, lead: Lead, condition: Dict[str, Any]) -> bool:
        """Evaluate if a rule condition matches the lead"""
        try:
            for field, criteria in condition.items():
                if field == "lead_quality":
                    if isinstance(criteria, str):
                        if lead.lead_quality != criteria:
                            return False
                    elif isinstance(criteria, list):
                        if lead.lead_quality not in criteria:
                            return False
                
                elif field == "lead_score":
                    if "min" in criteria and lead.lead_score < criteria["min"]:
                        return False
                    if "max" in criteria and lead.lead_score > criteria["max"]:
                        return False
                
                elif field == "estimated_value":
                    if "min" in criteria and (lead.estimated_value or 0) < criteria["min"]:
                        return False
                    if "max" in criteria and (lead.estimated_value or 0) > criteria["max"]:
                        return False
                
                elif field == "zip_code":
                    if "in" in criteria and lead.zip_code not in criteria["in"]:
                        return False
                    if "equals" in criteria and lead.zip_code != criteria["equals"]:
                        return False
                
                elif field == "exclusive_platform":
                    # This would check if lead has exclusive platform requirement
                    pass
            
            return True
            
        except Exception as e:
            logger.error("Error evaluating rule condition", error=str(e))
            return False
    
    async def _get_available_platforms(
        self, 
        lead: Lead, 
        constraints: Dict[str, Any] = None
    ) -> List[str]:
        """Get list of available platforms for lead routing"""
        
        available_platforms = []
        
        for platform_code, capacity in self.platform_capacities.items():
            # Check if platform is accepting leads
            if not capacity.health_status == "healthy":
                continue
            
            # Check capacity
            if capacity.available_slots <= 0:
                continue
            
            # Check quality requirements
            if not self._meets_quality_requirements(lead, capacity.quality_requirements):
                continue
            
            # Check constraints
            if constraints:
                if "excluded_platforms" in constraints:
                    if platform_code in constraints["excluded_platforms"]:
                        continue
                
                if "preferred_platforms" in constraints:
                    if constraints["preferred_platforms"] and platform_code not in constraints["preferred_platforms"]:
                        continue
            
            available_platforms.append(platform_code)
        
        return available_platforms
    
    def _meets_quality_requirements(self, lead: Lead, requirements: Dict[str, Any]) -> bool:
        """Check if lead meets platform quality requirements"""
        try:
            if "min_lead_score" in requirements:
                if lead.lead_score < requirements["min_lead_score"]:
                    return False
            
            if "min_estimated_value" in requirements:
                if (lead.estimated_value or 0) < requirements["min_estimated_value"]:
                    return False
            
            if "required_quality_tiers" in requirements:
                if lead.lead_quality not in requirements["required_quality_tiers"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Error checking quality requirements", error=str(e))
            return False
    
    async def _calculate_routing_score(
        self, 
        lead: Lead, 
        platform_code: str, 
        strategy: RoutingStrategy,
        applicable_rules: List[RoutingRule]
    ) -> Dict[str, Any]:
        """Calculate routing score for a platform"""
        
        try:
            capacity = self.platform_capacities[platform_code]
            score_components = {}
            reasoning = []
            risk_factors = []
            
            # Revenue component (40% weight)
            base_revenue = lead.estimated_value or 0
            net_revenue = base_revenue * (1 - capacity.revenue_share)
            revenue_score = min(net_revenue / 300, 1.0)  # Normalize to 0-1
            score_components["revenue"] = revenue_score * 0.4
            reasoning.append(f"Revenue potential: ${net_revenue:.2f}")
            
            # Platform performance component (25% weight)
            performance_score = capacity.success_rate * (1 - min(capacity.avg_response_time / 30000, 1))
            score_components["performance"] = performance_score * 0.25
            reasoning.append(f"Platform performance: {capacity.success_rate:.1%} success rate")
            
            # Capacity utilization component (15% weight)
            utilization_score = 1 - capacity.current_utilization
            score_components["capacity"] = utilization_score * 0.15
            reasoning.append(f"Capacity utilization: {capacity.current_utilization:.1%}")
            
            # NYC market optimization component (10% weight)
            nyc_score = 0.0
            if lead.zip_code in self.nyc_market_data.get("high_value_zip_codes", []):
                nyc_score = 0.1
                reasoning.append("High-value NYC zip code")
            
            if lead.borough in self.nyc_market_data.get("borough_performance", {}):
                borough_data = self.nyc_market_data["borough_performance"][lead.borough]
                nyc_score += borough_data["conversion_rate"] * 0.05
                reasoning.append(f"Borough performance: {lead.borough}")
            
            score_components["nyc_optimization"] = nyc_score
            
            # Rule-based component (10% weight)
            rule_score = 0.0
            for rule in applicable_rules:
                if platform_code in rule.action.get("preferred_platforms", []):
                    rule_score += 0.1
                    reasoning.append(f"Rule match: {rule.name}")
            
            score_components["rules"] = rule_score
            
            # Calculate total score
            total_score = sum(score_components.values())
            
            # Identify risk factors
            if capacity.current_utilization > 0.9:
                risk_factors.append("High capacity utilization")
            
            if capacity.success_rate < 0.8:
                risk_factors.append("Low success rate")
            
            if capacity.avg_response_time > 20000:  # 20 seconds
                risk_factors.append("Slow response time")
            
            if capacity.health_status != "healthy":
                risk_factors.append("Platform health issues")
            
            return {
                "total_score": total_score,
                "components": score_components,
                "reasoning": reasoning,
                "risk_factors": risk_factors,
                "estimated_revenue": net_revenue,
                "estimated_delivery_time": capacity.avg_response_time
            }
            
        except Exception as e:
            logger.error("Error calculating routing score", platform_code=platform_code, error=str(e))
            return {
                "total_score": 0.0,
                "components": {},
                "reasoning": ["Error calculating score"],
                "risk_factors": ["Calculation error"],
                "estimated_revenue": 0.0,
                "estimated_delivery_time": 0
            }
    
    async def optimize_routing_strategy(self, time_period: str = "7d") -> Dict[str, Any]:
        """Analyze and optimize routing strategy based on historical data"""
        
        try:
            # Analyze routing history
            recent_routes = [
                route for route in self.routing_history
                if datetime.fromisoformat(route["timestamp"]) > datetime.utcnow() - timedelta(days=7)
            ]
            
            # Calculate platform performance
            platform_performance = {}
            for route in recent_routes:
                platform = route["platform"]
                if platform not in platform_performance:
                    platform_performance[platform] = {
                        "total_routes": 0,
                        "total_revenue": 0.0,
                        "avg_confidence": 0.0,
                        "success_rate": 0.0
                    }
                
                platform_performance[platform]["total_routes"] += 1
                platform_performance[platform]["total_revenue"] += route["revenue"]
                platform_performance[platform]["avg_confidence"] += route["confidence"]
            
            # Calculate averages
            for platform, data in platform_performance.items():
                if data["total_routes"] > 0:
                    data["avg_revenue"] = data["total_revenue"] / data["total_routes"]
                    data["avg_confidence"] = data["avg_confidence"] / data["total_routes"]
            
            # Generate optimization recommendations
            recommendations = []
            
            # Find underperforming platforms
            avg_revenue = sum(p["avg_revenue"] for p in platform_performance.values()) / len(platform_performance)
            for platform, data in platform_performance.items():
                if data["avg_revenue"] < avg_revenue * 0.8:
                    recommendations.append({
                        "type": "platform_optimization",
                        "platform": platform,
                        "issue": "Below average revenue per lead",
                        "suggestion": "Review quality requirements and pricing"
                    })
            
            # Find overutilized platforms
            for platform_code, capacity in self.platform_capacities.items():
                if capacity.current_utilization > 0.9:
                    recommendations.append({
                        "type": "capacity_management",
                        "platform": platform_code,
                        "issue": "High capacity utilization",
                        "suggestion": "Consider load balancing or capacity increase"
                    })
            
            return {
                "platform_performance": platform_performance,
                "recommendations": recommendations,
                "total_routes_analyzed": len(recent_routes),
                "analysis_period": time_period
            }
            
        except Exception as e:
            logger.error("Error optimizing routing strategy", error=str(e))
            return {"error": str(e)}
    
    async def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing engine performance metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "total_routing_decisions": self.total_routing_decisions,
            "successful_routes": self.successful_routes,
            "success_rate": self.successful_routes / self.total_routing_decisions if self.total_routing_decisions > 0 else 0,
            "revenue_optimized": self.revenue_optimized,
            "uptime_seconds": uptime,
            "active_rules": len([r for r in self.routing_rules if r.is_active]),
            "platform_capacities": {
                code: {
                    "utilization": capacity.current_utilization,
                    "available_slots": capacity.available_slots,
                    "success_rate": capacity.success_rate,
                    "health_status": capacity.health_status
                }
                for code, capacity in self.platform_capacities.items()
            }
        }
