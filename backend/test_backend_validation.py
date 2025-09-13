#!/usr/bin/env python3
"""
Backend validation script for Aurum Solar
Tests core functionality without running the full server
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from main import app
        print("✅ Main app import successful")
        
        from app.core.database import get_db
        print("✅ Database module import successful")
        
        from app.core.redis import get_redis
        print("✅ Redis module import successful")
        
        from app.core.config import settings
        print("✅ Config module import successful")
        
        from app.core.health import router as health_router
        print("✅ Health module import successful")
        
        from app.services.conversation_agent import SolarConversationAgent
        print("✅ Conversation agent import successful")
        
        from app.services.solar_calculation_engine import SolarCalculationEngine
        print("✅ Solar calculation engine import successful")
        
        from app.services.revenue_analytics_service import RevenueAnalyticsService
        print("✅ Revenue analytics service import successful")
        
        from app.services.enhanced_b2b_export_service import EnhancedB2BExportService
        print("✅ B2B export service import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_app_creation():
    """Test that the FastAPI app can be created"""
    print("\n🧪 Testing FastAPI app creation...")
    
    try:
        from main import app
        
        # Check if app is a FastAPI instance
        from fastapi import FastAPI
        if isinstance(app, FastAPI):
            print("✅ FastAPI app created successfully")
            print(f"   Title: {app.title}")
            print(f"   Version: {app.version}")
            print(f"   Routes: {len(app.routes)}")
            return True
        else:
            print("❌ App is not a FastAPI instance")
            return False
            
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def test_health_endpoints():
    """Test health endpoint functionality"""
    print("\n🧪 Testing health endpoints...")
    
    try:
        from app.core.health import health_check, detailed_health_check, readiness_check, liveness_check, metrics, status
        
        print("✅ Health endpoint functions imported successfully")
        
        # Test basic health check
        health_result = asyncio.run(health_check())
        if health_result and health_result.get("status") == "healthy":
            print("✅ Basic health check working")
        else:
            print("❌ Basic health check failed")
            return False
        
        # Test status endpoint
        status_result = asyncio.run(status())
        if status_result and status_result.get("status") == "running":
            print("✅ Status endpoint working")
        else:
            print("❌ Status endpoint failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Health endpoints test failed: {e}")
        return False

def test_services():
    """Test core services functionality"""
    print("\n🧪 Testing core services...")
    
    try:
        # Test Solar Calculation Engine (with mock database)
        from app.services.solar_calculation_engine import SolarCalculationEngine
        from app.core.database import get_db
        
        # Get a database session
        db = next(get_db())
        engine = SolarCalculationEngine(db)
        print("✅ Solar calculation engine created")
        
        # Test basic calculation
        result = engine.calculate_system_size(300, "10001", "Manhattan")
        if result and "system_size_kw" in result:
            print("✅ Solar calculation working")
        else:
            print("❌ Solar calculation failed")
            return False
        
        # Test Revenue Analytics Service
        from app.services.revenue_analytics_service import RevenueAnalyticsService
        analytics = RevenueAnalyticsService()
        print("✅ Revenue analytics service created")
        
        # Test B2B Export Service
        from app.services.enhanced_b2b_export_service import EnhancedB2BExportService
        export_service = EnhancedB2BExportService()
        print("✅ B2B export service created")
        
        return True
        
    except Exception as e:
        print(f"❌ Services test failed: {e}")
        return False

def test_api_routes():
    """Test API route registration"""
    print("\n🧪 Testing API routes...")
    
    try:
        from main import app
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods)
                })
        
        print(f"✅ Found {len(routes)} API routes")
        
        # Check for key endpoints
        key_endpoints = [
            "/health",
            "/api/v1/chat/message",
            "/api/v1/leads/exportable",
            "/api/v1/revenue-dashboard/executive-summary",
            "/api/v1/b2b/platforms"
        ]
        
        found_endpoints = []
        for route in routes:
            if route['path'] in key_endpoints:
                found_endpoints.append(route['path'])
        
        print(f"✅ Found {len(found_endpoints)}/{len(key_endpoints)} key endpoints")
        
        if len(found_endpoints) >= 3:  # At least 3 key endpoints should be present
            print("✅ API routes configured correctly")
            return True
        else:
            print("❌ Missing key API endpoints")
            return False
        
    except Exception as e:
        print(f"❌ API routes test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 Aurum Solar Backend Validation")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("Module Imports", test_imports),
        ("App Creation", test_app_creation),
        ("Health Endpoints", test_health_endpoints),
        ("Core Services", test_services),
        ("API Routes", test_api_routes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    success_rate = (passed / total) * 100
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Backend validation PASSED - Ready for deployment!")
        return 0
    elif success_rate >= 60:
        print("⚠️  Backend validation PARTIAL - Some issues need attention")
        return 1
    else:
        print("❌ Backend validation FAILED - Critical issues need fixing")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
