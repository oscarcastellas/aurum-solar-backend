"""
B2B Export API Endpoints
RESTful API for B2B lead export and revenue optimization
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import io

from app.core.database import get_db
from app.services.enhanced_b2b_export_service import (
    EnhancedB2BExportService, QualityTier, ExportFormat
)
from app.models.lead import Lead
from pydantic import BaseModel, Field


router = APIRouter()


class LeadExportRequest(BaseModel):
    """Request model for single lead export"""
    lead_id: str = Field(..., description="Lead ID to export")
    platform: str = Field(..., description="Target B2B platform")
    format: Optional[str] = Field("json", description="Export format (json, csv, pdf)")
    priority: Optional[str] = Field("normal", description="Export priority")


class BatchExportRequest(BaseModel):
    """Request model for batch lead export"""
    platform: str = Field(..., description="Target B2B platform")
    quality_tier: Optional[str] = Field(None, description="Quality tier filter")
    max_leads: int = Field(20, description="Maximum number of leads to export")
    format: Optional[str] = Field("json", description="Export format")


class ExportPreviewRequest(BaseModel):
    """Request model for export preview"""
    lead_id: str = Field(..., description="Lead ID to preview")
    platform: str = Field(..., description="Target B2B platform")
    format: Optional[str] = Field("json", description="Export format")


class ExportResponse(BaseModel):
    """Response model for export operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LeadSummary(BaseModel):
    """Summary model for exportable leads"""
    lead_id: str
    quality_tier: str
    estimated_value: float
    confidence_score: float
    customer_name: str
    monthly_bill: Optional[float]
    borough: Optional[str]
    recommended_platforms: List[str]
    created_at: str


