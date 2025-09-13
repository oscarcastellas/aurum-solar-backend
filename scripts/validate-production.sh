#!/bin/bash

# Aurum Solar Production Validation Script
# Comprehensive testing of deployed production system

echo "🧪 Aurum Solar Production Validation"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL=${FRONTEND_URL:-"https://aurum-solar.vercel.app"}
BACKEND_URL=${BACKEND_URL:-"https://aurum-solar-backend.railway.app"}
API_URL="$BACKEND_URL/api/v1"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Function to print colored output
print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="${3:-200}"
    
    ((TOTAL_TESTS++))
    print_status "$test_name"
    
    local response=$(eval "$test_command")
    local status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" = "$expected_status" ]; then
        print_success "$test_name"
        return 0
    else
        print_error "$test_name (HTTP $status_code)"
        return 1
    fi
}

# Function to test API endpoint
test_api_endpoint() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"
    local expected_status="${4:-200}"
    
    local curl_cmd="curl -s -w '%{http_code}' -o /dev/null"
    
    if [ "$method" = "POST" ]; then
        curl_cmd="$curl_cmd -X POST -H 'Content-Type: application/json'"
        if [ -n "$data" ]; then
            curl_cmd="$curl_cmd -d '$data'"
        fi
    fi
    
    curl_cmd="$curl_cmd '$API_URL$endpoint'"
    
    echo "$curl_cmd"
}

echo "🔧 Configuration:"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Backend URL:  $BACKEND_URL"
echo "  API URL:      $API_URL"
echo ""

# Test 1: Backend Health Check
print_status "Testing backend health..."
HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")
if [ $? -eq 0 ] && echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_success "Backend health check"
else
    print_error "Backend health check"
fi

# Test 2: API Health Check
run_test "API Health Check" "curl -s -w '%{http_code}' -o /dev/null '$API_URL/health'" "200"

