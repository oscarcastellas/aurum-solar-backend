// COMPLETE API CONFIGURATION - All 80+ Railway Endpoints
export const API_CONFIG_COMPLETE = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'https://aurum-solarv3-production.up.railway.app',
  WS_URL: import.meta.env.VITE_WS_BASE_URL || 'wss://aurum-solarv3-production.up.railway.app',
  
  // Complete endpoint mapping for all Railway APIs
  ENDPOINTS: {
    // ============================================================================
    // CORE SYSTEM APIs
    // ============================================================================
    HEALTH: '/health',
    ROOT: '/',
    TEST: '/api/v1/test',
    
    // ============================================================================
    // LEAD MANAGEMENT APIs (CRITICAL FOR REVENUE)
    // ============================================================================
    LEADS: {
      CREATE: '/api/v1/leads',
      GET_ALL: '/api/v1/leads',
      GET_BY_ID: '/api/v1/leads/{id}',
      UPDATE: '/api/v1/leads/{id}',
      DELETE: '/api/v1/leads/{id}',
      QUALIFY: '/api/v1/leads/{id}/qualify',
      SCORE: '/api/v1/leads/{id}/score',
      EXPORT: '/api/v1/leads/{id}/export'
    },
    
    // ============================================================================
    // CONVERSATION & AI APIs (LEAD QUALIFICATION)
    // ============================================================================
    CONVERSATION: {
      CHAT: '/api/v1/chat/message',
      AI_CHAT: '/api/v1/ai/chat',
      CONVERSATION: '/api/v1/conversation',
      NYC_MARKET_DATA: '/api/v1/conversation/nyc-market-data',
      CALCULATE_SAVINGS: '/api/v1/conversation/calculate-savings',
      LEAD_STATUS: '/api/v1/conversation/lead-status/{session_id}',
      PERFORMANCE: '/api/v1/conversation/performance-dashboard'
    },
    
    // ============================================================================
    // B2B EXPORT SYSTEM (REVENUE GENERATION - $75-300/lead)
    // ============================================================================
    B2B: {
      LEADS: '/api/v1/b2b/leads',
      PLATFORMS: '/api/v1/b2b/platforms',
      EXPORT: '/api/v1/b2b/export',
      DELIVER_LEAD: '/api/v1/b2b/deliver-lead',
      DELIVERY_STATUS: '/api/v1/b2b/delivery-status/{request_id}',
      HEALTH: '/api/v1/b2b/health',
      ROUTING: '/api/v1/b2b/routing/optimize',
      ROUTING_DECISION: '/api/v1/b2b/routing/decision',
      METRICS: '/api/v1/b2b/metrics'
    },
    
    // ============================================================================
    // EXPORT MANAGEMENT (LEAD SALES)
    // ============================================================================
    EXPORTS: {
      EXPORT_LEAD: '/api/v1/exports/export-lead',
      HISTORY: '/api/v1/exports/history',
      PLATFORMS_STATUS: '/api/v1/exports/platforms/status',
      BULK_EXPORT: '/api/v1/exports/bulk-export',
      DELIVER_LEAD: '/api/v1/deliver-lead',
      DELIVERY_STATUS: '/api/v1/delivery-status/{request_id}'
    },
    
    // ============================================================================
    // REVENUE ANALYTICS (PERFORMANCE TRACKING)
    // ============================================================================
    REVENUE: {
      EXECUTIVE_SUMMARY: '/api/v1/revenue/executive-summary',
      REAL_TIME_DASHBOARD: '/api/v1/revenue/real-time-dashboard',
      CONVERSATION_ANALYTICS: '/api/v1/revenue/conversation-analytics'
    },
    
    // ============================================================================
    // ANALYTICS & BUSINESS INTELLIGENCE
    // ============================================================================
    ANALYTICS: {
      REVENUE: '/api/v1/analytics/revenue',
      LEADS: '/api/v1/analytics/leads',
      PLATFORMS: '/api/v1/analytics/platforms',
      NYC_MARKET: '/api/v1/analytics/nyc-market',
      DASHBOARD: '/api/v1/analytics/dashboard',
      EXECUTIVE_SUMMARY: '/api/v1/analytics/executive-summary',
      LEAD_QUALITY: '/api/v1/analytics/lead-quality'
    },
    
    // ============================================================================
    // NYC MARKET DATA (GEOGRAPHIC INTELLIGENCE)
    // ============================================================================
    NYC: {
      MARKET_DATA: '/api/v1/nyc/market-data',
      BOROUGH_STATS: '/api/v1/nyc/borough-stats'
    },
    
    // ============================================================================
    // AI & SOLAR CALCULATIONS
    // ============================================================================
    AI: {
      CHAT: '/api/v1/ai/chat',
      SOLAR_SCORE: '/api/v1/ai/solar-score',
      QUESTIONS: '/api/v1/ai/questions/{lead_id}',
      ANALYZE: '/api/v1/ai/analyze/{lead_id}'
    },
    
    // ============================================================================
    // AUTHENTICATION & SECURITY
    // ============================================================================
    AUTH: {
      LOGIN: '/api/v1/auth/login',
      LOGOUT: '/api/v1/auth/logout',
      REFRESH: '/api/v1/auth/refresh',
      ME: '/api/v1/auth/me'
    },
    
    // ============================================================================
    // PLATFORM MANAGEMENT
    // ============================================================================
    PLATFORMS: {
      GET_ALL: '/api/v1/platforms',
      CREATE: '/api/v1/platforms',
      CONFIG: '/api/v1/platforms/{platform_code}/config',
      UPDATE_CONFIG: '/api/v1/platforms/{platform_code}/config',
      DEACTIVATE: '/api/v1/platforms/{platform_code}/deactivate'
    },
    
    // ============================================================================
    // PERFORMANCE MONITORING
    // ============================================================================
    PERFORMANCE: {
      DASHBOARD: '/api/v1/performance/dashboard',
      METRICS: '/api/v1/performance/metrics'
    },
    
    // ============================================================================
    // WEBSOCKET ENDPOINTS
    // ============================================================================
    WEBSOCKET: {
      CHAT: '/ws/chat',
      TEST: '/ws/chat' // HTTP test endpoint
    }
  },
  
  // Configuration
  TIMEOUT: 15000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
  RAILWAY_OPTIMIZED: true,
  
  // WebSocket Configuration
  WS_RECONNECT_DELAY: 5000,
  WS_MAX_RECONNECT_ATTEMPTS: 5,
  WS_HEARTBEAT_INTERVAL: 30000
};

