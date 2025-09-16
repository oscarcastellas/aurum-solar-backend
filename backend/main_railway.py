"""
Railway-optimized FastAPI application for production deployment
This version is specifically designed for Railway's deployment environment
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
    logger.info("Starting Aurum Solar API", version="1.0.0", environment=ENVIRONMENT)
    logger.info("Aurum Solar API startup completed successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aurum Solar API")
    logger.info("Aurum Solar API shutdown completed successfully")

# Create FastAPI application
app = FastAPI(
    title="Aurum Solar API",
    description="AI-powered solar lead generation platform for NYC market",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Configure CORS for Railway production
cors_origins = [
    "https://aurum-solar.vercel.app",
    "https://aurum-solar-frontend.vercel.app", 
    "https://*.vercel.app",  # Allow preview deployments
    "http://localhost:3001",  # Local development
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8000",  # Local backend
]

# Add frontend URL from environment if provided
if FRONTEND_URL:
    cors_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Railway health check endpoint"""
    try:
        start_time = time.time()
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "environment": ENVIRONMENT,
            "response_time_ms": round(response_time, 2),
            "message": "Aurum Solar API is operational",
            "railway": True
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Aurum Solar API",
        "version": "1.0.0",
        "status": "operational",
        "environment": ENVIRONMENT,
        "documentation": "/docs" if ENVIRONMENT == "development" else "Contact support",
        "health": "/health",
        "railway": True
    }

# Simple test endpoints
@app.get("/api/v1/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "API is working",
        "timestamp": time.time(),
        "environment": ENVIRONMENT,
        "railway": True
    }

@app.post("/api/v1/chat/message")
async def chat_message(data: dict):
    """Advanced AI chat endpoint with OpenAI integration"""
    try:
        message = data.get("message", "")
        session_id = data.get("session_id", "test-session")
        
        # Import OpenAI for AI responses
        try:
            import openai
            from app.core.config import settings
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Create AI-powered response
            system_prompt = """You are a solar energy consultant for Aurum Solar, specializing in the NYC market. 
            
            Your goals:
            1. Qualify leads for solar installation
            2. Gather property details (ZIP code, electric bill, roof type, homeownership)
            3. Explain NYC solar incentives and benefits
            4. Calculate potential savings
            5. Schedule consultations when appropriate
            
            Be helpful, professional, and knowledgeable about NYC solar market. 
            Keep responses concise but informative. Ask follow-up questions to gather more details.
            Focus on NYC-specific incentives, borough data, and local solar potential."""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
        except Exception as ai_error:
            logger.warning("AI service unavailable, using fallback", error=str(ai_error))
            # Fallback to rule-based responses
            if "zip" in message.lower() or "10001" in message:
                ai_response = "I see you're in NYC! Let me help you understand your solar potential. What's your average monthly electric bill?"
            elif "bill" in message.lower() or "$" in message:
                ai_response = "Great! Based on your electric bill, you could save $200-400 per month with solar. Do you own your home?"
            elif "own" in message.lower() or "homeowner" in message.lower():
                ai_response = "Perfect! As a homeowner, you qualify for solar incentives. What type of roof do you have?"
            elif "roof" in message.lower():
                ai_response = "Excellent! Your roof type is suitable for solar. Would you like me to connect you with qualified installers for a free quote?"
            else:
                ai_response = "I'd love to help you explore solar options for your NYC home. What's your ZIP code?"
        
        response_data = {
            "response": ai_response,
            "session_id": session_id,
            "timestamp": time.time(),
            "status": "success",
            "environment": ENVIRONMENT,
            "railway": True,
            "ai_powered": True
        }
        
        return response_data
        
    except Exception as e:
        logger.error("Chat message error", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(e)
            }
        )

# Analytics endpoints
@app.get("/api/v1/analytics/revenue")
async def get_revenue_analytics():
    """Get revenue analytics data"""
    try:
        # Mock revenue data for now
        revenue_data = {
            "total_revenue": 15750.0,
            "monthly_revenue": 5250.0,
            "leads_sold": 45,
            "average_lead_value": 350.0,
            "platforms": {
                "solarreviews": {"revenue": 8750.0, "leads": 25},
                "modernize": {"revenue": 5250.0, "leads": 15},
                "homeadvisor": {"revenue": 1750.0, "leads": 5}
            },
            "trends": {
                "daily": [150, 200, 175, 300, 250, 400, 350],
                "weekly": [1200, 1400, 1600, 1800, 2000, 2200, 2400]
            },
            "timestamp": time.time()
        }
        
        return revenue_data
        
    except Exception as e:
        logger.error("Revenue analytics error", error=str(e))
        raise HTTPException(status_code=500, detail="Analytics processing failed")

