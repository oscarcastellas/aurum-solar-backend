"""
Revenue Optimization System for Aurum Solar
Main orchestration system that integrates all revenue optimization engines
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
from app.models.b2b_models import B2BLeadExport, B2BBuyer
from app.services.revenue_optimization_engine import (
    RealTimeLeadScoringEngine, 
    RealTimeLeadScore, 
    LeadQualityTier
)
from app.services.b2b_value_optimizer import B2BValueOptimizer, RoutingDecision
from app.services.conversation_revenue_tracker import ConversationRevenueTracker, ConversationRevenueState
from app.services.quality_feedback_loop import QualityFeedbackLoop, BuyerFeedback
from app.services.revenue_analytics_engine import (
    RevenueAnalyticsEngine, 
    RevenueDashboard, 
    RevenueForecast,
    OptimizationRecommendation
)


@dataclass
class RevenueOptimizationConfig:
    """Revenue optimization system configuration"""
    target_conversion_rate: float = 0.60
    target_avg_lead_value: float = 150.0
    target_revenue_per_hour: float = 30.0
    max_conversation_duration: int = 1800  # 30 minutes
    min_conversation_duration: int = 300   # 5 minutes
    quality_threshold_premium: int = 85
    quality_threshold_standard: int = 70
    quality_threshold_basic: int = 50
    surge_pricing_threshold: float = 0.80
    buyer_capacity_buffer: float = 0.10


@dataclass
class RevenueOptimizationMetrics:
    """Comprehensive revenue optimization metrics"""
    total_conversations: int
    total_revenue: float
    conversion_rate: float
    avg_revenue_per_conversation: float
    revenue_per_hour: float
    quality_tier_distribution: Dict[str, int]
    buyer_performance: Dict[str, Dict[str, float]]
    optimization_score: float
    recommendations_count: int
    alerts_count: int


class RevenueOptimizationSystem:
    """Main revenue optimization system that orchestrates all engines"""
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.config = RevenueOptimizationConfig()
        
        # Initialize all engines
        self.lead_scoring_engine = RealTimeLeadScoringEngine(db, redis_client)
        self.b2b_value_optimizer = B2BValueOptimizer(db, redis_client)
        self.conversation_tracker = ConversationRevenueTracker(db, redis_client)
        self.quality_feedback_loop = QualityFeedbackLoop(db, redis_client)
        self.analytics_engine = RevenueAnalyticsEngine(db, redis_client)
        
        # Start background optimization tasks
        asyncio.create_task(self._optimize_revenue_continuously())
        asyncio.create_task(self._monitor_performance())
        asyncio.create_task(self._update_scoring_algorithms())
    
    async def process_conversation_for_revenue_optimization(
        self,
        session_id: str,
        message: str,
        conversation_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process conversation with full revenue optimization"""
        
        try:
            # Start conversation tracking
            revenue_state = await self.conversation_tracker.start_conversation_tracking(
                session_id, 
                conversation_context.get("lead_id")
            )
            
            # Calculate real-time lead score
            lead_score = await self.lead_scoring_engine.calculate_real_time_score(
                session_id,
                conversation_context,
                conversation_history
            )
            
            # Update conversation revenue state
            conversation_update = {
                "questions_asked": 1 if "?" in message else 0,
                "technical_engagement_score": self._calculate_technical_engagement(message),
                "urgency_created": self._detect_urgency_signals(message),
                "conversation_stage": conversation_context.get("current_stage", "discovery")
            }
            
            updated_revenue_state = await self.conversation_tracker.update_conversation_revenue(
                session_id,
                conversation_update,
                lead_score
            )
            
            # Generate optimization recommendations
            optimization_recommendations = await self._generate_conversation_optimizations(
                updated_revenue_state,
                lead_score
            )
            
            # Check if ready for B2B routing
            routing_decision = None
            if self._is_ready_for_routing(lead_score, conversation_context):
                routing_decision = await self.b2b_value_optimizer.optimize_buyer_routing(
                    conversation_context.get("lead_id", f"lead_{session_id}"),
                    session_id,
                    lead_score.total_score,
                    conversation_context
                )
            
            # Generate response with revenue optimization
            response = await self._generate_optimized_response(
                message,
                conversation_context,
                lead_score,
                updated_revenue_state,
                optimization_recommendations,
                routing_decision
            )
            
            return response
            
        except Exception as e:
            print(f"Error processing conversation for revenue optimization: {e}")
            return {
                "content": "I'd be happy to help you explore solar options for your NYC home. What's your monthly electric bill?",
                "revenue_optimization": {
                    "error": str(e),
                    "fallback": True
                }
            }
    
    def _calculate_technical_engagement(self, message: str) -> float:
        """Calculate technical engagement score from message"""
        
        technical_keywords = [
            "solar panel", "inverter", "battery", "net metering", "incentive",
            "roof", "installation", "permit", "warranty", "efficiency",
            "kwh", "kw", "system size", "production", "savings"
        ]
        
        message_lower = message.lower()
        technical_count = sum(1 for keyword in technical_keywords if keyword in message_lower)
        
        # Normalize to 0-1 scale
        return min(1.0, technical_count / 5.0)
    
    def _detect_urgency_signals(self, message: str) -> bool:
        """Detect urgency signals in message"""
        
        urgency_keywords = [
            "urgent", "asap", "quickly", "soon", "immediately", "deadline",
            "expires", "limited time", "rush", "priority", "fast"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in urgency_keywords)
    
    def _is_ready_for_routing(
        self, 
        lead_score: RealTimeLeadScore, 
        conversation_context: Dict[str, Any]
    ) -> bool:
        """Check if lead is ready for B2B routing"""
        
        # Must have minimum qualification data
        required_fields = ["homeowner_verified", "bill_amount", "zip_code"]
        has_required_data = all(
            conversation_context.get(field) for field in required_fields
        )
        
        # Must meet minimum quality threshold
        meets_quality_threshold = lead_score.total_score >= self.config.quality_threshold_basic
        
        # Must have sufficient conversation engagement
        has_engagement = lead_score.behavioral_score >= 60
        
        return has_required_data and meets_quality_threshold and has_engagement
    
    async def _generate_conversation_optimizations(
        self,
        revenue_state: ConversationRevenueState,
        lead_score: RealTimeLeadScore
    ) -> List[str]:
        """Generate conversation optimization recommendations"""
        
        recommendations = []
        
        # Check conversation duration
        if revenue_state.current_duration < self.config.min_conversation_duration:
            recommendations.append("Ask more qualifying questions to gather essential information")
        
        if revenue_state.current_duration > self.config.max_conversation_duration:
            recommendations.append("Consider moving to qualification completion - conversation is getting long")
        
        # Check technical engagement
        if revenue_state.technical_engagement_score < 0.3:
            recommendations.append("Increase technical engagement by discussing solar system details")
        
        # Check urgency creation
        if not revenue_state.urgency_created and lead_score.total_score >= 70:
            recommendations.append("Create urgency by mentioning 2025 tax credit deadline")
        
        # Check qualification gaps
        if lead_score.total_score < 70:
            recommendations.append("Focus on core qualification: homeowner status, bill amount, timeline")
        
        # Check revenue potential
        if revenue_state.revenue_potential < 100:
            recommendations.append("Improve lead quality to increase revenue potential")
        
        return recommendations
    
    async def _generate_optimized_response(
        self,
        message: str,
        conversation_context: Dict[str, Any],
        lead_score: RealTimeLeadScore,
        revenue_state: ConversationRevenueState,
        optimization_recommendations: List[str],
        routing_decision: Optional[RoutingDecision]
    ) -> Dict[str, Any]:
        """Generate optimized response with revenue optimization data"""
        
        # Base response (this would integrate with the conversation agent)
        base_response = {
            "content": "I'd be happy to help you explore solar options for your NYC home.",
            "next_questions": [
                "What's your monthly electric bill?",
                "Do you own your home?",
                "What's your timeline for installation?"
            ]
        }
        
        # Add revenue optimization data
        revenue_optimization = {
            "lead_score": {
                "total_score": lead_score.total_score,
                "quality_tier": lead_score.quality_tier.value,
                "revenue_potential": lead_score.revenue_potential,
                "conversion_probability": lead_score.conversion_probability
            },
            "conversation_metrics": {
                "duration_minutes": revenue_state.current_duration / 60,
                "revenue_per_minute": revenue_state.revenue_per_minute,
                "technical_engagement": revenue_state.technical_engagement_score,
                "questions_asked": revenue_state.questions_asked
            },
            "optimization_recommendations": optimization_recommendations,
            "routing_decision": asdict(routing_decision) if routing_decision else None,
            "revenue_insights": await self._generate_revenue_insights(lead_score, revenue_state)
        }
        
        return {
            **base_response,
            "revenue_optimization": revenue_optimization
        }
    
    async def _generate_revenue_insights(
        self,
        lead_score: RealTimeLeadScore,
        revenue_state: ConversationRevenueState
    ) -> Dict[str, Any]:
        """Generate revenue insights for the conversation"""
        
        insights = {
            "quality_assessment": f"Lead quality: {lead_score.quality_tier.value} tier",
            "revenue_potential": f"Expected revenue: ${lead_score.revenue_potential:.0f}",
            "conversion_likelihood": f"Conversion probability: {lead_score.conversion_probability:.0%}",
            "optimization_opportunities": len(revenue_state.optimization_recommendations)
        }
        
        # Add specific insights based on score
        if lead_score.total_score >= 85:
            insights["assessment"] = "High-quality lead - focus on closing"
        elif lead_score.total_score >= 70:
            insights["assessment"] = "Good quality lead - continue qualification"
        elif lead_score.total_score >= 50:
            insights["assessment"] = "Fair quality lead - improve qualification"
        else:
            insights["assessment"] = "Low quality lead - basic qualification needed"
        
        return insights
    
    async def submit_buyer_feedback(
        self,
        lead_id: str,
        buyer_id: str,
        feedback_type: str,
        feedback_score: float,
        feedback_reason: str,
        conversion_value: Optional[float] = None,
        buyer_notes: Optional[str] = None
    ) -> BuyerFeedback:
        """Submit buyer feedback for quality improvement"""
        
        return await self.quality_feedback_loop.submit_buyer_feedback(
            lead_id,
            buyer_id,
            feedback_type,
            feedback_score,
            feedback_reason,
            conversion_value,
            buyer_notes
        )
    
    async def get_revenue_dashboard(self) -> RevenueDashboard:
        """Get real-time revenue dashboard"""
        
        return await self.analytics_engine.get_revenue_dashboard()
    
    async def get_revenue_forecast(
        self,
        forecast_period: str = "daily",
        days_ahead: int = 7
    ) -> RevenueForecast:
        """Get revenue forecast"""
        
        return await self.analytics_engine.generate_revenue_forecast(
            forecast_period,
            days_ahead
        )
    
    async def get_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Get revenue optimization recommendations"""
        
        return await self.analytics_engine.get_optimization_recommendations()
    
    async def get_comprehensive_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> RevenueOptimizationMetrics:
        """Get comprehensive revenue optimization metrics"""
        
        try:
            # Get basic metrics
            dashboard = await self.analytics_engine.get_revenue_dashboard()
            
            # Get conversation metrics
            conversation_analytics = await self.conversation_tracker.get_revenue_analytics(
                start_date, end_date
            )
            
            # Get quality feedback analysis
            feedback_analysis = await self.quality_feedback_loop.get_feedback_analysis(
                start_date, end_date
            )
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                dashboard.conversion_rate,
                dashboard.avg_revenue_per_conversation,
                dashboard.revenue_per_hour,
                feedback_analysis.overall_acceptance_rate
            )
            
            # Get buyer performance
            buyer_performance = {}
            for buyer_id, metrics in feedback_analysis.buyer_performance.items():
                buyer_performance[buyer_id] = {
                    "acceptance_rate": metrics.acceptance_rate,
                    "conversion_rate": metrics.conversion_rate,
                    "avg_score": metrics.avg_feedback_score,
                    "avg_value": metrics.avg_conversion_value
                }
            
            return RevenueOptimizationMetrics(
                total_conversations=conversation_analytics.total_conversations,
                total_revenue=conversation_analytics.total_revenue_potential,
                conversion_rate=dashboard.conversion_rate,
                avg_revenue_per_conversation=dashboard.avg_revenue_per_conversation,
                revenue_per_hour=dashboard.revenue_per_hour,
                quality_tier_distribution=dashboard.quality_tier_distribution,
                buyer_performance=buyer_performance,
                optimization_score=optimization_score,
                recommendations_count=len(await self.get_optimization_recommendations()),
                alerts_count=len(dashboard.alerts)
            )
            
        except Exception as e:
            print(f"Error getting comprehensive metrics: {e}")
            return RevenueOptimizationMetrics(
                total_conversations=0,
                total_revenue=0.0,
                conversion_rate=0.0,
                avg_revenue_per_conversation=0.0,
                revenue_per_hour=0.0,
                quality_tier_distribution={},
                buyer_performance={},
                optimization_score=0.0,
                recommendations_count=0,
                alerts_count=0
            )
    
    def _calculate_optimization_score(
        self,
        conversion_rate: float,
        avg_revenue_per_conversation: float,
        revenue_per_hour: float,
        acceptance_rate: float
    ) -> float:
        """Calculate overall optimization score"""
        
        # Weighted combination of key metrics
        score = (
            conversion_rate * 100 * 0.25 +  # 25% weight
            (avg_revenue_per_conversation / 200) * 100 * 0.25 +  # 25% weight
            (revenue_per_hour / 50) * 100 * 0.25 +  # 25% weight
            acceptance_rate * 100 * 0.25  # 25% weight
        )
        
        return min(100.0, score)
    
    async def _optimize_revenue_continuously(self):
        """Background task for continuous revenue optimization"""
        
        while True:
            try:
                # Update lead scoring algorithms based on feedback
                await self._update_scoring_weights()
                
                # Optimize buyer routing
                await self._optimize_buyer_routing()
                
                # Update conversation optimization rules
                await self._update_conversation_optimization_rules()
                
                # Wait 1 hour before next optimization cycle
                await asyncio.sleep(3600)
                
            except Exception as e:
                print(f"Error in continuous revenue optimization: {e}")
                await asyncio.sleep(3600)
    
    async def _monitor_performance(self):
        """Background task to monitor performance and generate alerts"""
        
        while True:
            try:
                # Get current performance metrics
                dashboard = await self.analytics_engine.get_revenue_dashboard()
                
                # Check for performance issues
                if dashboard.conversion_rate < self.config.target_conversion_rate:
                    print(f"ALERT: Conversion rate {dashboard.conversion_rate:.1%} below target {self.config.target_conversion_rate:.1%}")
                
                if dashboard.avg_revenue_per_conversation < self.config.target_avg_lead_value:
                    print(f"ALERT: Avg revenue ${dashboard.avg_revenue_per_conversation:.0f} below target ${self.config.target_avg_lead_value:.0f}")
                
                if dashboard.revenue_per_hour < self.config.target_revenue_per_hour:
                    print(f"ALERT: Revenue per hour ${dashboard.revenue_per_hour:.0f} below target ${self.config.target_revenue_per_hour:.0f}")
                
                # Wait 15 minutes before next monitoring cycle
                await asyncio.sleep(900)
                
            except Exception as e:
                print(f"Error monitoring performance: {e}")
                await asyncio.sleep(900)
    
    async def _update_scoring_algorithms(self):
        """Background task to update scoring algorithms"""
        
        while True:
            try:
                # Get feedback analysis
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=7)
                
                feedback_analysis = await self.quality_feedback_loop.get_feedback_analysis(
                    start_date, end_date
                )
                
                # Update scoring weights based on feedback
                if feedback_analysis.overall_acceptance_rate < 0.8:
                    print("Updating scoring weights based on low acceptance rate")
                    # This would trigger weight adjustments in the scoring engine
                
                # Wait 6 hours before next update
                await asyncio.sleep(21600)
                
            except Exception as e:
                print(f"Error updating scoring algorithms: {e}")
                await asyncio.sleep(21600)
    
    async def _update_scoring_weights(self):
        """Update scoring weights based on performance feedback"""
        
        try:
            # This would implement weight updates based on feedback analysis
            # For now, just log that we're checking for updates
            print("Checking for scoring weight updates...")
            
        except Exception as e:
            print(f"Error updating scoring weights: {e}")
    
    async def _optimize_buyer_routing(self):
        """Optimize buyer routing based on performance data"""
        
        try:
            # This would implement buyer routing optimization
            # For now, just log that we're optimizing routing
            print("Optimizing buyer routing...")
            
        except Exception as e:
            print(f"Error optimizing buyer routing: {e}")
    
    async def _update_conversation_optimization_rules(self):
        """Update conversation optimization rules based on performance"""
        
        try:
            # This would implement conversation rule updates
            # For now, just log that we're updating rules
            print("Updating conversation optimization rules...")
            
        except Exception as e:
            print(f"Error updating conversation optimization rules: {e}")
    
    async def end_conversation_with_revenue_tracking(
        self,
        session_id: str,
        final_revenue: float,
        conversion_success: bool
    ) -> ConversationRevenueState:
        """End conversation with revenue tracking"""
        
        return await self.conversation_tracker.end_conversation_tracking(
            session_id,
            final_revenue,
            conversion_success
        )
