"""
Quality Feedback Loop for Aurum Solar
Integrates B2B buyer feedback into scoring algorithms for continuous improvement
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
from app.models.b2b_models import B2BLeadExport, B2BBuyer
from app.models.lead import Lead, LeadQualityHistory
from app.services.revenue_optimization_engine import LeadQualityTier, RealTimeLeadScore


@dataclass
class BuyerFeedback:
    """B2B buyer feedback on lead quality"""
    lead_id: str
    buyer_id: str
    feedback_type: str  # "accepted", "rejected", "converted", "low_quality"
    feedback_score: float  # 1-10 scale
    feedback_reason: str
    conversion_value: Optional[float]  # Actual revenue if converted
    feedback_timestamp: datetime
    buyer_notes: Optional[str]


@dataclass
class QualityMetrics:
    """Quality metrics for feedback analysis"""
    buyer_id: str
    total_leads_received: int
    leads_accepted: int
    leads_rejected: int
    leads_converted: int
    acceptance_rate: float
    conversion_rate: float
    avg_feedback_score: float
    avg_conversion_value: float
    quality_trend: List[Tuple[datetime, float]]  # (date, avg_score)


@dataclass
class ScoringAdjustment:
    """Scoring algorithm adjustment based on feedback"""
    factor_name: str
    current_weight: float
    adjusted_weight: float
    adjustment_reason: str
    confidence_level: float
    effective_date: datetime
    performance_impact: float


@dataclass
class FeedbackAnalysis:
    """Comprehensive feedback analysis"""
    analysis_period: Tuple[datetime, datetime]
    total_feedback_received: int
    overall_acceptance_rate: float
    overall_conversion_rate: float
    quality_improvements: List[ScoringAdjustment]
    buyer_performance: Dict[str, QualityMetrics]
    recommendations: List[str]
    next_review_date: datetime


class QualityFeedbackLoop:
    """Quality feedback loop for continuous improvement"""
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis_client = redis_client
        self.feedback_history = []
        self.scoring_adjustments = []
        self.quality_metrics = {}
        
        # Start background tasks
        asyncio.create_task(self._process_feedback_queue())
        asyncio.create_task(self._analyze_quality_trends())
        asyncio.create_task(self._update_scoring_algorithms())
    
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
        """Submit buyer feedback for a lead"""
        
        try:
            # Create feedback record
            feedback = BuyerFeedback(
                lead_id=lead_id,
                buyer_id=buyer_id,
                feedback_type=feedback_type,
                feedback_score=feedback_score,
                feedback_reason=feedback_reason,
                conversion_value=conversion_value,
                feedback_timestamp=datetime.utcnow(),
                buyer_notes=buyer_notes
            )
            
            # Store in database
            await self._store_feedback(feedback)
            
            # Add to feedback history
            self.feedback_history.append(feedback)
            
            # Update quality metrics
            await self._update_quality_metrics(buyer_id, feedback)
            
            # Queue for processing
            await self._queue_feedback_for_processing(feedback)
            
            return feedback
            
        except Exception as e:
            print(f"Error submitting buyer feedback: {e}")
            return None
    
    async def _store_feedback(self, feedback: BuyerFeedback):
        """Store feedback in database"""
        
        try:
            # Update B2B lead export with feedback
            lead_export = self.db.query(B2BLeadExport).filter(
                B2BLeadExport.lead_id == feedback.lead_id,
                B2BLeadExport.buyer_id == feedback.buyer_id
            ).first()
            
            if lead_export:
                lead_export.feedback_type = feedback.feedback_type
                lead_export.feedback_score = feedback.feedback_score
                lead_export.feedback_reason = feedback.feedback_reason
                lead_export.conversion_value = feedback.conversion_value
                lead_export.buyer_notes = feedback.buyer_notes
                lead_export.feedback_received_at = feedback.feedback_timestamp
                
                self.db.commit()
            
        except Exception as e:
            print(f"Error storing feedback: {e}")
            self.db.rollback()
    
    async def _update_quality_metrics(self, buyer_id: str, feedback: BuyerFeedback):
        """Update quality metrics for buyer"""
        
        try:
            if buyer_id not in self.quality_metrics:
                # Initialize metrics for new buyer
                self.quality_metrics[buyer_id] = QualityMetrics(
                    buyer_id=buyer_id,
                    total_leads_received=0,
                    leads_accepted=0,
                    leads_rejected=0,
                    leads_converted=0,
                    acceptance_rate=0.0,
                    conversion_rate=0.0,
                    avg_feedback_score=0.0,
                    avg_conversion_value=0.0,
                    quality_trend=[]
                )
            
            metrics = self.quality_metrics[buyer_id]
            
            # Update counts
            metrics.total_leads_received += 1
            
            if feedback.feedback_type == "accepted":
                metrics.leads_accepted += 1
            elif feedback.feedback_type == "rejected":
                metrics.leads_rejected += 1
            elif feedback.feedback_type == "converted":
                metrics.leads_converted += 1
            
            # Update rates
            metrics.acceptance_rate = metrics.leads_accepted / metrics.total_leads_received
            metrics.conversion_rate = metrics.leads_converted / metrics.total_leads_received
            
            # Update average scores
            total_score = metrics.avg_feedback_score * (metrics.total_leads_received - 1)
            metrics.avg_feedback_score = (total_score + feedback.feedback_score) / metrics.total_leads_received
            
            # Update conversion value
            if feedback.conversion_value:
                total_value = metrics.avg_conversion_value * metrics.leads_converted
                metrics.avg_conversion_value = (total_value + feedback.conversion_value) / metrics.leads_converted
            
            # Add to quality trend
            metrics.quality_trend.append((feedback.feedback_timestamp, feedback.feedback_score))
            
            # Keep only last 30 days of trend data
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            metrics.quality_trend = [
                (date, score) for date, score in metrics.quality_trend
                if date >= cutoff_date
            ]
            
        except Exception as e:
            print(f"Error updating quality metrics: {e}")
    
    async def _queue_feedback_for_processing(self, feedback: BuyerFeedback):
        """Queue feedback for batch processing"""
        
        try:
            queue_key = "feedback_processing_queue"
            feedback_data = asdict(feedback)
            feedback_data["feedback_timestamp"] = feedback.feedback_timestamp.isoformat()
            
            self.redis_client.lpush(queue_key, json.dumps(feedback_data))
            
        except Exception as e:
            print(f"Error queuing feedback for processing: {e}")
    
    async def _process_feedback_queue(self):
        """Background task to process feedback queue"""
        
        while True:
            try:
                queue_key = "feedback_processing_queue"
                
                # Process up to 10 feedback items at a time
                for _ in range(10):
                    feedback_data = self.redis_client.rpop(queue_key)
                    if not feedback_data:
                        break
                    
                    try:
                        data = json.loads(feedback_data)
                        data["feedback_timestamp"] = datetime.fromisoformat(data["feedback_timestamp"])
                        
                        # Analyze feedback for scoring adjustments
                        await self._analyze_feedback_for_adjustments(data)
                        
                    except Exception as e:
                        print(f"Error processing feedback item: {e}")
                
                # Wait 30 seconds before next processing cycle
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Error processing feedback queue: {e}")
                await asyncio.sleep(30)
    
    async def _analyze_feedback_for_adjustments(self, feedback_data: Dict[str, Any]):
        """Analyze feedback to determine scoring adjustments"""
        
        try:
            buyer_id = feedback_data["buyer_id"]
            feedback_type = feedback_data["feedback_type"]
            feedback_score = feedback_data["feedback_score"]
            feedback_reason = feedback_data["feedback_reason"]
            
            # Get buyer's quality metrics
            if buyer_id not in self.quality_metrics:
                return
            
            metrics = self.quality_metrics[buyer_id]
            
            # Analyze patterns in feedback
            adjustments = []
            
            # Check for declining acceptance rate
            if metrics.total_leads_received >= 10:  # Need sufficient data
                recent_feedback = self._get_recent_feedback(buyer_id, days=7)
                if len(recent_feedback) >= 5:
                    recent_acceptance_rate = sum(1 for f in recent_feedback if f["feedback_type"] == "accepted") / len(recent_feedback)
                    
                    if recent_acceptance_rate < metrics.acceptance_rate * 0.8:  # 20% decline
                        adjustments.append(ScoringAdjustment(
                            factor_name="buyer_preference_alignment",
                            current_weight=0.1,
                            adjusted_weight=0.15,
                            adjustment_reason=f"Declining acceptance rate for {buyer_id}",
                            confidence_level=0.8,
                            effective_date=datetime.utcnow(),
                            performance_impact=0.1
                        ))
            
            # Check for quality score patterns
            if feedback_score < 5.0:  # Low quality feedback
                # Analyze common rejection reasons
                rejection_reasons = self._analyze_rejection_reasons(buyer_id)
                
                for reason, frequency in rejection_reasons.items():
                    if frequency > 0.3:  # More than 30% of rejections
                        adjustment = self._create_adjustment_for_reason(reason, frequency)
                        if adjustment:
                            adjustments.append(adjustment)
            
            # Apply adjustments
            for adjustment in adjustments:
                await self._apply_scoring_adjustment(adjustment)
            
        except Exception as e:
            print(f"Error analyzing feedback for adjustments: {e}")
    
    def _get_recent_feedback(self, buyer_id: str, days: int) -> List[Dict[str, Any]]:
        """Get recent feedback for a buyer"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_feedback = []
        for feedback in self.feedback_history:
            if (feedback.buyer_id == buyer_id and 
                feedback.feedback_timestamp >= cutoff_date):
                recent_feedback.append({
                    "feedback_type": feedback.feedback_type,
                    "feedback_score": feedback.feedback_score,
                    "feedback_reason": feedback.feedback_reason
                })
        
        return recent_feedback
    
    def _analyze_rejection_reasons(self, buyer_id: str) -> Dict[str, float]:
        """Analyze common rejection reasons for a buyer"""
        
        rejection_reasons = {}
        total_rejections = 0
        
        for feedback in self.feedback_history:
            if (feedback.buyer_id == buyer_id and 
                feedback.feedback_type == "rejected"):
                total_rejections += 1
                reason = feedback.feedback_reason.lower()
                
                # Categorize rejection reasons
                if "quality" in reason or "low quality" in reason:
                    rejection_reasons["low_quality"] = rejection_reasons.get("low_quality", 0) + 1
                elif "not qualified" in reason or "unqualified" in reason:
                    rejection_reasons["unqualified"] = rejection_reasons.get("unqualified", 0) + 1
                elif "wrong area" in reason or "geography" in reason:
                    rejection_reasons["wrong_geography"] = rejection_reasons.get("wrong_geography", 0) + 1
                elif "timeline" in reason or "timing" in reason:
                    rejection_reasons["wrong_timeline"] = rejection_reasons.get("wrong_timeline", 0) + 1
                elif "budget" in reason or "cost" in reason:
                    rejection_reasons["budget_issues"] = rejection_reasons.get("budget_issues", 0) + 1
                else:
                    rejection_reasons["other"] = rejection_reasons.get("other", 0) + 1
        
        # Convert to frequencies
        if total_rejections > 0:
            for reason in rejection_reasons:
                rejection_reasons[reason] = rejection_reasons[reason] / total_rejections
        
        return rejection_reasons
    
    def _create_adjustment_for_reason(self, reason: str, frequency: float) -> Optional[ScoringAdjustment]:
        """Create scoring adjustment based on rejection reason"""
        
        adjustments = {
            "low_quality": ScoringAdjustment(
                factor_name="technical_engagement_score",
                current_weight=0.3,
                adjusted_weight=0.35,
                adjustment_reason=f"High frequency of low quality rejections ({frequency:.0%})",
                confidence_level=0.7,
                effective_date=datetime.utcnow(),
                performance_impact=0.05
            ),
            "unqualified": ScoringAdjustment(
                factor_name="base_qualification_weight",
                current_weight=0.4,
                adjusted_weight=0.45,
                adjustment_reason=f"High frequency of unqualified rejections ({frequency:.0%})",
                confidence_level=0.8,
                effective_date=datetime.utcnow(),
                performance_impact=0.1
            ),
            "wrong_geography": ScoringAdjustment(
                factor_name="nyc_market_intelligence_weight",
                current_weight=0.1,
                adjusted_weight=0.15,
                adjustment_reason=f"High frequency of geography rejections ({frequency:.0%})",
                confidence_level=0.6,
                effective_date=datetime.utcnow(),
                performance_impact=0.05
            ),
            "wrong_timeline": ScoringAdjustment(
                factor_name="market_timing_weight",
                current_weight=0.2,
                adjusted_weight=0.25,
                adjustment_reason=f"High frequency of timeline rejections ({frequency:.0%})",
                confidence_level=0.7,
                effective_date=datetime.utcnow(),
                performance_impact=0.08
            ),
            "budget_issues": ScoringAdjustment(
                factor_name="bill_amount_scoring",
                current_weight=0.2,
                adjusted_weight=0.25,
                adjustment_reason=f"High frequency of budget rejections ({frequency:.0%})",
                confidence_level=0.6,
                effective_date=datetime.utcnow(),
                performance_impact=0.06
            )
        }
        
        return adjustments.get(reason)
    
    async def _apply_scoring_adjustment(self, adjustment: ScoringAdjustment):
        """Apply scoring adjustment to the system"""
        
        try:
            # Store adjustment
            self.scoring_adjustments.append(adjustment)
            
            # Update Redis cache with new weights
            cache_key = "scoring_weights"
            current_weights = self.redis_client.get(cache_key)
            
            if current_weights:
                weights = json.loads(current_weights)
            else:
                weights = {}
            
            weights[adjustment.factor_name] = adjustment.adjusted_weight
            weights["last_updated"] = datetime.utcnow().isoformat()
            
            self.redis_client.setex(cache_key, 86400, json.dumps(weights))  # 24 hour cache
            
            # Log adjustment
            print(f"Applied scoring adjustment: {adjustment.factor_name} "
                  f"{adjustment.current_weight} -> {adjustment.adjusted_weight} "
                  f"(Reason: {adjustment.adjustment_reason})")
            
        except Exception as e:
            print(f"Error applying scoring adjustment: {e}")
    
    async def _analyze_quality_trends(self):
        """Background task to analyze quality trends"""
        
        while True:
            try:
                # Analyze trends for each buyer
                for buyer_id, metrics in self.quality_metrics.items():
                    if len(metrics.quality_trend) >= 7:  # At least a week of data
                        trend_analysis = self._analyze_quality_trend(metrics.quality_trend)
                        
                        if trend_analysis["trend"] == "declining":
                            # Create adjustment for declining quality
                            adjustment = ScoringAdjustment(
                                factor_name="overall_quality_threshold",
                                current_weight=0.5,
                                adjusted_weight=0.55,
                                adjustment_reason=f"Declining quality trend for {buyer_id}",
                                confidence_level=0.6,
                                effective_date=datetime.utcnow(),
                                performance_impact=0.05
                            )
                            await self._apply_scoring_adjustment(adjustment)
                
                # Wait 1 hour before next analysis
                await asyncio.sleep(3600)
                
            except Exception as e:
                print(f"Error analyzing quality trends: {e}")
                await asyncio.sleep(3600)
    
    def _analyze_quality_trend(self, quality_trend: List[Tuple[datetime, float]]) -> Dict[str, Any]:
        """Analyze quality trend over time"""
        
        if len(quality_trend) < 7:
            return {"trend": "insufficient_data"}
        
        # Get recent vs. older scores
        recent_scores = [score for _, score in quality_trend[-7:]]  # Last 7 data points
        older_scores = [score for _, score in quality_trend[:-7]]  # Earlier data points
        
        if not older_scores:
            return {"trend": "insufficient_data"}
        
        recent_avg = np.mean(recent_scores)
        older_avg = np.mean(older_scores)
        
        # Calculate trend
        if recent_avg > older_avg * 1.1:
            trend = "improving"
        elif recent_avg < older_avg * 0.9:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "recent_avg": recent_avg,
            "older_avg": older_avg,
            "change_percent": ((recent_avg - older_avg) / older_avg) * 100
        }
    
    async def _update_scoring_algorithms(self):
        """Background task to update scoring algorithms"""
        
        while True:
            try:
                # Get current scoring weights from Redis
                cache_key = "scoring_weights"
                weights_data = self.redis_client.get(cache_key)
                
                if weights_data:
                    weights = json.loads(weights_data)
                    
                    # Check if weights need updating
                    last_updated = datetime.fromisoformat(weights.get("last_updated", "2023-01-01"))
                    if (datetime.utcnow() - last_updated).days >= 1:  # Update daily
                        await self._recalculate_optimal_weights()
                
                # Wait 6 hours before next update
                await asyncio.sleep(21600)
                
            except Exception as e:
                print(f"Error updating scoring algorithms: {e}")
                await asyncio.sleep(21600)
    
    async def _recalculate_optimal_weights(self):
        """Recalculate optimal scoring weights based on feedback"""
        
        try:
            # Analyze feedback patterns to determine optimal weights
            feedback_analysis = await self._analyze_feedback_patterns()
            
            # Calculate new weights based on analysis
            new_weights = self._calculate_optimal_weights(feedback_analysis)
            
            # Update Redis cache
            cache_key = "scoring_weights"
            new_weights["last_updated"] = datetime.utcnow().isoformat()
            self.redis_client.setex(cache_key, 86400, json.dumps(new_weights))
            
            print(f"Updated scoring weights: {new_weights}")
            
        except Exception as e:
            print(f"Error recalculating optimal weights: {e}")
    
    async def _analyze_feedback_patterns(self) -> Dict[str, Any]:
        """Analyze feedback patterns to inform weight adjustments"""
        
        analysis = {
            "total_feedback": len(self.feedback_history),
            "acceptance_rate": 0.0,
            "conversion_rate": 0.0,
            "quality_factors": {},
            "buyer_preferences": {}
        }
        
        if not self.feedback_history:
            return analysis
        
        # Calculate overall rates
        accepted = sum(1 for f in self.feedback_history if f.feedback_type == "accepted")
        converted = sum(1 for f in self.feedback_history if f.feedback_type == "converted")
        
        analysis["acceptance_rate"] = accepted / len(self.feedback_history)
        analysis["conversion_rate"] = converted / len(self.feedback_history)
        
        # Analyze quality factors
        quality_scores = [f.feedback_score for f in self.feedback_history if f.feedback_score > 0]
        if quality_scores:
            analysis["quality_factors"]["avg_score"] = np.mean(quality_scores)
            analysis["quality_factors"]["score_std"] = np.std(quality_scores)
        
        # Analyze buyer preferences
        for buyer_id, metrics in self.quality_metrics.items():
            analysis["buyer_preferences"][buyer_id] = {
                "acceptance_rate": metrics.acceptance_rate,
                "conversion_rate": metrics.conversion_rate,
                "avg_score": metrics.avg_feedback_score
            }
        
        return analysis
    
    def _calculate_optimal_weights(self, feedback_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate optimal scoring weights based on feedback analysis"""
        
        # Base weights
        weights = {
            "base_qualification_weight": 0.4,
            "behavioral_scoring_weight": 0.3,
            "market_timing_weight": 0.2,
            "nyc_market_intelligence_weight": 0.1
        }
        
        # Adjust based on feedback patterns
        if feedback_analysis["acceptance_rate"] < 0.8:  # Low acceptance rate
            # Increase qualification weight
            weights["base_qualification_weight"] = min(0.5, weights["base_qualification_weight"] + 0.05)
            weights["behavioral_scoring_weight"] = max(0.25, weights["behavioral_scoring_weight"] - 0.05)
        
        if feedback_analysis["conversion_rate"] < 0.6:  # Low conversion rate
            # Increase behavioral scoring weight
            weights["behavioral_scoring_weight"] = min(0.35, weights["behavioral_scoring_weight"] + 0.05)
            weights["market_timing_weight"] = max(0.15, weights["market_timing_weight"] - 0.05)
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        for factor in weights:
            weights[factor] = weights[factor] / total_weight
        
        return weights
    
    async def get_feedback_analysis(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> FeedbackAnalysis:
        """Get comprehensive feedback analysis"""
        
        try:
            # Filter feedback by date range
            period_feedback = [
                f for f in self.feedback_history
                if start_date <= f.feedback_timestamp <= end_date
            ]
            
            if not period_feedback:
                return FeedbackAnalysis(
                    analysis_period=(start_date, end_date),
                    total_feedback_received=0,
                    overall_acceptance_rate=0.0,
                    overall_conversion_rate=0.0,
                    quality_improvements=[],
                    buyer_performance={},
                    recommendations=[],
                    next_review_date=datetime.utcnow() + timedelta(days=7)
                )
            
            # Calculate overall metrics
            total_feedback = len(period_feedback)
            accepted = sum(1 for f in period_feedback if f.feedback_type == "accepted")
            converted = sum(1 for f in period_feedback if f.feedback_type == "converted")
            
            overall_acceptance_rate = accepted / total_feedback
            overall_conversion_rate = converted / total_feedback
            
            # Get quality improvements from scoring adjustments
            period_adjustments = [
                adj for adj in self.scoring_adjustments
                if start_date <= adj.effective_date <= end_date
            ]
            
            # Get buyer performance
            buyer_performance = {}
            for buyer_id, metrics in self.quality_metrics.items():
                buyer_performance[buyer_id] = metrics
            
            # Generate recommendations
            recommendations = self._generate_feedback_recommendations(
                overall_acceptance_rate,
                overall_conversion_rate,
                period_adjustments
            )
            
            return FeedbackAnalysis(
                analysis_period=(start_date, end_date),
                total_feedback_received=total_feedback,
                overall_acceptance_rate=overall_acceptance_rate,
                overall_conversion_rate=overall_conversion_rate,
                quality_improvements=period_adjustments,
                buyer_performance=buyer_performance,
                recommendations=recommendations,
                next_review_date=datetime.utcnow() + timedelta(days=7)
            )
            
        except Exception as e:
            print(f"Error getting feedback analysis: {e}")
            return FeedbackAnalysis(
                analysis_period=(start_date, end_date),
                total_feedback_received=0,
                overall_acceptance_rate=0.0,
                overall_conversion_rate=0.0,
                quality_improvements=[],
                buyer_performance={},
                recommendations=[],
                next_review_date=datetime.utcnow() + timedelta(days=7)
            )
    
    def _generate_feedback_recommendations(
        self,
        acceptance_rate: float,
        conversion_rate: float,
        adjustments: List[ScoringAdjustment]
    ) -> List[str]:
        """Generate recommendations based on feedback analysis"""
        
        recommendations = []
        
        if acceptance_rate < 0.8:
            recommendations.append("Improve lead qualification criteria to increase acceptance rate")
        
        if conversion_rate < 0.6:
            recommendations.append("Focus on behavioral scoring to improve conversion rate")
        
        if len(adjustments) > 5:
            recommendations.append("Consider stabilizing scoring algorithm - too many recent adjustments")
        
        if acceptance_rate > 0.9 and conversion_rate < 0.5:
            recommendations.append("Review buyer selection criteria - high acceptance but low conversion")
        
        if not recommendations:
            recommendations.append("Quality metrics are performing well - continue current approach")
        
        return recommendations
