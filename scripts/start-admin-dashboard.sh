#!/bin/bash

# Aurum Solar Admin Dashboard Startup Script
# Starts the admin dashboard development environment

echo "🚀 Starting Aurum Solar Admin Dashboard..."
echo "============================================="

# Check if we're in the right directory
if [ ! -d "admin-dashboard" ]; then
    echo "❌ Error: admin-dashboard directory not found"
    echo "Please run this script from the aurum_solar root directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed"
    echo "Please install npm with Node.js"
    exit 1
fi

# Navigate to admin dashboard directory
cd admin-dashboard

echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check if backend is running
echo "🔍 Checking if backend API is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is running on port 8000"
else
    echo "⚠️  Warning: Backend API is not running on port 8000"
    echo "Please start the backend API first:"
    echo "cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
    echo ""
    echo "Starting admin dashboard anyway..."
fi

echo ""
echo "🌐 Starting admin dashboard development server..."
echo "Dashboard will be available at: http://localhost:3002"
echo "API proxy configured for: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm run dev
