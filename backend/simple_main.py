"""
Simple FastAPI application for deployment testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import json

app = FastAPI(
    title="Aurum Solar API",
    description="AI-Powered Solar Lead Generation Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:5173",
        "https://aurum-solar.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Aurum Solar API is running!", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": "development"
    }

@app.get("/api/v1/health")
async def api_health():
    return {
        "status": "healthy",
        "service": "aurum-solar-api",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/chat/message")
async def chat_message(data: dict):
    """Simple chat endpoint for testing"""
    message = data.get("message", "")
    session_id = data.get("session_id", "test-session")
    
    # Simple response
    response = {
        "response": f"I received your message: '{message}'. This is a test response from the Aurum Solar API.",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }
    
    return response

@app.get("/api/v1/leads/exportable")
async def exportable_leads():
    """Simple leads endpoint for testing"""
    return {
        "leads": [
            {
                "id": "test-lead-1",
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1-555-0123",
                "zip_code": "10001",
                "monthly_bill": 300,
                "quality_tier": "premium",
                "estimated_value": 250
            }
        ],
        "total": 1,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/revenue-dashboard/executive-summary")
async def revenue_summary():
    """Simple revenue analytics endpoint for testing"""
    return {
        "total_revenue": 15000,
        "monthly_target": 15000,
        "leads_generated": 100,
        "conversion_rate": 0.75,
        "average_lead_value": 150,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/b2b/platforms")
async def b2b_platforms():
    """Simple B2B platforms endpoint for testing"""
    return {
        "platforms": [
            {
                "name": "SolarReviews",
                "status": "active",
                "price_per_lead": 200,
                "leads_exported": 25
            },
            {
                "name": "Modernize",
                "status": "active", 
                "price_per_lead": 175,
                "leads_exported": 15
            }
        ],
        "total_platforms": 2,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
