"""
Revenue Analytics Service
Comprehensive analytics and optimization for B2B lead revenue generation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
import numpy as np
from collections import defaultdict

from app.models.revenue_analytics import (
    RevenueTransaction, ConversationAnalytics, LeadQualityAnalytics,
    MarketPerformanceAnalytics, RevenueOptimizationInsight, DashboardMetrics
)
from app.models.lead import Lead, LeadConversation
from app.models.ai_models import AIConversation
from app.services.enhanced_b2b_export_service import QualityTier


class MetricPeriod(Enum):
    """Time periods for analytics"""
    REAL_TIME = "real_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class InsightPriority(Enum):
    """Priority levels for optimization insights"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RevenueMetrics:
    """Revenue performance metrics"""
    total_revenue: float
    lead_count: int
    average_revenue_per_lead: float
    conversion_rate: float
    growth_rate: float
    quality_distribution: Dict[str, int]
    platform_performance: Dict[str, float]


@dataclass
class ConversationMetrics:
    """Conversation performance metrics"""
    total_conversations: int
    completion_rate: float
    qualification_rate: float
    average_duration_minutes: float
    revenue_per_conversation: float
    engagement_score: float
    drop_off_stages: Dict[str, int]


@dataclass
class MarketMetrics:
    """NYC market performance metrics"""
    borough_performance: Dict[str, float]
    zip_code_heatmap: Dict[str, Dict[str, Any]]
    seasonal_trends: Dict[str, float]
    competition_impact: Dict[str, float]
    top_performing_areas: List[Dict[str, Any]]


@dataclass
class OptimizationInsight:
    """Revenue optimization insight"""
    insight_type: str
    priority: str
    title: str
    description: str
    potential_impact: float
    confidence: float
    recommendation: str


