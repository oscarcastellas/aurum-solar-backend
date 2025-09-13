"""
AI model tracking and conversation management
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.db_types import UUIDType, ArrayStringType, ArrayUUIDType, get_uuid_default
from app.core.database import Base
import uuid


class AIModel(Base):
    """
    AI model configuration and performance tracking
    Manages different AI models for lead analysis and conversation
    """
    __tablename__ = "ai_models"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Model identification
    model_name = Column(String(100), unique=True, nullable=False, index=True)
    model_type = Column(String(50), nullable=False, index=True)  # lead_analysis, conversation, scoring
    model_provider = Column(String(50), nullable=False, index=True)  # openai, anthropic, custom
    model_version = Column(String(50), nullable=False, index=True)
    
    # Model configuration
    api_endpoint = Column(String(500))
    api_key_encrypted = Column(Text)
    model_parameters = Column(JSON)  # Temperature, max_tokens, etc.
    prompt_templates = Column(JSON)  # Different prompts for different use cases
    
    # Performance metrics
    total_requests = Column(Integer, default=0, index=True)
    successful_requests = Column(Integer, default=0, index=True)
    failed_requests = Column(Integer, default=0, index=True)
    average_response_time_ms = Column(Float, default=0.0, index=True)
    average_tokens_used = Column(Float, default=0.0)
    average_cost_per_request = Column(Float, default=0.0, index=True)
    
    # Quality metrics
    accuracy_score = Column(Float, index=True)
    precision_score = Column(Float)
    recall_score = Column(Float)
    f1_score = Column(Float)
    user_satisfaction_score = Column(Float, index=True)
    
    # Model status
    is_active = Column(Boolean, default=True, index=True)
    is_primary = Column(Boolean, default=False, index=True)
    maintenance_mode = Column(Boolean, default=False)
    
    # Usage limits
    daily_request_limit = Column(Integer)
    monthly_request_limit = Column(Integer)
    cost_limit_daily = Column(Float)
    cost_limit_monthly = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    analyses = relationship("AIAnalysis", back_populates="model")
    conversations = relationship("AIConversation", back_populates="model")
    
    # Indexes
    __table_args__ = (
        Index('idx_model_type_provider', 'model_type', 'model_provider'),
        Index('idx_model_active_primary', 'is_active', 'is_primary'),
        Index('idx_model_performance', 'accuracy_score', 'average_response_time_ms'),
        UniqueConstraint('model_name', name='uq_ai_model_name'),
    )


class AIAnalysis(Base):
    """
    AI analysis results for leads
    Tracks AI insights, scoring, and recommendations
    """
    __tablename__ = "ai_analyses"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    model_id = Column(UUIDType, ForeignKey("ai_models.id"), nullable=False, index=True)
    
    # Analysis type
    analysis_type = Column(String(50), nullable=False, index=True)  # lead_scoring, qualification, market_analysis
    analysis_version = Column(String(20), default="1.0")
    
    # Input data
    input_data = Column(JSON)  # Lead data used for analysis
    input_tokens = Column(Integer)
    
    # Analysis results
    lead_score = Column(Integer, index=True)  # 0-100
    lead_quality = Column(String(20), index=True)  # hot, warm, cold
    confidence_score = Column(Float, index=True)  # 0-1
    
    # Detailed insights
    insights = Column(JSON)  # Structured insights and recommendations
    key_factors = Column(ArrayStringType)  # Factors that influenced the analysis
    risk_factors = Column(ArrayStringType)  # Potential risks or concerns
    opportunities = Column(ArrayStringType)  # Identified opportunities
    
    # Market-specific analysis
    nyc_market_score = Column(Float, index=True)  # NYC-specific market potential
    solar_potential_score = Column(Float, index=True)  # Solar installation potential
    financial_viability_score = Column(Float, index=True)  # Financial feasibility
    
    # Recommendations
    recommended_actions = Column(ArrayStringType)
    follow_up_questions = Column(ArrayStringType)
    estimated_lead_value = Column(Float, index=True)
    priority_level = Column(String(20), index=True)  # high, medium, low
    
    # Model performance tracking
    processing_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    cost = Column(Float)
    
    # Quality assessment
    human_review_score = Column(Float)  # Human validation of AI analysis
    human_reviewer_id = Column(UUIDType)
    human_review_notes = Column(Text)
    
    # Timestamps
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), index=True)  # When analysis becomes stale
    
    # Relationships
    lead = relationship("Lead", back_populates="ai_analysis")
    model = relationship("AIModel", back_populates="analyses")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_lead_type', 'lead_id', 'analysis_type'),
        Index('idx_analysis_score_quality', 'lead_score', 'lead_quality'),
        Index('idx_analysis_confidence', 'confidence_score', 'analyzed_at'),
        Index('idx_analysis_nyc_market', 'nyc_market_score', 'solar_potential_score'),
    )


class AIConversation(Base):
    """
    AI conversation tracking and analysis
    Manages chat interactions and conversation quality
    """
    __tablename__ = "ai_conversations"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    model_id = Column(UUIDType, ForeignKey("ai_models.id"), nullable=False, index=True)
    
    # Conversation identification
    session_id = Column(String(100), nullable=False, index=True)
    conversation_id = Column(String(100), index=True)
    
    # Message details
    message_type = Column(String(20), nullable=False, index=True)  # user, ai, system
    message_content = Column(Text, nullable=False)
    message_order = Column(Integer, nullable=False, index=True)
    
    # AI processing details
    prompt_used = Column(Text)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    processing_time_ms = Column(Integer)
    cost = Column(Float)
    
    # AI analysis of the message
    sentiment_score = Column(Float)  # -1 to 1
    intent_classification = Column(String(100))
    entities_extracted = Column(JSON)
    confidence_score = Column(Float)
    
    # Conversation context
    conversation_context = Column(JSON)  # Previous messages and context
    user_intent = Column(String(100))  # What the user is trying to achieve
    ai_response_strategy = Column(String(100))  # How AI responded
    
    # Quality metrics
    response_quality_score = Column(Float)  # 0-1
    user_satisfaction_score = Column(Float)  # 0-1
    conversation_flow_score = Column(Float)  # 0-1
    
    # Follow-up tracking
    requires_follow_up = Column(Boolean, default=False, index=True)
    follow_up_priority = Column(String(20))  # high, medium, low
    suggested_follow_up_actions = Column(ArrayStringType)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    lead = relationship("Lead")
    model = relationship("AIModel", back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_lead_session', 'lead_id', 'session_id', 'message_order'),
        Index('idx_conversation_type_created', 'message_type', 'created_at'),
        Index('idx_conversation_quality', 'response_quality_score', 'user_satisfaction_score'),
        Index('idx_conversation_follow_up', 'requires_follow_up', 'follow_up_priority'),
    )


class AIInsight(Base):
    """
    AI-generated insights and recommendations
    Stores valuable patterns and learnings from AI analysis
    """
    __tablename__ = "ai_insights"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Insight identification
    insight_type = Column(String(50), nullable=False, index=True)  # pattern, trend, recommendation, anomaly
    insight_category = Column(String(50), index=True)  # lead_quality, market_trend, conversion, revenue
    insight_title = Column(String(200), nullable=False)
    insight_description = Column(Text, nullable=False)
    
    # Insight data
    insight_data = Column(JSON)  # Structured data supporting the insight
    confidence_score = Column(Float, index=True)  # 0-1
    impact_score = Column(Float, index=True)  # 0-1, potential business impact
    
    # Source information
    source_analysis_ids = Column(ArrayUUIDType)  # AI analyses that contributed to this insight
    source_conversation_ids = Column(ArrayUUIDType)  # Conversations that contributed
    data_period_start = Column(DateTime(timezone=True), index=True)
    data_period_end = Column(DateTime(timezone=True), index=True)
    
    # Recommendations
    recommended_actions = Column(ArrayStringType)
    expected_impact = Column(Text)
    implementation_effort = Column(String(20))  # low, medium, high
    priority_level = Column(String(20), index=True)  # high, medium, low
    
    # Validation and feedback
    is_validated = Column(Boolean, default=False, index=True)
    validation_score = Column(Float)  # 0-1
    validation_notes = Column(Text)
    validated_by = Column(UUIDType)
    validated_at = Column(DateTime(timezone=True))
    
    # Usage tracking
    times_referenced = Column(Integer, default=0)
    last_referenced_at = Column(DateTime(timezone=True))
    implementation_status = Column(String(50), default="pending", index=True)  # pending, in_progress, implemented, rejected
    
    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), index=True)  # When insight becomes stale
    
    # Indexes
    __table_args__ = (
        Index('idx_insight_type_category', 'insight_type', 'insight_category'),
        Index('idx_insight_confidence_impact', 'confidence_score', 'impact_score'),
        Index('idx_insight_priority_status', 'priority_level', 'implementation_status'),
        Index('idx_insight_discovered', 'discovered_at', 'expires_at'),
    )


class AICalculation(Base):
    """Store AI calculation results for solar systems"""
    __tablename__ = "ai_calculations"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Calculation parameters
    zip_code = Column(String(10), nullable=False)
    monthly_bill = Column(Float, nullable=False)
    borough = Column(String(50), nullable=True)
    roof_type = Column(String(50), nullable=True)
    roof_size = Column(Float, nullable=True)
    shading_factor = Column(Float, nullable=True)
    
    # Calculation results
    system_size_kw = Column(Float, nullable=False)
    annual_production_kwh = Column(Integer, nullable=False)
    monthly_savings = Column(Float, nullable=False)
    annual_savings = Column(Float, nullable=False)
    gross_cost = Column(Float, nullable=False)
    net_cost = Column(Float, nullable=False)
    payback_years = Column(Float, nullable=False)
    roi_percentage = Column(Float, nullable=False)
    
    # Metadata
    calculation_version = Column(String(50), default="v1.0")
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AICalculationResult(Base):
    """Store detailed calculation results for AI responses"""
    __tablename__ = "ai_calculation_results"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    calculation_id = Column(UUIDType, ForeignKey("ai_calculations.id"), nullable=False)
    
    # Detailed results
    panel_count = Column(Integer, nullable=False)
    panel_type = Column(String(50), nullable=False)
    inverter_type = Column(String(50), nullable=True)
    roof_area_required = Column(Float, nullable=False)
    
    # Financial breakdown
    federal_credit = Column(Float, nullable=False)
    nyserda_rebate = Column(Float, nullable=False)
    property_tax_abatement = Column(Float, nullable=False)
    financing_options = Column(JSON, nullable=True)
    
    # Additional data
    roof_assessment = Column(JSON, nullable=True)
    permit_estimate = Column(JSON, nullable=True)
    installation_timeline = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    calculation = relationship("AICalculation")
