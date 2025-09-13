# Vercel Environment Configuration

## Environment Variables for Vercel Dashboard

Set these environment variables in your Vercel project dashboard:

### API Configuration
```
VITE_API_URL=https://aurum-solar-backend.railway.app
VITE_WS_URL=wss://aurum-solar-backend.railway.app
```

### App Configuration
```
VITE_APP_NAME=Aurum Solar
VITE_ENVIRONMENT=production
```

### Feature Flags
```
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_CHAT=true
VITE_ENABLE_CALCULATOR=true
```

### External Services
```
VITE_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
VITE_HOTJAR_ID=XXXXXXXX
```

### Performance
```
VITE_API_TIMEOUT=10000
VITE_WS_RECONNECT_INTERVAL=5000
```

### Security
```
VITE_ENABLE_CSP=true
VITE_TRUSTED_DOMAINS=aurum-solar-backend.railway.app
```

## Setting Environment Variables in Vercel

1. Go to your Vercel dashboard
2. Navigate to your project
3. Go to Settings > Environment Variables
4. Add each variable above
5. Make sure to set them for "Production" environment
6. Redeploy your application

## Custom Domain Configuration

1. Go to Settings > Domains
2. Add your custom domain (e.g., aurum-solar.com)
3. Configure DNS records as instructed
4. Enable HTTPS (automatic with Vercel)
