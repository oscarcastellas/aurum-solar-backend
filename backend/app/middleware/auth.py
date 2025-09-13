"""
Authentication Middleware
Handles JWT token validation and user authentication
"""

import jwt
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for JWT token validation"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        self.jwt_secret = settings.SECRET_KEY
        self.jwt_algorithm = settings.ALGORITHM
        
        # Validate security configuration
        if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == "your-secret-key-change-in-production":
            logger.critical("CRITICAL SECURITY: Default JWT secret detected in production!")
            raise ValueError("Must set SECRET_KEY environment variable in production")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate authentication for protected endpoints"""
        
        # Skip auth for excluded paths
        if self._should_skip_auth(request):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning("Missing authorization header", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authorization scheme")
        except ValueError:
            logger.warning("Invalid authorization header format", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate token
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Add user info to request state
            request.state.user_id = payload.get("user_id")
            request.state.user_email = payload.get("email")
            request.state.user_role = payload.get("role", "user")
            
            logger.debug("User authenticated", user_id=request.state.user_id, path=request.url.path)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            logger.warning("Invalid token", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Process request
        return await call_next(request)
    
    def _should_skip_auth(self, request: Request) -> bool:
        """Check if request should skip authentication"""
        path = request.url.path
        
        # Skip auth for excluded paths
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        
        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return True
        
        return False
