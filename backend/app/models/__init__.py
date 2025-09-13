"""
Database models package
"""

from .lead import Lead, LeadExport, LeadConversation, LeadQualityHistory
from .analytics import RevenueMetrics, PlatformPerformance, NYCMarketIntelligence, UserSession
from .auth import User, UserRole, UserPermission
from .nyc_data import NYCZipCode, NYCIncentive, NYCDemographic, NYCElectricRate
from .b2b_platforms import B2BPlatform, B2BLeadMapping, B2BRevenueTransaction
from .ai_models import AIModel, AIAnalysis, AIConversation, AIInsight

__all__ = [
    # Lead models
    "Lead",
    "LeadExport", 
    "LeadConversation",
    "LeadQualityHistory",
    
    # Analytics models
    "RevenueMetrics",
    "PlatformPerformance", 
    "NYCMarketIntelligence",
    "UserSession",
    
    # Auth models
    "User",
    "UserRole",
    "UserPermission",
    
    # NYC data models
    "NYCZipCode",
    "NYCIncentive", 
    "NYCDemographic",
    "NYCElectricRate",
    
    # B2B models
    "B2BPlatform",
    "B2BLeadMapping",
    "B2BRevenueTransaction",
    
    # AI models
    "AIModel",
    "AIAnalysis",
    "AIConversation", 
    "AIInsight"
]
