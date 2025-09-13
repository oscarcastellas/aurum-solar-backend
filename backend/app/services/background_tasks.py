"""
Background Task Manager
Handles async processing for lead delivery, analytics, and maintenance tasks
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import structlog

from app.core.redis import get_redis
from app.services.lead_processor import LeadProcessor
from app.services.b2b_integration import B2BIntegrationService
from app.services.analytics_service import AnalyticsService
from app.websocket.manager import WebSocketManager

logger = structlog.get_logger()

class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class BackgroundTask:
    """Background task definition"""
    id: str
    name: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300

class BackgroundTaskManager:
    """Manages background tasks for async processing"""
    
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.task_queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        self.redis = None
        
        # Task metrics
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = datetime.utcnow()
    
    async def start(self):
        """Start the background task manager"""
        if self.is_running:
            return
        
        self.redis = await get_redis()
        self.is_running = True
        
        # Start worker tasks for each priority level
        for priority in TaskPriority:
            worker = asyncio.create_task(self._worker(priority))
            self.workers.append(worker)
        
        # Start maintenance tasks
        asyncio.create_task(self._maintenance_worker())
        asyncio.create_task(self._metrics_worker())
        
        logger.info("Background task manager started")
    
    async def stop(self):
        """Stop the background task manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Cancel running tasks
        for task in self.tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
        
        logger.info("Background task manager stopped")
    
    async def submit_task(
        self,
        name: str,
        function: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: int = 300
    ) -> str:
        """Submit a task for background processing"""
        
        task_id = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task = BackgroundTask(
            id=task_id,
            name=name,
            function=function,
            args=args or (),
            kwargs=kwargs or {},
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        
        self.tasks[task_id] = task
        await self.task_queues[priority].put(task)
        self.total_tasks += 1
        
        logger.info("Task submitted", task_id=task_id, name=name, priority=priority.value)
        
        return task_id
    
    async def _worker(self, priority: TaskPriority):
        """Worker coroutine for processing tasks"""
        while self.is_running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(
                    self.task_queues[priority].get(),
                    timeout=1.0
                )
                
                await self._execute_task(task)
                
            except asyncio.TimeoutError:
                # No tasks available, continue
                continue
            except Exception as e:
                logger.error("Error in worker", priority=priority.value, error=str(e))
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: BackgroundTask):
        """Execute a background task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        try:
            # Execute task with timeout
            result = await asyncio.wait_for(
                task.function(*task.args, **task.kwargs),
                timeout=task.timeout_seconds
            )
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self.completed_tasks += 1
            
            logger.info(
                "Task completed successfully",
                task_id=task.id,
                name=task.name,
                duration_seconds=(task.completed_at - task.started_at).total_seconds()
            )
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error_message = f"Task timeout after {task.timeout_seconds} seconds"
            self.failed_tasks += 1
            
            logger.error("Task timeout", task_id=task.id, name=task.name)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            self.failed_tasks += 1
            
            logger.error("Task failed", task_id=task.id, name=task.name, error=str(e))
            
            # Retry if retries remaining
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.completed_at = None
                task.error_message = None
                
                # Add back to queue with delay
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
                await self.task_queues[task.priority].put(task)
                
                logger.info("Task retry scheduled", task_id=task.id, retry_count=task.retry_count)
    
    async def _maintenance_worker(self):
        """Background worker for maintenance tasks"""
        while self.is_running:
            try:
                # Clean up old completed tasks
                await self._cleanup_old_tasks()
                
                # Update task metrics
                await self._update_task_metrics()
                
                # Health check
                await self._health_check()
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error("Error in maintenance worker", error=str(e))
                await asyncio.sleep(60)
    
    async def _metrics_worker(self):
        """Background worker for metrics collection"""
        while self.is_running:
            try:
                # Collect and store metrics
                await self._collect_metrics()
                
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error("Error in metrics worker", error=str(e))
                await asyncio.sleep(60)
    
    async def _cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        tasks_to_remove = [
            task_id for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            and task.created_at < cutoff_time
        ]
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            logger.info("Cleaned up old tasks", count=len(tasks_to_remove))
    
    async def _update_task_metrics(self):
        """Update task metrics in Redis"""
        if not self.redis:
            return
        
        metrics = {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "active_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }
        
        await self.redis.hset("background_task_metrics", mapping=metrics)
    
    async def _health_check(self):
        """Perform health check on background tasks"""
        try:
            # Check if workers are running
            active_workers = len([w for w in self.workers if not w.done()])
            
            if active_workers < len(TaskPriority):
                logger.warning("Some background workers are not running", active_workers=active_workers)
            
            # Check for stuck tasks
            stuck_tasks = [
                task for task in self.tasks.values()
                if task.status == TaskStatus.RUNNING
                and task.started_at
                and datetime.utcnow() - task.started_at > timedelta(minutes=30)
            ]
            
            if stuck_tasks:
                logger.warning("Found stuck tasks", count=len(stuck_tasks))
                for task in stuck_tasks:
                    task.status = TaskStatus.FAILED
                    task.error_message = "Task stuck - marked as failed"
                    self.failed_tasks += 1
            
        except Exception as e:
            logger.error("Error in health check", error=str(e))
    
    async def _collect_metrics(self):
        """Collect and store metrics"""
        if not self.redis:
            return
        
        try:
            # Task queue sizes
            queue_sizes = {}
            for priority, queue in self.task_queues.items():
                queue_sizes[f"queue_{priority.value}"] = queue.qsize()
            
            # Task status distribution
            status_counts = {}
            for status in TaskStatus:
                status_counts[f"status_{status.value}"] = len([
                    t for t in self.tasks.values() if t.status == status
                ])
            
            # Combine metrics
            metrics = {
                **queue_sizes,
                **status_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis.hset("background_task_detailed_metrics", mapping=metrics)
            
        except Exception as e:
            logger.error("Error collecting metrics", error=str(e))
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get status of all tasks"""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
    
    def get_task_count(self) -> int:
        """Get total number of tasks"""
        return len(self.tasks)
    
    def is_healthy(self) -> bool:
        """Check if task manager is healthy"""
        return self.is_running and len(self.workers) > 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get task manager metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "is_running": self.is_running,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "active_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "success_rate": (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
            "uptime_seconds": uptime,
            "tasks_per_hour": self.total_tasks / (uptime / 3600) if uptime > 0 else 0,
            "worker_count": len(self.workers)
        }

# Predefined task functions
async def process_lead_task(lead_id: str, conversation_data: dict):
    """Task for processing a lead"""
    processor = LeadProcessor()
    await processor.initialize()
    return await processor.process_lead(lead_id, conversation_data)

async def export_lead_task(lead_id: str, platform_code: str):
    """Task for exporting a lead to B2B platform"""
    integration = B2BIntegrationService()
    await integration.initialize()
    return await integration.export_lead(lead_id, platform_code)

async def update_analytics_task():
    """Task for updating analytics"""
    analytics = AnalyticsService()
    await analytics.initialize()
    return await analytics.get_realtime_metrics()

async def cleanup_old_data_task():
    """Task for cleaning up old data"""
    # Implementation for data cleanup
    pass

async def health_check_task():
    """Task for system health check"""
    # Implementation for health check
    pass
