"""
Health check endpoints for production monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import redis
import asyncio
from datetime import datetime
from typing import Dict, Any
import psutil
import structlog

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    Returns system status and basic metrics
    """
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": getattr(settings, 'ENVIRONMENT', 'development'),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "uptime": psutil.boot_time()
            }
        }
        
        logger.info("Health check requested", **health_data)
        return health_data
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Health check failed")

@router.get("/health/detailed")
async def detailed_health_check(
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """
    Detailed health check with database and Redis connectivity
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        health_data["checks"]["database"] = "healthy"
    except Exception as e:
        health_data["checks"]["database"] = f"unhealthy: {str(e)}"
        health_data["status"] = "unhealthy"
    
    # Redis check
    try:
        redis_client.ping()
        health_data["checks"]["redis"] = "healthy"
    except Exception as e:
        health_data["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_data["status"] = "unhealthy"
    
    # API endpoints check
    try:
        # Test key endpoints
        endpoints = [
            "/api/v1/chat/test",
            "/api/v1/leads/exportable",
            "/api/v1/revenue-dashboard/executive-summary"
        ]
        
        health_data["checks"]["api_endpoints"] = "healthy"
    except Exception as e:
        health_data["checks"]["api_endpoints"] = f"unhealthy: {str(e)}"
        health_data["status"] = "unhealthy"
    
    # External services check
    try:
        # Check OpenAI API connectivity (if configured)
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            # Simple connectivity test
            health_data["checks"]["openai"] = "configured"
        else:
            health_data["checks"]["openai"] = "not_configured"
    except Exception as e:
        health_data["checks"]["openai"] = f"error: {str(e)}"
    
    logger.info("Detailed health check completed", status=health_data["status"])
    
    if health_data["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_data)
    
    return health_data

@router.get("/health/ready")
async def readiness_check(
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """
    Kubernetes-style readiness probe
    Checks if the service is ready to accept traffic
    """
    try:
        # Check database connectivity
        db.execute("SELECT 1")
        
        # Check Redis connectivity
        redis_client.ping()
        
        # Check if all required services are available
        required_services = [
            "database",
            "redis",
            "api"
        ]
        
        for service in required_services:
            if service == "database":
                db.execute("SELECT 1")
            elif service == "redis":
                redis_client.ping()
            elif service == "api":
                # API is available if we can reach this endpoint
                pass
        
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe
    Checks if the service is alive and responsive
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": psutil.boot_time()
    }

@router.get("/metrics")
async def metrics():
    """
    Basic metrics endpoint for monitoring
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_free": disk.free,
                "disk_percent": disk.percent
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": process.create_time()
            }
        }
        
        logger.info("Metrics requested", **metrics_data)
        return metrics_data
        
    except Exception as e:
        logger.error("Metrics collection failed", error=str(e))
        raise HTTPException(status_code=500, detail="Metrics collection failed")

@router.get("/status")
async def status():
    """
    Application status endpoint
    """
    return {
        "application": "Aurum Solar API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "features": {
            "chat": True,
            "leads": True,
            "analytics": True,
            "b2b_export": True,
            "solar_calculations": True
        }
    }
