"""
WebSocket API for real-time AI conversation
Provides immediate response feel for lead qualification
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.conversation_agent import SolarConversationAgent
from app.services.nyc_market_service import NYCMarketService
from app.services.lead_scoring_service import LeadScoringService
from app.services.b2b_export_service import B2BExportService


class ConnectionManager:
    """Manages WebSocket connections and conversation state"""
    
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
        
        print(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection and cleanup session"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.conversation_sessions:
            del self.conversation_sessions[session_id]
        
        print(f"WebSocket disconnected: {session_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], session_id: str):
        """Send message to specific WebSocket connection"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to {session_id}: {e}")
                self.disconnect(session_id)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation session data"""
        return self.conversation_sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update conversation session data"""
        if session_id in self.conversation_sessions:
            self.conversation_sessions[session_id].update(updates)


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, session_id: str = None, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time AI conversation"""
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Connect to WebSocket
    await manager.connect(websocket, session_id)
    
    # Initialize services
    conversation_agent = SolarConversationAgent(db)
    nyc_service = NYCMarketService(db)
    lead_scoring = LeadScoringService(db)
    b2b_export = B2BExportService(db)
    
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
                session = manager.get_session(session_id)
                if session:
                    session["message_count"] += 1
                    session["last_message_at"] = datetime.utcnow()
                
                # Handle different message types
                if message_type == "user_message":
                    await handle_user_message(
                        websocket, session_id, user_message, 
                        conversation_agent, nyc_service, lead_scoring, b2b_export
                    )
                elif message_type == "get_nyc_data":
                    await handle_nyc_data_request(
                        websocket, session_id, message_data, nyc_service
                    )
                elif message_type == "calculate_savings":
                    await handle_savings_calculation(
                        websocket, session_id, message_data, nyc_service
                    )
                elif message_type == "get_lead_status":
                    await handle_lead_status_request(
                        websocket, session_id, conversation_agent
                    )
                else:
                    await send_error_message(websocket, "Unknown message type")
                
            except json.JSONDecodeError:
                await send_error_message(websocket, "Invalid JSON format")
            except Exception as e:
                print(f"Error processing message: {e}")
                await send_error_message(websocket, "Error processing your message")
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)


async def handle_user_message(
    websocket: WebSocket,
    session_id: str,
    message: str,
    conversation_agent: SolarConversationAgent,
    nyc_service: NYCMarketService,
    lead_scoring: LeadScoringService,
    b2b_export: B2BExportService
):
    """Handle user message and generate AI response"""
    
    try:
        # Process message with conversation agent
        response = await conversation_agent.process_message(message, session_id)
        
        # Update session with response data
        session_updates = {
            "conversation_stage": response.get("stage", "welcome"),
            "lead_score": response.get("lead_score", 0),
            "quality_tier": response.get("quality_tier", "unqualified"),
            "lead_id": response.get("lead_id"),
            "last_response_at": datetime.utcnow()
        }
        manager.update_session(session_id, session_updates)
        
        # Send AI response
        ai_message = {
            "type": "ai_response",
            "message": response["response"],
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_stage": response.get("stage"),
            "lead_score": response.get("lead_score"),
            "quality_tier": response.get("quality_tier"),
            "next_questions": response.get("next_questions", []),
            "nyc_insights": response.get("nyc_insights", {}),
            "urgency_created": response.get("urgency_created", False)
        }
        
        await manager.send_personal_message(ai_message, session_id)
        
        # Send additional data if lead is qualified
        if response.get("quality_tier") in ["premium", "standard", "basic"]:
            await send_qualification_update(websocket, session_id, response, b2b_export)
        
    except Exception as e:
        print(f"Error handling user message: {e}")
        await send_error_message(websocket, "I'm having trouble processing your message. Please try again.")


async def handle_nyc_data_request(
    websocket: WebSocket,
    session_id: str,
    message_data: Dict[str, Any],
    nyc_service: NYCMarketService
):
    """Handle NYC market data request"""
    
    try:
        zip_code = message_data.get("zip_code")
        if not zip_code:
            await send_error_message(websocket, "Zip code is required")
            return
        
        # Get NYC market data
        nyc_data = await nyc_service.get_zip_code_data(zip_code)
        
        if nyc_data:
            response = {
                "type": "nyc_data",
                "zip_code": zip_code,
                "data": nyc_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            response = {
                "type": "nyc_data_error",
                "message": f"No market data available for zip code {zip_code}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        await manager.send_personal_message(response, session_id)
        
    except Exception as e:
        print(f"Error handling NYC data request: {e}")
        await send_error_message(websocket, "Error retrieving NYC market data")


async def handle_savings_calculation(
    websocket: WebSocket,
    session_id: str,
    message_data: Dict[str, Any],
    nyc_service: NYCMarketService
):
    """Handle savings calculation request"""
    
    try:
        zip_code = message_data.get("zip_code")
        monthly_bill = message_data.get("monthly_bill")
        
        if not zip_code or not monthly_bill:
            await send_error_message(websocket, "Zip code and monthly bill are required")
            return
        
        # Calculate savings potential
        savings_data = await nyc_service.calculate_savings_potential(
            zip_code, float(monthly_bill)
        )
        
        response = {
            "type": "savings_calculation",
            "zip_code": zip_code,
            "monthly_bill": monthly_bill,
            "savings_data": savings_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(response, session_id)
        
    except Exception as e:
        print(f"Error handling savings calculation: {e}")
        await send_error_message(websocket, "Error calculating savings potential")


async def handle_lead_status_request(
    websocket: WebSocket,
    session_id: str,
    conversation_agent: SolarConversationAgent
):
    """Handle lead status request"""
    
    try:
        session = manager.get_session(session_id)
        if not session:
            await send_error_message(websocket, "Session not found")
            return
        
        response = {
            "type": "lead_status",
            "session_id": session_id,
            "lead_id": session.get("lead_id"),
            "conversation_stage": session.get("conversation_stage"),
            "lead_score": session.get("lead_score"),
            "quality_tier": session.get("quality_tier"),
            "message_count": session.get("message_count"),
            "connected_at": session.get("connected_at").isoformat(),
            "last_message_at": session.get("last_message_at").isoformat() if session.get("last_message_at") else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(response, session_id)
        
    except Exception as e:
        print(f"Error handling lead status request: {e}")
        await send_error_message(websocket, "Error retrieving lead status")


async def send_qualification_update(
    websocket: WebSocket,
    session_id: str,
    response: Dict[str, Any],
    b2b_export: B2BExportService
):
    """Send qualification update when lead reaches qualified status"""
    
    try:
        lead_id = response.get("lead_id")
        quality_tier = response.get("quality_tier")
        lead_score = response.get("lead_score")
        
        if not lead_id:
            return
        
        # Get B2B export recommendations
        recommendations = await b2b_export.get_export_recommendations(
            lead_score, quality_tier, {}
        )
        
        qualification_message = {
            "type": "qualification_update",
            "message": f"Congratulations! You've been qualified as a {quality_tier} lead with a score of {lead_score}.",
            "lead_id": lead_id,
            "quality_tier": quality_tier,
            "lead_score": lead_score,
            "b2b_recommendations": recommendations,
            "next_steps": [
                "Schedule a consultation with our solar experts",
                "Receive a custom proposal with NYC incentives",
                "Get installation timeline and process details"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(qualification_message, session_id)
        
    except Exception as e:
        print(f"Error sending qualification update: {e}")


async def send_error_message(websocket: WebSocket, error_message: str):
    """Send error message to client"""
    
    error_response = {
        "type": "error",
        "message": error_message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        await websocket.send_text(json.dumps(error_response))
    except Exception as e:
        print(f"Error sending error message: {e}")


# Additional WebSocket endpoints for specific functionality

async def websocket_nyc_insights(websocket: WebSocket, zip_code: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for NYC market insights"""
    
    await websocket.accept()
    nyc_service = NYCMarketService(db)
    
    try:
        # Get comprehensive NYC data
        nyc_data = await nyc_service.get_zip_code_data(zip_code)
        urgency_factors = await nyc_service.get_urgency_factors(zip_code)
        neighborhood_insights = await nyc_service.get_neighborhood_insights(zip_code)
        competition_analysis = await nyc_service.get_competition_analysis(zip_code)
        
        insights_data = {
            "type": "nyc_insights",
            "zip_code": zip_code,
            "market_data": nyc_data,
            "urgency_factors": urgency_factors,
            "neighborhood_insights": neighborhood_insights,
            "competition_analysis": competition_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_text(json.dumps(insights_data))
        
    except Exception as e:
        error_data = {
            "type": "error",
            "message": f"Error retrieving NYC insights: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(error_data))
    
    finally:
        await websocket.close()


async def websocket_lead_analytics(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time lead analytics"""
    
    await websocket.accept()
    b2b_export = B2BExportService(db)
    
    try:
        # Get revenue analytics
        revenue_analytics = await b2b_export.get_revenue_analytics(30)
        
        # Get export optimization recommendations
        optimization_data = await b2b_export.optimize_export_strategies()
        
        analytics_data = {
            "type": "lead_analytics",
            "revenue_analytics": revenue_analytics,
            "optimization_data": optimization_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_text(json.dumps(analytics_data))
        
    except Exception as e:
        error_data = {
            "type": "error",
            "message": f"Error retrieving analytics: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(error_data))
    
    finally:
        await websocket.close()
