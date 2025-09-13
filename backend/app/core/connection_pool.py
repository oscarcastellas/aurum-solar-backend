"""
Database connection pooling and optimization configuration
"""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.dialects.postgresql import psycopg2
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """Manages database connection pooling and optimization"""
    
    # Production connection pool settings
    PRODUCTION_POOL_CONFIG = {
        'poolclass': QueuePool,
        'pool_size': 20,  # Base number of connections
        'max_overflow': 30,  # Additional connections when needed
        'pool_pre_ping': True,  # Validate connections before use
        'pool_recycle': 3600,  # Recycle connections after 1 hour
        'pool_timeout': 30,  # Timeout for getting connection from pool
        'pool_reset_on_return': 'commit',  # Reset connection state
        'echo': False,  # SQL query logging
        'echo_pool': False,  # Connection pool logging
    }
    
    # Development connection pool settings
    DEVELOPMENT_POOL_CONFIG = {
        'poolclass': QueuePool,
        'pool_size': 5,  # Smaller pool for development
        'max_overflow': 10,
        'pool_pre_ping': True,
        'pool_recycle': 1800,  # 30 minutes
        'pool_timeout': 10,
        'pool_reset_on_return': 'commit',
        'echo': True,  # Enable SQL logging in development
        'echo_pool': True,
    }
    
    # Testing connection pool settings
    TESTING_POOL_CONFIG = {
        'poolclass': StaticPool,
        'pool_size': 1,
        'max_overflow': 0,
        'pool_pre_ping': True,
        'pool_recycle': -1,  # Never recycle
        'pool_timeout': 5,
        'pool_reset_on_return': 'commit',
        'echo': False,
        'echo_pool': False,
    }
    
    @classmethod
    def create_optimized_engine(cls, database_url: str, environment: str = "production") -> Engine:
        """Create an optimized database engine with appropriate connection pooling"""
        
        # Select configuration based on environment
        config_map = {
            'production': cls.PRODUCTION_POOL_CONFIG,
            'development': cls.DEVELOPMENT_POOL_CONFIG,
            'testing': cls.TESTING_POOL_CONFIG,
        }
        
        config = config_map.get(environment, cls.PRODUCTION_POOL_CONFIG)
        
        # Create engine with optimized settings
        engine = create_engine(database_url, **config)
        
        # Add event listeners for optimization
        cls._add_optimization_listeners(engine, environment)
        
        logger.info(f"Created optimized database engine for {environment} environment")
        return engine
    
    @classmethod
    def _add_optimization_listeners(cls, engine: Engine, environment: str):
        """Add event listeners for database optimization"""
        
        @event.listens_for(engine, "connect")
        def set_connection_optimizations(dbapi_connection, connection_record):
            """Set connection-level optimizations"""
            if 'postgresql' in str(engine.url):
                with dbapi_connection.cursor() as cursor:
                    # Connection-level optimizations
                    cursor.execute("SET statement_timeout = '30s'")
                    cursor.execute("SET lock_timeout = '10s'")
                    cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
                    
                    # Query optimization
                    cursor.execute("SET random_page_cost = 1.1")
                    cursor.execute("SET effective_cache_size = '4GB'")
                    cursor.execute("SET work_mem = '256MB'")
                    cursor.execute("SET maintenance_work_mem = '1GB'")
                    cursor.execute("SET shared_buffers = '1GB'")
                    
                    # Enable parallel queries
                    cursor.execute("SET max_parallel_workers_per_gather = 4")
                    cursor.execute("SET max_parallel_workers = 8")
                    cursor.execute("SET max_parallel_maintenance_workers = 4")
                    
                    # JIT compilation for complex queries
                    cursor.execute("SET jit = on")
                    cursor.execute("SET jit_above_cost = 100000")
                    cursor.execute("SET jit_optimize_above_cost = 500000")
                    
                    # Connection pooling optimizations
                    cursor.execute("SET tcp_keepalives_idle = 600")
                    cursor.execute("SET tcp_keepalives_interval = 30")
                    cursor.execute("SET tcp_keepalives_count = 3")
                    
                    if environment == 'development':
                        cursor.execute("SET log_statement = 'all'")
                        cursor.execute("SET log_duration = on")
                        cursor.execute("SET log_min_duration_statement = 100")
                    
                    logger.debug("PostgreSQL connection optimizations applied")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout for monitoring"""
            logger.debug("Database connection checked out from pool")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin for monitoring"""
            logger.debug("Database connection checked in to pool")
        
        @event.listens_for(engine, "invalidate")
        def receive_invalidate(dbapi_connection, connection_record, exception):
            """Log connection invalidation for monitoring"""
            logger.warning(f"Database connection invalidated: {exception}")
    
    @classmethod
    def get_pool_status(cls, engine: Engine) -> Dict[str, Any]:
        """Get current connection pool status"""
        pool = engine.pool
        
        return {
            'pool_size': pool.size(),
            'checked_in_connections': pool.checkedin(),
            'checked_out_connections': pool.checkedout(),
            'overflow_connections': pool.overflow(),
            'total_connections': pool.size() + pool.overflow(),
            'pool_class': pool.__class__.__name__,
        }
    
    @classmethod
    def get_connection_metrics(cls, engine: Engine) -> Dict[str, Any]:
        """Get connection pool metrics for monitoring"""
        pool = engine.pool
        
        return {
            'pool_utilization': pool.checkedout() / pool.size() if pool.size() > 0 else 0,
            'overflow_utilization': pool.overflow() / pool._max_overflow if pool._max_overflow > 0 else 0,
            'available_connections': pool.size() - pool.checkedout(),
            'max_connections': pool.size() + pool._max_overflow,
            'pool_efficiency': (pool.checkedin() + pool.checkedout()) / (pool.size() + pool.overflow()) if (pool.size() + pool.overflow()) > 0 else 0,
        }
    
    @classmethod
    def optimize_pool_settings(cls, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest pool setting optimizations based on current metrics"""
        suggestions = {}
        
        pool_utilization = current_metrics.get('pool_utilization', 0)
        overflow_utilization = current_metrics.get('overflow_utilization', 0)
        
        # Suggest pool size adjustments
        if pool_utilization > 0.8:
            suggestions['increase_pool_size'] = True
            suggestions['recommended_pool_size'] = int(current_metrics.get('max_connections', 20) * 1.2)
        elif pool_utilization < 0.3:
            suggestions['decrease_pool_size'] = True
            suggestions['recommended_pool_size'] = max(5, int(current_metrics.get('max_connections', 20) * 0.8))
        
        # Suggest overflow adjustments
        if overflow_utilization > 0.7:
            suggestions['increase_max_overflow'] = True
            suggestions['recommended_max_overflow'] = int(current_metrics.get('max_connections', 20) * 0.5)
        elif overflow_utilization < 0.1:
            suggestions['decrease_max_overflow'] = True
            suggestions['recommended_max_overflow'] = max(5, int(current_metrics.get('max_connections', 20) * 0.2))
        
        # Suggest timeout adjustments
        if pool_utilization > 0.9:
            suggestions['increase_pool_timeout'] = True
            suggestions['recommended_pool_timeout'] = 60
        
        return suggestions
    
    @classmethod
    def get_health_check_query(cls) -> str:
        """Get a simple health check query for connection validation"""
        return "SELECT 1 as health_check"
    
    @classmethod
    def get_performance_queries(cls) -> Dict[str, str]:
        """Get queries for monitoring database performance"""
        return {
            'active_connections': """
                SELECT 
                    count(*) as active_connections,
                    state,
                    application_name
                FROM pg_stat_activity 
                WHERE state = 'active'
                GROUP BY state, application_name
            """,
            'connection_pool_stats': """
                SELECT 
                    datname as database_name,
                    numbackends as current_connections,
                    max_connections,
                    (numbackends::float / max_connections * 100) as connection_utilization
                FROM pg_stat_database 
                WHERE datname = current_database()
            """,
            'slow_queries': """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE mean_time > 1000
                ORDER BY mean_time DESC
                LIMIT 10
            """,
            'index_usage': """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE idx_scan = 0
                ORDER BY tablename, indexname
            """,
            'table_sizes': """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
        }
    
    @classmethod
    def create_read_replica_engine(cls, read_replica_url: str, environment: str = "production") -> Engine:
        """Create a read replica engine for read-only operations"""
        
        config = cls.PRODUCTION_POOL_CONFIG.copy()
        config.update({
            'pool_size': 10,  # Smaller pool for read replicas
            'max_overflow': 15,
            'echo': False,
            'echo_pool': False,
        })
        
        engine = create_engine(read_replica_url, **config)
        
        # Add read-only optimizations
        @event.listens_for(engine, "connect")
        def set_read_replica_optimizations(dbapi_connection, connection_record):
            """Set read replica specific optimizations"""
            if 'postgresql' in str(engine.url):
                with dbapi_connection.cursor() as cursor:
                    # Read replica optimizations
                    cursor.execute("SET default_transaction_read_only = on")
                    cursor.execute("SET statement_timeout = '60s'")
                    cursor.execute("SET work_mem = '512MB'")  # Larger work_mem for read operations
                    cursor.execute("SET effective_cache_size = '8GB'")  # Larger cache for reads
                    
                    logger.debug("Read replica optimizations applied")
        
        logger.info("Created read replica engine")
        return engine
