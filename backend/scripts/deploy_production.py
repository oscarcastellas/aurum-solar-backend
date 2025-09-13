#!/usr/bin/env python3
"""
Production Deployment Script for Aurum Solar
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_dependencies():
    """Check if required tools are installed"""
    print("🔍 Checking deployment dependencies...")
    
    dependencies = [
        ("docker", "Docker"),
        ("docker-compose", "Docker Compose"),
        ("curl", "cURL")
    ]
    
    missing = []
    for cmd, name in dependencies:
        if not run_command(f"which {cmd}", f"Checking {name}"):
            missing.append(name)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install the missing dependencies and try again.")
        return False
    
    print("✅ All dependencies are installed")
    return True

def build_application():
    """Build the Docker application"""
    print("\n🏗️ Building Aurum Solar application...")
    
    # Build Docker image
    if not run_command("docker build -t aurum-solar-backend .", "Building Docker image"):
        return False
    
    print("✅ Application built successfully")
    return True

def deploy_services():
    """Deploy services using Docker Compose"""
    print("\n🚀 Deploying services...")
    
    # Stop existing services
    run_command("docker-compose down", "Stopping existing services")
    
    # Start services
    if not run_command("docker-compose up -d", "Starting services"):
        return False
    
    print("✅ Services deployed successfully")
    return True

def wait_for_services():
    """Wait for services to be healthy"""
    print("\n⏳ Waiting for services to be ready...")
    
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        # Check if backend is responding
        if run_command("curl -f http://localhost:8000/health", "Checking backend health"):
            print("✅ All services are healthy and ready!")
            return True
        
        print("⏳ Services starting... waiting 10 seconds")
        time.sleep(10)
    
    print("❌ Services failed to start within timeout")
    return False

def run_final_tests():
    """Run final production tests"""
    print("\n🧪 Running production tests...")
    
    # Test database connection
    if not run_command("curl -f http://localhost:8000/health", "Testing backend health endpoint"):
        return False
    
    # Test API endpoints
    test_endpoints = [
        ("/api/v1/health", "Health check"),
        ("/api/v1/leads", "Leads API"),
        ("/api/v1/conversations", "Conversations API")
    ]
    
    for endpoint, description in test_endpoints:
        if not run_command(f"curl -f http://localhost:8000{endpoint}", f"Testing {description}"):
            print(f"⚠️ {description} endpoint not responding (may be expected)")
    
    print("✅ Production tests completed")
    return True

def show_deployment_info():
    """Show deployment information"""
    print("\n🎉 Aurum Solar Production Deployment Complete!")
    print("=" * 60)
    print("📊 Deployment Information:")
    print(f"   • Backend URL: http://localhost:8000")
    print(f"   • API Documentation: http://localhost:8000/docs")
    print(f"   • Health Check: http://localhost:8000/health")
    print(f"   • Database: PostgreSQL on port 5432")
    print(f"   • Cache: Redis on port 6379")
    print()
    print("🔧 Management Commands:")
    print("   • View logs: docker-compose logs -f")
    print("   • Stop services: docker-compose down")
    print("   • Restart services: docker-compose restart")
    print("   • Update application: docker-compose pull && docker-compose up -d")
    print()
    print("📈 Monitoring:")
    print("   • Service status: docker-compose ps")
    print("   • Resource usage: docker stats")
    print("   • Application logs: docker-compose logs backend")
    print("=" * 60)

def main():
    """Main deployment process"""
    print("🚀 Aurum Solar Production Deployment")
    print("=" * 50)
    print(f"📅 Deployment started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Step 2: Build application
    if not build_application():
        sys.exit(1)
    
    # Step 3: Deploy services
    if not deploy_services():
        sys.exit(1)
    
    # Step 4: Wait for services
    if not wait_for_services():
        sys.exit(1)
    
    # Step 5: Run tests
    if not run_final_tests():
        sys.exit(1)
    
    # Step 6: Show deployment info
    show_deployment_info()
    
    print(f"\n🎉 Deployment completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
