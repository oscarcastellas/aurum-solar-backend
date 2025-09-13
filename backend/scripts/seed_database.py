"""
Database seeding script for development
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.lead import Lead, LeadExport
from app.models.analytics import RevenueMetrics, PlatformPerformance, NYCMarketIntelligence
from app.models.auth import User
from app.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_sample_data():
    """Create sample data for development"""
    
    db = SessionLocal()
    
    try:
        # Create sample user
        user = User(
            email="admin@aurumsolar.com",
            hashed_password=pwd_context.hash("admin123"),
            full_name="Admin User",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Create sample leads
        sample_leads = [
            {
                "email": "john.doe@example.com",
                "phone": "(555) 123-4567",
                "first_name": "John",
                "last_name": "Doe",
                "property_address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "roof_type": "asphalt",
                "roof_condition": "good",
                "monthly_electric_bill": 150.0,
                "property_type": "residential",
                "square_footage": 2000,
                "lead_score": 85,
                "lead_quality": "hot",
                "status": "qualified",
                "source": "website",
                "estimated_value": 200.0,
                "ai_insights": "High-value lead with excellent solar potential. Property in prime NYC location with good roof condition."
            },
            {
                "email": "jane.smith@example.com",
                "phone": "(555) 234-5678",
                "first_name": "Jane",
                "last_name": "Smith",
                "property_address": "456 Oak Ave",
                "city": "Brooklyn",
                "state": "NY",
                "zip_code": "11201",
                "roof_type": "metal",
                "roof_condition": "excellent",
                "monthly_electric_bill": 200.0,
                "property_type": "residential",
                "square_footage": 2500,
                "lead_score": 92,
                "lead_quality": "hot",
                "status": "exported",
                "source": "referral",
                "estimated_value": 250.0,
                "exported_to": ["solarreviews"],
                "ai_insights": "Premium lead with exceptional solar potential. High electric bill indicates strong ROI potential."
            },
            {
                "email": "bob.johnson@example.com",
                "phone": "(555) 345-6789",
                "first_name": "Bob",
                "last_name": "Johnson",
                "property_address": "789 Pine St",
                "city": "Queens",
                "state": "NY",
                "zip_code": "11375",
                "roof_type": "asphalt",
                "roof_condition": "fair",
                "monthly_electric_bill": 120.0,
                "property_type": "residential",
                "square_footage": 1800,
                "lead_score": 65,
                "lead_quality": "warm",
                "status": "new",
                "source": "social_media",
                "estimated_value": 150.0,
                "ai_insights": "Good lead with moderate solar potential. Roof condition may need assessment."
            }
        ]
        
        for lead_data in sample_leads:
            lead = Lead(**lead_data)
            db.add(lead)
        
        db.commit()
        
        # Create sample revenue metrics
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            revenue_metric = RevenueMetrics(
                date=date,
                total_leads=random.randint(10, 50),
                qualified_leads=random.randint(5, 25),
                exported_leads=random.randint(3, 20),
                sold_leads=random.randint(1, 10),
                total_revenue=random.uniform(1000, 5000),
                average_lead_value=random.uniform(100, 300),
                commission_earned=random.uniform(150, 750)
            )
            db.add(revenue_metric)
        
        db.commit()
        
        # Create sample platform performance
        platforms = ["solarreviews", "modernize"]
        for platform in platforms:
            for i in range(7):
                date = datetime.utcnow() - timedelta(days=i)
                platform_perf = PlatformPerformance(
                    platform=platform,
                    date=date,
                    leads_exported=random.randint(5, 20),
                    leads_accepted=random.randint(3, 15),
                    leads_rejected=random.randint(1, 5),
                    total_revenue=random.uniform(500, 2000),
                    average_price_per_lead=random.uniform(150, 250),
                    commission_earned=random.uniform(75, 300)
                )
                db.add(platform_perf)
        
        db.commit()
        
        # Create sample NYC market intelligence
        nyc_zip_codes = [
            {"zip_code": "10001", "borough": "Manhattan"},
            {"zip_code": "11201", "borough": "Brooklyn"},
            {"zip_code": "11375", "borough": "Queens"},
            {"zip_code": "10451", "borough": "Bronx"},
            {"zip_code": "10301", "borough": "Staten Island"}
        ]
        
        for zip_data in nyc_zip_codes:
            intelligence = NYCMarketIntelligence(
                zip_code=zip_data["zip_code"],
                borough=zip_data["borough"],
                average_roof_size=random.uniform(1500, 3000),
                average_electric_bill=random.uniform(100, 250),
                solar_adoption_rate=random.uniform(0.05, 0.15),
                average_system_size=random.uniform(5, 10),
                average_installation_cost=random.uniform(15000, 30000),
                average_savings_per_month=random.uniform(100, 300),
                payback_period_years=random.uniform(5, 10),
                competitor_count=random.randint(5, 15),
                market_saturation=random.uniform(0.1, 0.4),
                high_value_zip_codes=random.choice([True, False]),
                conversion_rate=random.uniform(0.1, 0.3)
            )
            db.add(intelligence)
        
        db.commit()
        
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
