"""
Unit tests for Conversation Intelligence Engine
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.conversation_intelligence_engine import (
    ConversationIntelligenceEngine,
    ProactiveQualificationEngine,
    TechnicalExpertiseEngine,
    ObjectionHandlingExpert,
    UrgencyCreationEngine,
    ConversationPersonalizationEngine,
    ConversationContext,
    ConversationIntent,
    LeadValueImpact
)


class TestProactiveQualificationEngine:
    """Test cases for Proactive Qualification Engine"""
    
    def test_get_next_qualification_question(self):
        """Test getting next qualification question"""
        engine = ProactiveQualificationEngine()
        
        # Test with empty context
        context = ConversationContext(session_id="test_session")
        question = engine.get_next_qualification_question(context)
        assert question is not None
        assert "homeowner" in question.lower() or "own" in question.lower()
        
        # Test with partial context
        context.homeowner_verified = True
        context.bill_amount = 300.0
        question = engine.get_next_qualification_question(context)
        assert question is not None
        assert "zip" in question.lower() or "location" in question.lower()
    
    def test_calculate_qualification_progress(self):
        """Test qualification progress calculation"""
        engine = ProactiveQualificationEngine()
        
        # Test empty context
        context = ConversationContext(session_id="test_session")
        progress = engine.calculate_qualification_progress(context)
        assert progress == 0.0
        
        # Test partial context
        context.homeowner_verified = True
        context.bill_amount = 300.0
        context.credit_indicators = ["looking to finance"]
        progress = engine.calculate_qualification_progress(context)
        assert 0.0 < progress < 1.0
        
        # Test complete context
        context.timeline = "spring 2024"
        context.technical_questions_answered = 2
        progress = engine.calculate_qualification_progress(context)
        assert progress == 1.0


class TestTechnicalExpertiseEngine:
    """Test cases for Technical Expertise Engine"""
    
    def test_get_technical_response_coop_approval(self):
        """Test co-op approval technical response"""
        engine = TechnicalExpertiseEngine()
        context = ConversationContext(session_id="test_session")
        
        response = engine.get_technical_response("coop_approval", context)
        assert "co-op" in response.lower()
        assert "85%" in response or "approval" in response.lower()
    
    def test_get_technical_response_roof_concerns(self):
        """Test roof concerns technical response"""
        engine = TechnicalExpertiseEngine()
        context = ConversationContext(session_id="test_session")
        context.roof_type = "asphalt"
        
        response = engine.get_technical_response("roof_concerns", context)
        assert "asphalt" in response.lower()
        assert "installers" in response.lower()
    
    def test_get_technical_response_permits_process(self):
        """Test permits process technical response"""
        engine = TechnicalExpertiseEngine()
        context = ConversationContext(session_id="test_session")
        
        response = engine.get_technical_response("permits_process", context)
        assert "permit" in response.lower()
        assert "handle" in response.lower()
    
    def test_get_technical_response_financing_options(self):
        """Test financing options technical response"""
        engine = TechnicalExpertiseEngine()
        context = ConversationContext(session_id="test_session")
        
        response = engine.get_technical_response("financing_options", context)
        assert "financing" in response.lower()
        assert "loan" in response.lower()


class TestObjectionHandlingExpert:
    """Test cases for Objection Handling Expert"""
    
    def test_handle_objection_cost(self):
        """Test cost objection handling"""
        expert = ObjectionHandlingExpert()
        context = ConversationContext(session_id="test_session")
        context.bill_amount = 400.0
        
        response = expert.handle_objection("cost", context)
        assert "incentive" in response.lower() or "financing" in response.lower()
        assert "$" in response
    
    def test_handle_objection_roof(self):
        """Test roof objection handling"""
        expert = ObjectionHandlingExpert()
        context = ConversationContext(session_id="test_session")
        context.roof_type = "asphalt"
        context.neighborhood = "park_slope"
        
        response = expert.handle_objection("roof", context)
        assert "asphalt" in response.lower()
        assert "installers" in response.lower()
    
    def test_handle_objection_aesthetics(self):
        """Test aesthetics objection handling"""
        expert = ObjectionHandlingExpert()
        context = ConversationContext(session_id="test_session")
        context.neighborhood = "upper_east_side"
        
        response = expert.handle_objection("aesthetics", context)
        assert "modern" in response.lower() or "attractive" in response.lower()
    
    def test_handle_objection_process(self):
        """Test process objection handling"""
        expert = ObjectionHandlingExpert()
        context = ConversationContext(session_id="test_session")
        
        response = expert.handle_objection("process", context)
        assert "handle" in response.lower()
        assert "process" in response.lower()


class TestUrgencyCreationEngine:
    """Test cases for Urgency Creation Engine"""
    
    def test_create_urgency_tax_credit(self):
        """Test tax credit urgency creation"""
        engine = UrgencyCreationEngine()
        context = ConversationContext(session_id="test_session")
        
        urgency = engine.create_urgency(context)
        # Should mention tax credit or deadline
        assert "tax" in urgency.lower() or "deadline" in urgency.lower() or "2025" in urgency
    
    def test_create_urgency_nyserda(self):
        """Test NYSERDA urgency creation"""
        engine = UrgencyCreationEngine()
        context = ConversationContext(session_id="test_session")
        
        urgency = engine.create_urgency(context)
        # Should mention NYSERDA or rebate
        assert "nyserda" in urgency.lower() or "rebate" in urgency.lower() or "funding" in urgency.lower()


class TestConversationPersonalizationEngine:
    """Test cases for Conversation Personalization Engine"""
    
    def test_personalize_message_neighborhood(self):
        """Test neighborhood personalization"""
        engine = ConversationPersonalizationEngine()
        context = ConversationContext(session_id="test_session")
        context.neighborhood = "park_slope"
        context.bill_amount = 350.0
        
        base_message = "Solar can save you money on your electric bill."
        personalized = engine.personalize_message(base_message, context)
        
        assert len(personalized) > len(base_message)
        assert "park slope" in personalized.lower() or "brooklyn" in personalized.lower()
    
    def test_personalize_message_high_income(self):
        """Test high income personalization"""
        engine = ConversationPersonalizationEngine()
        context = ConversationContext(session_id="test_session")
        context.bill_amount = 500.0  # High income indicator
        
        base_message = "Solar is a great investment."
        personalized = engine.personalize_message(base_message, context)
        
        assert "investment" in personalized.lower()
        assert "roi" in personalized.lower() or "return" in personalized.lower()
    
    def test_personalize_message_coop(self):
        """Test co-op personalization"""
        engine = ConversationPersonalizationEngine()
        context = ConversationContext(session_id="test_session")
        context.board_approval_required = True
        
        base_message = "We can help with your solar installation."
        personalized = engine.personalize_message(base_message, context)
        
        assert "board" in personalized.lower() or "co-op" in personalized.lower()


class TestConversationIntelligenceEngine:
    """Test cases for main Conversation Intelligence Engine"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def engine(self, mock_db):
        """Create engine instance with mocked dependencies"""
        with patch('app.services.conversation_intelligence_engine.openai.OpenAI'):
            return ConversationIntelligenceEngine(mock_db)
    
    @pytest.mark.asyncio
    async def test_analyze_message_intelligence(self, engine):
        """Test message analysis with intelligence"""
        message = "I'm interested in solar for my co-op in Manhattan. What's the process?"
        context = ConversationContext(session_id="test_session")
        
        with patch.object(engine.openai_client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices[0].message.content = json.dumps({
                "primary_intent": "technical_question",
                "secondary_intents": ["high_intent_qualification"],
                "entities": {"zip_code": "10021", "homeowner_status": "owner"},
                "sentiment": 0.8,
                "objection_type": None,
                "qualification_signals": ["high_intent_phrases"],
                "urgency_indicators": [],
                "technical_engagement_level": 8,
                "b2b_value_potential": 8,
                "conversation_stage_recommendation": "discovery"
            })
            
            analysis = await engine._analyze_message_intelligence(message, context)
            
            assert analysis["primary_intent"] == "technical_question"
            assert analysis["technical_engagement_level"] == 8
            assert analysis["b2b_value_potential"] == 8
    
    @pytest.mark.asyncio
    async def test_update_context_intelligence(self, engine):
        """Test context update with intelligence"""
        context = ConversationContext(session_id="test_session")
        analysis = {
            "entities": {
                "zip_code": "10021",
                "bill_amount": "400",
                "homeowner_status": "owner"
            },
            "qualification_signals": ["high_intent_phrases"],
            "technical_engagement_level": 8,
            "b2b_value_potential": 8
        }
        
        updated_context = await engine._update_context_intelligence(context, analysis)
        
        assert updated_context.zip_code == "10021"
        assert updated_context.bill_amount == 400.0
        assert updated_context.homeowner_verified == True
        assert "high_intent_phrases" in updated_context.credit_indicators
        assert updated_context.technical_questions_answered == 1
    
    @pytest.mark.asyncio
    async def test_determine_conversation_strategy(self, engine):
        """Test conversation strategy determination"""
        context = ConversationContext(session_id="test_session")
        context.bill_amount = 350.0
        context.zip_code = "10021"
        context.homeowner_verified = True
        
        analysis = {
            "primary_intent": "high_intent_qualification",
            "b2b_value_potential": 8,
            "technical_engagement_level": 7
        }
        
        strategy = await engine._determine_conversation_strategy(context, analysis)
        
        assert strategy["primary_approach"] == "qualification"
        assert strategy["include_solar_calculation"] == True
        assert strategy["personalization_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_generate_intelligent_response(self, engine):
        """Test intelligent response generation"""
        context = ConversationContext(session_id="test_session")
        context.bill_amount = 350.0
        context.zip_code = "10021"
        context.neighborhood = "upper_east_side"
        
        analysis = {
            "primary_intent": "technical_question",
            "technical_engagement_level": 8,
            "b2b_value_potential": 8
        }
        
        strategy = {
            "primary_approach": "education",
            "secondary_approach": "qualification",
            "include_solar_calculation": True,
            "personalization_level": "high"
        }
        
        response = await engine._generate_intelligent_response(context, analysis, strategy)
        
        assert "content" in response
        assert "next_questions" in response
        assert "conversation_stage" in response
        assert "qualification_progress" in response
        assert "b2b_value_potential" in response
    
    @pytest.mark.asyncio
    async def test_process_intelligent_conversation(self, engine):
        """Test full intelligent conversation processing"""
        message = "I'm interested in solar for my co-op in Manhattan"
        context = ConversationContext(session_id="test_session")
        
        with patch.object(engine, '_analyze_message_intelligence', return_value={
            "primary_intent": "high_intent_qualification",
            "entities": {"zip_code": "10021", "homeowner_status": "owner"},
            "b2b_value_potential": 8,
            "technical_engagement_level": 7
        }):
            with patch.object(engine, '_determine_conversation_strategy', return_value={
                "primary_approach": "qualification",
                "include_solar_calculation": True
            }):
                with patch.object(engine, '_generate_intelligent_response', return_value={
                    "content": "Great! Manhattan is an excellent solar market.",
                    "next_questions": ["What's your monthly electric bill?"],
                    "conversation_stage": "discovery",
                    "qualification_progress": 0.4,
                    "b2b_value_potential": 8,
                    "technical_engagement_level": 7
                }):
                    response = await engine.process_intelligent_conversation(message, context)
                    
                    assert "content" in response
                    assert "next_questions" in response
                    assert response["b2b_value_potential"] == 8


class TestConversationContext:
    """Test cases for Conversation Context"""
    
    def test_context_initialization(self):
        """Test context initialization"""
        context = ConversationContext(session_id="test_session")
        
        assert context.session_id == "test_session"
        assert context.lead_id is None
        assert context.current_stage == "welcome"
        assert context.lead_score == 0
        assert context.quality_tier == "unqualified"
        assert context.conversation_history == []
        assert context.objections_handled == []
        assert context.qualification_gaps == []
        assert context.high_intent_signals == []
        assert context.personalization_data == {}
        assert context.local_installers == []
        assert context.neighborhood_examples == []
    
    def test_context_with_lead_id(self):
        """Test context with lead ID"""
        context = ConversationContext(session_id="test_session", lead_id="lead_123")
        
        assert context.session_id == "test_session"
        assert context.lead_id == "lead_123"
    
    def test_context_qualification_data(self):
        """Test context with qualification data"""
        context = ConversationContext(
            session_id="test_session",
            homeowner_verified=True,
            bill_amount=350.0,
            zip_code="10021",
            borough="manhattan"
        )
        
        assert context.homeowner_verified == True
        assert context.bill_amount == 350.0
        assert context.zip_code == "10021"
        assert context.borough == "manhattan"


if __name__ == "__main__":
    pytest.main([__file__])
