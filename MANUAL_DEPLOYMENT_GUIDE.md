# 🚀 Manual Production Deployment Guide

## 📋 **DEPLOYMENT OVERVIEW**

Since the automated deployment script requires CLI authentication, here's the manual deployment process for Vercel + Railway:

---

## 🔧 **PREREQUISITES**

### **Required Tools**
1. **Node.js 18+** - Already installed
2. **Vercel CLI** - Install with: `npm install -g vercel`
3. **Railway CLI** - Install with: `npm install -g @railway/cli`

### **Required Accounts**
1. **Vercel Account** - Sign up at https://vercel.com
2. **Railway Account** - Sign up at https://railway.app
3. **GitHub Account** - For repository access

---

## 🚀 **STEP-BY-STEP DEPLOYMENT**

### **Step 1: Backend Deployment (Railway)**

**1.1 Login to Railway:**
```bash
railway login
```

**1.2 Navigate to Backend Directory:**
```bash
cd backend
```

**1.3 Initialize Railway Project:**
```bash
railway init
# Select "Create new project"
# Name: aurum-solar-backend
```

**1.4 Add Database Services:**
```bash
# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis
```

**1.5 Set Environment Variables:**
```bash
railway variables set ENVIRONMENT=production
railway variables set FRONTEND_URL=https://aurum-solar.vercel.app
railway variables set OPENAI_API_KEY=your-openai-api-key-here
railway variables set SECRET_KEY=your-secure-secret-key-here
railway variables set JWT_SECRET_KEY=your-jwt-secret-key-here
railway variables set CSRF_SECRET_KEY=your-csrf-secret-key-here
```

**1.6 Deploy Backend:**
```bash
railway up --detach
```

**1.7 Get Backend URL:**
```bash
railway domain
# Copy the URL (e.g., https://aurum-solar-backend.railway.app)
```

**1.8 Run Database Migrations:**
```bash
railway run python -m alembic upgrade head
```

---

### **Step 2: Frontend Deployment (Vercel)**

**2.1 Login to Vercel:**
```bash
cd ../aurum-chat-solar-main
vercel login
```

**2.2 Initialize Vercel Project:**
```bash
vercel
# Select "Set up and deploy"
# Project name: aurum-solar-frontend
# Directory: ./
```

**2.3 Set Environment Variables:**
```bash
vercel env add VITE_API_URL production
# Enter your Railway backend URL: https://aurum-solar-backend.railway.app

vercel env add VITE_WS_URL production
# Enter WebSocket URL: wss://aurum-solar-backend.railway.app

vercel env add VITE_APP_NAME production
# Enter: Aurum Solar

vercel env add VITE_ENVIRONMENT production
# Enter: production
```

**2.4 Deploy Frontend:**
```bash
vercel --prod
```

**2.5 Get Frontend URL:**
```bash
vercel ls
# Copy the production URL
```

---

### **Step 3: Update Backend CORS**

**3.1 Update Railway Environment:**
```bash
cd ../backend
railway variables set FRONTEND_URL=https://your-vercel-url.vercel.app
```

**3.2 Redeploy Backend:**
```bash
railway up --detach
```

---

### **Step 4: Validation**

**4.1 Test Backend Health:**
```bash
curl https://aurum-solar-backend.railway.app/health
```

**4.2 Test Frontend:**
```bash
curl https://your-vercel-url.vercel.app
```

**4.3 Run Validation Script:**
```bash
cd ..
FRONTEND_URL=https://your-vercel-url.vercel.app BACKEND_URL=https://aurum-solar-backend.railway.app ./scripts/validate-production.sh
```

---

## 🔧 **ENVIRONMENT VARIABLES REFERENCE**

### **Railway Environment Variables**
```bash
# Core Configuration
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key-here
FRONTEND_URL=https://aurum-solar.vercel.app

# Database (Auto-configured by Railway)
DATABASE_URL=${{Railway.DATABASE_URL}}
REDIS_URL=${{Railway.REDIS_URL}}
PORT=${{Railway.PORT}}

# API Keys
OPENAI_API_KEY=your-openai-api-key-here
SERPAPI_API_KEY=your-serpapi-key-here

# Security
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
CSRF_SECRET_KEY=your-csrf-secret-key-here

# CORS
ALLOWED_HOSTS=aurum-solar.vercel.app,aurum-solar-frontend.vercel.app

# Performance
WORKERS=4
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Features
ENABLE_B2B_EXPORT=true
ENABLE_REVENUE_ANALYTICS=true
ENABLE_SOLAR_CALCULATIONS=true
ENABLE_CONVERSATION_AI=true
```

