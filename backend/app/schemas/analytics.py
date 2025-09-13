"""
Analytics Pydantic schemas
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class RevenueMetricsResponse(BaseModel):
    """Revenue metrics response schema"""
    total_revenue: float
    monthly_revenue: float
    average_lead_value: float
    total_leads: int
    qualified_leads: int
    conversion_rate: float
    revenue_growth: float
    platform_breakdown: Dict[str, float]
    period_start: datetime
    period_end: datetime


class LeadAnalyticsResponse(BaseModel):
    """Lead analytics response schema"""
    total_leads: int
    new_leads: int
    qualified_leads: int
    exported_leads: int
    sold_leads: int
    lead_quality_distribution: Dict[str, int]
    source_breakdown: Dict[str, int]
    average_lead_score: float
    conversion_funnel: Dict[str, int]
    period_start: datetime
    period_end: datetime


class PlatformPerformanceResponse(BaseModel):
    """Platform performance response schema"""
    platform: str
    total_exports: int
    successful_exports: int
    failed_exports: int
    acceptance_rate: float
    total_revenue: float
    average_price_per_lead: float
    average_lead_score: float
    error_rate: float
    uptime_percentage: float
    period_start: datetime
    period_end: datetime


class NYCMarketIntelligenceResponse(BaseModel):
    """NYC market intelligence response schema"""
    zip_code: str
    borough: str
    average_roof_size: Optional[float]
    average_electric_bill: Optional[float]
    solar_adoption_rate: Optional[float]
    average_system_size: Optional[float]
    average_installation_cost: Optional[float]
    average_savings_per_month: Optional[float]
    payback_period_years: Optional[float]
    state_incentives: Optional[Dict[str, Any]]
    federal_incentives: Optional[Dict[str, Any]]
    local_incentives: Optional[Dict[str, Any]]
    competitor_count: int
    market_saturation: float
    high_value_zip_code: bool
    conversion_rate: float
    last_updated: datetime


class DashboardDataResponse(BaseModel):
    """Dashboard data response schema"""
    revenue_metrics: RevenueMetricsResponse
    lead_analytics: LeadAnalyticsResponse
    platform_performance: List[PlatformPerformanceResponse]
    top_zip_codes: List[Dict[str, Any]]
    recent_leads: List[Dict[str, Any]]
    ai_performance: Dict[str, Any]
