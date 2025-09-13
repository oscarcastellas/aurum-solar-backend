#!/bin/bash

# Aurum Solar Core Systems Validation Script
# This script runs the complete validation suite for core systems

set -e  # Exit on any error

echo "🚀 Aurum Solar - Core Systems Validation"
echo "========================================"
echo "Started at: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "INFO" "Checking prerequisites..."

if ! command_exists python3; then
    print_status "ERROR" "Python 3 is required but not installed"
    exit 1
fi

if ! command_exists pip; then
    print_status "ERROR" "pip is required but not installed"
    exit 1
fi

print_status "SUCCESS" "Prerequisites check passed"

# Set up virtual environment
print_status "INFO" "Setting up virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "SUCCESS" "Virtual environment created"
else
    print_status "INFO" "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "SUCCESS" "Virtual environment activated"

# Install dependencies
print_status "INFO" "Installing dependencies..."

if [ -f "requirements-test.txt" ]; then
    pip install -r requirements-test.txt
    print_status "SUCCESS" "Test dependencies installed"
else
    print_status "WARNING" "requirements-test.txt not found, installing basic dependencies"
    pip install pytest pytest-asyncio httpx websockets redis
fi

# Set environment variables for testing
export ENVIRONMENT=test
export DATABASE_URL=sqlite:///./test.db
export REDIS_URL=redis://localhost:6379/1
export OPENAI_API_KEY=test_key

print_status "INFO" "Environment variables set for testing"

# Create test database directory
mkdir -p tests/data
print_status "SUCCESS" "Test directories created"

# Run validation phases
print_status "INFO" "Starting core systems validation..."

# Phase 1: Database & APIs Validation
print_status "INFO" "Phase 1: Database & APIs Validation"
python tests/test_runner.py --phase database
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "Database & APIs validation passed"
else
    print_status "ERROR" "Database & APIs validation failed"
    exit 1
fi

# Phase 2: AI Conversation Agent Validation
print_status "INFO" "Phase 2: AI Conversation Agent Validation"
python tests/test_runner.py --phase ai
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "AI Conversation Agent validation passed"
else
    print_status "ERROR" "AI Conversation Agent validation failed"
    exit 1
fi

# Phase 3: Real-Time Systems Validation
print_status "INFO" "Phase 3: Real-Time Systems Validation"
python tests/test_runner.py --phase realtime
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "Real-Time Systems validation passed"
else
    print_status "ERROR" "Real-Time Systems validation failed"
    exit 1
fi

# Generate final report
print_status "INFO" "Generating validation report..."

# Run all tests to generate comprehensive report
python tests/test_runner.py --phase all

# Check if all tests passed
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "All core systems validation tests passed!"
    print_status "SUCCESS" "System is ready for integration validation"
    
    # Create success marker
    echo "$(date)" > tests/validation_success.txt
    echo "All core systems validation tests passed" >> tests/validation_success.txt
    
    echo ""
    echo "🎉 VALIDATION COMPLETED SUCCESSFULLY!"
    echo "====================================="
    echo "✅ Database & APIs: PASSED"
    echo "✅ AI Conversation Agent: PASSED"
    echo "✅ Real-Time Systems: PASSED"
    echo ""
    echo "Next steps:"
    echo "1. Review validation report above"
    echo "2. Proceed with integration validation"
    echo "3. Prepare for production deployment"
    
else
    print_status "ERROR" "Some validation tests failed!"
    print_status "ERROR" "Please review the test output and fix issues"
    
    # Create failure marker
    echo "$(date)" > tests/validation_failure.txt
    echo "Some core systems validation tests failed" >> tests/validation_failure.txt
    
    echo ""
    echo "❌ VALIDATION FAILED!"
    echo "====================="
    echo "Please review the test output above and fix any issues"
    echo "Then re-run the validation script"
    
    exit 1
fi

echo ""
echo "Completed at: $(date)"
echo "Validation script finished"
