"""
Production FastAPI application for Aurum Solar
Complete backend with all 80+ API endpoints for revenue generation
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import os
from typing import Dict, Any

# Import all our API modules
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.core.redis import redis_client
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.performance import PerformanceMiddleware

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

# Railway environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://aurum-solar.vercel.app")
PORT = int(os.getenv("PORT", 8000))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with startup and shutdown tasks"""
    
    # Startup
    logger.info("Starting Aurum Solar Production API", version="1.0.0", environment=ENVIRONMENT)
    
    try:
        # Initialize database
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize Redis
        await redis_client.initialize()
        logger.info("Redis connection established")
        
        # Initialize services
        from app.services.conversation_agent import SolarConversationAgent
        from app.services.lead_scoring_service import LeadScoringService
        from app.services.b2b_export_service import B2BExportService
        from app.services.revenue_analytics_engine import RevenueAnalyticsEngine
        
        # Initialize core services
        conversation_agent = SolarConversationAgent()
        lead_scoring = LeadScoringService()
        b2b_export = B2BExportService()
        revenue_analytics = RevenueAnalyticsEngine()
        
        logger.info("Core services initialized successfully")
        logger.info("Aurum Solar Production API startup completed successfully")
        
    except Exception as e:
        logger.error("Error during startup", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aurum Solar Production API")
    try:
        await redis_client.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# Create FastAPI application
app = FastAPI(
    title="Aurum Solar API",
    description="AI-powered solar lead generation platform for NYC market",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
        "https://aurum-solar.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(PerformanceMiddleware)

# Include all API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway monitoring"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "response_time_ms": 0.0,
        "message": "Aurum Solar API is operational",
        "railway": True,
        "endpoints": {
            "total": 80,
            "categories": [
                "conversation", "leads", "analytics", "exports", 
                "b2b", "auth", "revenue-dashboard"
            ]
        }
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Aurum Solar API",
        "version": "1.0.0",
        "status": "operational",
        "environment": ENVIRONMENT,
        "documentation": "/docs",
        "health": "/health",
        "railway": True,
        "features": [
            "AI Conversation Agent",
            "Lead Management & Scoring",
            "B2B Export System",
            "Revenue Analytics",
            "NYC Market Intelligence",
            "Real-time WebSocket Chat"
        ]
    }

# Test endpoint
@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint for basic connectivity"""
    return {
        "message": "Aurum Solar API test endpoint",
        "status": "success",
        "timestamp": time.time(),
        "environment": ENVIRONMENT
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with structured logging"""
    logger.error(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "environment": ENVIRONMENT
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with structured logging"""
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": request.url.path,
            "environment": ENVIRONMENT
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_production:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        workers=1
    )
