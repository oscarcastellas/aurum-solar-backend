"""
Database & APIs Validation Tests
Tests for database schema, data integrity, and API endpoints
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.core.database import get_db, engine
from app.main import app
from app.models.lead import Lead, LeadConversation, LeadQualityHistory
from app.models.b2b_platforms import B2BPlatform, B2BRevenueTransaction
from app.models.analytics import AnalyticsEvent, PerformanceMetric
from app.core.redis import get_redis

client = TestClient(app)

class TestDatabaseValidation:
    """Database schema and data integrity validation tests"""
    
    def setup_method(self):
        """Setup test database and data"""
        # Create test database tables
        from app.models.lead import Base as LeadBase
        from app.models.b2b_platforms import Base as B2BBase
        from app.models.analytics import Base as AnalyticsBase
        
        LeadBase.metadata.create_all(bind=engine)
        B2BBase.metadata.create_all(bind=engine)
        AnalyticsBase.metadata.create_all(bind=engine)
    
    def teardown_method(self):
        """Cleanup test data"""
        # Drop test tables
        from app.models.lead import Base as LeadBase
        from app.models.b2b_platforms import Base as B2BBase
        from app.models.analytics import Base as AnalyticsBase
        
        LeadBase.metadata.drop_all(bind=engine)
        B2BBase.metadata.drop_all(bind=engine)
        AnalyticsBase.metadata.drop_all(bind=engine)
    
    def test_database_schema_creation(self):
        """Test that all database tables are created correctly"""
        db = next(get_db())
        
        # Test lead tables
        assert db.query(Lead).first() is None  # Empty but table exists
        assert db.query(LeadConversation).first() is None
        assert db.query(LeadQualityHistory).first() is None
        
        # Test B2B platform tables
        assert db.query(B2BPlatform).first() is None
        assert db.query(B2BRevenueTransaction).first() is None
        
        # Test analytics tables
        assert db.query(AnalyticsEvent).first() is None
        assert db.query(PerformanceMetric).first() is None
        
        print("✅ Database schema creation test passed")
    
    def test_lead_data_integrity(self):
        """Test lead data insertion and validation"""
        db = next(get_db())
        
        # Create test lead
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            property_address="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            borough="Manhattan",
            property_type="single_family",
            square_footage=2000,
            roof_type="asphalt_shingle",
            roof_condition="good",
            monthly_electric_bill=150.0,
            electric_provider="ConEd",
            lead_score=85,
            lead_quality="premium",
            qualification_status="qualified",
            estimated_value=250.0,
            source="website",
            created_at=datetime.utcnow()
        )
        
        db.add(lead)
        db.commit()
        
        # Verify lead was created
        saved_lead = db.query(Lead).filter(Lead.email == "john.doe@example.com").first()
        assert saved_lead is not None
        assert saved_lead.first_name == "John"
        assert saved_lead.lead_score == 85
        assert saved_lead.lead_quality == "premium"
        
        print("✅ Lead data integrity test passed")
    
    def test_b2b_platform_data_integrity(self):
        """Test B2B platform configuration storage"""
        db = next(get_db())
        
        # Create test platform
        platform = B2BPlatform(
            platform_code="test_platform",
            platform_name="Test Platform",
            delivery_method="json_api",
            api_endpoint="https://api.testplatform.com/leads",
            api_key="test_api_key",
            min_lead_score=70,
            max_daily_exports=100,
            revenue_share=0.15,
            sla_minutes=30,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(platform)
        db.commit()
        
        # Verify platform was created
        saved_platform = db.query(B2BPlatform).filter(B2BPlatform.platform_code == "test_platform").first()
        assert saved_platform is not None
        assert saved_platform.platform_name == "Test Platform"
        assert saved_platform.delivery_method == "json_api"
        assert saved_platform.revenue_share == 0.15
        
        print("✅ B2B platform data integrity test passed")
    
    def test_revenue_transaction_data_integrity(self):
        """Test revenue transaction data consistency"""
        db = next(get_db())
        
        # Create test lead and platform first
        lead = Lead(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="+1234567891",
            property_address="456 Oak St",
            city="Brooklyn",
            state="NY",
            zip_code="11215",
            borough="Brooklyn",
            lead_score=80,
            lead_quality="standard",
            estimated_value=200.0,
            created_at=datetime.utcnow()
        )
        
        platform = B2BPlatform(
            platform_code="revenue_test_platform",
            platform_name="Revenue Test Platform",
            delivery_method="json_api",
            revenue_share=0.20,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(lead)
        db.add(platform)
        db.commit()
        
        # Create revenue transaction
        transaction = B2BRevenueTransaction(
            lead_id=lead.id,
            platform_id=platform.id,
            transaction_date=datetime.utcnow(),
            gross_amount=200.0,
            commission_rate=0.20,
            commission_amount=40.0,
            net_amount=160.0,
            transaction_status="confirmed",
            payment_status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(transaction)
        db.commit()
        
        # Verify transaction was created
        saved_transaction = db.query(B2BRevenueTransaction).filter(
            B2BRevenueTransaction.lead_id == lead.id
        ).first()
        assert saved_transaction is not None
        assert saved_transaction.gross_amount == 200.0
        assert saved_transaction.commission_amount == 40.0
        assert saved_transaction.net_amount == 160.0
        
        print("✅ Revenue transaction data integrity test passed")
    
    def test_foreign_key_relationships(self):
        """Test foreign key constraints and relationships"""
        db = next(get_db())
        
        # Create test data
        lead = Lead(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="+1234567892",
            property_address="789 Pine St",
            city="Queens",
            state="NY",
            zip_code="11101",
            borough="Queens",
            lead_score=75,
            lead_quality="standard",
            estimated_value=175.0,
            created_at=datetime.utcnow()
        )
        
        db.add(lead)
        db.commit()
        
        # Test conversation relationship
        conversation = LeadConversation(
            lead_id=lead.id,
            conversation_data={"messages": [{"role": "user", "content": "Hello"}]},
            conversation_summary="Test conversation",
            sentiment_score=0.8,
            created_at=datetime.utcnow()
        )
        
        db.add(conversation)
        db.commit()
        
        # Verify relationship
        saved_conversation = db.query(LeadConversation).filter(
            LeadConversation.lead_id == lead.id
        ).first()
        assert saved_conversation is not None
        assert saved_conversation.lead_id == lead.id
        
        # Test quality history relationship
        quality_history = LeadQualityHistory(
            lead_id=lead.id,
            quality_score=75,
            quality_tier="standard",
            scoring_factors={"bill_amount": 0.3, "timeline": 0.4, "homeowner": 0.3},
            created_at=datetime.utcnow()
        )
        
        db.add(quality_history)
        db.commit()
        
        # Verify relationship
        saved_quality = db.query(LeadQualityHistory).filter(
            LeadQualityHistory.lead_id == lead.id
        ).first()
        assert saved_quality is not None
        assert saved_quality.lead_id == lead.id
        
        print("✅ Foreign key relationships test passed")

class TestAPIValidation:
    """API endpoint validation tests"""
    
    def setup_method(self):
        """Setup test data for API tests"""
        # Create test data in database
        db = next(get_db())
        
        # Create test leads
        leads = [
            Lead(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                property_address="123 Main St",
                city="New York",
                state="NY",
                zip_code="10001",
                borough="Manhattan",
                lead_score=85,
                lead_quality="premium",
                estimated_value=250.0,
                created_at=datetime.utcnow()
            ),
            Lead(
                first_name="Jane",
                last_name="Smith",
                email="jane.smith@example.com",
                phone="+1234567891",
                property_address="456 Oak St",
                city="Brooklyn",
                state="NY",
                zip_code="11215",
                borough="Brooklyn",
                lead_score=75,
                lead_quality="standard",
                estimated_value=200.0,
                created_at=datetime.utcnow()
            )
        ]
        
        for lead in leads:
            db.add(lead)
        
        # Create test platforms
        platforms = [
            B2BPlatform(
                platform_code="solarreviews",
                platform_name="SolarReviews",
                delivery_method="json_api",
                revenue_share=0.15,
                is_active=True,
                created_at=datetime.utcnow()
            ),
            B2BPlatform(
                platform_code="modernize",
                platform_name="Modernize",
                delivery_method="csv_email",
                revenue_share=0.20,
                is_active=True,
                created_at=datetime.utcnow()
            )
        ]
        
        for platform in platforms:
            db.add(platform)
        
        db.commit()
    
    def test_analytics_executive_summary_api(self):
        """Test executive summary API endpoint"""
        response = client.get("/api/v1/analytics/executive-summary?timeRange=7d")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "revenue" in data
        assert "leads" in data
        assert "quality" in data
        assert "performance" in data
        
        # Verify data types
        assert isinstance(data["revenue"]["total"], (int, float))
        assert isinstance(data["leads"]["total"], int)
        assert isinstance(data["quality"]["avg_score"], (int, float))
        
        print("✅ Executive summary API test passed")
    
    def test_analytics_revenue_api(self):
        """Test revenue analytics API endpoint"""
        response = client.get("/api/v1/analytics/revenue?timeRange=7d")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_revenue" in data
        assert "growth_percent" in data
        assert "daily_revenue" in data
        assert "platform_breakdown" in data
        
        print("✅ Revenue analytics API test passed")
    
    def test_analytics_lead_quality_api(self):
        """Test lead quality analytics API endpoint"""
        response = client.get("/api/v1/analytics/lead-quality?timeRange=7d")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_leads" in data
        assert "qualified_leads" in data
        assert "qualification_rate" in data
        assert "quality_distribution" in data
        
        print("✅ Lead quality analytics API test passed")
    
    def test_analytics_nyc_market_api(self):
        """Test NYC market intelligence API endpoint"""
        response = client.get("/api/v1/analytics/nyc-market?timeRange=7d")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "borough_performance" in data
        assert "zip_code_insights" in data
        assert "market_trends" in data
        
        print("✅ NYC market intelligence API test passed")
    
    def test_b2b_platforms_api(self):
        """Test B2B platforms API endpoint"""
        response = client.get("/api/v1/b2b/platforms")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify platform data structure
        platform = data[0]
        assert "platform_code" in platform
        assert "platform_name" in platform
        assert "delivery_method" in platform
        assert "is_active" in platform
        
        print("✅ B2B platforms API test passed")
    
    def test_websocket_endpoints(self):
        """Test WebSocket endpoints"""
        # Test chat WebSocket
        with client.websocket_connect("/ws/chat") as websocket:
            # Send test message
            websocket.send_json({
                "type": "message",
                "content": "Hello, I'm interested in solar"
            })
            
            # Receive response
            data = websocket.receive_json()
            assert "type" in data
            assert "content" in data
        
        print("✅ WebSocket endpoints test passed")

class TestDataFlowValidation:
    """Data flow validation tests"""
    
    def test_lead_creation_flow(self):
        """Test complete lead creation flow"""
        db = next(get_db())
        
        # Create lead
        lead = Lead(
            first_name="Flow",
            last_name="Test",
            email="flow.test@example.com",
            phone="+1234567893",
            property_address="321 Elm St",
            city="Bronx",
            state="NY",
            zip_code="10451",
            borough="Bronx",
            lead_score=70,
            lead_quality="basic",
            estimated_value=150.0,
            created_at=datetime.utcnow()
        )
        
        db.add(lead)
        db.commit()
        
        # Create conversation
        conversation = LeadConversation(
            lead_id=lead.id,
            conversation_data={"messages": [{"role": "user", "content": "Test message"}]},
            conversation_summary="Test conversation summary",
            sentiment_score=0.7,
            created_at=datetime.utcnow()
        )
        
        db.add(conversation)
        db.commit()
        
        # Create quality history
        quality_history = LeadQualityHistory(
            lead_id=lead.id,
            quality_score=70,
            quality_tier="basic",
            scoring_factors={"bill_amount": 0.2, "timeline": 0.3, "homeowner": 0.5},
            created_at=datetime.utcnow()
        )
        
        db.add(quality_history)
        db.commit()
        
        # Verify complete flow
        saved_lead = db.query(Lead).filter(Lead.email == "flow.test@example.com").first()
        assert saved_lead is not None
        
        saved_conversation = db.query(LeadConversation).filter(
            LeadConversation.lead_id == saved_lead.id
        ).first()
        assert saved_conversation is not None
        
        saved_quality = db.query(LeadQualityHistory).filter(
            LeadQualityHistory.lead_id == saved_lead.id
        ).first()
        assert saved_quality is not None
        
        print("✅ Lead creation flow test passed")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
