"""
Simplified FastAPI application for Railway deployment
This version removes problematic middleware and focuses on core functionality
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager
import asyncio
import time
from typing import Dict, Any
import os

from app.core.config import settings
from app.core.database import init_db, get_db
from app.core.redis import init_redis, get_redis
# from app.api.v1.api import api_router  # Commented out to avoid complex dependencies

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
        
        logger.info("Aurum Solar API startup completed successfully")
        
    except Exception as e:
        logger.error("Failed to start Aurum Solar API", error=str(e))
        # Don't raise - allow app to start even if some services fail
        logger.warning("Continuing startup despite service initialization failures")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aurum Solar API")
    
    try:
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

# Configure CORS for production
cors_origins = [
    "https://aurum-solar.vercel.app",
    "https://aurum-solar-frontend.vercel.app", 
    "https://*.vercel.app",  # Allow preview deployments
    "http://localhost:3001",  # Local development
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8000",  # Local backend
    "*"  # Allow all origins for Railway deployment
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

# Include API routes (commented out to avoid complex dependencies)
# app.include_router(api_router, prefix="/api/v1")

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
    
    response_time = (time.time() - start_time) * 1000
    
    # Consider app healthy if at least one core service is working
    core_services_healthy = db_status == "healthy" or redis_status == "healthy"
    
    health_status = "healthy" if core_services_healthy else "unhealthy"
    
    return {
        "status": health_status,
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "response_time_ms": round(response_time, 2),
        "services": {
            "database": db_status,
            "redis": redis_status
        }
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Aurum Solar API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs" if settings.ENVIRONMENT == "development" else "Contact support",
        "health": "/health"
    }

# Simple test endpoints
@app.get("/api/v1/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "API is working",
        "timestamp": time.time(),
        "environment": settings.ENVIRONMENT
    }

@app.post("/api/v1/chat/message")
async def chat_message(data: dict):
    """Simple chat endpoint for testing"""
    message = data.get("message", "")
    session_id = data.get("session_id", "test-session")
    
    response = {
        "response": f"I received your message: '{message}'. This is a test response from the Aurum Solar API.",
        "session_id": session_id,
        "timestamp": time.time(),
        "status": "success"
    }
    
    return response

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
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
        access_log=True,
        workers=1
    )
