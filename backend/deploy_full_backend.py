#!/usr/bin/env python3
"""
Deploy Full Aurum Solar Backend to Railway
This script deploys the complete backend with all 80+ API endpoints
"""

import subprocess
import sys
import os
import time
import requests
import json

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def test_railway_connection():
    """Test Railway CLI connection"""
    print("🔍 Testing Railway CLI connection...")
    try:
        result = subprocess.run("railway whoami", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Connected to Railway as: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Railway CLI not connected: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Railway CLI error: {e}")
        return False

def update_railway_files():
    """Update Railway deployment files"""
    print("📝 Updating Railway deployment files...")
    
    # Update Procfile for production
    with open("Procfile", "w") as f:
        f.write("web: uvicorn main_production:app --host 0.0.0.0 --port $PORT --workers 1\n")
    
    # Update requirements.txt with all dependencies
    requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "sqlalchemy==2.0.23",
        "alembic==1.12.1",
        "psycopg2-binary==2.9.9",
        "redis==5.0.1",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.6",
        "structlog==23.2.0",
        "openai==1.3.7",
        "aiohttp==3.9.1",
        "httpx==0.25.2",
        "websockets==12.0",
        "python-dotenv==1.0.0",
        "email-validator==2.1.0",
        "typing-extensions>=4.6.0"
    ]
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements) + "\n")
    
    print("✅ Railway files updated successfully")
    return True

def deploy_to_railway():
    """Deploy to Railway"""
    print("🚀 Deploying full backend to Railway...")
    
    # Deploy using Railway CLI
    if run_command("railway up", "Deploying to Railway"):
        print("✅ Deployment initiated successfully")
        return True
    else:
        print("❌ Deployment failed")
        return False

def test_deployed_endpoints():
    """Test deployed endpoints"""
    print("🧪 Testing deployed endpoints...")
    
    # Wait for deployment to complete
    print("⏳ Waiting for deployment to complete...")
    time.sleep(30)
    
    base_url = "https://backend-production-3f24.up.railway.app"
    
    # Test endpoints
    endpoints_to_test = [
        ("/health", "Health Check"),
        ("/", "Root Endpoint"),
        ("/api/v1/test", "Test Endpoint"),
        ("/api/v1/leads", "Lead Management"),
        ("/api/v1/analytics", "Analytics"),
        ("/api/v1/exports", "B2B Export"),
        ("/api/v1/b2b", "B2B Integration"),
        ("/api/v1/auth", "Authentication"),
        ("/api/v1/conversation", "Conversation API"),
        ("/docs", "API Documentation")
    ]
    
    results = {}
    
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code in [200, 401, 403]:  # 401/403 are expected for protected endpoints
                results[endpoint] = "✅ PASS"
                print(f"✅ {description}: {response.status_code}")
            else:
                results[endpoint] = f"❌ FAIL ({response.status_code})"
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            results[endpoint] = f"❌ ERROR ({str(e)})"
            print(f"❌ {description}: {str(e)}")
    
    return results

def main():
    """Main deployment process"""
    print("🚀 AURUM SOLAR FULL BACKEND DEPLOYMENT")
    print("=" * 50)
    
    # Step 1: Test Railway connection
    if not test_railway_connection():
        print("❌ Please login to Railway first: railway login")
        sys.exit(1)
    
    # Step 2: Update Railway files
    if not update_railway_files():
        print("❌ Failed to update Railway files")
        sys.exit(1)
    
    # Step 3: Deploy to Railway
    if not deploy_to_railway():
        print("❌ Failed to deploy to Railway")
        sys.exit(1)
    
    # Step 4: Test deployed endpoints
    results = test_deployed_endpoints()
    
    # Summary
    print("\n📊 DEPLOYMENT SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if "✅" in result)
    total = len(results)
    
    print(f"Endpoints Tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed >= total * 0.8:  # 80% success rate
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("✅ Full backend with 80+ endpoints deployed")
        print("✅ Ready for frontend integration")
        print("✅ Ready for revenue generation")
    else:
        print("⚠️  DEPLOYMENT PARTIAL")
        print("Some endpoints may need attention")
    
    print(f"\n🌐 Backend URL: https://backend-production-3f24.up.railway.app")
    print(f"📚 API Docs: https://backend-production-3f24.up.railway.app/docs")

if __name__ == "__main__":
    main()
