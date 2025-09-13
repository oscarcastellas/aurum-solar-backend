"""
Revenue Analytics Models
Comprehensive tracking for revenue optimization and B2B lead performance
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.db_types import UUIDType, ArrayStringType, get_uuid_default
import uuid


class RevenueTransaction(Base):
    """
    Track all revenue transactions from B2B lead sales
    Comprehensive attribution to conversations and leads
    """
    __tablename__ = "revenue_transactions"
    
    # Primary key
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Lead and conversation attribution
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    conversation_id = Column(UUIDType, ForeignKey("ai_conversations.id"), nullable=True, index=True)
    session_id = Column(String(100), index=True)
    
    # Revenue details
    transaction_type = Column(String(50), nullable=False, index=True)  # lead_sale, commission, bonus
    amount = Column(Float, nullable=False, index=True)
    currency = Column(String(3), default="USD")
    platform = Column(String(100), nullable=False, index=True)  # solarreviews, modernize, regional_nyc
    
    # Quality and performance metrics
    lead_quality_tier = Column(String(20), index=True)  # premium, standard, basic
    lead_score = Column(Integer, index=True)
    conversation_quality_score = Column(Float)
    qualification_confidence = Column(Float)
    
    # B2B buyer information
    buyer_id = Column(String(100), index=True)
    buyer_name = Column(String(200))
    buyer_acceptance_rate = Column(Float)
    
    # Transaction status
    status = Column(String(50), default="pending", index=True)  # pending, completed, failed, refunded
    payment_status = Column(String(50), default="pending", index=True)  # pending, paid, overdue
    payment_method = Column(String(50))  # api, bank_transfer, check
    
    # Performance tracking
    time_to_close = Column(Integer)  # hours from lead creation to sale
    conversation_duration_minutes = Column(Integer)
    messages_exchanged = Column(Integer)
    
    # Attribution data
    source_campaign = Column(String(100), index=True)
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    
    # NYC market context
    zip_code = Column(String(10), index=True)
    borough = Column(String(50), index=True)
    property_type = Column(String(50), index=True)
    monthly_bill = Column(Float, index=True)
    
    # Timestamps
    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    payment_date = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Metadata
    notes = Column(Text)
    metadata = Column(JSON)
    
    # Relationships
    lead = relationship("Lead", back_populates="revenue_transactions")
    conversation = relationship("AIConversation", back_populates="revenue_transactions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_revenue_platform_date', 'platform', 'transaction_date'),
        Index('idx_revenue_quality_amount', 'lead_quality_tier', 'amount'),
        Index('idx_revenue_zip_performance', 'zip_code', 'amount'),
        Index('idx_revenue_buyer_performance', 'buyer_name', 'status'),
        Index('idx_revenue_monthly_performance', 'transaction_date', 'amount'),
    )


class ConversationAnalytics(Base):
    """
    Track conversation performance and optimization metrics
    Real-time analytics for conversation-to-revenue conversion
    """
    __tablename__ = "conversation_analytics"
    
    # Primary key
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Conversation identification
    session_id = Column(String(100), nullable=False, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=True, index=True)
    
    # Conversation metrics
    total_messages = Column(Integer, default=0)
    user_messages = Column(Integer, default=0)
    ai_messages = Column(Integer, default=0)
    conversation_duration_minutes = Column(Integer, default=0)
    
    # Engagement metrics
    engagement_score = Column(Float, index=True)  # 0-1 scale
    response_time_avg = Column(Float)  # seconds
    conversation_quality_score = Column(Float, index=True)  # 0-100
    
    # Qualification metrics
    qualification_achieved = Column(Boolean, default=False, index=True)
    qualification_stage_reached = Column(String(50), index=True)
    objections_handled = Column(Integer, default=0)
    urgency_created = Column(Boolean, default=False, index=True)
    
    # Revenue potential
    estimated_lead_value = Column(Float, index=True)
    actual_revenue_generated = Column(Float, default=0.0, index=True)
    conversion_probability = Column(Float, index=True)  # 0-1 scale
    
    # Conversation flow analysis
    stages_completed = Column(ArrayStringType, default=[])
    stage_transition_times = Column(JSON)  # stage -> time in minutes
    drop_off_stage = Column(String(50), index=True)
    
    # AI performance metrics
    ai_model_used = Column(String(100))
    ai_confidence_scores = Column(JSON)  # average confidence per stage
    ai_response_quality = Column(Float)
    
    # NYC market context
    zip_code = Column(String(10), index=True)
    borough = Column(String(50), index=True)
    property_type = Column(String(50), index=True)
    monthly_bill = Column(Float, index=True)
    
    # A/B testing data
    ab_test_variant = Column(String(100), index=True)
    ab_test_group = Column(String(100), index=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), index=True)
    last_activity_at = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lead = relationship("Lead")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_conversation_engagement', 'engagement_score', 'qualification_achieved'),
        Index('idx_conversation_revenue', 'estimated_lead_value', 'actual_revenue_generated'),
        Index('idx_conversation_zip_performance', 'zip_code', 'conversion_probability'),
        Index('idx_conversation_ab_testing', 'ab_test_variant', 'ab_test_group'),
        Index('idx_conversation_time_performance', 'conversation_duration_minutes', 'qualification_achieved'),
    )


class LeadQualityAnalytics(Base):
    """
    Track lead quality performance and B2B buyer feedback
    Optimize lead scoring algorithms and quality classification
    """
    __tablename__ = "lead_quality_analytics"
    
    # Primary key
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Lead identification
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Quality assessment
    predicted_quality_tier = Column(String(20), nullable=False, index=True)  # premium, standard, basic
    predicted_lead_score = Column(Integer, nullable=False, index=True)
    predicted_value = Column(Float, nullable=False, index=True)
    
    # Actual performance
    actual_quality_tier = Column(String(20), index=True)  # Based on buyer feedback
    actual_lead_score = Column(Integer, index=True)
    actual_value = Column(Float, index=True)
    
    # B2B buyer feedback
    buyer_platform = Column(String(100), index=True)
    buyer_acceptance = Column(Boolean, index=True)  # accepted, rejected
    buyer_feedback_score = Column(Float)  # 1-10 scale
    buyer_feedback_reason = Column(Text)
    buyer_response_time_hours = Column(Float)
    
    # Quality accuracy metrics
    prediction_accuracy = Column(Float, index=True)  # 0-1 scale
    value_accuracy = Column(Float, index=True)  # predicted vs actual value
    tier_accuracy = Column(Boolean, index=True)  # predicted tier == actual tier
    
    # Lead characteristics
    conversation_count = Column(Integer)
    qualification_time_hours = Column(Float)
    engagement_level = Column(String(20), index=True)
    timeline_urgency = Column(String(20), index=True)
    
    # NYC market context
    zip_code = Column(String(10), index=True)
    borough = Column(String(50), index=True)
    property_type = Column(String(50), index=True)
    monthly_bill = Column(Float, index=True)
    
    # Model performance tracking
    model_version = Column(String(50), index=True)
    model_confidence = Column(Float)
    feature_importance = Column(JSON)  # Which features most influenced prediction
    
    # Timestamps
    predicted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    buyer_feedback_at = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lead = relationship("Lead")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_quality_prediction_accuracy', 'prediction_accuracy', 'predicted_quality_tier'),
        Index('idx_quality_buyer_feedback', 'buyer_platform', 'buyer_acceptance'),
        Index('idx_quality_zip_performance', 'zip_code', 'prediction_accuracy'),
        Index('idx_quality_model_performance', 'model_version', 'prediction_accuracy'),
        Index('idx_quality_tier_accuracy', 'tier_accuracy', 'predicted_quality_tier'),
    )


class MarketPerformanceAnalytics(Base):
    """
    Track NYC market performance and trends
    Geographic and temporal analysis for optimization
    """
    __tablename__ = "market_performance_analytics"
    
    # Primary key
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Geographic identification
    zip_code = Column(String(10), nullable=False, index=True)
    borough = Column(String(50), nullable=False, index=True)
    neighborhood = Column(String(100), index=True)
    
    # Time period
    period_type = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly, quarterly
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Lead generation metrics
    total_leads = Column(Integer, default=0)
    qualified_leads = Column(Integer, default=0)
    exported_leads = Column(Integer, default=0)
    sold_leads = Column(Integer, default=0)
    
    # Quality distribution
    premium_leads = Column(Integer, default=0)
    standard_leads = Column(Integer, default=0)
    basic_leads = Column(Integer, default=0)
    
    # Revenue metrics
    total_revenue = Column(Float, default=0.0)
    average_lead_value = Column(Float, default=0.0)
    revenue_per_zip = Column(Float, default=0.0)
    
    # Performance metrics
    qualification_rate = Column(Float, default=0.0)  # qualified_leads / total_leads
    conversion_rate = Column(Float, default=0.0)  # sold_leads / qualified_leads
    revenue_per_lead = Column(Float, default=0.0)  # total_revenue / sold_leads
    
    # Market context
    competition_level = Column(String(20), index=True)  # low, medium, high
    solar_adoption_rate = Column(Float)
    average_electric_rate = Column(Float)
    incentive_value = Column(Float)
    
    # Trend analysis
    growth_rate = Column(Float)  # period-over-period growth
    trend_direction = Column(String(20))  # up, down, stable
    seasonal_factor = Column(Float)
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_market_zip_period', 'zip_code', 'period_start'),
        Index('idx_market_borough_performance', 'borough', 'total_revenue'),
        Index('idx_market_trends', 'period_start', 'trend_direction'),
        Index('idx_market_competition', 'competition_level', 'revenue_per_lead'),
        UniqueConstraint('zip_code', 'period_type', 'period_start', name='uq_market_performance'),
    )


class RevenueOptimizationInsight(Base):
    """
    Store optimization insights and recommendations
    AI-powered recommendations for revenue improvement
    """
    __tablename__ = "revenue_optimization_insights"
    
    # Primary key
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Insight identification
    insight_type = Column(String(50), nullable=False, index=True)  # conversation, quality, market, pricing
    insight_category = Column(String(50), nullable=False, index=True)  # opportunity, issue, trend, recommendation
    priority = Column(String(20), nullable=False, index=True)  # high, medium, low
    
    # Insight details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text)
    
    # Impact assessment
    potential_revenue_impact = Column(Float, index=True)
    confidence_score = Column(Float, index=True)  # 0-1 scale
    implementation_effort = Column(String(20))  # low, medium, high
    
    # Data context
    affected_metrics = Column(ArrayStringType, default=[])
    data_period = Column(String(50))  # last_7_days, last_30_days, etc.
    sample_size = Column(Integer)
    
    # Geographic/temporal scope
    zip_code = Column(String(10), index=True)
    borough = Column(String(50), index=True)
    platform = Column(String(100), index=True)
    
    # Status tracking
    status = Column(String(50), default="active", index=True)  # active, implemented, dismissed, expired
    implemented_at = Column(DateTime(timezone=True), index=True)
    implementation_results = Column(JSON)
    
    # A/B testing
    ab_test_required = Column(Boolean, default=False)
    ab_test_id = Column(String(100), index=True)
    ab_test_results = Column(JSON)
    
    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_insight_type_priority', 'insight_type', 'priority'),
        Index('idx_insight_revenue_impact', 'potential_revenue_impact', 'confidence_score'),
        Index('idx_insight_status_expires', 'status', 'expires_at'),
        Index('idx_insight_geographic', 'zip_code', 'borough'),
    )


class DashboardMetrics(Base):
    """
    Pre-calculated dashboard metrics for real-time performance
    Optimized for fast dashboard loading
    """
    __tablename__ = "dashboard_metrics"
    
    # Primary key
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Metric identification
    metric_type = Column(String(50), nullable=False, index=True)  # revenue, leads, conversion, quality
    metric_name = Column(String(100), nullable=False, index=True)
    metric_category = Column(String(50), nullable=False, index=True)  # daily, weekly, monthly, real_time
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metric values
    current_value = Column(Float, nullable=False)
    previous_value = Column(Float)
    change_percentage = Column(Float)
    trend_direction = Column(String(20))  # up, down, stable
    
    # Geographic breakdown (optional)
    zip_code = Column(String(10), index=True)
    borough = Column(String(50), index=True)
    
    # Platform breakdown (optional)
    platform = Column(String(100), index=True)
    
    # Quality breakdown (optional)
    quality_tier = Column(String(20), index=True)
    
    # Metadata
    calculation_method = Column(String(100))
    data_points = Column(Integer)
    confidence_level = Column(Float)
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_dashboard_metric_type_period', 'metric_type', 'period_start'),
        Index('idx_dashboard_real_time_metrics', 'metric_category', 'calculated_at'),
        Index('idx_dashboard_geographic_metrics', 'zip_code', 'metric_type'),
        Index('idx_dashboard_platform_metrics', 'platform', 'metric_type'),
        UniqueConstraint('metric_name', 'period_start', 'zip_code', 'platform', 'quality_tier', name='uq_dashboard_metrics'),
    )
