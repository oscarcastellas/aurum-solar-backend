"""
Lead service for business logic
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.lead import Lead, LeadExport
from app.schemas.lead import LeadCreate, LeadUpdate


class LeadService:
    """Lead service for managing lead operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_lead(self, lead_data: LeadCreate) -> Lead:
        """Create a new lead"""
        lead = Lead(**lead_data.dict())
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead
    
    def get_lead(self, lead_id: int) -> Optional[Lead]:
        """Get a lead by ID"""
        return self.db.query(Lead).filter(
            and_(Lead.id == lead_id, Lead.is_active == True)
        ).first()
    
    def get_lead_by_email(self, email: str) -> Optional[Lead]:
        """Get a lead by email"""
        return self.db.query(Lead).filter(
            and_(Lead.email == email, Lead.is_active == True)
        ).first()
    
    def get_leads(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        quality: Optional[str] = None
    ) -> Tuple[List[Lead], int]:
        """Get leads with filtering"""
        query = self.db.query(Lead).filter(Lead.is_active == True)
        
        if status:
            query = query.filter(Lead.status == status)
        
        if quality:
            query = query.filter(Lead.lead_quality == quality)
        
        total = query.count()
        leads = query.offset(skip).limit(limit).all()
        
        return leads, total
    
    def update_lead(self, lead_id: int, lead_data: LeadUpdate) -> Optional[Lead]:
        """Update a lead"""
        lead = self.get_lead(lead_id)
        if not lead:
            return None
        
        update_data = lead_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)
        
        lead.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(lead)
        return lead
    
    def delete_lead(self, lead_id: int) -> bool:
        """Soft delete a lead"""
        lead = self.get_lead(lead_id)
        if not lead:
            return False
        
        lead.is_active = False
        lead.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def qualify_lead(self, lead_id: int) -> Optional[Lead]:
        """Qualify a lead for export"""
        lead = self.get_lead(lead_id)
        if not lead:
            return None
        
        # Update lead status and quality
        lead.status = "qualified"
        lead.lead_quality = "warm"  # or "hot" based on scoring
        lead.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(lead)
        return lead
    
    def update_lead_ai_data(self, lead_id: int, ai_insights: dict) -> Optional[Lead]:
        """Update lead with AI insights"""
        lead = self.get_lead(lead_id)
        if not lead:
            return None
        
        lead.ai_insights = ai_insights.get("insights", "")
        lead.lead_score = ai_insights.get("score", 0)
        lead.lead_quality = ai_insights.get("quality", "cold")
        lead.estimated_value = ai_insights.get("estimated_value", 0)
        lead.conversation_data = ai_insights.get("conversation_data", {})
        
        self.db.commit()
        self.db.refresh(lead)
        return lead
    
    def get_lead_exports(self, lead_id: int) -> List[LeadExport]:
        """Get export history for a lead"""
        return self.db.query(LeadExport).filter(LeadExport.lead_id == lead_id).all()
    
    def export_lead(self, lead_id: int, platform: str, export_data: dict) -> LeadExport:
        """Export a lead to a B2B platform"""
        lead = self.get_lead(lead_id)
        if not lead:
            raise ValueError("Lead not found")
        
        # Create export record
        export = LeadExport(
            lead_id=lead_id,
            platform=platform,
            export_data=export_data,
            export_status="pending"
        )
        
        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)
        
        # Update lead export status
        lead.export_status = "pending"
        if not lead.exported_to:
            lead.exported_to = []
        lead.exported_to.append(platform)
        
        self.db.commit()
        return export
