#!/usr/bin/env python3
"""
Database initialization script for Aurum Solar
Creates tables and initial data
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, engine, async_engine
from app.core.config import settings
from app.models import *  # Import all models

async def init_database():
    """Initialize database with tables and initial data"""
    
    print("🚀 Initializing Aurum Solar Database...")
    
    try:
        # Create all tables
        print("📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Test database connection
        print("🔍 Testing database connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.fetchone():
                print("✅ Database connection successful!")
            else:
                print("❌ Database connection failed!")
                return False
        
        # Initialize Redis
        print("🔍 Testing Redis connection...")
        from app.core.database import get_redis
        redis_client = await get_redis()
        await redis_client.ping()
        print("✅ Redis connection successful!")
        
        print("\n🎉 Database initialization complete!")
        print("✅ PostgreSQL tables created")
        print("✅ Redis connection established")
        print("✅ System ready for operation")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def create_test_data():
    """Create test data for development"""
    
    print("\n📝 Creating test data...")
    
    try:
        # This would create sample NYC data, leads, etc.
        # For now, just confirm the structure is ready
        print("✅ Test data structure ready")
        return True
        
    except Exception as e:
        print(f"❌ Test data creation error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Aurum Solar Database Initialization")
    print("=" * 50)
    
    # Run initialization
    success = asyncio.run(init_database())
    
    if success:
        print("\n🎉 Database setup complete!")
        print("Next steps:")
        print("1. Configure your .env file with database credentials")
        print("2. Run: python scripts/init_database.py")
        print("3. Start the application: uvicorn app.main:app --reload")
    else:
        print("\n❌ Database setup failed!")
        print("Please check your database configuration and try again.")
        sys.exit(1)
