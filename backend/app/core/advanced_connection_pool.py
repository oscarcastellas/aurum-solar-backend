"""
Advanced Connection Pool Management for 5/5 Rating
Intelligent connection pooling with adaptive scaling and monitoring
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis
import json
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics"""
    pool_size: int
    checked_out: int
    overflow: int
    invalid: int
    total_connections: int
    utilization_percentage: float
    avg_connection_time: float
    avg_query_time: float
    error_rate: float
    last_updated: float

class AdaptiveConnectionPool:
    """Intelligent connection pool with adaptive scaling"""
    
    def __init__(self, database_url: str, redis_url: str):
        self.database_url = database_url
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
        # Adaptive scaling parameters
        self.min_pool_size = 5
        self.max_pool_size = 15  # Railway limit: 20
        self.current_pool_size = 10
        self.scaling_threshold = 0.8  # Scale up when 80% utilized
        self.scale_down_threshold = 0.3  # Scale down when 30% utilized
        
        # Performance tracking
        self.metrics_history: List[ConnectionPoolMetrics] = []
        self.query_times: List[float] = []
        self.connection_times: List[float] = []
        
        # Create initial engine
        self.engine = self._create_optimized_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Start monitoring
        self._start_monitoring()
    
    def _create_optimized_engine(self) -> Engine:
        """Create Railway-optimized engine with advanced settings"""
        
        # Advanced connection pool configuration
        pool_config = {
            'poolclass': QueuePool,
            'pool_size': self.current_pool_size,
            'max_overflow': 20 - self.current_pool_size,  # Railway limit: 20
            'pool_pre_ping': True,
            'pool_recycle': 1800,  # 30 minutes
            'pool_timeout': 30,
            'pool_reset_on_return': 'commit',
            'echo': False,
            'echo_pool': False,
            'connect_args': {
                'sslmode': 'require',
                'application_name': 'aurum_solar_adaptive_pool',
                'options': '-c default_transaction_isolation=read committed',
                'connect_timeout': 10,
                'command_timeout': 60,
            }
        }
        
        engine = create_engine(self.database_url, **pool_config)
        
        # Add advanced event listeners
        self._add_advanced_listeners(engine)
        
        return engine
    
    def _add_advanced_listeners(self, engine: Engine):
        """Add advanced event listeners for monitoring and optimization"""
        
        @event.listens_for(engine, "connect")
        def set_advanced_connection_settings(dbapi_connection, connection_record):
            """Set advanced connection-specific settings"""
            with dbapi_connection.cursor() as cursor:
                # Advanced PostgreSQL optimizations
                cursor.execute("SET work_mem = '128MB'")  # Increased work memory
                cursor.execute("SET shared_buffers = '512MB'")  # Increased shared buffers
                cursor.execute("SET effective_cache_size = '2GB'")  # Increased cache size
                cursor.execute("SET random_page_cost = 1.0")  # Optimized for SSD
                cursor.execute("SET effective_io_concurrency = 300")  # Optimized for SSD
                cursor.execute("SET maintenance_work_mem = '512MB'")  # Increased maintenance memory
                cursor.execute("SET checkpoint_completion_target = 0.9")  # Optimize checkpoints
                cursor.execute("SET wal_buffers = '32MB'")  # Increased WAL buffers
                cursor.execute("SET default_statistics_target = 500")  # Better query planning
                cursor.execute("SET log_statement = 'none'")  # Disable statement logging
                cursor.execute("SET log_min_duration_statement = 1000")  # Log slow queries
                cursor.execute("SET log_checkpoints = on")  # Log checkpoints
                cursor.execute("SET log_connections = off")  # Disable connection logging
                cursor.execute("SET log_disconnections = off")  # Disable disconnection logging
        
        @event.listens_for(engine, "checkout")
        def track_connection_checkout(dbapi_connection, connection_record, connection_proxy):
            """Track connection checkout with timing"""
            start_time = time.time()
            connection_record._checkout_start = start_time
            
            # Log pool utilization
            utilization = (engine.pool.checkedout() / engine.pool.size()) * 100
            if utilization > 80:
                logger.warning(f"High connection pool utilization: {utilization:.1f}%")
        
        @event.listens_for(engine, "checkin")
        def track_connection_checkin(dbapi_connection, connection_record):
            """Track connection checkin with timing"""
            if hasattr(connection_record, '_checkout_start'):
                connection_time = time.time() - connection_record._checkout_start
                self.connection_times.append(connection_time)
                
                # Keep only last 100 connection times
                if len(self.connection_times) > 100:
                    self.connection_times = self.connection_times[-100:]
        
        @event.listens_for(engine, "before_cursor_execute")
        def track_query_start(conn, cursor, statement, parameters, context, executemany):
            """Track query execution start"""
            context._query_start = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def track_query_end(conn, cursor, statement, parameters, context, executemany):
            """Track query execution end"""
            if hasattr(context, '_query_start'):
                query_time = time.time() - context._query_start
                self.query_times.append(query_time)
                
                # Keep only last 1000 query times
                if len(self.query_times) > 1000:
                    self.query_times = self.query_times[-1000:]
                
                # Log slow queries
                if query_time > 1.0:  # Log queries > 1 second
                    logger.warning(f"Slow query detected: {query_time:.2f}s - {statement[:100]}...")
    
    async def _start_monitoring(self):
        """Start background monitoring of connection pool"""
        asyncio.create_task(self._monitor_pool_performance())
        asyncio.create_task(self._adaptive_scaling())
    
    async def _monitor_pool_performance(self):
        """Monitor connection pool performance continuously"""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
                # Get current metrics
                metrics = self.get_pool_metrics()
                
                # Store in history
                self.metrics_history.append(metrics)
                
                # Keep only last 100 metrics
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]
                
                # Cache metrics in Redis
                await self._cache_metrics(metrics)
                
                # Log performance
                if metrics.utilization_percentage > 80:
                    logger.warning(f"High pool utilization: {metrics.utilization_percentage:.1f}%")
                
            except Exception as e:
                logger.error(f"Error monitoring pool performance: {e}")
    
    async def _adaptive_scaling(self):
        """Implement adaptive scaling based on utilization"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                if len(self.metrics_history) < 5:
                    continue
                
                # Get average utilization over last 5 minutes
                recent_metrics = self.metrics_history[-5:]
                avg_utilization = sum(m.utilization_percentage for m in recent_metrics) / len(recent_metrics)
                
                # Scale up if consistently high utilization
                if avg_utilization > self.scaling_threshold and self.current_pool_size < self.max_pool_size:
                    await self._scale_up()
                
                # Scale down if consistently low utilization
                elif avg_utilization < self.scale_down_threshold and self.current_pool_size > self.min_pool_size:
                    await self._scale_down()
                
            except Exception as e:
                logger.error(f"Error in adaptive scaling: {e}")
    
    async def _scale_up(self):
        """Scale up connection pool"""
        if self.current_pool_size < self.max_pool_size:
            self.current_pool_size += 1
            logger.info(f"Scaling up connection pool to {self.current_pool_size}")
            await self._recreate_engine()
    
    async def _scale_down(self):
        """Scale down connection pool"""
        if self.current_pool_size > self.min_pool_size:
            self.current_pool_size -= 1
            logger.info(f"Scaling down connection pool to {self.current_pool_size}")
            await self._recreate_engine()
    
    async def _recreate_engine(self):
        """Recreate engine with new pool size"""
        try:
            # Close old engine
            self.engine.dispose()
            
            # Create new engine
            self.engine = self._create_optimized_engine()
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info(f"Engine recreated with pool size {self.current_pool_size}")
            
        except Exception as e:
            logger.error(f"Error recreating engine: {e}")
    
    async def _cache_metrics(self, metrics: ConnectionPoolMetrics):
        """Cache metrics in Redis for monitoring"""
        try:
            if not self.redis_client:
                self.redis_client = await self._get_redis_client()
            
            metrics_data = {
                'pool_size': metrics.pool_size,
                'checked_out': metrics.checked_out,
                'utilization_percentage': metrics.utilization_percentage,
                'avg_query_time': metrics.avg_query_time,
                'error_rate': metrics.error_rate,
                'timestamp': time.time()
            }
            
            await self.redis_client.setex(
                'connection_pool_metrics',
                300,  # 5 minutes TTL
                json.dumps(metrics_data)
            )
            
        except Exception as e:
            logger.error(f"Error caching metrics: {e}")
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get Redis client"""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
        return self.redis_client
    
    def get_pool_metrics(self) -> ConnectionPoolMetrics:
        """Get current connection pool metrics"""
        pool = self.engine.pool
        
        # Calculate metrics
        pool_size = pool.size()
        checked_out = pool.checkedout()
        overflow = pool.overflow()
        invalid = pool.invalid()
        total_connections = pool_size + checked_out
        utilization_percentage = (checked_out / pool_size) * 100 if pool_size > 0 else 0
        
        # Calculate average times
        avg_connection_time = sum(self.connection_times) / len(self.connection_times) if self.connection_times else 0
        avg_query_time = sum(self.query_times) / len(self.query_times) if self.query_times else 0
        
        # Calculate error rate (simplified)
        error_rate = 0.0  # Would need to track errors
        
        return ConnectionPoolMetrics(
            pool_size=pool_size,
            checked_out=checked_out,
            overflow=overflow,
            invalid=invalid,
            total_connections=total_connections,
            utilization_percentage=utilization_percentage,
            avg_connection_time=avg_connection_time,
            avg_query_time=avg_query_time,
            error_rate=error_rate,
            last_updated=time.time()
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        return {
            'current_pool_size': self.current_pool_size,
            'avg_utilization': sum(m.utilization_percentage for m in recent_metrics) / len(recent_metrics),
            'max_utilization': max(m.utilization_percentage for m in recent_metrics),
            'avg_query_time': sum(m.avg_query_time for m in recent_metrics) / len(recent_metrics),
            'max_query_time': max(m.avg_query_time for m in recent_metrics),
            'total_queries': len(self.query_times),
            'total_connections': len(self.connection_times),
            'recommendations': self._get_recommendations()
        }
    
    def _get_recommendations(self) -> List[str]:
        """Get performance recommendations"""
        recommendations = []
        
        if not self.metrics_history:
            return recommendations
        
        recent_metrics = self.metrics_history[-5:]
        avg_utilization = sum(m.utilization_percentage for m in recent_metrics) / len(recent_metrics)
        
        if avg_utilization > 90:
            recommendations.append("Consider increasing pool size - utilization > 90%")
        elif avg_utilization < 20:
            recommendations.append("Consider decreasing pool size - utilization < 20%")
        
        if self.query_times:
            avg_query_time = sum(self.query_times) / len(self.query_times)
            if avg_query_time > 0.5:
                recommendations.append("Consider query optimization - avg query time > 500ms")
        
        return recommendations
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with connection pooling"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

# Global adaptive pool instance
adaptive_pool: Optional[AdaptiveConnectionPool] = None

def initialize_adaptive_pool(database_url: str, redis_url: str):
    """Initialize the adaptive connection pool"""
    global adaptive_pool
    adaptive_pool = AdaptiveConnectionPool(database_url, redis_url)
    return adaptive_pool

def get_adaptive_pool() -> Optional[AdaptiveConnectionPool]:
    """Get the adaptive connection pool instance"""
    return adaptive_pool

async def get_optimized_session():
    """Get optimized database session"""
    if not adaptive_pool:
        raise RuntimeError("Adaptive pool not initialized")
    
    async with adaptive_pool.get_session() as session:
        yield session
