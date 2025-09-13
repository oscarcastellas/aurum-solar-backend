# Aurum Solar - Codebase Overview

## Project Structure

```
aurum_solar/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/endpoints/         # API Endpoints
│   │   │   ├── analytics.py          # Analytics & Dashboard APIs
│   │   │   ├── b2b_integration.py    # B2B Integration APIs
│   │   │   ├── leads.py              # Lead Management APIs
│   │   │   └── websocket.py          # WebSocket Endpoints
│   │   ├── core/                     # Core Configuration
│   │   │   ├── config.py             # Environment Configuration
│   │   │   ├── database.py           # Database Connection
│   │   │   ├── redis.py              # Redis Connection
│   │   │   └── security.py           # Authentication & Security
│   │   ├── models/                   # SQLAlchemy Models
│   │   │   ├── lead.py               # Lead Data Models
│   │   │   ├── b2b_platforms.py      # B2B Platform Models
│   │   │   └── analytics.py          # Analytics Models
│   │   ├── schemas/                  # Pydantic Schemas
│   │   │   ├── analytics.py          # Analytics API Schemas
│   │   │   ├── b2b_integration.py    # B2B Integration Schemas
│   │   │   └── leads.py              # Lead Management Schemas
│   │   ├── services/                 # Business Logic Services
│   │   │   ├── ai_conversation.py    # AI Chat Engine
│   │   │   ├── b2b_orchestrator.py   # B2B Delivery Orchestration
│   │   │   ├── lead_routing_engine.py # Lead Routing & Optimization
│   │   │   ├── revenue_tracker.py    # Revenue Tracking & Reconciliation
│   │   │   ├── b2b_platform_manager.py # Platform Management
│   │   │   ├── integration_monitor.py # Health Monitoring
│   │   │   └── analytics_service.py  # Analytics & Reporting
│   │   ├── websocket/                # WebSocket Handlers
│   │   │   ├── chat_handler.py       # AI Chat WebSocket
│   │   │   └── analytics_handler.py  # Real-time Analytics
│   │   └── main.py                   # FastAPI Application Entry
│   ├── requirements.txt              # Python Dependencies
│   └── Dockerfile                    # Backend Container
├── frontend/                         # Next.js Frontend
│   ├── app/                          # Next.js App Router
│   │   ├── dashboard/                # Analytics Dashboard
│   │   │   ├── layout.tsx            # Dashboard Layout
│   │   │   ├── page.tsx              # Main Dashboard
│   │   │   └── [subpages]/           # Dashboard Subpages
│   │   ├── chat/                     # AI Chat Interface
│   │   │   ├── page.tsx              # Chat Interface
│   │   │   └── components/           # Chat Components
│   │   └── globals.css               # Global Styles
│   ├── components/                   # React Components
│   │   ├── dashboard/                # Dashboard Components
│   │   │   ├── ExecutiveSummary.tsx  # Executive Summary Widget
│   │   │   ├── RevenueOverview.tsx   # Revenue Analytics
│   │   │   ├── LeadQualityMetrics.tsx # Lead Quality Analytics
│   │   │   ├── NYCMarketIntelligence.tsx # NYC Market Data
│   │   │   ├── B2BPerformance.tsx    # B2B Platform Performance
│   │   │   ├── ConversionFunnel.tsx  # Conversion Funnel Analysis
│   │   │   ├── RealTimeMetrics.tsx   # Real-time Metrics
│   │   │   ├── OperationalInsights.tsx # Operational Insights
│   │   │   ├── Sidebar.tsx           # Dashboard Sidebar
│   │   │   ├── Header.tsx            # Dashboard Header
│   │   │   └── NotificationPanel.tsx # Notifications Panel
│   │   ├── chat/                     # Chat Components
│   │   │   ├── ChatInterface.tsx     # Main Chat Interface
│   │   │   ├── MessageBubble.tsx     # Message Components
│   │   │   ├── TypingIndicator.tsx   # Typing Indicators
│   │   │   └── LeadCapture.tsx       # Lead Capture Form
│   │   └── ui/                       # Reusable UI Components
│   │       ├── Button.tsx            # Button Component
│   │       ├── Input.tsx             # Input Component
│   │       └── Modal.tsx             # Modal Component
│   ├── hooks/                        # Custom React Hooks
│   │   ├── useAnalytics.tsx          # Analytics Hook
│   │   ├── useWebSocket.tsx          # WebSocket Hook
│   │   └── useChat.tsx               # Chat Hook
│   ├── lib/                          # Utility Libraries
│   │   ├── utils.ts                  # General Utilities
│   │   ├── api.ts                    # API Client
│   │   └── types.ts                  # TypeScript Types
│   ├── package.json                  # Node.js Dependencies
│   ├── tailwind.config.js            # Tailwind CSS Config
│   └── next.config.js                # Next.js Configuration
├── docker-compose.yml                # Development Environment
├── .env.example                      # Environment Variables Template
└── README.md                         # Project Documentation
```

