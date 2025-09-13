#!/bin/bash

# Aurum Solar Production Monitoring Script
# Continuous monitoring of production system health

echo "📊 Aurum Solar Production Monitoring"
echo "===================================="

# Configuration
FRONTEND_URL=${FRONTEND_URL:-"https://aurum-solar.vercel.app"}
BACKEND_URL=${BACKEND_URL:-"https://aurum-solar-backend.railway.app"}
API_URL="$BACKEND_URL/api/v1"

# Monitoring settings
CHECK_INTERVAL=${CHECK_INTERVAL:-60}  # seconds
ALERT_THRESHOLD=3  # consecutive failures before alert
LOG_FILE="monitoring.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Monitoring state
FAILURE_COUNT=0
LAST_ALERT=0
ALERT_COOLDOWN=300  # 5 minutes

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function to log to file
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to send alert (placeholder for integration with monitoring services)
send_alert() {
    local message="$1"
    local current_time=$(date +%s)
    
    if [ $((current_time - LAST_ALERT)) -gt $ALERT_COOLDOWN ]; then
        print_error "🚨 ALERT: $message"
        log_message "ALERT: $message"
        
        # Here you would integrate with your alerting system:
        # - Send email
        # - Send Slack notification
        # - Send SMS
        # - Create PagerDuty incident
        
        # Example integrations:
        # curl -X POST -H 'Content-type: application/json' \
        #     --data "{\"text\":\"🚨 Aurum Solar Alert: $message\"}" \
        #     "$SLACK_WEBHOOK_URL"
        
        LAST_ALERT=$current_time
    fi
}

# Function to check service health
check_service_health() {
    local service_name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    local response=$(curl -s -w '%{http_code}' -o /dev/null --max-time 30 "$url")
    
    if [ "$response" = "$expected_status" ]; then
        print_success "$service_name: Healthy (HTTP $response)"
        log_message "$service_name: Healthy (HTTP $response)"
        return 0
    else
        print_error "$service_name: Unhealthy (HTTP $response)"
        log_message "$service_name: Unhealthy (HTTP $response)"
        return 1
    fi
}

# Function to check API performance
check_api_performance() {
    local endpoint="$1"
    local max_response_time="${2:-2000}"  # milliseconds
    
    local start_time=$(date +%s%N)
    local response=$(curl -s -w '%{http_code}' -o /dev/null --max-time 30 "$endpoint")
    local end_time=$(date +%s%N)
    
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ "$response" = "200" ] && [ $response_time -lt $max_response_time ]; then
        print_success "API Performance: $response_time ms (Good)"
        log_message "API Performance: $response_time ms (Good)"
        return 0
    elif [ "$response" = "200" ]; then
        print_warning "API Performance: $response_time ms (Slow)"
        log_message "API Performance: $response_time ms (Slow)"
        return 1
    else
        print_error "API Performance: HTTP $response (Failed)"
        log_message "API Performance: HTTP $response (Failed)"
        return 1
    fi
}

