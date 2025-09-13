"""
WebSocket Manager for Real-time Chat and Analytics
Handles concurrent connections, message routing, and connection management
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
import structlog

from app.core.database import get_db
from app.services.conversation_agent import SolarConversationAgent
from app.services.nyc_market_service import NYCMarketService
from app.services.lead_scoring_service import LeadScoringService
from app.services.b2b_export_service import B2BExportService
from app.services.analytics_service import AnalyticsService
from app.core.redis import get_redis

logger = structlog.get_logger()

class WebSocketManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.nyc_insights_connections: Set[WebSocket] = set()
        self.analytics_connections: Set[WebSocket] = set()
        self.connection_lock = asyncio.Lock()
        
        # Service instances
        self.conversation_agent = None
        self.nyc_service = None
        self.lead_scoring = None
        self.b2b_export = None
        self.analytics = None
        
        # Connection metrics
        self.total_connections = 0
        self.active_sessions = 0
        self.messages_processed = 0
        self.start_time = datetime.utcnow()
    
    async def initialize_services(self):
        """Initialize service instances"""
        if not self.conversation_agent:
            db = next(get_db())
            self.conversation_agent = SolarConversationAgent(db)
            self.nyc_service = NYCMarketService(db)
            self.lead_scoring = LeadScoringService(db)
            self.b2b_export = B2BExportService(db)
            self.analytics = AnalyticsService(db)
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        async with self.connection_lock:
            self.active_connections[session_id] = websocket
            self.connection_metadata[session_id] = {
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "message_count": 0,
                "session_type": "chat"
            }
            self.total_connections += 1
            self.active_sessions += 1
        
        await self.initialize_services()
        
        logger.info("WebSocket connected", session_id=session_id, total_connections=len(self.active_connections))
        
        try:
            # Send welcome message
            welcome_message = {
                "type": "welcome",
                "message": "Welcome to Aurum Solar AI! I'm here to help you explore solar options for your NYC home.",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "suggestions": [
                    "What's your monthly electric bill?",
                    "Do you own your home?",
                    "What zip code are you in?"
                ]
            }
            
            await self.send_personal_message(session_id, welcome_message)
            
            # Main message loop
            while True:
                try:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Update connection metadata
                    async with self.connection_lock:
                        if session_id in self.connection_metadata:
                            self.connection_metadata[session_id]["last_activity"] = datetime.utcnow()
                            self.connection_metadata[session_id]["message_count"] += 1
                    
                    # Process message
                    await self.process_message(session_id, message_data)
                    
                except json.JSONDecodeError:
                    await self.send_error(session_id, "Invalid JSON format")
                except Exception as e:
                    logger.error("Error processing message", session_id=session_id, error=str(e))
                    await self.send_error(session_id, "Error processing your message")
        
        except WebSocketDisconnect:
            await self.disconnect(session_id)
        except Exception as e:
            logger.error("WebSocket error", session_id=session_id, error=str(e))
            await self.disconnect(session_id)
    
    async def connect_nyc_insights(self, websocket: WebSocket, zip_code: str):
        """Connect for NYC market insights"""
        await websocket.accept()
        self.nyc_insights_connections.add(websocket)
        
        await self.initialize_services()
        
        try:
            # Get comprehensive NYC data
            nyc_data = await self.nyc_service.get_zip_code_data(zip_code)
            urgency_factors = await self.nyc_service.get_urgency_factors(zip_code)
            neighborhood_insights = await self.nyc_service.get_neighborhood_insights(zip_code)
            competition_analysis = await self.nyc_service.get_competition_analysis(zip_code)
            
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
            self.nyc_insights_connections.discard(websocket)
            await websocket.close()
    
    async def connect_analytics(self, websocket: WebSocket):
        """Connect for real-time analytics"""
        await websocket.accept()
        self.analytics_connections.add(websocket)
        
        await self.initialize_services()
        
        try:
            # Send initial analytics data
            analytics_data = await self.analytics.get_realtime_metrics()
            await websocket.send_text(json.dumps(analytics_data))
            
            # Keep connection alive and send updates
            while True:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                analytics_data = await self.analytics.get_realtime_metrics()
                await websocket.send_text(json.dumps(analytics_data))
                
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error("Analytics WebSocket error", error=str(e))
        finally:
            self.analytics_connections.discard(websocket)
            await websocket.close()
    
    async def process_message(self, session_id: str, message_data: Dict[str, Any]):
        """Process incoming message and generate response"""
        try:
            message_type = message_data.get("type", "user_message")
            message_content = message_data.get("message", "")
            
            if message_type == "user_message":
                await self.process_chat_message(session_id, message_content)
            elif message_type == "get_nyc_data":
                await self.process_nyc_data_request(session_id, message_data)
            elif message_type == "calculate_savings":
                await self.process_savings_calculation(session_id, message_data)
            elif message_type == "get_lead_status":
                await self.process_lead_status_request(session_id)
            else:
                await self.send_error(session_id, "Unknown message type")
        
        except Exception as e:
            logger.error("Error processing message", session_id=session_id, error=str(e))
            await self.send_error(session_id, "Error processing your message")
    
    async def process_chat_message(self, session_id: str, message: str):
        """Process chat message with AI agent"""
        try:
            # Process message with conversation agent
            response = await self.conversation_agent.process_message(message, session_id)
            
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
            
            await self.send_personal_message(session_id, ai_message)
            
            # Send qualification update if lead is qualified
            if response.get("quality_tier") in ["premium", "standard", "basic"]:
                await self.send_qualification_update(session_id, response)
            
            # Update metrics
            self.messages_processed += 1
            
        except Exception as e:
            logger.error("Error processing chat message", session_id=session_id, error=str(e))
            await self.send_error(session_id, "I'm having trouble processing your message. Please try again.")
    
    async def process_nyc_data_request(self, session_id: str, message_data: Dict[str, Any]):
        """Process NYC market data request"""
        try:
            zip_code = message_data.get("zip_code")
            if not zip_code:
                await self.send_error(session_id, "Zip code is required")
                return
            
            # Get NYC market data
            nyc_data = await self.nyc_service.get_zip_code_data(zip_code)
            
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
            
            await self.send_personal_message(session_id, response)
            
        except Exception as e:
            logger.error("Error processing NYC data request", session_id=session_id, error=str(e))
            await self.send_error(session_id, "Error retrieving NYC market data")
    
    async def process_savings_calculation(self, session_id: str, message_data: Dict[str, Any]):
        """Process savings calculation request"""
        try:
            zip_code = message_data.get("zip_code")
            monthly_bill = message_data.get("monthly_bill")
            
            if not zip_code or not monthly_bill:
                await self.send_error(session_id, "Zip code and monthly bill are required")
                return
            
            # Calculate savings potential
            savings_data = await self.nyc_service.calculate_savings_potential(
                zip_code, float(monthly_bill)
            )
            
            response = {
                "type": "savings_calculation",
                "zip_code": zip_code,
                "monthly_bill": monthly_bill,
                "savings_data": savings_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.send_personal_message(session_id, response)
            
        except Exception as e:
            logger.error("Error processing savings calculation", session_id=session_id, error=str(e))
            await self.send_error(session_id, "Error calculating savings potential")
    
    async def process_lead_status_request(self, session_id: str):
        """Process lead status request"""
        try:
            # Get lead status from conversation agent
            lead_status = await self.conversation_agent.get_lead_status(session_id)
            
            response = {
                "type": "lead_status",
                "session_id": session_id,
                "lead_id": lead_status.get("lead_id"),
                "conversation_stage": lead_status.get("stage"),
                "lead_score": lead_status.get("lead_score"),
                "quality_tier": lead_status.get("quality_tier"),
                "message_count": lead_status.get("message_count"),
                "connected_at": lead_status.get("connected_at"),
                "last_message_at": lead_status.get("last_message_at"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.send_personal_message(session_id, response)
            
        except Exception as e:
            logger.error("Error processing lead status request", session_id=session_id, error=str(e))
            await self.send_error(session_id, "Error retrieving lead status")
    
    async def send_qualification_update(self, session_id: str, response: Dict[str, Any]):
        """Send qualification update when lead reaches qualified status"""
        try:
            lead_id = response.get("lead_id")
            quality_tier = response.get("quality_tier")
            lead_score = response.get("lead_score")
            
            if not lead_id:
                return
            
            # Get B2B export recommendations
            recommendations = await self.b2b_export.get_export_recommendations(
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
            
            await self.send_personal_message(session_id, qualification_message)
            
        except Exception as e:
            logger.error("Error sending qualification update", session_id=session_id, error=str(e))
    
    async def send_personal_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific WebSocket connection"""
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error("Error sending message", session_id=session_id, error=str(e))
                await self.disconnect(session_id)
    
    async def send_error(self, session_id: str, error_message: str):
        """Send error message to client"""
        error_response = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(session_id, error_response)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error("Error broadcasting message", session_id=session_id, error=str(e))
                await self.disconnect(session_id)
    
    async def disconnect(self, session_id: str):
        """Disconnect WebSocket connection"""
        async with self.connection_lock:
            if session_id in self.active_connections:
                try:
                    websocket = self.active_connections[session_id]
                    await websocket.close()
                except Exception as e:
                    logger.error("Error closing WebSocket", session_id=session_id, error=str(e))
                
                del self.active_connections[session_id]
                if session_id in self.connection_metadata:
                    del self.connection_metadata[session_id]
                
                self.active_sessions -= 1
        
        logger.info("WebSocket disconnected", session_id=session_id, active_connections=len(self.active_connections))
    
    async def disconnect_all(self):
        """Disconnect all WebSocket connections"""
        async with self.connection_lock:
            for session_id in list(self.active_connections.keys()):
                await self.disconnect(session_id)
    
    def get_connection_count(self) -> int:
        """Get current connection count"""
        return len(self.active_connections)
    
    def get_connection_metadata(self) -> Dict[str, Any]:
        """Get connection metadata"""
        return {
            "total_connections": self.total_connections,
            "active_connections": len(self.active_connections),
            "active_sessions": self.active_sessions,
            "messages_processed": self.messages_processed,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "nyc_insights_connections": len(self.nyc_insights_connections),
            "analytics_connections": len(self.analytics_connections)
        }
    
    def is_healthy(self) -> bool:
        """Check if WebSocket manager is healthy"""
        return len(self.active_connections) >= 0  # Basic health check
    
    async def cleanup_stale_connections(self):
        """Clean up stale connections"""
        current_time = datetime.utcnow()
        stale_sessions = []
        
        async with self.connection_lock:
            for session_id, metadata in self.connection_metadata.items():
                if current_time - metadata["last_activity"] > timedelta(hours=1):
                    stale_sessions.append(session_id)
        
        for session_id in stale_sessions:
            await self.disconnect(session_id)
        
        if stale_sessions:
            logger.info("Cleaned up stale connections", count=len(stale_sessions))