## Backend Architecture

### Core Services

#### 1. **AI Conversation Engine** (`ai_conversation.py`)
- **Purpose**: Handles AI-powered lead qualification conversations
- **Key Features**:
  - OpenAI GPT-4 integration with Claude fallback
  - Multi-stage conversation orchestration
  - NYC market-specific knowledge base
  - Real-time lead scoring and qualification
  - Objection handling with local data
- **Dependencies**: OpenAI API, Redis for conversation state

#### 2. **B2B Orchestrator** (`b2b_orchestrator.py`)
- **Purpose**: Centralized lead delivery management to multiple B2B platforms
- **Key Features**:
  - Multi-format delivery (JSON API, CSV email, webhook)
  - Async delivery workers with queue management
  - Retry logic with exponential backoff
  - Revenue tracking and commission calculation
  - Platform performance monitoring
- **Dependencies**: aiohttp, Redis queues, PostgreSQL

#### 3. **Lead Routing Engine** (`lead_routing_engine.py`)
- **Purpose**: Intelligent lead routing and optimization
- **Key Features**:
  - Multi-strategy routing (revenue, capacity, quality, load balancing)
  - NYC market intelligence integration
  - Rule-based routing system
  - Platform scoring algorithm
  - Alternative routing options
- **Dependencies**: Redis for platform data, PostgreSQL for lead data

#### 4. **Revenue Tracker** (`revenue_tracker.py`)
- **Purpose**: Comprehensive revenue management and reconciliation
- **Key Features**:
  - Multi-platform revenue tracking
  - Commission calculation and management
  - Revenue reconciliation with platforms
  - Payment status monitoring
  - Financial reporting and analytics
- **Dependencies**: PostgreSQL, Redis for caching

#### 5. **Platform Manager** (`b2b_platform_manager.py`)
- **Purpose**: B2B platform onboarding and management
- **Key Features**:
  - Step-by-step platform onboarding
  - Configuration management
  - Health monitoring
  - Template system for different delivery methods
  - Platform lifecycle management
- **Dependencies**: PostgreSQL, Redis for onboarding state

#### 6. **Integration Monitor** (`integration_monitor.py`)
- **Purpose**: Health monitoring and alerting system
- **Key Features**:
  - Real-time platform health checks
  - Multi-level alerting system
  - Performance metrics collection
  - Issue detection and notification
  - Alert management workflow
- **Dependencies**: Redis for metrics, notification services

### API Endpoints

#### Analytics APIs (`analytics.py`)
- `GET /analytics/executive-summary` - Executive dashboard metrics
- `GET /analytics/revenue` - Revenue analytics and trends
- `GET /analytics/lead-quality` - Lead quality metrics
- `GET /analytics/nyc-market` - NYC market intelligence
- `GET /analytics/b2b-performance` - B2B platform performance
- `GET /analytics/conversion-funnel` - Conversion funnel analysis
- `GET /analytics/operational-insights` - Operational insights

#### B2B Integration APIs (`b2b_integration.py`)
- `POST /deliver-lead` - Deliver lead to optimal platform
- `GET /delivery-status/{id}` - Get delivery status
- `POST /platforms` - Create new B2B platform
- `GET /platforms` - List all platforms
- `GET /platforms/{id}/health` - Get platform health
- `POST /platforms/{id}/onboard` - Start platform onboarding
- `GET /alerts` - Get active alerts
- `POST /alerts/{id}/acknowledge` - Acknowledge alert
- `GET /revenue/metrics` - Get revenue metrics

#### WebSocket Endpoints (`websocket.py`)
- `/ws/chat` - AI conversation WebSocket
- `/ws/analytics` - Real-time analytics WebSocket

### Database Models

#### Lead Models (`lead.py`)
- `Lead` - Main lead entity with qualification data
- `LeadConversation` - AI conversation history
- `LeadQualityHistory` - Quality score tracking
- `LeadExport` - B2B delivery records

#### B2B Platform Models (`b2b_platforms.py`)
- `B2BPlatform` - Platform configuration and settings
- `B2BLeadMapping` - Lead to platform mapping
- `B2BRevenueTransaction` - Revenue and commission tracking

#### Analytics Models (`analytics.py`)
- `AnalyticsEvent` - User interaction tracking
- `PerformanceMetric` - System performance metrics
- `Alert` - System alerts and notifications

## Frontend Architecture

### Dashboard Components

#### Executive Summary (`ExecutiveSummary.tsx`)
- Real-time KPI display
- Revenue, leads, quality, performance metrics
- Animated counters with CountUp
- Quick insights and trend indicators

#### Revenue Overview (`RevenueOverview.tsx`)
- Interactive revenue charts
- Platform breakdown and performance
- Growth trends and forecasting
- Canvas-based visualizations

