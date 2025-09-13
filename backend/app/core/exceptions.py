"""
Custom Exception Classes and Handlers
Centralized exception handling for the application
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

logger = structlog.get_logger()

class AurumSolarException(Exception):
    """Base exception for Aurum Solar application"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class LeadProcessingError(AurumSolarException):
    """Error in lead processing pipeline"""
    pass

class B2BExportError(AurumSolarException):
    """Error in B2B export process"""
    pass

class ConversationError(AurumSolarException):
    """Error in conversation processing"""
    pass

class NYCMarketDataError(AurumSolarException):
    """Error retrieving NYC market data"""
    pass

class AnalyticsError(AurumSolarException):
    """Error in analytics processing"""
    pass

class RateLimitExceededError(AurumSolarException):
    """Rate limit exceeded"""
    pass

class AuthenticationError(AurumSolarException):
    """Authentication error"""
    pass

class AuthorizationError(AurumSolarException):
    """Authorization error"""
    pass

class ValidationError(AurumSolarException):
    """Data validation error"""
    pass

class DatabaseError(AurumSolarException):
    """Database operation error"""
    pass

class ExternalServiceError(AurumSolarException):
    """External service error"""
    pass

def setup_exception_handlers(app: FastAPI):
    """Setup custom exception handlers for the application"""
    
    @app.exception_handler(AurumSolarException)
    async def aurum_solar_exception_handler(request: Request, exc: AurumSolarException):
        """Handle custom Aurum Solar exceptions"""
        logger.error(
            "Aurum Solar exception",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "Aurum Solar Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(LeadProcessingError)
    async def lead_processing_error_handler(request: Request, exc: LeadProcessingError):
        """Handle lead processing errors"""
        logger.error(
            "Lead processing error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Lead Processing Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(B2BExportError)
    async def b2b_export_error_handler(request: Request, exc: B2BExportError):
        """Handle B2B export errors"""
        logger.error(
            "B2B export error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "B2B Export Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(ConversationError)
    async def conversation_error_handler(request: Request, exc: ConversationError):
        """Handle conversation processing errors"""
        logger.error(
            "Conversation error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Conversation Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(NYCMarketDataError)
    async def nyc_market_data_error_handler(request: Request, exc: NYCMarketDataError):
        """Handle NYC market data errors"""
        logger.error(
            "NYC market data error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "NYC Market Data Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(AnalyticsError)
    async def analytics_error_handler(request: Request, exc: AnalyticsError):
        """Handle analytics errors"""
        logger.error(
            "Analytics error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Analytics Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_error_handler(request: Request, exc: RateLimitExceededError):
        """Handle rate limit errors"""
        logger.warning(
            "Rate limit exceeded",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
            client_ip=request.client.host if request.client else None
        )
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate Limit Exceeded",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "retry_after": exc.details.get("retry_after", 60)
            },
            headers={
                "Retry-After": str(exc.details.get("retry_after", 60))
            }
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        """Handle authentication errors"""
        logger.warning(
            "Authentication error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError):
        """Handle authorization errors"""
        logger.warning(
            "Authorization error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=403,
            content={
                "error": "Authorization Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """Handle validation errors"""
        logger.warning(
            "Validation error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        """Handle database errors"""
        logger.error(
            "Database error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Database Error",
                "error_code": exc.error_code,
                "message": "An internal error occurred",
                "details": {"internal_error": True}
            }
        )
    
    @app.exception_handler(ExternalServiceError)
    async def external_service_error_handler(request: Request, exc: ExternalServiceError):
        """Handle external service errors"""
        logger.error(
            "External service error",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=502,
            content={
                "error": "External Service Error",
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(
            "Request validation error",
            errors=exc.errors(),
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "details": {"internal_error": True}
            }
        )