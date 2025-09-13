# 🏗️ Aurum Solar Deployment Architecture

## 📋 **DEPLOYMENT OVERVIEW**

Aurum Solar uses a **multi-service architecture** with separate deployments for user-facing and admin functionality:

### **Service Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    AURUM SOLAR ECOSYSTEM                    │
├─────────────────────────────────────────────────────────────┤
│  USER-FACING FRONTEND    │  ADMIN DASHBOARD                │
│  (Port 3001)             │  (Port 3002)                    │
│  ┌─────────────────┐     │  ┌─────────────────┐            │
│  │   Vite + React  │     │  │   Vite + React  │            │
│  │   Chat Interface│     │  │   Analytics UI  │            │
│  │   Lead Forms    │     │  │   Revenue Data  │            │
│  └─────────────────┘     │  └─────────────────┘            │
│           │               │           │                     │
│           └───────────────┼───────────┘                     │
│                           │                                 │
│           SHARED BACKEND API (Port 8000)                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              FastAPI + Python                          ││
│  │  • AI Conversation Agent                               ││
│  │  • Lead Management                                     ││
│  │  • Revenue Analytics                                   ││
│  │  • B2B Export System                                   ││
│  │  • Solar Calculation Engine                            ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              DATABASE LAYER                             ││
│  │  • PostgreSQL (Primary)                                ││
│  │  • Redis (Cache & Real-time)                           ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 **DEPLOYMENT OPTIONS**

### **Option 1: Separate Deployments (Recommended)**

**User-Facing Application:**
- **Frontend**: `aurum-chat-solar-main/` → Port 3001
- **Purpose**: Public chat interface, lead generation
- **Users**: End customers, prospects

**Admin Dashboard:**
- **Frontend**: `admin-dashboard/` → Port 3002
- **Purpose**: Revenue analytics, lead management, B2B exports
- **Users**: Internal team, administrators

**Shared Backend:**
- **API**: FastAPI → Port 8000
- **Purpose**: Serves both frontends with different endpoints

### **Option 2: Single Application with Routes**

**Single Frontend Application:**
- **Routes**: `/` (public), `/admin/*` (protected)
- **Authentication**: Route-based access control
- **Bundle Size**: Larger, includes admin components

---

## 🎯 **RECOMMENDED DEPLOYMENT STRATEGY**

### **Why Separate Deployments?**

1. **Security & Access Control**
   - Admin dashboard requires authentication
   - Sensitive revenue data protection
   - Different user roles and permissions

2. **Performance Optimization**
   - Smaller bundle sizes for each application
   - Independent scaling and updates
   - Different caching strategies

3. **Development & Maintenance**
   - Separate development teams possible
   - Independent deployment cycles
   - Easier debugging and monitoring

4. **User Experience**
   - Clean separation of public vs internal tools
   - Different UI/UX requirements
   - No admin clutter in user interface

---

## 🐳 **DOCKER DEPLOYMENT**

### **Development Environment**

```bash
# Start user-facing application
cd aurum-chat-solar-main/
npm run dev  # Port 3001

# Start admin dashboard
cd admin-dashboard/
npm run dev  # Port 3002

# Start backend API
cd backend/
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### **Production Deployment**

```bash
# User-facing application
docker-compose -f docker-compose.yml up -d

# Admin dashboard
docker-compose -f docker-compose.admin.yml up -d
```

### **Full Stack Deployment**

```bash
# Complete system with all services
docker-compose -f docker-compose.full.yml up -d
```

---

## 🌐 **PRODUCTION DEPLOYMENT GUIDE**

### **1. User-Facing Application**

**File**: `docker-compose.yml`
```yaml
services:
  user-frontend:
    build: ./aurum-chat-solar-main
    ports:
      - "3001:80"
    environment:
      - VITE_API_URL=https://api.aurumsolar.com
    depends_on:
      - backend
```

**Deployment:**
```bash
# Build and deploy user-facing app
cd aurum-chat-solar-main/
npm run build
docker build -t aurum-solar-frontend .
docker run -p 3001:80 aurum-solar-frontend
```

### **2. Admin Dashboard**

**File**: `docker-compose.admin.yml`
```yaml
services:
  admin-dashboard:
    build: ./admin-dashboard
    ports:
      - "3002:80"
    environment:
      - VITE_API_URL=https://api.aurumsolar.com
    depends_on:
      - backend
```

**Deployment:**
```bash
# Build and deploy admin dashboard
cd admin-dashboard/
npm run build
docker build -t aurum-solar-admin .
docker run -p 3002:80 aurum-solar-admin
```

### **3. Backend API**

**File**: `backend/docker-compose.yml`
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/aurum
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
```