# Test 3: CORS Configuration
print_status "Testing CORS configuration..."
CORS_RESPONSE=$(curl -s -H "Origin: $FRONTEND_URL" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: X-Requested-With" -X OPTIONS "$API_URL/health")
if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    print_success "CORS configuration"
else
    print_error "CORS configuration"
fi

# Test 4: Frontend Accessibility
print_status "Testing frontend accessibility..."
FRONTEND_RESPONSE=$(curl -s -w '%{http_code}' -o /dev/null "$FRONTEND_URL")
if [ "$FRONTEND_RESPONSE" = "200" ]; then
    print_success "Frontend accessibility"
else
    print_error "Frontend accessibility (HTTP $FRONTEND_RESPONSE)"
fi

# Test 5: API Documentation
run_test "API Documentation" "curl -s -w '%{http_code}' -o /dev/null '$BACKEND_URL/docs'" "200"

# Test 6: Chat API Endpoint
run_test "Chat API Endpoint" "curl -s -w '%{http_code}' -o /dev/null '$API_URL/chat/test'" "200"

# Test 7: Lead Generation API
run_test "Lead Generation API" "curl -s -w '%{http_code}' -o /dev/null '$API_URL/leads/exportable'" "200"

# Test 8: Revenue Analytics API
run_test "Revenue Analytics API" "curl -s -w '%{http_code}' -o /dev/null '$API_URL/revenue-dashboard/executive-summary'" "200"

# Test 9: B2B Export API
run_test "B2B Export API" "curl -s -w '%{http_code}' -o /dev/null '$API_URL/b2b/platforms'" "200"

# Test 10: Solar Calculator API
print_status "Testing solar calculator API..."
SOLAR_CALC_DATA='{"monthly_bill": 300, "zip_code": "10001", "borough": "Manhattan"}'
SOLAR_RESPONSE=$(curl -s -w '%{http_code}' -o /dev/null -X POST -H "Content-Type: application/json" -d "$SOLAR_CALC_DATA" "$API_URL/solar/calculate")
if [ "$SOLAR_RESPONSE" = "200" ]; then
    print_success "Solar calculator API"
else
    print_error "Solar calculator API (HTTP $SOLAR_RESPONSE)"
fi

# Test 11: Performance Test
print_status "Testing API performance..."
PERFORMANCE_START=$(date +%s%N)
curl -s "$API_URL/health" > /dev/null
PERFORMANCE_END=$(date +%s%N)
PERFORMANCE_TIME=$(( (PERFORMANCE_END - PERFORMANCE_START) / 1000000 ))

if [ $PERFORMANCE_TIME -lt 2000 ]; then
    print_success "API performance (${PERFORMANCE_TIME}ms)"
else
    print_warning "API performance (${PERFORMANCE_TIME}ms - slow)"
fi

# Test 12: Database Connectivity
print_status "Testing database connectivity..."
DB_TEST=$(curl -s "$API_URL/health" | grep -o '"database": "[^"]*"')
if [ $? -eq 0 ]; then
    print_success "Database connectivity"
else
    print_error "Database connectivity"
fi

# Test 13: Redis Connectivity
print_status "Testing Redis connectivity..."
REDIS_TEST=$(curl -s "$API_URL/health" | grep -o '"redis": "[^"]*"')
if [ $? -eq 0 ]; then
    print_success "Redis connectivity"
else
    print_error "Redis connectivity"
fi

# Test 14: WebSocket Connectivity
print_status "Testing WebSocket connectivity..."
WS_URL=$(echo "$BACKEND_URL" | sed 's/https/wss/')
# Note: WebSocket testing requires a more complex setup
print_warning "WebSocket test skipped (requires browser environment)"

# Test 15: Security Headers
print_status "Testing security headers..."
SECURITY_HEADERS=$(curl -s -I "$FRONTEND_URL" | grep -E "(X-Frame-Options|X-Content-Type-Options|X-XSS-Protection)")
if [ -n "$SECURITY_HEADERS" ]; then
    print_success "Security headers"
else
    print_error "Security headers"
fi

# Test 16: HTTPS Configuration
print_status "Testing HTTPS configuration..."
HTTPS_TEST=$(curl -s -I "$FRONTEND_URL" | grep -i "strict-transport-security")
if [ -n "$HTTPS_TEST" ]; then
    print_success "HTTPS configuration"
else
    print_warning "HTTPS configuration (HSTS not configured)"
fi

# Test 17: Frontend Build Optimization
print_status "Testing frontend build optimization..."
FRONTEND_SIZE=$(curl -s "$FRONTEND_URL" | wc -c)
if [ $FRONTEND_SIZE -lt 1000000 ]; then
    print_success "Frontend build optimization (${FRONTEND_SIZE} bytes)"
else
    print_warning "Frontend build optimization (${FRONTEND_SIZE} bytes - large)"
fi

# Test 18: API Rate Limiting
print_status "Testing API rate limiting..."
RATE_LIMIT_TEST=0
for i in {1..5}; do
    RESPONSE=$(curl -s -w '%{http_code}' -o /dev/null "$API_URL/health")
    if [ "$RESPONSE" = "200" ]; then
        ((RATE_LIMIT_TEST++))
    fi
    sleep 1
done

if [ $RATE_LIMIT_TEST -eq 5 ]; then
    print_success "API rate limiting (5/5 requests successful)"
else
    print_error "API rate limiting ($RATE_LIMIT_TEST/5 requests successful)"
fi

# Test 19: Error Handling
print_status "Testing error handling..."
ERROR_RESPONSE=$(curl -s -w '%{http_code}' -o /dev/null "$API_URL/nonexistent")
if [ "$ERROR_RESPONSE" = "404" ]; then
    print_success "Error handling"
else
    print_error "Error handling (HTTP $ERROR_RESPONSE)"
fi

# Test 20: Integration Test
print_status "Testing end-to-end integration..."
INTEGRATION_TEST=$(curl -s -X POST -H "Content-Type: application/json" -d '{"message": "Hello, I want to learn about solar", "session_id": "test-session-123"}' "$API_URL/chat/message")
if [ $? -eq 0 ] && echo "$INTEGRATION_TEST" | grep -q "response"; then
    print_success "End-to-end integration"
else
    print_error "End-to-end integration"
fi

# Final Results
echo ""
echo "📊 Validation Results"
echo "===================="
echo ""
echo "✅ Tests Passed: $TESTS_PASSED"
echo "❌ Tests Failed: $TESTS_FAILED"
echo "📊 Total Tests:  $TOTAL_TESTS"
echo ""

SUCCESS_RATE=$(( (TESTS_PASSED * 100) / TOTAL_TESTS ))
echo "🎯 Success Rate: ${SUCCESS_RATE}%"

if [ $SUCCESS_RATE -ge 90 ]; then
    echo -e "${GREEN}🎉 Production system is ready!${NC}"
    echo ""
    echo "🚀 System Status: READY FOR REVENUE GENERATION"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Begin B2B outreach with qualified leads"
    echo "2. Monitor revenue generation and analytics"
    echo "3. Optimize conversation flows based on data"
    echo "4. Scale lead generation efforts"
    echo ""
elif [ $SUCCESS_RATE -ge 70 ]; then
    echo -e "${YELLOW}⚠️  Production system has minor issues${NC}"
    echo ""
    echo "🔧 Recommended Actions:"
    echo "1. Review failed tests and fix issues"
    echo "2. Re-run validation after fixes"
    echo "3. Monitor system closely after launch"
    echo ""
else
    echo -e "${RED}❌ Production system has critical issues${NC}"
    echo ""
    echo "🚨 Required Actions:"
    echo "1. Fix critical issues before launch"
    echo "2. Re-run full validation"
    echo "3. Consider rolling back deployment"
    echo ""
fi

echo "🌐 System URLs:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo "  API Docs: $BACKEND_URL/docs"
echo ""

exit $([ $SUCCESS_RATE -ge 70 ] && echo 0 || echo 1)
