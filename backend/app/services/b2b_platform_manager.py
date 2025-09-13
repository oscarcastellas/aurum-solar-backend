"""
B2B Platform Management and Onboarding System
Easy onboarding and management of new B2B buyers
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
from app.models.b2b_platforms import B2BPlatform, B2BLeadMapping, B2BRevenueTransaction
from app.core.redis import get_redis

logger = structlog.get_logger()

class PlatformStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    TESTING = "testing"

class OnboardingStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PlatformConfiguration:
    platform_code: str
    platform_name: str
    delivery_method: str
    api_endpoint: str
    api_key: str
    webhook_url: str
    email_address: str
    min_lead_score: int
    max_daily_exports: int
    revenue_share: float
    sla_minutes: int
    quality_requirements: Dict[str, Any]
    field_mapping: Dict[str, str]
    rate_limit_per_minute: int
    retry_policy: Dict[str, Any]

@dataclass
class OnboardingStep:
    step_id: str
    name: str
    description: str
    status: str
    required: bool
    completed_at: Optional[datetime]
    error_message: Optional[str]

@dataclass
class PlatformHealth:
    platform_code: str
    status: str
    last_check: datetime
    response_time_ms: int
    success_rate: float
    error_count: int
    uptime_percentage: float
    issues: List[str]

class B2BPlatformManager:
    """Comprehensive B2B platform management and onboarding system"""
    
    def __init__(self):
        self.redis = None
        self.platform_configs: Dict[str, PlatformConfiguration] = {}
        self.onboarding_templates = {}
        self.health_monitors = {}
        
        # Performance metrics
        self.total_platforms = 0
        self.active_platforms = 0
        self.onboarding_success_rate = 0.0
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize the platform manager"""
        self.redis = await get_redis()
        await self._load_platform_configurations()
        await self._load_onboarding_templates()
        await self._start_health_monitoring()
    
    async def _load_platform_configurations(self):
        """Load existing platform configurations"""
        try:
            db = next(get_db())
            platforms = db.query(B2BPlatform).all()
            
            for platform in platforms:
                config = PlatformConfiguration(
                    platform_code=platform.platform_code,
                    platform_name=platform.platform_name,
                    delivery_method=platform.delivery_method,
                    api_endpoint=platform.api_endpoint or "",
                    api_key=platform.api_key or "",
                    webhook_url=platform.webhook_url or "",
                    email_address=platform.email_address or "",
                    min_lead_score=platform.min_lead_score or 50,
                    max_daily_exports=platform.max_daily_exports or 100,
                    revenue_share=platform.revenue_share or 0.15,
                    sla_minutes=platform.sla_minutes or 30,
                    quality_requirements=platform.quality_requirements or {},
                    field_mapping=platform.field_mapping or {},
                    rate_limit_per_minute=platform.rate_limit_per_minute or 60,
                    retry_policy=platform.retry_policy or {"max_retries": 3, "backoff_factor": 2}
                )
                
                self.platform_configs[platform.platform_code] = config
            
            self.total_platforms = len(platforms)
            self.active_platforms = len([p for p in platforms if p.is_active])
            
            logger.info("Loaded platform configurations", total=self.total_platforms, active=self.active_platforms)
            
        except Exception as e:
            logger.error("Error loading platform configurations", error=str(e))
    
    async def _load_onboarding_templates(self):
        """Load onboarding templates for different platform types"""
        try:
            self.onboarding_templates = {
                "json_api": {
                    "steps": [
                        {
                            "step_id": "api_credentials",
                            "name": "API Credentials Setup",
                            "description": "Configure API endpoint and authentication credentials",
                            "required": True
                        },
                        {
                            "step_id": "field_mapping",
                            "name": "Field Mapping Configuration",
                            "description": "Map lead fields to platform-specific format",
                            "required": True
                        },
                        {
                            "step_id": "test_connection",
                            "name": "Test API Connection",
                            "description": "Verify API connectivity and authentication",
                            "required": True
                        },
                        {
                            "step_id": "test_delivery",
                            "name": "Test Lead Delivery",
                            "description": "Send test lead to verify end-to-end delivery",
                            "required": True
                        },
                        {
                            "step_id": "rate_limits",
                            "name": "Rate Limiting Configuration",
                            "description": "Configure rate limits and retry policies",
                            "required": False
                        }
                    ]
                },
                "csv_email": {
                    "steps": [
                        {
                            "step_id": "email_configuration",
                            "name": "Email Configuration",
                            "description": "Set up email delivery settings and templates",
                            "required": True
                        },
                        {
                            "step_id": "csv_format",
                            "name": "CSV Format Definition",
                            "description": "Define CSV column structure and data format",
                            "required": True
                        },
                        {
                            "step_id": "test_email",
                            "name": "Test Email Delivery",
                            "description": "Send test CSV email to verify delivery",
                            "required": True
                        },
                        {
                            "step_id": "batch_processing",
                            "name": "Batch Processing Setup",
                            "description": "Configure batch size and processing frequency",
                            "required": False
                        }
                    ]
                },
                "webhook": {
                    "steps": [
                        {
                            "step_id": "webhook_url",
                            "name": "Webhook URL Configuration",
                            "description": "Configure webhook endpoint and security settings",
                            "required": True
                        },
                        {
                            "step_id": "webhook_security",
                            "name": "Webhook Security Setup",
                            "description": "Configure webhook signatures and authentication",
                            "required": True
                        },
                        {
                            "step_id": "test_webhook",
                            "name": "Test Webhook Delivery",
                            "description": "Send test webhook to verify delivery",
                            "required": True
                        },
                        {
                            "step_id": "error_handling",
                            "name": "Error Handling Configuration",
                            "description": "Set up webhook error handling and retry logic",
                            "required": False
                        }
                    ]
                }
            }
            
            logger.info("Loaded onboarding templates", count=len(self.onboarding_templates))
            
        except Exception as e:
            logger.error("Error loading onboarding templates", error=str(e))
    
    async def _start_health_monitoring(self):
        """Start health monitoring for all platforms"""
        async def monitor():
            while True:
                try:
                    for platform_code in self.platform_configs.keys():
                        await self._check_platform_health(platform_code)
                    await asyncio.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error("Error in health monitoring", error=str(e))
                    await asyncio.sleep(60)
        
        asyncio.create_task(monitor())
    
    async def create_platform(
        self, 
        platform_data: Dict[str, Any],
        delivery_method: str
    ) -> str:
        """Create a new B2B platform"""
        
        try:
            db = next(get_db())
            
            # Generate platform code
            platform_code = platform_data.get("platform_code") or self._generate_platform_code(platform_data["platform_name"])
            
            # Create platform record
            platform = B2BPlatform(
                platform_code=platform_code,
                platform_name=platform_data["platform_name"],
                delivery_method=delivery_method,
                api_endpoint=platform_data.get("api_endpoint"),
                api_key=platform_data.get("api_key"),
                webhook_url=platform_data.get("webhook_url"),
                email_address=platform_data.get("email_address"),
                min_lead_score=platform_data.get("min_lead_score", 50),
                max_daily_exports=platform_data.get("max_daily_exports", 100),
                revenue_share=platform_data.get("revenue_share", 0.15),
                sla_minutes=platform_data.get("sla_minutes", 30),
                quality_requirements=platform_data.get("quality_requirements", {}),
                field_mapping=platform_data.get("field_mapping", {}),
                rate_limit_per_minute=platform_data.get("rate_limit_per_minute", 60),
                retry_policy=platform_data.get("retry_policy", {"max_retries": 3, "backoff_factor": 2}),
                is_active=False,  # Start as inactive until onboarding is complete
                health_status="unknown",
                created_at=datetime.utcnow()
            )
            
            db.add(platform)
            db.commit()
            
            # Initialize onboarding
            onboarding_id = await self._initialize_onboarding(platform_code, delivery_method)
            
            # Update platform configs
            config = PlatformConfiguration(
                platform_code=platform_code,
                platform_name=platform_data["platform_name"],
                delivery_method=delivery_method,
                api_endpoint=platform_data.get("api_endpoint", ""),
                api_key=platform_data.get("api_key", ""),
                webhook_url=platform_data.get("webhook_url", ""),
                email_address=platform_data.get("email_address", ""),
                min_lead_score=platform_data.get("min_lead_score", 50),
                max_daily_exports=platform_data.get("max_daily_exports", 100),
                revenue_share=platform_data.get("revenue_share", 0.15),
                sla_minutes=platform_data.get("sla_minutes", 30),
                quality_requirements=platform_data.get("quality_requirements", {}),
                field_mapping=platform_data.get("field_mapping", {}),
                rate_limit_per_minute=platform_data.get("rate_limit_per_minute", 60),
                retry_policy=platform_data.get("retry_policy", {"max_retries": 3, "backoff_factor": 2})
            )
            
            self.platform_configs[platform_code] = config
            
            logger.info(
                "Platform created successfully",
                platform_code=platform_code,
                platform_name=platform_data["platform_name"],
                delivery_method=delivery_method,
                onboarding_id=onboarding_id
            )
            
            return platform_code
            
        except Exception as e:
            logger.error("Error creating platform", error=str(e))
            db.rollback()
            raise
    
    def _generate_platform_code(self, platform_name: str) -> str:
        """Generate a unique platform code from platform name"""
        import re
        
        # Convert to lowercase and replace spaces/special chars with underscores
        code = re.sub(r'[^a-z0-9]+', '_', platform_name.lower())
        code = code.strip('_')
        
        # Add random suffix to ensure uniqueness
        suffix = str(uuid.uuid4())[:8]
        return f"{code}_{suffix}"
    
    async def _initialize_onboarding(self, platform_code: str, delivery_method: str) -> str:
        """Initialize onboarding process for a platform"""
        try:
            onboarding_id = str(uuid.uuid4())
            
            # Get onboarding template
            template = self.onboarding_templates.get(delivery_method, {})
            steps = template.get("steps", [])
            
            # Create onboarding steps
            onboarding_data = {
                "onboarding_id": onboarding_id,
                "platform_code": platform_code,
                "delivery_method": delivery_method,
                "status": OnboardingStatus.IN_PROGRESS.value,
                "steps": [
                    {
                        "step_id": step["step_id"],
                        "name": step["name"],
                        "description": step["description"],
                        "status": "pending",
                        "required": step["required"],
                        "completed_at": None,
                        "error_message": None
                    }
                    for step in steps
                ],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store in Redis
            if self.redis:
                await self.redis.set(
                    f"onboarding:{onboarding_id}",
                    json.dumps(onboarding_data),
                    ex=86400 * 30  # 30 days TTL
                )
            
            logger.info("Onboarding initialized", platform_code=platform_code, onboarding_id=onboarding_id)
            
            return onboarding_id
            
        except Exception as e:
            logger.error("Error initializing onboarding", platform_code=platform_code, error=str(e))
            raise
    
    async def get_onboarding_status(self, onboarding_id: str) -> Dict[str, Any]:
        """Get onboarding status and progress"""
        try:
            if not self.redis:
                return {"error": "Redis not available"}
            
            onboarding_data = await self.redis.get(f"onboarding:{onboarding_id}")
            if not onboarding_data:
                return {"error": "Onboarding not found"}
            
            data = json.loads(onboarding_data)
            
            # Calculate progress
            total_steps = len(data["steps"])
            completed_steps = len([s for s in data["steps"] if s["status"] == "completed"])
            progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            
            # Determine overall status
            if completed_steps == total_steps:
                data["status"] = OnboardingStatus.COMPLETED.value
            elif any(s["status"] == "failed" for s in data["steps"]):
                data["status"] = OnboardingStatus.FAILED.value
            elif completed_steps > 0:
                data["status"] = OnboardingStatus.IN_PROGRESS.value
            
            data["progress_percentage"] = progress_percentage
            data["completed_steps"] = completed_steps
            data["total_steps"] = total_steps
            
            return data
            
        except Exception as e:
            logger.error("Error getting onboarding status", onboarding_id=onboarding_id, error=str(e))
            return {"error": str(e)}
    
    async def complete_onboarding_step(
        self, 
        onboarding_id: str, 
        step_id: str, 
        step_data: Dict[str, Any]
    ) -> bool:
        """Complete an onboarding step"""
        
        try:
            if not self.redis:
                return False
            
            # Get onboarding data
            onboarding_data = await self.redis.get(f"onboarding:{onboarding_id}")
            if not onboarding_data:
                return False
            
            data = json.loads(onboarding_data)
            
            # Find and update step
            step_updated = False
            for step in data["steps"]:
                if step["step_id"] == step_id:
                    step["status"] = "completed"
                    step["completed_at"] = datetime.utcnow().isoformat()
                    step["step_data"] = step_data
                    step_updated = True
                    break
            
            if not step_updated:
                return False
            
            # Update overall status
            data["updated_at"] = datetime.utcnow().isoformat()
            
            # Check if all required steps are completed
            required_steps = [s for s in data["steps"] if s["required"]]
            completed_required = [s for s in required_steps if s["status"] == "completed"]
            
            if len(completed_required) == len(required_steps):
                data["status"] = OnboardingStatus.COMPLETED.value
                
                # Activate platform
                await self._activate_platform(data["platform_code"])
            
            # Save updated data
            await self.redis.set(
                f"onboarding:{onboarding_id}",
                json.dumps(data),
                ex=86400 * 30
            )
            
            logger.info(
                "Onboarding step completed",
                onboarding_id=onboarding_id,
                step_id=step_id,
                platform_code=data["platform_code"]
            )
            
            return True
            
        except Exception as e:
            logger.error("Error completing onboarding step", onboarding_id=onboarding_id, step_id=step_id, error=str(e))
            return False
    
    async def _activate_platform(self, platform_code: str):
        """Activate a platform after successful onboarding"""
        try:
            db = next(get_db())
            
            # Update platform status
            platform = db.query(B2BPlatform).filter(B2BPlatform.platform_code == platform_code).first()
            if platform:
                platform.is_active = True
                platform.health_status = "healthy"
                platform.updated_at = datetime.utcnow()
                db.commit()
                
                # Update platform configs
                if platform_code in self.platform_configs:
                    self.platform_configs[platform_code].is_active = True
                
                self.active_platforms += 1
                
                logger.info("Platform activated", platform_code=platform_code)
            
        except Exception as e:
            logger.error("Error activating platform", platform_code=platform_code, error=str(e))
            db.rollback()
    
    async def _check_platform_health(self, platform_code: str):
        """Check health of a specific platform"""
        try:
            config = self.platform_configs.get(platform_code)
            if not config:
                return
            
            start_time = datetime.utcnow()
            health_status = "unknown"
            response_time = 0
            error_count = 0
            issues = []
            
            try:
                if config.delivery_method == "json_api" and config.api_endpoint:
                    # Test API endpoint
                    import aiohttp
                    
                    async with aiohttp.ClientSession() as session:
                        timeout = aiohttp.ClientTimeout(total=10)
                        
                        async with session.get(
                            f"{config.api_endpoint}/health",
                            headers={"Authorization": f"Bearer {config.api_key}"},
                            timeout=timeout
                        ) as response:
                            
                            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                            
                            if response.status == 200:
                                health_status = "healthy"
                            else:
                                health_status = "degraded"
                                issues.append(f"API returned status {response.status}")
                
                elif config.delivery_method == "webhook" and config.webhook_url:
                    # Test webhook endpoint
                    import aiohttp
                    
                    test_payload = {
                        "event": "health_check",
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "aurum_solar"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        timeout = aiohttp.ClientTimeout(total=10)
                        
                        async with session.post(
                            config.webhook_url,
                            json=test_payload,
                            timeout=timeout
                        ) as response:
                            
                            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                            
                            if response.status in [200, 201, 202]:
                                health_status = "healthy"
                            else:
                                health_status = "degraded"
                                issues.append(f"Webhook returned status {response.status}")
                
                else:
                    # For email delivery, just check configuration
                    if config.email_address:
                        health_status = "healthy"
                    else:
                        health_status = "degraded"
                        issues.append("Email address not configured")
            
            except Exception as e:
                health_status = "unhealthy"
                error_count = 1
                issues.append(f"Health check failed: {str(e)}")
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Store health data
            health_data = PlatformHealth(
                platform_code=platform_code,
                status=health_status,
                last_check=datetime.utcnow(),
                response_time_ms=int(response_time),
                success_rate=1.0 if health_status == "healthy" else 0.0,
                error_count=error_count,
                uptime_percentage=100.0 if health_status == "healthy" else 0.0,
                issues=issues
            )
            
            self.health_monitors[platform_code] = health_data
            
            # Update platform health status in database
            db = next(get_db())
            platform = db.query(B2BPlatform).filter(B2BPlatform.platform_code == platform_code).first()
            if platform:
                platform.health_status = health_status
                platform.updated_at = datetime.utcnow()
                db.commit()
            
            logger.debug(
                "Platform health checked",
                platform_code=platform_code,
                status=health_status,
                response_time_ms=response_time,
                issues=issues
            )
            
        except Exception as e:
            logger.error("Error checking platform health", platform_code=platform_code, error=str(e))
    
    async def get_platform_health(self, platform_code: str) -> Optional[PlatformHealth]:
        """Get health status of a platform"""
        return self.health_monitors.get(platform_code)
    
    async def get_all_platform_health(self) -> Dict[str, PlatformHealth]:
        """Get health status of all platforms"""
        return self.health_monitors
    
    async def update_platform_config(
        self, 
        platform_code: str, 
        config_updates: Dict[str, Any]
    ) -> bool:
        """Update platform configuration"""
        
        try:
            db = next(get_db())
            
            # Update database
            platform = db.query(B2BPlatform).filter(B2BPlatform.platform_code == platform_code).first()
            if not platform:
                return False
            
            # Update fields
            for field, value in config_updates.items():
                if hasattr(platform, field):
                    setattr(platform, field, value)
            
            platform.updated_at = datetime.utcnow()
            db.commit()
            
            # Update platform configs
            if platform_code in self.platform_configs:
                config = self.platform_configs[platform_code]
                for field, value in config_updates.items():
                    if hasattr(config, field):
                        setattr(config, field, value)
            
            logger.info("Platform configuration updated", platform_code=platform_code, updates=list(config_updates.keys()))
            
            return True
            
        except Exception as e:
            logger.error("Error updating platform config", platform_code=platform_code, error=str(e))
            db.rollback()
            return False
    
    async def deactivate_platform(self, platform_code: str) -> bool:
        """Deactivate a platform"""
        try:
            db = next(get_db())
            
            # Update database
            platform = db.query(B2BPlatform).filter(B2BPlatform.platform_code == platform_code).first()
            if platform:
                platform.is_active = False
                platform.updated_at = datetime.utcnow()
                db.commit()
                
                # Update platform configs
                if platform_code in self.platform_configs:
                    self.platform_configs[platform_code].is_active = False
                
                self.active_platforms = max(0, self.active_platforms - 1)
                
                logger.info("Platform deactivated", platform_code=platform_code)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error deactivating platform", platform_code=platform_code, error=str(e))
            db.rollback()
            return False
    
    async def get_platform_manager_metrics(self) -> Dict[str, Any]:
        """Get platform manager performance metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "total_platforms": self.total_platforms,
            "active_platforms": self.active_platforms,
            "onboarding_success_rate": self.onboarding_success_rate,
            "uptime_seconds": uptime,
            "health_monitors_active": len(self.health_monitors),
            "onboarding_templates_available": len(self.onboarding_templates)
        }