class RevenueAnalyticsService:
    """Comprehensive revenue analytics and optimization service"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Performance targets
        self.targets = {
            "conversion_rate": 0.60,  # 60% conversation-to-lead conversion
            "avg_revenue_per_lead": 150.0,  # $150 average revenue per lead
            "quality_accuracy": 0.90,  # 90% B2B acceptance rate
            "monthly_growth_rate": 0.50,  # 50% month-over-month growth
            "mrr_target_month_1": 15000.0,  # $15K MRR month 1
            "mrr_target_month_3": 50000.0,  # $50K MRR month 3
        }
    
    async def get_executive_summary(self, period_days: int = 30) -> Dict[str, Any]:
        """Get executive summary with key performance indicators"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get revenue metrics
        revenue_metrics = await self._calculate_revenue_metrics(start_date, end_date)
        
        # Get conversation metrics
        conversation_metrics = await self._calculate_conversation_metrics(start_date, end_date)
        
        # Get market performance
        market_metrics = await self._calculate_market_metrics(start_date, end_date)
        
        # Calculate KPIs
        kpis = self._calculate_kpis(revenue_metrics, conversation_metrics, period_days)
        
        # Get optimization insights
        insights = await self._get_optimization_insights(limit=5)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "revenue_metrics": {
                "total_revenue": revenue_metrics.total_revenue,
                "lead_count": revenue_metrics.lead_count,
                "average_revenue_per_lead": revenue_metrics.average_revenue_per_lead,
                "growth_rate": revenue_metrics.growth_rate,
                "quality_distribution": revenue_metrics.quality_distribution,
                "platform_performance": revenue_metrics.platform_performance
            },
            "conversation_metrics": {
                "total_conversations": conversation_metrics.total_conversations,
                "completion_rate": conversation_metrics.completion_rate,
                "qualification_rate": conversation_metrics.qualification_rate,
                "average_duration_minutes": conversation_metrics.average_duration_minutes,
                "revenue_per_conversation": conversation_metrics.revenue_per_conversation,
                "engagement_score": conversation_metrics.engagement_score
            },
            "market_metrics": {
                "top_performing_boroughs": list(market_metrics.borough_performance.keys())[:3],
                "total_zip_codes_active": len(market_metrics.zip_code_heatmap),
                "seasonal_trend": market_metrics.seasonal_trends.get("current", 0.0)
            },
            "kpis": kpis,
            "optimization_insights": insights,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data for live monitoring"""
        
        # Get today's metrics
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.utcnow()
        
        # Get yesterday's metrics for comparison
        yesterday = today - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(yesterday, datetime.max.time())
        
        # Calculate real-time metrics
        today_metrics = await self._calculate_revenue_metrics(today_start, today_end)
        yesterday_metrics = await self._calculate_revenue_metrics(yesterday_start, yesterday_end)
        
        # Get active conversations
        active_conversations = await self._get_active_conversations()
        
        # Get pipeline value
        pipeline_value = await self._calculate_pipeline_value()
        
        # Get quality tier distribution
        quality_distribution = await self._get_quality_distribution(today_start, today_end)
        
        # Calculate hourly trends
        hourly_trends = await self._get_hourly_trends(today_start, today_end)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "today": {
                "revenue": today_metrics.total_revenue,
                "leads": today_metrics.lead_count,
                "avg_revenue_per_lead": today_metrics.average_revenue_per_lead,
                "conversion_rate": today_metrics.conversion_rate
            },
            "yesterday_comparison": {
                "revenue_change": self._calculate_change_percentage(
                    today_metrics.total_revenue, yesterday_metrics.total_revenue
                ),
                "leads_change": self._calculate_change_percentage(
                    today_metrics.lead_count, yesterday_metrics.lead_count
                ),
                "avg_revenue_change": self._calculate_change_percentage(
                    today_metrics.average_revenue_per_lead, yesterday_metrics.average_revenue_per_lead
                )
            },
            "active_conversations": {
                "count": len(active_conversations),
                "estimated_value": sum(conv.get("estimated_value", 0) for conv in active_conversations),
                "avg_engagement_score": np.mean([conv.get("engagement_score", 0) for conv in active_conversations])
            },
            "pipeline_value": pipeline_value,
            "quality_distribution": quality_distribution,
            "hourly_trends": hourly_trends,
            "performance_vs_targets": {
                "conversion_rate": {
                    "current": today_metrics.conversion_rate,
                    "target": self.targets["conversion_rate"],
                    "status": "above_target" if today_metrics.conversion_rate >= self.targets["conversion_rate"] else "below_target"
                },
                "avg_revenue_per_lead": {
                    "current": today_metrics.average_revenue_per_lead,
                    "target": self.targets["avg_revenue_per_lead"],
                    "status": "above_target" if today_metrics.average_revenue_per_lead >= self.targets["avg_revenue_per_lead"] else "below_target"
                }
            }
        }
    
    async def get_conversation_analytics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get detailed conversation performance analytics"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get conversation metrics
        conversation_metrics = await self._calculate_conversation_metrics(start_date, end_date)
        
        # Get stage performance analysis
        stage_performance = await self._analyze_stage_performance(start_date, end_date)
        
        # Get conversation flow optimization
        flow_optimization = await self._analyze_conversation_flows(start_date, end_date)
        
        # Get agent response effectiveness
        agent_effectiveness = await self._analyze_agent_effectiveness(start_date, end_date)
        
        # Get high-value conversation paths
        high_value_paths = await self._identify_high_value_paths(start_date, end_date)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "overview": {
                "total_conversations": conversation_metrics.total_conversations,
                "completion_rate": conversation_metrics.completion_rate,
                "qualification_rate": conversation_metrics.qualification_rate,
                "average_duration_minutes": conversation_metrics.average_duration_minutes,
                "revenue_per_conversation": conversation_metrics.revenue_per_conversation,
                "engagement_score": conversation_metrics.engagement_score
            },
            "stage_performance": stage_performance,
            "flow_optimization": flow_optimization,
            "agent_effectiveness": agent_effectiveness,
            "high_value_paths": high_value_paths,
            "drop_off_analysis": {
                "stages": conversation_metrics.drop_off_stages,
                "recommendations": await self._get_drop_off_recommendations(conversation_metrics.drop_off_stages)
            },
            "optimization_opportunities": await self._get_conversation_optimization_opportunities(start_date, end_date)
        }
    
    async def get_market_performance(self, period_days: int = 30) -> Dict[str, Any]:
        """Get NYC market performance analytics"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get market metrics
        market_metrics = await self._calculate_market_metrics(start_date, end_date)
        
        # Get zip code heatmap
        zip_code_heatmap = await self._generate_zip_code_heatmap(start_date, end_date)
        
        # Get seasonal trends
        seasonal_trends = await self._analyze_seasonal_trends(period_days)
        
        # Get competition analysis
        competition_analysis = await self._analyze_competition_impact(start_date, end_date)
        
        # Get neighborhood performance
        neighborhood_performance = await self._analyze_neighborhood_performance(start_date, end_date)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "borough_performance": market_metrics.borough_performance,
            "zip_code_heatmap": zip_code_heatmap,
            "seasonal_trends": seasonal_trends,
            "competition_analysis": competition_analysis,
            "neighborhood_performance": neighborhood_performance,
            "top_performing_areas": market_metrics.top_performing_areas,
            "market_opportunities": await self._identify_market_opportunities(start_date, end_date)
        }
    
    async def get_revenue_optimization(self, period_days: int = 30) -> Dict[str, Any]:
        """Get revenue optimization insights and recommendations"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get optimization insights
        insights = await self._get_optimization_insights(limit=10)
        
        # Get lead routing effectiveness
        routing_effectiveness = await self._analyze_lead_routing(start_date, end_date)
        
        # Get quality tier accuracy
        quality_accuracy = await self._analyze_quality_accuracy(start_date, end_date)
        
        # Get B2B buyer performance
        buyer_performance = await self._analyze_buyer_performance(start_date, end_date)
        
        # Get pricing optimization
        pricing_optimization = await self._analyze_pricing_optimization(start_date, end_date)
        
        # Get A/B testing results
        ab_test_results = await self._get_ab_test_results(start_date, end_date)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "insights": insights,
            "routing_effectiveness": routing_effectiveness,
            "quality_accuracy": quality_accuracy,
            "buyer_performance": buyer_performance,
            "pricing_optimization": pricing_optimization,
            "ab_test_results": ab_test_results,
            "optimization_recommendations": await self._generate_optimization_recommendations(
                routing_effectiveness, quality_accuracy, buyer_performance
            )
        }
    
    async def _calculate_revenue_metrics(self, start_date: datetime, end_date: datetime) -> RevenueMetrics:
        """Calculate comprehensive revenue metrics"""
        
        # Get revenue transactions
        transactions = self.db.query(RevenueTransaction).filter(
            and_(
                RevenueTransaction.transaction_date >= start_date,
                RevenueTransaction.transaction_date <= end_date,
                RevenueTransaction.status == "completed"
            )
        ).all()
        
        if not transactions:
            return RevenueMetrics(0, 0, 0, 0, 0, {}, {})
        
        # Calculate basic metrics
        total_revenue = sum(t.amount for t in transactions)
        lead_count = len(set(t.lead_id for t in transactions))
        average_revenue_per_lead = total_revenue / lead_count if lead_count > 0 else 0
        
        # Calculate growth rate (simplified - would need historical comparison)
        growth_rate = 0.0  # Placeholder
        
        # Calculate quality distribution
        quality_distribution = defaultdict(int)
        for t in transactions:
            if t.lead_quality_tier:
                quality_distribution[t.lead_quality_tier] += 1
        
        # Calculate platform performance
        platform_performance = defaultdict(float)
        for t in transactions:
            platform_performance[t.platform] += t.amount
        
        # Calculate conversion rate (simplified)
        total_leads = self.db.query(Lead).filter(
            and_(
                Lead.created_at >= start_date,
                Lead.created_at <= end_date,
                Lead.qualification_status == "qualified"
            )
        ).count()
        
        conversion_rate = lead_count / total_leads if total_leads > 0 else 0
        
        return RevenueMetrics(
            total_revenue=total_revenue,
            lead_count=lead_count,
            average_revenue_per_lead=average_revenue_per_lead,
            conversion_rate=conversion_rate,
            growth_rate=growth_rate,
            quality_distribution=dict(quality_distribution),
            platform_performance=dict(platform_performance)
        )
    
    async def _calculate_conversation_metrics(self, start_date: datetime, end_date: datetime) -> ConversationMetrics:
        """Calculate conversation performance metrics"""
        
        # Get conversation analytics
        conversations = self.db.query(ConversationAnalytics).filter(
            and_(
                ConversationAnalytics.started_at >= start_date,
                ConversationAnalytics.started_at <= end_date
            )
        ).all()
        
        if not conversations:
            return ConversationMetrics(0, 0, 0, 0, 0, 0, {})
        
        # Calculate basic metrics
        total_conversations = len(conversations)
        completed_conversations = [c for c in conversations if c.completed_at]
        qualified_conversations = [c for c in conversations if c.qualification_achieved]
        
        completion_rate = len(completed_conversations) / total_conversations if total_conversations > 0 else 0
        qualification_rate = len(qualified_conversations) / total_conversations if total_conversations > 0 else 0
        
        # Calculate averages
        avg_duration = np.mean([c.conversation_duration_minutes for c in conversations if c.conversation_duration_minutes])
        avg_engagement = np.mean([c.engagement_score for c in conversations if c.engagement_score])
        
        # Calculate revenue per conversation
        total_revenue = sum(c.actual_revenue_generated for c in conversations)
        revenue_per_conversation = total_revenue / total_conversations if total_conversations > 0 else 0
        
        # Calculate drop-off stages
        drop_off_stages = defaultdict(int)
        for c in conversations:
            if c.drop_off_stage:
                drop_off_stages[c.drop_off_stage] += 1
        
        return ConversationMetrics(
            total_conversations=total_conversations,
            completion_rate=completion_rate,
            qualification_rate=qualification_rate,
            average_duration_minutes=avg_duration,
            revenue_per_conversation=revenue_per_conversation,
            engagement_score=avg_engagement,
            drop_off_stages=dict(drop_off_stages)
        )
    
    async def _calculate_market_metrics(self, start_date: datetime, end_date: datetime) -> MarketMetrics:
        """Calculate NYC market performance metrics"""
        
        # Get market performance data
        market_data = self.db.query(MarketPerformanceAnalytics).filter(
            and_(
                MarketPerformanceAnalytics.period_start >= start_date,
                MarketPerformanceAnalytics.period_end <= end_date
            )
        ).all()
        
        if not market_data:
            return MarketMetrics({}, {}, {}, {}, [])
        
        # Calculate borough performance
        borough_performance = defaultdict(float)
        for data in market_data:
            borough_performance[data.borough] += data.total_revenue
        
        # Calculate zip code heatmap (simplified)
        zip_code_heatmap = {}
        for data in market_data:
            zip_code_heatmap[data.zip_code] = {
                "revenue": data.total_revenue,
                "leads": data.total_leads,
                "conversion_rate": data.conversion_rate,
                "borough": data.borough
            }
        
        # Calculate seasonal trends (simplified)
        seasonal_trends = {"current": 0.0, "trend": "stable"}
        
        # Calculate competition impact (simplified)
        competition_impact = {"high": 0.0, "medium": 0.0, "low": 0.0}
        
        # Get top performing areas
        top_performing_areas = sorted(
            market_data,
            key=lambda x: x.total_revenue,
            reverse=True
        )[:5]
        
        top_areas = []
        for area in top_performing_areas:
            top_areas.append({
                "zip_code": area.zip_code,
                "borough": area.borough,
                "revenue": area.total_revenue,
                "leads": area.total_leads,
                "conversion_rate": area.conversion_rate
            })
        
        return MarketMetrics(
            borough_performance=dict(borough_performance),
            zip_code_heatmap=zip_code_heatmap,
            seasonal_trends=seasonal_trends,
            competition_impact=competition_impact,
            top_performing_areas=top_areas
        )
    
    async def _get_active_conversations(self) -> List[Dict[str, Any]]:
        """Get currently active conversations"""
        
        # Get conversations started in last 24 hours without completion
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        active_conversations = self.db.query(ConversationAnalytics).filter(
            and_(
                ConversationAnalytics.started_at >= cutoff_time,
                ConversationAnalytics.completed_at.is_(None)
            )
        ).all()
        
        conversations_data = []
        for conv in active_conversations:
            conversations_data.append({
                "session_id": conv.session_id,
                "lead_id": str(conv.lead_id) if conv.lead_id else None,
                "duration_minutes": conv.conversation_duration_minutes,
                "engagement_score": conv.engagement_score,
                "estimated_value": conv.estimated_lead_value,
                "qualification_stage": conv.qualification_stage_reached,
                "messages_count": conv.total_messages,
                "started_at": conv.started_at.isoformat()
            })
        
        return conversations_data
    
    async def _calculate_pipeline_value(self) -> Dict[str, Any]:
        """Calculate total pipeline value from active conversations and qualified leads"""
        
        # Get active conversations value
        active_conversations = await self._get_active_conversations()
        active_value = sum(conv.get("estimated_value", 0) for conv in active_conversations)
        
        # Get qualified leads not yet exported
        qualified_leads = self.db.query(Lead).filter(
            and_(
                Lead.qualification_status == "qualified",
                Lead.export_status != "exported"
            )
        ).all()
        
        qualified_value = sum(lead.estimated_value or 0 for lead in qualified_leads)
        
        # Get exported leads not yet sold
        exported_leads = self.db.query(Lead).filter(
            and_(
                Lead.export_status == "exported",
                Lead.status != "sold"
            )
        ).all()
        
        exported_value = sum(lead.estimated_value or 0 for lead in exported_leads)
        
        return {
            "active_conversations": {
                "count": len(active_conversations),
                "estimated_value": active_value
            },
            "qualified_leads": {
                "count": len(qualified_leads),
                "estimated_value": qualified_value
            },
            "exported_leads": {
                "count": len(exported_leads),
                "estimated_value": exported_value
            },
            "total_pipeline_value": active_value + qualified_value + exported_value
        }
    
    async def _get_quality_distribution(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get quality tier distribution for the period"""
        
        # Get leads created in period
        leads = self.db.query(Lead).filter(
            and_(
                Lead.created_at >= start_date,
                Lead.created_at <= end_date,
                Lead.qualification_status == "qualified"
            )
        ).all()
        
        quality_distribution = {"premium": 0, "standard": 0, "basic": 0}
        
        for lead in leads:
            if lead.lead_score >= 85:
                quality_distribution["premium"] += 1
            elif lead.lead_score >= 70:
                quality_distribution["standard"] += 1
            elif lead.lead_score >= 50:
                quality_distribution["basic"] += 1
        
        total = sum(quality_distribution.values())
        if total > 0:
            quality_distribution["percentages"] = {
                tier: (count / total) * 100 
                for tier, count in quality_distribution.items()
            }
        
        return quality_distribution
    
    async def _get_hourly_trends(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get hourly performance trends for today"""
        
        hourly_data = []
        
        for hour in range(24):
            hour_start = start_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            # Get leads created in this hour
            leads_count = self.db.query(Lead).filter(
                and_(
                    Lead.created_at >= hour_start,
                    Lead.created_at < hour_end
                )
            ).count()
            
            # Get revenue from this hour
            revenue = self.db.query(func.sum(RevenueTransaction.amount)).filter(
                and_(
                    RevenueTransaction.transaction_date >= hour_start,
                    RevenueTransaction.transaction_date < hour_end,
                    RevenueTransaction.status == "completed"
                )
            ).scalar() or 0
            
            hourly_data.append({
                "hour": hour,
                "leads": leads_count,
                "revenue": revenue,
                "time_label": f"{hour:02d}:00"
            })
        
        return hourly_data
    
    def _calculate_change_percentage(self, current: float, previous: float) -> float:
        """Calculate percentage change between current and previous values"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100
    
    def _calculate_kpis(self, revenue_metrics: RevenueMetrics, conversation_metrics: ConversationMetrics, period_days: int) -> Dict[str, Any]:
        """Calculate key performance indicators vs targets"""
        
        return {
            "conversion_rate": {
                "current": conversation_metrics.qualification_rate,
                "target": self.targets["conversion_rate"],
                "status": "above_target" if conversation_metrics.qualification_rate >= self.targets["conversion_rate"] else "below_target",
                "gap": conversation_metrics.qualification_rate - self.targets["conversion_rate"]
            },
            "avg_revenue_per_lead": {
                "current": revenue_metrics.average_revenue_per_lead,
                "target": self.targets["avg_revenue_per_lead"],
                "status": "above_target" if revenue_metrics.average_revenue_per_lead >= self.targets["avg_revenue_per_lead"] else "below_target",
                "gap": revenue_metrics.average_revenue_per_lead - self.targets["avg_revenue_per_lead"]
            },
            "mrr_projection": {
                "current_monthly_revenue": revenue_metrics.total_revenue * (30 / period_days),
                "target_month_1": self.targets["mrr_target_month_1"],
                "target_month_3": self.targets["mrr_target_month_3"],
                "status": "on_track" if revenue_metrics.total_revenue * (30 / period_days) >= self.targets["mrr_target_month_1"] * 0.8 else "behind_target"
            }
        }
    
    async def _get_optimization_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get optimization insights and recommendations"""
        
        insights = self.db.query(RevenueOptimizationInsight).filter(
            RevenueOptimizationInsight.status == "active"
        ).order_by(
            desc(RevenueOptimizationInsight.potential_revenue_impact)
        ).limit(limit).all()
        
        insights_data = []
        for insight in insights:
            insights_data.append({
                "id": str(insight.id),
                "type": insight.insight_type,
                "priority": insight.priority,
                "title": insight.title,
                "description": insight.description,
                "potential_impact": insight.potential_revenue_impact,
                "confidence": insight.confidence_score,
                "recommendation": insight.recommendation,
                "implementation_effort": insight.implementation_effort,
                "discovered_at": insight.discovered_at.isoformat()
            })
        
        return insights_data
    
    # Additional helper methods would be implemented here for:
    # - _analyze_stage_performance
    # - _analyze_conversation_flows
    # - _analyze_agent_effectiveness
    # - _identify_high_value_paths
    # - _generate_zip_code_heatmap
    # - _analyze_seasonal_trends
    # - _analyze_competition_impact
    # - _analyze_neighborhood_performance
    # - _analyze_lead_routing
    # - _analyze_quality_accuracy
    # - _analyze_buyer_performance
    # - _analyze_pricing_optimization
    # - _get_ab_test_results
    # - And many more specialized analytics methods
    
    async def track_conversation_analytics(self, session_id: str, lead_id: str = None, **kwargs) -> None:
        """Track conversation analytics in real-time"""
        
        try:
            # Create or update conversation analytics
            analytics = self.db.query(ConversationAnalytics).filter(
                ConversationAnalytics.session_id == session_id
            ).first()
            
            if not analytics:
                analytics = ConversationAnalytics(
                    session_id=session_id,
                    lead_id=lead_id
                )
                self.db.add(analytics)
            
            # Update analytics with new data
            for key, value in kwargs.items():
                if hasattr(analytics, key):
                    setattr(analytics, key, value)
            
            analytics.last_activity_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            print(f"Error tracking conversation analytics: {e}")
            self.db.rollback()
    
    async def track_revenue_transaction(self, lead_id: str, platform: str, amount: float, **kwargs) -> None:
        """Track revenue transaction"""
        
        try:
            transaction = RevenueTransaction(
                lead_id=lead_id,
                platform=platform,
                amount=amount,
                transaction_type="lead_sale",
                status="completed",
                transaction_date=datetime.utcnow(),
                **kwargs
            )
            
            self.db.add(transaction)
            self.db.commit()
            
        except Exception as e:
            print(f"Error tracking revenue transaction: {e}")
            self.db.rollback()
    
    async def generate_optimization_insight(self, insight_type: str, title: str, description: str, 
                                          potential_impact: float, recommendation: str, **kwargs) -> None:
        """Generate new optimization insight"""
        
        try:
            insight = RevenueOptimizationInsight(
                insight_type=insight_type,
                insight_category="recommendation",
                priority="medium",
                title=title,
                description=description,
                recommendation=recommendation,
                potential_revenue_impact=potential_impact,
                confidence_score=0.8,
                implementation_effort="medium",
                status="active",
                **kwargs
            )
            
            self.db.add(insight)
            self.db.commit()
            
        except Exception as e:
            print(f"Error generating optimization insight: {e}")
            self.db.rollback()
