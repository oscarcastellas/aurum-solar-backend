"""
B2B platform integration models for lead sales and revenue tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.db_types import UUIDType, ArrayStringType, get_uuid_default
import uuid


class B2BPlatform(Base):
    """
    B2B platform configuration and performance tracking
    Manages relationships with SolarReviews, Modernize, and other buyers
    """
    __tablename__ = "b2b_platforms"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    
    # Platform identification
    platform_name = Column(String(100), unique=True, nullable=False, index=True)
    platform_code = Column(String(50), unique=True, nullable=False, index=True)
    platform_type = Column(String(50), index=True)  # lead_buyer, aggregator, marketplace
    
    # API configuration
    api_base_url = Column(String(500), nullable=False)
    api_version = Column(String(20), default="v1")
    authentication_type = Column(String(50), default="api_key")  # api_key, oauth2, basic_auth
    api_credentials = Column(JSON)  # Encrypted API keys and tokens
    
    # Lead requirements and pricing
    min_lead_score = Column(Integer, default=0, index=True)
    max_lead_score = Column(Integer, default=100, index=True)
    accepted_lead_qualities = Column(ArrayStringType, default=["hot", "warm"])
    base_price_per_lead = Column(Float, nullable=False, index=True)
    price_tiers = Column(JSON)  # Score-based pricing tiers
    commission_rate = Column(Float, default=0.15, index=True)
    
    # Lead data requirements
    required_fields = Column(ArrayStringType)
    optional_fields = Column(ArrayStringType)
    data_format = Column(String(50), default="json")  # json, xml, csv
    lead_validation_rules = Column(JSON)
    
    # Platform capabilities
    supports_bulk_export = Column(Boolean, default=False)
    supports_real_time_export = Column(Boolean, default=True)
    supports_lead_updates = Column(Boolean, default=False)
    supports_revenue_tracking = Column(Boolean, default=True)
    max_export_batch_size = Column(Integer, default=100)
    
    # Performance tracking
    total_leads_exported = Column(Integer, default=0, index=True)
    successful_exports = Column(Integer, default=0, index=True)
    failed_exports = Column(Integer, default=0, index=True)
    acceptance_rate = Column(Float, default=0.0, index=True)
    average_response_time_ms = Column(Float, default=0.0)
    
    # Revenue tracking
    total_revenue_generated = Column(Float, default=0.0, index=True)
    total_commission_earned = Column(Float, default=0.0, index=True)
    average_lead_value = Column(Float, default=0.0, index=True)
    
    # Platform status
    is_active = Column(Boolean, default=True, index=True)
    is_accepting_leads = Column(Boolean, default=True, index=True)
    maintenance_mode = Column(Boolean, default=False)
    last_health_check = Column(DateTime(timezone=True), index=True)
    health_status = Column(String(20), default="unknown", index=True)  # healthy, degraded, down
    
    # Error tracking
    consecutive_failures = Column(Integer, default=0)
    last_error_message = Column(Text)
    last_error_at = Column(DateTime(timezone=True))
    
    # Rate limiting
    requests_per_minute = Column(Integer, default=60)
    requests_per_hour = Column(Integer, default=1000)
    daily_export_limit = Column(Integer)
    monthly_export_limit = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_export_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    exports = relationship("LeadExport", back_populates="platform")
    lead_mappings = relationship("B2BLeadMapping", back_populates="platform")
    revenue_transactions = relationship("B2BRevenueTransaction", back_populates="platform")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_platform_active_accepting', 'is_active', 'is_accepting_leads'),
        Index('idx_platform_performance', 'acceptance_rate', 'total_revenue_generated'),
        Index('idx_platform_health', 'health_status', 'last_health_check'),
        UniqueConstraint('platform_name', name='uq_platform_name'),
        UniqueConstraint('platform_code', name='uq_platform_code'),
    )


class B2BLeadMapping(Base):
    """
    Maps leads to B2B platforms with detailed tracking
    Supports many-to-many relationship between leads and platforms
    """
    __tablename__ = "b2b_lead_mappings"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    platform_id = Column(UUIDType, ForeignKey("b2b_platforms.id"), nullable=False, index=True)
    
    # Platform-specific lead identification
    platform_lead_id = Column(String(100), index=True)
    platform_lead_url = Column(String(500))
    platform_lead_status = Column(String(50), index=True)
    
    # Export details
    export_data = Column(JSON)
    export_format = Column(String(50))
    export_version = Column(String(20))
    
    # Platform response
    platform_response = Column(JSON)
    response_status_code = Column(Integer)
    response_time_ms = Column(Integer)
    
    # Quality and scoring
    platform_quality_score = Column(Float, index=True)
    platform_acceptance_probability = Column(Float)
    platform_lead_rating = Column(String(20))  # A, B, C, D
    
    # Revenue details
    agreed_price = Column(Float, index=True)
    commission_rate = Column(Float)
    commission_amount = Column(Float, index=True)
    platform_fee = Column(Float, default=0.0)
    net_revenue = Column(Float, index=True)
    
    # Status tracking
    mapping_status = Column(String(50), default="active", index=True)  # active, inactive, suspended
    is_primary_mapping = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="b2b_mappings")
    platform = relationship("B2BPlatform", back_populates="lead_mappings")
    
    # Indexes
    __table_args__ = (
        Index('idx_mapping_lead_platform', 'lead_id', 'platform_id'),
        Index('idx_mapping_status_created', 'mapping_status', 'created_at'),
        Index('idx_mapping_revenue', 'net_revenue', 'created_at'),
        UniqueConstraint('lead_id', 'platform_id', name='uq_lead_platform_mapping'),
    )


class B2BRevenueTransaction(Base):
    """
    Detailed revenue transactions from B2B platform sales
    Tracks payments, commissions, and financial performance
    """
    __tablename__ = "b2b_revenue_transactions"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    lead_id = Column(UUIDType, ForeignKey("leads.id"), nullable=False, index=True)
    platform_id = Column(UUIDType, ForeignKey("b2b_platforms.id"), nullable=False, index=True)
    export_id = Column(UUIDType, ForeignKey("lead_exports.id"), index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False, index=True)  # lead_sale, commission, refund, adjustment
    transaction_reference = Column(String(100), index=True)  # External transaction ID
    platform_transaction_id = Column(String(100), index=True)
    
    # Financial amounts
    gross_amount = Column(Float, nullable=False, index=True)
    platform_fee = Column(Float, default=0.0)
    processing_fee = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    net_amount = Column(Float, nullable=False, index=True)
    
    # Commission details
    commission_rate = Column(Float, index=True)
    commission_amount = Column(Float, index=True)
    commission_paid = Column(Boolean, default=False, index=True)
    commission_paid_at = Column(DateTime(timezone=True), index=True)
    
    # Payment details
    payment_method = Column(String(50))  # bank_transfer, check, wire, ach
    payment_reference = Column(String(100))
    payment_status = Column(String(50), default="pending", index=True)  # pending, completed, failed, refunded
    payment_processed_at = Column(DateTime(timezone=True), index=True)
    
    # Currency and exchange
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Float, default=1.0)
    original_amount = Column(Float)
    original_currency = Column(String(3))
    
    # Transaction metadata
    description = Column(Text)
    notes = Column(Text)
    tags = Column(ArrayStringType)
    
    # Status tracking
    status = Column(String(50), default="pending", index=True)  # pending, completed, failed, cancelled
    is_reconciled = Column(Boolean, default=False, index=True)
    reconciliation_date = Column(DateTime(timezone=True))
    
    # Timestamps
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="revenue_transactions")
    platform = relationship("B2BPlatform", back_populates="revenue_transactions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_transaction_lead_platform', 'lead_id', 'platform_id'),
        Index('idx_transaction_date_status', 'transaction_date', 'status'),
        Index('idx_transaction_revenue', 'net_amount', 'transaction_date'),
        Index('idx_transaction_commission', 'commission_amount', 'commission_paid'),
        Index('idx_transaction_payment', 'payment_status', 'payment_processed_at'),
    )
