"""
Aurum Solar - AI-Powered Solar Lead Generation Platform
FastAPI Backend Application with High Performance Architecture
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager
import asyncio
import time
from typing import Dict, Any

from app.core.config import settings
from app.core.database import init_db, get_db
from app.core.redis import init_redis, get_redis
from app.core.rate_limiter import RateLimiter
from app.core.monitoring import setup_monitoring
from app.api.v1.api import api_router
from app.websocket.manager import WebSocketManager
from app.services.background_tasks import BackgroundTaskManager
from app.core.exceptions import setup_exception_handlers
from app.middleware.performance import PerformanceMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.input_validation import InputValidationMiddleware
from app.middleware.csrf_protection import CSRFProtectionMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global instances
websocket_manager = WebSocketManager()
background_task_manager = BackgroundTaskManager()
rate_limiter = RateLimiter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with startup and shutdown tasks"""
    
    # Startup
    logger.info("Starting Aurum Solar API", version="1.0.0")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize Redis
        await init_redis()
        logger.info("Redis initialized successfully")
        
        # Setup monitoring
        setup_monitoring()
        logger.info("Monitoring setup completed")
        
        # Start background tasks
        await background_task_manager.start()
        logger.info("Background task manager started")
        
        # Initialize rate limiter
        await rate_limiter.initialize()
        logger.info("Rate limiter initialized")
        
        logger.info("Aurum Solar API startup completed successfully")
        
    except Exception as e:
        logger.error("Failed to start Aurum Solar API", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aurum Solar API")
    
    try:
        # Stop background tasks
        await background_task_manager.stop()
        logger.info("Background task manager stopped")
        
        # Close WebSocket connections
        await websocket_manager.disconnect_all()
        logger.info("WebSocket connections closed")
        
        # Close Redis connection
        try:
            redis_client = await get_redis()
            if redis_client:
                await redis_client.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.warning("Error closing Redis connection", error=str(e))
        
        logger.info("Aurum Solar API shutdown completed successfully")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# Create FastAPI application
app = FastAPI(
    title="Aurum Solar API",
    description="AI-powered solar lead generation platform for NYC market",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Security
security = HTTPBearer()

# Middleware stack (order matters - security first)
app.add_middleware(
    InputValidationMiddleware,
    max_request_size=10 * 1024 * 1024  # 10MB
)

app.add_middleware(
    CSRFProtectionMiddleware,
    exclude_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/api/v1/auth/login", "/api/v1/auth/register"]
)

app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=rate_limiter
)

app.add_middleware(
    AuthMiddleware,
    exclude_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/api/v1/conversation/send-message", "/api/v1/nyc-market/insights"]
)

app.add_middleware(
    PerformanceMiddleware,
    enable_metrics=True,
    enable_profiling=settings.ENVIRONMENT == "development"
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

# Configure CORS for production
cors_origins = [
    "https://aurum-solar.vercel.app",
    "https://aurum-solar-frontend.vercel.app", 
    "https://*.vercel.app",  # Allow preview deployments
    "http://localhost:3001",  # Local development
    "http://localhost:5173",  # Vite dev server
]

# Add frontend URL from environment if provided
if hasattr(settings, 'FRONTEND_URL') and settings.FRONTEND_URL:
    cors_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Only add TrustedHostMiddleware in production with proper hosts
if settings.ENVIRONMENT == "production" and settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    start_time = time.time()
    
    # Check database connection
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "healthy"
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis connection
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # Check WebSocket manager
    try:
        ws_status = "healthy" if websocket_manager.is_healthy() else "unhealthy"
    except Exception as e:
        ws_status = f"unhealthy: {str(e)}"
    
    # Check background tasks
    try:
        bg_status = "healthy" if background_task_manager.is_healthy() else "unhealthy"
    except Exception as e:
        bg_status = f"unhealthy: {str(e)}"
    
    response_time = (time.time() - start_time) * 1000
    
    # Consider app healthy if core services (database, redis) are working
    core_services_healthy = all(
        status == "healthy" 
        for status in [db_status, redis_status]
    )
    
    health_status = "healthy" if core_services_healthy else "unhealthy"
    
    return {
        "status": health_status,
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "response_time_ms": round(response_time, 2),
        "services": {
            "database": db_status,
            "redis": redis_status,
            "websocket": ws_status,
            "background_tasks": bg_status
        },
        "metrics": {
            "active_connections": websocket_manager.get_connection_count() if ws_status == "healthy" else 0,
            "background_tasks_running": background_task_manager.get_task_count() if bg_status == "healthy" else 0,
            "memory_usage": get_memory_usage(),
            "cpu_usage": get_cpu_usage()
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    from app.core.monitoring import get_metrics
    
    return get_metrics()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Aurum Solar API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs" if settings.ENVIRONMENT == "development" else "Contact support",
        "health": "/health",
        "metrics": "/metrics"
    }

# WebSocket endpoints
@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket_manager.connect(websocket, session_id)

@app.websocket("/ws/nyc-insights/{zip_code}")
async def websocket_nyc_insights(websocket, zip_code: str):
    """WebSocket endpoint for NYC market insights"""
    await websocket_manager.connect_nyc_insights(websocket, zip_code)

@app.websocket("/ws/analytics")
async def websocket_analytics(websocket):
    """WebSocket endpoint for real-time analytics"""
    await websocket_manager.connect_analytics(websocket)

# Background task endpoints
@app.post("/admin/background-tasks/start")
async def start_background_tasks():
    """Start background task processing"""
    await background_task_manager.start()
    return {"message": "Background tasks started"}

@app.post("/admin/background-tasks/stop")
async def stop_background_tasks():
    """Stop background task processing"""
    await background_task_manager.stop()
    return {"message": "Background tasks stopped"}

@app.get("/admin/background-tasks/status")
async def background_tasks_status():
    """Get background task status"""
    return {
        "running": background_task_manager.is_running(),
        "task_count": background_task_manager.get_task_count(),
        "tasks": background_task_manager.get_task_status()
    }

# Rate limiting endpoints
@app.get("/admin/rate-limits/status")
async def rate_limits_status():
    """Get rate limiting status"""
    return await rate_limiter.get_status()

@app.post("/admin/rate-limits/reset")
async def reset_rate_limits():
    """Reset rate limiting counters"""
    await rate_limiter.reset_all()
    return {"message": "Rate limits reset"}

# Utility functions
def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2)
        }
    except ImportError:
        return {"error": "psutil not available"}

def get_cpu_usage() -> Dict[str, Any]:
    """Get current CPU usage"""
    try:
        import psutil
        return {
            "percent": round(psutil.cpu_percent(), 2),
            "count": psutil.cpu_count()
        }
    except ImportError:
        return {"error": "psutil not available"}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error("Internal server error", error=str(exc), path=str(request.url.path))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
        access_log=True,
        workers=1 if settings.ENVIRONMENT == "development" else 4
    )