#### Lead Quality Metrics (`LeadQualityMetrics.tsx`)
- Quality distribution analysis
- Score trend charts
- Conversion rate tracking
- Quality improvement recommendations

#### NYC Market Intelligence (`NYCMarketIntelligence.tsx`)
- Borough performance mapping
- Zip code insights and analytics
- Market trends and seasonal analysis
- Competitive positioning data

#### B2B Performance (`B2BPerformance.tsx`)
- Platform performance comparison
- Revenue optimization tools
- Capacity management
- Quality feedback integration

#### Conversion Funnel (`ConversionFunnel.tsx`)
- Multi-stage funnel visualization
- Conversion rate analysis
- Bottleneck identification
- Performance optimization

#### Real-Time Metrics (`RealTimeMetrics.tsx`)
- Live data streaming
- WebSocket integration
- System status monitoring
- Performance indicators

#### Operational Insights (`OperationalInsights.tsx`)
- Automated recommendations
- Alert management
- Optimization suggestions
- Quick action tools

### Chat Interface Components

#### Chat Interface (`ChatInterface.tsx`)
- Main chat container
- Message display and input
- Typing indicators
- Lead capture integration

#### Message Components
- `MessageBubble.tsx` - Individual message display
- `TypingIndicator.tsx` - AI typing animation
- `LeadCapture.tsx` - Lead information form

### Custom Hooks

#### Analytics Hook (`useAnalytics.tsx`)
- Event tracking and analytics
- Performance monitoring
- User interaction logging

#### WebSocket Hook (`useWebSocket.tsx`)
- Real-time data connection
- Automatic reconnection
- Message handling

#### Chat Hook (`useChat.tsx`)
- Chat state management
- Message handling
- AI conversation flow

## Key Features

### AI-Powered Lead Generation
- **Conversational Qualification**: Natural language lead qualification using OpenAI GPT-4
- **NYC Market Expertise**: Borough-specific knowledge and incentive information
- **Quality Scoring**: Multi-tier lead classification (Premium $200+/Standard $125/Basic $75)
- **Objection Handling**: NYC-specific data and neighborhood examples
- **Real-Time Processing**: WebSocket-powered live conversations

### B2B Integration System
- **Multi-Platform Delivery**: JSON API, CSV email, webhook, SFTP support
- **Intelligent Routing**: Revenue maximization and capacity optimization
- **Real-Time Processing**: Async delivery with retry logic and error handling
- **Revenue Tracking**: Automated commission calculation and reconciliation
- **Platform Management**: Easy onboarding and configuration management

### Analytics & Business Intelligence
- **Real-Time Dashboard**: Live metrics and performance monitoring
- **Revenue Analytics**: Multi-platform revenue tracking and analysis
- **Lead Quality Analytics**: Quality distribution and improvement tracking
- **NYC Market Intelligence**: Geographic and demographic analytics
- **Operational Insights**: Automated recommendations and optimization

### Technical Architecture
- **Async Processing**: Non-blocking async/await architecture
- **Queue Management**: Redis-based delivery queues for scalability
- **Caching Strategy**: Multi-layer caching for performance
- **WebSocket Integration**: Real-time data streaming
- **Health Monitoring**: Proactive system monitoring and alerting

## Dependencies

### Backend Dependencies
- **FastAPI**: Web framework and API development
- **SQLAlchemy**: ORM and database management
- **Alembic**: Database migrations
- **Redis**: Caching and real-time data
- **OpenAI**: AI conversation capabilities
- **aiohttp**: Async HTTP client for external APIs
- **Pydantic**: Data validation and serialization
- **structlog**: Structured logging

### Frontend Dependencies
- **Next.js 14**: React framework with app router
- **TypeScript**: Type safety and development experience
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Animation and transitions
- **React Hook Form**: Form handling and validation
- **Zod**: Schema validation
- **Socket.IO**: WebSocket client
- **Chart.js**: Data visualization (via canvas)

## Development Workflow

### Local Development
1. **Backend**: `uvicorn app.main:app --reload`
2. **Frontend**: `npm run dev`
3. **Database**: PostgreSQL with Redis
4. **Environment**: Docker Compose for services

### Testing
- **Unit Tests**: pytest for backend services
- **Integration Tests**: API endpoint testing
- **E2E Tests**: Frontend component testing
- **Performance Tests**: Load testing for scalability

### Deployment
- **Frontend**: Vercel with global CDN
- **Backend**: Railway/DigitalOcean with auto-scaling
- **Database**: Managed PostgreSQL with read replicas
- **Monitoring**: Prometheus + Grafana

This codebase provides a comprehensive, scalable solution for AI-powered solar lead generation with advanced B2B integration capabilities, designed for rapid growth and operational excellence in the NYC solar market.
