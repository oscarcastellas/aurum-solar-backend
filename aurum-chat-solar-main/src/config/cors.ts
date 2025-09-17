// CORS Configuration for Railway Backend
export const CORS_CONFIG = {
  origin: [
    'https://aurum-solar.vercel.app',
    'http://localhost:3001',
    'http://localhost:5173', // Vite dev server
    'https://backend-production-3f24.up.railway.app'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: [
    'Content-Type', 
    'Authorization', 
    'X-Requested-With',
    'Accept',
    'Origin',
    'Access-Control-Request-Method',
    'Access-Control-Request-Headers'
  ],
  exposedHeaders: [
    'X-Total-Count',
    'X-Page-Count',
    'X-Current-Page'
  ],
  maxAge: 86400, // 24 hours
  preflightContinue: false,
  optionsSuccessStatus: 200
} as const;

// Railway-specific CORS headers
export const RAILWAY_CORS_HEADERS = {
  'Access-Control-Allow-Origin': 'https://aurum-solar.vercel.app',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
  'Access-Control-Allow-Credentials': 'true',
  'Access-Control-Max-Age': '86400'
} as const;

// CORS validation helper
export const validateCORSOrigin = (origin: string): boolean => {
  return CORS_CONFIG.origin.includes(origin);
};

// CORS error messages
export const CORS_ERRORS = {
  INVALID_ORIGIN: 'Invalid origin. Please check CORS configuration.',
  MISSING_HEADERS: 'Missing required CORS headers.',
  PREFLIGHT_FAILED: 'CORS preflight request failed.',
  CREDENTIALS_NOT_ALLOWED: 'Credentials not allowed for this origin.'
} as const;
