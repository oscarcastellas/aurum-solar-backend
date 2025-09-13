"""
CSRF Protection Middleware
Implements CSRF token validation for state-changing operations
"""

import hmac
import hashlib
import time
import secrets
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for state-changing operations"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health", "/metrics", "/docs", "/redoc", "/openapi.json",
            "/api/v1/auth/login", "/api/v1/auth/register"  # Auth endpoints
        ]
        
        # State-changing HTTP methods that require CSRF protection
        self.protected_methods = ["POST", "PUT", "PATCH", "DELETE"]
        
        # CSRF token expiration time (in seconds)
        self.token_expire_time = settings.CSRF_TOKEN_EXPIRE_MINUTES * 60
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check CSRF token for state-changing operations"""
        
        # Skip CSRF check for excluded paths
        if self._should_skip_csrf(request):
            return await call_next(request)
        
        # Only check state-changing methods
        if request.method not in self.protected_methods:
            return await call_next(request)
        
        # Get CSRF token from header or form data
        csrf_token = self._get_csrf_token(request)
        
        if not csrf_token:
            logger.warning("Missing CSRF token", method=request.method, path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required for this operation"
            )
        
        # Validate CSRF token
        if not self._validate_csrf_token(csrf_token, request):
            logger.warning("Invalid CSRF token", method=request.method, path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )
        
        # Process request
        return await call_next(request)
    
    def _should_skip_csrf(self, request: Request) -> bool:
        """Check if request should skip CSRF validation"""
        path = request.url.path
        
        # Skip CSRF for excluded paths
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        
        # Skip CSRF for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return True
        
        return False
    
    def _get_csrf_token(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request"""
        # Try header first (preferred for AJAX requests)
        csrf_token = request.headers.get("X-CSRF-Token")
        
        if not csrf_token:
            # Try form data for traditional form submissions
            content_type = request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type:
                # This would require parsing the body, which is complex in middleware
                # For now, we'll rely on header-based CSRF tokens
                pass
        
        return csrf_token
    
    def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token"""
        try:
            # Split token into timestamp and signature
            if '.' not in token:
                return False
            
            timestamp_str, signature = token.split('.', 1)
            timestamp = int(timestamp_str)
            
            # Check token expiration
            current_time = int(time.time())
            if current_time - timestamp > self.token_expire_time:
                logger.debug("CSRF token expired", timestamp=timestamp, current_time=current_time)
                return False
            
            # Verify signature
            expected_signature = self._generate_csrf_signature(timestamp_str, request)
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            logger.debug("Invalid CSRF token format", token=token[:20] + "...")
            return False
    
    def _generate_csrf_signature(self, timestamp: str, request: Request) -> str:
        """Generate CSRF token signature"""
        # Create message with timestamp, path, and secret
        message = f"{timestamp}:{request.url.path}:{settings.CSRF_SECRET_KEY}"
        
        # Generate HMAC signature
        signature = hmac.new(
            settings.CSRF_SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature

class CSRFTokenManager:
    """Utility class for generating and managing CSRF tokens"""
    
    @staticmethod
    def generate_csrf_token(request: Request) -> str:
        """Generate a new CSRF token for the request"""
        timestamp = str(int(time.time()))
        
        # Create message with timestamp, path, and secret
        message = f"{timestamp}:{request.url.path}:{settings.CSRF_SECRET_KEY}"
        
        # Generate HMAC signature
        signature = hmac.new(
            settings.CSRF_SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Return timestamp.signature
        return f"{timestamp}.{signature}"
    
    @staticmethod
    def get_csrf_token_from_session(request: Request) -> Optional[str]:
        """Get CSRF token from session (if using session-based auth)"""
        # This would integrate with session management
        # For now, we'll use stateless CSRF tokens
        return CSRFTokenManager.generate_csrf_token(request)
    
    @staticmethod
    def validate_csrf_token(token: str, request: Request) -> bool:
        """Validate a CSRF token"""
        try:
            if '.' not in token:
                return False
            
            timestamp_str, signature = token.split('.', 1)
            timestamp = int(timestamp_str)
            
            # Check token expiration
            current_time = int(time.time())
            if current_time - timestamp > settings.CSRF_TOKEN_EXPIRE_MINUTES * 60:
                return False
            
            # Verify signature
            message = f"{timestamp_str}:{request.url.path}:{settings.CSRF_SECRET_KEY}"
            expected_signature = hmac.new(
                settings.CSRF_SECRET_KEY.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False
