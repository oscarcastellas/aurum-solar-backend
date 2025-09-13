"""
Rate Limiter Service
High-performance rate limiting with Redis backend
"""

import time
from typing import Tuple, Optional
import structlog

logger = structlog.get_logger()

class RateLimiter:
    """Redis-based rate limiter for high performance"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.redis = None
    
    async def initialize(self):
        """Initialize rate limiter with Redis connection"""
        from app.core.redis import get_redis
        self.redis = await get_redis()
    
    async def check_rate_limit(
        self, 
        client_id: str, 
        endpoint: str = "default"
    ) -> Tuple[bool, int, int]:
        """
        Check if client is within rate limits
        
        Returns:
            (is_allowed, remaining_requests, reset_time)
        """
        if not self.redis:
            # If Redis is not available, allow all requests
            return True, self.requests_per_minute, int(time.time()) + 60
        
        try:
            current_time = int(time.time())
            minute_key = f"rate_limit:{client_id}:{endpoint}:{current_time // 60}"
            hour_key = f"rate_limit:{client_id}:{endpoint}:{current_time // 3600}"
            
            # Check minute limit
            minute_count = await self.redis.get(minute_key)
            if minute_count and int(minute_count) >= self.requests_per_minute:
                reset_time = ((current_time // 60) + 1) * 60
                return False, 0, reset_time
            
            # Check hour limit
            hour_count = await self.redis.get(hour_key)
            if hour_count and int(hour_count) >= self.requests_per_hour:
                reset_time = ((current_time // 3600) + 1) * 3600
                return False, 0, reset_time
            
            # Increment counters
            pipe = self.redis.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            await pipe.execute()
            
            # Calculate remaining requests
            remaining_minute = self.requests_per_minute - (int(minute_count) + 1 if minute_count else 1)
            remaining_hour = self.requests_per_hour - (int(hour_count) + 1 if hour_count else 1)
            remaining = min(remaining_minute, remaining_hour)
            
            # Calculate reset time
            minute_reset = ((current_time // 60) + 1) * 60
            hour_reset = ((current_time // 3600) + 1) * 3600
            reset_time = min(minute_reset, hour_reset)
            
            return True, max(0, remaining), reset_time
            
        except Exception as e:
            logger.error("Error checking rate limit", client_id=client_id, error=str(e))
            # On error, allow the request
            return True, self.requests_per_minute, int(time.time()) + 60
    
    async def get_status(self) -> dict:
        """Get rate limiter status"""
        if not self.redis:
            return {"status": "disabled", "reason": "Redis not available"}
        
        try:
            # Get current rate limit stats
            keys = await self.redis.keys("rate_limit:*")
            active_limits = len(keys)
            
            return {
                "status": "active",
                "requests_per_minute": self.requests_per_minute,
                "requests_per_hour": self.requests_per_hour,
                "active_limits": active_limits,
                "redis_connected": True
            }
            
        except Exception as e:
            logger.error("Error getting rate limiter status", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "redis_connected": False
            }
    
    async def reset_all(self):
        """Reset all rate limits"""
        if not self.redis:
            return
        
        try:
            keys = await self.redis.keys("rate_limit:*")
            if keys:
                await self.redis.delete(*keys)
                logger.info("Rate limits reset", keys_deleted=len(keys))
        except Exception as e:
            logger.error("Error resetting rate limits", error=str(e))
    
    async def reset_client(self, client_id: str):
        """Reset rate limits for specific client"""
        if not self.redis:
            return
        
        try:
            keys = await self.redis.keys(f"rate_limit:{client_id}:*")
            if keys:
                await self.redis.delete(*keys)
                logger.info("Client rate limits reset", client_id=client_id, keys_deleted=len(keys))
        except Exception as e:
            logger.error("Error resetting client rate limits", client_id=client_id, error=str(e))