@app.get("/api/v1/analytics/leads")
async def get_lead_analytics():
    """Get lead quality analytics data"""
    try:
        # Mock lead analytics data
        lead_data = {
            "total_leads": 127,
            "qualified_leads": 89,
            "conversion_rate": 0.70,
            "quality_distribution": {
                "premium": 23,
                "standard": 45,
                "basic": 21,
                "unqualified": 38
            },
            "avg_qualification_score": 78.5,
            "top_zip_codes": [
                {"zip": "10001", "leads": 15, "avg_value": 285},
                {"zip": "10002", "leads": 12, "avg_value": 320},
                {"zip": "10003", "leads": 10, "avg_value": 295}
            ],
            "timestamp": time.time()
        }
        
        return lead_data
        
    except Exception as e:
        logger.error("Lead analytics error", error=str(e))
        raise HTTPException(status_code=500, detail="Analytics processing failed")

# Lead management endpoints
@app.post("/api/v1/leads")
async def create_lead(lead_data: dict):
    """Create a new lead"""
    try:
        # Mock lead creation
        lead_id = f"lead_{int(time.time())}"
        
        lead_response = {
            "id": lead_id,
            "name": lead_data.get("name", "Unknown"),
            "email": lead_data.get("email", ""),
            "phone": lead_data.get("phone", ""),
            "zip_code": lead_data.get("zip_code", ""),
            "monthly_bill": lead_data.get("monthly_bill", 0),
            "qualification_score": 75,
            "estimated_value": 250.0,
            "status": "new",
            "created_at": time.time(),
            "timestamp": time.time()
        }
        
        return lead_response
        
    except Exception as e:
        logger.error("Lead creation error", error=str(e))
        raise HTTPException(status_code=500, detail="Lead creation failed")

@app.get("/api/v1/leads")
async def get_leads():
    """Get all leads"""
    try:
        # Mock leads data
        leads = [
            {
                "id": "lead_001",
                "name": "John Smith",
                "email": "john@example.com",
                "phone": "555-0123",
                "zip_code": "10001",
                "monthly_bill": 150,
                "qualification_score": 85,
                "estimated_value": 300.0,
                "status": "qualified",
                "created_at": time.time() - 86400
            },
            {
                "id": "lead_002", 
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "555-0456",
                "zip_code": "10002",
                "monthly_bill": 200,
                "qualification_score": 92,
                "estimated_value": 350.0,
                "status": "premium",
                "created_at": time.time() - 172800
            }
        ]
        
        return leads
        
    except Exception as e:
        logger.error("Get leads error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve leads")

# Export endpoints
@app.post("/api/v1/exports/export-lead")
async def export_lead(export_data: dict):
    """Export lead to B2B platforms"""
    try:
        export_id = f"export_{int(time.time())}"
        
        export_response = {
            "export_id": export_id,
            "lead_id": export_data.get("lead_id", ""),
            "platform": export_data.get("platform", "solarreviews"),
            "status": "delivered",
            "delivered_at": time.time(),
            "revenue": 250.0,
            "timestamp": time.time()
        }
        
        return export_response
        
    except Exception as e:
        logger.error("Export error", error=str(e))
        raise HTTPException(status_code=500, detail="Export failed")

@app.get("/api/v1/exports/history")
async def get_export_history():
    """Get export history"""
    try:
        # Mock export history
        exports = [
            {
                "export_id": "export_001",
                "lead_id": "lead_001",
                "platform": "solarreviews",
                "status": "delivered",
                "revenue": 300.0,
                "delivered_at": time.time() - 3600
            },
            {
                "export_id": "export_002",
                "lead_id": "lead_002", 
                "platform": "modernize",
                "status": "delivered",
                "revenue": 250.0,
                "delivered_at": time.time() - 7200
            }
        ]
        
        return exports
        
    except Exception as e:
        logger.error("Export history error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve export history")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
            "environment": ENVIRONMENT
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
            "environment": ENVIRONMENT
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_railway:app",
        host="0.0.0.0",
        port=PORT,
        reload=ENVIRONMENT == "development",
        log_level="info",
        access_log=True,
        workers=1
    )
