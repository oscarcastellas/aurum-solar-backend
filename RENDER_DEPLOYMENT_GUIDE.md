# 🚀 **RENDER.COM FREE DEPLOYMENT GUIDE**

## 🎯 **OVERVIEW**

**Render.com** is the best free platform for FastAPI deployment with:
- ✅ **750 hours/month free** (enough for 24/7 operation)
- ✅ **512MB RAM, 0.1 CPU** (sufficient for FastAPI)
- ✅ **Free PostgreSQL database**
- ✅ **Free Redis cache**
- ✅ **Automatic HTTPS/SSL**
- ✅ **Custom domains**
- ✅ **GitHub integration**

---

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### **✅ Files Ready for Render:**
- `main_simple.py` - Simplified FastAPI app
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `start_render.py` - Startup script
- `app/` directory - All application code

### **✅ Features Included:**
- Health check endpoint (`/health`)
- CORS configured for frontend
- Database and Redis integration
- Error handling
- Structured logging

---

## 🚀 **DEPLOYMENT STEPS**

### **Step 1: Prepare GitHub Repository**

```bash
# Navigate to backend directory
cd /Users/oscarcastellas-cartwright/Documents/VSCode/aurum_solar/backend

# Initialize git if not already done
git init

# Add all files
git add .

# Commit changes
git commit -m "Prepare for Render deployment"

# Push to GitHub (replace with your repo URL)
git remote add origin https://github.com/yourusername/aurum-solar-backend.git
git push -u origin main
```

### **Step 2: Create Render Account**

1. **Visit**: https://render.com
2. **Sign up** with GitHub account
3. **Connect GitHub** repository

### **Step 3: Deploy Backend Service**

1. **Click "New +"** → **"Web Service"**
2. **Connect Repository**: Select your `aurum-solar-backend` repo
3. **Configure Service**:
   - **Name**: `aurum-solar-backend`
   - **Environment**: `Python 3`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Root Directory**: `backend` (if repo has frontend too)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main_simple:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

### **Step 4: Add Database**

1. **Click "New +"** → **"PostgreSQL"**
2. **Configure Database**:
   - **Name**: `aurum-solar-db`
   - **Database**: `aurum_solar`
   - **User**: `aurum_user`
   - **Plan**: `Free`

### **Step 5: Add Redis Cache**

1. **Click "New +"** → **"Redis"**
2. **Configure Redis**:
   - **Name**: `aurum-solar-redis`
   - **Plan**: `Free`

### **Step 6: Configure Environment Variables**

In your Render service settings, add:

```bash
# Core Configuration
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key-here
FRONTEND_URL=https://aurum-solar.vercel.app

# Database (Auto-configured by Render)
DATABASE_URL=${{aurum-solar-db.connectionString}}
REDIS_URL=${{aurum-solar-redis.connectionString}}

# API Keys (Add your actual keys)
OPENAI_API_KEY=your-openai-api-key
SERPAPI_KEY=your-serpapi-key

# Security
JWT_SECRET_KEY=your-jwt-secret-key
CSRF_SECRET_KEY=your-csrf-secret-key
```

---

## 🧪 **TESTING DEPLOYMENT**

### **Health Check**
```bash
curl https://aurum-solar-backend.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": 1694567890.123,
  "version": "1.0.0",
  "environment": "production",
  "response_time_ms": 45.67,
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### **Root Endpoint**
```bash
curl https://aurum-solar-backend.onrender.com/
```

**Expected Response:**
```json
{
  "message": "Aurum Solar API",
  "version": "1.0.0",
  "status": "operational",
  "documentation": "Contact support",
  "health": "/health"
}
```

---

## ⚙️ **RENDER CONFIGURATION**

### **Service Settings**
- **Auto-Deploy**: `Yes` (deploys on git push)
- **Health Check Path**: `/health`
- **Health Check Timeout**: `30 seconds`
- **Sleep After Inactivity**: `15 minutes` (free tier)

### **Database Settings**
- **PostgreSQL 15**
- **Connection Pooling**: Enabled
- **Backup**: Daily (free tier)

### **Redis Settings**
- **Redis 7**
- **Persistence**: Disabled (free tier)
- **Memory**: 25MB (free tier)

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

1. **Build Fails**
   - Check `requirements.txt` for missing packages
   - Verify Python version compatibility
   - Check build logs in Render dashboard

2. **Health Check Fails**
   - Verify `/health` endpoint is accessible
   - Check database connection
   - Review service logs

3. **Service Sleeps**
   - Free tier sleeps after 15 minutes of inactivity
   - First request after sleep takes 30-60 seconds
   - Consider upgrading to paid plan for production

4. **Database Connection Issues**
   - Verify `DATABASE_URL` environment variable
   - Check database service status
   - Review connection string format

### **Debug Commands**

```bash
# Check service logs
# Go to Render dashboard → Service → Logs

# Test database connection
curl https://aurum-solar-backend.onrender.com/health

# Check environment variables
# Go to Render dashboard → Service → Environment
```

---

## 📊 **PERFORMANCE EXPECTATIONS**

### **Free Tier Limits**
- **CPU**: 0.1 CPU (shared)
- **RAM**: 512MB
- **Storage**: 1GB
- **Bandwidth**: 100GB/month
- **Sleep**: After 15 minutes inactivity

### **Expected Performance**
- **Cold Start**: 30-60 seconds (after sleep)
- **Warm Response**: 100-500ms
- **Concurrent Users**: 10-50 (depending on usage)
- **Database Queries**: 1000/hour

---

## 🎯 **NEXT STEPS AFTER DEPLOYMENT**

### **1. Test All Endpoints**
```bash
# Health check
curl https://aurum-solar-backend.onrender.com/health

# Root endpoint
curl https://aurum-solar-backend.onrender.com/

# Test endpoint
curl https://aurum-solar-backend.onrender.com/api/v1/test
```

### **2. Update Frontend Configuration**
Update your Vite frontend to use the new backend URL:
```javascript
// In vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'https://aurum-solar-backend.onrender.com',
        changeOrigin: true,
        secure: true
      }
    }
  }
})
```

### **3. Monitor Performance**
- Check Render dashboard for metrics
- Monitor response times
- Watch for errors in logs

### **4. Scale When Ready**
- Upgrade to paid plan for production
- Add more resources as needed
- Implement proper monitoring

---

## 🎉 **SUCCESS CRITERIA**

### **Deployment Successful When:**
- ✅ Service shows "Live" status in Render
- ✅ Health check returns 200 status
- ✅ Database connection works
- ✅ Redis connection works
- ✅ All API endpoints respond correctly

### **Ready for Production When:**
- ✅ All tests pass
- ✅ Performance meets requirements
- ✅ Error handling works
- ✅ Logging is configured
- ✅ Monitoring is set up

---

## 📞 **SUPPORT RESOURCES**

### **Render Documentation**
- **Main Docs**: https://render.com/docs
- **Python Guide**: https://render.com/docs/python
- **Database Guide**: https://render.com/docs/databases

### **Community Support**
- **Render Discord**: https://discord.gg/render
- **GitHub Issues**: Your repository issues
- **Stack Overflow**: Tag `render.com`

---

**Your FastAPI backend will be live at**: `https://aurum-solar-backend.onrender.com`

**Ready to deploy? Follow the steps above!** 🚀
