#!/bin/bash

# Aurum Solar Full Stack Deployment Script
# Deploys user-facing app, admin dashboard, and backend API

echo "🚀 Aurum Solar Full Stack Deployment"
echo "===================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker from https://docker.com/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose"
    exit 1
fi

# Check environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable not set"
    echo "Please set it with: export OPENAI_API_KEY=your_key_here"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  Warning: SECRET_KEY environment variable not set"
    echo "Generating a random secret key..."
    export SECRET_KEY=$(openssl rand -hex 32)
fi

echo "🔧 Environment Configuration:"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:0:20}..."
echo "  SECRET_KEY: ${SECRET_KEY:0:20}..."
echo ""

# Create network if it doesn't exist
echo "🌐 Creating Docker network..."
docker network create aurum-network 2>/dev/null || echo "Network already exists"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.yml down 2>/dev/null
docker-compose -f docker-compose.admin.yml down 2>/dev/null

# Build and start services
echo "🏗️  Building and starting services..."

# Start backend services (database, redis, backend)
echo "📊 Starting backend services..."
docker-compose -f docker-compose.admin.yml up -d postgres redis backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend API is ready"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# Start user-facing frontend
echo "🌐 Starting user-facing frontend..."
if [ -d "aurum-chat-solar-main" ]; then
    cd aurum-chat-solar-main
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    echo "🚀 Starting frontend on port 3001..."
    npm run dev &
    FRONTEND_PID=$!
    cd ..
else
    echo "⚠️  Warning: aurum-chat-solar-main directory not found"
fi

# Start admin dashboard
echo "📊 Starting admin dashboard..."
if [ -d "admin-dashboard" ]; then
    cd admin-dashboard
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing admin dashboard dependencies..."
        npm install
    fi
    echo "🚀 Starting admin dashboard on port 3002..."
    npm run dev &
    ADMIN_PID=$!
    cd ..
else
    echo "⚠️  Warning: admin-dashboard directory not found"
fi

# Wait a moment for services to start
sleep 5

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "🌐 Services running:"
echo "  User-Facing Frontend: http://localhost:3001"
echo "  Admin Dashboard:      http://localhost:3002"
echo "  Backend API:          http://localhost:8000"
echo "  API Documentation:    http://localhost:8000/docs"
echo ""
echo "📊 Health Checks:"
curl -s http://localhost:8000/health > /dev/null && echo "  ✅ Backend API: Healthy" || echo "  ❌ Backend API: Unhealthy"

if [ -n "$FRONTEND_PID" ]; then
    echo "  ✅ User Frontend: Running (PID: $FRONTEND_PID)"
else
    echo "  ❌ User Frontend: Not started"
fi

if [ -n "$ADMIN_PID" ]; then
    echo "  ✅ Admin Dashboard: Running (PID: $ADMIN_PID)"
else
    echo "  ❌ Admin Dashboard: Not started"
fi

echo ""
echo "🔧 Management Commands:"
echo "  Stop all services:    docker-compose -f docker-compose.admin.yml down"
echo "  View logs:            docker-compose -f docker-compose.admin.yml logs -f"
echo "  Restart backend:      docker-compose -f docker-compose.admin.yml restart backend"
echo ""
echo "📚 Documentation:"
echo "  Deployment Guide:     ./DEPLOYMENT_ARCHITECTURE.md"
echo "  API Documentation:    http://localhost:8000/docs"
echo ""

# Keep script running and show logs
echo "📋 Showing backend logs (Press Ctrl+C to stop)..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    if [ -n "$ADMIN_PID" ]; then
        kill $ADMIN_PID 2>/dev/null
    fi
    docker-compose -f docker-compose.admin.yml down
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Show logs
docker-compose -f docker-compose.admin.yml logs -f
