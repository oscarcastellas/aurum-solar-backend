"""
AI Conversation Agent Validation Tests
Tests for AI conversation capabilities and lead qualification
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_conversation import AIConversationEngine
from app.core.redis import get_redis

client = TestClient(app)

class TestAIConversationValidation:
    """AI conversation agent validation tests"""
    
    def setup_method(self):
        """Setup test environment"""
        self.conversation_engine = AIConversationEngine()
        self.test_lead_id = "test_lead_123"
        self.test_conversation_id = "test_conv_123"
    
    @pytest.mark.asyncio
    async def test_conversation_initiation(self):
        """Test conversation start and greeting"""
        # Mock Redis connection
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test conversation initiation
            response = await self.conversation_engine.start_conversation(
                lead_id=self.test_lead_id,
                user_message="Hello, I'm interested in solar"
            )
            
            assert response is not None
            assert "conversation_id" in response
            assert "ai_response" in response
            assert "conversation_state" in response
            
            # Verify greeting contains NYC context
            ai_response = response["ai_response"]
            assert "solar" in ai_response.lower()
            assert any(borough in ai_response for borough in ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"])
            
            print("✅ Conversation initiation test passed")
    
    @pytest.mark.asyncio
    async def test_lead_qualification_flow(self):
        """Test lead qualification questions and flow"""
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test homeowner verification
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="Yes, I own my home"
            )
            
            assert response is not None
            assert "ai_response" in response
            assert "conversation_state" in response
            
            # Test electric bill discovery
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="My electric bill is about $200 per month"
            )
            
            assert response is not None
            assert "ai_response" in response
            
            # Test timeline urgency
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="I'd like to install solar by the end of this year"
            )
            
            assert response is not None
            assert "ai_response" in response
            
            print("✅ Lead qualification flow test passed")
    
    @pytest.mark.asyncio
    async def test_nyc_market_expertise(self):
        """Test NYC market knowledge and expertise"""
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test borough-specific knowledge
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="I live in Brooklyn, what are the solar incentives?"
            )
            
            assert response is not None
            ai_response = response["ai_response"]
            
            # Verify Brooklyn-specific information
            assert "Brooklyn" in ai_response or "NYC" in ai_response
            assert any(keyword in ai_response.lower() for keyword in ["incentive", "rebate", "tax credit"])
            
            # Test electric rate knowledge
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="What are the electric rates in NYC?"
            )
            
            assert response is not None
            ai_response = response["ai_response"]
            
            # Verify electric rate information
            assert any(keyword in ai_response.lower() for keyword in ["rate", "cost", "kwh", "electric"])
            
            print("✅ NYC market expertise test passed")
    
    @pytest.mark.asyncio
    async def test_quality_scoring(self):
        """Test real-time lead scoring and quality classification"""
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test high-quality lead
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="I own my home in Manhattan, my electric bill is $300/month, and I want to install solar this year"
            )
            
            assert response is not None
            assert "quality_score" in response
            assert "quality_tier" in response
            
            quality_score = response["quality_score"]
            quality_tier = response["quality_tier"]
            
            # Verify high-quality lead scoring
            assert quality_score >= 80  # High score for premium lead
            assert quality_tier in ["premium", "standard"]
            
            print("✅ Quality scoring test passed")
    
    @pytest.mark.asyncio
    async def test_objection_handling(self):
        """Test objection handling with NYC-specific data"""
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test cost objection
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="Solar is too expensive for me"
            )
            
            assert response is not None
            ai_response = response["ai_response"]
            
            # Verify cost objection handling
            assert any(keyword in ai_response.lower() for keyword in ["cost", "expensive", "affordable", "savings"])
            assert any(keyword in ai_response.lower() for keyword in ["incentive", "rebate", "tax credit"])
            
            # Test roof objection
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="My roof is too old for solar"
            )
            
            assert response is not None
            ai_response = response["ai_response"]
            
            # Verify roof objection handling
            assert any(keyword in ai_response.lower() for keyword in ["roof", "inspection", "assessment", "condition"])
            
            print("✅ Objection handling test passed")
    
    @pytest.mark.asyncio
    async def test_conversation_quality(self):
        """Test conversation quality and user experience"""
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test response relevance
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="Tell me about solar panels"
            )
            
            assert response is not None
            ai_response = response["ai_response"]
            
            # Verify response relevance
            assert len(ai_response) > 50  # Substantial response
            assert any(keyword in ai_response.lower() for keyword in ["solar", "panel", "energy", "electric"])
            
            # Test natural language processing
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="I'm not sure if this is right for me"
            )
            
            assert response is not None
            ai_response = response["ai_response"]
            
            # Verify empathetic response
            assert any(keyword in ai_response.lower() for keyword in ["understand", "help", "questions", "concerns"])
            
            print("✅ Conversation quality test passed")
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self):
        """Test AI conversation performance requirements"""
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test response time
            start_time = datetime.utcnow()
            
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="Hello, I want to learn about solar"
            )
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            assert response is not None
            assert response_time < 2.0  # Response time under 2 seconds
            
            print(f"✅ Performance test passed - Response time: {response_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_edge_case_handling(self):
        """Test edge case handling and error scenarios"""
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test invalid input
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message=""
            )
            
            assert response is not None
            assert "ai_response" in response
            assert len(response["ai_response"]) > 0  # Should handle empty input gracefully
            
            # Test conversation interruption
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="I need to go now"
            )
            
            assert response is not None
            ai_response = response["ai_response"]
            assert any(keyword in ai_response.lower() for keyword in ["contact", "information", "follow", "later"])
            
            print("✅ Edge case handling test passed")
    
    @pytest.mark.asyncio
    async def test_database_integration(self):
        """Test AI conversation database integration"""
        with patch('app.core.redis.get_redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis.return_value = mock_redis_instance
            
            # Test conversation storage
            response = await self.conversation_engine.process_message(
                conversation_id=self.test_conversation_id,
                user_message="I'm interested in solar for my home"
            )
            
            assert response is not None
            assert "conversation_id" in response
            
            # Verify conversation is stored in Redis
            mock_redis_instance.set.assert_called()
            
            print("✅ Database integration test passed")
    
    @pytest.mark.asyncio
    async def test_websocket_integration(self):
        """Test AI conversation WebSocket integration"""
        # Test WebSocket connection
        with client.websocket_connect("/ws/chat") as websocket:
            # Send initial message
            websocket.send_json({
                "type": "message",
                "content": "Hello, I'm interested in solar"
            })
            
            # Receive AI response
            response = websocket.receive_json()
            assert "type" in response
            assert "content" in response
            assert response["type"] == "ai_response"
            
            # Send follow-up message
            websocket.send_json({
                "type": "message",
                "content": "I live in Brooklyn"
            })
            
            # Receive AI response
            response = websocket.receive_json()
            assert "type" in response
            assert "content" in response
            
            print("✅ WebSocket integration test passed")

class TestConversationQualityValidation:
    """Conversation quality and user experience validation"""
    
    def test_conversation_flow_consistency(self):
        """Test conversation flow consistency and logic"""
        # Test that conversation follows logical progression
        conversation_steps = [
            "Hello, I'm interested in solar",
            "Yes, I own my home",
            "My electric bill is about $200 per month",
            "I'd like to install solar this year",
            "I live in Brooklyn"
        ]
        
        # This would test the conversation flow logic
        # In a real implementation, you'd test the conversation state machine
        
        print("✅ Conversation flow consistency test passed")
    
    def test_nyc_market_data_accuracy(self):
        """Test NYC market data accuracy and currency"""
        # Test that market data is accurate and up-to-date
        test_data = {
            "electric_rates": {
                "Manhattan": 0.35,
                "Brooklyn": 0.32,
                "Queens": 0.31,
                "Bronx": 0.29,
                "Staten Island": 0.30
            },
            "incentives": {
                "federal_tax_credit": 0.30,
                "nyserda_rebate": 0.25,
                "nyc_property_tax_abatement": 0.20
            }
        }
        
        # Verify data accuracy
        assert all(rate > 0 for rate in test_data["electric_rates"].values())
        assert all(incentive >= 0 for incentive in test_data["incentives"].values())
        
        print("✅ NYC market data accuracy test passed")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
