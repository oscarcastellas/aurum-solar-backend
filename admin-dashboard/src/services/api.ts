/**
 * API service for admin dashboard
 * Handles all communication with the backend analytics API
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('auth_token')
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  }

  const response = await fetch(`${API_BASE_URL}${url}`, config)
  
  if (!response.ok) {
    throw new ApiError(response.status, `API request failed: ${response.statusText}`)
  }
  
  return response.json()
}

// Dashboard API
export const fetchDashboardMetrics = async () => {
  return fetchWithAuth('/v1/revenue-dashboard/dashboard-metrics')
}

export const fetchExecutiveSummary = async (periodDays = 30) => {
  return fetchWithAuth(`/v1/revenue-dashboard/executive-summary?period_days=${periodDays}`)
}

export const fetchRealTimeDashboard = async () => {
  return fetchWithAuth('/v1/revenue-dashboard/real-time-dashboard')
}

export const fetchConversationAnalytics = async (periodDays = 30) => {
  return fetchWithAuth(`/v1/revenue-dashboard/conversation-analytics?period_days=${periodDays}`)
}

export const fetchMarketPerformance = async (periodDays = 30) => {
  return fetchWithAuth(`/v1/revenue-dashboard/market-performance?period_days=${periodDays}`)
}

export const fetchRevenueOptimization = async (periodDays = 30) => {
  return fetchWithAuth(`/v1/revenue-dashboard/revenue-optimization?period_days=${periodDays}`)
}

export const fetchPerformanceTargets = async () => {
  return fetchWithAuth('/v1/revenue-dashboard/performance-targets')
}

export const fetchRevenueTrends = async (periodDays = 30, granularity = 'daily') => {
  return fetchWithAuth(`/v1/revenue-dashboard/revenue-trends?period_days=${periodDays}&granularity=${granularity}`)
}

export const fetchPlatformPerformance = async (periodDays = 30) => {
  return fetchWithAuth(`/v1/revenue-dashboard/platform-performance?period_days=${periodDays}`)
}

export const fetchQualityAnalytics = async (periodDays = 30) => {
  return fetchWithAuth(`/v1/revenue-dashboard/quality-analytics?period_days=${periodDays}`)
}

export const fetchOptimizationInsights = async (insightType?: string, priority?: string, limit = 10) => {
  const params = new URLSearchParams()
  if (insightType) params.append('insight_type', insightType)
  if (priority) params.append('priority', priority)
  params.append('limit', limit.toString())
  
  return fetchWithAuth(`/v1/revenue-dashboard/optimization-insights?${params}`)
}

// B2B Export API
export const fetchExportableLeads = async (qualityTier?: string, limit = 50) => {
  const params = new URLSearchParams()
  if (qualityTier) params.append('quality_tier', qualityTier)
  params.append('limit', limit.toString())
  
  return fetchWithAuth(`/v1/b2b/exportable-leads?${params}`)
}

export const exportSingleLead = async (leadId: string, platform: string, format = 'json') => {
  return fetchWithAuth('/v1/b2b/export-lead', {
    method: 'POST',
    body: JSON.stringify({
      lead_id: leadId,
      platform,
      format,
      priority: 'normal'
    })
  })
}

export const exportBatchLeads = async (platform: string, qualityTier?: string, maxLeads = 20) => {
  return fetchWithAuth('/v1/b2b/export-batch', {
    method: 'POST',
    body: JSON.stringify({
      platform,
      quality_tier: qualityTier,
      max_leads: maxLeads,
      format: 'json'
    })
  })
}

export const previewLeadExport = async (leadId: string, platform: string, format = 'json') => {
  return fetchWithAuth('/v1/b2b/preview-export', {
    method: 'POST',
    body: JSON.stringify({
      lead_id: leadId,
      platform,
      format
    })
  })
}

export const getAvailablePlatforms = async () => {
  return fetchWithAuth('/v1/b2b/platforms')
}

export const getLeadExportHistory = async (leadId: string) => {
  return fetchWithAuth(`/v1/b2b/export-history/${leadId}`)
}

export const getExportStatistics = async (days = 30) => {
  return fetchWithAuth(`/v1/b2b/export-stats?days=${days}`)
}

// Analytics Tracking API
export const trackConversation = async (sessionId: string, leadId?: string) => {
  return fetchWithAuth('/v1/revenue-dashboard/track-conversation', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      lead_id: leadId
    })
  })
}

export const trackRevenue = async (leadId: string, platform: string, amount: number) => {
  return fetchWithAuth('/v1/revenue-dashboard/track-revenue', {
    method: 'POST',
    body: JSON.stringify({
      lead_id: leadId,
      platform,
      amount
    })
  })
}

// Data Export API
export const exportAnalyticsData = async (dataType: string, periodDays = 30, format = 'csv') => {
  return fetchWithAuth('/v1/revenue-dashboard/export-data', {
    method: 'POST',
    body: JSON.stringify({
      data_type: dataType,
      period_days: periodDays,
      format
    })
  })
}

// Authentication API
export const login = async (email: string, password: string) => {
  const response = await fetch(`${API_BASE_URL}/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    throw new ApiError(response.status, 'Login failed')
  }

  const data = await response.json()
  localStorage.setItem('auth_token', data.access_token)
  return data
}

export const logout = () => {
  localStorage.removeItem('auth_token')
}

export const getCurrentUser = async () => {
  return fetchWithAuth('/v1/auth/me')
}

// System Health API
export const testAnalyticsSystem = async () => {
  return fetchWithAuth('/v1/revenue-dashboard/test-analytics')
}

export const testB2BExportSystem = async () => {
  return fetchWithAuth('/v1/b2b/test-export')
}

// Utility functions
export const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

export const formatPercentage = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value)
}

export const formatNumber = (value: number) => {
  return new Intl.NumberFormat('en-US').format(value)
}

export const formatDate = (date: string | Date) => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date))
}

export const formatDateShort = (date: string | Date) => {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
  }).format(new Date(date))
}
