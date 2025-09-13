"""
Integration Health Monitoring and Alerting System
Comprehensive monitoring for B2B integration health and performance
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from app.core.database import get_db
from app.models.b2b_platforms import B2BPlatform, B2BRevenueTransaction, B2BLeadMapping
from app.core.redis import get_redis

logger = structlog.get_logger()

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class HealthMetric:
    metric_name: str
    value: float
    threshold: float
    status: str
    timestamp: datetime
    platform_code: Optional[str] = None

@dataclass
class Alert:
    alert_id: str
    platform_code: str
    alert_type: str
    level: AlertLevel
    status: AlertStatus
    title: str
    description: str
    created_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    metadata: Dict[str, Any]

@dataclass
class IntegrationHealth:
    platform_code: str
    overall_status: str
    health_score: float
    metrics: List[HealthMetric]
    alerts: List[Alert]
    last_updated: datetime

class IntegrationMonitor:
    """Comprehensive integration health monitoring and alerting system"""
    
    def __init__(self):
        self.redis = None
        self.health_metrics: Dict[str, List[HealthMetric]] = {}
        self.active_alerts: Dict[str, List[Alert]] = {}
        self.alert_rules = {}
        self.monitoring_config = {}
        
        # Performance metrics
        self.total_alerts_generated = 0
        self.alerts_resolved = 0
        self.health_checks_performed = 0
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize the integration monitor"""
        self.redis = await get_redis()
        await self._load_alert_rules()
        await self._load_monitoring_config()
        await self._start_monitoring_workers()
    
    async def _load_alert_rules(self):
        """Load alert rules and thresholds"""
        try:
            self.alert_rules = {
                "delivery_failure_rate": {
                    "warning_threshold": 0.05,  # 5%
                    "error_threshold": 0.15,    # 15%
                    "critical_threshold": 0.30,  # 30%
                    "window_minutes": 60
                },
                "response_time": {
                    "warning_threshold": 5000,   # 5 seconds
                    "error_threshold": 15000,    # 15 seconds
                    "critical_threshold": 30000, # 30 seconds
                    "window_minutes": 15
                },
                "revenue_discrepancy": {
                    "warning_threshold": 100.0,  # $100
                    "error_threshold": 500.0,    # $500
                    "critical_threshold": 1000.0, # $1000
                    "window_minutes": 1440       # 24 hours
                },
                "platform_health": {
                    "warning_threshold": 0.95,   # 95% uptime
                    "error_threshold": 0.90,     # 90% uptime
                    "critical_threshold": 0.80,  # 80% uptime
                    "window_minutes": 60
                },
                "capacity_utilization": {
                    "warning_threshold": 0.80,   # 80%
                    "error_threshold": 0.90,     # 90%
                    "critical_threshold": 0.95,  # 95%
                    "window_minutes": 30
                }
            }
            
            logger.info("Loaded alert rules", count=len(self.alert_rules))
            
        except Exception as e:
            logger.error("Error loading alert rules", error=str(e))
    
    async def _load_monitoring_config(self):
        """Load monitoring configuration"""
        try:
            self.monitoring_config = {
                "health_check_interval": 300,      # 5 minutes
                "alert_check_interval": 60,        # 1 minute
                "metrics_retention_days": 30,      # 30 days
                "alert_retention_days": 90,        # 90 days
                "notification_channels": ["email", "slack", "webhook"],
                "escalation_rules": {
                    "critical": {"escalate_after_minutes": 15},
                    "error": {"escalate_after_minutes": 60},
                    "warning": {"escalate_after_minutes": 240}
                }
            }
            
        except Exception as e:
            logger.error("Error loading monitoring config", error=str(e))
    
    async def _start_monitoring_workers(self):
        """Start background monitoring workers"""
        async def health_monitor():
            while True:
                try:
                    await self._perform_health_checks()
                    await asyncio.sleep(self.monitoring_config["health_check_interval"])
                except Exception as e:
                    logger.error("Error in health monitoring", error=str(e))
                    await asyncio.sleep(60)
        
        async def alert_monitor():
            while True:
                try:
                    await self._check_alert_conditions()
                    await asyncio.sleep(self.monitoring_config["alert_check_interval"])
                except Exception as e:
                    logger.error("Error in alert monitoring", error=str(e))
                    await asyncio.sleep(60)
        
        async def metrics_cleanup():
            while True:
                try:
                    await self._cleanup_old_metrics()
                    await asyncio.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error("Error in metrics cleanup", error=str(e))
                    await asyncio.sleep(3600)
        
        asyncio.create_task(health_monitor())
        asyncio.create_task(alert_monitor())
        asyncio.create_task(metrics_cleanup())
    
    async def _perform_health_checks(self):
        """Perform comprehensive health checks on all platforms"""
        try:
            db = next(get_db())
            platforms = db.query(B2BPlatform).filter(B2BPlatform.is_active == True).all()
            
            for platform in platforms:
                await self._check_platform_health(platform)
            
            self.health_checks_performed += 1
            
        except Exception as e:
            logger.error("Error performing health checks", error=str(e))
    
    async def _check_platform_health(self, platform: B2BPlatform):
        """Check health of a specific platform"""
        try:
            platform_code = platform.platform_code
            current_time = datetime.utcnow()
            
            # Get recent delivery metrics
            recent_deliveries = db.query(B2BRevenueTransaction).filter(
                B2BRevenueTransaction.platform_id == platform_code,
                B2BRevenueTransaction.transaction_date >= current_time - timedelta(hours=1)
            ).all()
            
            # Calculate delivery failure rate
            total_deliveries = len(recent_deliveries)
            failed_deliveries = len([d for d in recent_deliveries if d.transaction_status == "failed"])
            failure_rate = failed_deliveries / total_deliveries if total_deliveries > 0 else 0
            
            # Calculate average response time
            avg_response_time = 0
            if recent_deliveries:
                response_times = [d.response_data.get("delivery_time_ms", 0) for d in recent_deliveries if d.response_data]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calculate capacity utilization
            daily_count = await self.redis.get(f"platform_daily_count:{platform_code}") or 0
            daily_count = int(daily_count)
            capacity_utilization = daily_count / platform.max_daily_exports if platform.max_daily_exports > 0 else 0
            
            # Calculate platform health score
            health_score = 1.0
            health_score -= failure_rate * 0.4  # 40% weight for failure rate
            health_score -= min(avg_response_time / 30000, 1) * 0.3  # 30% weight for response time
            health_score -= capacity_utilization * 0.2  # 20% weight for capacity
            health_score -= (1 - (platform.success_rate or 0)) * 0.1  # 10% weight for success rate
            
            health_score = max(0.0, min(1.0, health_score))
            
            # Create health metrics
            metrics = [
                HealthMetric(
                    metric_name="delivery_failure_rate",
                    value=failure_rate,
                    threshold=self.alert_rules["delivery_failure_rate"]["warning_threshold"],
                    status="healthy" if failure_rate < self.alert_rules["delivery_failure_rate"]["warning_threshold"] else "warning",
                    timestamp=current_time,
                    platform_code=platform_code
                ),
                HealthMetric(
                    metric_name="avg_response_time",
                    value=avg_response_time,
                    threshold=self.alert_rules["response_time"]["warning_threshold"],
                    status="healthy" if avg_response_time < self.alert_rules["response_time"]["warning_threshold"] else "warning",
                    timestamp=current_time,
                    platform_code=platform_code
                ),
                HealthMetric(
                    metric_name="capacity_utilization",
                    value=capacity_utilization,
                    threshold=self.alert_rules["capacity_utilization"]["warning_threshold"],
                    status="healthy" if capacity_utilization < self.alert_rules["capacity_utilization"]["warning_threshold"] else "warning",
                    timestamp=current_time,
                    platform_code=platform_code
                ),
                HealthMetric(
                    metric_name="platform_health_score",
                    value=health_score,
                    threshold=0.8,
                    status="healthy" if health_score >= 0.8 else "warning",
                    timestamp=current_time,
                    platform_code=platform_code
                )
            ]
            
            # Store metrics
            if platform_code not in self.health_metrics:
                self.health_metrics[platform_code] = []
            
            self.health_metrics[platform_code].extend(metrics)
            
            # Keep only last 1000 metrics per platform
            if len(self.health_metrics[platform_code]) > 1000:
                self.health_metrics[platform_code] = self.health_metrics[platform_code][-1000:]
            
            # Cache health data
            if self.redis:
                health_data = {
                    "platform_code": platform_code,
                    "overall_status": "healthy" if health_score >= 0.8 else "warning" if health_score >= 0.6 else "critical",
                    "health_score": health_score,
                    "last_updated": current_time.isoformat(),
                    "metrics": [
                        {
                            "name": m.metric_name,
                            "value": m.value,
                            "status": m.status
                        }
                        for m in metrics
                    ]
                }
                
                await self.redis.set(
                    f"health:{platform_code}",
                    json.dumps(health_data),
                    ex=3600  # 1 hour TTL
                )
            
            logger.debug(
                "Platform health checked",
                platform_code=platform_code,
                health_score=health_score,
                failure_rate=failure_rate,
                avg_response_time=avg_response_time,
                capacity_utilization=capacity_utilization
            )
            
        except Exception as e:
            logger.error("Error checking platform health", platform_code=platform.platform_code, error=str(e))
    
    async def _check_alert_conditions(self):
        """Check for alert conditions and generate alerts"""
        try:
            for platform_code, metrics in self.health_metrics.items():
                if not metrics:
                    continue
                
                # Get recent metrics (last hour)
                recent_metrics = [
                    m for m in metrics
                    if m.timestamp > datetime.utcnow() - timedelta(hours=1)
                ]
                
                if not recent_metrics:
                    continue
                
                # Check each metric type
                for metric_name, rules in self.alert_rules.items():
                    metric_values = [m.value for m in recent_metrics if m.metric_name == metric_name]
                    
                    if not metric_values:
                        continue
                    
                    avg_value = sum(metric_values) / len(metric_values)
                    
                    # Check thresholds
                    alert_level = None
                    if avg_value >= rules["critical_threshold"]:
                        alert_level = AlertLevel.CRITICAL
                    elif avg_value >= rules["error_threshold"]:
                        alert_level = AlertLevel.ERROR
                    elif avg_value >= rules["warning_threshold"]:
                        alert_level = AlertLevel.WARNING
                    
                    if alert_level:
                        await self._create_alert(
                            platform_code=platform_code,
                            alert_type=metric_name,
                            level=alert_level,
                            value=avg_value,
                            threshold=rules["warning_threshold"]
                        )
            
        except Exception as e:
            logger.error("Error checking alert conditions", error=str(e))
    
    async def _create_alert(
        self, 
        platform_code: str, 
        alert_type: str, 
        level: AlertLevel,
        value: float,
        threshold: float
    ):
        """Create a new alert"""
        try:
            alert_id = f"{platform_code}_{alert_type}_{int(datetime.utcnow().timestamp())}"
            
            # Check if similar alert already exists
            if platform_code in self.active_alerts:
                existing_alerts = [
                    a for a in self.active_alerts[platform_code]
                    if a.alert_type == alert_type and a.status == AlertStatus.ACTIVE
                ]
                
                if existing_alerts:
                    # Update existing alert instead of creating new one
                    existing_alert = existing_alerts[0]
                    existing_alert.metadata["value"] = value
                    existing_alert.metadata["threshold"] = threshold
                    existing_alert.metadata["updated_at"] = datetime.utcnow().isoformat()
                    return
            
            # Create new alert
            alert = Alert(
                alert_id=alert_id,
                platform_code=platform_code,
                alert_type=alert_type,
                level=level,
                status=AlertStatus.ACTIVE,
                title=f"{alert_type.replace('_', ' ').title()} Alert - {platform_code}",
                description=f"{alert_type.replace('_', ' ').title()} is {value:.2f}, exceeding threshold of {threshold:.2f}",
                created_at=datetime.utcnow(),
                acknowledged_at=None,
                resolved_at=None,
                metadata={
                    "value": value,
                    "threshold": threshold,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Store alert
            if platform_code not in self.active_alerts:
                self.active_alerts[platform_code] = []
            
            self.active_alerts[platform_code].append(alert)
            
            # Store in Redis for persistence
            if self.redis:
                await self.redis.set(
                    f"alert:{alert_id}",
                    json.dumps({
                        "alert_id": alert.alert_id,
                        "platform_code": alert.platform_code,
                        "alert_type": alert.alert_type,
                        "level": alert.level.value,
                        "status": alert.status.value,
                        "title": alert.title,
                        "description": alert.description,
                        "created_at": alert.created_at.isoformat(),
                        "metadata": alert.metadata
                    }),
                    ex=86400 * self.monitoring_config["alert_retention_days"]
                )
            
            # Send notifications
            await self._send_alert_notifications(alert)
            
            self.total_alerts_generated += 1
            
            logger.warning(
                "Alert created",
                alert_id=alert_id,
                platform_code=platform_code,
                alert_type=alert_type,
                level=level.value,
                value=value,
                threshold=threshold
            )
            
        except Exception as e:
            logger.error("Error creating alert", platform_code=platform_code, alert_type=alert_type, error=str(e))
    
    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        try:
            notification_channels = self.monitoring_config.get("notification_channels", [])
            
            for channel in notification_channels:
                if channel == "email":
                    await self._send_email_alert(alert)
                elif channel == "slack":
                    await self._send_slack_alert(alert)
                elif channel == "webhook":
                    await self._send_webhook_alert(alert)
            
        except Exception as e:
            logger.error("Error sending alert notifications", alert_id=alert.alert_id, error=str(e))
    
    async def _send_email_alert(self, alert: Alert):
        """Send email alert (simplified)"""
        # This would integrate with email service
        logger.info("Email alert sent", alert_id=alert.alert_id)
    
    async def _send_slack_alert(self, alert: Alert):
        """Send Slack alert (simplified)"""
        # This would integrate with Slack API
        logger.info("Slack alert sent", alert_id=alert.alert_id)
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send webhook alert (simplified)"""
        # This would send webhook notification
        logger.info("Webhook alert sent", alert_id=alert.alert_id)
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            for platform_code, alerts in self.active_alerts.items():
                for alert in alerts:
                    if alert.alert_id == alert_id:
                        alert.status = AlertStatus.ACKNOWLEDGED
                        alert.acknowledged_at = datetime.utcnow()
                        alert.metadata["acknowledged_by"] = acknowledged_by
                        
                        # Update in Redis
                        if self.redis:
                            await self.redis.set(
                                f"alert:{alert_id}",
                                json.dumps({
                                    "alert_id": alert.alert_id,
                                    "platform_code": alert.platform_code,
                                    "alert_type": alert.alert_type,
                                    "level": alert.level.value,
                                    "status": alert.status.value,
                                    "title": alert.title,
                                    "description": alert.description,
                                    "created_at": alert.created_at.isoformat(),
                                    "acknowledged_at": alert.acknowledged_at.isoformat(),
                                    "metadata": alert.metadata
                                }),
                                ex=86400 * self.monitoring_config["alert_retention_days"]
                            )
                        
                        logger.info("Alert acknowledged", alert_id=alert_id, acknowledged_by=acknowledged_by)
                        return True
            
            return False
            
        except Exception as e:
            logger.error("Error acknowledging alert", alert_id=alert_id, error=str(e))
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert"""
        try:
            for platform_code, alerts in self.active_alerts.items():
                for alert in alerts:
                    if alert.alert_id == alert_id:
                        alert.status = AlertStatus.RESOLVED
                        alert.resolved_at = datetime.utcnow()
                        alert.metadata["resolved_by"] = resolved_by
                        
                        # Update in Redis
                        if self.redis:
                            await self.redis.set(
                                f"alert:{alert_id}",
                                json.dumps({
                                    "alert_id": alert.alert_id,
                                    "platform_code": alert.platform_code,
                                    "alert_type": alert.alert_type,
                                    "level": alert.level.value,
                                    "status": alert.status.value,
                                    "title": alert.title,
                                    "description": alert.description,
                                    "created_at": alert.created_at.isoformat(),
                                    "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                                    "resolved_at": alert.resolved_at.isoformat(),
                                    "metadata": alert.metadata
                                }),
                                ex=86400 * self.monitoring_config["alert_retention_days"]
                            )
                        
                        self.alerts_resolved += 1
                        logger.info("Alert resolved", alert_id=alert_id, resolved_by=resolved_by)
                        return True
            
            return False
            
        except Exception as e:
            logger.error("Error resolving alert", alert_id=alert_id, error=str(e))
            return False
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory issues"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=self.monitoring_config["metrics_retention_days"])
            
            for platform_code, metrics in self.health_metrics.items():
                self.health_metrics[platform_code] = [
                    m for m in metrics if m.timestamp > cutoff_time
                ]
            
            logger.debug("Cleaned up old metrics")
            
        except Exception as e:
            logger.error("Error cleaning up old metrics", error=str(e))
    
    async def get_integration_health(self, platform_code: str = None) -> Dict[str, Any]:
        """Get integration health status"""
        try:
            if platform_code:
                # Get specific platform health
                if platform_code in self.health_metrics:
                    recent_metrics = [
                        m for m in self.health_metrics[platform_code]
                        if m.timestamp > datetime.utcnow() - timedelta(hours=1)
                    ]
                    
                    if recent_metrics:
                        health_score = sum(m.value for m in recent_metrics if m.metric_name == "platform_health_score") / len([m for m in recent_metrics if m.metric_name == "platform_health_score"])
                        overall_status = "healthy" if health_score >= 0.8 else "warning" if health_score >= 0.6 else "critical"
                        
                        return {
                            "platform_code": platform_code,
                            "overall_status": overall_status,
                            "health_score": health_score,
                            "metrics": [
                                {
                                    "name": m.metric_name,
                                    "value": m.value,
                                    "status": m.status,
                                    "timestamp": m.timestamp.isoformat()
                                }
                                for m in recent_metrics
                            ],
                            "alerts": [
                                {
                                    "alert_id": a.alert_id,
                                    "alert_type": a.alert_type,
                                    "level": a.level.value,
                                    "status": a.status.value,
                                    "title": a.title,
                                    "description": a.description,
                                    "created_at": a.created_at.isoformat()
                                }
                                for a in self.active_alerts.get(platform_code, [])
                                if a.status == AlertStatus.ACTIVE
                            ]
                        }
                
                return {"error": "Platform not found or no recent data"}
            
            else:
                # Get all platforms health
                all_platforms_health = {}
                
                for platform_code in self.health_metrics.keys():
                    platform_health = await self.get_integration_health(platform_code)
                    if "error" not in platform_health:
                        all_platforms_health[platform_code] = platform_health
                
                return {
                    "platforms": all_platforms_health,
                    "summary": {
                        "total_platforms": len(all_platforms_health),
                        "healthy_platforms": len([p for p in all_platforms_health.values() if p["overall_status"] == "healthy"]),
                        "warning_platforms": len([p for p in all_platforms_health.values() if p["overall_status"] == "warning"]),
                        "critical_platforms": len([p for p in all_platforms_health.values() if p["overall_status"] == "critical"])
                    }
                }
            
        except Exception as e:
            logger.error("Error getting integration health", error=str(e))
            return {"error": str(e)}
    
    async def get_monitoring_metrics(self) -> Dict[str, Any]:
        """Get monitoring system performance metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "total_alerts_generated": self.total_alerts_generated,
            "alerts_resolved": self.alerts_resolved,
            "health_checks_performed": self.health_checks_performed,
            "uptime_seconds": uptime,
            "active_alerts": sum(len(alerts) for alerts in self.active_alerts.values()),
            "platforms_monitored": len(self.health_metrics),
            "alert_rules_configured": len(self.alert_rules)
        }