@router.get("/exportable-leads", response_model=List[LeadSummary])
async def get_exportable_leads(
    quality_tier: Optional[str] = Query(None, description="Filter by quality tier"),
    limit: int = Query(50, description="Maximum number of leads to return"),
    db: Session = Depends(get_db)
):
    """Get leads ready for B2B export"""
    
    try:
        export_service = EnhancedB2BExportService(db)
        
        # Convert string quality tier to enum
        tier_enum = None
        if quality_tier:
            try:
                tier_enum = QualityTier(quality_tier.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid quality tier: {quality_tier}")
        
        # Get exportable leads
        leads = await export_service.get_exportable_leads(tier_enum, limit)
        
        return leads
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-lead", response_model=ExportResponse)
async def export_single_lead(
    request: LeadExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Export a single lead to a B2B platform"""
    
    try:
        export_service = EnhancedB2BExportService(db)
        
        # Convert format string to enum
        format_enum = None
        if request.format:
            try:
                format_enum = ExportFormat(request.format.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid export format: {request.format}")
        
        # Export the lead
        result = await export_service.export_lead_to_platform(
            request.lead_id, 
            request.platform, 
            format_enum
        )
        
        if result["success"]:
            # Add background task for analytics tracking
            background_tasks.add_task(
                track_export_analytics, 
                request.lead_id, 
                request.platform, 
                result["estimated_value"]
            )
            
            return ExportResponse(
                success=True,
                message=f"Lead successfully exported to {request.platform}",
                data={
                    "lead_id": request.lead_id,
                    "platform": request.platform,
                    "format": request.format,
                    "quality_tier": result["lead_quality"],
                    "estimated_value": result["estimated_value"],
                    "export_timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            return ExportResponse(
                success=False,
                message="Export failed",
                error=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-batch", response_model=ExportResponse)
async def export_batch_leads(
    request: BatchExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Export multiple leads to a B2B platform in batch"""
    
    try:
        export_service = EnhancedB2BExportService(db)
        
        # Convert quality tier string to enum
        tier_enum = None
        if request.quality_tier:
            try:
                tier_enum = QualityTier(request.quality_tier.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid quality tier: {request.quality_tier}")
        
        # Batch export leads
        result = await export_service.batch_export_leads(
            request.platform,
            tier_enum,
            request.max_leads
        )
        
        if result["success"]:
            # Add background task for analytics tracking
            background_tasks.add_task(
                track_batch_export_analytics,
                request.platform,
                result["successful_exports"],
                result["total_estimated_value"]
            )
            
            return ExportResponse(
                success=True,
                message=f"Batch export completed to {request.platform}",
                data={
                    "platform": request.platform,
                    "leads_processed": result["leads_processed"],
                    "successful_exports": result["successful_exports"],
                    "total_estimated_value": result["total_estimated_value"],
                    "export_timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            return ExportResponse(
                success=False,
                message="Batch export failed",
                error=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview-export", response_model=ExportResponse)
async def preview_lead_export(
    request: ExportPreviewRequest,
    db: Session = Depends(get_db)
):
    """Preview how a lead would look when exported to a platform"""
    
    try:
        export_service = EnhancedB2BExportService(db)
        
        # Get enriched lead data
        enriched_data = await export_service.enrich_lead_for_b2b_export(request.lead_id)
        
        if not enriched_data:
            raise HTTPException(status_code=404, detail="Lead not found or enrichment failed")
        
        # Convert format string to enum
        format_enum = None
        if request.format:
            try:
                format_enum = ExportFormat(request.format.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid export format: {request.format}")
        
        # Get platform configuration
        platform_config = export_service.platform_configs.get(request.platform)
        if not platform_config:
            raise HTTPException(status_code=400, detail=f"Platform {request.platform} not configured")
        
        # Generate preview data
        preview_data = export_service._generate_export_format(
            enriched_data, 
            format_enum, 
            platform_config
        )
        
        return ExportResponse(
            success=True,
            message="Export preview generated",
            data={
                "lead_id": request.lead_id,
                "platform": request.platform,
                "format": request.format,
                "quality_tier": enriched_data.quality_tier.value,
                "estimated_value": enriched_data.estimated_value,
                "confidence_score": enriched_data.confidence_score,
                "preview_data": preview_data,
                "platform_requirements_met": export_service._meets_platform_requirements(
                    enriched_data, platform_config
                )
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms", response_model=Dict[str, Any])
async def get_available_platforms(db: Session = Depends(get_db)):
    """Get available B2B platforms and their configurations"""
    
    try:
        export_service = EnhancedB2BExportService(db)
        
        platforms_info = {}
        for platform_name, config in export_service.platform_configs.items():
            platforms_info[platform_name] = {
                "name": config.platform_name,
                "min_lead_score": config.min_lead_score,
                "max_daily_exports": config.max_daily_exports,
                "price_per_lead": config.price_per_lead,
                "quality_tiers_accepted": [tier.value for tier in config.quality_tiers_accepted],
                "format_preference": config.format_preference.value,
                "exclusivity_required": config.exclusivity_required,
                "contact_method": config.contact_method,
                "required_fields": config.required_fields,
                "optional_fields": config.optional_fields
            }
        
        return {
            "platforms": platforms_info,
            "quality_tiers": {
                tier.value: {
                    "min_score": export_service.quality_thresholds[tier]["min_score"],
                    "min_bill": export_service.quality_thresholds[tier]["min_bill"],
                    "min_timeline_urgency": export_service.quality_thresholds[tier]["min_timeline_urgency"]
                }
                for tier in QualityTier
            },
            "export_formats": [format.value for format in ExportFormat]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-history/{lead_id}")
async def get_lead_export_history(lead_id: str, db: Session = Depends(get_db)):
    """Get export history for a specific lead"""
    
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        export_history = {
            "lead_id": str(lead.id),
            "exported_to_platforms": lead.exported_to_platforms or [],
            "export_timestamps": lead.export_timestamps or {},
            "export_status": lead.export_status,
            "exported_at": lead.exported_at.isoformat() if lead.exported_at else None,
            "total_revenue_earned": lead.total_revenue_earned or 0.0
        }
        
        return export_history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-stats")
async def get_export_statistics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get export statistics and performance metrics"""
    
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get export statistics
        exported_leads = db.query(Lead).filter(
            Lead.exported_at >= start_date,
            Lead.exported_at <= end_date,
            Lead.export_status == "exported"
        ).all()
        
        # Calculate metrics
        total_exports = len(exported_leads)
        total_revenue = sum(lead.total_revenue_earned or 0 for lead in exported_leads)
        
        # Platform breakdown
        platform_stats = {}
        for lead in exported_leads:
            if lead.exported_to_platforms:
                for platform in lead.exported_to_platforms:
                    if platform not in platform_stats:
                        platform_stats[platform] = {"count": 0, "revenue": 0}
                    platform_stats[platform]["count"] += 1
                    platform_stats[platform]["revenue"] += lead.total_revenue_earned or 0
        
        # Quality tier breakdown
        quality_stats = {}
        for lead in exported_leads:
            if lead.lead_quality:
                if lead.lead_quality not in quality_stats:
                    quality_stats[lead.lead_quality] = {"count": 0, "revenue": 0}
                quality_stats[lead.lead_quality]["count"] += 1
                quality_stats[lead.lead_quality]["revenue"] += lead.total_revenue_earned or 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_exports": total_exports,
                "total_revenue": total_revenue,
                "average_revenue_per_lead": total_revenue / total_exports if total_exports > 0 else 0,
                "export_success_rate": 1.0  # Simplified - would need more detailed tracking
            },
            "platform_breakdown": platform_stats,
            "quality_breakdown": quality_stats,
            "top_performing_platforms": sorted(
                platform_stats.items(), 
                key=lambda x: x[1]["revenue"], 
                reverse=True
            )[:5]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-export/{format}")
async def download_export_file(
    format: str,
    platform: Optional[str] = Query(None, description="Platform filter"),
    quality_tier: Optional[str] = Query(None, description="Quality tier filter"),
    limit: int = Query(100, description="Maximum number of leads"),
    db: Session = Depends(get_db)
):
    """Download export file in specified format"""
    
    try:
        export_service = EnhancedB2BExportService(db)
        
        # Get exportable leads
        tier_enum = None
        if quality_tier:
            try:
                tier_enum = QualityTier(quality_tier.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid quality tier: {quality_tier}")
        
        leads = await export_service.get_exportable_leads(tier_enum, limit)
        
        # Filter by platform if specified
        if platform:
            leads = [lead for lead in leads if platform in lead["recommended_platforms"]]
        
        # Generate file content
        if format.lower() == "csv":
            content = generate_csv_export(leads)
            media_type = "text/csv"
            filename = f"aurum_solar_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif format.lower() == "json":
            content = json.dumps(leads, indent=2)
            media_type = "application/json"
            filename = f"aurum_solar_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_csv_export(leads: List[Dict[str, Any]]) -> str:
    """Generate CSV export from leads data"""
    
    output = io.StringIO()
    
    if not leads:
        return output.getvalue()
    
    # Get headers from first lead
    headers = list(leads[0].keys())
    
    # Write CSV content
    import csv
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(leads)
    
    return output.getvalue()


async def track_export_analytics(lead_id: str, platform: str, estimated_value: float):
    """Background task to track export analytics"""
    
    # This would integrate with your analytics system
    # For now, just log the export
    print(f"Export Analytics: Lead {lead_id} exported to {platform} with estimated value ${estimated_value}")


async def track_batch_export_analytics(platform: str, count: int, total_value: float):
    """Background task to track batch export analytics"""
    
    # This would integrate with your analytics system
    # For now, just log the batch export
    print(f"Batch Export Analytics: {count} leads exported to {platform} with total estimated value ${total_value}")


@router.post("/test-export")
async def test_export_system(db: Session = Depends(get_db)):
    """Test endpoint to verify B2B export system functionality"""
    
    try:
        export_service = EnhancedB2BExportService(db)
        
        # Get a sample lead for testing
        sample_lead = db.query(Lead).filter(
            Lead.qualification_status == "qualified"
        ).first()
        
        if not sample_lead:
            return {
                "success": False,
                "message": "No qualified leads found for testing",
                "recommendation": "Create some qualified leads first"
            }
        
        # Test enrichment
        enriched_data = await export_service.enrich_lead_for_b2b_export(str(sample_lead.id))
        
        if not enriched_data:
            return {
                "success": False,
                "message": "Lead enrichment failed",
                "error": "Could not enrich lead data"
            }
        
        # Test platform configurations
        platforms_available = list(export_service.platform_configs.keys())
        
        # Test export format generation
        test_formats = {}
        for platform_name, platform_config in export_service.platform_configs.items():
            if enriched_data.quality_tier in platform_config.quality_tiers_accepted:
                json_export = export_service._generate_export_format(
                    enriched_data, ExportFormat.JSON, platform_config
                )
                test_formats[platform_name] = {
                    "format": "json",
                    "data_keys": list(json_export.keys()) if isinstance(json_export, dict) else [],
                    "meets_requirements": export_service._meets_platform_requirements(
                        enriched_data, platform_config
                    )
                }
        
        return {
            "success": True,
            "message": "B2B export system test completed successfully",
            "test_results": {
                "sample_lead_id": str(sample_lead.id),
                "enrichment_success": True,
                "quality_tier": enriched_data.quality_tier.value,
                "estimated_value": enriched_data.estimated_value,
                "confidence_score": enriched_data.confidence_score,
                "platforms_available": platforms_available,
                "compatible_platforms": len(test_formats),
                "export_formats_tested": test_formats,
                "system_ready": True
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "B2B export system test failed",
            "error": str(e),
            "system_ready": False
        }
