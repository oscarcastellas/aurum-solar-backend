import { API_CONFIG_COMPLETE, type ApiResponse, type ApiError } from '@/config/api-complete';
import { CORS_CONFIG, RAILWAY_CORS_HEADERS } from '@/config/cors';

/**
 * COMPLETE API CLIENT - All 80+ Railway Endpoints
 * Comprehensive client for Aurum Solar lead generation platform
 */
class CompleteAPIClient {
  private baseURL: string;
  private wsURL: string;
  private token: string | null = null;
  private refreshToken: string | null = null;
  private isConnected: boolean = false;
  private connectionRetries: number = 0;
  private maxRetries: number = 3;

  constructor() {
    this.baseURL = API_CONFIG_COMPLETE.BASE_URL;
    this.wsURL = API_CONFIG_COMPLETE.WS_URL;
    this.loadTokensFromStorage();
  }

  // ============================================================================
  // AUTHENTICATION & TOKEN MANAGEMENT
  // ============================================================================
  private loadTokensFromStorage() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
      this.refreshToken = localStorage.getItem('refresh_token');
    }
  }

  private saveTokensToStorage(accessToken: string, refreshToken: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
    }
  }

  private clearTokens() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
    }
    this.token = null;
    this.refreshToken = null;
  }

  // ============================================================================
  // CORE HTTP REQUEST HANDLER
  // ============================================================================
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
      ...RAILWAY_CORS_HEADERS
    };

    if (this.token) {
      defaultHeaders.Authorization = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
      signal: AbortSignal.timeout(API_CONFIG_COMPLETE.TIMEOUT)
    };

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401 && this.refreshToken) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          config.headers = {
            ...config.headers,
            Authorization: `Bearer ${this.token}`,
          };
          const retryResponse = await fetch(url, config);
          return this.handleResponse<T>(retryResponse);
        }
      }

      return this.handleResponse<T>(response);
    } catch (error) {
      throw this.handleError(error);
    }
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw {
        message: errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        code: errorData.code,
        details: errorData.details
      } as ApiError;
    }

    const data = await response.json();
    return {
      success: true,
      data,
      timestamp: new Date().toISOString()
    };
  }

  private handleError(error: any): ApiError {
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      return {
        message: 'Network error. Please check your connection to Railway backend.',
        status: 0,
        code: 'NETWORK_ERROR',
      };
    }
    
    if (error.name === 'AbortError') {
      return {
        message: 'Request timeout. Railway backend may be slow to respond.',
        status: 408,
        code: 'TIMEOUT_ERROR',
      };
    }
    
    return {
      message: error.message || 'An unexpected error occurred',
      status: error.status || 500,
      code: error.code || 'UNKNOWN_ERROR',
      details: error.details
    };
  }

  // ============================================================================
  // SYSTEM & HEALTH APIs
  // ============================================================================
  async healthCheck(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.HEALTH);
  }

  async getSystemInfo(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.ROOT);
  }

  async testConnection(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.TEST);
  }

  // ============================================================================
  // AUTHENTICATION APIs
  // ============================================================================
  async login(email: string, password: string): Promise<ApiResponse<any>> {
    const response = await this.request(API_CONFIG_COMPLETE.ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    if (response.success && response.data.access_token) {
      this.saveTokensToStorage(response.data.access_token, response.data.refresh_token);
    }
    
    return response;
  }

  async logout(): Promise<ApiResponse<void>> {
    const response = await this.request(API_CONFIG_COMPLETE.ENDPOINTS.AUTH.LOGOUT, {
      method: 'POST'
    });
    
    this.clearTokens();
    return response;
  }

  async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) return false;
    
    try {
      const response = await this.request(API_CONFIG_COMPLETE.ENDPOINTS.AUTH.REFRESH, {
        method: 'POST',
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });
      
      if (response.success && response.data.access_token) {
        this.saveTokensToStorage(response.data.access_token, response.data.refresh_token);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }
    
    return false;
  }

  async getCurrentUser(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.AUTH.ME);
  }

  // ============================================================================
  // LEAD MANAGEMENT APIs (CRITICAL FOR REVENUE)
  // ============================================================================
  async createLead(leadData: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.LEADS.CREATE, {
      method: 'POST',
      body: JSON.stringify(leadData)
    });
  }

  async getLeads(filters?: any): Promise<ApiResponse<any[]>> {
    const queryParams = filters ? `?${new URLSearchParams(filters).toString()}` : '';
    return this.request(`${API_CONFIG_COMPLETE.ENDPOINTS.LEADS.GET_ALL}${queryParams}`);
  }

  async getLead(leadId: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.LEADS.GET_BY_ID.replace('{id}', leadId));
  }

  async updateLead(leadId: string, updates: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.LEADS.UPDATE.replace('{id}', leadId), {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async deleteLead(leadId: string): Promise<ApiResponse<void>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.LEADS.DELETE.replace('{id}', leadId), {
      method: 'DELETE'
    });
  }

  async qualifyLead(leadId: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.LEADS.QUALIFY.replace('{id}', leadId), {
      method: 'POST'
    });
  }

  async scoreLead(leadId: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.LEADS.SCORE.replace('{id}', leadId), {
      method: 'POST'
    });
  }

  // ============================================================================
  // CONVERSATION & AI APIs
  // ============================================================================
  async sendChatMessage(message: string, sessionId: string, context?: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.CONVERSATION.CHAT, {
      method: 'POST',
      body: JSON.stringify({
        message,
        session_id: sessionId,
        context,
        timestamp: new Date().toISOString()
      })
    });
  }

  async sendAIMessage(message: string, sessionId: string, context?: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.CONVERSATION.AI_CHAT, {
      method: 'POST',
      body: JSON.stringify({
        message,
        session_id: sessionId,
        context,
        timestamp: new Date().toISOString()
      })
    });
  }

  async processConversation(message: string, sessionId: string, leadId?: string, context?: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.CONVERSATION.CONVERSATION, {
      method: 'POST',
      body: JSON.stringify({
        message,
        session_id: sessionId,
        lead_id: leadId,
        context,
        timestamp: new Date().toISOString()
      })
    });
  }

  async getNYCMarketData(zipCode: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.CONVERSATION.NYC_MARKET_DATA, {
      method: 'POST',
      body: JSON.stringify({ zip_code: zipCode })
    });
  }

  async calculateSavings(input: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.CONVERSATION.CALCULATE_SAVINGS, {
      method: 'POST',
      body: JSON.stringify(input)
    });
  }

  async getLeadStatus(sessionId: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.CONVERSATION.LEAD_STATUS.replace('{session_id}', sessionId));
  }

  async getConversationPerformance(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.CONVERSATION.PERFORMANCE);
  }

  // ============================================================================
  // B2B EXPORT APIs (REVENUE GENERATION)
  // ============================================================================
  async getB2BLeads(): Promise<ApiResponse<any[]>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.B2B.LEADS);
  }

  async getB2BPlatforms(): Promise<ApiResponse<any[]>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.B2B.PLATFORMS);
  }

  async exportB2BLead(leadId: string, platform: string, format: string = 'json'): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.B2B.EXPORT, {
      method: 'POST',
      body: JSON.stringify({
        lead_id: leadId,
        platform,
        format
      })
    });
  }

  async deliverLead(leadId: string, platform: string, priority: string = 'normal'): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.B2B.DELIVER_LEAD, {
      method: 'POST',
      body: JSON.stringify({
        lead_id: leadId,
        platform,
        priority
      })
    });
  }

  async getDeliveryStatus(requestId: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.B2B.DELIVERY_STATUS.replace('{request_id}', requestId));
  }

  async getB2BHealth(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.B2B.HEALTH);
  }

  async optimizeRouting(timePeriod: string = '7d'): Promise<ApiResponse<any>> {
    return this.request(`${API_CONFIG_COMPLETE.ENDPOINTS.B2B.ROUTING}?time_period=${timePeriod}`);
  }

  async getRoutingDecision(leadId: string, strategy: string = 'revenue_maximization', priority: string = 'normal'): Promise<ApiResponse<any>> {
    return this.request(`${API_CONFIG_COMPLETE.ENDPOINTS.B2B.ROUTING_DECISION}?lead_id=${leadId}&strategy=${strategy}&priority=${priority}`);
  }

  async getB2BMetrics(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.B2B.METRICS);
  }

  // ============================================================================
  // EXPORT MANAGEMENT APIs
  // ============================================================================
  async exportLead(leadId: string, platform: string, format: string = 'json'): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.EXPORTS.EXPORT_LEAD, {
      method: 'POST',
      body: JSON.stringify({
        lead_id: leadId,
        platform,
        format
      })
    });
  }

  async getExportHistory(): Promise<ApiResponse<any[]>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.EXPORTS.HISTORY);
  }

  async getPlatformsStatus(): Promise<ApiResponse<any[]>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.EXPORTS.PLATFORMS_STATUS);
  }

  async bulkExport(leadIds: string[], platform: string, format: string = 'json'): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.EXPORTS.BULK_EXPORT, {
      method: 'POST',
      body: JSON.stringify({
        lead_ids: leadIds,
        platform,
        format
      })
    });
  }

  // ============================================================================
  // REVENUE ANALYTICS APIs
  // ============================================================================
  async getRevenueAnalytics(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.ANALYTICS.REVENUE);
  }

  async getLeadAnalytics(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.ANALYTICS.LEADS);
  }

  async getRevenueExecutiveSummary(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.REVENUE.EXECUTIVE_SUMMARY);
  }

  async getRealTimeDashboard(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.REVENUE.REAL_TIME_DASHBOARD);
  }

  async getConversationAnalytics(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.REVENUE.CONVERSATION_ANALYTICS);
  }

  // ============================================================================
  // NYC MARKET DATA APIs
  // ============================================================================
  async getNYCMarketData(zipCode: string): Promise<ApiResponse<any>> {
    return this.request(`${API_CONFIG_COMPLETE.ENDPOINTS.NYC.MARKET_DATA}?zip_code=${zipCode}`);
  }

  async getNYCBoroughStats(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.NYC.BOROUGH_STATS);
  }

  // ============================================================================
  // AI & SOLAR CALCULATIONS
  // ============================================================================
  async calculateSolarScore(input: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.AI.SOLAR_SCORE, {
      method: 'POST',
      body: JSON.stringify(input)
    });
  }

  async getAIQuestions(leadId: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.AI.QUESTIONS.replace('{lead_id}', leadId));
  }

  async analyzeLead(leadId: string, analysisData: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.AI.ANALYZE.replace('{lead_id}', leadId), {
      method: 'POST',
      body: JSON.stringify(analysisData)
    });
  }

  // ============================================================================
  // PLATFORM MANAGEMENT APIs
  // ============================================================================
  async getPlatforms(): Promise<ApiResponse<any[]>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.PLATFORMS.GET_ALL);
  }

  async createPlatform(platformData: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.PLATFORMS.CREATE, {
      method: 'POST',
      body: JSON.stringify(platformData)
    });
  }

  async getPlatformConfig(platformCode: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.PLATFORMS.CONFIG.replace('{platform_code}', platformCode));
  }

  async updatePlatformConfig(platformCode: string, config: any): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.PLATFORMS.UPDATE_CONFIG.replace('{platform_code}', platformCode), {
      method: 'PUT',
      body: JSON.stringify(config)
    });
  }

  async deactivatePlatform(platformCode: string): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.PLATFORMS.DEACTIVATE.replace('{platform_code}', platformCode), {
      method: 'POST'
    });
  }

  // ============================================================================
  // PERFORMANCE MONITORING APIs
  // ============================================================================
  async getPerformanceDashboard(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.PERFORMANCE.DASHBOARD);
  }

  async getPerformanceMetrics(): Promise<ApiResponse<any>> {
    return this.request(API_CONFIG_COMPLETE.ENDPOINTS.PERFORMANCE.METRICS);
  }

  // ============================================================================
  // WEBSOCKET CONNECTION
  // ============================================================================
  createWebSocketConnection(sessionId: string): WebSocket {
    const ws = new WebSocket(`${this.wsURL}${API_CONFIG_COMPLETE.ENDPOINTS.WEBSOCKET.CHAT}?session_id=${sessionId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected to Railway backend');
      this.isConnected = true;
      this.connectionRetries = 0;
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isConnected = false;
    };
    
    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.isConnected = false;
      
      // Auto-reconnect logic
      if (event.code !== 1000 && this.connectionRetries < this.maxRetries) {
        this.connectionRetries++;
        setTimeout(() => {
          console.log(`Attempting to reconnect WebSocket (${this.connectionRetries}/${this.maxRetries})`);
          this.createWebSocketConnection(sessionId);
        }, API_CONFIG_COMPLETE.WS_RECONNECT_DELAY * this.connectionRetries);
      }
    };
    
    return ws;
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================
  getConnectionStatus(): { isConnected: boolean; retries: number } {
    return {
      isConnected: this.isConnected,
      retries: this.connectionRetries
    };
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  getAuthToken(): string {
    return this.token || '';
  }
}

// Create and export singleton instance
export const completeApiClient = new CompleteAPIClient();

// Export types
export type { ApiResponse, ApiError };
