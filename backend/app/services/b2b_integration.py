"""
B2B Integration Service
Handles multiple lead buyers with different formats and delivery methods
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import structlog

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lead import Lead, LeadExport
from app.models.b2b_platforms import B2BPlatform, B2BLeadMapping, B2BRevenueTransaction
from app.core.redis import get_redis

logger = structlog.get_logger()

class ExportFormat(Enum):
    """B2B export formats"""
    JSON_API = "json_api"
    CSV_EMAIL = "csv_email"
    WEBHOOK = "webhook"
    SFTP = "sftp"
    FTP = "ftp"

class DeliveryStatus(Enum):
    """Delivery status"""
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class B2BExportRequest:
    """B2B export request"""
    lead_id: str
    platform_id: str
    format: ExportFormat
    priority: str
    delivery_method: str
    custom_fields: Dict[str, Any]
    sla_deadline: datetime

@dataclass
class B2BExportResult:
    """B2B export result"""
    export_id: str
    platform: str
    status: DeliveryStatus
    delivery_time_ms: int
    external_id: Optional[str]
    revenue: float
    commission: float
    error_message: Optional[str]
    retry_count: int

class B2BIntegrationService:
    """High-performance B2B integration service"""
    
    def __init__(self):
        self.platforms: Dict[str, Dict[str, Any]] = {}
        self.export_queue = asyncio.Queue()
        self.retry_queue = asyncio.Queue()
        self.active_exports: Dict[str, B2BExportResult] = {}
        self.redis = None
        
        # Performance metrics
        self.total_exports = 0
        self.successful_exports = 0
        self.failed_exports = 0
        self.total_revenue = 0.0
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize the B2B integration service"""
        self.redis = await get_redis()
        await self._load_platform_configurations()
        await self._start_export_workers()
    
    async def _load_platform_configurations(self):
        """Load B2B platform configurations from database"""
        try:
            db = next(get_db())
            platforms = db.query(B2BPlatform).filter(B2BPlatform.is_active == True).all()
            
            for platform in platforms:
                self.platforms[platform.platform_code] = {
                    "id": str(platform.id),
                    "name": platform.platform_name,
                    "code": platform.platform_code,
                    "api_endpoint": platform.api_endpoint,
                    "api_key": platform.api_key,
                    "webhook_url": platform.webhook_url,
                    "email_address": platform.email_address,
                    "supported_formats": platform.supported_formats or ["json_api"],
                    "min_lead_score": platform.min_lead_score or 50,
                    "max_daily_exports": platform.max_daily_exports or 100,
                    "revenue_share": platform.revenue_share or 0.15,
                    "sla_minutes": platform.sla_minutes or 30,
                    "health_status": platform.health_status or "unknown",
                    "is_accepting_leads": platform.is_accepting_leads or False,
                    "custom_fields": platform.custom_fields or {},
                    "rate_limit_per_minute": platform.rate_limit_per_minute or 60
                }
            
            logger.info("Loaded B2B platform configurations", count=len(self.platforms))
            
        except Exception as e:
            logger.error("Error loading platform configurations", error=str(e))
    
    async def _start_export_workers(self):
        """Start background workers for export processing"""
        # Start main export worker
        asyncio.create_task(self._export_worker())
        
        # Start retry worker
        asyncio.create_task(self._retry_worker())
        
        # Start health check worker
        asyncio.create_task(self._health_check_worker())
        
        logger.info("B2B export workers started")
    
    async def export_lead(
        self, 
        lead_id: str, 
        platform_code: str, 
        export_format: ExportFormat = ExportFormat.JSON_API,
        priority: str = "normal"
    ) -> B2BExportResult:
        """Export a lead to a B2B platform"""
        
        try:
            # Validate platform
            if platform_code not in self.platforms:
                raise ValueError(f"Platform {platform_code} not found")
            
            platform = self.platforms[platform_code]
            
            if not platform["is_accepting_leads"]:
                raise ValueError(f"Platform {platform_code} not accepting leads")
            
            # Get lead data
            db = next(get_db())
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Create export request
            export_request = B2BExportRequest(
                lead_id=lead_id,
                platform_id=platform["id"],
                format=export_format,
                priority=priority,
                delivery_method=platform["api_endpoint"],
                custom_fields=platform["custom_fields"],
                sla_deadline=datetime.utcnow() + timedelta(minutes=platform["sla_minutes"])
            )
            
            # Process export based on format
            if export_format == ExportFormat.JSON_API:
                result = await self._export_via_json_api(lead, platform, export_request)
            elif export_format == ExportFormat.WEBHOOK:
                result = await self._export_via_webhook(lead, platform, export_request)
            elif export_format == ExportFormat.CSV_EMAIL:
                result = await self._export_via_csv_email(lead, platform, export_request)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Update metrics
            await self._update_export_metrics(result)
            
            # Store export record
            await self._store_export_record(lead, platform, result)
            
            logger.info(
                "Lead exported successfully",
                lead_id=lead_id,
                platform=platform_code,
                export_id=result.export_id,
                revenue=result.revenue
            )
            
            return result
            
        except Exception as e:
            logger.error("Error exporting lead", lead_id=lead_id, platform=platform_code, error=str(e))
            
            return B2BExportResult(
                export_id=str(uuid.uuid4()),
                platform=platform_code,
                status=DeliveryStatus.FAILED,
                delivery_time_ms=0,
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=str(e),
                retry_count=0
            )
    
    async def _export_via_json_api(
        self, 
        lead: Lead, 
        platform: Dict[str, Any], 
        request: B2BExportRequest
    ) -> B2BExportResult:
        """Export lead via JSON API"""
        
        start_time = datetime.utcnow()
        export_id = str(uuid.uuid4())
        
        try:
            # Prepare lead data
            lead_data = await self._prepare_lead_data(lead, platform)
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {platform['api_key']}",
                    "Content-Type": "application/json",
                    "User-Agent": "AurumSolar/1.0"
                }
                
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with session.post(
                    platform["api_endpoint"],
                    json=lead_data,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    
                    response_data = await response.json()
                    delivery_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    if response.status == 200:
                        # Calculate revenue
                        revenue = self._calculate_revenue(lead, platform)
                        commission = revenue * platform["revenue_share"]
                        
                        return B2BExportResult(
                            export_id=export_id,
                            platform=platform["code"],
                            status=DeliveryStatus.DELIVERED,
                            delivery_time_ms=int(delivery_time),
                            external_id=response_data.get("lead_id"),
                            revenue=revenue,
                            commission=commission,
                            error_message=None,
                            retry_count=0
                        )
                    else:
                        return B2BExportResult(
                            export_id=export_id,
                            platform=platform["code"],
                            status=DeliveryStatus.FAILED,
                            delivery_time_ms=int(delivery_time),
                            external_id=None,
                            revenue=0.0,
                            commission=0.0,
                            error_message=f"API error: {response.status} - {response_data.get('message', 'Unknown error')}",
                            retry_count=0
                        )
        
        except asyncio.TimeoutError:
            return B2BExportResult(
                export_id=export_id,
                platform=platform["code"],
                status=DeliveryStatus.FAILED,
                delivery_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message="Request timeout",
                retry_count=0
            )
        except Exception as e:
            return B2BExportResult(
                export_id=export_id,
                platform=platform["code"],
                status=DeliveryStatus.FAILED,
                delivery_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=str(e),
                retry_count=0
            )
    
    async def _export_via_webhook(
        self, 
        lead: Lead, 
        platform: Dict[str, Any], 
        request: B2BExportRequest
    ) -> B2BExportResult:
        """Export lead via webhook"""
        
        start_time = datetime.utcnow()
        export_id = str(uuid.uuid4())
        
        try:
            # Prepare lead data
            lead_data = await self._prepare_lead_data(lead, platform)
            
            # Add webhook-specific fields
            webhook_data = {
                "event": "lead.created",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "aurum_solar",
                "data": lead_data
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "AurumSolar/1.0",
                    "X-Webhook-Signature": self._generate_webhook_signature(webhook_data, platform["api_key"])
                }
                
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with session.post(
                    platform["webhook_url"],
                    json=webhook_data,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    
                    delivery_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    if response.status in [200, 201, 202]:
                        revenue = self._calculate_revenue(lead, platform)
                        commission = revenue * platform["revenue_share"]
                        
                        return B2BExportResult(
                            export_id=export_id,
                            platform=platform["code"],
                            status=DeliveryStatus.DELIVERED,
                            delivery_time_ms=int(delivery_time),
                            external_id=None,
                            revenue=revenue,
                            commission=commission,
                            error_message=None,
                            retry_count=0
                        )
                    else:
                        return B2BExportResult(
                            export_id=export_id,
                            platform=platform["code"],
                            status=DeliveryStatus.FAILED,
                            delivery_time_ms=int(delivery_time),
                            external_id=None,
                            revenue=0.0,
                            commission=0.0,
                            error_message=f"Webhook error: {response.status}",
                            retry_count=0
                        )
        
        except Exception as e:
            return B2BExportResult(
                export_id=export_id,
                platform=platform["code"],
                status=DeliveryStatus.FAILED,
                delivery_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=str(e),
                retry_count=0
            )
    
    async def _export_via_csv_email(
        self, 
        lead: Lead, 
        platform: Dict[str, Any], 
        request: B2BExportRequest
    ) -> B2BExportResult:
        """Export lead via CSV email"""
        
        start_time = datetime.utcnow()
        export_id = str(uuid.uuid4())
        
        try:
            # Prepare CSV data
            csv_data = await self._prepare_csv_data(lead, platform)
            
            # Send email (simplified - in production, use proper email service)
            # This would integrate with SendGrid, AWS SES, etc.
            
            delivery_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            revenue = self._calculate_revenue(lead, platform)
            commission = revenue * platform["revenue_share"]
            
            return B2BExportResult(
                export_id=export_id,
                platform=platform["code"],
                status=DeliveryStatus.DELIVERED,
                delivery_time_ms=int(delivery_time),
                external_id=None,
                revenue=revenue,
                commission=commission,
                error_message=None,
                retry_count=0
            )
        
        except Exception as e:
            return B2BExportResult(
                export_id=export_id,
                platform=platform["code"],
                status=DeliveryStatus.FAILED,
                delivery_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=str(e),
                retry_count=0
            )
    
    async def _prepare_lead_data(self, lead: Lead, platform: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare lead data for export"""
        
        # Base lead data
        lead_data = {
            "lead_id": str(lead.id),
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
                "borough": lead.borough,
                "property_type": lead.property_type,
                "square_footage": lead.square_footage
            },
            "solar_details": {
                "roof_type": lead.roof_type,
                "roof_condition": lead.roof_condition,
                "monthly_electric_bill": lead.monthly_electric_bill,
                "electric_provider": lead.electric_provider
            },
            "qualification": {
                "lead_score": lead.lead_score,
                "lead_quality": lead.lead_quality,
                "qualification_status": lead.qualification_status,
                "estimated_value": lead.estimated_value
            },
            "metadata": {
                "source": lead.source,
                "created_at": lead.created_at.isoformat(),
                "aurum_lead_id": str(lead.id),
                "quality_tier": lead.lead_quality,
                "export_priority": "normal"
            }
        }
        
        # Add platform-specific custom fields
        if platform["custom_fields"]:
            lead_data["custom_fields"] = platform["custom_fields"]
        
        # Add AI insights if available
        if lead.ai_insights:
            try:
                ai_insights = json.loads(lead.ai_insights)
                lead_data["ai_insights"] = ai_insights
            except:
                pass
        
        return lead_data
    
    async def _prepare_csv_data(self, lead: Lead, platform: Dict[str, Any]) -> str:
        """Prepare CSV data for email export"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # CSV headers
        headers = [
            "Lead ID", "First Name", "Last Name", "Email", "Phone",
            "Address", "City", "State", "Zip Code", "Borough",
            "Property Type", "Square Footage", "Roof Type", "Roof Condition",
            "Monthly Electric Bill", "Electric Provider", "Lead Score",
            "Lead Quality", "Estimated Value", "Created At"
        ]
        
        writer.writerow(headers)
        
        # Lead data row
        row = [
            str(lead.id),
            lead.first_name,
            lead.last_name,
            lead.email,
            lead.phone,
            lead.property_address,
            lead.city,
            lead.state,
            lead.zip_code,
            lead.borough,
            lead.property_type,
            lead.square_footage,
            lead.roof_type,
            lead.roof_condition,
            lead.monthly_electric_bill,
            lead.electric_provider,
            lead.lead_score,
            lead.lead_quality,
            lead.estimated_value,
            lead.created_at.isoformat()
        ]
        
        writer.writerow(row)
        
        return output.getvalue()
    
    def _calculate_revenue(self, lead: Lead, platform: Dict[str, Any]) -> float:
        """Calculate revenue for lead export"""
        base_value = lead.estimated_value or 0
        return base_value * (1 - platform["revenue_share"])
    
    def _generate_webhook_signature(self, data: Dict[str, Any], secret: str) -> str:
        """Generate webhook signature for security"""
        import hmac
        import hashlib
        
        payload = json.dumps(data, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def _update_export_metrics(self, result: B2BExportResult):
        """Update export metrics"""
        self.total_exports += 1
        
        if result.status == DeliveryStatus.DELIVERED:
            self.successful_exports += 1
            self.total_revenue += result.revenue
        else:
            self.failed_exports += 1
        
        # Update Redis metrics
        if self.redis:
            await self.redis.hincrby("b2b_export_metrics", "total_exports", 1)
            await self.redis.hincrby("b2b_export_metrics", f"status_{result.status.value}", 1)
            await self.redis.hincrby("b2b_export_metrics", f"platform_{result.platform}", 1)
            await self.redis.hincrbyfloat("b2b_export_metrics", "total_revenue", result.revenue)
    
    async def _store_export_record(self, lead: Lead, platform: Dict[str, Any], result: B2BExportResult):
        """Store export record in database"""
        try:
            db = next(get_db())
            
            export_record = LeadExport(
                lead_id=lead.id,
                platform_id=platform["id"],
                export_status=result.status.value,
                export_priority="normal",
                export_data=await self._prepare_lead_data(lead, platform),
                export_format="json",
                export_version="v1",
                price_per_lead=result.revenue,
                commission_rate=platform["revenue_share"],
                platform_lead_id=result.external_id,
                response_data={"delivery_time_ms": result.delivery_time_ms},
                exported_at=datetime.utcnow() if result.status == DeliveryStatus.DELIVERED else None,
                commission_earned=result.commission,
                error_message=result.error_message,
                retry_count=result.retry_count
            )
            
            db.add(export_record)
            db.commit()
            
        except Exception as e:
            logger.error("Error storing export record", error=str(e))
            db.rollback()
    
    async def _export_worker(self):
        """Background worker for processing exports"""
        while True:
            try:
                # Process exports from queue
                if not self.export_queue.empty():
                    export_request = await self.export_queue.get()
                    # Process export request
                    # Implementation would go here
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("Error in export worker", error=str(e))
                await asyncio.sleep(5)
    
    async def _retry_worker(self):
        """Background worker for retrying failed exports"""
        while True:
            try:
                # Process retries from queue
                if not self.retry_queue.empty():
                    failed_export = await self.retry_queue.get()
                    # Retry failed export
                    # Implementation would go here
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error("Error in retry worker", error=str(e))
                await asyncio.sleep(10)
    
    async def _health_check_worker(self):
        """Background worker for platform health checks"""
        while True:
            try:
                # Check platform health
                for platform_code, platform in self.platforms.items():
                    await self._check_platform_health(platform_code, platform)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error("Error in health check worker", error=str(e))
                await asyncio.sleep(60)
    
    async def _check_platform_health(self, platform_code: str, platform: Dict[str, Any]):
        """Check health of a B2B platform"""
        try:
            if not platform["api_endpoint"]:
                return
            
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                
                async with session.get(
                    f"{platform['api_endpoint']}/health",
                    timeout=timeout
                ) as response:
                    
                    if response.status == 200:
                        platform["health_status"] = "healthy"
                    else:
                        platform["health_status"] = "degraded"
        
        except Exception as e:
            platform["health_status"] = "unhealthy"
            logger.warning("Platform health check failed", platform=platform_code, error=str(e))
    
    async def get_export_metrics(self) -> Dict[str, Any]:
        """Get export metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        metrics = {
            "total_exports": self.total_exports,
            "successful_exports": self.successful_exports,
            "failed_exports": self.failed_exports,
            "total_revenue": self.total_revenue,
            "uptime_seconds": uptime,
            "export_rate_per_hour": self.total_exports / (uptime / 3600) if uptime > 0 else 0,
            "success_rate": self.successful_exports / self.total_exports if self.total_exports > 0 else 0,
            "average_revenue_per_export": self.total_revenue / self.successful_exports if self.successful_exports > 0 else 0,
            "platforms": {
                code: {
                    "health_status": platform["health_status"],
                    "is_accepting_leads": platform["is_accepting_leads"],
                    "daily_export_limit": platform["max_daily_exports"]
                }
                for code, platform in self.platforms.items()
            }
        }
        
        return metrics
