import { API_CONFIG, type ApiResponse, type ApiError, type AuthResponse, type LoginRequest, type ChatRequest, type ChatResponse, type SavingsInput, type SavingsResult, type NYCStatsResponse, type LeadData, type Lead, type SolarData, type SolarScoreResponse } from '@/config/api';

class ApiClient {
  private baseURL: string;
  private token: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseURL: string = API_CONFIG.BASE_URL) {
    this.baseURL = baseURL;
    this.loadTokensFromStorage();
  }

  // Token Management
  private loadTokensFromStorage() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
    }
  }

  private saveTokensToStorage(accessToken: string, refreshToken: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
    }
  }

  private clearTokens() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
    this.token = null;
    this.refreshToken = null;
  }

  // HTTP Methods
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
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
        message: 'Network error. Please check your connection.',
        status: 0,
        code: 'NETWORK_ERROR',
      };
    }
    
    return {
      message: error.message || 'An unexpected error occurred',
      status: error.status || 500,
      code: error.code || 'UNKNOWN_ERROR',
    };
  }

  // Authentication Methods - DISABLED (endpoints not available on backend)
  // async login(credentials: LoginRequest): Promise<AuthResponse> {
  //   throw new Error('Authentication not implemented on backend');
  // }

  // async logout(): Promise<void> {
  //   this.clearTokens();
  // }

  // async refreshAccessToken(): Promise<boolean> {
  //   return false;
  // }

  // AI Chat Methods - DISABLED (endpoints not available on backend)
  // async sendMessage(request: ChatRequest): Promise<ChatResponse> {
  //   throw new Error('AI chat not implemented on backend');
  // }

  // async getSolarScore(data: SolarData): Promise<SolarScoreResponse> {
  //   throw new Error('Solar score not implemented on backend');
  // }

  // Analytics Methods - DISABLED (endpoints not available on backend)
  // async calculateSavings(input: SavingsInput): Promise<SavingsResult> {
  //   throw new Error('Savings calculation not implemented on backend');
  // }

  // async getNYCBoroughStats(): Promise<NYCStatsResponse> {
  //   throw new Error('NYC borough stats not implemented on backend');
  // }

  // async getNYCIncentives(zipCode: string): Promise<IncentiveData[]> {
  //   throw new Error('NYC incentives not implemented on backend');
  // }

  // async getElectricityRates(zipCode: string): Promise<{ rate: number; utility: string }> {
  //   throw new Error('Electricity rates not implemented on backend');
  // }

  // Lead Methods
  async createLead(leadData: { name: string; email: string; phone: string; zip_code: string; monthly_bill: number }): Promise<Lead> {
    const response = await this.request<Lead>(
      API_CONFIG.ENDPOINTS.LEADS,
      {
        method: 'POST',
        body: JSON.stringify(leadData),
      }
    );

    return response.data;
  }

  async updateLead(leadId: string, updates: Partial<Lead>): Promise<Lead> {
    const response = await this.request<Lead>(
      `${API_CONFIG.ENDPOINTS.LEADS}/${leadId}`,
      {
        method: 'PUT',
        body: JSON.stringify(updates),
      }
    );

    return response.data;
  }

  async getLead(leadId: string): Promise<Lead> {
    const response = await this.request<Lead>(
      `${API_CONFIG.ENDPOINTS.LEADS}/${leadId}`,
      {
        method: 'GET',
      }
    );

    return response.data;
  }

  // Health Check - Railway optimized
  async healthCheck(): Promise<{ status: string; timestamp: number }> {
    const response = await this.request<{ status: string; timestamp: number }>(
      API_CONFIG.ENDPOINTS.HEALTH,
      {
        method: 'GET',
      }
    );

    return response.data;
  }

  // Railway-specific health check
  async railwayHealthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}${API_CONFIG.ENDPOINTS.HEALTH}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch (error) {
      console.error('Railway health check failed:', error);
      return false;
    }
  }

  // Lead Management - Additional Methods
  async getLeads(): Promise<Lead[]> {
    const response = await this.request<Lead[]>(
      API_CONFIG.ENDPOINTS.LEADS,
      {
        method: 'GET',
      }
    );
    return response.data;
  }

  // B2B Export
  async exportLead(leadId: string, platform: string): Promise<{ success: boolean; export_id: string; platform: string; message: string }> {
    const response = await this.request<{ success: boolean; export_id: string; platform: string; message: string }>(
      API_CONFIG.ENDPOINTS.EXPORTS,
      {
        method: 'POST',
        body: JSON.stringify({ lead_id: leadId, platform }),
      }
    );
    return response.data;
  }

  async getExportHistory(): Promise<any[]> {
    const response = await this.request<any[]>(
      API_CONFIG.ENDPOINTS.EXPORT_HISTORY,
      {
        method: 'GET',
      }
    );
    return response.data;
  }

  // Analytics
  async getRevenueAnalytics(): Promise<any> {
    const response = await this.request<any>(
      API_CONFIG.ENDPOINTS.REVENUE_ANALYTICS,
      {
        method: 'GET',
      }
    );
    return response.data;
  }

  async getLeadAnalytics(): Promise<any> {
    const response = await this.request<any>(
      API_CONFIG.ENDPOINTS.LEAD_ANALYTICS,
      {
        method: 'GET',
      }
    );
    return response.data;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Export types for use in components
export type { ApiResponse, ApiError, AuthResponse, LoginRequest, ChatRequest, ChatResponse, SavingsInput, SavingsResult, NYCStatsResponse, LeadData, Lead, SolarData, SolarScoreResponse };
