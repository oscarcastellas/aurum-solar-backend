// Environment configuration - Railway Optimized
export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'https://backend-production-3f24.up.railway.app',
  WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL || 'wss://backend-production-3f24.up.railway.app',
  NODE_ENV: import.meta.env.VITE_NODE_ENV || 'development',
  ENVIRONMENT: import.meta.env.VITE_ENVIRONMENT || 'production',
  GA_ID: import.meta.env.VITE_GA_ID || '',
  SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN || '',
} as const;

// Validate required environment variables
export const validateEnv = () => {
  const required = ['API_BASE_URL'];
  const missing = required.filter(key => !ENV[key as keyof typeof ENV]);
  
  if (missing.length > 0) {
    console.warn(`Missing environment variables: ${missing.join(', ')}`);
  }
  
  return missing.length === 0;
};
