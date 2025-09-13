"""
Export service for B2B platform integrations
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import json

from app.models.lead import Lead, LeadExport
from app.core.config import settings
from app.schemas.exports import (
    ExportHistoryResponse,
    PlatformStatusResponse
)


class ExportService:
    """Export service for managing B2B platform exports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.platform_configs = {
            "solarreviews": {
                "api_key": settings.SOLARREVIEWS_API_KEY,
                "base_url": "https://api.solarreviews.com/v1",
                "price_per_lead": 150.0
            },
            "modernize": {
                "api_key": settings.MODERNIZE_API_KEY,
                "base_url": "https://api.modernize.com/v1",
                "price_per_lead": 200.0
            }
        }
    
    async def export_lead(
        self,
        lead_id: int,
        platform: str,
        export_data: Dict[str, Any]
    ) -> LeadExport:
        """Export a lead to a B2B platform"""
        
        # Get lead
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead not found")
        
        # Check platform configuration
        if platform not in self.platform_configs:
            raise ValueError(f"Unsupported platform: {platform}")
        
        platform_config = self.platform_configs[platform]
        
        # Prepare export data
        export_payload = self._prepare_export_payload(lead, export_data)
        
        # Create export record
        export = LeadExport(
            lead_id=lead_id,
            platform=platform,
            export_data=export_payload,
            export_status="pending",
            price_per_lead=platform_config["price_per_lead"]
        )
        
        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)
        
        try:
            # Export to platform
            platform_lead_id = await self._export_to_platform(platform, export_payload)
            
            # Update export record
            export.platform_lead_id = platform_lead_id
            export.export_status = "success"
            export.exported_at = datetime.utcnow()
            export.commission_earned = platform_config["price_per_lead"] * 0.15  # 15% commission
            
            # Update lead
            lead.export_status = "exported"
            if not lead.exported_to:
                lead.exported_to = []
            lead.exported_to.append(platform)
            
            if not lead.export_timestamps:
                lead.export_timestamps = {}
            lead.export_timestamps[platform] = str(datetime.utcnow())
            
        except Exception as e:
            # Update export record with error
            export.export_status = "failed"
            export.error_message = str(e)
            export.exported_at = datetime.utcnow()
        
        self.db.commit()
        return export
    
    def _prepare_export_payload(self, lead: Lead, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare lead data for export to B2B platform"""
        
        base_payload = {
            "contact": {
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "phone": lead.phone
            },
            "property": {
                "address": lead.property_address,
                "city": lead.city,
                "state": lead.state,
                "zip_code": lead.zip_code,
                "property_type": lead.property_type,
                "square_footage": lead.square_footage
            },
            "solar_details": {
                "roof_type": lead.roof_type,
                "roof_condition": lead.roof_condition,
                "monthly_electric_bill": lead.monthly_electric_bill
            },
            "lead_qualification": {
                "lead_score": lead.lead_score,
                "lead_quality": lead.lead_quality,
                "estimated_value": lead.estimated_value,
                "ai_insights": lead.ai_insights
            },
            "metadata": {
                "source": lead.source,
                "created_at": lead.created_at.isoformat(),
                "aurum_lead_id": lead.id
            }
        }
        
        # Merge additional data
        base_payload.update(additional_data)
        
        return base_payload
    
    async def _export_to_platform(self, platform: str, payload: Dict[str, Any]) -> str:
        """Export data to specific B2B platform"""
        
        platform_config = self.platform_configs[platform]
        
        async with httpx.AsyncClient() as client:
            if platform == "solarreviews":
                return await self._export_to_solarreviews(client, platform_config, payload)
            elif platform == "modernize":
                return await self._export_to_modernize(client, platform_config, payload)
            else:
                raise ValueError(f"Export not implemented for platform: {platform}")
    
    async def _export_to_solarreviews(self, client: httpx.AsyncClient, config: Dict[str, Any], payload: Dict[str, Any]) -> str:
        """Export to SolarReviews platform"""
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            f"{config['base_url']}/leads",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code == 201:
            response_data = response.json()
            return response_data.get("lead_id", "unknown")
        else:
            raise Exception(f"SolarReviews export failed: {response.status_code} - {response.text}")
    
    async def _export_to_modernize(self, client: httpx.AsyncClient, config: Dict[str, Any], payload: Dict[str, Any]) -> str:
        """Export to Modernize platform"""
        
        headers = {
            "X-API-Key": config["api_key"],
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            f"{config['base_url']}/leads",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code == 201:
            response_data = response.json()
            return response_data.get("id", "unknown")
        else:
            raise Exception(f"Modernize export failed: {response.status_code} - {response.text}")
    
    def get_export_history(
        self,
        lead_id: Optional[int] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ExportHistoryResponse]:
        """Get export history with optional filtering"""
        
        query = self.db.query(LeadExport)
        
        if lead_id:
            query = query.filter(LeadExport.lead_id == lead_id)
        
        if platform:
            query = query.filter(LeadExport.platform == platform)
        
        if status:
            query = query.filter(LeadExport.export_status == status)
        
        exports = query.order_by(LeadExport.created_at.desc()).all()
        
        return [
            ExportHistoryResponse(
                id=export.id,
                lead_id=export.lead_id,
                platform=export.platform,
                platform_lead_id=export.platform_lead_id,
                export_status=export.export_status,
                price_per_lead=export.price_per_lead,
                commission_earned=export.commission_earned,
                created_at=export.created_at,
                exported_at=export.exported_at,
                error_message=export.error_message
            )
            for export in exports
        ]
    
    def get_platform_status(self) -> List[PlatformStatusResponse]:
        """Get status of all B2B platforms"""
        
        platforms = []
        
        for platform_name, config in self.platform_configs.items():
            # Get export statistics
            exports = self.db.query(LeadExport).filter(
                LeadExport.platform == platform_name
            ).all()
            
            total_exports = len(exports)
            successful_exports = len([e for e in exports if e.export_status == "success"])
            failed_exports = len([e for e in exports if e.export_status == "failed"])
            
            # Get last sync time
            last_export = self.db.query(LeadExport).filter(
                LeadExport.platform == platform_name
            ).order_by(LeadExport.created_at.desc()).first()
            
            last_sync = last_export.created_at if last_export else None
            
            # Determine platform status
            if total_exports == 0:
                status = "inactive"
            elif failed_exports > successful_exports:
                status = "error"
            else:
                status = "active"
            
            platforms.append(PlatformStatusResponse(
                platform=platform_name,
                status=status,
                last_sync=last_sync,
                total_exports=total_exports,
                successful_exports=successful_exports,
                failed_exports=failed_exports,
                success_rate=(successful_exports / total_exports * 100) if total_exports > 0 else 0.0,
                average_response_time=None,  # Placeholder
                error_message=None
            ))
        
        return platforms
    
    def get_platform_leads(self, platform: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get leads exported to a specific platform"""
        
        query = self.db.query(LeadExport, Lead).join(
            Lead, LeadExport.lead_id == Lead.id
        ).filter(LeadExport.platform == platform)
        
        if status:
            query = query.filter(LeadExport.export_status == status)
        
        results = query.all()
        
        return [
            {
                "export_id": export.id,
                "lead_id": lead.id,
                "lead_name": f"{lead.first_name} {lead.last_name}",
                "lead_email": lead.email,
                "lead_phone": lead.phone,
                "property_address": lead.property_address,
                "zip_code": lead.zip_code,
                "lead_score": lead.lead_score,
                "lead_quality": lead.lead_quality,
                "export_status": export.export_status,
                "platform_lead_id": export.platform_lead_id,
                "price_per_lead": export.price_per_lead,
                "commission_earned": export.commission_earned,
                "exported_at": export.exported_at,
                "created_at": export.created_at
            }
            for export, lead in results
        ]
    
    async def sync_platform_data(self, platform: str) -> Dict[str, Any]:
        """Sync data with a B2B platform"""
        
        if platform not in self.platform_configs:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # This would implement platform-specific sync logic
        # For now, return a placeholder response
        
        return {
            "platform": platform,
            "sync_status": "completed",
            "synced_at": datetime.utcnow().isoformat(),
            "records_synced": 0,
            "message": f"Sync completed for {platform}"
        }