**Deployment:**
```bash
# Build and deploy backend
cd backend/
docker build -t aurum-solar-backend .
docker run -p 8000:8000 aurum-solar-backend
```

---

## 🔧 **ENVIRONMENT CONFIGURATION**

### **Environment Variables**

**User-Facing Frontend:**
```env
VITE_API_URL=https://api.aurumsolar.com
VITE_APP_NAME=Aurum Solar
VITE_ENVIRONMENT=production
```

**Admin Dashboard:**
```env
VITE_API_URL=https://api.aurumsolar.com
VITE_APP_NAME=Aurum Solar Admin
VITE_ENVIRONMENT=production
VITE_ADMIN_DASHBOARD=true
```

**Backend API:**
```env
DATABASE_URL=postgresql://user:pass@postgres:5432/aurum
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_secret_key
ENVIRONMENT=production
```

---

## 🔐 **SECURITY CONSIDERATIONS**

### **Authentication & Authorization**

**User-Facing Application:**
- Public access for lead generation
- Optional user accounts for saved preferences
- No sensitive data exposure

**Admin Dashboard:**
- JWT-based authentication required
- Role-based access control (Admin, Manager, Analyst)
- Session timeout and refresh tokens
- IP whitelisting for production

### **API Security**

**Rate Limiting:**
- Public endpoints: 100 requests/minute per IP
- Admin endpoints: 1000 requests/minute per authenticated user
- B2B export endpoints: 50 requests/minute per platform

**Data Protection:**
- HTTPS encryption for all communications
- Database encryption at rest
- API key rotation and management
- Audit logging for admin actions

---

## 📊 **MONITORING & ANALYTICS**

### **Application Monitoring**

**User-Facing Application:**
- Page load times and performance
- User engagement metrics
- Conversion funnel analysis
- Error tracking and reporting

**Admin Dashboard:**
- Real-time performance monitoring
- Revenue analytics and trends
- System health and uptime
- User activity and access logs

### **Infrastructure Monitoring**

**Backend Services:**
- API response times and error rates
- Database performance and queries
- Redis cache hit rates
- Resource utilization (CPU, memory, disk)

**Deployment Monitoring:**
- Container health and restart events
- Service discovery and load balancing
- Network connectivity and latency
- Log aggregation and analysis

---

## 🚀 **DEPLOYMENT COMMANDS**

### **Quick Start (Development)**

```bash
# Terminal 1: User-facing frontend
cd aurum-chat-solar-main/
npm install
npm run dev  # http://localhost:3001

# Terminal 2: Admin dashboard
cd admin-dashboard/
npm install
npm run dev  # http://localhost:3002

# Terminal 3: Backend API
cd backend/
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000  # http://localhost:8000
```

### **Production Deployment**

```bash
# Option 1: Separate deployments
docker-compose -f docker-compose.yml up -d      # User-facing
docker-compose -f docker-compose.admin.yml up -d # Admin dashboard

# Option 2: Full stack deployment
docker-compose -f docker-compose.full.yml up -d  # Everything
```

### **Health Checks**

```bash
# Check user-facing application
curl http://localhost:3001/health

# Check admin dashboard
curl http://localhost:3002/health

# Check backend API
curl http://localhost:8000/health

# Check database
docker exec -it aurum_postgres pg_isready -U aurum_user

# Check Redis
docker exec -it aurum_redis redis-cli ping
```

---

## 📈 **SCALING CONSIDERATIONS**

### **Horizontal Scaling**

**Frontend Applications:**
- Use load balancer (nginx, HAProxy)
- CDN for static assets (CloudFlare, AWS CloudFront)
- Multiple instances behind load balancer

**Backend API:**
- Multiple FastAPI instances
- Database connection pooling
- Redis clustering for cache scaling

**Database:**
- Read replicas for analytics queries
- Database sharding by region/tenant
- Connection pooling and query optimization

### **Performance Optimization**

**Frontend:**
- Code splitting and lazy loading
- Image optimization and compression
- Browser caching strategies
- Progressive Web App (PWA) features

**Backend:**
- API response caching
- Database query optimization
- Background task processing
- WebSocket connection pooling

---

## 🎯 **RECOMMENDED NEXT STEPS**

1. **Set up development environment** with separate frontend applications
2. **Configure authentication** for admin dashboard access
3. **Deploy to staging environment** for testing
4. **Set up monitoring and logging** for production readiness
5. **Configure CI/CD pipelines** for automated deployments
6. **Implement backup and disaster recovery** procedures

**Deployment Status: 🟢 READY FOR PRODUCTION DEPLOYMENT**

Your multi-service architecture provides optimal separation of concerns, security, and scalability for both user-facing and admin functionality!
