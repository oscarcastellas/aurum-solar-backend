"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Aurum Solar"
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: os.urandom(32).hex(), description="JWT secret key - MUST be set in production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST_SIZE: int = 20
    
    # CSRF Protection
    CSRF_SECRET_KEY: str = Field(default_factory=lambda: os.urandom(32).hex(), description="CSRF secret key")
    CSRF_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = "postgresql://aurum:password@localhost:5432/aurum_solar"
    DATABASE_URL_ASYNC: str = "postgresql+asyncpg://aurum:password@localhost:5432/aurum_solar"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # External APIs
    OPENAI_API_KEY: str = ""
    SERPAPI_KEY: str = ""
    
    # B2B Integration APIs
    SOLARREVIEWS_API_KEY: str = ""
    MODERNIZE_API_KEY: str = ""
    
    # Stripe (for future payment processing)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    
    # NYC Market Intelligence
    NYC_SOLAR_DATA_API: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
