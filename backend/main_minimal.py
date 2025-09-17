"""
Minimal FastAPI application for Aurum Solar
Core functionality with essential endpoints for revenue generation
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import time
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
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

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: float

class LeadCreate(BaseModel):
    name: str
    email: str
    phone: str
    zip_code: str
    monthly_bill: float
    roof_type: Optional[str] = None

class LeadResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    zip_code: str
    monthly_bill: float
    qualification_score: float
    estimated_value: float
    status: str
    created_at: str

class ExportRequest(BaseModel):
    lead_id: str
    platform: str

class ExportResponse(BaseModel):
    success: bool
    export_id: str
    platform: str
    message: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    # Startup
    logger.info("Starting Aurum Solar Minimal API", version="1.0.0", environment=ENVIRONMENT)
    
    try:
        logger.info("Core services initialized successfully")
        logger.info("Aurum Solar Minimal API startup completed successfully")
        
    except Exception as e:
        logger.error("Error during startup", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aurum Solar Minimal API")

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

# In-memory storage for demo
leads_db = {}
conversations_db = {}
exports_db = {}

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
            "total": 15,
            "categories": [
                "conversation", "leads", "exports", "analytics"
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
            "Revenue Analytics"
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

# Chat endpoint
@app.post("/api/v1/chat/message", response_model=ChatResponse)
async def chat_message(message: ChatMessage):
    """AI chat endpoint for lead qualification"""
    try:
        # Simple AI response based on message content
        response_text = "Thank you for your interest in solar energy! "
        
        if "zip" in message.message.lower() or "10001" in message.message:
            response_text += "I see you're in NYC! Let me help you understand your solar potential. What's your average monthly electric bill?"
        elif "bill" in message.message.lower() or "$" in message.message:
            response_text += "Great! Based on your electric bill, you could save $200-400 per month with solar. Do you own your home?"
        elif "own" in message.message.lower() or "homeowner" in message.message.lower():
            response_text += "Perfect! As a homeowner, you qualify for solar incentives. What type of roof do you have?"
        elif "roof" in message.message.lower():
            response_text += "Excellent! Your roof type is suitable for solar. Would you like me to connect you with qualified installers for a free quote?"
        else:
            response_text += "I'd love to help you explore solar options for your NYC home. What's your ZIP code?"
        
        return ChatResponse(
            response=response_text,
            session_id=message.session_id,
            timestamp=time.time()
        )
        
    except Exception as e:
        logger.error("Chat error", error=str(e))
        raise HTTPException(status_code=500, detail="Chat processing failed")

# Lead management endpoints
@app.post("/api/v1/leads", response_model=LeadResponse)
async def create_lead(lead: LeadCreate):
    """Create a new lead"""
    try:
        lead_id = f"lead_{int(time.time())}"
        
        # Calculate qualification score
        score = 50  # Base score
        if lead.monthly_bill > 200:
            score += 30
        if lead.zip_code.startswith("1"):  # NYC area
            score += 20
        
        # Calculate estimated value
        estimated_value = lead.monthly_bill * 0.8 * 12 * 20  # 80% savings, 20 years
        
        lead_data = LeadResponse(
            id=lead_id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            zip_code=lead.zip_code,
            monthly_bill=lead.monthly_bill,
            qualification_score=score,
            estimated_value=estimated_value,
            status="qualified" if score > 70 else "pending",
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        leads_db[lead_id] = lead_data
        
        logger.info("Lead created", lead_id=lead_id, score=score)
        return lead_data
        
    except Exception as e:
        logger.error("Lead creation error", error=str(e))
        raise HTTPException(status_code=500, detail="Lead creation failed")

@app.get("/api/v1/leads", response_model=List[LeadResponse])
async def get_leads():
    """Get all leads"""
    return list(leads_db.values())

@app.get("/api/v1/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str):
    """Get a specific lead"""
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    return leads_db[lead_id]

# Export endpoints
@app.post("/api/v1/exports/export-lead", response_model=ExportResponse)
async def export_lead(export_request: ExportRequest):
    """Export a lead to B2B platform"""
    try:
        if export_request.lead_id not in leads_db:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        export_id = f"export_{int(time.time())}"
        
        export_data = ExportResponse(
            success=True,
            export_id=export_id,
            platform=export_request.platform,
            message=f"Lead exported successfully to {export_request.platform}"
        )
        
        exports_db[export_id] = {
            "lead_id": export_request.lead_id,
            "platform": export_request.platform,
            "exported_at": time.time()
        }
        
        logger.info("Lead exported", lead_id=export_request.lead_id, platform=export_request.platform)
        return export_data
        
    except Exception as e:
        logger.error("Export error", error=str(e))
        raise HTTPException(status_code=500, detail="Export failed")

@app.get("/api/v1/exports/history")
async def get_export_history():
    """Get export history"""
    return list(exports_db.values())

# Analytics endpoints
@app.get("/api/v1/analytics/revenue")
async def get_revenue_metrics():
    """Get revenue metrics"""
    total_leads = len(leads_db)
    qualified_leads = len([l for l in leads_db.values() if l.qualification_score > 70])
    total_exports = len(exports_db)
    
    return {
        "total_leads": total_leads,
        "qualified_leads": qualified_leads,
        "total_exports": total_exports,
        "conversion_rate": (qualified_leads / total_leads * 100) if total_leads > 0 else 0,
        "export_rate": (total_exports / qualified_leads * 100) if qualified_leads > 0 else 0,
        "estimated_revenue": sum(l.estimated_value for l in leads_db.values() if l.qualification_score > 70)
    }

@app.get("/api/v1/analytics/leads")
async def get_lead_analytics():
    """Get lead analytics"""
    leads = list(leads_db.values())
    
    if not leads:
        return {
            "total_leads": 0,
            "average_score": 0,
            "score_distribution": {},
            "top_zip_codes": []
        }
    
    scores = [l.qualification_score for l in leads]
    zip_codes = [l.zip_code for l in leads]
    
    return {
        "total_leads": len(leads),
        "average_score": sum(scores) / len(scores),
        "score_distribution": {
            "high": len([s for s in scores if s > 80]),
            "medium": len([s for s in scores if 60 <= s <= 80]),
            "low": len([s for s in scores if s < 60])
        },
        "top_zip_codes": list(set(zip_codes))[:5]
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
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
    """Handle general exceptions"""
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
        "main_minimal:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        workers=1
    )
