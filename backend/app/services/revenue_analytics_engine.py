"""
Revenue Analytics Engine for Aurum Solar
Real-time revenue dashboards, forecasting, and optimization recommendations
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
from app.services.revenue_optimization_engine import LeadQualityTier
from app.services.conversation_revenue_tracker import ConversationRevenueState


@dataclass
class RevenueDashboard:
    """Real-time revenue dashboard data"""
    current_hour_revenue: float
    today_revenue: float
    week_revenue: float
    month_revenue: float
    active_conversations: int
    conversion_rate: float
    avg_revenue_per_conversation: float
    revenue_per_hour: float
    top_performing_buyers: List[Tuple[str, float]]  # (buyer_id, revenue)
    quality_tier_distribution: Dict[str, int]
    revenue_trend: List[Tuple[datetime, float]]  # (timestamp, revenue)
    alerts: List[str]


@dataclass
class RevenueForecast:
    """Revenue forecasting data"""
    forecast_period: str  # "hourly", "daily", "weekly", "monthly"
    forecast_data: List[Tuple[datetime, float, float]]  # (timestamp, predicted, confidence)
    accuracy_score: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    seasonal_factors: Dict[str, float]
    market_conditions: Dict[str, Any]


@dataclass
class OptimizationRecommendation:
    """Revenue optimization recommendation"""
    recommendation_id: str
    priority: str  # "high", "medium", "low"
    category: str  # "conversation", "routing", "pricing", "quality"
    title: str
    description: str
    expected_impact: float  # Expected revenue increase
    implementation_effort: str  # "low", "medium", "high"
    time_to_implement: str  # "immediate", "1-3 days", "1-2 weeks"
    action_items: List[str]
    success_metrics: List[str]
    created_at: datetime


@dataclass
class PerformanceBenchmark:
    """Performance benchmarking data"""
    metric_name: str
    current_value: float
    benchmark_value: float
    industry_average: float
    performance_vs_benchmark: float  # Percentage
    performance_vs_industry: float  # Percentage
    trend: str  # "improving", "declining", "stable"
    recommendation: str


class RevenueAnalyticsEngine:
    """Revenue analytics and optimization engine"""
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.analytics_cache = {}
        self.forecast_models = {}
        
        # Start background tasks
        asyncio.create_task(self._update_dashboard_data())
        asyncio.create_task(self._generate_forecasts())
        asyncio.create_task(self._analyze_optimization_opportunities())
    
    async def get_revenue_dashboard(self) -> RevenueDashboard:
        """Get real-time revenue dashboard data"""
        
        try:
            # Get current time periods
            now = datetime.utcnow()
            current_hour_start = now.replace(minute=0, second=0, microsecond=0)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())
            month_start = today_start.replace(day=1)
            
            # Calculate revenue for different periods
            current_hour_revenue = await self._calculate_period_revenue(current_hour_start, now)
            today_revenue = await self._calculate_period_revenue(today_start, now)
            week_revenue = await self._calculate_period_revenue(week_start, now)
            month_revenue = await self._calculate_period_revenue(month_start, now)
            
            # Get active conversations
            active_conversations = await self._get_active_conversations_count()
            
            # Calculate conversion rate
            conversion_rate = await self._calculate_conversion_rate(today_start, now)
            
            # Calculate average revenue per conversation
            conversations_today = await self._get_conversations_count(today_start, now)
            avg_revenue_per_conversation = today_revenue / conversations_today if conversations_today > 0 else 0
            
            # Calculate revenue per hour
            hours_elapsed = (now - today_start).total_seconds() / 3600
            revenue_per_hour = today_revenue / hours_elapsed if hours_elapsed > 0 else 0
            
            # Get top performing buyers
            top_performing_buyers = await self._get_top_performing_buyers(today_start, now)
            
            # Get quality tier distribution
            quality_tier_distribution = await self._get_quality_tier_distribution(today_start, now)
            
            # Get revenue trend
            revenue_trend = await self._get_revenue_trend(now - timedelta(days=7), now)
            
            # Generate alerts
            alerts = await self._generate_revenue_alerts(
                current_hour_revenue,
                today_revenue,
                conversion_rate,
                revenue_per_hour
            )
            
            return RevenueDashboard(
                current_hour_revenue=current_hour_revenue,
                today_revenue=today_revenue,
                week_revenue=week_revenue,
                month_revenue=month_revenue,
                active_conversations=active_conversations,
                conversion_rate=conversion_rate,
                avg_revenue_per_conversation=avg_revenue_per_conversation,
                revenue_per_hour=revenue_per_hour,
                top_performing_buyers=top_performing_buyers,
                quality_tier_distribution=quality_tier_distribution,
                revenue_trend=revenue_trend,
                alerts=alerts
            )
            
        except Exception as e:
            print(f"Error getting revenue dashboard: {e}")
            return RevenueDashboard(
                current_hour_revenue=0.0,
                today_revenue=0.0,
                week_revenue=0.0,
                month_revenue=0.0,
                active_conversations=0,
                conversion_rate=0.0,
                avg_revenue_per_conversation=0.0,
                revenue_per_hour=0.0,
                top_performing_buyers=[],
                quality_tier_distribution={},
                revenue_trend=[],
                alerts=[]
            )
    
    async def _calculate_period_revenue(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate revenue for a specific time period"""
        
        try:
            # Query B2B lead exports for the period
            lead_exports = self.db.query(B2BLeadExport).filter(
                B2BLeadExport.exported_at >= start_date,
                B2BLeadExport.exported_at <= end_date
            ).all()
            
            # Calculate total revenue
            total_revenue = sum(export.expected_revenue for export in lead_exports)
            
            return total_revenue
            
        except Exception as e:
            print(f"Error calculating period revenue: {e}")
            return 0.0
    
    async def _get_active_conversations_count(self) -> int:
        """Get count of active conversations"""
        
        try:
            # Query Redis for active conversation sessions
            pattern = "conversation_revenue:*"
            keys = self.redis_client.keys(pattern)
            return len(keys)
            
        except Exception as e:
            print(f"Error getting active conversations count: {e}")
            return 0
    
    async def _calculate_conversion_rate(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate conversion rate for a period"""
        
        try:
            # Query conversations for the period
            conversations = self.db.query(LeadConversation).filter(
                LeadConversation.started_at >= start_date,
                LeadConversation.started_at <= end_date
            ).all()
            
            if not conversations:
                return 0.0
            
            # Calculate conversion rate
            successful_conversions = sum(1 for conv in conversations if conv.conversion_success)
            conversion_rate = successful_conversions / len(conversations)
            
            return conversion_rate
            
        except Exception as e:
            print(f"Error calculating conversion rate: {e}")
            return 0.0
    
    async def _get_conversations_count(self, start_date: datetime, end_date: datetime) -> int:
        """Get count of conversations for a period"""
        
        try:
            count = self.db.query(LeadConversation).filter(
                LeadConversation.started_at >= start_date,
                LeadConversation.started_at <= end_date
            ).count()
            
            return count
            
        except Exception as e:
            print(f"Error getting conversations count: {e}")
            return 0
    
    async def _get_top_performing_buyers(self, start_date: datetime, end_date: datetime) -> List[Tuple[str, float]]:
        """Get top performing buyers by revenue"""
        
        try:
            # Query lead exports grouped by buyer
            lead_exports = self.db.query(B2BLeadExport).filter(
                B2BLeadExport.exported_at >= start_date,
                B2BLeadExport.exported_at <= end_date
            ).all()
            
            # Group by buyer and calculate revenue
            buyer_revenue = {}
            for export in lead_exports:
                buyer_id = export.buyer_id
                if buyer_id not in buyer_revenue:
                    buyer_revenue[buyer_id] = 0
                buyer_revenue[buyer_id] += export.expected_revenue
            
            # Sort by revenue
            sorted_buyers = sorted(buyer_revenue.items(), key=lambda x: x[1], reverse=True)
            
            return sorted_buyers[:5]  # Top 5 buyers
            
        except Exception as e:
            print(f"Error getting top performing buyers: {e}")
            return []
    
    async def _get_quality_tier_distribution(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get quality tier distribution for a period"""
        
        try:
            # Query conversations for quality tier distribution
            conversations = self.db.query(LeadConversation).filter(
                LeadConversation.started_at >= start_date,
                LeadConversation.started_at <= end_date
            ).all()
            
            distribution = {}
            for conv in conversations:
                tier = conv.quality_tier
                distribution[tier] = distribution.get(tier, 0) + 1
            
            return distribution
            
        except Exception as e:
            print(f"Error getting quality tier distribution: {e}")
            return {}
    
    async def _get_revenue_trend(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, float]]:
        """Get revenue trend data"""
        
        try:
            # Get daily revenue for the period
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                daily_revenue = await self._calculate_period_revenue(current_date, next_date)
                trend_data.append((current_date, daily_revenue))
                current_date = next_date
            
            return trend_data
            
        except Exception as e:
            print(f"Error getting revenue trend: {e}")
            return []
    
    async def _generate_revenue_alerts(
        self,
        current_hour_revenue: float,
        today_revenue: float,
        conversion_rate: float,
        revenue_per_hour: float
    ) -> List[str]:
        """Generate revenue alerts based on performance"""
        
        alerts = []
        
        # Low revenue alerts
        if current_hour_revenue < 50:  # Less than $50 this hour
            alerts.append("Low revenue this hour - consider increasing conversation volume")
        
        if today_revenue < 500:  # Less than $500 today
            alerts.append("Daily revenue below target - review conversation quality")
        
        # Conversion rate alerts
        if conversion_rate < 0.6:  # Less than 60% conversion
            alerts.append("Conversion rate below target - review qualification process")
        
        # Revenue per hour alerts
        if revenue_per_hour < 25:  # Less than $25/hour
            alerts.append("Revenue per hour below target - optimize conversation efficiency")
        
        # High performance alerts
        if current_hour_revenue > 200:  # More than $200 this hour
            alerts.append("High revenue this hour - excellent performance!")
        
        if conversion_rate > 0.8:  # More than 80% conversion
            alerts.append("High conversion rate - maintain current approach")
        
        return alerts
    
    async def generate_revenue_forecast(
        self,
        forecast_period: str = "daily",
        days_ahead: int = 7
    ) -> RevenueForecast:
        """Generate revenue forecast"""
        
        try:
            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)  # Last 30 days
            
            historical_data = await self._get_revenue_trend(start_date, end_date)
            
            if not historical_data:
                return RevenueForecast(
                    forecast_period=forecast_period,
                    forecast_data=[],
                    accuracy_score=0.0,
                    trend_direction="unknown",
                    seasonal_factors={},
                    market_conditions={}
                )
            
            # Generate forecast using simple linear regression
            forecast_data = self._generate_linear_forecast(historical_data, days_ahead)
            
            # Calculate accuracy score (based on recent performance)
            accuracy_score = self._calculate_forecast_accuracy(historical_data)
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(historical_data)
            
            # Calculate seasonal factors
            seasonal_factors = self._calculate_seasonal_factors(historical_data)
            
            # Get market conditions
            market_conditions = await self._get_market_conditions()
            
            return RevenueForecast(
                forecast_period=forecast_period,
                forecast_data=forecast_data,
                accuracy_score=accuracy_score,
                trend_direction=trend_direction,
                seasonal_factors=seasonal_factors,
                market_conditions=market_conditions
            )
            
        except Exception as e:
            print(f"Error generating revenue forecast: {e}")
            return RevenueForecast(
                forecast_period=forecast_period,
                forecast_data=[],
                accuracy_score=0.0,
                trend_direction="unknown",
                seasonal_factors={},
                market_conditions={}
            )
    
    def _generate_linear_forecast(
        self, 
        historical_data: List[Tuple[datetime, float]], 
        days_ahead: int
    ) -> List[Tuple[datetime, float, float]]:
        """Generate linear forecast using historical data"""
        
        if len(historical_data) < 2:
            return []
        
        # Extract dates and values
        dates = [item[0] for item in historical_data]
        values = [item[1] for item in historical_data]
        
        # Convert dates to numeric values (days since first date)
        first_date = dates[0]
        numeric_dates = [(date - first_date).days for date in dates]
        
        # Calculate linear regression
        n = len(numeric_dates)
        sum_x = sum(numeric_dates)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(numeric_dates, values))
        sum_x2 = sum(x * x for x in numeric_dates)
        
        # Calculate slope and intercept
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Generate forecast
        forecast_data = []
        last_date = dates[-1]
        
        for i in range(1, days_ahead + 1):
            forecast_date = last_date + timedelta(days=i)
            forecast_value = intercept + slope * (numeric_dates[-1] + i)
            confidence = max(0.1, 1.0 - (i * 0.1))  # Decreasing confidence over time
            
            forecast_data.append((forecast_date, max(0, forecast_value), confidence))
        
        return forecast_data
    
    def _calculate_forecast_accuracy(self, historical_data: List[Tuple[datetime, float]]) -> float:
        """Calculate forecast accuracy based on recent data"""
        
        if len(historical_data) < 7:
            return 0.5  # Default accuracy
        
        # Use last 7 days to calculate accuracy
        recent_data = historical_data[-7:]
        values = [item[1] for item in recent_data]
        
        # Calculate coefficient of variation (lower is better)
        mean_value = np.mean(values)
        std_value = np.std(values)
        
        if mean_value == 0:
            return 0.5
        
        cv = std_value / mean_value
        accuracy = max(0.1, 1.0 - cv)  # Higher accuracy for lower variation
        
        return accuracy
    
    def _determine_trend_direction(self, historical_data: List[Tuple[datetime, float]]) -> str:
        """Determine trend direction from historical data"""
        
        if len(historical_data) < 7:
            return "insufficient_data"
        
        # Compare first half vs second half
        mid_point = len(historical_data) // 2
        first_half = historical_data[:mid_point]
        second_half = historical_data[mid_point:]
        
        first_avg = np.mean([item[1] for item in first_half])
        second_avg = np.mean([item[1] for item in second_half])
        
        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_seasonal_factors(self, historical_data: List[Tuple[datetime, float]]) -> Dict[str, float]:
        """Calculate seasonal factors from historical data"""
        
        if len(historical_data) < 30:
            return {}
        
        # Group by day of week
        weekday_revenue = {}
        for date, revenue in historical_data:
            weekday = date.weekday()
            if weekday not in weekday_revenue:
                weekday_revenue[weekday] = []
            weekday_revenue[weekday].append(revenue)
        
        # Calculate average revenue by day of week
        weekday_avg = {}
        for weekday, revenues in weekday_revenue.items():
            weekday_avg[weekday] = np.mean(revenues)
        
        # Calculate overall average
        overall_avg = np.mean([item[1] for item in historical_data])
        
        # Calculate seasonal factors
        seasonal_factors = {}
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for weekday, avg_revenue in weekday_avg.items():
            factor = avg_revenue / overall_avg if overall_avg > 0 else 1.0
            seasonal_factors[weekday_names[weekday]] = factor
        
        return seasonal_factors
    
    async def _get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions"""
        
        try:
            # This would integrate with external market data in production
            return {
                "solar_market_growth": 0.15,  # 15% annual growth
                "nyc_solar_adoption": 0.12,  # 12% adoption rate
                "incentive_availability": 0.9,  # 90% of incentives available
                "competition_intensity": 0.7,  # 70% competition level
                "economic_conditions": "stable"
            }
            
        except Exception as e:
            print(f"Error getting market conditions: {e}")
            return {}
    
    async def get_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Get revenue optimization recommendations"""
        
        try:
            recommendations = []
            
            # Get current performance metrics
            dashboard = await self.get_revenue_dashboard()
            
            # Generate recommendations based on performance
            if dashboard.conversion_rate < 0.6:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id="improve_conversion_rate",
                    priority="high",
                    category="conversation",
                    title="Improve Conversation Conversion Rate",
                    description=f"Current conversion rate is {dashboard.conversion_rate:.1%}, below target of 60%",
                    expected_impact=0.15,  # 15% revenue increase
                    implementation_effort="medium",
                    time_to_implement="1-2 weeks",
                    action_items=[
                        "Enhance qualification questions",
                        "Improve objection handling",
                        "Add urgency creation techniques",
                        "Optimize conversation flow"
                    ],
                    success_metrics=[
                        "Conversion rate > 60%",
                        "Revenue per conversation > $150",
                        "Qualified lead rate > 80%"
                    ],
                    created_at=datetime.utcnow()
                ))
            
            if dashboard.avg_revenue_per_conversation < 150:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id="increase_revenue_per_conversation",
                    priority="high",
                    category="routing",
                    title="Optimize Lead Routing for Higher Revenue",
                    description=f"Average revenue per conversation is ${dashboard.avg_revenue_per_conversation:.0f}, below target of $150",
                    expected_impact=0.20,  # 20% revenue increase
                    implementation_effort="low",
                    time_to_implement="immediate",
                    action_items=[
                        "Improve buyer routing algorithm",
                        "Implement dynamic pricing",
                        "Optimize lead quality scoring",
                        "Enhance buyer capacity management"
                    ],
                    success_metrics=[
                        "Average revenue per conversation > $150",
                        "Buyer acceptance rate > 85%",
                        "Revenue per hour > $30"
                    ],
                    created_at=datetime.utcnow()
                ))
            
            if dashboard.revenue_per_hour < 25:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id="improve_conversation_efficiency",
                    priority="medium",
                    category="conversation",
                    title="Improve Conversation Efficiency",
                    description=f"Revenue per hour is ${dashboard.revenue_per_hour:.0f}, below target of $25",
                    expected_impact=0.12,  # 12% revenue increase
                    implementation_effort="medium",
                    time_to_implement="1-3 days",
                    action_items=[
                        "Streamline conversation flow",
                        "Add quick qualification questions",
                        "Implement conversation templates",
                        "Optimize response generation"
                    ],
                    success_metrics=[
                        "Revenue per hour > $25",
                        "Average conversation duration < 15 minutes",
                        "Qualification rate > 70%"
                    ],
                    created_at=datetime.utcnow()
                ))
            
            # Add more recommendations based on other metrics
            if len(dashboard.top_performing_buyers) < 3:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id="diversify_buyer_base",
                    priority="medium",
                    category="routing",
                    title="Diversify B2B Buyer Base",
                    description="Limited number of top-performing buyers may create dependency risk",
                    expected_impact=0.08,  # 8% revenue increase
                    implementation_effort="high",
                    time_to_implement="1-2 weeks",
                    action_items=[
                        "Identify new B2B buyers",
                        "Negotiate pricing agreements",
                        "Test buyer performance",
                        "Implement buyer rotation"
                    ],
                    success_metrics=[
                        "Number of active buyers > 5",
                        "Buyer diversity score > 0.7",
                        "Revenue stability > 0.9"
                    ],
                    created_at=datetime.utcnow()
                ))
            
            return recommendations
            
        except Exception as e:
            print(f"Error getting optimization recommendations: {e}")
            return []
    
    async def get_performance_benchmarks(self) -> List[PerformanceBenchmark]:
        """Get performance benchmarks against industry standards"""
        
        try:
            # Get current performance metrics
            dashboard = await self.get_revenue_dashboard()
            
            benchmarks = []
            
            # Conversion rate benchmark
            benchmarks.append(PerformanceBenchmark(
                metric_name="Conversion Rate",
                current_value=dashboard.conversion_rate,
                benchmark_value=0.65,  # Internal benchmark
                industry_average=0.55,  # Industry average
                performance_vs_benchmark=((dashboard.conversion_rate - 0.65) / 0.65) * 100,
                performance_vs_industry=((dashboard.conversion_rate - 0.55) / 0.55) * 100,
                trend="improving" if dashboard.conversion_rate > 0.65 else "declining",
                recommendation="Maintain current approach" if dashboard.conversion_rate > 0.65 else "Improve qualification process"
            ))
            
            # Revenue per conversation benchmark
            benchmarks.append(PerformanceBenchmark(
                metric_name="Revenue per Conversation",
                current_value=dashboard.avg_revenue_per_conversation,
                benchmark_value=150.0,  # Internal benchmark
                industry_average=120.0,  # Industry average
                performance_vs_benchmark=((dashboard.avg_revenue_per_conversation - 150.0) / 150.0) * 100,
                performance_vs_industry=((dashboard.avg_revenue_per_conversation - 120.0) / 120.0) * 100,
                trend="improving" if dashboard.avg_revenue_per_conversation > 150.0 else "declining",
                recommendation="Continue optimization" if dashboard.avg_revenue_per_conversation > 150.0 else "Focus on lead quality"
            ))
            
            # Revenue per hour benchmark
            benchmarks.append(PerformanceBenchmark(
                metric_name="Revenue per Hour",
                current_value=dashboard.revenue_per_hour,
                benchmark_value=30.0,  # Internal benchmark
                industry_average=25.0,  # Industry average
                performance_vs_benchmark=((dashboard.revenue_per_hour - 30.0) / 30.0) * 100,
                performance_vs_industry=((dashboard.revenue_per_hour - 25.0) / 25.0) * 100,
                trend="improving" if dashboard.revenue_per_hour > 30.0 else "declining",
                recommendation="Maintain efficiency" if dashboard.revenue_per_hour > 30.0 else "Improve conversation speed"
            ))
            
            return benchmarks
            
        except Exception as e:
            print(f"Error getting performance benchmarks: {e}")
            return []
    
    async def _update_dashboard_data(self):
        """Background task to update dashboard data"""
        
        while True:
            try:
                # Update dashboard data every 5 minutes
                dashboard = await self.get_revenue_dashboard()
                
                # Cache dashboard data
                cache_key = "revenue_dashboard"
                dashboard_data = asdict(dashboard)
                
                # Convert datetime objects to ISO strings
                dashboard_data["revenue_trend"] = [
                    (timestamp.isoformat(), revenue)
                    for timestamp, revenue in dashboard_data["revenue_trend"]
                ]
                
                self.redis_client.setex(
                    cache_key,
                    300,  # 5 minute cache
                    json.dumps(dashboard_data)
                )
                
                # Wait 5 minutes before next update
                await asyncio.sleep(300)
                
            except Exception as e:
                print(f"Error updating dashboard data: {e}")
                await asyncio.sleep(300)
    
    async def _generate_forecasts(self):
        """Background task to generate revenue forecasts"""
        
        while True:
            try:
                # Generate daily forecast
                daily_forecast = await self.generate_revenue_forecast("daily", 7)
                
                # Cache forecast data
                cache_key = "revenue_forecast_daily"
                forecast_data = asdict(daily_forecast)
                
                # Convert datetime objects to ISO strings
                forecast_data["forecast_data"] = [
                    (timestamp.isoformat(), predicted, confidence)
                    for timestamp, predicted, confidence in forecast_data["forecast_data"]
                ]
                
                self.redis_client.setex(
                    cache_key,
                    3600,  # 1 hour cache
                    json.dumps(forecast_data)
                )
                
                # Wait 1 hour before next forecast
                await asyncio.sleep(3600)
                
            except Exception as e:
                print(f"Error generating forecasts: {e}")
                await asyncio.sleep(3600)
    
    async def _analyze_optimization_opportunities(self):
        """Background task to analyze optimization opportunities"""
        
        while True:
            try:
                # Get optimization recommendations
                recommendations = await self.get_optimization_recommendations()
                
                # Cache recommendations
                cache_key = "optimization_recommendations"
                recommendations_data = [asdict(rec) for rec in recommendations]
                
                # Convert datetime objects to ISO strings
                for rec in recommendations_data:
                    rec["created_at"] = rec["created_at"].isoformat()
                
                self.redis_client.setex(
                    cache_key,
                    1800,  # 30 minute cache
                    json.dumps(recommendations_data)
                )
                
                # Wait 30 minutes before next analysis
                await asyncio.sleep(1800)
                
            except Exception as e:
                print(f"Error analyzing optimization opportunities: {e}")
                await asyncio.sleep(1800)
