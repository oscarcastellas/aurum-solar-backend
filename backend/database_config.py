"""
Database Configuration for Railway Deployment
Handles PostgreSQL and Redis connections with Railway environment variables
"""

import os
import asyncio
import asyncpg
import redis.asyncio as redis
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import structlog

logger = structlog.get_logger()

# Database Configuration
class DatabaseConfig:
    def __init__(self):
        # PostgreSQL Configuration
        self.postgres_url = self._get_postgres_url()
        self.redis_url = self._get_redis_url()
        
        # SQLAlchemy Configuration
        self.engine = None
        self.SessionLocal = None
        self.Base = declarative_base()
        
        # AsyncPG Configuration
        self.pool = None
        
        # Redis Configuration
        self.redis_client = None
        
    def _get_postgres_url(self) -> str:
        """Get PostgreSQL connection URL from Railway environment variables"""
        # Railway provides these environment variables for PostgreSQL
        if os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")
        
        # Fallback to individual components
        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        user = os.getenv("PGUSER", "postgres")
        password = os.getenv("PGPASSWORD", "")
        database = os.getenv("PGDATABASE", "railway")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _get_redis_url(self) -> str:
        """Get Redis connection URL from Railway environment variables"""
        if os.getenv("REDIS_URL"):
            return os.getenv("REDIS_URL")
        
        # Fallback to individual components
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", "6379")
        password = os.getenv("REDIS_PASSWORD", "")
        
        if password:
            return f"redis://:{password}@{host}:{port}"
        return f"redis://{host}:{port}"
    
    async def init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            return False
    
    async def init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            return False
    
    def init_sqlalchemy(self):
        """Initialize SQLAlchemy engine and session"""
        try:
            self.engine = create_engine(
                self.postgres_url,
                poolclass=NullPool,
                echo=False
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("SQLAlchemy engine initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SQLAlchemy: {e}")
            return False
    
    async def create_tables(self):
        """Create database tables"""
        try:
            # Create all tables
            self.Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    async def test_connections(self):
        """Test all database connections"""
        results = {
            "postgres": False,
            "redis": False,
            "sqlalchemy": False
        }
        
        # Test PostgreSQL
        try:
            if self.pool:
                async with self.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                results["postgres"] = True
                logger.info("PostgreSQL connection test: SUCCESS")
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
        
        # Test Redis
        try:
            if self.redis_client:
                await self.redis_client.ping()
                results["redis"] = True
                logger.info("Redis connection test: SUCCESS")
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
        
        # Test SQLAlchemy
        try:
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute("SELECT 1")
                results["sqlalchemy"] = True
                logger.info("SQLAlchemy connection test: SUCCESS")
        except Exception as e:
            logger.error(f"SQLAlchemy connection test failed: {e}")
        
        return results
    
    async def close_connections(self):
        """Close all database connections"""
        if self.pool:
            await self.pool.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.engine:
            self.engine.dispose()

# Database Models
class LeadModel(Base):
    __tablename__ = "leads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    monthly_bill = Column(Float, nullable=False)
    qualification_score = Column(Float, default=0.0)
    estimated_value = Column(Float, default=0.0)
    status = Column(String, default="new")
    source = Column(String, default="website")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationModel(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, unique=True)
    lead_id = Column(String, nullable=True)
    messages = Column(JSON)
    context = Column(JSON)
    qualification_stage = Column(String, default="initial")
    conversation_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnalyticsModel(Base):
    __tablename__ = "analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_data = Column(JSON)
    period = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Global database instance
db_config = DatabaseConfig()

# Dependency functions
async def get_postgres_connection():
    """Get PostgreSQL connection from pool"""
    if not db_config.pool:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_config.pool

async def get_redis_connection():
    """Get Redis connection"""
    if not db_config.redis_client:
        raise HTTPException(status_code=500, detail="Redis not initialized")
    return db_config.redis_client

def get_db_session():
    """Get SQLAlchemy database session"""
    if not db_config.SessionLocal:
        raise HTTPException(status_code=500, detail="Database not initialized")
    db = db_config.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database on startup
async def init_database():
    """Initialize all database connections"""
    logger.info("Initializing database connections...")
    
    # Initialize PostgreSQL
    postgres_success = await db_config.init_postgres()
    
    # Initialize Redis
    redis_success = await db_config.init_redis()
    
    # Initialize SQLAlchemy
    sqlalchemy_success = db_config.init_sqlalchemy()
    
    # Create tables if PostgreSQL is available
    if postgres_success and sqlalchemy_success:
        await db_config.create_tables()
    
    # Test connections
    test_results = await db_config.test_connections()
    
    logger.info(f"Database initialization complete: {test_results}")
    return test_results

# Cleanup on shutdown
async def close_database():
    """Close all database connections"""
    logger.info("Closing database connections...")
    await db_config.close_connections()
    logger.info("Database connections closed")
