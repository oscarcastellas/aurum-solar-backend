"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import redis.asyncio as redis
from app.core.config import settings

# PostgreSQL setup
engine = create_engine(settings.DATABASE_URL)
async_engine = create_async_engine(settings.DATABASE_URL_ASYNC)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)

Base = declarative_base()

# Redis setup
redis_client = None


async def get_redis():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL)
    return redis_client


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Initialize database"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize Redis
    await get_redis()
