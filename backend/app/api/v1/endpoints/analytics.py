"""
Analytics endpoints for revenue tracking and performance metrics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    RevenueMetricsResponse,
    LeadAnalyticsResponse,
    PlatformPerformanceResponse,
    NYCMarketIntelligenceResponse
)

router = APIRouter()


@router.get("/revenue", response_model=RevenueMetricsResponse)
async def get_revenue_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get revenue metrics for the specified period"""
    analytics_service = AnalyticsService(db)
    
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    metrics = analytics_service.get_revenue_metrics(start_date, end_date)
    return metrics


@router.get("/leads", response_model=LeadAnalyticsResponse)
async def get_lead_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get lead analytics and performance metrics"""
    analytics_service = AnalyticsService(db)
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    analytics = analytics_service.get_lead_analytics(start_date, end_date)
    return analytics


@router.get("/platforms", response_model=PlatformPerformanceResponse)
async def get_platform_performance(
    platform: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get B2B platform performance metrics"""
    analytics_service = AnalyticsService(db)
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    performance = analytics_service.get_platform_performance(
        platform=platform,
        start_date=start_date,
        end_date=end_date
    )
    return performance


@router.get("/nyc-market", response_model=NYCMarketIntelligenceResponse)
async def get_nyc_market_intelligence(
    zip_code: Optional[str] = Query(None),
    borough: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get NYC market intelligence data"""
    analytics_service = AnalyticsService(db)
    
    intelligence = analytics_service.get_nyc_market_intelligence(
        zip_code=zip_code,
        borough=borough
    )
    return intelligence


@router.get("/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data"""
    analytics_service = AnalyticsService(db)
    
    # Get data for last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    dashboard_data = {
        "revenue_metrics": analytics_service.get_revenue_metrics(start_date, end_date),
        "lead_analytics": analytics_service.get_lead_analytics(start_date, end_date),
        "platform_performance": analytics_service.get_platform_performance(
            start_date=start_date,
            end_date=end_date
        ),
        "top_zip_codes": analytics_service.get_top_performing_zip_codes(start_date, end_date),
        "recent_leads": analytics_service.get_recent_leads(limit=10),
        "ai_performance": analytics_service.get_ai_performance_metrics(start_date, end_date)
    }
    
    return dashboard_data
