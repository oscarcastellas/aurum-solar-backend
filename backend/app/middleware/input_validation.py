"""
Input Validation and Sanitization Middleware
Handles input validation, sanitization, and security checks
"""

import re
import html
import json
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from pydantic import ValidationError

logger = structlog.get_logger()

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware"""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_request_size = max_request_size
        
        # Dangerous patterns to detect and block
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'on\w+\s*=',  # Event handlers
            r'<iframe[^>]*>',  # Iframe tags
            r'<object[^>]*>',  # Object tags
            r'<embed[^>]*>',  # Embed tags
            r'<link[^>]*>',  # Link tags
            r'<meta[^>]*>',  # Meta tags
            r'<style[^>]*>.*?</style>',  # Style tags
            r'expression\s*\(',  # CSS expressions
            r'url\s*\(',  # CSS URLs
            r'@import',  # CSS imports
            r'\.\./',  # Directory traversal
            r'\.\.\\',  # Directory traversal (Windows)
            r'<[^>]*>',  # Any HTML tags (basic check)
            r'alert\s*\(',  # JavaScript alert
            r'document\.',  # Document object access
            r'window\.',  # Window object access
            r'eval\s*\(',  # Eval function
            r'exec\s*\(',  # Exec function
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                for pattern in self.dangerous_patterns]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate and sanitize input before processing"""
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            logger.warning("Request too large", size=content_length, max_size=self.max_request_size)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request entity too large"
            )
        
        # Validate and sanitize query parameters
        if request.query_params:
            sanitized_params = {}
            for key, value in request.query_params.items():
                sanitized_key = self._sanitize_string(key)
                sanitized_value = self._sanitize_string(value)
                sanitized_params[sanitized_key] = sanitized_value
                
                # Check for dangerous patterns
                if self._contains_dangerous_content(key) or self._contains_dangerous_content(value):
                    logger.warning("Dangerous content detected in query params", 
                                 key=key, value=value, path=request.url.path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )
            
            # Replace query params with sanitized versions
            request._query_params = sanitized_params
        
        # Validate and sanitize path parameters
        if hasattr(request, 'path_params'):
            sanitized_path_params = {}
            for key, value in request.path_params.items():
                sanitized_key = self._sanitize_string(key)
                sanitized_value = self._sanitize_string(value)
                sanitized_path_params[sanitized_key] = sanitized_value
                
                # Check for dangerous patterns
                if self._contains_dangerous_content(value):
                    logger.warning("Dangerous content detected in path params", 
                                 key=key, value=value, path=request.url.path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )
            
            request.path_params = sanitized_path_params
        
        # For POST/PUT/PATCH requests, validate body
        if request.method in ["POST", "PUT", "PATCH"]:
            # Read and validate request body
            body = await self._get_request_body(request)
            if body:
                # Check for dangerous patterns in raw body
                if self._contains_dangerous_content(body):
                    logger.warning("Dangerous content detected in request body", 
                                 path=request.url.path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected"
                    )
                
                # Try to parse and sanitize JSON
                try:
                    if request.headers.get("content-type", "").startswith("application/json"):
                        json_data = json.loads(body)
                        sanitized_data = self._sanitize_json(json_data)
                        # Store sanitized data for the endpoint to use
                        request.state.sanitized_body = sanitized_data
                except json.JSONDecodeError:
                    # Not JSON, treat as plain text and sanitize
                    sanitized_body = self._sanitize_string(body)
                    request.state.sanitized_body = sanitized_body
        
        # Process request
        return await call_next(request)
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Safely get request body"""
        try:
            body = await request.body()
            return body.decode('utf-8') if body else None
        except Exception as e:
            logger.error("Error reading request body", error=str(e))
            return None
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize a string by escaping HTML and removing dangerous characters"""
        if not isinstance(text, str):
            return str(text)
        
        # Check for dangerous patterns first
        if self._contains_dangerous_content(text):
            # For dangerous content, escape everything
            sanitized = html.escape(text)
        else:
            # For safe content, basic HTML escape
            sanitized = html.escape(text)
        
        # Remove null bytes and control characters (except newline and tab)
        sanitized = ''.join(char for char in sanitized 
                          if ord(char) >= 32 or char in ['\n', '\t'])
        
        # Additional security: Remove or escape dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '(', ')', ';', '\\', '/']
        for char in dangerous_chars:
            if char in ['<', '>', '&']:  # Already escaped by html.escape
                continue
            sanitized = sanitized.replace(char, f'&#x{ord(char):x};')
        
        # Limit length
        if len(sanitized) > 10000:  # 10KB limit per field
            sanitized = sanitized[:10000]
        
        return sanitized
    
    def _sanitize_json(self, data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {self._sanitize_string(key): self._sanitize_json(value) 
                   for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _contains_dangerous_content(self, text: str) -> bool:
        """Check if text contains dangerous patterns"""
        if not isinstance(text, str):
            return False
        
        # Check against compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        
        return False

class ConversationInputValidator:
    """Specialized validator for conversation inputs"""
    
    @staticmethod
    def validate_message(message: str) -> str:
        """Validate and sanitize conversation message"""
        if not isinstance(message, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message must be a string"
            )
        
        # Length validation
        if len(message) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message too long (max 5000 characters)"
            )
        
        if len(message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Sanitize
        sanitized = html.escape(message.strip())
        
        # Remove excessive whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    @staticmethod
    def validate_session_id(session_id: str) -> str:
        """Validate session ID format"""
        if not isinstance(session_id, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID must be a string"
            )
        
        # Allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format"
            )
        
        if len(session_id) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID too long"
            )
        
        return session_id
    
    @staticmethod
    def validate_zip_code(zip_code: str) -> str:
        """Validate NYC zip code"""
        if not isinstance(zip_code, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zip code must be a string"
            )
        
        # NYC zip codes are 5 digits
        if not re.match(r'^\d{5}$', zip_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid zip code format"
            )
        
        # Basic NYC zip code range validation
        zip_num = int(zip_code)
        if not (10001 <= zip_num <= 11697):  # NYC zip code range
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zip code must be within NYC area"
            )
        
        return zip_code
    
    @staticmethod
    def validate_bill_amount(bill_amount: float) -> float:
        """Validate monthly electric bill amount"""
        if not isinstance(bill_amount, (int, float)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill amount must be a number"
            )
        
        if bill_amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill amount cannot be negative"
            )
        
        if bill_amount > 10000:  # Reasonable upper limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bill amount too high"
            )
        
        return float(bill_amount)
