"""
Export Pydantic schemas
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ExportRequest(BaseModel):
    """Export request schema"""
    lead_id: int
    platform: str
    export_data: Optional[Dict[str, Any]] = {}


class ExportResponse(BaseModel):
    """Export response schema"""
    success: bool
    export_id: int
    platform: str
    platform_lead_id: Optional[str] = None
    message: str


class ExportHistoryResponse(BaseModel):
    """Export history response schema"""
    id: int
    lead_id: int
    platform: str
    platform_lead_id: Optional[str] = None
    export_status: str
    price_per_lead: Optional[float] = None
    commission_earned: Optional[float] = None
    created_at: datetime
    exported_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PlatformStatusResponse(BaseModel):
    """Platform status response schema"""
    platform: str
    status: str  # active, inactive, error
    last_sync: Optional[datetime] = None
    total_exports: int
    successful_exports: int
    failed_exports: int
    success_rate: float
    average_response_time: Optional[float] = None
    error_message: Optional[str] = None


class BulkExportRequest(BaseModel):
    """Bulk export request schema"""
    lead_ids: List[int]
    platform: str
    export_data: Optional[Dict[str, Any]] = {}


class BulkExportResponse(BaseModel):
    """Bulk export response schema"""
    message: str
    total_leads: int
    successful_exports: int
    failed_exports: int
    results: List[Dict[str, Any]]
