"""
Lead Pydantic schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class LeadBase(BaseModel):
    """Base lead schema"""
    email: EmailStr
    phone: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    
    # Property details
    property_address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(default="New York", max_length=100)
    state: str = Field(default="NY", max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)
    
    # Solar details
    roof_type: Optional[str] = None
    roof_condition: Optional[str] = None
    monthly_electric_bill: Optional[float] = Field(None, ge=0)
    property_type: Optional[str] = None
    square_footage: Optional[int] = Field(None, ge=0)
    
    # Lead metadata
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    """Schema for creating a lead"""
    pass


class LeadUpdate(BaseModel):
    """Schema for updating a lead"""
    phone: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    property_address: Optional[str] = Field(None, min_length=1, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, min_length=5, max_length=10)
    roof_type: Optional[str] = None
    roof_condition: Optional[str] = None
    monthly_electric_bill: Optional[float] = Field(None, ge=0)
    property_type: Optional[str] = None
    square_footage: Optional[int] = Field(None, ge=0)
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(LeadBase):
    """Schema for lead response"""
    id: int
    lead_score: int = 0
    lead_quality: str = "cold"
    status: str = "new"
    export_status: Optional[str] = None
    exported_to: Optional[List[str]] = None
    export_timestamps: Optional[Dict[str, str]] = None
    estimated_value: Optional[float] = None
    actual_value: Optional[float] = None
    commission_rate: float = 0.15
    conversation_data: Optional[Dict[str, Any]] = None
    ai_insights: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_contacted: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    """Schema for lead list response"""
    leads: List[LeadResponse]
    total: int
    skip: int
    limit: int


class LeadExportResponse(BaseModel):
    """Schema for lead export response"""
    id: int
    lead_id: int
    platform: str
    platform_lead_id: Optional[str] = None
    export_status: str
    price_per_lead: Optional[float] = None
    commission_earned: Optional[float] = None
    created_at: datetime
    exported_at: Optional[datetime] = None

    class Config:
        from_attributes = True
