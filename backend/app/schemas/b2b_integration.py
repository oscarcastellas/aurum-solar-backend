"""
Pydantic schemas for B2B Integration API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DeliveryMethod(str, Enum):
    JSON_API = "json_api"
    CSV_EMAIL = "csv_email"
    WEBHOOK = "webhook"
    SFTP = "sftp"

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    REJECTED = "rejected"
    EXPIRED = "expired"

class RoutingStrategy(str, Enum):
    REVENUE_MAXIMIZATION = "revenue_maximization"
    CAPACITY_OPTIMIZATION = "capacity_optimization"
    QUALITY_MATCHING = "quality_matching"
    LOAD_BALANCING = "load_balancing"
    EXCLUSIVE_ROUTING = "exclusive_routing"

class LeadPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class PlatformStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    TESTING = "testing"

class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

# Lead Delivery Schemas
class LeadDeliveryRequest(BaseModel):
    lead_id: str = Field(..., description="ID of the lead to deliver")
    strategy: Optional[RoutingStrategy] = Field(None, description="Routing strategy to use")
    priority: Optional[LeadPriority] = Field(None, description="Lead priority level")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Routing constraints")
    preferred_platforms: Optional[List[str]] = Field(None, description="Preferred platforms for delivery")

class RoutingDecision(BaseModel):
    platform_code: str = Field(..., description="Selected platform code")
    confidence_score: float = Field(..., description="Confidence score for the routing decision")
    reasoning: List[str] = Field(..., description="Reasoning for the routing decision")
    estimated_revenue: float = Field(..., description="Estimated revenue from this platform")
    estimated_delivery_time: int = Field(..., description="Estimated delivery time in milliseconds")
    risk_factors: List[str] = Field(..., description="Risk factors for this routing decision")
    alternative_platforms: List[str] = Field(..., description="Alternative platform options")

class LeadDeliveryResponse(BaseModel):
    request_id: str = Field(..., description="Unique request ID")
    platform_code: str = Field(..., description="Platform where lead was delivered")
    status: DeliveryStatus = Field(..., description="Delivery status")
    delivery_time_ms: int = Field(..., description="Delivery time in milliseconds")
    external_id: Optional[str] = Field(None, description="External ID from the platform")
    revenue: float = Field(..., description="Revenue generated from this delivery")
    commission: float = Field(..., description="Commission earned")
    routing_decision: RoutingDecision = Field(..., description="Routing decision details")
    delivered_at: Optional[str] = Field(None, description="Delivery timestamp")
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")

# Platform Management Schemas
class PlatformConfiguration(BaseModel):
    platform_name: str = Field(..., description="Name of the B2B platform")
    platform_code: Optional[str] = Field(None, description="Platform code (auto-generated if not provided)")
    delivery_method: DeliveryMethod = Field(..., description="Delivery method for leads")
    api_endpoint: Optional[str] = Field(None, description="API endpoint for JSON delivery")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for webhook delivery")
    email_address: Optional[str] = Field(None, description="Email address for CSV delivery")
    min_lead_score: int = Field(50, description="Minimum lead score required")
    max_daily_exports: int = Field(100, description="Maximum daily lead exports")
    revenue_share: float = Field(0.15, description="Revenue share percentage")
    sla_minutes: int = Field(30, description="SLA in minutes")
    quality_requirements: Dict[str, Any] = Field(default_factory=dict, description="Quality requirements")
    field_mapping: Dict[str, str] = Field(default_factory=dict, description="Field mapping configuration")
    rate_limit_per_minute: int = Field(60, description="Rate limit per minute")
    retry_policy: Dict[str, Any] = Field(default_factory=dict, description="Retry policy configuration")

class OnboardingRequest(BaseModel):
    platform_code: str = Field(..., description="Platform code to onboard")
    delivery_method: DeliveryMethod = Field(..., description="Delivery method for the platform")
    configuration: Dict[str, Any] = Field(..., description="Platform configuration data")

class OnboardingStep(BaseModel):
    step_id: str = Field(..., description="Step identifier")
    name: str = Field(..., description="Step name")
    description: str = Field(..., description="Step description")
    status: str = Field(..., description="Step status")
    required: bool = Field(..., description="Whether step is required")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if step failed")

class OnboardingResponse(BaseModel):
    onboarding_id: str = Field(..., description="Onboarding process ID")
    platform_code: str = Field(..., description="Platform code being onboarded")
    status: OnboardingStatus = Field(..., description="Overall onboarding status")
    steps_remaining: int = Field(..., description="Number of steps remaining")
    estimated_completion_time: datetime = Field(..., description="Estimated completion time")
    steps: Optional[List[OnboardingStep]] = Field(None, description="List of onboarding steps")

# Health Monitoring Schemas
class HealthMetric(BaseModel):
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    status: str = Field(..., description="Metric status")
    timestamp: str = Field(..., description="Metric timestamp")

class AlertResponse(BaseModel):
    alert_id: str = Field(..., description="Alert ID")
    platform_code: str = Field(..., description="Platform code")
    alert_type: str = Field(..., description="Alert type")
    level: AlertLevel = Field(..., description="Alert level")
    status: AlertStatus = Field(..., description="Alert status")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    created_at: str = Field(..., description="Alert creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Alert metadata")

class HealthStatus(BaseModel):
    platform_code: str = Field(..., description="Platform code")
    overall_status: str = Field(..., description="Overall health status")
    health_score: float = Field(..., description="Health score (0-1)")
    metrics: List[HealthMetric] = Field(..., description="Health metrics")
    alerts: List[AlertResponse] = Field(..., description="Active alerts")
    last_updated: str = Field(..., description="Last update timestamp")

# Revenue Tracking Schemas
class RevenueMetrics(BaseModel):
    total_revenue: float = Field(..., description="Total revenue")
    total_commission: float = Field(..., description="Total commission")
    net_revenue: float = Field(..., description="Net revenue")
    platform_breakdown: Dict[str, float] = Field(..., description="Revenue breakdown by platform")
    quality_tier_breakdown: Dict[str, float] = Field(..., description="Revenue breakdown by quality tier")
    time_period: str = Field(..., description="Time period for metrics")
    transaction_count: int = Field(..., description="Number of transactions")
    avg_revenue_per_lead: float = Field(..., description="Average revenue per lead")

class ReconciliationResult(BaseModel):
    platform: str = Field(..., description="Platform code")
    expected_revenue: float = Field(..., description="Expected revenue amount")
    actual_revenue: float = Field(..., description="Actual revenue amount")
    discrepancy: float = Field(..., description="Revenue discrepancy")
    status: str = Field(..., description="Reconciliation status")
    issues: List[str] = Field(..., description="Reconciliation issues")
    recommendations: List[str] = Field(..., description="Recommendations")

# Platform Performance Schemas
class PlatformPerformance(BaseModel):
    platform_code: str = Field(..., description="Platform code")
    daily_count: int = Field(..., description="Daily lead count")
    max_daily_exports: int = Field(..., description="Maximum daily exports")
    success_rate: float = Field(..., description="Success rate")
    avg_response_time: float = Field(..., description="Average response time")
    health_status: str = Field(..., description="Health status")
    is_accepting_leads: bool = Field(..., description="Whether platform is accepting leads")

class IntegrationMetrics(BaseModel):
    orchestrator: Dict[str, Any] = Field(..., description="Orchestrator metrics")
    routing: Dict[str, Any] = Field(..., description="Routing engine metrics")
    revenue: Dict[str, Any] = Field(..., description="Revenue tracker metrics")
    platforms: Dict[str, Any] = Field(..., description="Platform manager metrics")
    monitoring: Dict[str, Any] = Field(..., description="Integration monitor metrics")
    timestamp: str = Field(..., description="Metrics timestamp")

# Field Mapping Schemas
class FieldMapping(BaseModel):
    platform_field: str = Field(..., description="Platform-specific field name")
    aurum_field: str = Field(..., description="Aurum Solar field name")
    transformation: Optional[str] = Field(None, description="Data transformation rule")
    required: bool = Field(True, description="Whether field is required")

class QualityRequirement(BaseModel):
    min_lead_score: Optional[int] = Field(None, description="Minimum lead score")
    min_estimated_value: Optional[float] = Field(None, description="Minimum estimated value")
    required_quality_tiers: Optional[List[str]] = Field(None, description="Required quality tiers")
    excluded_quality_tiers: Optional[List[str]] = Field(None, description="Excluded quality tiers")

# Retry Policy Schemas
class RetryPolicy(BaseModel):
    max_retries: int = Field(3, description="Maximum number of retries")
    backoff_factor: float = Field(2.0, description="Exponential backoff factor")
    initial_delay: int = Field(1000, description="Initial delay in milliseconds")
    max_delay: int = Field(30000, description="Maximum delay in milliseconds")

# Rate Limiting Schemas
class RateLimit(BaseModel):
    requests_per_minute: int = Field(60, description="Requests per minute")
    burst_limit: int = Field(100, description="Burst limit")
    window_size: int = Field(60, description="Window size in seconds")

# SLA Monitoring Schemas
class SLAConfiguration(BaseModel):
    delivery_sla_minutes: int = Field(30, description="Delivery SLA in minutes")
    response_sla_minutes: int = Field(5, description="Response SLA in minutes")
    escalation_threshold: int = Field(15, description="Escalation threshold in minutes")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")

# Webhook Schemas
class WebhookPayload(BaseModel):
    event: str = Field(..., description="Event type")
    timestamp: str = Field(..., description="Event timestamp")
    source: str = Field(..., description="Event source")
    data: Dict[str, Any] = Field(..., description="Event data")

class WebhookResponse(BaseModel):
    success: bool = Field(..., description="Whether webhook was processed successfully")
    message: str = Field(..., description="Response message")
    processed_at: str = Field(..., description="Processing timestamp")

# Error Schemas
class IntegrationError(BaseModel):
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    platform_code: Optional[str] = Field(None, description="Platform code if applicable")
    request_id: Optional[str] = Field(None, description="Request ID if applicable")
    timestamp: str = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Configuration Schemas
class IntegrationConfig(BaseModel):
    default_routing_strategy: RoutingStrategy = Field(RoutingStrategy.REVENUE_MAXIMIZATION, description="Default routing strategy")
    default_lead_priority: LeadPriority = Field(LeadPriority.NORMAL, description="Default lead priority")
    max_concurrent_deliveries: int = Field(100, description="Maximum concurrent deliveries")
    health_check_interval: int = Field(300, description="Health check interval in seconds")
    alert_check_interval: int = Field(60, description="Alert check interval in seconds")
    metrics_retention_days: int = Field(30, description="Metrics retention in days")
    alert_retention_days: int = Field(90, description="Alert retention in days")

# Test Schemas
class TestDeliveryRequest(BaseModel):
    platform_code: str = Field(..., description="Platform code to test")
    test_lead_data: Dict[str, Any] = Field(..., description="Test lead data")
    delivery_method: DeliveryMethod = Field(..., description="Delivery method to test")

class TestDeliveryResponse(BaseModel):
    success: bool = Field(..., description="Whether test was successful")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    external_id: Optional[str] = Field(None, description="External ID if successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    platform_response: Optional[Dict[str, Any]] = Field(None, description="Platform response data")
