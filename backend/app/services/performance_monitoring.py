"""
Performance Monitoring Service
Tracks conversation performance, lead quality, and revenue optimization
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.lead import Lead, LeadConversation, LeadQualityHistory
from app.models.ai_models import AIAnalysis, AIConversation
from app.models.analytics import RevenueMetrics, PlatformPerformance
from app.models.b2b_platforms import B2BPlatform, B2BRevenueTransaction


class MetricType(Enum):
    """Types of performance metrics"""
    CONVERSATION = "conversation"
    LEAD_QUALITY = "lead_quality"
    REVENUE = "revenue"
    AI_PERFORMANCE = "ai_performance"
    B2B_EXPORT = "b2b_export"


@dataclass
class PerformanceAlert:
    """Performance alert configuration"""
    metric_name: str
    threshold: float
    operator: str  # "gt", "lt", "eq", "gte", "lte"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    action_required: str


class PerformanceMonitoringService:
    """Service for monitoring conversation and business performance"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Performance thresholds
        self.thresholds = {
            "conversion_rate": {"min": 0.15, "target": 0.25, "max": 0.35},
            "avg_lead_score": {"min": 60, "target": 75, "max": 85},
            "response_time_ms": {"min": 500, "target": 1000, "max": 2000},
            "revenue_per_lead": {"min": 100, "target": 200, "max": 300},
            "b2b_acceptance_rate": {"min": 0.70, "target": 0.85, "max": 0.95},
            "ai_accuracy": {"min": 0.80, "target": 0.90, "max": 0.95}
        }
        
        # Alert configurations
        self.alerts = [
            PerformanceAlert("conversion_rate", 0.10, "lt", "high", 
                           "Conversion rate below 10%", "Review conversation flow"),
            PerformanceAlert("avg_lead_score", 50, "lt", "medium", 
                           "Average lead score below 50", "Improve qualification questions"),
            PerformanceAlert("response_time_ms", 3000, "gt", "medium", 
                           "Response time above 3 seconds", "Check AI service performance"),
            PerformanceAlert("b2b_acceptance_rate", 0.60, "lt", "high", 
                           "B2B acceptance rate below 60%", "Review lead quality and platform requirements")
        ]
    
    async def get_conversation_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get conversation performance metrics"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total conversations
            total_conversations = self.db.query(LeadConversation).filter(
                LeadConversation.created_at >= start_date
            ).count()
            
            # Unique sessions
            unique_sessions = self.db.query(LeadConversation.session_id).filter(
                LeadConversation.created_at >= start_date
            ).distinct().count()
            
            # Conversation completion rate
            completed_conversations = self.db.query(LeadConversation).filter(
                and_(
                    LeadConversation.created_at >= start_date,
                    LeadConversation.message_type == "ai",
                    LeadConversation.content.like("%schedule%")
                )
            ).count()
            
            completion_rate = (
                completed_conversations / unique_sessions if unique_sessions > 0 else 0
            )
            
            # Average conversation length
            avg_conversation_length = self.db.query(
                func.count(LeadConversation.id).label('message_count')
            ).filter(
                LeadConversation.created_at >= start_date
            ).group_by(LeadConversation.session_id).all()
            
            avg_length = (
                sum([count[0] for count in avg_conversation_length]) / len(avg_conversation_length)
                if avg_conversation_length else 0
            )
            
            # Response time analysis
            response_times = self.db.query(LeadConversation.response_time_ms).filter(
                and_(
                    LeadConversation.created_at >= start_date,
                    LeadConversation.response_time_ms.isnot(None)
                )
            ).all()
            
            avg_response_time = (
                sum([rt[0] for rt in response_times]) / len(response_times)
                if response_times else 0
            )
            
            # Sentiment analysis
            sentiment_scores = self.db.query(LeadConversation.sentiment_score).filter(
                and_(
                    LeadConversation.created_at >= start_date,
                    LeadConversation.sentiment_score.isnot(None)
                )
            ).all()
            
            avg_sentiment = (
                sum([s[0] for s in sentiment_scores]) / len(sentiment_scores)
                if sentiment_scores else 0
            )
            
            return {
                "period_days": days,
                "total_conversations": total_conversations,
                "unique_sessions": unique_sessions,
                "completion_rate": completion_rate,
                "avg_conversation_length": avg_length,
                "avg_response_time_ms": avg_response_time,
                "avg_sentiment": avg_sentiment,
                "conversation_volume_trend": await self._get_volume_trend(days),
                "peak_hours": await self._get_peak_hours(days)
            }
            
        except Exception as e:
            print(f"Error getting conversation metrics: {e}")
            return {}
    
    async def get_lead_quality_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get lead quality performance metrics"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total leads created
            total_leads = self.db.query(Lead).filter(
                Lead.created_at >= start_date
            ).count()
            
            # Qualified leads
            qualified_leads = self.db.query(Lead).filter(
                and_(
                    Lead.created_at >= start_date,
                    Lead.status == "qualified"
                )
            ).count()
            
            # Lead quality distribution
            quality_distribution = self.db.query(
                Lead.lead_quality,
                func.count(Lead.id).label('count')
            ).filter(
                Lead.created_at >= start_date
            ).group_by(Lead.lead_quality).all()
            
            quality_dist = {
                quality: count for quality, count in quality_distribution
            }
            
            # Average lead score
            avg_lead_score = self.db.query(func.avg(Lead.lead_score)).filter(
                Lead.created_at >= start_date
            ).scalar() or 0
            
            # Lead score distribution
            score_ranges = [
                (0, 30, "low"),
                (31, 60, "medium"),
                (61, 80, "high"),
                (81, 100, "premium")
            ]
            
            score_distribution = {}
            for min_score, max_score, label in score_ranges:
                count = self.db.query(Lead).filter(
                    and_(
                        Lead.created_at >= start_date,
                        Lead.lead_score >= min_score,
                        Lead.lead_score <= max_score
                    )
                ).count()
                score_distribution[label] = count
            
            # Conversion rate by quality tier
            conversion_by_quality = {}
            for quality in ["hot", "warm", "cold"]:
                total = self.db.query(Lead).filter(
                    and_(
                        Lead.created_at >= start_date,
                        Lead.lead_quality == quality
                    )
                ).count()
                
                converted = self.db.query(Lead).filter(
                    and_(
                        Lead.created_at >= start_date,
                        Lead.lead_quality == quality,
                        Lead.status == "qualified"
                    )
                ).count()
                
                conversion_by_quality[quality] = (
                    converted / total if total > 0 else 0
                )
            
            return {
                "period_days": days,
                "total_leads": total_leads,
                "qualified_leads": qualified_leads,
                "qualification_rate": qualified_leads / total_leads if total_leads > 0 else 0,
                "avg_lead_score": avg_lead_score,
                "quality_distribution": quality_dist,
                "score_distribution": score_distribution,
                "conversion_by_quality": conversion_by_quality,
                "quality_trend": await self._get_quality_trend(days)
            }
            
        except Exception as e:
            print(f"Error getting lead quality metrics: {e}")
            return {}
    
    async def get_revenue_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get revenue performance metrics"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total revenue
            total_revenue = self.db.query(func.sum(B2BRevenueTransaction.net_amount)).filter(
                B2BRevenueTransaction.transaction_date >= start_date
            ).scalar() or 0
            
            # Revenue by platform
            revenue_by_platform = self.db.query(
                B2BPlatform.platform_name,
                func.sum(B2BRevenueTransaction.net_amount).label('revenue')
            ).join(
                B2BRevenueTransaction, B2BPlatform.id == B2BRevenueTransaction.platform_id
            ).filter(
                B2BRevenueTransaction.transaction_date >= start_date
            ).group_by(B2BPlatform.platform_name).all()
            
            platform_revenue = {
                platform: revenue for platform, revenue in revenue_by_platform
            }
            
            # Average revenue per lead
            total_leads = self.db.query(Lead).filter(
                Lead.created_at >= start_date
            ).count()
            
            avg_revenue_per_lead = total_revenue / total_leads if total_leads > 0 else 0
            
            # Revenue by quality tier
            revenue_by_quality = {}
            for quality in ["premium", "standard", "basic"]:
                leads = self.db.query(Lead).filter(
                    and_(
                        Lead.created_at >= start_date,
                        Lead.lead_quality == quality
                    )
                ).all()
                
                lead_revenue = sum([
                    self.db.query(func.sum(B2BRevenueTransaction.net_amount)).filter(
                        B2BRevenueTransaction.lead_id == lead.id
                    ).scalar() or 0
                    for lead in leads
                ])
                
                revenue_by_quality[quality] = lead_revenue
            
            # Commission earned
            total_commission = self.db.query(func.sum(B2BRevenueTransaction.commission_amount)).filter(
                B2BRevenueTransaction.transaction_date >= start_date
            ).scalar() or 0
            
            return {
                "period_days": days,
                "total_revenue": total_revenue,
                "total_commission": total_commission,
                "avg_revenue_per_lead": avg_revenue_per_lead,
                "platform_revenue": platform_revenue,
                "revenue_by_quality": revenue_by_quality,
                "revenue_trend": await self._get_revenue_trend(days)
            }
            
        except Exception as e:
            print(f"Error getting revenue metrics: {e}")
            return {}
    
    async def get_ai_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get AI performance metrics"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # AI model usage
            model_usage = self.db.query(
                AIModel.model_name,
                func.count(AIAnalysis.id).label('usage_count')
            ).join(
                AIAnalysis, AIModel.id == AIAnalysis.model_id
            ).filter(
                AIAnalysis.analyzed_at >= start_date
            ).group_by(AIModel.model_name).all()
            
            model_usage_dict = {
                model: count for model, count in model_usage
            }
            
            # Average accuracy scores
            avg_accuracy = self.db.query(func.avg(AIAnalysis.confidence_score)).filter(
                AIAnalysis.analyzed_at >= start_date
            ).scalar() or 0
            
            # Analysis types
            analysis_types = self.db.query(
                AIAnalysis.analysis_type,
                func.count(AIAnalysis.id).label('count')
            ).filter(
                AIAnalysis.analyzed_at >= start_date
            ).group_by(AIAnalysis.analysis_type).all()
            
            analysis_type_dist = {
                analysis_type: count for analysis_type, count in analysis_types
            }
            
            # AI conversation metrics
            ai_conversations = self.db.query(AIConversation).filter(
                AIConversation.created_at >= start_date
            ).all()
            
            total_ai_messages = len(ai_conversations)
            avg_tokens_used = (
                sum([conv.total_tokens or 0 for conv in ai_conversations]) / total_ai_messages
                if total_ai_messages > 0 else 0
            )
            
            avg_processing_time = (
                sum([conv.processing_time_ms or 0 for conv in ai_conversations]) / total_ai_messages
                if total_ai_messages > 0 else 0
            )
            
            return {
                "period_days": days,
                "model_usage": model_usage_dict,
                "avg_accuracy": avg_accuracy,
                "analysis_type_distribution": analysis_type_dist,
                "total_ai_messages": total_ai_messages,
                "avg_tokens_used": avg_tokens_used,
                "avg_processing_time_ms": avg_processing_time,
                "ai_performance_trend": await self._get_ai_performance_trend(days)
            }
            
        except Exception as e:
            print(f"Error getting AI performance metrics: {e}")
            return {}
    
    async def get_b2b_export_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get B2B export performance metrics"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Export statistics
            total_exports = self.db.query(LeadExport).filter(
                LeadExport.created_at >= start_date
            ).count()
            
            successful_exports = self.db.query(LeadExport).filter(
                and_(
                    LeadExport.created_at >= start_date,
                    LeadExport.export_status == "success"
                )
            ).count()
            
            failed_exports = self.db.query(LeadExport).filter(
                and_(
                    LeadExport.created_at >= start_date,
                    LeadExport.export_status == "failed"
                )
            ).count()
            
            # Export success rate
            success_rate = successful_exports / total_exports if total_exports > 0 else 0
            
            # Exports by platform
            exports_by_platform = self.db.query(
                B2BPlatform.platform_name,
                func.count(LeadExport.id).label('export_count')
            ).join(
                LeadExport, B2BPlatform.id == LeadExport.platform_id
            ).filter(
                LeadExport.created_at >= start_date
            ).group_by(B2BPlatform.platform_name).all()
            
            platform_exports = {
                platform: count for platform, count in exports_by_platform
            }
            
            # Average commission earned
            avg_commission = self.db.query(func.avg(LeadExport.commission_earned)).filter(
                and_(
                    LeadExport.created_at >= start_date,
                    LeadExport.commission_earned.isnot(None)
                )
            ).scalar() or 0
            
            # Export response times
            response_times = self.db.query(LeadExport.response_time_ms).filter(
                and_(
                    LeadExport.created_at >= start_date,
                    LeadExport.response_time_ms.isnot(None)
                )
            ).all()
            
            avg_response_time = (
                sum([rt[0] for rt in response_times]) / len(response_times)
                if response_times else 0
            )
            
            return {
                "period_days": days,
                "total_exports": total_exports,
                "successful_exports": successful_exports,
                "failed_exports": failed_exports,
                "success_rate": success_rate,
                "platform_exports": platform_exports,
                "avg_commission": avg_commission,
                "avg_response_time_ms": avg_response_time,
                "export_trend": await self._get_export_trend(days)
            }
            
        except Exception as e:
            print(f"Error getting B2B export metrics: {e}")
            return {}
    
    async def get_comprehensive_dashboard(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        
        try:
            # Get all metrics
            conversation_metrics = await self.get_conversation_metrics(days)
            lead_quality_metrics = await self.get_lead_quality_metrics(days)
            revenue_metrics = await self.get_revenue_metrics(days)
            ai_metrics = await self.get_ai_performance_metrics(days)
            b2b_metrics = await self.get_b2b_export_metrics(days)
            
            # Calculate KPIs
            kpis = {
                "conversion_rate": lead_quality_metrics.get("qualification_rate", 0),
                "avg_lead_score": lead_quality_metrics.get("avg_lead_score", 0),
                "revenue_per_lead": revenue_metrics.get("avg_revenue_per_lead", 0),
                "b2b_success_rate": b2b_metrics.get("success_rate", 0),
                "ai_accuracy": ai_metrics.get("avg_accuracy", 0)
            }
            
            # Check for alerts
            alerts = await self._check_performance_alerts(kpis)
            
            # Calculate performance score
            performance_score = await self._calculate_performance_score(kpis)
            
            return {
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat(),
                "kpis": kpis,
                "performance_score": performance_score,
                "alerts": alerts,
                "conversation_metrics": conversation_metrics,
                "lead_quality_metrics": lead_quality_metrics,
                "revenue_metrics": revenue_metrics,
                "ai_metrics": ai_metrics,
                "b2b_metrics": b2b_metrics,
                "recommendations": await self._generate_recommendations(kpis)
            }
            
        except Exception as e:
            print(f"Error getting comprehensive dashboard: {e}")
            return {}
    
    async def _get_volume_trend(self, days: int) -> List[Dict[str, Any]]:
        """Get conversation volume trend over time"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Group by day
            daily_volumes = self.db.query(
                func.date(LeadConversation.created_at).label('date'),
                func.count(LeadConversation.id).label('count')
            ).filter(
                LeadConversation.created_at >= start_date
            ).group_by(
                func.date(LeadConversation.created_at)
            ).order_by('date').all()
            
            return [
                {"date": date.isoformat(), "count": count}
                for date, count in daily_volumes
            ]
            
        except Exception as e:
            print(f"Error getting volume trend: {e}")
            return []
    
    async def _get_peak_hours(self, days: int) -> List[Dict[str, Any]]:
        """Get peak conversation hours"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Group by hour
            hourly_volumes = self.db.query(
                func.extract('hour', LeadConversation.created_at).label('hour'),
                func.count(LeadConversation.id).label('count')
            ).filter(
                LeadConversation.created_at >= start_date
            ).group_by(
                func.extract('hour', LeadConversation.created_at)
            ).order_by('hour').all()
            
            return [
                {"hour": int(hour), "count": count}
                for hour, count in hourly_volumes
            ]
            
        except Exception as e:
            print(f"Error getting peak hours: {e}")
            return []
    
    async def _get_quality_trend(self, days: int) -> List[Dict[str, Any]]:
        """Get lead quality trend over time"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily average lead scores
            daily_scores = self.db.query(
                func.date(Lead.created_at).label('date'),
                func.avg(Lead.lead_score).label('avg_score')
            ).filter(
                Lead.created_at >= start_date
            ).group_by(
                func.date(Lead.created_at)
            ).order_by('date').all()
            
            return [
                {"date": date.isoformat(), "avg_score": float(avg_score or 0)}
                for date, avg_score in daily_scores
            ]
            
        except Exception as e:
            print(f"Error getting quality trend: {e}")
            return []
    
    async def _get_revenue_trend(self, days: int) -> List[Dict[str, Any]]:
        """Get revenue trend over time"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily revenue
            daily_revenue = self.db.query(
                func.date(B2BRevenueTransaction.transaction_date).label('date'),
                func.sum(B2BRevenueTransaction.net_amount).label('revenue')
            ).filter(
                B2BRevenueTransaction.transaction_date >= start_date
            ).group_by(
                func.date(B2BRevenueTransaction.transaction_date)
            ).order_by('date').all()
            
            return [
                {"date": date.isoformat(), "revenue": float(revenue or 0)}
                for date, revenue in daily_revenue
            ]
            
        except Exception as e:
            print(f"Error getting revenue trend: {e}")
            return []
    
    async def _get_ai_performance_trend(self, days: int) -> List[Dict[str, Any]]:
        """Get AI performance trend over time"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily AI accuracy
            daily_accuracy = self.db.query(
                func.date(AIAnalysis.analyzed_at).label('date'),
                func.avg(AIAnalysis.confidence_score).label('avg_accuracy')
            ).filter(
                AIAnalysis.analyzed_at >= start_date
            ).group_by(
                func.date(AIAnalysis.analyzed_at)
            ).order_by('date').all()
            
            return [
                {"date": date.isoformat(), "avg_accuracy": float(avg_accuracy or 0)}
                for date, avg_accuracy in daily_accuracy
            ]
            
        except Exception as e:
            print(f"Error getting AI performance trend: {e}")
            return []
    
    async def _get_export_trend(self, days: int) -> List[Dict[str, Any]]:
        """Get export trend over time"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily exports
            daily_exports = self.db.query(
                func.date(LeadExport.created_at).label('date'),
                func.count(LeadExport.id).label('export_count')
            ).filter(
                LeadExport.created_at >= start_date
            ).group_by(
                func.date(LeadExport.created_at)
            ).order_by('date').all()
            
            return [
                {"date": date.isoformat(), "export_count": count}
                for date, count in daily_exports
            ]
            
        except Exception as e:
            print(f"Error getting export trend: {e}")
            return []
    
    async def _check_performance_alerts(self, kpis: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check for performance alerts based on KPIs"""
        
        alerts = []
        
        for alert in self.alerts:
            metric_value = kpis.get(alert.metric_name, 0)
            threshold = alert.threshold
            
            # Check alert condition
            alert_triggered = False
            if alert.operator == "lt" and metric_value < threshold:
                alert_triggered = True
            elif alert.operator == "gt" and metric_value > threshold:
                alert_triggered = True
            elif alert.operator == "eq" and metric_value == threshold:
                alert_triggered = True
            elif alert.operator == "lte" and metric_value <= threshold:
                alert_triggered = True
            elif alert.operator == "gte" and metric_value >= threshold:
                alert_triggered = True
            
            if alert_triggered:
                alerts.append({
                    "metric": alert.metric_name,
                    "value": metric_value,
                    "threshold": threshold,
                    "severity": alert.severity,
                    "message": alert.message,
                    "action_required": alert.action_required,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return alerts
    
    async def _calculate_performance_score(self, kpis: Dict[str, float]) -> float:
        """Calculate overall performance score"""
        
        try:
            # Weighted scoring based on business importance
            weights = {
                "conversion_rate": 0.25,
                "avg_lead_score": 0.20,
                "revenue_per_lead": 0.25,
                "b2b_success_rate": 0.20,
                "ai_accuracy": 0.10
            }
            
            total_score = 0
            total_weight = 0
            
            for metric, value in kpis.items():
                if metric in weights:
                    # Normalize value to 0-100 scale
                    normalized_value = min(100, max(0, value * 100))
                    total_score += normalized_value * weights[metric]
                    total_weight += weights[metric]
            
            return total_score / total_weight if total_weight > 0 else 0
            
        except Exception as e:
            print(f"Error calculating performance score: {e}")
            return 0
    
    async def _generate_recommendations(self, kpis: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate performance improvement recommendations"""
        
        recommendations = []
        
        # Conversion rate recommendations
        if kpis.get("conversion_rate", 0) < 0.20:
            recommendations.append({
                "category": "conversion",
                "priority": "high",
                "title": "Improve Conversion Rate",
                "description": "Conversion rate is below target. Consider optimizing conversation flow and qualification questions.",
                "actions": [
                    "Review conversation templates",
                    "A/B test different approaches",
                    "Improve objection handling"
                ]
            })
        
        # Lead quality recommendations
        if kpis.get("avg_lead_score", 0) < 70:
            recommendations.append({
                "category": "lead_quality",
                "priority": "medium",
                "title": "Improve Lead Quality",
                "description": "Average lead score is below target. Focus on better qualification.",
                "actions": [
                    "Enhance qualification questions",
                    "Improve NYC market data integration",
                    "Better lead scoring algorithm"
                ]
            })
        
        # Revenue recommendations
        if kpis.get("revenue_per_lead", 0) < 150:
            recommendations.append({
                "category": "revenue",
                "priority": "high",
                "title": "Increase Revenue Per Lead",
                "description": "Revenue per lead is below target. Focus on higher-value leads.",
                "actions": [
                    "Target higher-value zip codes",
                    "Improve B2B platform selection",
                    "Optimize pricing tiers"
                ]
            })
        
        return recommendations
