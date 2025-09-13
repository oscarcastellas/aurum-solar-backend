"""
AI chat Pydantic schemas
"""

from pydantic import BaseModel
from typing import List
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message schema"""
    lead_id: int
    content: str


class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str
    lead_id: int
    timestamp: datetime


class LeadQuestionsResponse(BaseModel):
    """Lead questions response schema"""
    lead_id: int
    questions: List[str]
    generated_at: datetime