### **Vercel Environment Variables**
```bash
# API Configuration
VITE_API_URL=https://aurum-solar-backend.railway.app
VITE_WS_URL=wss://aurum-solar-backend.railway.app

# App Configuration
VITE_APP_NAME=Aurum Solar
VITE_ENVIRONMENT=production

# Features
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_CHAT=true
VITE_ENABLE_CALCULATOR=true

# Performance
VITE_API_TIMEOUT=10000
VITE_WS_RECONNECT_INTERVAL=5000

# Security
VITE_ENABLE_CSP=true
VITE_TRUSTED_DOMAINS=aurum-solar-backend.railway.app
```

---

## 🌐 **DEPLOYMENT CHECKLIST**

### **Backend Deployment ✅**
- [ ] Railway CLI installed and authenticated
- [ ] PostgreSQL database added
- [ ] Redis cache added
- [ ] Environment variables set
- [ ] Backend deployed successfully
- [ ] Database migrations run
- [ ] Backend URL obtained
- [ ] Health check passes

### **Frontend Deployment ✅**
- [ ] Vercel CLI installed and authenticated
- [ ] Vercel project initialized
- [ ] Environment variables set
- [ ] Frontend deployed successfully
- [ ] Frontend URL obtained
- [ ] Frontend loads correctly

### **Integration ✅**
- [ ] Backend CORS updated with frontend URL
- [ ] Backend redeployed
- [ ] API connectivity working
- [ ] WebSocket connectivity working
- [ ] End-to-end integration tested

### **Validation ✅**
- [ ] Backend health check passes
- [ ] Frontend accessibility confirmed
- [ ] API endpoints responding
- [ ] Database connectivity confirmed
- [ ] Redis connectivity confirmed
- [ ] Performance metrics acceptable

---

## 🚨 **TROUBLESHOOTING**

### **Common Issues**

**Backend Deployment Fails:**
```bash
# Check Railway logs
railway logs

# Check environment variables
railway variables

# Redeploy with verbose output
railway up --detach --verbose
```

**Frontend Build Fails:**
```bash
# Check build locally
npm run build

# Check Vercel logs
vercel logs

# Redeploy with debug
vercel --prod --debug
```

**CORS Issues:**
```bash
# Update frontend URL in Railway
railway variables set FRONTEND_URL=https://your-actual-vercel-url.vercel.app

# Redeploy backend
railway up --detach
```

**Database Connection Issues:**
```bash
# Check database status
railway status

# Run migrations manually
railway run python -m alembic upgrade head

# Check database connectivity
railway run python -c "from app.core.database import engine; print('DB OK' if engine else 'DB ERROR')"
```

---

## 📊 **POST-DEPLOYMENT VALIDATION**

### **Health Checks**
```bash
# Backend health
curl https://aurum-solar-backend.railway.app/health

# API health
curl https://aurum-solar-backend.railway.app/api/v1/health

# Frontend health
curl https://aurum-solar.vercel.app

# API documentation
curl https://aurum-solar-backend.railway.app/docs
```

### **Performance Tests**
```bash
# API response time
curl -w "@curl-format.txt" -o /dev/null -s https://aurum-solar-backend.railway.app/health

# Frontend load time
curl -w "@curl-format.txt" -o /dev/null -s https://aurum-solar.vercel.app
```

### **Integration Tests**
```bash
# Test chat API
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test"}' \
  https://aurum-solar-backend.railway.app/api/v1/chat/message

# Test lead export
curl https://aurum-solar-backend.railway.app/api/v1/leads/exportable

# Test revenue analytics
curl https://aurum-solar-backend.railway.app/api/v1/revenue-dashboard/executive-summary
```

---

## 🎯 **SUCCESS CRITERIA**

### **Deployment Success**
- ✅ Backend deployed and healthy
- ✅ Frontend deployed and accessible
- ✅ Database migrations completed
- ✅ Environment variables configured
- ✅ CORS properly configured
- ✅ Health checks passing

### **Integration Success**
- ✅ API endpoints responding
- ✅ WebSocket connections working
- ✅ Database connectivity confirmed
- ✅ Redis connectivity confirmed
- ✅ End-to-end functionality tested

### **Performance Success**
- ✅ API response time <2 seconds
- ✅ Frontend load time <3 seconds
- ✅ Database query time <100ms
- ✅ No critical errors in logs

---

## 🚀 **NEXT STEPS AFTER DEPLOYMENT**

1. **Configure Custom Domains** (Optional)
2. **Set Up Monitoring** - Run `./scripts/monitor-production.sh`
3. **Begin B2B Outreach** - Start generating leads
4. **Monitor Revenue** - Track against $15K MRR target
5. **Optimize Performance** - Based on real usage data

**Your Aurum Solar platform will be ready for immediate revenue generation!**
