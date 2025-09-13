"""
Rate Limiting Middleware
Implements rate limiting with Redis backend for high performance
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis backend"""
    
    def __init__(self, app, rate_limiter=None):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        
        # Fallback rate limiting configuration
        self.requests_per_minute = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.burst_size = settings.RATE_LIMIT_BURST_SIZE
        
        # Simple in-memory rate limiting as fallback
        self.client_requests = {}  # {client_id: [(timestamp, count)]}
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request"""
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Use Redis-based rate limiting if available, otherwise use fallback
        if self.rate_limiter:
            try:
                is_allowed, remaining, reset_time = await self.rate_limiter.check_rate_limit(
                    client_id, 
                    request.url.path
                )
            except Exception as e:
                logger.error("Rate limiter error, using fallback", error=str(e))
                is_allowed, remaining, reset_time = self._check_fallback_rate_limit(client_id)
        else:
            is_allowed, remaining, reset_time = self._check_fallback_rate_limit(client_id)
        
        if not is_allowed:
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.url.path,
                remaining=remaining,
                reset_time=reset_time
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": reset_time - int(time.time()),
                    "limit_type": "per_minute"
                },
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(time.time()))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Try to get user ID from headers or auth
        user_id = request.headers.get("X-User-ID")
        
        # Use user ID if available, otherwise use IP
        return user_id or client_ip
    
    def _check_fallback_rate_limit(self, client_id: str) -> tuple[bool, int, int]:
        """Fallback rate limiting using in-memory storage"""
        current_time = time.time()
        
        # Clean up old entries periodically
        if current_time - self.last_cleanup > 60:  # Cleanup every minute
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Get or create client request history
        if client_id not in self.client_requests:
            self.client_requests[client_id] = []
        
        requests = self.client_requests[client_id]
        
        # Remove requests older than 1 minute
        cutoff_time = current_time - 60
        requests[:] = [(ts, count) for ts, count in requests if ts > cutoff_time]
        
        # Count current requests in the last minute
        current_count = sum(count for _, count in requests)
        
        # Check if limit exceeded
        is_allowed = current_count < self.requests_per_minute
        remaining = max(0, self.requests_per_minute - current_count - 1)
        reset_time = int(current_time + 60)
        
        # Record this request
        requests.append((current_time, 1))
        
        return is_allowed, remaining, reset_time
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up old client request entries"""
        cutoff_time = current_time - 120  # Remove entries older than 2 minutes
        
        for client_id in list(self.client_requests.keys()):
            requests = self.client_requests[client_id]
            requests[:] = [(ts, count) for ts, count in requests if ts > cutoff_time]
            
            # Remove client if no recent requests
            if not requests:
                del self.client_requests[client_id]
