"""
AI chat endpoints for lead interaction
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.ai_service import AIService
from app.services.lead_service import LeadService
from app.schemas.ai_chat import ChatMessage, ChatResponse, LeadQuestionsResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_lead(
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """Chat with a lead using AI"""
    ai_service = AIService()
    lead_service = LeadService(db)
    
    # Get lead context
    lead = lead_service.get_lead(message.lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Prepare lead context
    lead_context = {
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "property_address": lead.property_address,
        "city": lead.city,
        "state": lead.state,
        "zip_code": lead.zip_code,
        "monthly_electric_bill": lead.monthly_electric_bill,
        "property_type": lead.property_type,
        "roof_type": lead.roof_type,
        "roof_condition": lead.roof_condition
    }
    
    # Get AI response
    ai_response = await ai_service.chat_with_lead(message.content, lead_context)
    
    # Update lead with conversation data
    if not lead.conversation_data:
        lead.conversation_data = {}
    
    if "conversations" not in lead.conversation_data:
        lead.conversation_data["conversations"] = []
    
    lead.conversation_data["conversations"].append({
        "timestamp": str(datetime.utcnow()),
        "user_message": message.content,
        "ai_response": ai_response,
        "lead_id": message.lead_id
    })
    
    lead_service.update_lead_ai_data(lead.id, {"conversation_data": lead.conversation_data})
    
    return ChatResponse(
        response=ai_response,
        lead_id=message.lead_id,
        timestamp=datetime.utcnow()
    )


@router.get("/questions/{lead_id}", response_model=LeadQuestionsResponse)
async def get_lead_questions(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Get AI-generated follow-up questions for a lead"""
    ai_service = AIService()
    lead_service = LeadService(db)
    
    # Get lead context
    lead = lead_service.get_lead(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Prepare lead context
    lead_context = {
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "property_address": lead.property_address,
        "city": lead.city,
        "state": lead.state,
        "zip_code": lead.zip_code,
        "monthly_electric_bill": lead.monthly_electric_bill,
        "property_type": lead.property_type,
        "roof_type": lead.roof_type,
        "roof_condition": lead.roof_condition
    }
    
    # Generate questions
    questions = await ai_service.generate_lead_questions(lead_context)
    
    return LeadQuestionsResponse(
        lead_id=lead_id,
        questions=questions,
        generated_at=datetime.utcnow()
    )


@router.post("/analyze/{lead_id}")
async def analyze_lead_with_ai(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Re-analyze a lead with AI for updated insights"""
    ai_service = AIService()
    lead_service = LeadService(db)
    
    # Get lead
    lead = lead_service.get_lead(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Analyze with AI
    ai_insights = await ai_service.analyze_lead(lead)
    
    # Update lead
    updated_lead = lead_service.update_lead_ai_data(lead_id, ai_insights)
    
    return {
        "message": "Lead analyzed successfully",
        "lead_id": lead_id,
        "ai_insights": ai_insights,
        "updated_lead": updated_lead
    }
