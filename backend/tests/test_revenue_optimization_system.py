"""
Unit tests for Revenue Optimization System
Tests all revenue optimization engines and their integration
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.revenue_optimization_engine import (
    RealTimeLeadScoringEngine,
    LeadQualityTier,
    RealTimeLeadScore,
    RevenueOptimizationConfig
)
from app.services.b2b_value_optimizer import (
    B2BValueOptimizer,
    B2BBuyerTier,
    B2BBuyerCapacity,
    RoutingDecision
)
from app.services.conversation_revenue_tracker import (
    ConversationRevenueTracker,
    ConversationRevenueState
)
from app.services.quality_feedback_loop import (
    QualityFeedbackLoop,
    BuyerFeedback
)
from app.services.revenue_analytics_engine import (
    RevenueAnalyticsEngine,
    RevenueDashboard,
    RevenueForecast
)
from app.services.revenue_optimization_system import (
    RevenueOptimizationSystem,
    RevenueOptimizationConfig as SystemConfig
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = Mock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.keys.return_value = []
    redis_mock.lpush.return_value = True
    redis_mock.rpop.return_value = None
    return redis_mock


@pytest.fixture
def revenue_optimization_system(mock_db, mock_redis):
    """Revenue optimization system instance"""
    return RevenueOptimizationSystem(mock_db, mock_redis)


class TestRealTimeLeadScoringEngine:
    """Test RealTimeLeadScoringEngine"""
    
    def test_calculate_real_time_score_basic(self, mock_db, mock_redis):
        """Test basic lead scoring calculation"""
        engine = RealTimeLeadScoringEngine(mock_db, mock_redis)
        
        conversation_context = {
            "homeowner_verified": True,
            "bill_amount": 350.0,
            "zip_code": "10021",
            "borough": "manhattan",
            "neighborhood": "upper_east_side",
            "home_type": "condo"
        }
        
        conversation_history = [
            {"intent": "technical_question", "sentiment": 0.8, "high_intent_signal": True},
            {"intent": "general_question", "sentiment": 0.6, "objection_resolved": True}
        ]
        
        # Test scoring calculation
        score = asyncio.run(engine.calculate_real_time_score(
            "session_123",
            conversation_context,
            conversation_history
        ))
        
        assert isinstance(score, RealTimeLeadScore)
        assert score.session_id == "session_123"
        assert score.total_score > 0
        assert score.quality_tier in [LeadQualityTier.PREMIUM, LeadQualityTier.STANDARD, LeadQualityTier.BASIC, LeadQualityTier.UNQUALIFIED]
        assert score.revenue_potential > 0
        assert 0 <= score.conversion_probability <= 1
    
    def test_calculate_real_time_score_unqualified(self, mock_db, mock_redis):
        """Test scoring for unqualified lead"""
        engine = RealTimeLeadScoringEngine(mock_db, mock_redis)
        
        conversation_context = {
            "homeowner_verified": False,  # Not homeowner
            "bill_amount": 100.0,  # Low bill
            "zip_code": "10021"
        }
        
        conversation_history = []
        
        score = asyncio.run(engine.calculate_real_time_score(
            "session_456",
            conversation_context,
            conversation_history
        ))
        
        assert score.quality_tier == LeadQualityTier.UNQUALIFIED
        assert score.revenue_potential == 0.0
        assert score.conversion_probability < 0.5
    
    def test_calculate_real_time_score_premium(self, mock_db, mock_redis):
        """Test scoring for premium lead"""
        engine = RealTimeLeadScoringEngine(mock_db, mock_redis)
        
        conversation_context = {
            "homeowner_verified": True,
            "bill_amount": 450.0,  # High bill
            "zip_code": "10021",
            "borough": "manhattan",
            "neighborhood": "upper_east_side",
            "home_type": "single_family",
            "timeline": "2025 spring",
            "decision_maker": True,
            "credit_indicators": ["financing", "pre_approved"]
        }
        
        conversation_history = [
            {"intent": "technical_question", "sentiment": 0.9, "high_intent_signal": True},
            {"intent": "technical_question", "sentiment": 0.8, "objection_resolved": True},
            {"intent": "technical_question", "sentiment": 0.9, "high_intent_signal": True}
        ]
        
        score = asyncio.run(engine.calculate_real_time_score(
            "session_789",
            conversation_context,
            conversation_history
        ))
        
        assert score.quality_tier == LeadQualityTier.PREMIUM
        assert score.revenue_potential >= 200.0
        assert score.conversion_probability >= 0.7
    
    def test_nyc_market_intelligence_scoring(self, mock_db, mock_redis):
        """Test NYC market intelligence scoring"""
        engine = RealTimeLeadScoringEngine(mock_db, mock_redis)
        
        # Test Manhattan (premium area)
        manhattan_context = {
            "homeowner_verified": True,
            "bill_amount": 300.0,
            "borough": "manhattan",
            "neighborhood": "upper_east_side"
        }
        
        manhattan_score = asyncio.run(engine.calculate_real_time_score(
            "session_manhattan",
            manhattan_context,
            []
        ))
        
        # Test Bronx (lower value area)
        bronx_context = {
            "homeowner_verified": True,
            "bill_amount": 300.0,
            "borough": "bronx",
            "neighborhood": "south_bronx"
        }
        
        bronx_score = asyncio.run(engine.calculate_real_time_score(
            "session_bronx",
            bronx_context,
            []
        ))
        
        # Manhattan should score higher due to market intelligence
        assert manhattan_score.nyc_intelligence_score > bronx_score.nyc_intelligence_score


class TestB2BValueOptimizer:
    """Test B2BValueOptimizer"""
    
    def test_calculate_dynamic_pricing(self, mock_db, mock_redis):
        """Test dynamic pricing calculation"""
        optimizer = B2BValueOptimizer(mock_db, mock_redis)
        
        # Test premium tier pricing
        price = asyncio.run(optimizer.calculate_dynamic_pricing(
            B2BBuyerTier.PREMIUM,
            85,  # High quality score
            {"borough": "manhattan", "neighborhood": "upper_east_side"}
        ))
        
        assert price > 200.0  # Should be above base price due to quality and location
    
    def test_optimize_buyer_routing(self, mock_db, mock_redis):
        """Test buyer routing optimization"""
        optimizer = B2BValueOptimizer(mock_db, mock_redis)
        
        # Mock buyer capacities
        optimizer.buyer_capacities = {
            "solarreviews": B2BBuyerCapacity(
                buyer_id="solarreviews",
                buyer_name="SolarReviews",
                tier=B2BBuyerTier.PREMIUM,
                daily_capacity=50,
                current_daily_count=30,
                weekly_capacity=300,
                current_weekly_count=200,
                price_per_lead=250.0,
                acceptance_rate=0.85,
                avg_lead_value=280.0,
                is_available=True
            ),
            "modernize": B2BBuyerCapacity(
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
        }
        
        routing_decision = asyncio.run(optimizer.optimize_buyer_routing(
            "lead_123",
            "session_123",
            85,  # High quality score
            {"borough": "manhattan", "bill_amount": 400.0}
        ))
        
        assert isinstance(routing_decision, RoutingDecision)
        assert routing_decision.lead_id == "lead_123"
        assert routing_decision.session_id == "session_123"
        assert routing_decision.price_per_lead > 0
        assert routing_decision.expected_revenue > 0
        assert routing_decision.confidence_score > 0
    
    def test_surge_pricing_calculation(self, mock_db, mock_redis):
        """Test surge pricing calculation"""
        optimizer = B2BValueOptimizer(mock_db, mock_redis)
        
        # Test normal pricing
        normal_price = asyncio.run(optimizer.calculate_dynamic_pricing(
            B2BBuyerTier.STANDARD,
            70,
            {"borough": "brooklyn"}
        ))
        
        # Test with high demand (would trigger surge pricing)
        with patch.object(optimizer, '_calculate_surge_multiplier', return_value=1.5):
            surge_price = asyncio.run(optimizer.calculate_dynamic_pricing(
                B2BBuyerTier.STANDARD,
                70,
                {"borough": "brooklyn"}
            ))
        
        assert surge_price > normal_price


class TestConversationRevenueTracker:
    """Test ConversationRevenueTracker"""
    
    def test_start_conversation_tracking(self, mock_db, mock_redis):
        """Test starting conversation tracking"""
        tracker = ConversationRevenueTracker(mock_db, mock_redis)
        
        revenue_state = asyncio.run(tracker.start_conversation_tracking(
            "session_123",
            "lead_123",
            {"borough": "manhattan"}
        ))
        
        assert isinstance(revenue_state, ConversationRevenueState)
        assert revenue_state.session_id == "session_123"
        assert revenue_state.lead_id == "lead_123"
        assert revenue_state.start_time is not None
        assert revenue_state.current_duration == 0
    
    def test_update_conversation_revenue(self, mock_db, mock_redis):
        """Test updating conversation revenue"""
        tracker = ConversationRevenueTracker(mock_db, mock_redis)
        
        # Start tracking
        revenue_state = asyncio.run(tracker.start_conversation_tracking("session_123"))
        
        # Create mock lead score
        lead_score = RealTimeLeadScore(
            session_id="session_123",
            lead_id="lead_123",
            base_score=80,
            behavioral_score=75,
            market_timing_score=85,
            nyc_intelligence_score=90,
            total_score=82,
            quality_tier=LeadQualityTier.STANDARD,
            revenue_potential=150.0,
            conversion_probability=0.75,
            optimal_buyer_tier=B2BBuyerTier.STANDARD,
            last_updated=datetime.utcnow(),
            scoring_factors={}
        )
        
        # Update conversation
        conversation_update = {
            "questions_asked": 2,
            "technical_engagement_score": 0.6,
            "urgency_created": True,
            "conversation_stage": "qualification"
        }
        
        updated_state = asyncio.run(tracker.update_conversation_revenue(
            "session_123",
            conversation_update,
            lead_score
        ))
        
        assert updated_state.questions_asked == 2
        assert updated_state.technical_engagement_score == 0.6
        assert updated_state.urgency_created is True
        assert updated_state.revenue_potential == 150.0
        assert updated_state.quality_tier == LeadQualityTier.STANDARD
    
    def test_end_conversation_tracking(self, mock_db, mock_redis):
        """Test ending conversation tracking"""
        tracker = ConversationRevenueTracker(mock_db, mock_redis)
        
        # Start tracking
        revenue_state = asyncio.run(tracker.start_conversation_tracking("session_123"))
        
        # End tracking
        final_state = asyncio.run(tracker.end_conversation_tracking(
            "session_123",
            175.0,  # Final revenue
            True    # Conversion success
        ))
        
        assert final_state.revenue_potential == 175.0
        assert final_state.conversion_probability == 1.0


class TestQualityFeedbackLoop:
    """Test QualityFeedbackLoop"""
    
    def test_submit_buyer_feedback(self, mock_db, mock_redis):
        """Test submitting buyer feedback"""
        feedback_loop = QualityFeedbackLoop(mock_db, mock_redis)
        
        feedback = asyncio.run(feedback_loop.submit_buyer_feedback(
            "lead_123",
            "solarreviews",
            "accepted",
            8.5,
            "High quality lead with good technical engagement",
            275.0,
            "Customer was very engaged"
        ))
        
        assert isinstance(feedback, BuyerFeedback)
        assert feedback.lead_id == "lead_123"
        assert feedback.buyer_id == "solarreviews"
        assert feedback.feedback_type == "accepted"
        assert feedback.feedback_score == 8.5
        assert feedback.conversion_value == 275.0
    
    def test_quality_metrics_update(self, mock_db, mock_redis):
        """Test quality metrics update"""
        feedback_loop = QualityFeedbackLoop(mock_db, mock_redis)
        
        # Submit multiple feedbacks
        asyncio.run(feedback_loop.submit_buyer_feedback(
            "lead_1", "solarreviews", "accepted", 8.0, "Good lead", 250.0
        ))
        asyncio.run(feedback_loop.submit_buyer_feedback(
            "lead_2", "solarreviews", "accepted", 9.0, "Excellent lead", 300.0
        ))
        asyncio.run(feedback_loop.submit_buyer_feedback(
            "lead_3", "solarreviews", "rejected", 4.0, "Low quality", None
        ))
        
        # Check metrics
        assert "solarreviews" in feedback_loop.quality_metrics
        metrics = feedback_loop.quality_metrics["solarreviews"]
        assert metrics.total_leads_received == 3
        assert metrics.leads_accepted == 2
        assert metrics.leads_rejected == 1
        assert metrics.acceptance_rate == 2/3
        assert metrics.avg_feedback_score == (8.0 + 9.0 + 4.0) / 3


class TestRevenueAnalyticsEngine:
    """Test RevenueAnalyticsEngine"""
    
    def test_get_revenue_dashboard(self, mock_db, mock_redis):
        """Test getting revenue dashboard"""
        analytics = RevenueAnalyticsEngine(mock_db, mock_redis)
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        dashboard = asyncio.run(analytics.get_revenue_dashboard())
        
        assert isinstance(dashboard, RevenueDashboard)
        assert dashboard.current_hour_revenue >= 0
        assert dashboard.today_revenue >= 0
        assert dashboard.week_revenue >= 0
        assert dashboard.month_revenue >= 0
        assert dashboard.active_conversations >= 0
        assert 0 <= dashboard.conversion_rate <= 1
    
    def test_generate_revenue_forecast(self, mock_db, mock_redis):
        """Test revenue forecast generation"""
        analytics = RevenueAnalyticsEngine(mock_db, mock_redis)
        
        # Mock historical data
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        forecast = asyncio.run(analytics.generate_revenue_forecast("daily", 7))
        
        assert isinstance(forecast, RevenueForecast)
        assert forecast.forecast_period == "daily"
        assert 0 <= forecast.accuracy_score <= 1
        assert forecast.trend_direction in ["increasing", "decreasing", "stable", "unknown"]
    
    def test_get_optimization_recommendations(self, mock_db, mock_redis):
        """Test getting optimization recommendations"""
        analytics = RevenueAnalyticsEngine(mock_db, mock_redis)
        
        # Mock dashboard data
        with patch.object(analytics, 'get_revenue_dashboard') as mock_dashboard:
            mock_dashboard.return_value = RevenueDashboard(
                current_hour_revenue=0.0,
                today_revenue=0.0,
                week_revenue=0.0,
                month_revenue=0.0,
                active_conversations=0,
                conversion_rate=0.5,  # Low conversion rate
                avg_revenue_per_conversation=100.0,  # Low revenue per conversation
                revenue_per_hour=20.0,  # Low revenue per hour
                top_performing_buyers=[],
                quality_tier_distribution={},
                revenue_trend=[],
                alerts=[]
            )
            
            recommendations = asyncio.run(analytics.get_optimization_recommendations())
            
            assert len(recommendations) > 0
            assert all(rec.priority in ["high", "medium", "low"] for rec in recommendations)
            assert all(rec.expected_impact > 0 for rec in recommendations)


class TestRevenueOptimizationSystem:
    """Test RevenueOptimizationSystem integration"""
    
    def test_process_conversation_for_revenue_optimization(self, revenue_optimization_system):
        """Test end-to-end conversation processing with revenue optimization"""
        
        conversation_context = {
            "homeowner_verified": True,
            "bill_amount": 400.0,
            "zip_code": "10021",
            "borough": "manhattan",
            "neighborhood": "upper_east_side",
            "home_type": "condo"
        }
        
        conversation_history = [
            {"intent": "technical_question", "sentiment": 0.8, "high_intent_signal": True},
            {"intent": "general_question", "sentiment": 0.6, "objection_resolved": True}
        ]
        
        response = asyncio.run(revenue_optimization_system.process_conversation_for_revenue_optimization(
            "session_123",
            "I'm interested in solar for my co-op in Manhattan",
            conversation_context,
            conversation_history
        ))
        
        assert "content" in response
        assert "revenue_optimization" in response
        assert "lead_score" in response["revenue_optimization"]
        assert "conversation_metrics" in response["revenue_optimization"]
        assert "optimization_recommendations" in response["revenue_optimization"]
    
    def test_submit_buyer_feedback(self, revenue_optimization_system):
        """Test submitting buyer feedback through the main system"""
        
        feedback = asyncio.run(revenue_optimization_system.submit_buyer_feedback(
            "lead_123",
            "solarreviews",
            "accepted",
            8.5,
            "High quality lead with good technical engagement",
            275.0,
            "Customer was very engaged"
        ))
        
        assert isinstance(feedback, BuyerFeedback)
        assert feedback.lead_id == "lead_123"
        assert feedback.buyer_id == "solarreviews"
    
    def test_get_revenue_dashboard(self, revenue_optimization_system):
        """Test getting revenue dashboard through the main system"""
        
        dashboard = asyncio.run(revenue_optimization_system.get_revenue_dashboard())
        
        assert isinstance(dashboard, RevenueDashboard)
        assert dashboard.current_hour_revenue >= 0
        assert dashboard.today_revenue >= 0
    
    def test_get_comprehensive_metrics(self, revenue_optimization_system):
        """Test getting comprehensive metrics"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        metrics = asyncio.run(revenue_optimization_system.get_comprehensive_metrics(
            start_date, end_date
        ))
        
        assert metrics.total_conversations >= 0
        assert metrics.total_revenue >= 0
        assert 0 <= metrics.conversion_rate <= 1
        assert metrics.avg_revenue_per_conversation >= 0
        assert metrics.revenue_per_hour >= 0
        assert 0 <= metrics.optimization_score <= 100


