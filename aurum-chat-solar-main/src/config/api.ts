// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  ENDPOINTS: {
    AUTH: '/api/v1/auth',
    AI: '/api/v1/ai',
    ANALYTICS: '/api/v1/analytics',
    LEADS: '/api/v1/leads',
    CONVERSATION: '/api/v1/conversation',
  },
  TIMEOUT: 10000, // 10 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
};

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface ApiError {
  message: string;
  status: number;
  code?: string;
}

// Request Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

// Chat Types
export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  sessionId?: string;
}

export interface ChatRequest {
  message: string;
  sessionId: string;
  context?: {
    zipCode?: string;
    monthlyBill?: number;
    homeType?: string;
    roofSize?: number;
  };
}

export interface ChatResponse {
  message: string;
  solarScore: number;
  sessionId: string;
  suggestions?: string[];
  nextQuestions?: string[];
}

// Analytics Types
export interface SavingsInput {
  zipCode: string;
  monthlyBill: number;
  homeType: string;
  roofSize?: number;
  roofType?: string;
  shading?: string;
}

export interface SavingsResult {
  systemSize: number;
  systemCost: number;
  federalCredit: number;
  nyCredit: number;
  netCost: number;
  annualSavings: number;
  monthlySavings: number;
  paybackYears: number;
  lifetimeSavings: number;
  incentives: IncentiveData[];
}

export interface IncentiveData {
  name: string;
  amount: number;
  type: 'federal' | 'state' | 'local' | 'utility';
  description: string;
  eligibility: string[];
}

export interface BoroughStats {
  name: string;
  installs: number;
  avgSavings: string;
  incentives: string;
  payback: string;
  avgSystemSize: number;
  avgCost: number;
  growthRate: number;
}

export interface NYCStatsResponse {
  boroughs: Record<string, BoroughStats>;
  totalInstalls: number;
  avgSavings: number;
  marketGrowth: number;
  lastUpdated: string;
}

// Lead Types
export interface LeadData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  zipCode: string;
  monthlyBill: number;
  homeType: string;
  roofSize?: number;
  solarScore: number;
  source: string;
  notes?: string;
}

export interface Lead {
  id: string;
  ...LeadData;
  status: 'new' | 'contacted' | 'qualified' | 'quoted' | 'converted' | 'lost';
  createdAt: string;
  updatedAt: string;
  qualificationScore: number;
  estimatedValue: number;
}

// Solar Score Types
export interface SolarData {
  zipCode: string;
  monthlyBill: number;
  homeType: string;
  roofSize?: number;
  roofType?: string;
  shading?: string;
  orientation?: string;
}

export interface SolarScoreResponse {
  score: number;
  factors: {
    location: number;
    bill: number;
    roof: number;
    incentives: number;
    shading: number;
  };
  recommendations: string[];
  nextSteps: string[];
}
