"""
Lead management models with comprehensive tracking and analytics
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.db_types import UUIDType, ArrayStringType, get_uuid_default
import uuid


class Lead(Base):
    """
    Core lead model for solar prospects with comprehensive tracking
    Optimized for NYC market with performance indexing
    """
    __tablename__ = "leads"
    
    # Primary key with UUID for better distribution
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Contact information
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), index=True)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    
    # Property details - NYC specific
    property_address = Column(String(500), nullable=False, index=True)
    city = Column(String(100), default="New York", index=True)
    state = Column(String(2), default="NY", index=True)
    zip_code = Column(String(10), nullable=False, index=True)
    borough = Column(String(50), index=True)  # NYC specific
    
    # Property characteristics
    property_type = Column(String(50), index=True)  # residential, commercial, multi_family
    square_footage = Column(Integer, index=True)
    lot_size = Column(Float)  # For solar potential calculation
    roof_type = Column(String(50), index=True)
    roof_condition = Column(String(50), index=True)
    roof_age = Column(Integer)
    roof_slope = Column(String(20))  # flat, low, medium, steep
    roof_orientation = Column(String(20))  # north, south, east, west, mixed
    
    # Energy consumption
    monthly_electric_bill = Column(Float, index=True)
    annual_electric_usage = Column(Float)  # kWh
    electric_provider = Column(String(100))
    current_rate_per_kwh = Column(Float)
    
    # Solar potential assessment
    solar_potential_score = Column(Float, index=True)  # 0-100
    estimated_system_size = Column(Float)  # kW
    estimated_annual_production = Column(Float)  # kWh
    estimated_savings_annual = Column(Float)
    estimated_payback_period = Column(Float)  # years
    
    # Lead scoring and qualification
    lead_score = Column(Integer, default=0, index=True)
    lead_quality = Column(String(20), default="cold", index=True)  # hot, warm, cold
    qualification_status = Column(String(50), default="unqualified", index=True)
    qualification_reason = Column(Text)
    
    # Source and attribution
    source = Column(String(100), index=True)
    source_campaign = Column(String(100))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    referrer_url = Column(Text)
    
    # AI and conversation data
    ai_analysis_id = Column(UUIDType, ForeignKey("ai_analyses.id"), index=True)
    conversation_count = Column(Integer, default=0)
    last_conversation_at = Column(DateTime(timezone=True))
    
    # Status tracking
    status = Column(String(50), default="new", index=True)  # new, qualified, exported, sold, lost
    export_status = Column(String(50), index=True)  # pending, exported, failed, rejected
    sales_stage = Column(String(50), default="prospect", index=True)
    
    # Revenue tracking
    estimated_value = Column(Float, index=True)
    actual_value = Column(Float, index=True)
    commission_rate = Column(Float, default=0.15)
    total_revenue_earned = Column(Float, default=0.0, index=True)
    
    # B2B platform tracking
    exported_to_platforms = Column(ArrayStringType, default=[], index=True)
    export_timestamps = Column(JSON)  # Platform -> timestamp mapping
    platform_lead_ids = Column(JSON)  # Platform -> platform_lead_id mapping
    
    # Timestamps with timezone support
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), index=True)
    last_contacted = Column(DateTime(timezone=True), index=True)
    qualified_at = Column(DateTime(timezone=True), index=True)
    exported_at = Column(DateTime(timezone=True), index=True)
    sold_at = Column(DateTime(timezone=True), index=True)
    
    # Metadata and compliance
    is_active = Column(Boolean, default=True, index=True)
    is_gdpr_compliant = Column(Boolean, default=True)
    consent_given_at = Column(DateTime(timezone=True))
    data_retention_until = Column(DateTime(timezone=True), index=True)
    
    # Notes and custom fields
    notes = Column(Text)
    custom_fields = Column(JSON)
    
    # Relationships
    conversations = relationship("LeadConversation", back_populates="lead", cascade="all, delete-orphan")
    quality_history = relationship("LeadQualityHistory", back_populates="lead", cascade="all, delete-orphan")
    exports = relationship("LeadExport", back_populates="lead", cascade="all, delete-orphan")
    b2b_mappings = relationship("B2BLeadMapping", back_populates="lead", cascade="all, delete-orphan")
    revenue_transactions = relationship("B2BRevenueTransaction", back_populates="lead", cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysis", back_populates="lead")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_lead_created_status', 'created_at', 'status'),
        Index('idx_lead_quality_score', 'lead_quality', 'lead_score'),
        Index('idx_lead_zip_quality', 'zip_code', 'lead_quality'),
        Index('idx_lead_revenue', 'total_revenue_earned', 'created_at'),
        Index('idx_lead_export_status', 'export_status', 'created_at'),
        Index('idx_lead_borough_type', 'borough', 'property_type'),
        Index('idx_lead_electric_bill', 'monthly_electric_bill', 'zip_code'),
        UniqueConstraint('email', name='uq_lead_email'),
    )


class LeadConversation(Base):
    """
    Conversation history between AI agent and leads
    Supports conversation analysis and AI improvement
    """
    __tablename__ = "lead_conversations"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Conversation details
    session_id = Column(String(100), index=True)  # Groups related messages
    message_type = Column(String(20), nullable=False, index=True)  # user, ai, system
    content = Column(Text, nullable=False)
    
    # AI analysis
    sentiment_score = Column(Float)  # -1 to 1
    intent_classification = Column(String(100))
    entities_extracted = Column(JSON)
    confidence_score = Column(Float)
    
    # Response metadata
    response_time_ms = Column(Integer)
    ai_model_used = Column(String(100))
    tokens_used = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_lead_session', 'lead_id', 'session_id', 'created_at'),
        Index('idx_conversation_type_created', 'message_type', 'created_at'),
    )


class LeadQualityHistory(Base):
    """
    Historical tracking of lead quality scores and changes
    Enables quality trend analysis and scoring algorithm improvement
    """
    __tablename__ = "lead_quality_history"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Quality metrics
    previous_score = Column(Integer)
    new_score = Column(Integer, nullable=False)
    previous_quality = Column(String(20))
    new_quality = Column(String(20), nullable=False)
    
    # Change tracking
    score_change = Column(Integer)
    quality_change_reason = Column(String(200))
    factors_considered = Column(JSON)  # What factors influenced the change
    
    # AI analysis
    ai_model_version = Column(String(50))
    confidence_score = Column(Float)
    
    # Timestamps
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="quality_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_quality_lead_changed', 'lead_id', 'changed_at'),
        Index('idx_quality_score_change', 'score_change', 'changed_at'),
    )


class LeadExport(Base):
    """
    Tracks lead exports to B2B platforms with detailed status and revenue tracking
    """
    __tablename__ = "lead_exports"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    platform_id = Column(UUIDType, ForeignKey("b2b_platforms.id"), nullable=False, index=True)
    
    # Export details
    platform_lead_id = Column(String(100), index=True)  # ID from the platform
    export_status = Column(String(50), default="pending", index=True)  # pending, success, failed, rejected
    export_priority = Column(Integer, default=1)  # 1=high, 2=medium, 3=low
    
    # Data sent to platform
    export_data = Column(JSON)
    export_format = Column(String(50))  # json, xml, csv
    export_version = Column(String(20))
    
    # Platform response
    response_data = Column(JSON)
    response_status_code = Column(Integer)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # Revenue tracking
    price_per_lead = Column(Float, index=True)
    commission_rate = Column(Float, default=0.15)
    commission_earned = Column(Float, index=True)
    platform_fee = Column(Float, default=0.0)
    net_revenue = Column(Float, index=True)
    
    # Quality metrics
    platform_quality_score = Column(Float)
    acceptance_probability = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    exported_at = Column(DateTime(timezone=True), index=True)
    accepted_at = Column(DateTime(timezone=True), index=True)
    rejected_at = Column(DateTime(timezone=True), index=True)
    
    # Retry tracking
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime(timezone=True))
    max_retries = Column(Integer, default=3)
    
    # Relationships
    lead = relationship("Lead", back_populates="exports")
    platform = relationship("B2BPlatform", back_populates="exports")
    
    # Indexes
    __table_args__ = (
        Index('idx_export_lead_platform', 'lead_id', 'platform_id'),
        Index('idx_export_status_created', 'export_status', 'created_at'),
        Index('idx_export_revenue', 'commission_earned', 'created_at'),
        Index('idx_export_platform_status', 'platform_id', 'export_status'),
    )