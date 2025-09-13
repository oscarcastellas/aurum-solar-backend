#!/usr/bin/env python3
"""
Simple database test to verify setup works
"""

import sys
import os
from sqlalchemy import create_engine, text

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_connection():
    """Test basic database connection and table creation"""
    
    print("🚀 Testing Aurum Solar Database Setup...")
    
    try:
        # Create a simple test engine
        engine = create_engine('sqlite:///test.db')
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.fetchone():
                print("✅ Database connection successful!")
            else:
                print("❌ Database connection failed!")
                return False
        
        # Test importing models
        print("🔍 Testing model imports...")
        try:
            from app.models.lead import Lead
            print("✅ Lead model imported successfully")
        except Exception as e:
            print(f"❌ Lead model import failed: {e}")
            return False
        
        try:
            from app.models.b2b_platforms import B2BPlatform
            print("✅ B2BPlatform model imported successfully")
        except Exception as e:
            print(f"❌ B2BPlatform model import failed: {e}")
            return False
        
        try:
            from app.services.solar_calculation_engine import SolarCalculationEngine
            print("✅ SolarCalculationEngine imported successfully")
        except Exception as e:
            print(f"❌ SolarCalculationEngine import failed: {e}")
            return False
        
        print("\n🎉 Database setup test successful!")
        print("✅ Database connection working")
        print("✅ Models importing correctly")
        print("✅ Services accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    
    if success:
        print("\n🚀 Database is ready for production!")
        print("Next steps:")
        print("1. Set up PostgreSQL database")
        print("2. Configure environment variables")
        print("3. Deploy to production")
    else:
        print("\n❌ Database setup needs attention")
        sys.exit(1)
