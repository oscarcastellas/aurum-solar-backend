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

  // Authentication Methods
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>(
      `${API_CONFIG.ENDPOINTS.AUTH}/login`,
      {
        method: 'POST',
        body: JSON.stringify(credentials),
      }
    );

    this.token = response.data.access_token;
    this.refreshToken = response.data.refresh_token;
    this.saveTokensToStorage(response.data.access_token, response.data.refresh_token);

    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.request(`${API_CONFIG.ENDPOINTS.AUTH}/logout`, {
        method: 'POST',
      });
    } finally {
      this.clearTokens();
    }
  }

  async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) return false;

    try {
      const response = await this.request<AuthResponse>(
        `${API_CONFIG.ENDPOINTS.AUTH}/refresh`,
        {
          method: 'POST',
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        }
      );

      this.token = response.data.access_token;
      this.refreshToken = response.data.refresh_token;
      this.saveTokensToStorage(response.data.access_token, response.data.refresh_token);

      return true;
    } catch (error) {
      this.clearTokens();
      return false;
    }
  }

  // AI Chat Methods
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.request<ChatResponse>(
      `${API_CONFIG.ENDPOINTS.AI}/chat`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    return response.data;
  }

  async getSolarScore(data: SolarData): Promise<SolarScoreResponse> {
    const response = await this.request<SolarScoreResponse>(
      `${API_CONFIG.ENDPOINTS.AI}/solar-score`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );

    return response.data;
  }

  // Analytics Methods
  async calculateSavings(input: SavingsInput): Promise<SavingsResult> {
    const response = await this.request<SavingsResult>(
      `${API_CONFIG.ENDPOINTS.ANALYTICS}/savings-calculation`,
      {
        method: 'POST',
        body: JSON.stringify(input),
      }
    );

    return response.data;
  }

  async getNYCBoroughStats(): Promise<NYCStatsResponse> {
    const response = await this.request<NYCStatsResponse>(
      `${API_CONFIG.ENDPOINTS.ANALYTICS}/nyc-borough-stats`,
      {
        method: 'GET',
      }
    );

    return response.data;
  }

  async getNYCIncentives(zipCode: string): Promise<IncentiveData[]> {
    const response = await this.request<IncentiveData[]>(
      `${API_CONFIG.ENDPOINTS.ANALYTICS}/nyc-incentives?zipCode=${zipCode}`,
      {
        method: 'GET',
      }
    );

    return response.data;
  }

  async getElectricityRates(zipCode: string): Promise<{ rate: number; utility: string }> {
    const response = await this.request<{ rate: number; utility: string }>(
      `${API_CONFIG.ENDPOINTS.ANALYTICS}/electricity-rates?zipCode=${zipCode}`,
      {
        method: 'GET',
      }
    );

    return response.data;
  }

  // Lead Methods
  async createLead(leadData: LeadData): Promise<Lead> {
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

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.request<{ status: string; timestamp: string }>(
      '/api/v1/health',
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
