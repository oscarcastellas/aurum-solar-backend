"""
Lead export endpoints for B2B platform integrations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.export_service import ExportService
from app.services.lead_service import LeadService
from app.schemas.exports import (
    ExportRequest,
    ExportResponse,
    ExportHistoryResponse,
    PlatformStatusResponse
)

router = APIRouter()


@router.post("/export", response_model=ExportResponse)
async def export_lead(
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export a lead to a B2B platform"""
    export_service = ExportService(db)
    lead_service = LeadService(db)
    
    # Verify lead exists
    lead = lead_service.get_lead(export_request.lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Check if lead is qualified
    if lead.status != "qualified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead must be qualified before export"
        )
    
    # Export lead
    try:
        export_result = await export_service.export_lead(
            lead_id=export_request.lead_id,
            platform=export_request.platform,
            export_data=export_request.export_data
        )
        
        return ExportResponse(
            success=True,
            export_id=export_result.id,
            platform=export_result.platform,
            platform_lead_id=export_result.platform_lead_id,
            message="Lead exported successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/history", response_model=List[ExportHistoryResponse])
async def get_export_history(
    lead_id: Optional[int] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get export history with optional filtering"""
    export_service = ExportService(db)
    
    exports = export_service.get_export_history(
        lead_id=lead_id,
        platform=platform,
        status=status
    )
    
    return exports


@router.get("/platforms/status", response_model=List[PlatformStatusResponse])
async def get_platform_status(
    db: Session = Depends(get_db)
):
    """Get status of all B2B platforms"""
    export_service = ExportService(db)
    
    platform_status = export_service.get_platform_status()
    return platform_status


@router.post("/bulk-export")
async def bulk_export_leads(
    lead_ids: List[int],
    platform: str,
    db: Session = Depends(get_db)
):
    """Export multiple leads to a B2B platform"""
    export_service = ExportService(db)
    lead_service = LeadService(db)
    
    results = []
    
    for lead_id in lead_ids:
        try:
            # Verify lead exists and is qualified
            lead = lead_service.get_lead(lead_id)
            if not lead:
                results.append({
                    "lead_id": lead_id,
                    "success": False,
                    "error": "Lead not found"
                })
                continue
            
            if lead.status != "qualified":
                results.append({
                    "lead_id": lead_id,
                    "success": False,
                    "error": "Lead not qualified"
                })
                continue
            
            # Export lead
            export_result = await export_service.export_lead(
                lead_id=lead_id,
                platform=platform,
                export_data={}
            )
            
            results.append({
                "lead_id": lead_id,
                "success": True,
                "export_id": export_result.id,
                "platform_lead_id": export_result.platform_lead_id
            })
            
        except Exception as e:
            results.append({
                "lead_id": lead_id,
                "success": False,
                "error": str(e)
            })
    
    return {
        "message": "Bulk export completed",
        "total_leads": len(lead_ids),
        "successful_exports": len([r for r in results if r["success"]]),
        "failed_exports": len([r for r in results if not r["success"]]),
        "results": results
    }


@router.get("/platforms/{platform}/leads")
async def get_platform_leads(
    platform: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get leads exported to a specific platform"""
    export_service = ExportService(db)
    
    leads = export_service.get_platform_leads(platform, status)
    return leads


@router.post("/platforms/{platform}/sync")
async def sync_platform_data(
    platform: str,
    db: Session = Depends(get_db)
):
    """Sync data with a B2B platform"""
    export_service = ExportService(db)
    
    try:
        sync_result = await export_service.sync_platform_data(platform)
        return {
            "message": f"Platform {platform} synced successfully",
            "sync_result": sync_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
