"""
Main API router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import leads, analytics, ai_chat, exports, auth, conversation_api

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ai_chat.router, prefix="/ai", tags=["ai-chat"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(conversation_api.router, prefix="/conversation", tags=["conversation"])
