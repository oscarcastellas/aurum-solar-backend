// Environment configuration
export const ENV = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  NODE_ENV: import.meta.env.VITE_NODE_ENV || 'development',
  GA_ID: import.meta.env.VITE_GA_ID || '',
  SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN || '',
} as const;

// Validate required environment variables
export const validateEnv = () => {
  const required = ['API_URL'];
  const missing = required.filter(key => !ENV[key as keyof typeof ENV]);
  
  if (missing.length > 0) {
    console.warn(`Missing environment variables: ${missing.join(', ')}`);
  }
  
  return missing.length === 0;
};
