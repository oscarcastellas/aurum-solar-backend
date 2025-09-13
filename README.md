# Aurum Solar - AI-Powered Solar Lead Generation Platform

A comprehensive full-stack web application for AI-powered solar lead generation targeting the NYC market. Built for rapid deployment and revenue generation with a focus on B2B lead export capabilities.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd aurum_solar
cp env.example .env
# Edit .env with your API keys and configuration
```

2. **Install dependencies:**
```bash
# Install root dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

3. **Start development environment:**
```bash
# Option 1: Using Docker (Recommended)
docker-compose -f docker-compose.dev.yml up --build

# Option 2: Manual setup
# Terminal 1 - Database
docker run -d --name postgres -e POSTGRES_DB=aurum_solar -e POSTGRES_USER=aurum -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Terminal 2 - Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 - Frontend
cd frontend
npm run dev
```

4. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for real-time features
- **AI Integration**: OpenAI GPT-4 for lead analysis
- **Authentication**: JWT-based auth
- **Background Tasks**: Celery with Redis

### Frontend (Next.js 14)
- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query + useState
- **Forms**: React Hook Form with Zod validation
- **UI Components**: Headless UI + Heroicons

### Database Schema
- **Leads**: Core lead data with AI insights
- **Lead Exports**: B2B platform export tracking
- **Revenue Metrics**: Performance and revenue analytics
- **Platform Performance**: B2B platform analytics
- **NYC Market Intelligence**: NYC-specific market data

## 📊 Key Features

### Lead Generation
- AI-powered lead qualification and scoring
- NYC market-specific intelligence
- Real-time lead analysis and insights
- Multi-platform lead export capabilities

### Analytics Dashboard
- Revenue tracking and forecasting
- Lead quality metrics
- Platform performance analytics
- NYC market intelligence insights

### B2B Integrations
- SolarReviews API integration
- Modernize platform integration
- Automated lead export workflows
- Revenue tracking per platform

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://aurum:password@localhost:5432/aurum_solar
REDIS_URL=redis://localhost:6379/0

# AI Services
OPENAI_API_KEY=your-openai-api-key

# B2B Integrations
SOLARREVIEWS_API_KEY=your-solarreviews-key
MODERNIZE_API_KEY=your-modernize-key

# Security
SECRET_KEY=your-secret-key
```

### Database Migrations
```bash
cd backend
alembic upgrade head
```

## 🚀 Deployment

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Vercel (Frontend)
```bash
cd frontend
vercel --prod
```

### Railway/DigitalOcean (Backend)
```bash
# Deploy using Railway CLI or DigitalOcean App Platform
railway deploy
```

## 📈 Business Model

- **Revenue Target**: $15K MRR by month 1
- **Lead Pricing**: $75-300 per qualified lead
- **Target Volume**: 1000+ leads/month
- **Market Focus**: NYC solar market
- **B2B Platforms**: SolarReviews, Modernize, etc.

## 🛠️ Development

### Code Quality
```bash
# Backend
cd backend
black .
isort .
flake8 .
mypy .

# Frontend
cd frontend
npm run lint
npm run type-check
npm run format
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Git Workflow
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature development
- `hotfix/*`: Critical fixes

## 📚 API Documentation

### Lead Management
- `POST /api/v1/leads` - Create new lead
- `GET /api/v1/leads` - List leads with filtering
- `GET /api/v1/leads/{id}` - Get specific lead
- `PUT /api/v1/leads/{id}` - Update lead
- `DELETE /api/v1/leads/{id}` - Delete lead

### Analytics
- `GET /api/v1/analytics/revenue` - Revenue metrics
- `GET /api/v1/analytics/leads` - Lead analytics
- `GET /api/v1/analytics/platforms` - Platform performance

### AI Chat
- `POST /api/v1/ai/chat` - Chat with lead
- `GET /api/v1/ai/questions/{lead_id}` - Generate follow-up questions

### Exports
- `POST /api/v1/exports/export` - Export lead to B2B platform
- `GET /api/v1/exports/history` - Export history

## 🎯 Success Metrics

- **Lead Quality Score**: 80+ average
- **Conversion Rate**: 15%+ qualified leads
- **Revenue per Lead**: $150+ average
- **Platform Uptime**: 99.9%+
- **Response Time**: <200ms API calls

## 📞 Support

For technical support or business inquiries:
- Email: support@aurumsolar.com
- Documentation: [API Docs](http://localhost:8000/docs)
- Issues: GitHub Issues

---

**Built with ❤️ for the NYC solar market**
