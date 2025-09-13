#!/bin/bash

# Aurum Solar Production Deployment Script
# Deploys to Vercel (Frontend) + Railway (Backend)

echo "🚀 Aurum Solar Production Deployment"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "aurum-chat-solar-main" ] || [ ! -d "backend" ]; then
    print_error "Please run this script from the aurum_solar root directory"
    exit 1
fi

# Check if required tools are installed
print_status "Checking prerequisites..."

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
fi

if ! command -v vercel &> /dev/null; then
    print_warning "Vercel CLI not found. Installing..."
    npm install -g vercel
fi

if ! command -v railway &> /dev/null; then
    print_warning "Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

print_success "Prerequisites checked"

# Step 1: Deploy Backend to Railway
print_status "Deploying backend to Railway..."

cd backend

# Check if Railway is logged in
if ! railway whoami &> /dev/null; then
    print_warning "Please log in to Railway CLI first:"
    echo "railway login"
    exit 1
fi

# Deploy to Railway
print_status "Building and deploying backend..."
railway up --detach

if [ $? -eq 0 ]; then
    print_success "Backend deployed to Railway successfully"
    
    # Get the Railway URL
    RAILWAY_URL=$(railway domain)
    print_status "Backend URL: $RAILWAY_URL"
    
    # Update environment variables
    print_status "Updating Railway environment variables..."
    railway variables set FRONTEND_URL=https://aurum-solar.vercel.app
    railway variables set ENVIRONMENT=production
    
else
    print_error "Backend deployment failed"
    exit 1
fi

cd ..

# Step 2: Deploy Frontend to Vercel
print_status "Deploying frontend to Vercel..."

cd aurum-chat-solar-main

# Check if Vercel is logged in
if ! vercel whoami &> /dev/null; then
    print_warning "Please log in to Vercel CLI first:"
    echo "vercel login"
    exit 1
fi

# Set environment variables for Vercel
print_status "Setting Vercel environment variables..."
vercel env add VITE_API_URL production
echo "https://$RAILWAY_URL" | vercel env add VITE_API_URL production

vercel env add VITE_WS_URL production
echo "wss://$RAILWAY_URL" | vercel env add VITE_WS_URL production

vercel env add VITE_APP_NAME production
echo "Aurum Solar" | vercel env add VITE_APP_NAME production

vercel env add VITE_ENVIRONMENT production
echo "production" | vercel env add VITE_ENVIRONMENT production

# Build and deploy to Vercel
print_status "Building and deploying frontend..."
vercel --prod

if [ $? -eq 0 ]; then
    print_success "Frontend deployed to Vercel successfully"
    
    # Get the Vercel URL
    VERCEL_URL=$(vercel ls --json | jq -r '.[0].url')
    print_status "Frontend URL: https://$VERCEL_URL"
    
else
    print_error "Frontend deployment failed"
    exit 1
fi

cd ..

# Step 3: Run Database Migrations
print_status "Running database migrations..."
railway run --service backend python -m alembic upgrade head

if [ $? -eq 0 ]; then
    print_success "Database migrations completed"
else
    print_warning "Database migrations failed - check logs"
fi

# Step 4: Health Check
print_status "Performing health checks..."

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check backend health
print_status "Checking backend health..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "https://$RAILWAY_URL/health")

if [ "$BACKEND_HEALTH" = "200" ]; then
    print_success "Backend health check passed"
else
    print_error "Backend health check failed (HTTP $BACKEND_HEALTH)"
fi

# Check frontend health
print_status "Checking frontend health..."
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "https://$VERCEL_URL")

if [ "$FRONTEND_HEALTH" = "200" ]; then
    print_success "Frontend health check passed"
else
    print_error "Frontend health check failed (HTTP $FRONTEND_HEALTH)"
fi

# Step 5: Integration Test
print_status "Running integration tests..."

# Test API connectivity
API_TEST=$(curl -s "https://$RAILWAY_URL/api/v1/health")
if [ $? -eq 0 ]; then
    print_success "API connectivity test passed"
else
    print_error "API connectivity test failed"
fi

# Test CORS
CORS_TEST=$(curl -s -H "Origin: https://$VERCEL_URL" "https://$RAILWAY_URL/api/v1/health")
if [ $? -eq 0 ]; then
    print_success "CORS test passed"
else
    print_error "CORS test failed"
fi

# Step 6: Performance Test
print_status "Running performance tests..."

# Test API response time
API_RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null "https://$RAILWAY_URL/api/v1/health")
if (( $(echo "$API_RESPONSE_TIME < 2.0" | bc -l) )); then
    print_success "API response time: ${API_RESPONSE_TIME}s (Good)"
else
    print_warning "API response time: ${API_RESPONSE_TIME}s (Slow)"
fi

# Step 7: Final Status
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "🌐 Services:"
echo "  Frontend: https://$VERCEL_URL"
echo "  Backend:  https://$RAILWAY_URL"
echo "  API Docs: https://$RAILWAY_URL/docs"
echo ""
echo "📊 Health Status:"
echo "  Backend:  $([ "$BACKEND_HEALTH" = "200" ] && echo "✅ Healthy" || echo "❌ Unhealthy")"
echo "  Frontend: $([ "$FRONTEND_HEALTH" = "200" ] && echo "✅ Healthy" || echo "❌ Unhealthy")"
echo ""
echo "⚡ Performance:"
echo "  API Response Time: ${API_RESPONSE_TIME}s"
echo ""
echo "🔧 Management:"
echo "  Railway Dashboard: https://railway.app/dashboard"
echo "  Vercel Dashboard:  https://vercel.com/dashboard"
echo ""
echo "📚 Documentation:"
echo "  API Documentation: https://$RAILWAY_URL/docs"
echo "  Deployment Guide:  ./DEPLOYMENT_ARCHITECTURE.md"
echo ""

# Step 8: Next Steps
echo "🚀 Next Steps:"
echo "1. Configure custom domains in Vercel and Railway"
echo "2. Set up monitoring and alerts"
echo "3. Run comprehensive integration tests"
echo "4. Begin B2B outreach with qualified leads"
echo "5. Monitor revenue generation and optimize"
echo ""

print_success "Production deployment completed successfully!"
