"""
Lead management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.lead import Lead, LeadExport
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadListResponse
from app.services.lead_service import LeadService
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db)
):
    """Create a new lead"""
    lead_service = LeadService(db)
    
    # Check if lead already exists
    existing_lead = lead_service.get_lead_by_email(lead_data.email)
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists"
        )
    
    # Create lead
    lead = lead_service.create_lead(lead_data)
    
    # AI processing for lead scoring and insights
    ai_service = AIService()
    ai_insights = await ai_service.analyze_lead(lead)
    lead = lead_service.update_lead_ai_data(lead.id, ai_insights)
    
    return lead


@router.get("/", response_model=LeadListResponse)
async def get_leads(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    quality: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get leads with filtering"""
    lead_service = LeadService(db)
    leads, total = lead_service.get_leads(
        skip=skip,
        limit=limit,
        status=status,
        quality=quality
    )
    
    return LeadListResponse(
        leads=leads,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific lead"""
    lead_service = LeadService(db)
    lead = lead_service.get_lead(lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: Session = Depends(get_db)
):
    """Update a lead"""
    lead_service = LeadService(db)
    lead = lead_service.update_lead(lead_id, lead_data)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Delete a lead (soft delete)"""
    lead_service = LeadService(db)
    success = lead_service.delete_lead(lead_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return {"message": "Lead deleted successfully"}


@router.post("/{lead_id}/qualify")
async def qualify_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Qualify a lead for export"""
    lead_service = LeadService(db)
    lead = lead_service.qualify_lead(lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return {"message": "Lead qualified successfully", "lead": lead}


@router.get("/{lead_id}/exports")
async def get_lead_exports(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Get export history for a lead"""
    lead_service = LeadService(db)
    exports = lead_service.get_lead_exports(lead_id)
    
    return {"exports": exports}
