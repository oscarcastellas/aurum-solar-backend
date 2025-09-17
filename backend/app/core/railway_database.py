"""
Railway-optimized database configuration for Aurum Solar
Optimized for Railway PostgreSQL connection limits and performance
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import redis.asyncio as redis
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Railway PostgreSQL connection limits
RAILWAY_MAX_CONNECTIONS = 20
RAILWAY_RECOMMENDED_POOL_SIZE = 10
RAILWAY_RECOMMENDED_MAX_OVERFLOW = 10

Base = declarative_base()

class RailwayDatabaseConfig:
    """Railway-optimized database configuration"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Railway-specific connection pool settings
        self.pool_config = {
            'poolclass': QueuePool,
            'pool_size': int(os.getenv('DB_POOL_SIZE', RAILWAY_RECOMMENDED_POOL_SIZE)),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', RAILWAY_RECOMMENDED_MAX_OVERFLOW)),
            'pool_pre_ping': True,  # Validate connections before use
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 1800)),  # 30 minutes
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30)),  # 30 seconds
            'pool_reset_on_return': 'commit',  # Reset connection state
            'echo': os.getenv('DB_ECHO', 'false').lower() == 'true',
            'echo_pool': os.getenv('DB_ECHO_POOL', 'false').lower() == 'true',
        }
        
        # Railway PostgreSQL connection arguments
        self.connect_args = {
            'sslmode': 'require',  # Railway requires SSL
            'application_name': 'aurum_solar_backend',
            'options': '-c default_transaction_isolation=read committed',
            'connect_timeout': 30,
            'command_timeout': 60,
        }
        
        # Validate pool configuration
        total_connections = self.pool_config['pool_size'] + self.pool_config['max_overflow']
        if total_connections > RAILWAY_MAX_CONNECTIONS:
            logger.warning(f"Total connections ({total_connections}) exceeds Railway limit ({RAILWAY_MAX_CONNECTIONS})")
            # Adjust to Railway limits
            self.pool_config['pool_size'] = min(self.pool_config['pool_size'], RAILWAY_MAX_CONNECTIONS // 2)
            self.pool_config['max_overflow'] = RAILWAY_MAX_CONNECTIONS - self.pool_config['pool_size']
    
    def create_engine(self) -> Engine:
        """Create Railway-optimized database engine"""
        
        engine = create_engine(
            self.database_url,
            **self.pool_config,
            connect_args=self.connect_args
        )
        
        # Add Railway-specific event listeners
        self._add_railway_listeners(engine)
        
        return engine
    
    def create_async_engine(self):
        """Create Railway-optimized async database engine"""
        
        # Convert to async URL
        async_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        
        return create_async_engine(
            async_url,
            **self.pool_config,
            connect_args=self.connect_args
        )
    
    def _add_railway_listeners(self, engine: Engine):
        """Add Railway-specific event listeners for monitoring and optimization"""
        
        @event.listens_for(engine, "connect")
        def set_connection_settings(dbapi_connection, connection_record):
            """Set connection-specific settings for Railway"""
            with dbapi_connection.cursor() as cursor:
                # Optimize for Railway PostgreSQL
                cursor.execute("SET work_mem = '64MB'")  # Increase work memory
                cursor.execute("SET shared_buffers = '256MB'")  # Increase shared buffers
                cursor.execute("SET effective_cache_size = '1GB'")  # Set effective cache size
                cursor.execute("SET random_page_cost = 1.1")  # Optimize for SSD
                cursor.execute("SET effective_io_concurrency = 200")  # Optimize for SSD
                cursor.execute("SET maintenance_work_mem = '256MB'")  # Increase maintenance memory
                cursor.execute("SET checkpoint_completion_target = 0.9")  # Optimize checkpoints
                cursor.execute("SET wal_buffers = '16MB'")  # Increase WAL buffers
                cursor.execute("SET default_statistics_target = 100")  # Better query planning
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout for monitoring"""
            logger.debug(f"Connection checked out from pool. Pool size: {engine.pool.size()}, Checked out: {engine.pool.checkedout()}")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin for monitoring"""
            logger.debug(f"Connection checked in to pool. Pool size: {engine.pool.size()}, Checked out: {engine.pool.checkedout()}")

class RailwayRedisConfig:
    """Railway-optimized Redis configuration"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        
        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable is required")
    
    async def create_client(self):
        """Create Railway-optimized Redis client"""
        
        # Railway Redis connection settings
        redis_client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        
        return redis_client

# Global instances
_db_config = RailwayDatabaseConfig()
_redis_config = RailwayRedisConfig()

# Create engines
engine = _db_config.create_engine()
async_engine = _db_config.create_async_engine()

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)

# Redis client (lazy initialization)
redis_client: Optional[redis.Redis] = None

def get_db():
    """Get database session with Railway optimization"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def get_async_db():
    """Get async database session with Railway optimization"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_redis():
    """Get Redis client with Railway optimization"""
    global redis_client
    if redis_client is None:
        redis_client = await _redis_config.create_client()
    return redis_client

def get_connection_pool_stats():
    """Get connection pool statistics for monitoring"""
    return {
        'pool_size': engine.pool.size(),
        'checked_out': engine.pool.checkedout(),
        'overflow': engine.pool.overflow(),
        'invalid': engine.pool.invalid(),
        'total_connections': engine.pool.size() + engine.pool.checkedout(),
    }

def validate_railway_config():
    """Validate Railway configuration and connection limits"""
    
    # Check environment variables
    required_vars = ['DATABASE_URL', 'REDIS_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    # Validate connection pool configuration
    pool_stats = get_connection_pool_stats()
    total_connections = pool_stats['total_connections']
    
    if total_connections > RAILWAY_MAX_CONNECTIONS:
        logger.warning(f"Total connections ({total_connections}) exceeds Railway limit ({RAILWAY_MAX_CONNECTIONS})")
        return False
    
    logger.info(f"Railway configuration validated. Pool size: {pool_stats['pool_size']}, Max overflow: {_db_config.pool_config['max_overflow']}")
    return True

# Performance monitoring
class RailwayPerformanceMonitor:
    """Monitor Railway database performance"""
    
    @staticmethod
    def log_slow_queries(threshold_ms: int = 1000):
        """Log queries that exceed threshold"""
        # This would be implemented with query logging middleware
        pass
    
    @staticmethod
    def get_connection_utilization():
        """Get connection pool utilization percentage"""
        stats = get_connection_pool_stats()
        total_capacity = stats['pool_size'] + _db_config.pool_config['max_overflow']
        utilization = (stats['checked_out'] / total_capacity) * 100
        return {
            'utilization_percentage': utilization,
            'checked_out': stats['checked_out'],
            'total_capacity': total_capacity,
            'is_healthy': utilization < 80  # Alert if > 80% utilization
        }
    
    @staticmethod
    def get_query_performance_stats():
        """Get query performance statistics"""
        # This would query pg_stat_statements if enabled
        return {
            'avg_query_time_ms': 0,  # Placeholder
            'slow_queries_count': 0,  # Placeholder
            'total_queries': 0,  # Placeholder
        }

# Initialize configuration validation
if __name__ == "__main__":
    try:
        validate_railway_config()
        print("✅ Railway database configuration validated successfully")
    except Exception as e:
        print(f"❌ Railway database configuration validation failed: {e}")
