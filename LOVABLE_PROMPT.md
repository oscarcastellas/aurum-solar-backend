# Aurum Solar Frontend Development Prompt for Lovable.dev

## Project Overview

Build a comprehensive Next.js 14 frontend for **Aurum Solar**, an AI-powered solar lead generation platform targeting the NYC market. This is a B2B lead generation business that sells qualified solar leads to multiple platforms like SolarReviews, Modernize, and HomeAdvisor.

## Business Context

**Revenue Model**: Sell qualified leads to B2B platforms at $75-300 per lead
**Target Market**: NYC homeowners interested in solar
**Goal**: Launch in 14 days, generate $15K MRR by month 1
**Key Success Factors**: Lead quality, fast delivery, NYC market expertise

## Core Features Required

### 1. Landing Page & Lead Generation
- **Hero Section**: Compelling value proposition with NYC-specific messaging + **integrated chat interface** (chat bar/input field)
- **Inline Chat Experience**: Users can start asking questions directly on the hero page
- **Seamless Chat Transition**: Chat bar expands or redirects to full chat page when user engages
- **Savings Calculator**: Interactive calculator showing potential solar savings
- **NYC Market Intelligence**: Borough-specific data, incentives, and performance
- **Trust Signals**: Customer testimonials, certifications, guarantees
- **Lead Capture Forms**: Multiple conversion points throughout the site

### 2. AI Chat Interface
- **Conversational Lead Qualification**: Natural language chat for lead qualification
- **Real-time Messaging**: WebSocket-powered live chat
- **Lead Scoring Display**: Show quality score progression during conversation
- **NYC Market Expertise**: AI responses with local data and incentives
- **Mobile-Responsive Chat**: Optimized for mobile lead generation

### 3. Analytics Dashboard (B2B Focus)
- **Executive Summary**: Key metrics for business owners
- **Revenue Tracking**: Multi-platform revenue analytics
- **Lead Quality Metrics**: Quality distribution and conversion rates
- **NYC Market Performance**: Borough and zip code analytics
- **B2B Platform Performance**: Buyer performance comparison
- **Real-time Updates**: Live data without page refresh

### 4. B2B Integration Management
- **Platform Management**: Add/edit B2B buyer platforms
- **Lead Routing Configuration**: Set up routing rules and preferences
- **Delivery Monitoring**: Track lead delivery status and success rates
- **Revenue Reconciliation**: Monitor payments and commissions
- **Health Monitoring**: Platform status and alert management

## Technical Requirements

### Framework & Dependencies
- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **React Hook Form** + **Zod** for form handling
- **Socket.IO Client** for real-time features
- **Chart.js** or **Recharts** for data visualization

### API Integration
- **Backend API**: `http://localhost:8000/api/v1/`
- **WebSocket**: `ws://localhost:8000/ws/`
- **Authentication**: JWT-based auth system
- **Real-time Data**: WebSocket connections for live updates

### Key API Endpoints to Integrate
```
GET /analytics/executive-summary - Dashboard metrics
GET /analytics/revenue - Revenue analytics
GET /analytics/lead-quality - Lead quality metrics
GET /analytics/nyc-market - NYC market data
GET /analytics/b2b-performance - B2B platform performance
POST /leads/qualify - Submit lead for qualification
POST /chat/message - Send chat message
GET /platforms - List B2B platforms
POST /platforms - Create new platform
```

## Design Requirements