// Enhanced Type Definitions
export interface LeadCreateRequest {
  name: string;
  email: string;
  phone: string;
  zip_code: string;
  monthly_bill: number;
  home_type?: string;
  roof_size?: number;
  notes?: string;
}

export interface LeadUpdateRequest {
  name?: string;
  email?: string;
  phone?: string;
  zip_code?: string;
  monthly_bill?: number;
  qualification_score?: number;
  estimated_value?: number;
  status?: string;
  notes?: string;
}

export interface B2BExportRequest {
  lead_id: string;
  platform: string;
  format?: 'json' | 'csv' | 'xml';
  priority?: 'low' | 'normal' | 'high';
}

export interface B2BExportResponse {
  export_id: string;
  lead_id: string;
  platform: string;
  status: 'pending' | 'processing' | 'exported' | 'failed';
  exported_at: string;
  error_message?: string;
}

export interface RevenueMetrics {
  total_revenue: number;
  monthly_revenue: number;
  revenue_growth: number;
  average_deal_size: number;
  conversion_rate: number;
  period: string;
}

export interface LeadAnalytics {
  total_leads: number;
  new_leads: number;
  qualified_leads: number;
  conversion_rate: number;
  lead_quality_score: number;
  period: string;
}

export interface ConversationAnalytics {
  total_conversations: number;
  average_duration: number;
  qualification_rate: number;
  conversion_rate: number;
  top_qualifying_questions: string[];
  performance_score: number;
}

export interface NYCBoroughStats {
  name: string;
  leads: number;
  conversion_rate: number;
  average_system_size: number;
  average_savings: number;
  incentives_available: number;
}

export interface SolarScoreRequest {
  zip_code: string;
  monthly_bill: number;
  roof_type: string;
  home_type?: string;
  roof_size?: number;
  shading?: string;
  orientation?: string;
}

export interface SolarScoreResponse {
  solar_score: number;
  zip_code: string;
  monthly_bill: number;
  roof_type: string;
  recommendations: string[];
  estimated_savings: number;
  system_size_recommendation: number;
  payback_period: number;
  calculated_at: string;
}

export interface WebSocketMessage {
  type: 'welcome' | 'ai_response' | 'user_message' | 'system_message' | 'error';
  message: string;
  session_id: string;
  timestamp?: number;
  data?: any;
}

export interface ConversationContext {
  session_id: string;
  lead_id?: string;
  zip_code?: string;
  monthly_bill?: number;
  home_type?: string;
  roof_size?: number;
  qualification_stage?: 'initial' | 'qualifying' | 'qualified' | 'converting';
  conversation_score?: number;
}

// API Response Wrapper
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
  timestamp?: string;
}

export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: any;
}

// Pagination
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Filter Options
export interface LeadFilters {
  status?: string;
  quality?: string;
  date_from?: string;
  date_to?: string;
  zip_code?: string;
  min_score?: number;
  max_score?: number;
}

export interface AnalyticsFilters {
  period?: '7d' | '30d' | '90d' | '1y';
  date_from?: string;
  date_to?: string;
  platform?: string;
  borough?: string;
}
