"""
Monitoring Service
Comprehensive system monitoring and metrics collection
"""

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()

class SystemMonitor:
    """System monitoring and metrics collection"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.metrics_history = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time_ms": 2000.0
        }
        self.alerts = []
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                    "cpu": {
                        "percent": cpu_percent,
                        "count": cpu_count,
                        "frequency_mhz": cpu_freq.current if cpu_freq else None
                    },
                    "memory": {
                        "total_gb": round(memory.total / (1024**3), 2),
                        "available_gb": round(memory.available / (1024**3), 2),
                        "used_gb": round(memory.used / (1024**3), 2),
                        "percent": memory.percent,
                        "swap_total_gb": round(swap.total / (1024**3), 2),
                        "swap_used_gb": round(swap.used / (1024**3), 2),
                        "swap_percent": swap.percent
                    },
                    "disk": {
                        "total_gb": round(disk.total / (1024**3), 2),
                        "used_gb": round(disk.used / (1024**3), 2),
                        "free_gb": round(disk.free / (1024**3), 2),
                        "percent": round((disk.used / disk.total) * 100, 2),
                        "read_bytes": disk_io.read_bytes if disk_io else 0,
                        "write_bytes": disk_io.write_bytes if disk_io else 0
                    },
                    "network": {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    }
                },
                "process": {
                    "pid": process.pid,
                    "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                    "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                    "cpu_percent": process_cpu,
                    "num_threads": process.num_threads(),
                    "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
                }
            }
            
            # Check for alerts
            self._check_alerts(metrics)
            
            # Store metrics history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:  # Keep last 1000 metrics
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error("Error collecting system metrics", error=str(e))
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for alert conditions"""
        try:
            current_time = datetime.utcnow()
            
            # CPU alert
            cpu_percent = metrics["system"]["cpu"]["percent"]
            if cpu_percent > self.alert_thresholds["cpu_percent"]:
                self._create_alert("high_cpu", f"CPU usage is {cpu_percent}%", current_time)
            
            # Memory alert
            memory_percent = metrics["system"]["memory"]["percent"]
            if memory_percent > self.alert_thresholds["memory_percent"]:
                self._create_alert("high_memory", f"Memory usage is {memory_percent}%", current_time)
            
            # Disk alert
            disk_percent = metrics["system"]["disk"]["percent"]
            if disk_percent > self.alert_thresholds["disk_percent"]:
                self._create_alert("high_disk", f"Disk usage is {disk_percent}%", current_time)
            
        except Exception as e:
            logger.error("Error checking alerts", error=str(e))
    
    def _create_alert(self, alert_type: str, message: str, timestamp: datetime):
        """Create a new alert"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": timestamp.isoformat(),
            "severity": "warning"
        }
        
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        logger.warning("System alert", alert_type=alert_type, message=message)
    
    def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]
    
    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            metrics for metrics in self.metrics_history
            if datetime.fromisoformat(metrics["timestamp"]) > cutoff_time
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            metrics = self.get_system_metrics()
            
            # Determine health status
            health_status = "healthy"
            issues = []
            
            if metrics["system"]["cpu"]["percent"] > self.alert_thresholds["cpu_percent"]:
                health_status = "degraded"
                issues.append("High CPU usage")
            
            if metrics["system"]["memory"]["percent"] > self.alert_thresholds["memory_percent"]:
                health_status = "degraded"
                issues.append("High memory usage")
            
            if metrics["system"]["disk"]["percent"] > self.alert_thresholds["disk_percent"]:
                health_status = "degraded"
                issues.append("High disk usage")
            
            # Check for recent alerts
            recent_alerts = self.get_alerts(hours=1)
            if recent_alerts:
                health_status = "degraded"
                issues.append(f"{len(recent_alerts)} recent alerts")
            
            return {
                "status": health_status,
                "issues": issues,
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error("Error getting health status", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global monitor instance
system_monitor = SystemMonitor()

def setup_monitoring():
    """Setup monitoring system"""
    logger.info("System monitoring initialized")

def get_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    return system_monitor.get_system_metrics()

def get_health_status() -> Dict[str, Any]:
    """Get system health status"""
    return system_monitor.get_health_status()

def get_alerts(hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent alerts"""
    return system_monitor.get_alerts(hours)
