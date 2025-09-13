"""
AI-powered conversational agent for NYC solar lead generation
Core system for lead qualification and B2B revenue optimization
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import openai
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.lead import Lead, LeadConversation, LeadQualityHistory
from app.models.ai_models import AIModel, AIAnalysis, AIConversation
from app.models.nyc_data import NYCZipCode, NYCIncentive
from app.services.nyc_market_service import NYCMarketService
from app.services.lead_scoring_service import LeadScoringService
from app.services.b2b_export_service import B2BExportService
from app.services.solar_calculation_engine import SolarCalculationEngine
from app.services.conversation_intelligence_engine import ConversationIntelligenceEngine
from app.services.conversation_ab_testing import ConversationABTesting
from app.services.nyc_solar_expertise import NYCSolarExpertiseEngine


class ConversationStage(Enum):
    """Conversation flow stages"""
    WELCOME = "welcome"
    INTEREST_ASSESSMENT = "interest_assessment"
    LOCATION_QUALIFICATION = "location_qualification"
    BILL_DISCOVERY = "bill_discovery"
    HOMEOWNER_VERIFICATION = "homeowner_verification"
    ROOF_ASSESSMENT = "roof_assessment"
    SOLAR_CALCULATION = "solar_calculation"
    URGENCY_CREATION = "urgency_creation"
    OBJECTION_RESOLUTION = "objection_resolution"
    QUALIFICATION_COMPLETION = "qualification_completion"
    FOLLOW_UP = "follow_up"


class LeadQualityTier(Enum):
    """B2B lead quality tiers with pricing"""
    PREMIUM = "premium"  # $200+ B2B value
    STANDARD = "standard"  # $125 B2B value
    BASIC = "basic"  # $75 B2B value
    UNQUALIFIED = "unqualified"  # No B2B value


@dataclass
class ConversationContext:
    """Conversation state and context"""
    session_id: str
    lead_id: Optional[str] = None
    current_stage: ConversationStage = ConversationStage.WELCOME
    stage_progress: float = 0.0
    lead_score: int = 0
    quality_tier: LeadQualityTier = LeadQualityTier.UNQUALIFIED
    nyc_data: Optional[Dict] = None
    conversation_data: Dict = None
    qualification_factors: Dict = None
    objections_handled: List[str] = None
    urgency_created: bool = False
    homeowner_verified: bool = False
    bill_amount: Optional[float] = None
    zip_code: Optional[str] = None
    borough: Optional[str] = None
    timeline: Optional[str] = None
    roof_type: Optional[str] = None
    roof_size: Optional[float] = None
    shading_factor: Optional[float] = None
    roof_orientation: Optional[str] = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.conversation_data is None:
            self.conversation_data = {}
        if self.qualification_factors is None:
            self.qualification_factors = {}
        if self.objections_handled is None:
            self.objections_handled = []
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()


class SolarConversationAgent:
    """AI-powered conversational agent for NYC solar lead generation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.nyc_service = NYCMarketService(db)
        self.lead_scoring = LeadScoringService(db)
        self.b2b_export = B2BExportService(db)
        self.solar_calculator = SolarCalculationEngine(db)
        self.conversation_intelligence = ConversationIntelligenceEngine(db)
        self.ab_testing = ConversationABTesting(db)
        self.nyc_expertise = NYCSolarExpertiseEngine()
        
        # NYC market data cache
        self.nyc_data_cache = {}
        
        # Conversation templates and prompts
        self.conversation_templates = self._load_conversation_templates()
        self.nyc_neighborhood_data = self._load_nyc_neighborhood_data()
    
    async def process_message(
        self, 
        message: str, 
        session_id: str, 
        lead_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process incoming message and generate response"""
        
        try:
            # Get or create conversation context
            context = await self._get_conversation_context(session_id, lead_id)
            
            # Update context with new message
            context.last_activity = datetime.utcnow()
            
            # Analyze message for intent and entities
            message_analysis = await self._analyze_message(message, context)
            
            # Update conversation context based on analysis
            context = await self._update_context_from_analysis(context, message_analysis)
            
            # Generate response based on current stage and context
            response = await self._generate_response(context, message, message_analysis)
            
            # Store conversation in database
            await self._store_conversation(context, message, response, message_analysis)
            
            # Store solar recommendation in database if generated
            if response.get("solar_recommendation"):
                await self._store_solar_recommendation(context, response["solar_recommendation"])
            
            # Update lead scoring if we have a lead
            if context.lead_id:
                await self._update_lead_scoring(context)
            
            # Check if lead is ready for B2B export
            if context.quality_tier != LeadQualityTier.UNQUALIFIED:
                await self._prepare_b2b_export(context)
            
            return {
                "response": response["content"],
                "stage": context.current_stage.value,
                "lead_score": context.lead_score,
                "quality_tier": context.quality_tier.value,
                "next_questions": response.get("next_questions", []),
                "nyc_insights": response.get("nyc_insights", {}),
                "urgency_created": context.urgency_created,
                "session_id": session_id,
                "lead_id": context.lead_id
            }
            
        except Exception as e:
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact us directly at (555) 123-4567.",
                "error": str(e),
                "session_id": session_id
            }
    
    async def _get_conversation_context(self, session_id: str, lead_id: Optional[str]) -> ConversationContext:
        """Get or create conversation context"""
        
        # Try to get existing context from Redis (implement Redis caching)
        # For now, create new context
        context = ConversationContext(session_id=session_id, lead_id=lead_id)
        
        # If we have a lead_id, load existing lead data
        if lead_id:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                context.lead_id = str(lead.id)
                context.zip_code = lead.zip_code
                context.borough = lead.borough
                context.bill_amount = lead.monthly_electric_bill
                context.lead_score = lead.lead_score
                
                # Load NYC data if we have zip code
                if lead.zip_code:
                    context.nyc_data = await self.nyc_service.get_zip_code_data(lead.zip_code)
        
        return context
    
    async def _analyze_message(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze message for intent, entities, and sentiment"""
        
        analysis_prompt = f"""
        Analyze this message from a potential solar customer in NYC:
        
        Message: "{message}"
        Current Stage: {context.current_stage.value}
        Lead Score: {context.lead_score}
        
        Extract:
        1. Intent (interest, objection, question, qualification_signal, urgency_signal)
        2. Entities (zip_code, bill_amount, timeline, homeowner_status, roof_type, roof_size, shading, roof_orientation, roof_age)
        3. Sentiment (-1 to 1)
        4. Objection type (cost, roof, aesthetics, process, timeline, other)
        5. Qualification signals (high_intent_phrases, budget_indicators, timeline_urgency)
        6. Urgency indicators (deadline_mentions, immediate_need, competitive_pressure)
        7. Roof characteristics (type, size, condition, shading, orientation, age)
        
        Return as JSON.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing customer conversations for solar lead qualification. Return only valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Add confidence scoring
            analysis["confidence"] = 0.8  # Placeholder - implement actual confidence scoring
            
            return analysis
            
        except Exception as e:
            return {
                "intent": "unknown",
                "entities": {},
                "sentiment": 0.0,
                "objection_type": None,
                "qualification_signals": [],
                "urgency_indicators": [],
                "confidence": 0.5,
                "error": str(e)
            }
    
    async def _update_context_from_analysis(
        self, 
        context: ConversationContext, 
        analysis: Dict[str, Any]
    ) -> ConversationContext:
        """Update conversation context based on message analysis"""
        
        # Extract entities
        entities = analysis.get("entities", {})
        
        if "zip_code" in entities:
            context.zip_code = entities["zip_code"]
            # Load NYC data for this zip code
            context.nyc_data = await self.nyc_service.get_zip_code_data(entities["zip_code"])
            if context.nyc_data:
                context.borough = context.nyc_data.get("borough")
            
            # Load NYC expertise data
            nyc_expertise = self.nyc_expertise.get_zip_code_expertise(entities["zip_code"])
            if nyc_expertise:
                context.conversation_data.update({
                    "building_type": nyc_expertise.building_type.value,
                    "historic_district": nyc_expertise.historic_district.value if nyc_expertise.historic_district else None,
                    "co_op_approval_required": nyc_expertise.co_op_approval_required,
                    "permit_timeline": nyc_expertise.installation_timeline,
                    "roof_challenges": nyc_expertise.roof_challenges,
                    "regulatory_notes": nyc_expertise.regulatory_notes
                })
        
        if "bill_amount" in entities:
            context.bill_amount = float(entities["bill_amount"])
        
        if "timeline" in entities:
            context.timeline = entities["timeline"]
        
        if "homeowner_status" in entities:
            context.homeowner_verified = entities["homeowner_status"] in ["owner", "homeowner", "yes"]
        
        if "roof_type" in entities:
            context.roof_type = entities["roof_type"]
        
        if "roof_size" in entities:
            context.roof_size = float(entities["roof_size"])
        
        if "shading" in entities:
            context.shading_factor = float(entities["shading"])
        
        if "roof_orientation" in entities:
            context.roof_orientation = entities["roof_orientation"]
        
        # Update qualification factors
        qualification_signals = analysis.get("qualification_signals", [])
        for signal in qualification_signals:
            context.qualification_factors[signal] = True
        
        # Track objections
        if analysis.get("objection_type"):
            context.objections_handled.append(analysis["objection_type"])
        
        # Check for urgency creation
        urgency_indicators = analysis.get("urgency_indicators", [])
        if urgency_indicators:
            context.urgency_created = True
        
        # Update stage based on progress
        context = await self._update_conversation_stage(context, analysis)
        
        return context
    
    async def _update_conversation_stage(
        self, 
        context: ConversationContext, 
        analysis: Dict[str, Any]
    ) -> ConversationContext:
        """Update conversation stage based on progress and analysis"""
        
        current_stage = context.current_stage
        intent = analysis.get("intent", "")
        entities = analysis.get("entities", {})
        
        # Stage progression logic
        if current_stage == ConversationStage.WELCOME:
            if intent == "interest" or "solar" in analysis.get("qualification_signals", []):
                context.current_stage = ConversationStage.INTEREST_ASSESSMENT
                context.stage_progress = 0.2
        
        elif current_stage == ConversationStage.INTEREST_ASSESSMENT:
            if context.zip_code or "zip_code" in entities:
                context.current_stage = ConversationStage.LOCATION_QUALIFICATION
                context.stage_progress = 0.4
        
        elif current_stage == ConversationStage.LOCATION_QUALIFICATION:
            if context.bill_amount or "bill_amount" in entities:
                context.current_stage = ConversationStage.BILL_DISCOVERY
                context.stage_progress = 0.6
        
        elif current_stage == ConversationStage.BILL_DISCOVERY:
            if context.homeowner_verified or "homeowner_status" in entities:
                context.current_stage = ConversationStage.HOMEOWNER_VERIFICATION
                context.stage_progress = 0.8
        
        elif current_stage == ConversationStage.HOMEOWNER_VERIFICATION:
            if context.roof_type or "roof" in entities:
                context.current_stage = ConversationStage.ROOF_ASSESSMENT
                context.stage_progress = 0.7
            elif context.urgency_created or "urgency" in intent:
                context.current_stage = ConversationStage.URGENCY_CREATION
                context.stage_progress = 0.9
        
        elif current_stage == ConversationStage.ROOF_ASSESSMENT:
            if (context.bill_amount and context.zip_code and 
                (context.roof_type or context.roof_size)):
                context.current_stage = ConversationStage.SOLAR_CALCULATION
                context.stage_progress = 0.8
        
        elif current_stage == ConversationStage.SOLAR_CALCULATION:
            if context.urgency_created or "urgency" in intent:
                context.current_stage = ConversationStage.URGENCY_CREATION
                context.stage_progress = 0.9
        
        # Check if ready for qualification completion
        if (context.bill_amount and context.homeowner_verified and 
            context.zip_code and context.lead_score >= 70):
            context.current_stage = ConversationStage.QUALIFICATION_COMPLETION
            context.stage_progress = 1.0
        
        return context
    
    async def _generate_response(
        self, 
        context: ConversationContext, 
        message: str, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI response based on context and analysis"""
        
        # Get stage-specific template
        template = self.conversation_templates.get(context.current_stage.value, {})
        
        # Build context for AI
        ai_context = {
            "stage": context.current_stage.value,
            "lead_score": context.lead_score,
            "nyc_data": context.nyc_data,
            "bill_amount": context.bill_amount,
            "zip_code": context.zip_code,
            "borough": context.borough,
            "objections_handled": context.objections_handled,
            "urgency_created": context.urgency_created,
            "homeowner_verified": context.homeowner_verified,
            "message_analysis": analysis
        }
        
        # Generate response using AI
        response_prompt = self._build_response_prompt(template, ai_context, message)
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": template.get("system_prompt", "")},
                    {"role": "user", "content": response_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            ai_response = response.choices[0].message.content
            
            # Add intelligent solar recommendations based on conversation stage
            solar_recommendation = None
            technical_response = ""
            nyc_expertise_response = ""
            
            # Generate solar recommendations when we have sufficient data
            if (context.bill_amount and context.zip_code and 
                context.current_stage in [ConversationStage.SOLAR_CALCULATION, 
                                        ConversationStage.URGENCY_CREATION,
                                        ConversationStage.OBJECTION_RESOLUTION]):
                try:
                    solar_recommendation = await self.solar_calculator.calculate_solar_recommendation(
                        monthly_bill=context.bill_amount,
                        zip_code=context.zip_code,
                        borough=context.borough,
                        roof_type=context.roof_type,
                        roof_size=context.roof_size,
                        shading_factor=context.shading_factor,
                        home_type=context.conversation_data.get("home_type")
                    )
                    
                    # Generate technical response with solar data
                    technical_response = self.solar_calculator.generate_conversation_response(
                        solar_recommendation, 
                        context.conversation_data.get("customer_name", "there"),
                        context.bill_amount,
                        context.borough
                    )
                    
                except Exception as e:
                    print(f"Error calculating solar recommendation: {e}")
            
            # Add NYC-specific expertise based on context
            if context.zip_code:
                # Generate NYC-specific advice
                nyc_expertise_response = self.nyc_expertise.generate_nyc_specific_advice(
                    context.zip_code,
                    context.conversation_data.get("building_type"),
                    context.conversation_data.get("concerns", [])
                )
                
                # Add urgency creation if appropriate
                if (context.current_stage == ConversationStage.URGENCY_CREATION and 
                    not context.urgency_created):
                    urgency_message = self.nyc_expertise.get_urgency_creation_message(context.zip_code)
                    nyc_expertise_response = f"{nyc_expertise_response} {urgency_message}"
                    context.urgency_created = True
                
                # Add objection handling if needed
                if (analysis.get("objection_type") and 
                    context.current_stage == ConversationStage.OBJECTION_RESOLUTION):
                    objection_response = self.nyc_expertise.get_objection_responses(
                        analysis["objection_type"], 
                        context.zip_code
                    )
                    nyc_expertise_response = f"{nyc_expertise_response} {objection_response}"
            
            # Combine responses intelligently
            combined_response = ai_response
            if technical_response:
                combined_response = f"{ai_response}\n\n{technical_response}"
            if nyc_expertise_response:
                combined_response = f"{combined_response}\n\n{nyc_expertise_response}"
            
            # Post-process response
            response_data = {
                "content": combined_response,
                "next_questions": template.get("next_questions", []),
                "nyc_insights": self._extract_nyc_insights(context),
                "urgency_created": context.urgency_created,
                "solar_recommendation": solar_recommendation.__dict__ if solar_recommendation else None,
                "technical_details": {
                    "system_size_kw": solar_recommendation.system_size_kw if solar_recommendation else None,
                    "panel_count": solar_recommendation.panel_count if solar_recommendation else None,
                    "monthly_savings": solar_recommendation.monthly_savings if solar_recommendation else None,
                    "payback_years": solar_recommendation.payback_years if solar_recommendation else None,
                    "net_cost": solar_recommendation.net_cost if solar_recommendation else None
                },
                "nyc_expertise": {
                    "building_type": context.conversation_data.get("building_type"),
                    "historic_district": context.conversation_data.get("historic_district"),
                    "co_op_approval_required": context.conversation_data.get("co_op_approval_required"),
                    "permit_timeline": context.conversation_data.get("permit_timeline")
                }
            }
            
            return response_data
            
        except Exception as e:
            return {
                "content": "I'd love to help you explore solar options for your NYC home. Could you tell me what's driving your interest in solar energy?",
                "next_questions": ["What's your monthly electric bill?", "Do you own your home?"],
                "nyc_insights": {},
                "error": str(e)
            }
    
    async def process_intelligent_conversation(
        self,
        message: str,
        session_id: str,
        lead_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process conversation with advanced intelligence engine"""
        
        try:
            # Get or create conversation context
            context = await self._get_or_create_intelligent_context(session_id, lead_id)
            
            # Get A/B test strategy
            ab_strategy = self.ab_testing.get_optimized_conversation_strategy(session_id, context.__dict__)
            
            # Process with conversation intelligence
            response = await self.conversation_intelligence.process_intelligent_conversation(
                message, context
            )
            
            # Track A/B test metrics
            await self._track_ab_test_metrics(session_id, context, response)
            
            # Update context in database
            await self._update_intelligent_context(context)
            
            return response
            
        except Exception as e:
            # Fallback to basic conversation processing
            return await self.process_conversation(message, session_id, lead_id)
    
    async def _get_or_create_intelligent_context(
        self, 
        session_id: str, 
        lead_id: Optional[str]
    ) -> 'ConversationContext':
        """Get or create intelligent conversation context"""
        
        from app.services.conversation_intelligence_engine import ConversationContext
        
        # Try to load existing context from database
        try:
            conversations = self.db.query(AIConversation).filter(
                AIConversation.session_id == session_id
            ).order_by(AIConversation.created_at.desc()).limit(10).all()
            
            if conversations:
                # Reconstruct context from conversation history
                context = ConversationContext(session_id=session_id, lead_id=lead_id)
                
                for conv in reversed(conversations):
                    if conv.entities_extracted:
                        # Update context with extracted entities
                        entities = conv.entities_extracted
                        
                        if "zip_code" in entities:
                            context.zip_code = entities["zip_code"]
                        if "bill_amount" in entities:
                            context.bill_amount = float(entities["bill_amount"])
                        if "homeowner_status" in entities:
                            context.homeowner_verified = entities["homeowner_status"] in ["owner", "homeowner", "yes"]
                        if "roof_type" in entities:
                            context.roof_type = entities["roof_type"]
                        if "timeline" in entities:
                            context.timeline = entities["timeline"]
                
                return context
                
        except Exception as e:
            print(f"Error loading context: {e}")
        
        # Create new context
        return ConversationContext(session_id=session_id, lead_id=lead_id)
    
    async def _track_ab_test_metrics(
        self, 
        session_id: str, 
        context: 'ConversationContext', 
        response: Dict[str, Any]
    ):
        """Track A/B test metrics"""
        
        try:
            # Track qualification rate
            if context.homeowner_verified and context.bill_amount and context.zip_code:
                self.ab_testing.track_conversation_metric(
                    "qualification_sequence",
                    self.ab_testing.get_test_variant("qualification_sequence", session_id),
                    session_id,
                    "qualification_rate",
                    1.0
                )
            
            # Track B2B value
            b2b_value = response.get("b2b_value_potential", 5)
            self.ab_testing.track_conversation_metric(
                "qualification_sequence",
                self.ab_testing.get_test_variant("qualification_sequence", session_id),
                session_id,
                "b2b_value",
                b2b_value
            )
            
            # Track technical engagement
            technical_engagement = response.get("technical_engagement_level", 5)
            self.ab_testing.track_conversation_metric(
                "technical_expertise",
                self.ab_testing.get_test_variant("technical_expertise", session_id),
                session_id,
                "technical_engagement",
                technical_engagement
            )
            
            # Track urgency creation
            if context.urgency_created:
                self.ab_testing.track_conversation_metric(
                    "urgency_creation",
                    self.ab_testing.get_test_variant("urgency_creation", session_id),
                    session_id,
                    "urgency_creation",
                    1.0
                )
            
        except Exception as e:
            print(f"Error tracking A/B test metrics: {e}")
    
    async def _update_intelligent_context(self, context: 'ConversationContext'):
        """Update intelligent context in database"""
        
        try:
            # Store conversation context as JSON
            context_data = {
                "session_id": context.session_id,
                "lead_id": context.lead_id,
                "current_stage": context.current_stage,
                "lead_score": context.lead_score,
                "quality_tier": context.quality_tier,
                "homeowner_verified": context.homeowner_verified,
                "bill_amount": context.bill_amount,
                "zip_code": context.zip_code,
                "borough": context.borough,
                "neighborhood": context.neighborhood,
                "home_type": context.home_type,
                "roof_type": context.roof_type,
                "roof_size": context.roof_size,
                "shading_factor": context.shading_factor,
                "credit_indicators": context.credit_indicators,
                "timeline": context.timeline,
                "urgency_created": context.urgency_created,
                "technical_questions_answered": context.technical_questions_answered,
                "high_intent_signals": context.high_intent_signals,
                "personalization_data": context.personalization_data,
                "utility_territory": context.utility_territory,
                "electric_rate": context.electric_rate,
                "local_installers": context.local_installers,
                "neighborhood_examples": context.neighborhood_examples,
                "board_approval_required": context.board_approval_required,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store in conversation table
            conversation = AIConversation(
                lead_id=context.lead_id,
                session_id=context.session_id,
                message_type="context_update",
                content=json.dumps(context_data),
                sentiment_score=0.0,
                intent_classification="context_update",
                entities_extracted={},
                confidence_score=1.0,
                response_time_ms=0,
                ai_model_used="conversation_intelligence",
                tokens_used=0
            )
            
            self.db.add(conversation)
            self.db.commit()
            
        except Exception as e:
            print(f"Error updating intelligent context: {e}")
            self.db.rollback()
    
    def _build_response_prompt(self, template: Dict, context: Dict, message: str) -> str:
        """Build AI response prompt with context"""
        
        prompt = f"""
        You are a knowledgeable NYC solar consultant. Respond to this message naturally while advancing the conversation toward lead qualification.
        
        Customer Message: "{message}"
        
        Context:
        - Stage: {context['stage']}
        - Lead Score: {context['lead_score']}
        - NYC Data: {json.dumps(context.get('nyc_data', {}), indent=2)}
        - Bill Amount: {context.get('bill_amount', 'Not provided')}
        - Borough: {context.get('borough', 'Not provided')}
        - Homeowner Verified: {context.get('homeowner_verified', False)}
        - Objections Handled: {context.get('objections_handled', [])}
        
        Guidelines:
        1. Use NYC-specific data and examples
        2. Create urgency around 2025 tax credit deadline
        3. Address objections with local expertise
        4. Qualify for B2B value ($75-300 tiers)
        5. Keep conversation natural, not interrogative
        6. Use neighborhood-specific examples when possible
        
        Response should be 2-3 sentences, conversational, and advance qualification.
        """
        
        return prompt
    
    def _extract_nyc_insights(self, context: ConversationContext) -> Dict[str, Any]:
        """Extract NYC-specific insights for the response"""
        
        if not context.nyc_data:
            return {}
        
        insights = {
            "electric_rate": context.nyc_data.get("average_electric_rate_per_kwh", 0.31),
            "solar_adoption": context.nyc_data.get("solar_adoption_rate", 0.0),
            "borough": context.nyc_data.get("borough", ""),
            "incentives_available": context.nyc_data.get("state_incentives_available", True),
            "average_savings": context.nyc_data.get("average_savings_per_month", 0),
            "competition_level": context.nyc_data.get("competition_intensity", "medium")
        }
        
        return insights
    
    async def _store_conversation(
        self, 
        context: ConversationContext, 
        message: str, 
        response: Dict[str, Any], 
        analysis: Dict[str, Any]
    ):
        """Store conversation in database"""
        
        try:
            # Create conversation record
            conversation = LeadConversation(
                lead_id=context.lead_id,
                session_id=context.session_id,
                message_type="user",
                content=message,
                sentiment_score=analysis.get("sentiment", 0.0),
                intent_classification=analysis.get("intent", "unknown"),
                entities_extracted=analysis.get("entities", {}),
                confidence_score=analysis.get("confidence", 0.5),
                response_time_ms=0,  # Calculate actual response time
                ai_model_used="gpt-4",
                tokens_used=0  # Calculate actual token usage
            )
            
            self.db.add(conversation)
            
            # Create AI response record
            ai_response = LeadConversation(
                lead_id=context.lead_id,
                session_id=context.session_id,
                message_type="ai",
                content=response["content"],
                sentiment_score=0.8,  # AI responses are generally positive
                intent_classification="response",
                entities_extracted={},
                confidence_score=0.9,
                response_time_ms=0,
                ai_model_used="gpt-4",
                tokens_used=0
            )
            
            self.db.add(ai_response)
            self.db.commit()
            
        except Exception as e:
            print(f"Error storing conversation: {e}")
    
    async def _store_solar_recommendation(self, context: ConversationContext, recommendation_data: Dict[str, Any]):
        """Store solar recommendation in database for B2B export"""
        
        try:
            if not context.lead_id:
                return
            
            # Create AICalculation record
            calculation = AICalculation(
                lead_id=context.lead_id,
                session_id=context.session_id,
                calculation_type="solar_recommendation",
                input_data={
                    "monthly_bill": context.bill_amount,
                    "zip_code": context.zip_code,
                    "borough": context.borough,
                    "roof_type": context.roof_type,
                    "roof_size": context.roof_size,
                    "shading_factor": context.shading_factor
                },
                output_data=recommendation_data,
                confidence_score=0.9,
                calculation_timestamp=datetime.utcnow()
            )
            
            self.db.add(calculation)
            self.db.commit()
            
            # Store detailed calculation results
            calculation_result = AICalculationResult(
                calculation_id=calculation.id,
                system_size_kw=recommendation_data.get("system_size_kw"),
                panel_count=recommendation_data.get("panel_count"),
                annual_production_kwh=recommendation_data.get("annual_production_kwh"),
                gross_cost=recommendation_data.get("gross_cost"),
                net_cost=recommendation_data.get("net_cost"),
                monthly_savings=recommendation_data.get("monthly_savings"),
                annual_savings=recommendation_data.get("annual_savings"),
                payback_years=recommendation_data.get("payback_years"),
                lifetime_savings=recommendation_data.get("lifetime_savings"),
                roi_percentage=recommendation_data.get("roi_percentage"),
                financing_options=recommendation_data.get("financing_options", []),
                incentives=recommendation_data.get("incentives", {}),
                installation_timeline=recommendation_data.get("installation_timeline"),
                confidence_score=recommendation_data.get("confidence_score", 0.9)
            )
            
            self.db.add(calculation_result)
            self.db.commit()
            
        except Exception as e:
            print(f"Error storing solar recommendation: {e}")
            self.db.rollback()
    
    async def _update_lead_scoring(self, context: ConversationContext):
        """Update lead scoring based on conversation progress"""
        
        if not context.lead_id:
            return
        
        try:
            # Calculate new lead score
            new_score = await self.lead_scoring.calculate_lead_score(context)
            
            # Update lead record
            lead = self.db.query(Lead).filter(Lead.id == context.lead_id).first()
            if lead:
                old_score = lead.lead_score
                lead.lead_score = new_score
                lead.updated_at = datetime.utcnow()
                
                # Create quality history record
                if new_score != old_score:
                    quality_history = LeadQualityHistory(
                        lead_id=context.lead_id,
                        previous_score=old_score,
                        new_score=new_score,
                        previous_quality=lead.lead_quality,
                        new_quality=self._determine_quality_tier(new_score),
                        score_change=new_score - old_score,
                        quality_change_reason="Conversation progress",
                        factors_considered=context.qualification_factors,
                        ai_model_version="gpt-4",
                        confidence_score=0.8
                    )
                    
                    self.db.add(quality_history)
                
                # Update quality tier
                context.quality_tier = self._determine_quality_tier(new_score)
                lead.lead_quality = context.quality_tier.value
                
                self.db.commit()
                
        except Exception as e:
            print(f"Error updating lead scoring: {e}")
            self.db.rollback()
    
    def _determine_quality_tier(self, score: int) -> LeadQualityTier:
        """Determine B2B quality tier based on lead score"""
        
        if score >= 85:
            return LeadQualityTier.PREMIUM
        elif score >= 70:
            return LeadQualityTier.STANDARD
        elif score >= 50:
            return LeadQualityTier.BASIC
        else:
            return LeadQualityTier.UNQUALIFIED
    
    async def _prepare_b2b_export(self, context: ConversationContext):
        """Prepare lead for B2B export when qualified"""
        
        if not context.lead_id or context.quality_tier == LeadQualityTier.UNQUALIFIED:
            return
        
        try:
            # Enrich lead with NYC market data
            lead = self.db.query(Lead).filter(Lead.id == context.lead_id).first()
            if lead and context.nyc_data:
                # Update lead with NYC insights
                lead.ai_insights = json.dumps({
                    "nyc_market_data": context.nyc_data,
                    "conversation_insights": context.conversation_data,
                    "qualification_factors": context.qualification_factors,
                    "quality_tier": context.quality_tier.value,
                    "b2b_value_estimate": self._calculate_b2b_value(context)
                })
                
                # Mark as qualified
                lead.status = "qualified"
                lead.qualification_status = "qualified"
                lead.qualification_reason = f"Conversation qualified - {context.quality_tier.value} tier"
                lead.qualified_at = datetime.utcnow()
                
                self.db.commit()
                
        except Exception as e:
            print(f"Error preparing B2B export: {e}")
            self.db.rollback()
    
    def _calculate_b2b_value(self, context: ConversationContext) -> float:
        """Calculate estimated B2B value based on quality tier"""
        
        tier_values = {
            LeadQualityTier.PREMIUM: 250.0,
            LeadQualityTier.STANDARD: 150.0,
            LeadQualityTier.BASIC: 100.0,
            LeadQualityTier.UNQUALIFIED: 0.0
        }
        
        base_value = tier_values.get(context.quality_tier, 0.0)
        
        # Adjust based on NYC market factors
        if context.nyc_data:
            if context.nyc_data.get("high_value_zip_code", False):
                base_value *= 1.2
            if context.nyc_data.get("solar_adoption_rate", 0) > 0.15:
                base_value *= 1.1
        
        return base_value
    
    def _load_conversation_templates(self) -> Dict[str, Dict]:
        """Load conversation templates for each stage"""
        
        return {
            "welcome": {
                "system_prompt": "You are a knowledgeable NYC solar consultant. Create excitement about solar savings while qualifying the lead.",
                "next_questions": [
                    "What's driving your interest in solar?",
                    "What's your monthly Con Ed bill?",
                    "Do you own your home?"
                ]
            },
            "interest_assessment": {
                "system_prompt": "Assess their interest level and gather basic qualification info.",
                "next_questions": [
                    "What's your monthly electric bill?",
                    "What zip code are you in?",
                    "Are you the homeowner?"
                ]
            },
            "location_qualification": {
                "system_prompt": "Use their location to provide personalized NYC solar insights and incentives.",
                "next_questions": [
                    "What's your monthly Con Ed bill?",
                    "When are you looking to install?",
                    "What type of roof do you have?"
                ]
            },
            "bill_discovery": {
                "system_prompt": "Use their bill amount to calculate specific savings and create urgency.",
                "next_questions": [
                    "Are you the homeowner?",
                    "What's your timeline for installation?",
                    "Have you looked into the 2025 tax credit?"
                ]
            },
            "homeowner_verification": {
                "system_prompt": "Confirm homeownership and create urgency around the 2025 tax credit deadline.",
                "next_questions": [
                    "What's your timeline for installation?",
                    "Have you considered the 2025 tax credit deadline?",
                    "What questions do you have about the process?"
                ]
            },
            "roof_assessment": {
                "system_prompt": "Gather roof information to determine solar system feasibility and sizing.",
                "next_questions": [
                    "What type of roof do you have? (asphalt, metal, tile, flat, etc.)",
                    "How old is your roof?",
                    "Are there any trees or buildings that shade your roof?",
                    "What direction does your roof face?",
                    "Do you know the approximate size of your roof?"
                ]
            },
            "solar_calculation": {
                "system_prompt": "Provide detailed solar system recommendations with technical specifications and financial analysis.",
                "next_questions": [
                    "Would you like to see financing options?",
                    "Do you have any questions about the installation process?",
                    "Would you like to schedule a consultation?",
                    "What's your preferred timeline for installation?"
                ]
            },
            "urgency_creation": {
                "system_prompt": "Create urgency around the 2025 tax credit deadline and move toward qualification.",
                "next_questions": [
                    "Would you like to schedule a consultation?",
                    "What's your preferred timeline?",
                    "Do you have any concerns about the process?"
                ]
            },
            "objection_resolution": {
                "system_prompt": "Address their specific objections with NYC expertise and data.",
                "next_questions": [
                    "Does that address your concern?",
                    "What other questions do you have?",
                    "Would you like to move forward?"
                ]
            },
            "qualification_completion": {
                "system_prompt": "Complete qualification and prepare for B2B export.",
                "next_questions": [
                    "Would you like to schedule a consultation?",
                    "What's the best way to contact you?",
                    "Do you have any final questions?"
                ]
            }
        }
    
    def _load_nyc_neighborhood_data(self) -> Dict[str, Dict]:
        """Load NYC neighborhood-specific data for personalization"""
        
        return {
            "10001": {  # Chelsea
                "neighborhood": "Chelsea",
                "borough": "Manhattan",
                "avg_bill": 380,
                "savings_potential": 2800,
                "incentive_combination": "Federal + NYSERDA + Property Tax Abatement",
                "roof_challenges": "Historic district restrictions",
                "success_story": "Chelsea co-op saved $3,200 annually with board-approved installation"
            },
            "11201": {  # DUMBO
                "neighborhood": "DUMBO",
                "borough": "Brooklyn",
                "avg_bill": 320,
                "savings_potential": 2400,
                "incentive_combination": "Federal + NYSERDA + Local Grant",
                "roof_challenges": "Industrial building conversions",
                "success_story": "DUMBO loft owner achieved 85% cost reduction with stacked incentives"
            },
            "11375": {  # Forest Hills
                "neighborhood": "Forest Hills",
                "borough": "Queens",
                "avg_bill": 220,
                "savings_potential": 1800,
                "incentive_combination": "Federal + NYSERDA + Community Solar",
                "roof_challenges": "Co-op board approval process",
                "success_story": "Forest Hills co-op installed 50+ systems with board support"
            },
            "10451": {  # South Bronx
                "neighborhood": "South Bronx",
                "borough": "Bronx",
                "avg_bill": 180,
                "savings_potential": 1400,
                "incentive_combination": "Federal + NYSERDA + Low-Income Grant",
                "roof_challenges": "Multi-family building complexity",
                "success_story": "Bronx affordable housing project saved residents $1,200 annually"
            },
            "10301": {  # Staten Island
                "neighborhood": "St. George",
                "borough": "Staten Island",
                "avg_bill": 200,
                "savings_potential": 1600,
                "incentive_combination": "Federal + NYSERDA + Utility Rebate",
                "roof_challenges": "Hurricane zone considerations",
                "success_story": "Staten Island homeowner achieved 6-year payback with hurricane-rated panels"
            }
        }
