"""
Analytics Service for Revenue Tracking and Business Intelligence
Provides real-time metrics, revenue tracking, and performance analytics
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from app.core.database import get_db
from app.models.lead import Lead, LeadConversation, LeadQualityHistory
from app.models.b2b_platforms import B2BPlatform, B2BRevenueTransaction
from app.models.analytics import RevenueMetrics, PlatformPerformance, ConversationMetrics
from app.core.redis import get_redis

logger = structlog.get_logger()

class MetricType(Enum):
    """Types of metrics"""
    REVENUE = "revenue"
    CONVERSATION = "conversation"
    LEAD_QUALITY = "lead_quality"
    B2B_EXPORT = "b2b_export"
    PLATFORM_PERFORMANCE = "platform_performance"

class TimeRange(Enum):
    """Time range for analytics"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

@dataclass
class AnalyticsQuery:
    """Analytics query parameters"""
    metric_type: MetricType
    time_range: TimeRange
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    platform_filter: Optional[str] = None
    quality_tier_filter: Optional[str] = None
    group_by: Optional[str] = None

@dataclass
class AnalyticsResult:
    """Analytics query result"""
    metric_type: str
    time_range: str
    data_points: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: datetime

class AnalyticsService:
    """High-performance analytics service for business intelligence"""
    
    def __init__(self):
        self.redis = None
        self.cache_ttl = 300  # 5 minutes
        self.realtime_metrics = {}
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize analytics service"""
        self.redis = await get_redis()
        await self._start_realtime_metrics_worker()
    
    async def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard"""
        try:
            # Get cached metrics or calculate new ones
            if self.redis:
                cached_metrics = await self.redis.get("realtime_metrics")
                if cached_metrics:
                    return json.loads(cached_metrics)
            
            # Calculate real-time metrics
            metrics = await self._calculate_realtime_metrics()
            
            # Cache results
            if self.redis:
                await self.redis.setex(
                    "realtime_metrics",
                    self.cache_ttl,
                    json.dumps(metrics, default=str)
                )
            
            return metrics
            
        except Exception as e:
            logger.error("Error getting real-time metrics", error=str(e))
            return {}
    
    async def _calculate_realtime_metrics(self) -> Dict[str, Any]:
        """Calculate real-time metrics"""
        try:
            db = next(get_db())
            now = datetime.utcnow()
            today = now.date()
            yesterday = today - timedelta(days=1)
            this_hour = now.replace(minute=0, second=0, microsecond=0)
            last_hour = this_hour - timedelta(hours=1)
            
            # Lead metrics
            total_leads_today = db.query(Lead).filter(
                func.date(Lead.created_at) == today
            ).count()
            
            qualified_leads_today = db.query(Lead).filter(
                and_(
                    func.date(Lead.created_at) == today,
                    Lead.status == "qualified"
                )
            ).count()
            
            # Conversation metrics
            active_conversations = db.query(LeadConversation).filter(
                LeadConversation.created_at >= last_hour
            ).count()
            
            # Revenue metrics
            revenue_today = db.query(func.sum(B2BRevenueTransaction.net_amount)).filter(
                func.date(B2BRevenueTransaction.transaction_date) == today
            ).scalar() or 0
            
            revenue_this_hour = db.query(func.sum(B2BRevenueTransaction.net_amount)).filter(
                B2BRevenueTransaction.transaction_date >= this_hour
            ).scalar() or 0
            
            # Platform performance
            platform_metrics = db.query(
                B2BPlatform.platform_name,
                func.count(B2BRevenueTransaction.id).label('transaction_count'),
                func.sum(B2BRevenueTransaction.net_amount).label('total_revenue')
            ).join(
                B2BRevenueTransaction, B2BPlatform.id == B2BRevenueTransaction.platform_id
            ).filter(
                func.date(B2BRevenueTransaction.transaction_date) == today
            ).group_by(B2BPlatform.platform_name).all()
            
            # Quality distribution
            quality_distribution = db.query(
                Lead.lead_quality,
                func.count(Lead.id).label('count')
            ).filter(
                func.date(Lead.created_at) == today
            ).group_by(Lead.lead_quality).all()
            
            # Conversion rates
            conversion_rate = (qualified_leads_today / total_leads_today * 100) if total_leads_today > 0 else 0
            
            # Average lead score
            avg_lead_score = db.query(func.avg(Lead.lead_score)).filter(
                func.date(Lead.created_at) == today
            ).scalar() or 0
            
            # Response time metrics
            avg_response_time = db.query(func.avg(LeadConversation.response_time_ms)).filter(
                LeadConversation.created_at >= today
            ).scalar() or 0
            
            metrics = {
                "timestamp": now.isoformat(),
                "time_range": "realtime",
                "leads": {
                    "total_today": total_leads_today,
                    "qualified_today": qualified_leads_today,
                    "conversion_rate": round(conversion_rate, 2),
                    "avg_lead_score": round(avg_lead_score, 2)
                },
                "conversations": {
                    "active_last_hour": active_conversations,
                    "avg_response_time_ms": round(avg_response_time, 2)
                },
                "revenue": {
                    "total_today": round(revenue_today, 2),
                    "this_hour": round(revenue_this_hour, 2),
                    "avg_per_lead": round(revenue_today / qualified_leads_today, 2) if qualified_leads_today > 0 else 0
                },
                "platforms": [
                    {
                        "platform": platform,
                        "transactions": count,
                        "revenue": round(revenue, 2)
                    }
                    for platform, count, revenue in platform_metrics
                ],
                "quality_distribution": {
                    quality: count for quality, count in quality_distribution
                },
                "system": {
                    "uptime_seconds": (now - self.start_time).total_seconds(),
                    "cache_hit_rate": await self._get_cache_hit_rate(),
                    "active_connections": await self._get_active_connections()
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error("Error calculating real-time metrics", error=str(e))
            return {}
    
    async def get_revenue_analytics(
        self, 
        time_range: TimeRange = TimeRange.DAY,
        days: int = 30
    ) -> AnalyticsResult:
        """Get revenue analytics for specified time range"""
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            db = next(get_db())
            
            # Revenue by day
            daily_revenue = db.query(
                func.date(B2BRevenueTransaction.transaction_date).label('date'),
                func.sum(B2BRevenueTransaction.net_amount).label('revenue'),
                func.sum(B2BRevenueTransaction.commission_amount).label('commission'),
                func.count(B2BRevenueTransaction.id).label('transactions')
            ).filter(
                B2BRevenueTransaction.transaction_date >= start_date
            ).group_by(
                func.date(B2BRevenueTransaction.transaction_date)
            ).order_by('date').all()
            
            # Revenue by platform
            platform_revenue = db.query(
                B2BPlatform.platform_name,
                func.sum(B2BRevenueTransaction.net_amount).label('revenue'),
                func.count(B2BRevenueTransaction.id).label('transactions'),
                func.avg(B2BRevenueTransaction.net_amount).label('avg_revenue_per_transaction')
            ).join(
                B2BRevenueTransaction, B2BPlatform.id == B2BRevenueTransaction.platform_id
            ).filter(
                B2BRevenueTransaction.transaction_date >= start_date
            ).group_by(B2BPlatform.platform_name).all()
            
            # Revenue by quality tier
            quality_revenue = db.query(
                Lead.lead_quality,
                func.sum(B2BRevenueTransaction.net_amount).label('revenue'),
                func.count(B2BRevenueTransaction.id).label('transactions')
            ).join(
                B2BRevenueTransaction, Lead.id == B2BRevenueTransaction.lead_id
            ).filter(
                B2BRevenueTransaction.transaction_date >= start_date
            ).group_by(Lead.lead_quality).all()
            
            # Calculate summary metrics
            total_revenue = sum(row.revenue for row in daily_revenue)
            total_commission = sum(row.commission for row in daily_revenue)
            total_transactions = sum(row.transactions for row in daily_revenue)
            avg_daily_revenue = total_revenue / len(daily_revenue) if daily_revenue else 0
            
            # Revenue growth
            if len(daily_revenue) >= 2:
                first_half_revenue = sum(row.revenue for row in daily_revenue[:len(daily_revenue)//2])
                second_half_revenue = sum(row.revenue for row in daily_revenue[len(daily_revenue)//2:])
                revenue_growth = ((second_half_revenue - first_half_revenue) / first_half_revenue * 100) if first_half_revenue > 0 else 0
            else:
                revenue_growth = 0
            
            data_points = [
                {
                    "date": row.date.isoformat(),
                    "revenue": float(row.revenue),
                    "commission": float(row.commission),
                    "transactions": row.transactions
                }
                for row in daily_revenue
            ]
            
            summary = {
                "total_revenue": round(total_revenue, 2),
                "total_commission": round(total_commission, 2),
                "total_transactions": total_transactions,
                "avg_daily_revenue": round(avg_daily_revenue, 2),
                "revenue_growth_percent": round(revenue_growth, 2),
                "platforms": [
                    {
                        "platform": row.platform_name,
                        "revenue": round(row.revenue, 2),
                        "transactions": row.transactions,
                        "avg_revenue_per_transaction": round(row.avg_revenue_per_transaction, 2)
                    }
                    for row in platform_revenue
                ],
                "quality_tiers": [
                    {
                        "quality_tier": row.lead_quality,
                        "revenue": round(row.revenue, 2),
                        "transactions": row.transactions
                    }
                    for row in quality_revenue
                ]
            }
            
            return AnalyticsResult(
                metric_type=MetricType.REVENUE.value,
                time_range=time_range.value,
                data_points=data_points,
                summary=summary,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Error getting revenue analytics", error=str(e))
            return AnalyticsResult(
                metric_type=MetricType.REVENUE.value,
                time_range=time_range.value,
                data_points=[],
                summary={},
                generated_at=datetime.utcnow()
            )
    
    async def get_conversation_analytics(
        self, 
        time_range: TimeRange = TimeRange.DAY,
        days: int = 7
    ) -> AnalyticsResult:
        """Get conversation analytics"""
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            db = next(get_db())
            
            # Conversation volume by day
            daily_conversations = db.query(
                func.date(LeadConversation.created_at).label('date'),
                func.count(LeadConversation.id).label('total_messages'),
                func.count(func.distinct(LeadConversation.session_id)).label('unique_sessions'),
                func.avg(LeadConversation.response_time_ms).label('avg_response_time')
            ).filter(
                LeadConversation.created_at >= start_date
            ).group_by(
                func.date(LeadConversation.created_at)
            ).order_by('date').all()
            
            # Message types
            message_types = db.query(
                LeadConversation.message_type,
                func.count(LeadConversation.id).label('count')
            ).filter(
                LeadConversation.created_at >= start_date
            ).group_by(LeadConversation.message_type).all()
            
            # Sentiment analysis
            sentiment_analysis = db.query(
                func.avg(LeadConversation.sentiment_score).label('avg_sentiment'),
                func.min(LeadConversation.sentiment_score).label('min_sentiment'),
                func.max(LeadConversation.sentiment_score).label('max_sentiment')
            ).filter(
                and_(
                    LeadConversation.created_at >= start_date,
                    LeadConversation.sentiment_score.isnot(None)
                )
            ).first()
            
            # Intent analysis
            intent_analysis = db.query(
                LeadConversation.intent_classification,
                func.count(LeadConversation.id).label('count')
            ).filter(
                and_(
                    LeadConversation.created_at >= start_date,
                    LeadConversation.intent_classification.isnot(None)
                )
            ).group_by(LeadConversation.intent_classification).all()
            
            # Calculate summary metrics
            total_messages = sum(row.total_messages for row in daily_conversations)
            total_sessions = sum(row.unique_sessions for row in daily_conversations)
            avg_messages_per_session = total_messages / total_sessions if total_sessions > 0 else 0
            avg_response_time = sum(row.avg_response_time or 0 for row in daily_conversations) / len(daily_conversations) if daily_conversations else 0
            
            data_points = [
                {
                    "date": row.date.isoformat(),
                    "total_messages": row.total_messages,
                    "unique_sessions": row.unique_sessions,
                    "avg_response_time_ms": round(row.avg_response_time or 0, 2)
                }
                for row in daily_conversations
            ]
            
            summary = {
                "total_messages": total_messages,
                "total_sessions": total_sessions,
                "avg_messages_per_session": round(avg_messages_per_session, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "message_types": {
                    msg_type: count for msg_type, count in message_types
                },
                "sentiment": {
                    "average": round(sentiment_analysis.avg_sentiment or 0, 3),
                    "min": round(sentiment_analysis.min_sentiment or 0, 3),
                    "max": round(sentiment_analysis.max_sentiment or 0, 3)
                },
                "intents": {
                    intent: count for intent, count in intent_analysis
                }
            }
            
            return AnalyticsResult(
                metric_type=MetricType.CONVERSATION.value,
                time_range=time_range.value,
                data_points=data_points,
                summary=summary,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Error getting conversation analytics", error=str(e))
            return AnalyticsResult(
                metric_type=MetricType.CONVERSATION.value,
                time_range=time_range.value,
                data_points=[],
                summary={},
                generated_at=datetime.utcnow()
            )
    
    async def get_lead_quality_analytics(
        self, 
        time_range: TimeRange = TimeRange.DAY,
        days: int = 30
    ) -> AnalyticsResult:
        """Get lead quality analytics"""
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            db = next(get_db())
            
            # Lead quality by day
            daily_quality = db.query(
                func.date(Lead.created_at).label('date'),
                func.avg(Lead.lead_score).label('avg_score'),
                func.count(Lead.id).label('total_leads'),
                func.count(func.case([(Lead.status == "qualified", 1)])).label('qualified_leads')
            ).filter(
                Lead.created_at >= start_date
            ).group_by(
                func.date(Lead.created_at)
            ).order_by('date').all()
            
            # Quality tier distribution
            quality_tiers = db.query(
                Lead.lead_quality,
                func.count(Lead.id).label('count'),
                func.avg(Lead.lead_score).label('avg_score'),
                func.avg(Lead.estimated_value).label('avg_value')
            ).filter(
                Lead.created_at >= start_date
            ).group_by(Lead.lead_quality).all()
            
            # Score distribution
            score_ranges = [
                (0, 30, "low"),
                (31, 60, "medium"),
                (61, 80, "high"),
                (81, 100, "premium")
            ]
            
            score_distribution = []
            for min_score, max_score, label in score_ranges:
                count = db.query(Lead).filter(
                    and_(
                        Lead.created_at >= start_date,
                        Lead.lead_score >= min_score,
                        Lead.lead_score <= max_score
                    )
                ).count()
                score_distribution.append({
                    "range": f"{min_score}-{max_score}",
                    "label": label,
                    "count": count
                })
            
            # Calculate summary metrics
            total_leads = sum(row.total_leads for row in daily_quality)
            qualified_leads = sum(row.qualified_leads for row in daily_quality)
            qualification_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
            avg_lead_score = sum(row.avg_score or 0 for row in daily_quality) / len(daily_quality) if daily_quality else 0
            
            data_points = [
                {
                    "date": row.date.isoformat(),
                    "avg_score": round(row.avg_score or 0, 2),
                    "total_leads": row.total_leads,
                    "qualified_leads": row.qualified_leads,
                    "qualification_rate": round((row.qualified_leads / row.total_leads * 100) if row.total_leads > 0 else 0, 2)
                }
                for row in daily_quality
            ]
            
            summary = {
                "total_leads": total_leads,
                "qualified_leads": qualified_leads,
                "qualification_rate": round(qualification_rate, 2),
                "avg_lead_score": round(avg_lead_score, 2),
                "quality_tiers": [
                    {
                        "tier": row.lead_quality,
                        "count": row.count,
                        "avg_score": round(row.avg_score or 0, 2),
                        "avg_value": round(row.avg_value or 0, 2)
                    }
                    for row in quality_tiers
                ],
                "score_distribution": score_distribution
            }
            
            return AnalyticsResult(
                metric_type=MetricType.LEAD_QUALITY.value,
                time_range=time_range.value,
                data_points=data_points,
                summary=summary,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Error getting lead quality analytics", error=str(e))
            return AnalyticsResult(
                metric_type=MetricType.LEAD_QUALITY.value,
                time_range=time_range.value,
                data_points=[],
                summary={},
                generated_at=datetime.utcnow()
            )
    
    async def _start_realtime_metrics_worker(self):
        """Start background worker for real-time metrics"""
        async def worker():
            while True:
                try:
                    # Update real-time metrics every 30 seconds
                    await self._calculate_realtime_metrics()
                    await asyncio.sleep(30)
                except Exception as e:
                    logger.error("Error in real-time metrics worker", error=str(e))
                    await asyncio.sleep(60)
        
        asyncio.create_task(worker())
    
    async def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        if not self.redis:
            return 0.0
        
        try:
            hits = await self.redis.get("cache_hits") or 0
            misses = await self.redis.get("cache_misses") or 0
            total = int(hits) + int(misses)
            return (int(hits) / total * 100) if total > 0 else 0.0
        except:
            return 0.0
    
    async def _get_active_connections(self) -> int:
        """Get active WebSocket connections"""
        if not self.redis:
            return 0
        
        try:
            return await self.redis.get("active_connections") or 0
        except:
            return 0
    
    async def get_custom_analytics(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Get custom analytics based on query parameters"""
        # Implementation for custom analytics queries
        # This would handle complex queries with multiple filters and groupings
        pass
    
    async def export_analytics_data(
        self, 
        metric_type: MetricType, 
        time_range: TimeRange,
        format: str = "json"
    ) -> str:
        """Export analytics data in specified format"""
        try:
            if metric_type == MetricType.REVENUE:
                result = await self.get_revenue_analytics(time_range)
            elif metric_type == MetricType.CONVERSATION:
                result = await self.get_conversation_analytics(time_range)
            elif metric_type == MetricType.LEAD_QUALITY:
                result = await self.get_lead_quality_analytics(time_range)
            else:
                raise ValueError(f"Unsupported metric type: {metric_type}")
            
            if format == "json":
                return json.dumps({
                    "metric_type": result.metric_type,
                    "time_range": result.time_range,
                    "data_points": result.data_points,
                    "summary": result.summary,
                    "generated_at": result.generated_at.isoformat()
                }, default=str)
            elif format == "csv":
                # Convert to CSV format
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write headers
                if result.data_points:
                    headers = list(result.data_points[0].keys())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in result.data_points:
                        writer.writerow([row.get(header, "") for header in headers])
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error("Error exporting analytics data", error=str(e))
            return ""