"""
NYC market intelligence seed data
Populates NYC-specific data for solar market analysis
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random
import json

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.nyc_data import NYCZipCode, NYCIncentive, NYCDemographic, NYCElectricRate
from app.models.b2b_platforms import B2BPlatform
from app.models.ai_models import AIModel
from app.models.auth import User, UserPermission
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_nyc_zip_codes():
    """Seed NYC zip codes with market intelligence data"""
    
    db = SessionLocal()
    
    try:
        # NYC zip codes with comprehensive data
        nyc_zip_data = [
            {
                "zip_code": "10001",
                "borough": "Manhattan",
                "neighborhood": "Chelsea",
                "latitude": 40.7505,
                "longitude": -73.9934,
                "area_sq_miles": 0.8,
                "total_population": 45000,
                "median_age": 38.5,
                "median_household_income": 125000,
                "homeownership_rate": 0.25,
                "average_home_value": 1200000,
                "average_rent": 3500,
                "total_housing_units": 22000,
                "single_family_homes": 500,
                "multi_family_homes": 21500,
                "average_home_age": 85,
                "average_home_size_sqft": 1200,
                "solar_adoption_rate": 0.08,
                "total_solar_installations": 45,
                "average_system_size_kw": 8.5,
                "average_installation_cost": 25000,
                "average_savings_per_month": 180,
                "average_payback_period_years": 8.5,
                "primary_electric_provider": "ConEd",
                "average_electric_rate_per_kwh": 0.28,
                "average_monthly_bill": 220,
                "peak_demand_charges": 15.50,
                "solar_potential_score": 75,
                "average_roof_size_sqft": 2000,
                "average_roof_condition": "good",
                "shading_factor": 0.3,
                "roof_orientation_score": 85,
                "solar_installers_count": 12,
                "market_saturation": 0.15,
                "competition_intensity": "high",
                "state_incentives_available": True,
                "local_incentives_available": True,
                "net_metering_available": True,
                "community_solar_available": True,
                "high_value_zip_code": True,
                "conversion_rate": 0.18,
                "average_lead_value": 280,
                "lead_volume_per_month": 25,
                "data_source": "NYC Open Data + Solar Industry Reports",
                "data_confidence": 0.92
            },
            {
                "zip_code": "11201",
                "borough": "Brooklyn",
                "neighborhood": "DUMBO",
                "latitude": 40.7033,
                "longitude": -73.9881,
                "area_sq_miles": 0.3,
                "total_population": 12000,
                "median_age": 35.2,
                "median_household_income": 145000,
                "homeownership_rate": 0.35,
                "average_home_value": 950000,
                "average_rent": 3200,
                "total_housing_units": 8000,
                "single_family_homes": 200,
                "multi_family_homes": 7800,
                "average_home_age": 95,
                "average_home_size_sqft": 1100,
                "solar_adoption_rate": 0.12,
                "total_solar_installations": 28,
                "average_system_size_kw": 7.8,
                "average_installation_cost": 22000,
                "average_savings_per_month": 165,
                "average_payback_period_years": 7.2,
                "primary_electric_provider": "ConEd",
                "average_electric_rate_per_kwh": 0.26,
                "average_monthly_bill": 195,
                "peak_demand_charges": 14.20,
                "solar_potential_score": 82,
                "average_roof_size_sqft": 1800,
                "average_roof_condition": "excellent",
                "shading_factor": 0.2,
                "roof_orientation_score": 90,
                "solar_installers_count": 8,
                "market_saturation": 0.08,
                "competition_intensity": "medium",
                "state_incentives_available": True,
                "local_incentives_available": True,
                "net_metering_available": True,
                "community_solar_available": True,
                "high_value_zip_code": True,
                "conversion_rate": 0.22,
                "average_lead_value": 320,
                "lead_volume_per_month": 18,
                "data_source": "NYC Open Data + Solar Industry Reports",
                "data_confidence": 0.88
            },
            {
                "zip_code": "11375",
                "borough": "Queens",
                "neighborhood": "Forest Hills",
                "latitude": 40.7209,
                "longitude": -73.8448,
                "area_sq_miles": 2.1,
                "total_population": 85000,
                "median_age": 42.1,
                "median_household_income": 85000,
                "homeownership_rate": 0.65,
                "average_home_value": 650000,
                "average_rent": 2200,
                "total_housing_units": 35000,
                "single_family_homes": 12000,
                "multi_family_homes": 23000,
                "average_home_age": 45,
                "average_home_size_sqft": 1800,
                "solar_adoption_rate": 0.15,
                "total_solar_installations": 125,
                "average_system_size_kw": 9.2,
                "average_installation_cost": 20000,
                "average_savings_per_month": 140,
                "average_payback_period_years": 6.8,
                "primary_electric_provider": "ConEd",
                "average_electric_rate_per_kwh": 0.24,
                "average_monthly_bill": 165,
                "peak_demand_charges": 12.80,
                "solar_potential_score": 88,
                "average_roof_size_sqft": 2500,
                "average_roof_condition": "good",
                "shading_factor": 0.15,
                "roof_orientation_score": 92,
                "solar_installers_count": 15,
                "market_saturation": 0.12,
                "competition_intensity": "medium",
                "state_incentives_available": True,
                "local_incentives_available": False,
                "net_metering_available": True,
                "community_solar_available": True,
                "high_value_zip_code": True,
                "conversion_rate": 0.25,
                "average_lead_value": 250,
                "lead_volume_per_month": 35,
                "data_source": "NYC Open Data + Solar Industry Reports",
                "data_confidence": 0.90
            },
            {
                "zip_code": "10451",
                "borough": "Bronx",
                "neighborhood": "South Bronx",
                "latitude": 40.8176,
                "longitude": -73.9442,
                "area_sq_miles": 1.2,
                "total_population": 65000,
                "median_age": 35.8,
                "median_household_income": 45000,
                "homeownership_rate": 0.15,
                "average_home_value": 350000,
                "average_rent": 1800,
                "total_housing_units": 28000,
                "single_family_homes": 2000,
                "multi_family_homes": 26000,
                "average_home_age": 75,
                "average_home_size_sqft": 900,
                "solar_adoption_rate": 0.03,
                "total_solar_installations": 8,
                "average_system_size_kw": 6.5,
                "average_installation_cost": 18000,
                "average_savings_per_month": 95,
                "average_payback_period_years": 9.2,
                "primary_electric_provider": "ConEd",
                "average_electric_rate_per_kwh": 0.22,
                "average_monthly_bill": 120,
                "peak_demand_charges": 10.50,
                "solar_potential_score": 65,
                "average_roof_size_sqft": 1200,
                "average_roof_condition": "fair",
                "shading_factor": 0.4,
                "roof_orientation_score": 70,
                "solar_installers_count": 3,
                "market_saturation": 0.02,
                "competition_intensity": "low",
                "state_incentives_available": True,
                "local_incentives_available": True,
                "net_metering_available": True,
                "community_solar_available": True,
                "high_value_zip_code": False,
                "conversion_rate": 0.08,
                "average_lead_value": 150,
                "lead_volume_per_month": 12,
                "data_source": "NYC Open Data + Solar Industry Reports",
                "data_confidence": 0.75
            },
            {
                "zip_code": "10301",
                "borough": "Staten Island",
                "neighborhood": "St. George",
                "latitude": 40.6431,
                "longitude": -74.0776,
                "area_sq_miles": 3.2,
                "total_population": 25000,
                "median_age": 40.5,
                "median_household_income": 75000,
                "homeownership_rate": 0.55,
                "average_home_value": 550000,
                "average_rent": 2000,
                "total_housing_units": 12000,
                "single_family_homes": 8000,
                "multi_family_homes": 4000,
                "average_home_age": 35,
                "average_home_size_sqft": 2200,
                "solar_adoption_rate": 0.18,
                "total_solar_installations": 45,
                "average_system_size_kw": 10.5,
                "average_installation_cost": 23000,
                "average_savings_per_month": 175,
                "average_payback_period_years": 6.5,
                "primary_electric_provider": "ConEd",
                "average_electric_rate_per_kwh": 0.25,
                "average_monthly_bill": 180,
                "peak_demand_charges": 13.20,
                "solar_potential_score": 92,
                "average_roof_size_sqft": 3000,
                "average_roof_condition": "excellent",
                "shading_factor": 0.1,
                "roof_orientation_score": 95,
                "solar_installers_count": 6,
                "market_saturation": 0.10,
                "competition_intensity": "low",
                "state_incentives_available": True,
                "local_incentives_available": False,
                "net_metering_available": True,
                "community_solar_available": False,
                "high_value_zip_code": True,
                "conversion_rate": 0.28,
                "average_lead_value": 290,
                "lead_volume_per_month": 22,
                "data_source": "NYC Open Data + Solar Industry Reports",
                "data_confidence": 0.85
            }
        ]
        
        for zip_data in nyc_zip_data:
            zip_code = NYCZipCode(**zip_data)
            db.add(zip_code)
        
        db.commit()
        print(f"Successfully seeded {len(nyc_zip_data)} NYC zip codes")
        
    except Exception as e:
        print(f"Error seeding NYC zip codes: {e}")
        db.rollback()
    finally:
        db.close()


def seed_nyc_incentives():
    """Seed NYC solar incentives data"""
    
    db = SessionLocal()
    
    try:
        # Get zip codes for foreign key relationships
        zip_codes = db.query(NYCZipCode).all()
        
        incentives_data = [
            {
                "zip_code_id": zip_codes[0].id,  # 10001
                "incentive_name": "NY-Sun Solar Incentive",
                "incentive_type": "state",
                "incentive_category": "rebate",
                "incentive_amount": 0.50,  # per watt
                "max_incentive_amount": 5000,
                "eligibility_criteria": {
                    "min_system_size": 1,
                    "max_system_size": 25,
                    "property_type": ["residential", "commercial"],
                    "income_limits": None
                },
                "is_active": True,
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 12, 31),
                "total_applications": 150,
                "total_amount_awarded": 75000,
                "remaining_funding": 25000
            },
            {
                "zip_code_id": zip_codes[0].id,  # 10001
                "incentive_name": "Federal Solar Tax Credit",
                "incentive_type": "federal",
                "incentive_category": "tax_credit",
                "incentive_percentage": 30,
                "max_incentive_amount": None,
                "eligibility_criteria": {
                    "min_system_size": 1,
                    "max_system_size": None,
                    "property_type": ["residential", "commercial"],
                    "income_limits": None
                },
                "is_active": True,
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2032, 12, 31),
                "total_applications": 300,
                "total_amount_awarded": 150000,
                "remaining_funding": None
            },
            {
                "zip_code_id": zip_codes[1].id,  # 11201
                "incentive_name": "Brooklyn Solar Initiative",
                "incentive_type": "local",
                "incentive_category": "grant",
                "incentive_amount": 2000,
                "max_incentive_amount": 2000,
                "eligibility_criteria": {
                    "min_system_size": 3,
                    "max_system_size": 15,
                    "property_type": ["residential"],
                    "income_limits": {"max_income": 80000}
                },
                "is_active": True,
                "start_date": datetime(2024, 3, 1),
                "end_date": datetime(2024, 11, 30),
                "total_applications": 45,
                "total_amount_awarded": 90000,
                "remaining_funding": 10000
            }
        ]
        
        for incentive_data in incentives_data:
            incentive = NYCIncentive(**incentive_data)
            db.add(incentive)
        
        db.commit()
        print(f"Successfully seeded {len(incentives_data)} NYC incentives")
        
    except Exception as e:
        print(f"Error seeding NYC incentives: {e}")
        db.rollback()
    finally:
        db.close()


def seed_b2b_platforms():
    """Seed B2B platform data"""
    
    db = SessionLocal()
    
    try:
        platforms_data = [
            {
                "platform_name": "SolarReviews",
                "platform_code": "solarreviews",
                "platform_type": "lead_buyer",
                "api_base_url": "https://api.solarreviews.com/v1",
                "api_version": "v1",
                "authentication_type": "api_key",
                "min_lead_score": 70,
                "max_lead_score": 100,
                "accepted_lead_qualities": ["hot", "warm"],
                "base_price_per_lead": 150.0,
                "price_tiers": {
                    "hot": 200.0,
                    "warm": 150.0,
                    "cold": 100.0
                },
                "commission_rate": 0.15,
                "required_fields": ["email", "phone", "property_address", "zip_code"],
                "supports_bulk_export": True,
                "supports_real_time_export": True,
                "max_export_batch_size": 50,
                "is_active": True,
                "is_accepting_leads": True
            },
            {
                "platform_name": "Modernize",
                "platform_code": "modernize",
                "platform_type": "lead_buyer",
                "api_base_url": "https://api.modernize.com/v1",
                "api_version": "v1",
                "authentication_type": "api_key",
                "min_lead_score": 60,
                "max_lead_score": 100,
                "accepted_lead_qualities": ["hot", "warm", "cold"],
                "base_price_per_lead": 200.0,
                "price_tiers": {
                    "hot": 250.0,
                    "warm": 200.0,
                    "cold": 150.0
                },
                "commission_rate": 0.18,
                "required_fields": ["email", "phone", "property_address", "zip_code", "monthly_electric_bill"],
                "supports_bulk_export": True,
                "supports_real_time_export": True,
                "max_export_batch_size": 100,
                "is_active": True,
                "is_accepting_leads": True
            }
        ]
        
        for platform_data in platforms_data:
            platform = B2BPlatform(**platform_data)
            db.add(platform)
        
        db.commit()
        print(f"Successfully seeded {len(platforms_data)} B2B platforms")
        
    except Exception as e:
        print(f"Error seeding B2B platforms: {e}")
        db.rollback()
    finally:
        db.close()


def seed_ai_models():
    """Seed AI model configurations"""
    
    db = SessionLocal()
    
    try:
        ai_models_data = [
            {
                "model_name": "GPT-4 Lead Analysis",
                "model_type": "lead_analysis",
                "model_provider": "openai",
                "model_version": "gpt-4",
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "model_parameters": {
                    "temperature": 0.3,
                    "max_tokens": 1000,
                    "top_p": 0.9
                },
                "prompt_templates": {
                    "lead_analysis": "Analyze this solar lead for the NYC market...",
                    "conversation": "You are a solar energy consultant for NYC...",
                    "scoring": "Score this lead based on solar potential..."
                },
                "is_active": True,
                "is_primary": True,
                "daily_request_limit": 1000,
                "monthly_request_limit": 30000
            },
            {
                "model_name": "GPT-3.5 Conversation",
                "model_type": "conversation",
                "model_provider": "openai",
                "model_version": "gpt-3.5-turbo",
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "model_parameters": {
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "top_p": 0.9
                },
                "prompt_templates": {
                    "conversation": "You are a helpful solar consultant...",
                    "questions": "Generate follow-up questions for this lead..."
                },
                "is_active": True,
                "is_primary": False,
                "daily_request_limit": 2000,
                "monthly_request_limit": 60000
            }
        ]
        
        for model_data in ai_models_data:
            ai_model = AIModel(**model_data)
            db.add(ai_model)
        
        db.commit()
        print(f"Successfully seeded {len(ai_models_data)} AI models")
        
    except Exception as e:
        print(f"Error seeding AI models: {e}")
        db.rollback()
    finally:
        db.close()


def seed_users_and_permissions():
    """Seed users and permissions"""
    
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = User(
            email="admin@aurumsolar.com",
            hashed_password=pwd_context.hash("admin123"),
            full_name="Admin User",
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_verified=True,
            is_superuser=True,
            email_verified=True
        )
        db.add(admin_user)
        
        # Create demo user
        demo_user = User(
            email="demo@aurumsolar.com",
            hashed_password=pwd_context.hash("demo123"),
            full_name="Demo User",
            first_name="Demo",
            last_name="User",
            is_active=True,
            is_verified=True,
            is_superuser=False,
            email_verified=True
        )
        db.add(demo_user)
        
        db.commit()
        
        # Create permissions
        permissions_data = [
            {"permission_name": "leads.create", "permission_category": "leads", "resource": "leads", "action": "create"},
            {"permission_name": "leads.read", "permission_category": "leads", "resource": "leads", "action": "read"},
            {"permission_name": "leads.update", "permission_category": "leads", "resource": "leads", "action": "update"},
            {"permission_name": "leads.delete", "permission_category": "leads", "resource": "leads", "action": "delete"},
            {"permission_name": "analytics.read", "permission_category": "analytics", "resource": "analytics", "action": "read"},
            {"permission_name": "exports.create", "permission_category": "exports", "resource": "exports", "action": "create"},
            {"permission_name": "exports.read", "permission_category": "exports", "resource": "exports", "action": "read"},
            {"permission_name": "ai.chat", "permission_category": "ai", "resource": "ai", "action": "chat"},
            {"permission_name": "ai.analyze", "permission_category": "ai", "resource": "ai", "action": "analyze"},
        ]
        
        for perm_data in permissions_data:
            permission = UserPermission(**perm_data)
            db.add(permission)
        
        db.commit()
        print("Successfully seeded users and permissions")
        
    except Exception as e:
        print(f"Error seeding users and permissions: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Run all seed functions"""
    print("Starting NYC market intelligence data seeding...")
    
    seed_nyc_zip_codes()
    seed_nyc_incentives()
    seed_b2b_platforms()
    seed_ai_models()
    seed_users_and_permissions()
    
    print("NYC market intelligence data seeding completed!")


if __name__ == "__main__":
    main()
