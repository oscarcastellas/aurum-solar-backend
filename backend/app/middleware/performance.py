"""
Performance Middleware
Monitors and optimizes API performance with metrics collection
"""

import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and optimization"""
    
    def __init__(self, app, enable_metrics: bool = True, enable_profiling: bool = False):
        super().__init__(app)
        self.enable_metrics = enable_metrics
        self.enable_profiling = enable_profiling
        self.request_count = 0
        self.total_response_time = 0.0
        self.slow_requests = []
        self.error_count = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring"""
        
        # Start timing
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000000)}"
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Increment request count
        self.request_count += 1
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            response_time_ms = process_time * 1000
            
            # Add performance headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            # Update metrics
            if self.enable_metrics:
                await self._update_metrics(request, response, response_time_ms)
            
            # Log slow requests
            if response_time_ms > 1000:  # Slower than 1 second
                self.slow_requests.append({
                    "request_id": request_id,
                    "path": str(request.url.path),
                    "method": request.method,
                    "response_time_ms": response_time_ms,
                    "status_code": response.status_code,
                    "timestamp": time.time()
                })
                
                logger.warning(
                    "Slow request detected",
                    request_id=request_id,
                    path=str(request.url.path),
                    method=request.method,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
            
            # Log request completion
            logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                response_time_ms=round(response_time_ms, 2),
                client_ip=request.client.host if request.client else None
            )
            
            return response
            
        except Exception as e:
            # Handle errors
            process_time = time.time() - start_time
            self.error_count += 1
            
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                error=str(e),
                response_time_ms=round(process_time * 1000, 2)
            )
            
            raise
    
    async def _update_metrics(self, request: Request, response: Response, response_time_ms: float):
        """Update performance metrics"""
        try:
            # Update basic metrics
            self.total_response_time += response_time_ms
            
            # Calculate average response time
            avg_response_time = self.total_response_time / self.request_count
            
            # Log metrics every 100 requests
            if self.request_count % 100 == 0:
                logger.info(
                    "Performance metrics",
                    total_requests=self.request_count,
                    avg_response_time_ms=round(avg_response_time, 2),
                    error_count=self.error_count,
                    error_rate=round((self.error_count / self.request_count) * 100, 2)
                )
            
            # Store metrics in Redis if available
            # This would be implemented with Redis integration
            
        except Exception as e:
            logger.error("Error updating metrics", error=str(e))
    
    def get_metrics(self) -> dict:
        """Get current performance metrics"""
        avg_response_time = self.total_response_time / self.request_count if self.request_count > 0 else 0
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "total_requests": self.request_count,
            "total_response_time_ms": round(self.total_response_time, 2),
            "average_response_time_ms": round(avg_response_time, 2),
            "error_count": self.error_count,
            "error_rate_percent": round(error_rate, 2),
            "slow_requests_count": len(self.slow_requests),
            "recent_slow_requests": self.slow_requests[-10:]  # Last 10 slow requests
        }
