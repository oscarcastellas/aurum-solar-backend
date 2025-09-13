"""
Analytics and performance tracking models
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.db_types import UUIDType, ArrayStringType, ArrayUUIDType, get_uuid_default
from app.core.database import Base
import uuid


class RevenueMetrics(Base):
    """
    Revenue and performance metrics with time-series data
    Optimized for analytics queries and reporting
    """
    __tablename__ = "revenue_metrics"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Time dimension
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), default="daily", index=True)  # daily, weekly, monthly, quarterly, yearly
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    day = Column(Integer, index=True)
    week = Column(Integer, index=True)
    quarter = Column(Integer, index=True)
    
    # Lead metrics
    total_leads = Column(Integer, default=0, index=True)
    new_leads = Column(Integer, default=0)
    qualified_leads = Column(Integer, default=0, index=True)
    exported_leads = Column(Integer, default=0, index=True)
    sold_leads = Column(Integer, default=0, index=True)
    lost_leads = Column(Integer, default=0)
    
    # Lead quality distribution
    hot_leads = Column(Integer, default=0)
    warm_leads = Column(Integer, default=0)
    cold_leads = Column(Integer, default=0)
    
    # Revenue metrics
    total_revenue = Column(Float, default=0.0, index=True)
    gross_revenue = Column(Float, default=0.0)
    net_revenue = Column(Float, default=0.0, index=True)
    commission_revenue = Column(Float, default=0.0, index=True)
    platform_fees = Column(Float, default=0.0)
    
    # Average metrics
    average_lead_value = Column(Float, default=0.0, index=True)
    average_lead_score = Column(Float, default=0.0, index=True)
    average_commission_rate = Column(Float, default=0.0)
    
    # Conversion rates
    qualification_rate = Column(Float, default=0.0, index=True)
    export_rate = Column(Float, default=0.0, index=True)
    sales_conversion_rate = Column(Float, default=0.0, index=True)
    overall_conversion_rate = Column(Float, default=0.0, index=True)
    
    # Growth metrics
    revenue_growth_rate = Column(Float, default=0.0, index=True)
    lead_growth_rate = Column(Float, default=0.0, index=True)
    month_over_month_growth = Column(Float, default=0.0)
    year_over_year_growth = Column(Float, default=0.0)
    
    # Platform breakdown
    platform_metrics = Column(JSON)  # Revenue and leads per platform
    source_breakdown = Column(JSON)  # Leads and revenue by source
    zip_code_breakdown = Column(JSON)  # Performance by NYC zip code
    borough_breakdown = Column(JSON)  # Performance by NYC borough
    
    # AI performance
    ai_analyzed_leads = Column(Integer, default=0)
    ai_accuracy_score = Column(Float, default=0.0)
    ai_conversion_improvement = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_revenue_date_period', 'date', 'period_type'),
        Index('idx_revenue_year_month', 'year', 'month'),
        Index('idx_revenue_qualified_sold', 'qualified_leads', 'sold_leads'),
        Index('idx_revenue_total_growth', 'total_revenue', 'revenue_growth_rate'),
        UniqueConstraint('date', 'period_type', name='uq_revenue_date_period'),
    )


class PlatformPerformance(Base):
    """
    B2B platform performance tracking
    Detailed metrics for each platform integration
    """
    __tablename__ = "platform_performance"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    platform_id = Column(UUIDType, ForeignKey("b2b_platforms.id"), nullable=False, index=True)
    
    # Time dimension
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), default="daily", index=True)
    
    # Export metrics
    leads_exported = Column(Integer, default=0, index=True)
    leads_accepted = Column(Integer, default=0, index=True)
    leads_rejected = Column(Integer, default=0, index=True)
    leads_pending = Column(Integer, default=0)
    
    # Performance rates
    acceptance_rate = Column(Float, default=0.0, index=True)
    rejection_rate = Column(Float, default=0.0)
    pending_rate = Column(Float, default=0.0)
    
    # Revenue metrics
    total_revenue = Column(Float, default=0.0, index=True)
    gross_revenue = Column(Float, default=0.0)
    net_revenue = Column(Float, default=0.0, index=True)
    commission_earned = Column(Float, default=0.0, index=True)
    platform_fees = Column(Float, default=0.0)
    
    # Pricing metrics
    average_price_per_lead = Column(Float, default=0.0, index=True)
    average_commission_rate = Column(Float, default=0.0)
    price_tier_breakdown = Column(JSON)  # Revenue by price tier
    
    # Quality metrics
    average_lead_score = Column(Float, default=0.0, index=True)
    average_lead_quality = Column(String(20), index=True)
    quality_score_distribution = Column(JSON)
    
    # Response metrics
    average_response_time_ms = Column(Float, default=0.0, index=True)
    fastest_response_ms = Column(Integer)
    slowest_response_ms = Column(Integer)
    
    # Error tracking
    export_errors = Column(Integer, default=0, index=True)
    api_errors = Column(Integer, default=0)
    timeout_errors = Column(Integer, default=0)
    validation_errors = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0, index=True)
    
    # Uptime and availability
    uptime_percentage = Column(Float, default=100.0, index=True)
    api_downtime_minutes = Column(Integer, default=0)
    maintenance_downtime_minutes = Column(Integer, default=0)
    
    # Customer satisfaction
    customer_satisfaction_score = Column(Float, default=0.0, index=True)
    customer_feedback_count = Column(Integer, default=0)
    complaint_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    platform = relationship("B2BPlatform")
    
    # Indexes
    __table_args__ = (
        Index('idx_platform_date_period', 'platform_id', 'date', 'period_type'),
        Index('idx_platform_acceptance_revenue', 'acceptance_rate', 'total_revenue'),
        Index('idx_platform_quality_score', 'average_lead_score', 'average_lead_quality'),
        Index('idx_platform_error_uptime', 'error_rate', 'uptime_percentage'),
        UniqueConstraint('platform_id', 'date', 'period_type', name='uq_platform_date_period'),
    )


class NYCMarketIntelligence(Base):
    """
    NYC market intelligence and trends
    Aggregated data for market analysis and decision making
    """
    __tablename__ = "nyc_market_intelligence"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Geographic dimension
    zip_code = Column(String(10), index=True)
    borough = Column(String(50), index=True)
    neighborhood = Column(String(100), index=True)
    
    # Time dimension
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), default="monthly", index=True)
    
    # Market size and penetration
    total_households = Column(Integer, default=0)
    solar_adopted_households = Column(Integer, default=0)
    solar_adoption_rate = Column(Float, default=0.0, index=True)
    market_potential_households = Column(Integer, default=0)
    market_penetration_rate = Column(Float, default=0.0, index=True)
    
    # Lead generation metrics
    leads_generated = Column(Integer, default=0, index=True)
    leads_per_household = Column(Float, default=0.0)
    lead_generation_rate = Column(Float, default=0.0, index=True)
    
    # Conversion metrics
    leads_qualified = Column(Integer, default=0)
    leads_sold = Column(Integer, default=0)
    qualification_rate = Column(Float, default=0.0, index=True)
    sales_conversion_rate = Column(Float, default=0.0, index=True)
    
    # Revenue metrics
    total_revenue = Column(Float, default=0.0, index=True)
    revenue_per_household = Column(Float, default=0.0)
    average_lead_value = Column(Float, default=0.0, index=True)
    average_sale_value = Column(Float, default=0.0, index=True)
    
    # Market characteristics
    average_home_value = Column(Float, default=0.0, index=True)
    median_household_income = Column(Float, default=0.0, index=True)
    average_electric_bill = Column(Float, default=0.0, index=True)
    average_electric_rate = Column(Float, default=0.0, index=True)
    
    # Solar potential
    average_roof_size = Column(Float, default=0.0)
    average_system_size = Column(Float, default=0.0)
    average_installation_cost = Column(Float, default=0.0)
    average_savings_per_month = Column(Float, default=0.0)
    average_payback_period = Column(Float, default=0.0)
    
    # Competition analysis
    active_installers = Column(Integer, default=0, index=True)
    new_installers = Column(Integer, default=0)
    installer_density = Column(Float, default=0.0, index=True)
    market_competition_score = Column(Float, default=0.0, index=True)
    
    # Incentive availability
    active_incentives_count = Column(Integer, default=0)
    total_incentive_value = Column(Float, default=0.0)
    incentive_effectiveness_score = Column(Float, default=0.0)
    
    # Market trends
    growth_rate = Column(Float, default=0.0, index=True)
    trend_direction = Column(String(20), index=True)  # growing, stable, declining
    market_maturity = Column(String(20), index=True)  # emerging, developing, mature, saturated
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_nyc_zip_date', 'zip_code', 'date'),
        Index('idx_nyc_borough_date', 'borough', 'date'),
        Index('idx_nyc_adoption_revenue', 'solar_adoption_rate', 'total_revenue'),
        Index('idx_nyc_competition_growth', 'market_competition_score', 'growth_rate'),
        Index('idx_nyc_trend_maturity', 'trend_direction', 'market_maturity'),
    )


class UserSession(Base):
    """
    User session tracking for engagement and conversion analysis
    """
    __tablename__ = "user_sessions"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=True, index=True)
    
    # Session identification
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_agent = Column(Text)
    ip_address = Column(String(45), index=True)
    
    # Geographic data
    country = Column(String(2), index=True)
    state = Column(String(50), index=True)
    city = Column(String(100), index=True)
    zip_code = Column(String(10), index=True)
    
    # Traffic source
    referrer_domain = Column(String(200), index=True)
    referrer_url = Column(Text)
    utm_source = Column(String(100), index=True)
    utm_medium = Column(String(100), index=True)
    utm_campaign = Column(String(100), index=True)
    utm_term = Column(String(100))
    utm_content = Column(String(100))
    
    # Session metrics
    page_views = Column(Integer, default=0, index=True)
    session_duration_seconds = Column(Integer, default=0, index=True)
    bounce_rate = Column(Float, default=0.0, index=True)
    conversion_events = Column(Integer, default=0, index=True)
    
    # Engagement metrics
    form_submissions = Column(Integer, default=0)
    button_clicks = Column(Integer, default=0)
    scroll_depth_percentage = Column(Float, default=0.0)
    time_on_site_seconds = Column(Integer, default=0)
    
    # Device and browser
    device_type = Column(String(50), index=True)  # desktop, mobile, tablet
    browser = Column(String(100), index=True)
    operating_system = Column(String(100), index=True)
    screen_resolution = Column(String(20))
    
    # Conversion tracking
    converted = Column(Boolean, default=False, index=True)
    conversion_type = Column(String(50), index=True)  # lead_form, phone_call, email
    conversion_value = Column(Float, default=0.0, index=True)
    conversion_timestamp = Column(DateTime(timezone=True), index=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ended_at = Column(DateTime(timezone=True), index=True)
    last_activity_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    lead = relationship("Lead")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_lead_converted', 'lead_id', 'converted'),
        Index('idx_session_source_medium', 'utm_source', 'utm_medium'),
        Index('idx_session_device_duration', 'device_type', 'session_duration_seconds'),
        Index('idx_session_started_ended', 'started_at', 'ended_at'),
        UniqueConstraint('session_id', name='uq_user_session_id'),
    )


class ConversationMetrics(Base):
    """
    Conversation and chat performance metrics
    """
    __tablename__ = "conversation_metrics"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Time dimension
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), default="daily", index=True)
    
    # Conversation metrics
    total_conversations = Column(Integer, default=0, index=True)
    completed_conversations = Column(Integer, default=0, index=True)
    abandoned_conversations = Column(Integer, default=0)
    avg_conversation_duration = Column(Float, default=0.0)
    avg_messages_per_conversation = Column(Float, default=0.0)
    
    # Lead generation metrics
    conversations_to_leads = Column(Integer, default=0, index=True)
    conversion_rate = Column(Float, default=0.0, index=True)
    avg_lead_value = Column(Float, default=0.0, index=True)
    
    # Quality metrics
    high_quality_leads = Column(Integer, default=0)
    medium_quality_leads = Column(Integer, default=0)
    low_quality_leads = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_metrics_date_period', 'date', 'period_type'),
        Index('idx_conversation_metrics_conversion', 'conversion_rate'),
    )