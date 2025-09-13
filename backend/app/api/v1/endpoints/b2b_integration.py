"""
B2B Integration API Endpoints
Comprehensive API for B2B lead delivery and management
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.services.b2b_orchestrator import B2BOrchestrator, DeliveryStatus
from app.services.lead_routing_engine import LeadRoutingEngine, RoutingStrategy, LeadPriority
from app.services.revenue_tracker import RevenueTracker
from app.services.b2b_platform_manager import B2BPlatformManager
from app.services.integration_monitor import IntegrationMonitor
from app.schemas.b2b_integration import (
    LeadDeliveryRequest,
    LeadDeliveryResponse,
    PlatformConfiguration,
    OnboardingRequest,
    OnboardingResponse,
    HealthStatus,
    AlertResponse,
    RevenueMetrics,
    RoutingDecision
)

logger = structlog.get_logger()

router = APIRouter()

# Initialize services
orchestrator = B2BOrchestrator()
routing_engine = LeadRoutingEngine()
revenue_tracker = RevenueTracker()
platform_manager = B2BPlatformManager()
integration_monitor = IntegrationMonitor()

@router.on_event("startup")
async def startup_event():
    """Initialize B2B integration services"""
    try:
        await orchestrator.initialize()
        await routing_engine.initialize()
        await revenue_tracker.initialize()
        await platform_manager.initialize()
        await integration_monitor.initialize()
        logger.info("B2B integration services initialized successfully")
    except Exception as e:
        logger.error("Error initializing B2B integration services", error=str(e))
        raise

@router.post("/deliver-lead", response_model=LeadDeliveryResponse)
async def deliver_lead(
    request: LeadDeliveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Deliver a lead to the optimal B2B platform"""
    try:
        # Route lead to optimal platform
        routing_decision = await routing_engine.route_lead(
            lead_id=request.lead_id,
            strategy=RoutingStrategy(request.strategy) if request.strategy else RoutingStrategy.REVENUE_MAXIMIZATION,
            priority=LeadPriority(request.priority) if request.priority else LeadPriority.NORMAL,
            constraints=request.constraints or {}
        )
        
        # Deliver lead
        delivery_result = await orchestrator.deliver_lead(
            lead_id=request.lead_id,
            preferred_platforms=[routing_decision.platform_code],
            priority=request.priority or "normal"
        )
        
        # Track revenue in background
        if delivery_result.status == DeliveryStatus.DELIVERED:
            background_tasks.add_task(
                revenue_tracker.track_revenue,
                lead_id=request.lead_id,
                platform_code=routing_decision.platform_code,
                revenue_amount=delivery_result.revenue,
                commission_rate=0.15,  # This would come from platform config
                external_transaction_id=delivery_result.external_id
            )
        
        return LeadDeliveryResponse(
            request_id=str(delivery_result.request_id),
            platform_code=routing_decision.platform_code,
            status=delivery_result.status.value,
            delivery_time_ms=delivery_result.delivery_time_ms,
            external_id=delivery_result.external_id,
            revenue=delivery_result.revenue,
            commission=delivery_result.commission,
            routing_decision=routing_decision,
            delivered_at=delivery_result.delivered_at.isoformat() if delivery_result.delivered_at else None,
            error_message=delivery_result.error_message
        )
        
    except Exception as e:
        logger.error("Error delivering lead", lead_id=request.lead_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/delivery-status/{request_id}")
async def get_delivery_status(request_id: str):
    """Get status of a lead delivery"""
    try:
        delivery_result = await orchestrator.get_delivery_status(request_id)
        
        if not delivery_result:
            raise HTTPException(status_code=404, detail="Delivery request not found")
        
        return {
            "request_id": request_id,
            "platform": delivery_result.platform,
            "status": delivery_result.status.value,
            "delivery_time_ms": delivery_result.delivery_time_ms,
            "external_id": delivery_result.external_id,
            "revenue": delivery_result.revenue,
            "commission": delivery_result.commission,
            "delivered_at": delivery_result.delivered_at.isoformat() if delivery_result.delivered_at else None,
            "error_message": delivery_result.error_message,
            "retry_count": delivery_result.retry_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting delivery status", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/platforms", response_model=Dict[str, str])
async def create_platform(
    request: PlatformConfiguration,
    background_tasks: BackgroundTasks
):
    """Create a new B2B platform"""
    try:
        platform_code = await platform_manager.create_platform(
            platform_data=request.dict(),
            delivery_method=request.delivery_method
        )
        
        return {
            "platform_code": platform_code,
            "message": "Platform created successfully",
            "onboarding_required": True
        }
        
    except Exception as e:
        logger.error("Error creating platform", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/platforms/{platform_code}/onboard", response_model=OnboardingResponse)
async def start_platform_onboarding(
    platform_code: str,
    request: OnboardingRequest
):
    """Start onboarding process for a platform"""
    try:
        # This would start the onboarding process
        # For now, return a mock response
        return OnboardingResponse(
            onboarding_id=f"onboard_{platform_code}_{int(datetime.utcnow().timestamp())}",
            platform_code=platform_code,
            status="in_progress",
            steps_remaining=5,
            estimated_completion_time=datetime.utcnow() + timedelta(hours=2)
        )
        
    except Exception as e:
        logger.error("Error starting platform onboarding", platform_code=platform_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms/{platform_code}/onboarding/{onboarding_id}")
async def get_onboarding_status(
    platform_code: str,
    onboarding_id: str
):
    """Get onboarding status for a platform"""
    try:
        status = await platform_manager.get_onboarding_status(onboarding_id)
        return status
        
    except Exception as e:
        logger.error("Error getting onboarding status", platform_code=platform_code, onboarding_id=onboarding_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/platforms/{platform_code}/onboarding/{onboarding_id}/complete-step")
async def complete_onboarding_step(
    platform_code: str,
    onboarding_id: str,
    step_id: str,
    step_data: Dict[str, Any]
):
    """Complete an onboarding step"""
    try:
        success = await platform_manager.complete_onboarding_step(
            onboarding_id=onboarding_id,
            step_id=step_id,
            step_data=step_data
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to complete onboarding step")
        
        return {"message": "Onboarding step completed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error completing onboarding step", platform_code=platform_code, step_id=step_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms", response_model=List[Dict[str, Any]])
async def list_platforms(
    status: Optional[str] = Query(None, description="Filter by platform status"),
    delivery_method: Optional[str] = Query(None, description="Filter by delivery method")
):
    """List all B2B platforms"""
    try:
        platforms = []
        
        for platform_code, config in platform_manager.platform_configs.items():
            platform_data = {
                "platform_code": platform_code,
                "platform_name": config.platform_name,
                "delivery_method": config.delivery_method,
                "is_active": getattr(config, 'is_active', False),
                "health_status": "unknown",  # This would come from health monitoring
                "daily_count": 0,  # This would come from Redis
                "max_daily_exports": config.max_daily_exports,
                "revenue_share": config.revenue_share,
                "sla_minutes": config.sla_minutes
            }
            
            # Apply filters
            if status and platform_data.get("is_active") != (status == "active"):
                continue
            if delivery_method and platform_data["delivery_method"] != delivery_method:
                continue
            
            platforms.append(platform_data)
        
        return platforms
        
    except Exception as e:
        logger.error("Error listing platforms", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms/{platform_code}/health", response_model=HealthStatus)
async def get_platform_health(platform_code: str):
    """Get health status of a specific platform"""
    try:
        health = await integration_monitor.get_integration_health(platform_code)
        
        if "error" in health:
            raise HTTPException(status_code=404, detail=health["error"])
        
        return HealthStatus(
            platform_code=platform_code,
            overall_status=health["overall_status"],
            health_score=health["health_score"],
            metrics=health["metrics"],
            alerts=health["alerts"],
            last_updated=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting platform health", platform_code=platform_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def get_integration_health():
    """Get overall integration health status"""
    try:
        health = await integration_monitor.get_integration_health()
        return health
        
    except Exception as e:
        logger.error("Error getting integration health", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(
    platform_code: Optional[str] = Query(None, description="Filter by platform"),
    level: Optional[str] = Query(None, description="Filter by alert level")
):
    """Get active alerts"""
    try:
        alerts = []
        
        for platform, platform_alerts in integration_monitor.active_alerts.items():
            if platform_code and platform != platform_code:
                continue
            
            for alert in platform_alerts:
                if alert.status.value == "active":
                    if level and alert.level.value != level:
                        continue
                    
                    alerts.append(AlertResponse(
                        alert_id=alert.alert_id,
                        platform_code=alert.platform_code,
                        alert_type=alert.alert_type,
                        level=alert.level.value,
                        status=alert.status.value,
                        title=alert.title,
                        description=alert.description,
                        created_at=alert.created_at.isoformat(),
                        metadata=alert.metadata
                    ))
        
        return alerts
        
    except Exception as e:
        logger.error("Error getting active alerts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str = "system"
):
    """Acknowledge an alert"""
    try:
        success = await integration_monitor.acknowledge_alert(alert_id, acknowledged_by)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error acknowledging alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolved_by: str = "system"
):
    """Resolve an alert"""
    try:
        success = await integration_monitor.resolve_alert(alert_id, resolved_by)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert resolved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resolving alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/revenue/metrics", response_model=RevenueMetrics)
async def get_revenue_metrics(
    time_period: str = Query("7d", description="Time period for metrics"),
    platform_code: Optional[str] = Query(None, description="Filter by platform")
):
    """Get revenue metrics"""
    try:
        metrics = await revenue_tracker.get_revenue_metrics(time_period, platform_code)
        return metrics
        
    except Exception as e:
        logger.error("Error getting revenue metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/revenue/reconcile/{platform_code}")
async def reconcile_platform_revenue(
    platform_code: str,
    background_tasks: BackgroundTasks
):
    """Reconcile revenue with a specific platform"""
    try:
        # Run reconciliation in background
        background_tasks.add_task(
            revenue_tracker.reconcile_platform_revenue,
            platform_code
        )
        
        return {"message": f"Revenue reconciliation started for {platform_code}"}
        
    except Exception as e:
        logger.error("Error starting revenue reconciliation", platform_code=platform_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/routing/optimize")
async def optimize_routing_strategy(
    time_period: str = Query("7d", description="Time period for optimization")
):
    """Optimize routing strategy based on historical data"""
    try:
        optimization = await routing_engine.optimize_routing_strategy(time_period)
        return optimization
        
    except Exception as e:
        logger.error("Error optimizing routing strategy", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/routing/decision")
async def get_routing_decision(
    lead_id: str,
    strategy: str = Query("revenue_maximization", description="Routing strategy"),
    priority: str = Query("normal", description="Lead priority")
):
    """Get routing decision for a lead without delivering"""
    try:
        # This would get the lead from database
        # For now, return a mock routing decision
        return {
            "lead_id": lead_id,
            "platform_code": "solarreviews",
            "confidence_score": 0.85,
            "reasoning": ["High revenue potential", "Good platform performance"],
            "estimated_revenue": 250.0,
            "estimated_delivery_time": 1500,
            "risk_factors": [],
            "alternative_platforms": ["modernize", "homeadvisor"]
        }
        
    except Exception as e:
        logger.error("Error getting routing decision", lead_id=lead_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_integration_metrics():
    """Get comprehensive integration metrics"""
    try:
        orchestrator_metrics = await orchestrator.get_platform_metrics()
        routing_metrics = await routing_engine.get_routing_metrics()
        revenue_metrics = await revenue_tracker.get_revenue_tracker_metrics()
        platform_metrics = await platform_manager.get_platform_manager_metrics()
        monitoring_metrics = await integration_monitor.get_monitoring_metrics()
        
        return {
            "orchestrator": orchestrator_metrics,
            "routing": routing_metrics,
            "revenue": revenue_metrics,
            "platforms": platform_metrics,
            "monitoring": monitoring_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting integration metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms/{platform_code}/config")
async def get_platform_config(platform_code: str):
    """Get platform configuration"""
    try:
        if platform_code not in platform_manager.platform_configs:
            raise HTTPException(status_code=404, detail="Platform not found")
        
        config = platform_manager.platform_configs[platform_code]
        return {
            "platform_code": config.platform_code,
            "platform_name": config.platform_name,
            "delivery_method": config.delivery_method,
            "api_endpoint": config.api_endpoint,
            "webhook_url": config.webhook_url,
            "email_address": config.email_address,
            "min_lead_score": config.min_lead_score,
            "max_daily_exports": config.max_daily_exports,
            "revenue_share": config.revenue_share,
            "sla_minutes": config.sla_minutes,
            "quality_requirements": config.quality_requirements,
            "field_mapping": config.field_mapping,
            "rate_limit_per_minute": config.rate_limit_per_minute,
            "retry_policy": config.retry_policy
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting platform config", platform_code=platform_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/platforms/{platform_code}/config")
async def update_platform_config(
    platform_code: str,
    config_updates: Dict[str, Any]
):
    """Update platform configuration"""
    try:
        success = await platform_manager.update_platform_config(platform_code, config_updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Platform not found")
        
        return {"message": "Platform configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating platform config", platform_code=platform_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/platforms/{platform_code}/deactivate")
async def deactivate_platform(platform_code: str):
    """Deactivate a platform"""
    try:
        success = await platform_manager.deactivate_platform(platform_code)
        
        if not success:
            raise HTTPException(status_code=404, detail="Platform not found")
        
        return {"message": f"Platform {platform_code} deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deactivating platform", platform_code=platform_code, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
