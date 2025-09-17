import { API_CONFIG, type ApiResponse, type ApiError, type ChatRequest, type ChatResponse } from '@/config/api';
import { CORS_CONFIG, RAILWAY_CORS_HEADERS } from '@/config/cors';

/**
 * Railway-Optimized API Client
 * Enhanced for Railway deployment with retry logic, timeout handling, and CORS optimization
 */
class RailwayAPIClient {
  private baseURL: string;
  private wsURL: string;
  private token: string | null = null;
  private refreshToken: string | null = null;
  private isConnected: boolean = false;
  private connectionRetries: number = 0;
  private maxRetries: number = 3;

  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.wsURL = API_CONFIG.WS_URL;
    this.loadTokensFromStorage();
  }

  // Token Management
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

  // Health check with Railway-specific timeout
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}${API_CONFIG.ENDPOINTS.HEALTH}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...RAILWAY_CORS_HEADERS
        },
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });
      
      this.isConnected = response.ok;
      this.connectionRetries = 0;
      
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      this.isConnected = false;
      this.connectionRetries++;
      return false;
    }
  }

  // Enhanced HTTP request with Railway optimizations
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
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
    };

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401 && this.refreshToken) {
        // Try to refresh token
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          // Retry the original request
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
      } as ApiError;
    }

    const data = await response.json();
    return {
      success: true,
      data,
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
    };
  }

  // Chat message with retry logic
  async sendChatMessage(message: string, sessionId: string): Promise<ChatResponse> {
    const maxRetries = API_CONFIG.RETRY_ATTEMPTS;
    let lastError: Error;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch(`${this.baseURL}${API_CONFIG.ENDPOINTS.CHAT}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.getAuthToken()}`,
            ...RAILWAY_CORS_HEADERS
          },
          body: JSON.stringify({
            message,
            session_id: sessionId,
            timestamp: new Date().toISOString()
          }),
          signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return data;
      } catch (error) {
        lastError = error as Error;
        console.warn(`Chat message attempt ${attempt} failed:`, error);
        
        if (attempt < maxRetries) {
          await this.delay(1000 * attempt); // Exponential backoff
        }
      }
    }
    
    throw lastError!;
  }

  // WebSocket connection with Railway optimization
  createWebSocketConnection(sessionId: string): WebSocket {
    const ws = new WebSocket(`${this.wsURL}/ws/chat/${sessionId}`);
    
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
      
      // Auto-reconnect logic for Railway
      if (event.code !== 1000 && this.connectionRetries < this.maxRetries) {
        this.connectionRetries++;
        setTimeout(() => {
          console.log(`Attempting to reconnect WebSocket (${this.connectionRetries}/${this.maxRetries})`);
          this.createWebSocketConnection(sessionId);
        }, 5000 * this.connectionRetries);
      }
    };
    
    return ws;
  }

  // Authentication Methods - DISABLED (endpoints not available on backend)
  // async login(email: string, password: string): Promise<any> {
  //   throw new Error('Authentication not implemented on backend');
  // }

  // async logout(): Promise<void> {
  //   this.clearTokens();
  // }

  // async refreshAccessToken(): Promise<boolean> {
  //   return false;
  // }

  // Utility methods
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private getAuthToken(): string {
    return this.token || '';
  }

  // Connection status
  getConnectionStatus(): { isConnected: boolean; retries: number } {
    return {
      isConnected: this.isConnected,
      retries: this.connectionRetries
    };
  }

  // Test Railway connection
  async testConnection(): Promise<{
    success: boolean;
    latency: number;
    error?: string;
  }> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${this.baseURL}${API_CONFIG.ENDPOINTS.HEALTH}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const latency = Date.now() - startTime;
      
      if (response.ok) {
        return { success: true, latency };
      } else {
        return { 
          success: false, 
          latency, 
          error: `HTTP ${response.status}: ${response.statusText}` 
        };
      }
    } catch (error) {
      return { 
        success: false, 
        latency: Date.now() - startTime, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }
}

// Create and export singleton instance
export const railwayApiClient = new RailwayAPIClient();

// Export types for use in components
export type { ApiResponse, ApiError, ChatRequest, ChatResponse };
