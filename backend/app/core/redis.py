"""
Redis connection and management for Aurum Solar
"""

import redis.asyncio as redis
import structlog
from typing import Optional
import asyncio
from contextlib import asynccontextmanager

logger = structlog.get_logger()

# Global Redis connection
_redis_client: Optional[redis.Redis] = None

async def init_redis():
    """Initialize Redis connection"""
    global _redis_client
    
    try:
        # For production, use environment variable
        redis_url = "redis://localhost:6379/0"  # Default for development
        
        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize Redis connection", error=str(e))
        # Create a mock Redis client for development
        _redis_client = None

async def get_redis():
    """Get Redis client instance"""
    global _redis_client
    
    if _redis_client is None:
        await init_redis()
    
    return _redis_client

async def close_redis():
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")

# Cache utilities
async def cache_set(key: str, value: str, ttl: int = 3600):
    """Set cache value with TTL"""
    try:
        client = await get_redis()
        if client:
            await client.setex(key, ttl, value)
            return True
    except Exception as e:
        logger.error("Failed to set cache", key=key, error=str(e))
    return False

async def cache_get(key: str) -> Optional[str]:
    """Get cache value"""
    try:
        client = await get_redis()
        if client:
            return await client.get(key)
    except Exception as e:
        logger.error("Failed to get cache", key=key, error=str(e))
    return None

async def cache_delete(key: str):
    """Delete cache value"""
    try:
        client = await get_redis()
        if client:
            await client.delete(key)
            return True
    except Exception as e:
        logger.error("Failed to delete cache", key=key, error=str(e))
    return False

# Session management
async def set_session(session_id: str, data: dict, ttl: int = 86400):
    """Set session data"""
    import json
    return await cache_set(f"session:{session_id}", json.dumps(data), ttl)

async def get_session(session_id: str) -> Optional[dict]:
    """Get session data"""
    import json
    data = await cache_get(f"session:{session_id}")
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None
    return None

async def delete_session(session_id: str):
    """Delete session data"""
    return await cache_delete(f"session:{session_id}")

# Rate limiting
async def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """Check if rate limit is exceeded"""
    try:
        client = await get_redis()
        if not client:
            return True  # Allow if Redis is not available
        
        current = await client.incr(f"rate_limit:{key}")
        if current == 1:
            await client.expire(f"rate_limit:{key}", window)
        
        return current <= limit
    except Exception as e:
        logger.error("Failed to check rate limit", key=key, error=str(e))
        return True  # Allow if Redis is not available