class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    def test_high_value_lead_processing(self, revenue_optimization_system):
        """Test processing a high-value lead through the entire system"""
        
        # High-value lead context
        conversation_context = {
            "homeowner_verified": True,
            "bill_amount": 500.0,  # High bill
            "zip_code": "10021",   # Premium area
            "borough": "manhattan",
            "neighborhood": "upper_east_side",
            "home_type": "single_family",
            "timeline": "2025 spring",
            "decision_maker": True,
            "credit_indicators": ["financing", "pre_approved"]
        }
        
        conversation_history = [
            {"intent": "technical_question", "sentiment": 0.9, "high_intent_signal": True},
            {"intent": "technical_question", "sentiment": 0.8, "objection_resolved": True},
            {"intent": "technical_question", "sentiment": 0.9, "high_intent_signal": True}
        ]
        
        response = asyncio.run(revenue_optimization_system.process_conversation_for_revenue_optimization(
            "session_premium",
            "I'm ready to move forward with solar installation",
            conversation_context,
            conversation_history
        ))
        
        # Should be classified as premium lead
        lead_score = response["revenue_optimization"]["lead_score"]
        assert lead_score["quality_tier"] == "premium"
        assert lead_score["revenue_potential"] >= 200.0
        assert lead_score["conversion_probability"] >= 0.7
    
    def test_low_value_lead_processing(self, revenue_optimization_system):
        """Test processing a low-value lead through the entire system"""
        
        # Low-value lead context
        conversation_context = {
            "homeowner_verified": True,
            "bill_amount": 150.0,  # Low bill
            "zip_code": "10451",   # Lower value area
            "borough": "bronx",
            "neighborhood": "south_bronx",
            "home_type": "co_op"
        }
        
        conversation_history = [
            {"intent": "general_question", "sentiment": 0.4, "high_intent_signal": False}
        ]
        
        response = asyncio.run(revenue_optimization_system.process_conversation_for_revenue_optimization(
            "session_basic",
            "I'm just looking into solar",
            conversation_context,
            conversation_history
        ))
        
        # Should be classified as basic or unqualified lead
        lead_score = response["revenue_optimization"]["lead_score"]
        assert lead_score["quality_tier"] in ["basic", "unqualified"]
        assert lead_score["revenue_potential"] < 200.0
        assert lead_score["conversion_probability"] < 0.7
    
    def test_feedback_integration_flow(self, revenue_optimization_system):
        """Test the complete feedback integration flow"""
        
        # Process a conversation
        conversation_context = {
            "homeowner_verified": True,
            "bill_amount": 350.0,
            "zip_code": "11215",
            "borough": "brooklyn",
            "neighborhood": "park_slope"
        }
        
        response = asyncio.run(revenue_optimization_system.process_conversation_for_revenue_optimization(
            "session_feedback_test",
            "I'm interested in solar for my brownstone",
            conversation_context,
            []
        ))
        
        # Submit buyer feedback
        feedback = asyncio.run(revenue_optimization_system.submit_buyer_feedback(
            "lead_feedback_test",
            "solarreviews",
            "accepted",
            8.0,
            "Good quality lead",
            200.0,
            "Customer was engaged"
        ))
        
        assert feedback.lead_id == "lead_feedback_test"
        assert feedback.feedback_type == "accepted"
        
        # Check that feedback is integrated into quality metrics
        feedback_loop = revenue_optimization_system.quality_feedback_loop
        assert "solarreviews" in feedback_loop.quality_metrics
        metrics = feedback_loop.quality_metrics["solarreviews"]
        assert metrics.total_leads_received == 1
        assert metrics.leads_accepted == 1
        assert metrics.acceptance_rate == 1.0


if __name__ == "__main__":
    pytest.main([__file__])
