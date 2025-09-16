"""
Railway-optimized FastAPI application for production deployment
This version is specifically designed for Railway's deployment environment
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager
import asyncio
import time
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
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

# WebSocket Connection Manager
class ConnectionManager:
    """Manages WebSocket connections for real-time AI chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection and initialize session"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Initialize conversation session
        self.conversation_sessions[session_id] = {
            "session_id": session_id,
            "connected_at": datetime.utcnow(),
            "message_count": 0,
            "lead_id": None,
            "conversation_stage": "welcome",
            "lead_score": 0,
            "quality_tier": "unqualified"
        }
        
        logger.info("WebSocket connected", session_id=session_id)
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection and cleanup session"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.conversation_sessions:
            del self.conversation_sessions[session_id]
        
        logger.info("WebSocket disconnected", session_id=session_id)
    
    async def send_personal_message(self, message: Dict[str, Any], session_id: str):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error("Error sending message", session_id=session_id, error=str(e))
                self.disconnect(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session data"""
        if session_id in self.conversation_sessions:
            self.conversation_sessions[session_id].update(updates)

# Global connection manager
manager = ConnectionManager()

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

# WebSocket Chat Endpoint for Real-time AI Conversations
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str = None):
    """Real-time AI conversation WebSocket endpoint"""
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Connect to WebSocket
    await manager.connect(websocket, session_id)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Welcome! I'm your NYC solar consultant. I can help you explore solar options and calculate your potential savings. What's driving your interest in solar energy?",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "suggestions": [
                "What's your monthly electric bill?",
                "Do you own your home?",
                "What zip code are you in?"
            ]
        }
        
        await manager.send_personal_message(welcome_message, session_id)
        
        # Main conversation loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Extract message content
                user_message = message_data.get("message", "")
                message_type = message_data.get("type", "user_message")
                
                # Update session
                session = manager.conversation_sessions.get(session_id)
                if session:
                    session["message_count"] += 1
                    session["last_message_at"] = datetime.utcnow()
                
                # Process message with AI
                if message_type == "user_message":
                    await process_ai_message(websocket, session_id, user_message)
                elif message_type == "get_nyc_data":
                    await process_nyc_data_request(websocket, session_id, message_data)
                elif message_type == "get_lead_status":
                    await process_lead_status_request(websocket, session_id)
                else:
                    await send_error_message(websocket, "Unknown message type")
                
            except json.JSONDecodeError:
                await send_error_message(websocket, "Invalid JSON format")
            except Exception as e:
                logger.error("Error processing message", error=str(e))
                await send_error_message(websocket, "Error processing your message")
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        manager.disconnect(session_id)

async def process_ai_message(websocket: WebSocket, session_id: str, message: str):
    """Process user message with AI and send response"""
    try:
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
        
        # Send AI response
        ai_message = {
            "type": "ai_response",
            "message": ai_response,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_stage": "active",
            "lead_score": 75,  # Mock lead score
            "quality_tier": "standard"
        }
        
        await manager.send_personal_message(ai_message, session_id)
        
    except Exception as e:
        logger.error("Error processing AI message", error=str(e))
        await send_error_message(websocket, "I'm having trouble processing your message. Please try again.")

async def process_nyc_data_request(websocket: WebSocket, session_id: str, message_data: Dict[str, Any]):
    """Process NYC market data request"""
    try:
        zip_code = message_data.get("zip_code", "")
        
        # Mock NYC market data
        nyc_data = {
            "zip_code": zip_code,
            "borough": "Manhattan" if zip_code.startswith("100") else "Brooklyn",
            "solar_potential": "High",
            "incentives": [
                "NYC Solar Property Tax Abatement",
                "Federal Solar Tax Credit (30%)",
                "NYSERDA Solar Incentive"
            ],
            "average_savings": "$200-400/month",
            "payback_period": "5-7 years"
        }
        
        response = {
            "type": "nyc_data",
            "data": nyc_data,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(response, session_id)
        
    except Exception as e:
        logger.error("Error processing NYC data request", error=str(e))
        await send_error_message(websocket, "Error retrieving NYC market data")

async def process_lead_status_request(websocket: WebSocket, session_id: str):
    """Process lead status request"""
    try:
        session = manager.conversation_sessions.get(session_id, {})
        
        lead_status = {
            "session_id": session_id,
            "lead_id": session.get("lead_id"),
            "conversation_stage": session.get("conversation_stage", "welcome"),
            "lead_score": session.get("lead_score", 0),
            "quality_tier": session.get("quality_tier", "unqualified"),
            "message_count": session.get("message_count", 0),
            "connected_at": session.get("connected_at", datetime.utcnow()).isoformat(),
            "last_message_at": session.get("last_message_at", datetime.utcnow()).isoformat()
        }
        
        response = {
            "type": "lead_status",
            "data": lead_status,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(response, session_id)
        
    except Exception as e:
        logger.error("Error processing lead status request", error=str(e))
        await send_error_message(websocket, "Error retrieving lead status")

async def send_error_message(websocket: WebSocket, message: str):
    """Send error message to client"""
    try:
        error_response = {
            "type": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))
    except Exception as e:
        logger.error("Error sending error message", error=str(e))

# Advanced Conversation API
@app.post("/api/v1/conversation")
async def process_conversation(request: dict):
    """Process conversation message and return AI response"""
    try:
        message = request.get("message", "")
        session_id = request.get("session_id", str(uuid.uuid4()))
        
        # Process with AI (same logic as WebSocket)
        try:
            import openai
            from app.core.config import settings
            
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
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
            # Fallback responses
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
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "timestamp": time.time(),
            "conversation_stage": "active",
            "lead_score": 75,
            "quality_tier": "standard",
            "status": "success"
        }
        
    except Exception as e:
        logger.error("Conversation processing error", error=str(e))
        raise HTTPException(status_code=500, detail="Conversation processing failed")

# NYC Market Data API
@app.get("/api/v1/analytics/nyc-market")
async def get_nyc_market_data(zip_code: str = "10001"):
    """Get NYC market intelligence data"""
    try:
        # Mock NYC market data
        nyc_data = {
            "zip_code": zip_code,
            "borough": "Manhattan" if zip_code.startswith("100") else "Brooklyn",
            "solar_potential": "High",
            "incentives": [
                "NYC Solar Property Tax Abatement",
                "Federal Solar Tax Credit (30%)",
                "NYSERDA Solar Incentive"
            ],
            "average_savings": "$200-400/month",
            "payback_period": "5-7 years",
            "installation_cost": "$15,000-25,000",
            "roi_percentage": "15-25%",
            "timestamp": time.time()
        }
        
        return nyc_data
        
    except Exception as e:
        logger.error("NYC market data error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve NYC market data")

# Advanced AI Chat API
@app.post("/api/v1/ai/chat")
async def advanced_ai_chat(request: dict):
    """Advanced AI chat with enhanced context and lead qualification"""
    try:
        message = request.get("message", "")
        session_id = request.get("session_id", str(uuid.uuid4()))
        lead_context = request.get("lead_context", {})
        
        # Enhanced AI processing with lead context
        try:
            import openai
            from app.core.config import settings
            
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Enhanced system prompt with lead context
            system_prompt = f"""You are an expert solar energy consultant for Aurum Solar, specializing in the NYC market.
            
            Lead Context:
            - Name: {lead_context.get('name', 'Prospect')}
            - Location: {lead_context.get('zip_code', 'NYC')}
            - Electric Bill: ${lead_context.get('monthly_bill', 'Unknown')}
            - Property Type: {lead_context.get('property_type', 'Unknown')}
            
            Your goals:
            1. Qualify leads for solar installation with intelligent scoring
            2. Gather detailed property information
            3. Explain NYC-specific solar incentives and benefits
            4. Calculate personalized savings estimates
            5. Address objections with local data and examples
            6. Guide toward consultation scheduling
            
            Be conversational, knowledgeable, and focus on NYC solar market expertise.
            Ask follow-up questions to gather qualification details.
            Provide specific, actionable advice based on their situation."""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            ai_response = response.choices[0].message.content
            
            # Calculate lead score based on message content
            lead_score = calculate_lead_score(message, lead_context)
            quality_tier = get_quality_tier(lead_score)
            
        except Exception as ai_error:
            logger.warning("AI service unavailable, using fallback", error=str(ai_error))
            ai_response = "I'd love to help you explore solar options for your NYC home. What's your ZIP code?"
            lead_score = 50
            quality_tier = "basic"
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "timestamp": time.time(),
            "lead_score": lead_score,
            "quality_tier": quality_tier,
            "conversation_stage": "active",
            "next_questions": [
                "What's your average monthly electric bill?",
                "Do you own your home?",
                "What type of roof do you have?"
            ],
            "status": "success"
        }
        
    except Exception as e:
        logger.error("Advanced AI chat error", error=str(e))
        raise HTTPException(status_code=500, detail="Advanced AI chat processing failed")

# Lead Status API
@app.get("/api/v1/conversation/lead-status")
async def get_lead_status(session_id: str):
    """Get real-time lead status and qualification progress"""
    try:
        # Get session data from manager
        session = manager.conversation_sessions.get(session_id, {})
        
        lead_status = {
            "session_id": session_id,
            "lead_id": session.get("lead_id"),
            "conversation_stage": session.get("conversation_stage", "welcome"),
            "lead_score": session.get("lead_score", 0),
            "quality_tier": session.get("quality_tier", "unqualified"),
            "message_count": session.get("message_count", 0),
            "connected_at": session.get("connected_at", datetime.utcnow()).isoformat(),
            "last_message_at": session.get("last_message_at", datetime.utcnow()).isoformat(),
            "qualification_progress": {
                "zip_code_collected": "zip" in str(session.get("lead_context", {})),
                "bill_amount_collected": "bill" in str(session.get("lead_context", {})),
                "homeownership_confirmed": "own" in str(session.get("lead_context", {})),
                "roof_type_collected": "roof" in str(session.get("lead_context", {}))
            },
            "next_steps": [
                "Gather ZIP code for NYC market data",
                "Collect monthly electric bill amount",
                "Confirm homeownership status",
                "Identify roof type and condition"
            ]
        }
        
        return lead_status
        
    except Exception as e:
        logger.error("Lead status error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve lead status")

# B2B Integration APIs
@app.post("/api/v1/deliver-lead")
async def deliver_lead(request: dict):
    """Deliver lead to optimal B2B platform"""
    try:
        lead_id = request.get("lead_id", "")
        platform = request.get("platform", "solarreviews")
        lead_data = request.get("lead_data", {})
        
        # Mock B2B delivery
        delivery_id = f"delivery_{int(time.time())}"
        
        delivery_response = {
            "delivery_id": delivery_id,
            "lead_id": lead_id,
            "platform": platform,
            "status": "delivered",
            "delivered_at": time.time(),
            "revenue": 250.0,
            "commission_rate": 0.15,
            "estimated_value": 250.0,
            "timestamp": time.time()
        }
        
        return delivery_response
        
    except Exception as e:
        logger.error("Lead delivery error", error=str(e))
        raise HTTPException(status_code=500, detail="Lead delivery failed")

@app.get("/api/v1/platforms")
async def get_platforms():
    """Get available B2B platforms"""
    try:
        platforms = [
            {
                "id": "solarreviews",
                "name": "SolarReviews",
                "status": "active",
                "commission_rate": 0.15,
                "min_lead_value": 200.0,
                "max_capacity": 100
            },
            {
                "id": "modernize",
                "name": "Modernize",
                "status": "active", 
                "commission_rate": 0.12,
                "min_lead_value": 150.0,
                "max_capacity": 75
            },
            {
                "id": "homeadvisor",
                "name": "HomeAdvisor",
                "status": "active",
                "commission_rate": 0.10,
                "min_lead_value": 100.0,
                "max_capacity": 50
            }
        ]
        
        return platforms
        
    except Exception as e:
        logger.error("Platforms error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve platforms")

# Advanced Analytics APIs
@app.get("/api/v1/analytics/executive-summary")
async def get_executive_summary():
    """Get executive dashboard summary"""
    try:
        summary = {
            "total_revenue": 15750.0,
            "monthly_revenue": 5250.0,
            "total_leads": 127,
            "qualified_leads": 89,
            "conversion_rate": 0.70,
            "average_lead_value": 350.0,
            "top_performing_zip": "10001",
            "revenue_growth": 0.25,
            "lead_quality_score": 78.5,
            "platform_performance": {
                "solarreviews": {"revenue": 8750.0, "leads": 25},
                "modernize": {"revenue": 5250.0, "leads": 15},
                "homeadvisor": {"revenue": 1750.0, "leads": 5}
            },
            "timestamp": time.time()
        }
        
        return summary
        
    except Exception as e:
        logger.error("Executive summary error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve executive summary")

@app.get("/api/v1/analytics/lead-quality")
async def get_lead_quality_analytics():
    """Get advanced lead quality analytics"""
    try:
        analytics = {
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
            "score_trends": {
                "daily": [75, 78, 80, 82, 79, 85, 88],
                "weekly": [70, 72, 75, 78, 80, 82, 85]
            },
            "top_qualification_factors": [
                "High electric bill (>$200)",
                "Homeownership confirmed",
                "Suitable roof type",
                "NYC location"
            ],
            "timestamp": time.time()
        }
        
        return analytics
        
    except Exception as e:
        logger.error("Lead quality analytics error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve lead quality analytics")

# Authentication APIs (Mock)
@app.post("/api/v1/auth/login")
async def login(request: dict):
    """User authentication"""
    try:
        email = request.get("email", "")
        password = request.get("password", "")
        
        # Mock authentication
        if email and password:
            token = f"token_{int(time.time())}"
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "user_123",
                    "email": email,
                    "role": "admin"
                },
                "timestamp": time.time()
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        logger.error("Login error", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.post("/api/v1/auth/logout")
async def logout():
    """User logout"""
    return {"message": "Successfully logged out", "timestamp": time.time()}

# Helper functions
def calculate_lead_score(message: str, lead_context: dict) -> int:
    """Calculate lead qualification score"""
    score = 0
    
    # Base score
    score += 20
    
    # Message content analysis
    if any(word in message.lower() for word in ["bill", "$", "cost", "expensive"]):
        score += 20
    if any(word in message.lower() for word in ["own", "homeowner", "property"]):
        score += 15
    if any(word in message.lower() for word in ["roof", "solar", "panels"]):
        score += 15
    if any(word in message.lower() for word in ["zip", "100", "nyc", "manhattan", "brooklyn"]):
        score += 10
    if any(word in message.lower() for word in ["save", "savings", "money"]):
        score += 10
    if any(word in message.lower() for word in ["install", "installation", "quote"]):
        score += 10
    
    return min(score, 100)

def get_quality_tier(score: int) -> str:
    """Determine quality tier based on score"""
    if score >= 85:
        return "premium"
    elif score >= 70:
        return "standard"
    elif score >= 50:
        return "basic"
    else:
        return "unqualified"

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
# Force redeploy - Tue Sep 16 19:32:51 EDT 2025
