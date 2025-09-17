#!/bin/bash

# Railway Deployment Script for Aurum Solar Backend
# This script deploys the Railway-optimized backend

echo "🚀 Starting Railway deployment for Aurum Solar Backend..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run: railway login"
    exit 1
fi

echo "✅ Railway CLI found and authenticated"

# Copy optimized files
echo "📋 Setting up Railway-optimized configuration..."

# Use the Railway-optimized files
cp railway-optimized.json railway.json
cp Dockerfile.railway Dockerfile
cp requirements-railway.txt requirements.txt

echo "✅ Configuration files updated"

# Deploy to Railway
echo "🚀 Deploying to Railway..."

# Deploy with the optimized configuration
railway up --detach

if [ $? -eq 0 ]; then
    echo "✅ Deployment initiated successfully!"
    echo ""
    echo "📊 Deployment Details:"
    echo "   - Application: main_railway.py"
    echo "   - Dockerfile: Dockerfile.railway"
    echo "   - Requirements: requirements-railway.txt"
    echo ""
    echo "🔍 Next Steps:"
    echo "   1. Check deployment status: railway logs"
    echo "   2. Get domain: railway domain"
    echo "   3. Test health: curl https://your-domain.up.railway.app/health"
    echo ""
    echo "🌐 Your backend will be available at:"
    railway domain
else
    echo "❌ Deployment failed. Check the logs above for details."
    exit 1
fi
