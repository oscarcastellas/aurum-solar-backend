"""
Conversation Revenue Tracker for Aurum Solar
Tracks revenue potential throughout conversations and optimizes for maximum value
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
from app.models.lead import Lead, LeadConversation
from app.services.revenue_optimization_engine import LeadQualityTier, RealTimeLeadScore


@dataclass
class ConversationRevenueState:
    """Real-time conversation revenue state"""
    session_id: str
    lead_id: Optional[str]
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
    conversation_stage: str
    last_activity: datetime
    revenue_trend: List[Tuple[datetime, float]]  # (timestamp, revenue_potential)


@dataclass
class ConversationOptimization:
    """Conversation optimization recommendations"""
    session_id: str
    optimization_type: str  # "increase_engagement", "create_urgency", "handle_objections", etc.
    priority: str  # "high", "medium", "low"
    description: str
    expected_impact: float  # Expected revenue increase
    action_items: List[str]
    created_at: datetime


@dataclass
class RevenueAnalytics:
    """Revenue analytics for conversation optimization"""
    total_conversations: int
    total_revenue_potential: float
    avg_revenue_per_conversation: float
    avg_conversation_duration: float
    conversion_rate: float
    revenue_per_minute: float
    top_performing_stages: List[Tuple[str, float]]  # (stage, avg_revenue)
    optimization_opportunities: List[ConversationOptimization]
    revenue_forecast: Dict[str, float]  # {date: predicted_revenue}


class ConversationRevenueTracker:
    """Tracks and optimizes conversation revenue potential"""
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.active_conversations = {}
        self.revenue_history = []
        self.optimization_rules = self._load_optimization_rules()
        
        # Start background tasks
        asyncio.create_task(self._update_revenue_states())
        asyncio.create_task(self._generate_optimization_recommendations())
    
    def _load_optimization_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load conversation optimization rules"""
        
        return {
            "increase_engagement": {
                "trigger_conditions": {
                    "conversation_duration": {"min": 300, "max": 600},  # 5-10 minutes
                    "questions_asked": {"max": 3},
                    "technical_engagement_score": {"max": 0.3}
                },
                "recommendations": [
                    "Ask more technical questions about solar installation",
                    "Discuss specific NYC solar incentives and savings",
                    "Share local success stories and examples",
                    "Explain the installation process in detail"
                ],
                "expected_impact": 0.15  # 15% revenue increase
            },
            "create_urgency": {
                "trigger_conditions": {
                    "urgency_created": False,
                    "conversation_duration": {"min": 180},  # 3+ minutes
                    "quality_tier": {"min": "standard"}
                },
                "recommendations": [
                    "Mention the 2025 federal tax credit deadline",
                    "Discuss limited NYSERDA rebate funding",
                    "Highlight peak installation season timing",
                    "Reference installer availability constraints"
                ],
                "expected_impact": 0.25  # 25% revenue increase
            },
            "handle_objections": {
                "trigger_conditions": {
                    "objections_handled": {"max": 0},
                    "conversation_duration": {"min": 240},  # 4+ minutes
                    "sentiment_score": {"max": 0.5}
                },
                "recommendations": [
                    "Address cost concerns with specific incentive calculations",
                    "Discuss roof compatibility and installation options",
                    "Explain the permit and installation process",
                    "Provide financing options and payment plans"
                ],
                "expected_impact": 0.30  # 30% revenue increase
            },
            "qualification_gaps": {
                "trigger_conditions": {
                    "conversation_duration": {"min": 300},  # 5+ minutes
                    "missing_qualification": True
                },
                "recommendations": [
                    "Confirm homeownership status",
                    "Gather monthly electric bill amount",
                    "Determine installation timeline",
                    "Assess decision-making authority"
                ],
                "expected_impact": 0.20  # 20% revenue increase
            },
            "technical_credibility": {
                "trigger_conditions": {
                    "technical_engagement_score": {"max": 0.4},
                    "conversation_duration": {"min": 180},  # 3+ minutes
                    "quality_tier": {"min": "basic"}
                },
                "recommendations": [
                    "Share NYC-specific solar market data",
                    "Discuss local installer certifications and experience",
                    "Explain borough-specific permit requirements",
                    "Provide neighborhood-specific success examples"
                ],
                "expected_impact": 0.18  # 18% revenue increase
            }
        }
    
    async def start_conversation_tracking(
        self,
        session_id: str,
        lead_id: Optional[str] = None,
        initial_context: Dict[str, Any] = None
    ) -> ConversationRevenueState:
        """Start tracking conversation revenue potential"""
        
        try:
            # Create initial revenue state
            revenue_state = ConversationRevenueState(
                session_id=session_id,
                lead_id=lead_id,
                start_time=datetime.utcnow(),
                current_duration=0,
                revenue_potential=0.0,
                conversion_probability=0.1,
                quality_tier=LeadQualityTier.UNQUALIFIED,
                questions_asked=0,
                objections_handled=0,
                technical_engagement_score=0.0,
                urgency_created=False,
                revenue_per_minute=0.0,
                optimization_recommendations=[],
                conversation_stage="welcome",
                last_activity=datetime.utcnow(),
                revenue_trend=[]
            )
            
            # Store in active conversations
            self.active_conversations[session_id] = revenue_state
            
            # Cache in Redis
            await self._cache_revenue_state(revenue_state)
            
            return revenue_state
            
        except Exception as e:
            print(f"Error starting conversation tracking: {e}")
            return None
    
    async def update_conversation_revenue(
        self,
        session_id: str,
        conversation_update: Dict[str, Any],
        lead_score: Optional[RealTimeLeadScore] = None
    ) -> ConversationRevenueState:
        """Update conversation revenue state with new data"""
        
        try:
            if session_id not in self.active_conversations:
                # Start tracking if not already started
                await self.start_conversation_tracking(session_id)
            
            revenue_state = self.active_conversations[session_id]
            
            # Update basic metrics
            revenue_state.last_activity = datetime.utcnow()
            revenue_state.current_duration = int(
                (revenue_state.last_activity - revenue_state.start_time).total_seconds()
            )
            
            # Update conversation metrics
            if "questions_asked" in conversation_update:
                revenue_state.questions_asked += conversation_update["questions_asked"]
            
            if "objections_handled" in conversation_update:
                revenue_state.objections_handled += conversation_update["objections_handled"]
            
            if "technical_engagement_score" in conversation_update:
                revenue_state.technical_engagement_score = conversation_update["technical_engagement_score"]
            
            if "urgency_created" in conversation_update:
                revenue_state.urgency_created = conversation_update["urgency_created"]
            
            if "conversation_stage" in conversation_update:
                revenue_state.conversation_stage = conversation_update["conversation_stage"]
            
            # Update revenue potential if lead score provided
            if lead_score:
                revenue_state.revenue_potential = lead_score.revenue_potential
                revenue_state.conversion_probability = lead_score.conversion_probability
                revenue_state.quality_tier = lead_score.quality_tier
                
                # Add to revenue trend
                revenue_state.revenue_trend.append((
                    revenue_state.last_activity,
                    lead_score.revenue_potential
                ))
            
            # Calculate revenue per minute
            if revenue_state.current_duration > 0:
                revenue_state.revenue_per_minute = (
                    revenue_state.revenue_potential / (revenue_state.current_duration / 60)
                )
            
            # Generate optimization recommendations
            await self._generate_revenue_optimizations(revenue_state)
            
            # Update cache
            await self._cache_revenue_state(revenue_state)
            
            return revenue_state
            
        except Exception as e:
            print(f"Error updating conversation revenue: {e}")
            return None
    
    async def _generate_revenue_optimizations(self, revenue_state: ConversationRevenueState):
        """Generate revenue optimization recommendations"""
        
        try:
            recommendations = []
            
            # Check each optimization rule
            for rule_name, rule_config in self.optimization_rules.items():
                if self._check_trigger_conditions(revenue_state, rule_config["trigger_conditions"]):
                    optimization = ConversationOptimization(
                        session_id=revenue_state.session_id,
                        optimization_type=rule_name,
                        priority=self._calculate_priority(rule_config["expected_impact"]),
                        description=f"Optimize {rule_name.replace('_', ' ')}",
                        expected_impact=rule_config["expected_impact"],
                        action_items=rule_config["recommendations"],
                        created_at=datetime.utcnow()
                    )
                    recommendations.append(optimization)
            
            # Sort by expected impact (highest first)
            recommendations.sort(key=lambda x: x.expected_impact, reverse=True)
            
            # Update revenue state with top recommendations
            revenue_state.optimization_recommendations = [
                f"{rec.optimization_type}: {rec.description} (Expected +{rec.expected_impact:.0%} revenue)"
                for rec in recommendations[:3]  # Top 3 recommendations
            ]
            
        except Exception as e:
            print(f"Error generating revenue optimizations: {e}")
    
    def _check_trigger_conditions(
        self, 
        revenue_state: ConversationRevenueState, 
        conditions: Dict[str, Any]
    ) -> bool:
        """Check if optimization rule conditions are met"""
        
        try:
            # Check conversation duration
            if "conversation_duration" in conditions:
                duration_conds = conditions["conversation_duration"]
                if "min" in duration_conds and revenue_state.current_duration < duration_conds["min"]:
                    return False
                if "max" in duration_conds and revenue_state.current_duration > duration_conds["max"]:
                    return False
            
            # Check questions asked
            if "questions_asked" in conditions:
                questions_conds = conditions["questions_asked"]
                if "max" in questions_conds and revenue_state.questions_asked > questions_conds["max"]:
                    return False
            
            # Check technical engagement score
            if "technical_engagement_score" in conditions:
                tech_conds = conditions["technical_engagement_score"]
                if "max" in tech_conds and revenue_state.technical_engagement_score > tech_conds["max"]:
                    return False
            
            # Check urgency created
            if "urgency_created" in conditions:
                if conditions["urgency_created"] != revenue_state.urgency_created:
                    return False
            
            # Check quality tier
            if "quality_tier" in conditions:
                tier_conds = conditions["quality_tier"]
                if "min" in tier_conds:
                    tier_hierarchy = {
                        "unqualified": 0,
                        "basic": 1,
                        "standard": 2,
                        "premium": 3
                    }
                    min_tier_level = tier_hierarchy.get(tier_conds["min"], 0)
                    current_tier_level = tier_hierarchy.get(revenue_state.quality_tier.value, 0)
                    if current_tier_level < min_tier_level:
                        return False
            
            # Check sentiment score (would need to be passed in)
            if "sentiment_score" in conditions:
                # This would need to be calculated from conversation history
                pass
            
            # Check missing qualification
            if "missing_qualification" in conditions and conditions["missing_qualification"]:
                # Check if key qualification data is missing
                if not revenue_state.lead_id:  # No lead ID means incomplete qualification
                    return True
            
            return True
            
        except Exception as e:
            print(f"Error checking trigger conditions: {e}")
            return False
    
    def _calculate_priority(self, expected_impact: float) -> str:
        """Calculate optimization priority based on expected impact"""
        
        if expected_impact >= 0.25:
            return "high"
        elif expected_impact >= 0.15:
            return "medium"
        else:
            return "low"
    
    async def get_conversation_revenue_metrics(
        self,
        session_id: str
    ) -> Optional[ConversationRevenueState]:
        """Get current conversation revenue metrics"""
        
        try:
            # Try to get from active conversations first
            if session_id in self.active_conversations:
                return self.active_conversations[session_id]
            
            # Try to get from Redis cache
            cached_state = await self._get_cached_revenue_state(session_id)
            if cached_state:
                return cached_state
            
            return None
            
        except Exception as e:
            print(f"Error getting conversation revenue metrics: {e}")
            return None
    
    async def end_conversation_tracking(
        self,
        session_id: str,
        final_revenue: float,
        conversion_success: bool
    ) -> ConversationRevenueState:
        """End conversation tracking and store final metrics"""
        
        try:
            if session_id not in self.active_conversations:
                return None
            
            revenue_state = self.active_conversations[session_id]
            
            # Update final metrics
            revenue_state.revenue_potential = final_revenue
            revenue_state.conversion_probability = 1.0 if conversion_success else 0.0
            
            # Store in revenue history
            self.revenue_history.append(revenue_state)
            
            # Store in database
            await self._store_conversation_revenue(revenue_state, conversion_success)
            
            # Remove from active conversations
            del self.active_conversations[session_id]
            
            # Clear Redis cache
            await self._clear_revenue_state_cache(session_id)
            
            return revenue_state
            
        except Exception as e:
            print(f"Error ending conversation tracking: {e}")
            return None
    
    async def _store_conversation_revenue(
        self, 
        revenue_state: ConversationRevenueState, 
        conversion_success: bool
    ):
        """Store conversation revenue data in database"""
        
        try:
            # Store in lead conversation table
            conversation = LeadConversation(
                lead_id=revenue_state.lead_id,
                session_id=revenue_state.session_id,
                conversation_duration=revenue_state.current_duration,
                revenue_potential=revenue_state.revenue_potential,
                conversion_success=conversion_success,
                quality_tier=revenue_state.quality_tier.value,
                questions_asked=revenue_state.questions_asked,
                objections_handled=revenue_state.objections_handled,
                technical_engagement_score=revenue_state.technical_engagement_score,
                urgency_created=revenue_state.urgency_created,
                revenue_per_minute=revenue_state.revenue_per_minute,
                optimization_recommendations=json.dumps(revenue_state.optimization_recommendations),
                conversation_stage=revenue_state.conversation_stage,
                started_at=revenue_state.start_time,
                ended_at=revenue_state.last_activity
            )
            
            self.db.add(conversation)
            self.db.commit()
            
        except Exception as e:
            print(f"Error storing conversation revenue: {e}")
            self.db.rollback()
    
    async def get_revenue_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> RevenueAnalytics:
        """Get comprehensive revenue analytics"""
        
        try:
            # Query conversation data from database
            conversations = self.db.query(LeadConversation).filter(
                LeadConversation.started_at >= start_date,
                LeadConversation.started_at <= end_date
            ).all()
            
            if not conversations:
                return RevenueAnalytics(
                    total_conversations=0,
                    total_revenue_potential=0.0,
                    avg_revenue_per_conversation=0.0,
                    avg_conversation_duration=0.0,
                    conversion_rate=0.0,
                    revenue_per_minute=0.0,
                    top_performing_stages=[],
                    optimization_opportunities=[],
                    revenue_forecast={}
                )
            
            # Calculate basic metrics
            total_conversations = len(conversations)
            total_revenue_potential = sum(conv.revenue_potential for conv in conversations)
            avg_revenue_per_conversation = total_revenue_potential / total_conversations
            
            # Calculate duration metrics
            total_duration = sum(conv.conversation_duration for conv in conversations)
            avg_conversation_duration = total_duration / total_conversations / 60  # minutes
            
            # Calculate conversion rate
            successful_conversions = sum(1 for conv in conversations if conv.conversion_success)
            conversion_rate = successful_conversions / total_conversations
            
            # Calculate revenue per minute
            total_minutes = total_duration / 60
            revenue_per_minute = total_revenue_potential / total_minutes if total_minutes > 0 else 0
            
            # Calculate top performing stages
            stage_revenue = {}
            stage_counts = {}
            for conv in conversations:
                stage = conv.conversation_stage
                if stage not in stage_revenue:
                    stage_revenue[stage] = 0
                    stage_counts[stage] = 0
                stage_revenue[stage] += conv.revenue_potential
                stage_counts[stage] += 1
            
            top_performing_stages = [
                (stage, stage_revenue[stage] / stage_counts[stage])
                for stage in stage_revenue.keys()
            ]
            top_performing_stages.sort(key=lambda x: x[1], reverse=True)
            
            # Generate optimization opportunities
            optimization_opportunities = await self._generate_analytics_optimizations(conversations)
            
            # Generate revenue forecast
            revenue_forecast = await self._generate_revenue_forecast(conversations)
            
            return RevenueAnalytics(
                total_conversations=total_conversations,
                total_revenue_potential=total_revenue_potential,
                avg_revenue_per_conversation=avg_revenue_per_conversation,
                avg_conversation_duration=avg_conversation_duration,
                conversion_rate=conversion_rate,
                revenue_per_minute=revenue_per_minute,
                top_performing_stages=top_performing_stages,
                optimization_opportunities=optimization_opportunities,
                revenue_forecast=revenue_forecast
            )
            
        except Exception as e:
            print(f"Error calculating revenue analytics: {e}")
            return RevenueAnalytics(
                total_conversations=0,
                total_revenue_potential=0.0,
                avg_revenue_per_conversation=0.0,
                avg_conversation_duration=0.0,
                conversion_rate=0.0,
                revenue_per_minute=0.0,
                top_performing_stages=[],
                optimization_opportunities=[],
                revenue_forecast={}
            )
    
    async def _generate_analytics_optimizations(
        self, 
        conversations: List[LeadConversation]
    ) -> List[ConversationOptimization]:
        """Generate optimization opportunities from analytics data"""
        
        optimizations = []
        
        # Find low-performing conversations
        low_revenue_conversations = [
            conv for conv in conversations 
            if conv.revenue_potential < 100 and conv.conversation_duration > 300
        ]
        
        if len(low_revenue_conversations) > len(conversations) * 0.3:  # More than 30% are low revenue
            optimizations.append(ConversationOptimization(
                session_id="analytics",
                optimization_type="increase_engagement",
                priority="high",
                description="30%+ of conversations have low revenue potential",
                expected_impact=0.20,
                action_items=[
                    "Improve qualification questions",
                    "Enhance technical engagement",
                    "Create more urgency"
                ],
                created_at=datetime.utcnow()
            ))
        
        # Find conversations with low technical engagement
        low_tech_conversations = [
            conv for conv in conversations 
            if conv.technical_engagement_score < 0.3
        ]
        
        if len(low_tech_conversations) > len(conversations) * 0.4:  # More than 40% have low tech engagement
            optimizations.append(ConversationOptimization(
                session_id="analytics",
                optimization_type="technical_credibility",
                priority="medium",
                description="40%+ of conversations lack technical engagement",
                expected_impact=0.15,
                action_items=[
                    "Add more technical questions",
                    "Share NYC-specific solar data",
                    "Discuss local installer experience"
                ],
                created_at=datetime.utcnow()
            ))
        
        return optimizations
    
    async def _generate_revenue_forecast(
        self, 
        conversations: List[LeadConversation]
    ) -> Dict[str, float]:
        """Generate revenue forecast based on historical data"""
        
        # Simple linear forecast based on recent trends
        recent_conversations = conversations[-30:]  # Last 30 conversations
        if not recent_conversations:
            return {}
        
        # Calculate daily revenue
        daily_revenue = {}
        for conv in recent_conversations:
            date = conv.started_at.date().isoformat()
            if date not in daily_revenue:
                daily_revenue[date] = 0
            daily_revenue[date] += conv.revenue_potential
        
        # Simple forecast for next 7 days
        dates = sorted(daily_revenue.keys())
        if len(dates) < 2:
            return {}
        
        # Calculate average daily revenue
        avg_daily_revenue = sum(daily_revenue.values()) / len(daily_revenue)
        
        # Generate forecast
        forecast = {}
        last_date = datetime.fromisoformat(dates[-1]).date()
        
        for i in range(1, 8):  # Next 7 days
            forecast_date = last_date + timedelta(days=i)
            forecast[forecast_date.isoformat()] = avg_daily_revenue
        
        return forecast
    
    async def _cache_revenue_state(self, revenue_state: ConversationRevenueState):
        """Cache revenue state in Redis"""
        
        try:
            cache_key = f"conversation_revenue:{revenue_state.session_id}"
            state_data = asdict(revenue_state)
            
            # Convert datetime objects to ISO strings
            state_data["start_time"] = revenue_state.start_time.isoformat()
            state_data["last_activity"] = revenue_state.last_activity.isoformat()
            state_data["revenue_trend"] = [
                (timestamp.isoformat(), revenue) 
                for timestamp, revenue in revenue_state.revenue_trend
            ]
            
            self.redis_client.setex(
                cache_key,
                3600,  # 1 hour cache
                json.dumps(state_data)
            )
            
        except Exception as e:
            print(f"Error caching revenue state: {e}")
    
    async def _get_cached_revenue_state(self, session_id: str) -> Optional[ConversationRevenueState]:
        """Get cached revenue state from Redis"""
        
        try:
            cache_key = f"conversation_revenue:{session_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                
                # Convert ISO strings back to datetime objects
                data["start_time"] = datetime.fromisoformat(data["start_time"])
                data["last_activity"] = datetime.fromisoformat(data["last_activity"])
                data["revenue_trend"] = [
                    (datetime.fromisoformat(timestamp), revenue)
                    for timestamp, revenue in data["revenue_trend"]
                ]
                
                return ConversationRevenueState(**data)
                
        except Exception as e:
            print(f"Error getting cached revenue state: {e}")
        
        return None
    
    async def _clear_revenue_state_cache(self, session_id: str):
        """Clear revenue state cache from Redis"""
        
        try:
            cache_key = f"conversation_revenue:{session_id}"
            self.redis_client.delete(cache_key)
        except Exception as e:
            print(f"Error clearing revenue state cache: {e}")
    
    async def _update_revenue_states(self):
        """Background task to update revenue states"""
        
        while True:
            try:
                for session_id, revenue_state in self.active_conversations.items():
                    # Update duration
                    revenue_state.current_duration = int(
                        (datetime.utcnow() - revenue_state.start_time).total_seconds()
                    )
                    
                    # Update revenue per minute
                    if revenue_state.current_duration > 0:
                        revenue_state.revenue_per_minute = (
                            revenue_state.revenue_potential / (revenue_state.current_duration / 60)
                        )
                    
                    # Update cache
                    await self._cache_revenue_state(revenue_state)
                
                # Wait 30 seconds before next update
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Error updating revenue states: {e}")
                await asyncio.sleep(30)
    
    async def _generate_optimization_recommendations(self):
        """Background task to generate optimization recommendations"""
        
        while True:
            try:
                for session_id, revenue_state in self.active_conversations.items():
                    await self._generate_revenue_optimizations(revenue_state)
                
                # Wait 60 seconds before next update
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"Error generating optimization recommendations: {e}")
                await asyncio.sleep(60)