### Visual Identity
- **Primary Colors**: Green (#059669, #10b981) for solar/eco theme
- **Accent Colors**: Yellow (#fbbf24) for CTAs and highlights
- **Typography**: Modern, clean fonts (Inter or similar)
- **Style**: Professional, trustworthy, modern

### NYC-Specific Elements
- **Borough Performance**: Visual representation of NYC boroughs
- **Local Incentives**: Display federal, state, and city incentives
- **Market Data**: NYC-specific solar adoption rates and savings
- **Geographic Features**: Zip code lookup and mapping

### User Experience
- **Mobile-First**: Optimized for mobile lead generation
- **Fast Loading**: Optimized performance for conversion
- **Accessibility**: WCAG 2.1 AA compliance
- **Progressive Enhancement**: Works without JavaScript

## Page Structure

### 1. Landing Page (`/`)
- Hero section with value proposition + **integrated chat bar**
- **Inline chat experience** - users can start conversations directly
- **Chat expansion/transition** - seamless move to full chat page
- NYC market intelligence section
- Savings calculator
- Customer testimonials
- Trust signals and certifications
- Multiple CTA buttons

### 2. Chat Interface (`/chat`)
- Full-screen chat interface
- Message history and typing indicators
- Lead capture form integration
- Quality score display
- Mobile-optimized design

### 3. Analytics Dashboard (`/dashboard`)
- Executive summary widgets
- Revenue analytics charts
- Lead quality metrics
- NYC market intelligence
- B2B platform performance
- Real-time metrics

### 4. B2B Management (`/b2b`)
- Platform management interface
- Lead routing configuration
- Delivery monitoring
- Revenue reconciliation
- Health monitoring dashboard

## Component Architecture

### Core Components
```typescript
// Landing Page Components
- HeroSection (with integrated chat bar)
- InlineChatBar (embedded in hero)
- ChatTransition (seamless transition to full chat)
- ValuePropositionSection
- NYCMarketSection
- SavingsCalculatorSection
- TestimonialsSection
- TrustSignalsSection
- CTASection

// Chat Components
- ChatInterface
- MessageBubble
- TypingIndicator
- LeadCaptureForm
- QualityScoreDisplay

// Dashboard Components
- ExecutiveSummary
- RevenueOverview
- LeadQualityMetrics
- NYCMarketIntelligence
- B2BPerformance
- RealTimeMetrics
- ConversionFunnel

// B2B Management Components
- PlatformManager
- LeadRoutingConfig
- DeliveryMonitor
- RevenueReconciliation
- HealthMonitor
```

### Custom Hooks
```typescript
- useAnalytics() - Event tracking and metrics
- useWebSocket() - Real-time data connection
- useChat() - Chat state management
- useAuth() - Authentication state
- useDashboard() - Dashboard data management
```

## Data Flow & State Management

### Real-time Data
- WebSocket connections for live chat and analytics
- Automatic reconnection on connection loss
- Optimistic updates for better UX

### State Management
- React Context for global state
- Local state with useState for component state
- Custom hooks for shared logic

### Data Fetching
- SWR or React Query for server state
- Optimistic updates for better UX
- Error handling and retry logic

## Performance Requirements

### Core Web Vitals
- **LCP**: < 2.5s
- **FID**: < 100ms
- **CLS**: < 0.1

### Optimization
- Image optimization with Next.js Image
- Code splitting and lazy loading
- Bundle size optimization
- Caching strategies

## Security Considerations

### Data Protection
- Secure API communication (HTTPS)
- Input validation and sanitization
- XSS protection
- CSRF protection

### Authentication
- JWT token management
- Secure token storage
- Automatic token refresh
- Protected routes

## Testing Requirements

### Unit Tests
- Component testing with React Testing Library
- Hook testing
- Utility function testing

### Integration Tests
- API integration testing
- WebSocket connection testing
- Form submission testing

## Deployment Considerations

### Environment Configuration
- Environment variables for API URLs
- Feature flags for A/B testing
- Analytics configuration

### Build Optimization
- Production build optimization
- Static generation where possible
- CDN integration ready

## Success Metrics

### Conversion Metrics
- Lead generation rate
- Chat engagement rate
- Form completion rate
- CTA click-through rate

### Performance Metrics
- Page load times
- Time to interactive
- WebSocket connection stability
- API response times

## Additional Requirements

### Chat Integration
- **Hero Page Chat Bar**: Prominent, easy-to-find chat input on hero section
- **Progressive Enhancement**: Chat bar works without JavaScript, falls back to CTA
- **Mobile Optimization**: Touch-friendly chat interface on mobile devices
- **Conversation Persistence**: Chat history maintained across page transitions
- **Smart Routing**: Automatic transition to full chat page when conversation starts

### Accessibility
- Screen reader compatibility
- Keyboard navigation
- High contrast mode support
- Focus management

### Internationalization
- Ready for future i18n implementation
- RTL language support preparation
- Date/time formatting considerations

### SEO Optimization
- Meta tags and structured data
- Open Graph tags
- Twitter Card support
- Sitemap generation

## Deliverables Expected

1. **Complete Next.js 14 Application** with all pages and components
2. **Responsive Design** that works on all devices
3. **Real-time Features** with WebSocket integration
4. **Analytics Dashboard** with interactive charts
5. **B2B Management Interface** for platform management
6. **TypeScript Types** for all data structures
7. **Custom Hooks** for shared functionality
8. **Testing Suite** with unit and integration tests
9. **Documentation** for component usage and API integration
10. **Performance Optimization** with Core Web Vitals compliance

## Integration Notes

This frontend will integrate with a FastAPI backend that provides:
- AI conversation engine with OpenAI GPT-4
- B2B platform integration system
- Real-time analytics and monitoring
- Lead qualification and scoring
- Revenue tracking and reconciliation

The frontend should be designed to work seamlessly with these backend services while providing an excellent user experience for both lead generation and B2B management.

Focus on creating a high-converting, professional interface that effectively communicates the value proposition of solar energy in NYC while providing powerful tools for managing the B2B lead generation business.
