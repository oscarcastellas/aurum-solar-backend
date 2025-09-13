#!/bin/bash

# 🚀 Aurum Solar - Render.com Deployment Setup Script

echo "🚀 Setting up Aurum Solar for Render.com deployment..."

# Check if we're in the right directory
if [ ! -f "backend/main_simple.py" ]; then
    echo "❌ Error: Please run this script from the aurum_solar project root directory"
    exit 1
fi

echo "✅ Project structure verified"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Aurum Solar FastAPI backend ready for Render deployment"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if backend files are ready
echo "🔍 Checking backend files..."

if [ -f "backend/main_simple.py" ]; then
    echo "✅ main_simple.py found"
else
    echo "❌ main_simple.py not found"
    exit 1
fi

if [ -f "backend/requirements.txt" ]; then
    echo "✅ requirements.txt found"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

if [ -f "backend/render.yaml" ]; then
    echo "✅ render.yaml found"
else
    echo "❌ render.yaml not found"
    exit 1
fi

echo ""
echo "🎉 Setup complete! Your project is ready for Render deployment."
echo ""
echo "📋 Next steps:"
echo "1. Create a GitHub repository:"
echo "   - Go to https://github.com/new"
echo "   - Name: aurum-solar-backend"
echo "   - Make it public (required for free Render)"
echo "   - Don't initialize with README"
echo ""
echo "2. Push your code to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/aurum-solar-backend.git"
echo "   git push -u origin main"
echo ""
echo "3. Deploy to Render:"
echo "   - Go to https://render.com"
echo "   - Sign up with GitHub"
echo "   - Click 'New +' → 'Web Service'"
echo "   - Connect your repository"
echo "   - Use these settings:"
echo "     • Build Command: pip install -r requirements.txt"
echo "     • Start Command: uvicorn main_simple:app --host 0.0.0.0 --port \$PORT"
echo "     • Plan: Free"
echo ""
echo "4. Add databases:"
echo "   - PostgreSQL: New → PostgreSQL → Free"
echo "   - Redis: New → Redis → Free"
echo ""
echo "5. Set environment variables in Render dashboard"
echo ""
echo "📖 Full guide: RENDER_DEPLOYMENT_GUIDE.md"
echo ""
echo "🚀 Ready to deploy!"
