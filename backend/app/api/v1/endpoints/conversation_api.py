"""
REST API endpoints for AI conversation system
Provides HTTP endpoints for conversation management and analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.conversation_agent import SolarConversationAgent
from app.services.nyc_market_service import NYCMarketService
from app.services.lead_scoring_service import LeadScoringService
from app.services.b2b_export_service import B2BExportService
from app.services.ab_testing_service import ABTestingService
from app.services.performance_monitoring import PerformanceMonitoringService
from app.models.lead import Lead, LeadConversation


router = APIRouter()


# Pydantic models for request/response
class ConversationRequest(BaseModel):
    message: str
    session_id: str
    lead_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        # Validate on assignment
        validate_assignment = True
        
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            # Validate and sanitize message
            if 'message' in v:
                from app.middleware.input_validation import ConversationInputValidator
                v['message'] = ConversationInputValidator.validate_message(v['message'])
            
            # Validate session_id
            if 'session_id' in v:
                from app.middleware.input_validation import ConversationInputValidator
                v['session_id'] = ConversationInputValidator.validate_session_id(v['session_id'])
        
        return v


class ConversationResponse(BaseModel):
    response: str
    session_id: str
    lead_id: Optional[str] = None
    stage: str
    lead_score: int
    quality_tier: str
    next_questions: List[str]
    nyc_insights: Dict[str, Any]
    urgency_created: bool
    timestamp: str


class NYCMarketRequest(BaseModel):
    zip_code: str


class NYCMarketResponse(BaseModel):
    zip_code: str
    market_data: Dict[str, Any]
    urgency_factors: Dict[str, Any]
    neighborhood_insights: Dict[str, Any]
    competition_analysis: Dict[str, Any]
    timestamp: str


class SavingsCalculationRequest(BaseModel):
    zip_code: str
    monthly_bill: float
    system_size_kw: Optional[float] = None


class SavingsCalculationResponse(BaseModel):
    zip_code: str
    monthly_bill: float
    savings_data: Dict[str, Any]
    timestamp: str


class LeadStatusResponse(BaseModel):
    session_id: str
    lead_id: Optional[str]
    conversation_stage: str
    lead_score: int
    quality_tier: str
    message_count: int
    connected_at: str
    last_message_at: Optional[str]
    timestamp: str


class PerformanceDashboardResponse(BaseModel):
    period_days: int
    generated_at: str
    kpis: Dict[str, float]
    performance_score: float
    alerts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    conversation_metrics: Dict[str, Any]
    lead_quality_metrics: Dict[str, Any]
    revenue_metrics: Dict[str, Any]
    ai_metrics: Dict[str, Any]
    b2b_metrics: Dict[str, Any]


@router.post("/conversation", response_model=ConversationResponse)
async def process_conversation(
    request: ConversationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process a conversation message and return AI response"""
    
    try:
        # Initialize conversation agent
        conversation_agent = SolarConversationAgent(db)
        
        # Process the message
        response = await conversation_agent.process_message(
            request.message,
            request.session_id,
            request.lead_id
        )
        
        # Add background tasks for analytics
        background_tasks.add_task(update_conversation_analytics, request.session_id, response)
        
        return ConversationResponse(
            response=response["response"],
            session_id=response["session_id"],
            lead_id=response.get("lead_id"),
            stage=response.get("stage", "welcome"),
            lead_score=response.get("lead_score", 0),
            quality_tier=response.get("quality_tier", "unqualified"),
            next_questions=response.get("next_questions", []),
            nyc_insights=response.get("nyc_insights", {}),
            urgency_created=response.get("urgency_created", False),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing conversation: {str(e)}")


@router.post("/nyc-market-data", response_model=NYCMarketResponse)
async def get_nyc_market_data(
    request: NYCMarketRequest,
    db: Session = Depends(get_db)
):
    """Get comprehensive NYC market data for a zip code"""
    
    try:
        nyc_service = NYCMarketService(db)
        
        # Get all NYC market data
        market_data = await nyc_service.get_zip_code_data(request.zip_code)
        urgency_factors = await nyc_service.get_urgency_factors(request.zip_code)
        neighborhood_insights = await nyc_service.get_neighborhood_insights(request.zip_code)
        competition_analysis = await nyc_service.get_competition_analysis(request.zip_code)
        
        if not market_data:
            raise HTTPException(status_code=404, detail=f"No market data found for zip code {request.zip_code}")
        
        return NYCMarketResponse(
            zip_code=request.zip_code,
            market_data=market_data,
            urgency_factors=urgency_factors,
            neighborhood_insights=neighborhood_insights,
            competition_analysis=competition_analysis,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving NYC market data: {str(e)}")


@router.post("/calculate-savings", response_model=SavingsCalculationResponse)
async def calculate_savings_potential(
    request: SavingsCalculationRequest,
    db: Session = Depends(get_db)
):
    """Calculate personalized savings potential for a lead"""
    
    try:
        nyc_service = NYCMarketService(db)
        
        # Calculate savings potential
        savings_data = await nyc_service.calculate_savings_potential(
            request.zip_code,
            request.monthly_bill,
            request.system_size_kw
        )
        
        if not savings_data:
            raise HTTPException(status_code=404, detail=f"Unable to calculate savings for zip code {request.zip_code}")
        
        return SavingsCalculationResponse(
            zip_code=request.zip_code,
            monthly_bill=request.monthly_bill,
            savings_data=savings_data,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating savings: {str(e)}")


@router.get("/lead-status/{session_id}", response_model=LeadStatusResponse)
async def get_lead_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get current lead status and conversation progress"""
    
    try:
        # Get conversation data
        conversations = db.query(LeadConversation).filter(
            LeadConversation.session_id == session_id
        ).order_by(LeadConversation.created_at.desc()).all()
        
        if not conversations:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get lead data if available
        lead_id = conversations[0].lead_id
        lead = None
        if lead_id:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        # Calculate conversation metrics
        message_count = len(conversations)
        connected_at = conversations[-1].created_at if conversations else datetime.utcnow()
        last_message_at = conversations[0].created_at if conversations else None
        
        return LeadStatusResponse(
            session_id=session_id,
            lead_id=str(lead_id) if lead_id else None,
            conversation_stage=lead.lead_quality if lead else "welcome",
            lead_score=lead.lead_score if lead else 0,
            quality_tier=lead.lead_quality if lead else "unqualified",
            message_count=message_count,
            connected_at=connected_at.isoformat(),
            last_message_at=last_message_at.isoformat() if last_message_at else None,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving lead status: {str(e)}")


@router.get("/performance-dashboard", response_model=PerformanceDashboardResponse)
async def get_performance_dashboard(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get comprehensive performance dashboard data"""
    
    try:
        performance_service = PerformanceMonitoringService(db)
        
        # Get comprehensive dashboard data
        dashboard_data = await performance_service.get_comprehensive_dashboard(days)
        
        if not dashboard_data:
            raise HTTPException(status_code=500, detail="Unable to generate performance dashboard")
        
        return PerformanceDashboardResponse(**dashboard_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating performance dashboard: {str(e)}")


@router.get("/conversation-analytics")
async def get_conversation_analytics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get conversation analytics and metrics"""
    
    try:
        performance_service = PerformanceMonitoringService(db)
        
        # Get conversation metrics
        conversation_metrics = await performance_service.get_conversation_metrics(days)
        lead_quality_metrics = await performance_service.get_lead_quality_metrics(days)
        ai_metrics = await performance_service.get_ai_performance_metrics(days)
        
        return {
            "period_days": days,
            "conversation_metrics": conversation_metrics,
            "lead_quality_metrics": lead_quality_metrics,
            "ai_metrics": ai_metrics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation analytics: {str(e)}")


@router.get("/revenue-analytics")
async def get_revenue_analytics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get revenue analytics and B2B export metrics"""
    
    try:
        performance_service = PerformanceMonitoringService(db)
        b2b_service = B2BExportService(db)
        
        # Get revenue metrics
        revenue_metrics = await performance_service.get_revenue_metrics(days)
        b2b_metrics = await performance_service.get_b2b_export_metrics(days)
        b2b_analytics = await b2b_service.get_revenue_analytics(days)
        
        return {
            "period_days": days,
            "revenue_metrics": revenue_metrics,
            "b2b_metrics": b2b_metrics,
            "b2b_analytics": b2b_analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving revenue analytics: {str(e)}")


@router.get("/ab-tests")
async def get_ab_tests(
    db: Session = Depends(get_db)
):
    """Get active A/B tests and their performance"""
    
    try:
        ab_testing_service = ABTestingService(db)
        
        # Get active tests
        active_tests = await ab_testing_service.get_active_tests()
        
        # Get performance for each test
        test_performances = {}
        for test in active_tests:
            test_id = test["test_id"]
            performance = await ab_testing_service.get_test_performance(test_id)
            test_performances[test_id] = performance
        
        return {
            "active_tests": active_tests,
            "test_performances": test_performances,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving A/B tests: {str(e)}")


@router.post("/ab-tests/{test_id}/assign-variant")
async def assign_ab_test_variant(
    test_id: str,
    session_id: str,
    lead_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Assign A/B test variant to a session"""
    
    try:
        ab_testing_service = ABTestingService(db)
        
        # Assign variant
        variant = await ab_testing_service.assign_variant(test_id, session_id, lead_id)
        
        if not variant:
            raise HTTPException(status_code=404, detail="Test not found or user not eligible")
        
        return {
            "test_id": test_id,
            "session_id": session_id,
            "variant": {
                "variant_id": variant.variant_id,
                "name": variant.name,
                "description": variant.description,
                "is_control": variant.is_control,
                "configuration": variant.configuration
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning A/B test variant: {str(e)}")


@router.post("/ab-tests/{test_id}/record-conversion")
async def record_ab_test_conversion(
    test_id: str,
    variant_id: str,
    session_id: str,
    lead_id: str,
    conversion_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Record a conversion for A/B test"""
    
    try:
        ab_testing_service = ABTestingService(db)
        
        # Record conversion
        await ab_testing_service.record_conversion(
            test_id, variant_id, session_id, lead_id, conversion_data
        )
        
        return {
            "test_id": test_id,
            "variant_id": variant_id,
            "session_id": session_id,
            "lead_id": lead_id,
            "conversion_recorded": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording A/B test conversion: {str(e)}")


@router.get("/objection-responses/{objection_type}")
async def get_objection_responses(
    objection_type: str,
    zip_code: str,
    db: Session = Depends(get_db)
):
    """Get NYC-specific objection responses"""
    
    try:
        nyc_service = NYCMarketService(db)
        
        # Get objection responses
        responses = await nyc_service.get_objection_responses(objection_type, zip_code)
        
        if not responses:
            raise HTTPException(status_code=404, detail=f"No responses found for objection type: {objection_type}")
        
        return {
            "objection_type": objection_type,
            "zip_code": zip_code,
            "responses": responses,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving objection responses: {str(e)}")


@router.get("/nyc-neighborhoods")
async def get_nyc_neighborhoods(
    borough: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get NYC neighborhood data for personalization"""
    
    try:
        nyc_service = NYCMarketService(db)
        
        # Get neighborhood data (this would query the database in production)
        neighborhoods = {
            "10001": {"neighborhood": "Chelsea", "borough": "Manhattan", "avg_bill": 380},
            "11201": {"neighborhood": "DUMBO", "borough": "Brooklyn", "avg_bill": 320},
            "11375": {"neighborhood": "Forest Hills", "borough": "Queens", "avg_bill": 220},
            "10451": {"neighborhood": "South Bronx", "borough": "Bronx", "avg_bill": 180},
            "10301": {"neighborhood": "St. George", "borough": "Staten Island", "avg_bill": 200}
        }
        
        # Filter by borough if specified
        if borough:
            neighborhoods = {
                zip_code: data for zip_code, data in neighborhoods.items()
                if data["borough"].lower() == borough.lower()
            }
        
        return {
            "borough": borough,
            "neighborhoods": neighborhoods,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving NYC neighborhoods: {str(e)}")


# Background task functions
async def update_conversation_analytics(session_id: str, response: Dict[str, Any]):
    """Update conversation analytics in background"""
    
    try:
        # This would update analytics in the background
        # For now, just log the response
        print(f"Analytics update for session {session_id}: {response.get('stage')}")
        
    except Exception as e:
        print(f"Error updating conversation analytics: {e}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for conversation service"""
    
    return {
        "status": "healthy",
        "service": "conversation_api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