# Function to check database connectivity
check_database_health() {
    local health_response=$(curl -s --max-time 30 "$API_URL/health/detailed")
    
    if echo "$health_response" | grep -q '"database": "healthy"'; then
        print_success "Database: Healthy"
        log_message "Database: Healthy"
        return 0
    else
        print_error "Database: Unhealthy"
        log_message "Database: Unhealthy"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis_health() {
    local health_response=$(curl -s --max-time 30 "$API_URL/health/detailed")
    
    if echo "$health_response" | grep -q '"redis": "healthy"'; then
        print_success "Redis: Healthy"
        log_message "Redis: Healthy"
        return 0
    else
        print_error "Redis: Unhealthy"
        log_message "Redis: Unhealthy"
        return 1
    fi
}

# Function to check system metrics
check_system_metrics() {
    local metrics_response=$(curl -s --max-time 30 "$API_URL/metrics")
    
    if [ $? -eq 0 ]; then
        local cpu_percent=$(echo "$metrics_response" | grep -o '"cpu_percent": [0-9.]*' | cut -d' ' -f2)
        local memory_percent=$(echo "$metrics_response" | grep -o '"memory_percent": [0-9.]*' | cut -d' ' -f2)
        local disk_percent=$(echo "$metrics_response" | grep -o '"disk_percent": [0-9.]*' | cut -d' ' -f2)
        
        print_status "System Metrics: CPU ${cpu_percent}%, Memory ${memory_percent}%, Disk ${disk_percent}%"
        log_message "System Metrics: CPU ${cpu_percent}%, Memory ${memory_percent}%, Disk ${disk_percent}%"
        
        # Check for high resource usage
        if (( $(echo "$cpu_percent > 80" | bc -l) )); then
            print_warning "High CPU usage: ${cpu_percent}%"
            log_message "High CPU usage: ${cpu_percent}%"
        fi
        
        if (( $(echo "$memory_percent > 80" | bc -l) )); then
            print_warning "High memory usage: ${memory_percent}%"
            log_message "High memory usage: ${memory_percent}%"
        fi
        
        if (( $(echo "$disk_percent > 80" | bc -l) )); then
            print_warning "High disk usage: ${disk_percent}%"
            log_message "High disk usage: ${disk_percent}%"
        fi
        
        return 0
    else
        print_error "System metrics: Failed to retrieve"
        log_message "System metrics: Failed to retrieve"
        return 1
    fi
}

# Function to run comprehensive health check
run_health_check() {
    local checks_passed=0
    local total_checks=0
    
    print_status "Running health check..."
    
    # Check frontend
    ((total_checks++))
    if check_service_health "Frontend" "$FRONTEND_URL"; then
        ((checks_passed++))
    fi
    
    # Check backend
    ((total_checks++))
    if check_service_health "Backend" "$BACKEND_URL/health"; then
        ((checks_passed++))
    fi
    
    # Check API
    ((total_checks++))
    if check_api_performance "$API_URL/health"; then
        ((checks_passed++))
    fi
    
    # Check database
    ((total_checks++))
    if check_database_health; then
        ((checks_passed++))
    fi
    
    # Check Redis
    ((total_checks++))
    if check_redis_health; then
        ((checks_passed++))
    fi
    
    # Check system metrics
    ((total_checks++))
    if check_system_metrics; then
        ((checks_passed++))
    fi
    
    # Calculate health percentage
    local health_percentage=$(( (checks_passed * 100) / total_checks ))
    
    print_status "Health Check Results: $checks_passed/$total_checks checks passed (${health_percentage}%)"
    log_message "Health Check Results: $checks_passed/$total_checks checks passed (${health_percentage}%)"
    
    # Determine if system is healthy
    if [ $health_percentage -ge 80 ]; then
        print_success "System Status: HEALTHY"
        log_message "System Status: HEALTHY"
        FAILURE_COUNT=0
        return 0
    elif [ $health_percentage -ge 60 ]; then
        print_warning "System Status: DEGRADED"
        log_message "System Status: DEGRADED"
        ((FAILURE_COUNT++))
        return 1
    else
        print_error "System Status: UNHEALTHY"
        log_message "System Status: UNHEALTHY"
        ((FAILURE_COUNT++))
        return 1
    fi
}

# Function to check for alerts
check_alerts() {
    if [ $FAILURE_COUNT -ge $ALERT_THRESHOLD ]; then
        send_alert "System has been unhealthy for $FAILURE_COUNT consecutive checks"
        FAILURE_COUNT=0  # Reset to avoid spam
    fi
}

# Main monitoring loop
main() {
    print_status "Starting production monitoring..."
    print_status "Frontend URL: $FRONTEND_URL"
    print_status "Backend URL: $BACKEND_URL"
    print_status "Check interval: ${CHECK_INTERVAL}s"
    print_status "Log file: $LOG_FILE"
    echo ""
    
    # Initialize log file
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Monitoring started" > "$LOG_FILE"
    
    # Main monitoring loop
    while true; do
        run_health_check
        check_alerts
        
        print_status "Next check in ${CHECK_INTERVAL}s..."
        echo ""
        
        sleep $CHECK_INTERVAL
    done
}

# Handle script interruption
trap 'echo ""; print_status "Monitoring stopped"; exit 0' INT TERM

# Run main function
main
