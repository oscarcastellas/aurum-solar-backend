"""
B2B Integration Orchestrator
Comprehensive system for managing lead sales to multiple B2B platforms
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lead import Lead, LeadExport
from app.models.b2b_platforms import B2BPlatform, B2BLeadMapping, B2BRevenueTransaction
from app.core.redis import get_redis

logger = structlog.get_logger()

class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    REJECTED = "rejected"
    EXPIRED = "expired"

class DeliveryMethod(Enum):
    JSON_API = "json_api"
    CSV_EMAIL = "csv_email"
    WEBHOOK = "webhook"
    SFTP = "sftp"

@dataclass
class LeadDeliveryRequest:
    lead_id: str
    platform_id: str
    delivery_method: DeliveryMethod
    priority: str
    sla_deadline: datetime
    retry_count: int = 0
    max_retries: int = 3
    custom_fields: Dict[str, Any] = None

@dataclass
class DeliveryResult:
    request_id: str
    platform: str
    status: DeliveryStatus
    delivery_time_ms: int
    external_id: Optional[str]
    revenue: float
    commission: float
    error_message: Optional[str]
    retry_count: int
    delivered_at: Optional[datetime]

class B2BOrchestrator:
    """Main orchestrator for B2B lead delivery and optimization"""
    
    def __init__(self):
        self.platforms: Dict[str, Dict[str, Any]] = {}
        self.delivery_queues: Dict[str, asyncio.Queue] = {}
        self.active_deliveries: Dict[str, DeliveryResult] = {}
        self.redis = None
        self.routing_engine = None
        self.revenue_tracker = None
        self.sla_monitor = None
        
        # Performance metrics
        self.total_deliveries = 0
        self.successful_deliveries = 0
        self.failed_deliveries = 0
        self.total_revenue = 0.0
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize the B2B orchestrator"""
        self.redis = await get_redis()
        await self._load_platform_configurations()
        await self._initialize_delivery_queues()
        await self._start_delivery_workers()
        await self._start_monitoring_workers()
    
    async def _load_platform_configurations(self):
        """Load B2B platform configurations"""
        try:
            db = next(get_db())
            platforms = db.query(B2BPlatform).filter(B2BPlatform.is_active == True).all()
            
            for platform in platforms:
                self.platforms[platform.platform_code] = {
                    "id": str(platform.id),
                    "name": platform.platform_name,
                    "code": platform.platform_code,
                    "delivery_method": platform.delivery_method,
                    "api_endpoint": platform.api_endpoint,
                    "api_key": platform.api_key,
                    "webhook_url": platform.webhook_url,
                    "email_address": platform.email_address,
                    "min_lead_score": platform.min_lead_score or 50,
                    "max_daily_exports": platform.max_daily_exports or 100,
                    "revenue_share": platform.revenue_share or 0.15,
                    "sla_minutes": platform.sla_minutes or 30,
                    "is_accepting_leads": platform.is_accepting_leads or False,
                    "quality_requirements": platform.quality_requirements or {},
                    "field_mapping": platform.field_mapping or {},
                    "rate_limit_per_minute": platform.rate_limit_per_minute or 60,
                    "retry_policy": platform.retry_policy or {"max_retries": 3, "backoff_factor": 2},
                    "health_status": platform.health_status or "unknown",
                    "last_delivery": None,
                    "daily_count": 0,
                    "success_rate": 0.0,
                    "avg_response_time": 0.0
                }
            
            logger.info("Loaded B2B platform configurations", count=len(self.platforms))
            
        except Exception as e:
            logger.error("Error loading platform configurations", error=str(e))
    
    async def _initialize_delivery_queues(self):
        """Initialize delivery queues for each platform"""
        for platform_code in self.platforms.keys():
            self.delivery_queues[platform_code] = asyncio.Queue()
    
    async def _start_delivery_workers(self):
        """Start delivery workers for each platform"""
        for platform_code in self.platforms.keys():
            asyncio.create_task(self._delivery_worker(platform_code))
    
    async def _start_monitoring_workers(self):
        """Start monitoring and health check workers"""
        asyncio.create_task(self._health_check_worker())
        asyncio.create_task(self._sla_monitoring_worker())
        asyncio.create_task(self._revenue_reconciliation_worker())
    
    async def deliver_lead(
        self, 
        lead_id: str, 
        preferred_platforms: List[str] = None,
        priority: str = "normal"
    ) -> DeliveryResult:
        """Deliver a lead to the optimal B2B platform"""
        
        try:
            # Get lead data
            db = next(get_db())
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Select optimal platform
            selected_platform = await self._select_optimal_platform(
                lead, preferred_platforms, priority
            )
            
            if not selected_platform:
                raise ValueError("No suitable platform available for lead delivery")
            
            # Create delivery request
            platform_config = self.platforms[selected_platform]
            delivery_request = LeadDeliveryRequest(
                lead_id=lead_id,
                platform_id=platform_config["id"],
                delivery_method=DeliveryMethod(platform_config["delivery_method"]),
                priority=priority,
                sla_deadline=datetime.utcnow() + timedelta(minutes=platform_config["sla_minutes"]),
                custom_fields=platform_config.get("field_mapping", {})
            )
            
            # Queue for delivery
            await self.delivery_queues[selected_platform].put(delivery_request)
            
            # Track delivery
            request_id = str(uuid.uuid4())
            delivery_result = DeliveryResult(
                request_id=request_id,
                platform=selected_platform,
                status=DeliveryStatus.PENDING,
                delivery_time_ms=0,
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=None,
                retry_count=0,
                delivered_at=None
            )
            
            self.active_deliveries[request_id] = delivery_result
            
            logger.info(
                "Lead queued for delivery",
                lead_id=lead_id,
                platform=selected_platform,
                priority=priority
            )
            
            return delivery_result
            
        except Exception as e:
            logger.error("Error delivering lead", lead_id=lead_id, error=str(e))
            raise
    
    async def _select_optimal_platform(
        self, 
        lead: Lead, 
        preferred_platforms: List[str] = None,
        priority: str = "normal"
    ) -> Optional[str]:
        """Select the optimal platform for lead delivery"""
        
        try:
            # Filter available platforms
            available_platforms = []
            
            for platform_code, config in self.platforms.items():
                if not config["is_accepting_leads"]:
                    continue
                
                if config["daily_count"] >= config["max_daily_exports"]:
                    continue
                
                if lead.lead_score < config["min_lead_score"]:
                    continue
                
                if preferred_platforms and platform_code not in preferred_platforms:
                    continue
                
                available_platforms.append((platform_code, config))
            
            if not available_platforms:
                return None
            
            # Score platforms based on multiple factors
            platform_scores = []
            
            for platform_code, config in available_platforms:
                score = await self._calculate_platform_score(lead, platform_code, config, priority)
                platform_scores.append((platform_code, score))
            
            # Sort by score (highest first)
            platform_scores.sort(key=lambda x: x[1], reverse=True)
            
            return platform_scores[0][0] if platform_scores else None
            
        except Exception as e:
            logger.error("Error selecting optimal platform", error=str(e))
            return None
    
    async def _calculate_platform_score(
        self, 
        lead: Lead, 
        platform_code: str, 
        config: Dict[str, Any],
        priority: str
    ) -> float:
        """Calculate platform score for lead routing"""
        
        try:
            score = 0.0
            
            # Revenue potential (40% weight)
            base_revenue = lead.estimated_value or 0
            revenue_share = config["revenue_share"]
            net_revenue = base_revenue * (1 - revenue_share)
            score += net_revenue * 0.4
            
            # Platform performance (25% weight)
            success_rate = config["success_rate"]
            avg_response_time = config["avg_response_time"]
            performance_score = success_rate * (1 - min(avg_response_time / 30000, 1))  # 30s max
            score += performance_score * 0.25
            
            # Lead quality match (20% weight)
            quality_requirements = config.get("quality_requirements", {})
            quality_score = 1.0
            if "min_score" in quality_requirements:
                quality_score = min(lead.lead_score / quality_requirements["min_score"], 1.0)
            score += quality_score * 0.20
            
            # Capacity utilization (10% weight)
            utilization = config["daily_count"] / config["max_daily_exports"]
            capacity_score = 1 - utilization  # Prefer less utilized platforms
            score += capacity_score * 0.10
            
            # Priority bonus (5% weight)
            if priority == "high":
                score += 0.05
            
            return score
            
        except Exception as e:
            logger.error("Error calculating platform score", platform_code=platform_code, error=str(e))
            return 0.0
    
    async def _delivery_worker(self, platform_code: str):
        """Worker for processing deliveries to a specific platform"""
        
        while True:
            try:
                # Get delivery request from queue
                delivery_request = await asyncio.wait_for(
                    self.delivery_queues[platform_code].get(),
                    timeout=1.0
                )
                
                # Process delivery
                await self._process_delivery(delivery_request, platform_code)
                
            except asyncio.TimeoutError:
                # No requests available, continue
                continue
            except Exception as e:
                logger.error("Error in delivery worker", platform_code=platform_code, error=str(e))
                await asyncio.sleep(5)
    
    async def _process_delivery(self, request: LeadDeliveryRequest, platform_code: str):
        """Process a single delivery request"""
        
        start_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        
        try:
            # Update platform daily count
            self.platforms[platform_code]["daily_count"] += 1
            
            # Get lead data
            db = next(get_db())
            lead = db.query(Lead).filter(Lead.id == request.lead_id).first()
            
            if not lead:
                raise ValueError(f"Lead {request.lead_id} not found")
            
            # Process based on delivery method
            platform_config = self.platforms[platform_code]
            
            if request.delivery_method == DeliveryMethod.JSON_API:
                result = await self._deliver_via_json_api(lead, platform_config, request)
            elif request.delivery_method == DeliveryMethod.CSV_EMAIL:
                result = await self._deliver_via_csv_email(lead, platform_config, request)
            elif request.delivery_method == DeliveryMethod.WEBHOOK:
                result = await self._deliver_via_webhook(lead, platform_config, request)
            else:
                raise ValueError(f"Unsupported delivery method: {request.delivery_method}")
            
            # Update metrics
            delivery_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.delivery_time_ms = int(delivery_time)
            result.delivered_at = datetime.utcnow()
            
            # Update platform performance
            self._update_platform_metrics(platform_code, result)
            
            # Store delivery record
            await self._store_delivery_record(lead, platform_config, result)
            
            # Update active deliveries
            if request_id in self.active_deliveries:
                self.active_deliveries[request_id] = result
            
            # Update counters
            self.total_deliveries += 1
            if result.status == DeliveryStatus.DELIVERED:
                self.successful_deliveries += 1
                self.total_revenue += result.revenue
            else:
                self.failed_deliveries += 1
            
            logger.info(
                "Lead delivery processed",
                lead_id=request.lead_id,
                platform=platform_code,
                status=result.status.value,
                delivery_time_ms=result.delivery_time_ms
            )
            
        except Exception as e:
            logger.error("Error processing delivery", platform_code=platform_code, error=str(e))
            
            # Create failed result
            result = DeliveryResult(
                request_id=request_id,
                platform=platform_code,
                status=DeliveryStatus.FAILED,
                delivery_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=str(e),
                retry_count=request.retry_count,
                delivered_at=None
            )
            
            # Handle retry logic
            if request.retry_count < request.max_retries:
                await self._schedule_retry(request, platform_code)
    
    async def _deliver_via_json_api(
        self, 
        lead: Lead, 
        platform_config: Dict[str, Any], 
        request: LeadDeliveryRequest
    ) -> DeliveryResult:
        """Deliver lead via JSON API"""
        
        import aiohttp
        
        try:
            # Prepare lead data
            lead_data = await self._prepare_lead_data(lead, platform_config)
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {platform_config['api_key']}",
                    "Content-Type": "application/json",
                    "User-Agent": "AurumSolar/1.0"
                }
                
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with session.post(
                    platform_config["api_endpoint"],
                    json=lead_data,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        # Calculate revenue
                        revenue = self._calculate_revenue(lead, platform_config)
                        commission = revenue * platform_config["revenue_share"]
                        
                        return DeliveryResult(
                            request_id=str(uuid.uuid4()),
                            platform=platform_config["code"],
                            status=DeliveryStatus.DELIVERED,
                            delivery_time_ms=0,  # Will be set by caller
                            external_id=response_data.get("lead_id"),
                            revenue=revenue,
                            commission=commission,
                            error_message=None,
                            retry_count=request.retry_count,
                            delivered_at=None
                        )
                    else:
                        return DeliveryResult(
                            request_id=str(uuid.uuid4()),
                            platform=platform_config["code"],
                            status=DeliveryStatus.FAILED,
                            delivery_time_ms=0,
                            external_id=None,
                            revenue=0.0,
                            commission=0.0,
                            error_message=f"API error: {response.status} - {response_data.get('message', 'Unknown error')}",
                            retry_count=request.retry_count,
                            delivered_at=None
                        )
        
        except Exception as e:
            return DeliveryResult(
                request_id=str(uuid.uuid4()),
                platform=platform_config["code"],
                status=DeliveryStatus.FAILED,
                delivery_time_ms=0,
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=str(e),
                retry_count=request.retry_count,
                delivered_at=None
            )
    
    async def _deliver_via_csv_email(
        self, 
        lead: Lead, 
        platform_config: Dict[str, Any], 
        request: LeadDeliveryRequest
    ) -> DeliveryResult:
        """Deliver lead via CSV email"""
        
        try:
            # Prepare CSV data
            csv_data = await self._prepare_csv_data(lead, platform_config)
            
            # Send email (simplified - in production, use proper email service)
            # This would integrate with SendGrid, AWS SES, etc.
            
            revenue = self._calculate_revenue(lead, platform_config)
            commission = revenue * platform_config["revenue_share"]
            
            return DeliveryResult(
                request_id=str(uuid.uuid4()),
                platform=platform_config["code"],
                status=DeliveryStatus.DELIVERED,
                delivery_time_ms=0,
                external_id=None,
                revenue=revenue,
                commission=commission,
                error_message=None,
                retry_count=request.retry_count,
                delivered_at=None
            )
        
        except Exception as e:
            return DeliveryResult(
                request_id=str(uuid.uuid4()),
                platform=platform_config["code"],
                status=DeliveryStatus.FAILED,
                delivery_time_ms=0,
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=str(e),
                retry_count=request.retry_count,
                delivered_at=None
            )
    
    async def _deliver_via_webhook(
        self, 
        lead: Lead, 
        platform_config: Dict[str, Any], 
        request: LeadDeliveryRequest
    ) -> DeliveryResult:
        """Deliver lead via webhook"""
        
        import aiohttp
        
        try:
            # Prepare lead data
            lead_data = await self._prepare_lead_data(lead, platform_config)
            
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
                    "X-Webhook-Signature": self._generate_webhook_signature(webhook_data, platform_config["api_key"])
                }
                
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with session.post(
                    platform_config["webhook_url"],
                    json=webhook_data,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    
                    if response.status in [200, 201, 202]:
                        revenue = self._calculate_revenue(lead, platform_config)
                        commission = revenue * platform_config["revenue_share"]
                        
                        return DeliveryResult(
                            request_id=str(uuid.uuid4()),
                            platform=platform_config["code"],
                            status=DeliveryStatus.DELIVERED,
                            delivery_time_ms=0,
                            external_id=None,
                            revenue=revenue,
                            commission=commission,
                            error_message=None,
                            retry_count=request.retry_count,
                            delivered_at=None
                        )
                    else:
                        return DeliveryResult(
                            request_id=str(uuid.uuid4()),
                            platform=platform_config["code"],
                            status=DeliveryStatus.FAILED,
                            delivery_time_ms=0,
                            external_id=None,
                            revenue=0.0,
                            commission=0.0,
                            error_message=f"Webhook error: {response.status}",
                            retry_count=request.retry_count,
                            delivered_at=None
                        )
        
        except Exception as e:
            return DeliveryResult(
                request_id=str(uuid.uuid4()),
                platform=platform_config["code"],
                status=DeliveryStatus.FAILED,
                delivery_time_ms=0,
                external_id=None,
                revenue=0.0,
                commission=0.0,
                error_message=str(e),
                retry_count=request.retry_count,
                delivered_at=None
            )
    
    async def _prepare_lead_data(self, lead: Lead, platform_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare lead data for delivery"""
        
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
        
        # Apply field mapping if configured
        field_mapping = platform_config.get("field_mapping", {})
        if field_mapping:
            mapped_data = {}
            for platform_field, aurum_field in field_mapping.items():
                mapped_data[platform_field] = self._get_nested_value(lead_data, aurum_field)
            lead_data = mapped_data
        
        return lead_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    async def _prepare_csv_data(self, lead: Lead, platform_config: Dict[str, Any]) -> str:
        """Prepare CSV data for email delivery"""
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
    
    def _calculate_revenue(self, lead: Lead, platform_config: Dict[str, Any]) -> float:
        """Calculate revenue for lead delivery"""
        base_value = lead.estimated_value or 0
        return base_value * (1 - platform_config["revenue_share"])
    
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
    
    def _update_platform_metrics(self, platform_code: str, result: DeliveryResult):
        """Update platform performance metrics"""
        platform = self.platforms[platform_code]
        
        # Update success rate
        total_deliveries = platform["daily_count"]
        if total_deliveries > 0:
            current_success_rate = platform["success_rate"]
            new_success = 1 if result.status == DeliveryStatus.DELIVERED else 0
            platform["success_rate"] = (current_success_rate * (total_deliveries - 1) + new_success) / total_deliveries
        
        # Update average response time
        current_avg_time = platform["avg_response_time"]
        platform["avg_response_time"] = (current_avg_time * (total_deliveries - 1) + result.delivery_time_ms) / total_deliveries
        
        # Update last delivery
        platform["last_delivery"] = datetime.utcnow()
    
    async def _store_delivery_record(self, lead: Lead, platform_config: Dict[str, Any], result: DeliveryResult):
        """Store delivery record in database"""
        try:
            db = next(get_db())
            
            export_record = LeadExport(
                lead_id=lead.id,
                platform_id=platform_config["id"],
                export_status=result.status.value,
                export_priority="normal",
                export_data=await self._prepare_lead_data(lead, platform_config),
                export_format="json",
                export_version="v1",
                price_per_lead=result.revenue,
                commission_rate=platform_config["revenue_share"],
                platform_lead_id=result.external_id,
                response_data={"delivery_time_ms": result.delivery_time_ms},
                exported_at=result.delivered_at,
                commission_earned=result.commission,
                error_message=result.error_message,
                retry_count=result.retry_count
            )
            
            db.add(export_record)
            db.commit()
            
        except Exception as e:
            logger.error("Error storing delivery record", error=str(e))
            db.rollback()
    
    async def _schedule_retry(self, request: LeadDeliveryRequest, platform_code: str):
        """Schedule retry for failed delivery"""
        retry_delay = 2 ** request.retry_count  # Exponential backoff
        request.retry_count += 1
        
        await asyncio.sleep(retry_delay)
        await self.delivery_queues[platform_code].put(request)
        
        logger.info(
            "Scheduled retry for failed delivery",
            lead_id=request.lead_id,
            platform=platform_code,
            retry_count=request.retry_count,
            delay_seconds=retry_delay
        )
    
    async def _health_check_worker(self):
        """Background worker for platform health checks"""
        while True:
            try:
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
            
            import aiohttp
            
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
    
    async def _sla_monitoring_worker(self):
        """Background worker for SLA monitoring"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Check for SLA violations
                for request_id, delivery in self.active_deliveries.items():
                    if delivery.status in [DeliveryStatus.PENDING, DeliveryStatus.DELIVERING]:
                        # Check if SLA deadline has passed
                        # This would need to be implemented with proper SLA tracking
                        pass
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Error in SLA monitoring worker", error=str(e))
                await asyncio.sleep(60)
    
    async def _revenue_reconciliation_worker(self):
        """Background worker for revenue reconciliation"""
        while True:
            try:
                # Reconcile revenue with B2B platforms
                # This would implement revenue reconciliation logic
                pass
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error("Error in revenue reconciliation worker", error=str(e))
                await asyncio.sleep(3600)
    
    async def get_delivery_status(self, request_id: str) -> Optional[DeliveryResult]:
        """Get status of a delivery request"""
        return self.active_deliveries.get(request_id)
    
    async def get_platform_metrics(self) -> Dict[str, Any]:
        """Get platform performance metrics"""
        return {
            "total_deliveries": self.total_deliveries,
            "successful_deliveries": self.successful_deliveries,
            "failed_deliveries": self.failed_deliveries,
            "total_revenue": self.total_revenue,
            "platforms": {
                code: {
                    "daily_count": platform["daily_count"],
                    "max_daily_exports": platform["max_daily_exports"],
                    "success_rate": platform["success_rate"],
                    "avg_response_time": platform["avg_response_time"],
                    "health_status": platform["health_status"],
                    "is_accepting_leads": platform["is_accepting_leads"]
                }
                for code, platform in self.platforms.items()
            }
        }
