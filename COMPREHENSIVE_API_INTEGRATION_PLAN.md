# 🚀 Comprehensive API Integration Plan: Vite Frontend ↔ FastAPI Backend

## 📋 **Current Status**
- ✅ **Frontend**: Lovable Vite app running on `http://localhost:3001`
- ✅ **Backend**: FastAPI server with comprehensive API structure
- 🎯 **Goal**: Seamlessly integrate all existing APIs with the Vite frontend

---

## 🏗️ **Phase 1: API Client Setup & Configuration**

### 1.1 **Create API Client Service**
```typescript
// src/services/apiClient.ts
class ApiClient {
  private baseURL: string;
  private token: string | null = null;
  
  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }
  
  // Authentication methods
  async login(credentials: LoginRequest): Promise<AuthResponse>
  async refreshToken(): Promise<AuthResponse>
  async logout(): Promise<void>
  
  // Chat & AI endpoints
  async sendMessage(message: ChatMessage): Promise<ChatResponse>
  async getConversationHistory(sessionId: string): Promise<Conversation[]>
  async getSolarScore(data: SolarData): Promise<SolarScoreResponse>
  
  // Lead management
  async createLead(leadData: LeadData): Promise<Lead>
  async getLeads(filters: LeadFilters): Promise<Lead[]>
  async updateLeadStatus(leadId: string, status: LeadStatus): Promise<Lead>
  
  // Analytics & insights
  async getNYCMarketData(zipCode: string): Promise<NYCMarketData>
  async getAnalytics(timeRange: TimeRange): Promise<AnalyticsData>
  async getRevenueMetrics(): Promise<RevenueMetrics>
  
  // B2B Integration
  async exportLeads(platform: B2BPlatform, leads: string[]): Promise<ExportResult>
  async getB2BStatus(): Promise<B2BStatus>
}
```

### 1.2 **Environment Configuration**
```typescript
// src/config/api.ts
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  ENDPOINTS: {
    AUTH: '/api/v1/auth',
    CHAT: '/api/v1/ai',
    CONVERSATION: '/api/v1/conversation',
    LEADS: '/api/v1/leads',
    ANALYTICS: '/api/v1/analytics',
    EXPORTS: '/api/v1/exports',
    HEALTH: '/health'
  },
  WEBSOCKETS: {
    CHAT: '/ws/chat',
    NYC_INSIGHTS: '/ws/nyc-insights',
    ANALYTICS: '/ws/analytics'
  }
}
```

---

## 🔌 **Phase 2: Real-time WebSocket Integration**

### 2.1 **WebSocket Manager**
```typescript
// src/services/websocketManager.ts
class WebSocketManager {
  private connections: Map<string, WebSocket> = new Map();
  
  // Chat WebSocket
  connectChat(sessionId: string): Promise<WebSocket>
  sendChatMessage(message: ChatMessage): void
  onChatMessage(callback: (message: ChatResponse) => void): void
  
  // NYC Insights WebSocket
  connectNYCInsights(zipCode: string): Promise<WebSocket>
  onNYCDataUpdate(callback: (data: NYCMarketData) => void): void
  
  // Analytics WebSocket
  connectAnalytics(): Promise<WebSocket>
  onAnalyticsUpdate(callback: (data: AnalyticsData) => void): void
  
  // Connection management
  disconnect(sessionId: string): void
  disconnectAll(): void
  isConnected(sessionId: string): boolean
}
```

### 2.2 **React Hooks for WebSocket**
```typescript
// src/hooks/useWebSocket.ts
export const useChatWebSocket = (sessionId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  
  // WebSocket connection logic
  // Message handling
  // Auto-reconnection
}

// src/hooks/useNYCInsights.ts
export const useNYCInsights = (zipCode: string) => {
  const [marketData, setMarketData] = useState<NYCMarketData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Real-time NYC data updates
}
```

---

## 💬 **Phase 3: Chat Interface Integration**

### 3.1 **Enhanced ChatInterface Component**
```typescript
// src/components/ChatInterface.tsx (Enhanced)
export const ChatInterface = ({ isOpen, onClose }: ChatInterfaceProps) => {
  const { messages, sendMessage, isConnected } = useChatWebSocket(sessionId);
  const { solarScore, updateScore } = useSolarScoring();
  const { nycData } = useNYCInsights(zipCode);
  
  // Real-time message handling
  // Solar score calculation
  // NYC market data integration
  // Lead capture functionality
}
```

### 3.2 **AI Service Integration**
```typescript
// src/services/aiService.ts
class AIService {
  async processMessage(message: string, context: ChatContext): Promise<AIResponse> {
    // Send to /api/v1/ai/chat endpoint
    // Handle streaming responses
    // Update solar score
    // Trigger lead qualification
  }
  
  async getSolarRecommendations(data: PropertyData): Promise<SolarRecommendations> {
    // Send to /api/v1/ai/recommendations
  }
  
  async analyzeLead(leadData: LeadData): Promise<LeadAnalysis> {
    // Send to /api/v1/ai/analyze-lead
  }
}
```

---

## 📊 **Phase 4: Analytics & Dashboard Integration**

### 4.1 **Real-time Analytics Dashboard**
```typescript
// src/components/AnalyticsDashboard.tsx
export const AnalyticsDashboard = () => {
  const { metrics, isConnected } = useAnalyticsWebSocket();
  const { revenueData } = useRevenueTracking();
  const { leadMetrics } = useLeadAnalytics();
  
  // Real-time charts and metrics
  // Revenue tracking
  // Lead quality metrics
  // NYC market intelligence
}
```

### 4.2 **Analytics Service**
```typescript
// src/services/analyticsService.ts
class AnalyticsService {
  async getRevenueMetrics(timeRange: TimeRange): Promise<RevenueMetrics>
  async getLeadQualityMetrics(): Promise<LeadQualityMetrics>
  async getNYCMarketIntelligence(zipCode: string): Promise<NYCMarketData>
  async getConversionFunnel(): Promise<ConversionFunnel>
  async getRealTimeMetrics(): Promise<RealTimeMetrics>
}
```

---

## 🏠 **Phase 5: NYC Market Data Integration**

### 5.1 **NYC Stats Panel Enhancement**
```typescript
// src/components/NYCStatsPanel.tsx (Enhanced)
export const NYCStatsPanel = () => {
  const { marketData, isLoading } = useNYCInsights(selectedZipCode);
  const { incentives } = useNYCIncentives(zipCode);
  const { solarPotential } = useSolarPotential(zipCode);
  
  // Real-time NYC data
  // Dynamic borough selection
  // Incentive calculations
  // Solar potential analysis
}
```

### 5.2 **NYC Market Service**
```typescript
// src/services/nycMarketService.ts
class NYCMarketService {
  async getBoroughData(borough: string): Promise<BoroughData>
  async getIncentives(zipCode: string): Promise<IncentiveData[]>
  async getSolarPotential(address: string): Promise<SolarPotentialData>
  async getElectricityRates(zipCode: string): Promise<ElectricityRates>
  async getInstallationData(borough: string): Promise<InstallationData>
}
```

---

## 💰 **Phase 6: Savings Calculator Integration**

### 6.1 **Enhanced SavingsCalculator**
```typescript
// src/components/SavingsCalculator.tsx (Enhanced)
export const SavingsCalculator = () => {
  const { calculateSavings } = useSavingsCalculation();
  const { nycData } = useNYCInsights(zipCode);
  const { incentives } = useNYCIncentives(zipCode);
  
  // Real-time calculations
  // NYC-specific data
  // Incentive integration
  // Lead generation
}
```

### 6.2 **Savings Calculation Service**
```typescript
// src/services/savingsService.ts
class SavingsService {
  async calculateSolarSavings(input: SavingsInput): Promise<SavingsResult> {
    // Send to /api/v1/analytics/savings-calculation
    // Include NYC-specific rates
    // Factor in incentives
    // Generate lead data
  }
  
  async getIncentiveData(zipCode: string): Promise<IncentiveData[]>
  async getElectricityRates(zipCode: string): Promise<ElectricityRates>
  async getSystemRecommendations(propertyData: PropertyData): Promise<SystemRecommendations>
}
```

---

## 🔗 **Phase 7: B2B Integration & Lead Export**

### 7.1 **B2B Export Service**
```typescript
// src/services/b2bService.ts
class B2BService {
  async exportLeads(platform: B2BPlatform, leads: string[]): Promise<ExportResult>
  async getB2BStatus(): Promise<B2BStatus>
  async getExportHistory(): Promise<ExportHistory[]>
  async configurePlatform(platform: B2BPlatform, config: PlatformConfig): Promise<void>
}
```

### 7.2 **Lead Management Integration**
```typescript
// src/services/leadService.ts
class LeadService {
  async createLead(leadData: LeadData): Promise<Lead>
  async updateLead(leadId: string, updates: Partial<Lead>): Promise<Lead>
  async getLeads(filters: LeadFilters): Promise<Lead[]>
  async qualifyLead(leadId: string): Promise<LeadQualification>
  async exportLead(leadId: string, platform: B2BPlatform): Promise<ExportResult>
}
```

---

## 🎯 **Phase 8: Authentication & Security**

### 8.1 **Auth Service**
```typescript
// src/services/authService.ts
class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse>
  async refreshToken(): Promise<AuthResponse>
  async logout(): Promise<void>
  async getCurrentUser(): Promise<User | null>
  async hasPermission(permission: string): Promise<boolean>
}
```

### 8.2 **Protected Routes & Components**
```typescript
// src/components/ProtectedRoute.tsx
export const ProtectedRoute = ({ children, requiredPermission }: ProtectedRouteProps) => {
  const { isAuthenticated, hasPermission } = useAuth();
  
  // Route protection logic
}

// src/hooks/useAuth.ts
export const useAuth = () => {
  // Authentication state management
  // Token handling
  // Permission checking
}
```

---

## 📱 **Phase 9: State Management & Caching**

### 9.1 **Global State Management**
```typescript
// src/store/index.ts
export const store = createStore({
  auth: authSlice,
  chat: chatSlice,
  leads: leadsSlice,
  analytics: analyticsSlice,
  nyc: nycSlice,
  ui: uiSlice
})

// src/store/slices/chatSlice.ts
export const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [],
    isConnected: false,
    solarScore: 0,
    sessionId: null
  },
  reducers: {
    addMessage,
    updateSolarScore,
    setConnectionStatus,
    clearChat
  }
})
```

### 9.2 **Caching Strategy**
```typescript
// src/services/cacheService.ts
class CacheService {
  // Redis-like caching for API responses
  // Local storage for user preferences
  // Session storage for temporary data
  // Cache invalidation strategies
}
```

---

## 🧪 **Phase 10: Testing & Quality Assurance**

### 10.1 **API Integration Tests**
```typescript
// src/tests/api.test.ts
describe('API Integration', () => {
  test('Chat API integration', async () => {
    // Test chat message sending
    // Test response handling
    // Test error scenarios
  })
  
  test('Analytics API integration', async () => {
    // Test metrics retrieval
    // Test real-time updates
  })
})
```

### 10.2 **WebSocket Tests**
```typescript
// src/tests/websocket.test.ts
describe('WebSocket Integration', () => {
  test('Chat WebSocket connection', async () => {
    // Test connection establishment
    // Test message sending/receiving
    // Test reconnection logic
  })
})
```

---

## 🚀 **Implementation Timeline**

### **Week 1: Foundation**
- [ ] Set up API client service
- [ ] Configure environment variables
- [ ] Implement basic authentication
- [ ] Create WebSocket manager

### **Week 2: Core Features**
- [ ] Integrate chat interface with AI API
- [ ] Implement real-time messaging
- [ ] Add solar scoring functionality
- [ ] Connect savings calculator

### **Week 3: Advanced Features**
- [ ] Integrate NYC market data
- [ ] Add analytics dashboard
- [ ] Implement lead management
- [ ] Set up B2B export functionality

### **Week 4: Polish & Testing**
- [ ] Add error handling and loading states
- [ ] Implement caching strategies
- [ ] Add comprehensive testing
- [ ] Performance optimization

---

## 🔧 **Technical Considerations**

### **Performance**
- Implement request batching
- Add response caching
- Use WebSocket connection pooling
- Optimize bundle size

### **Error Handling**
- Global error boundary
- API error interceptors
- WebSocket reconnection logic
- User-friendly error messages

### **Security**
- JWT token management
- API request signing
- CORS configuration
- Input validation

### **Monitoring**
- API response time tracking
- WebSocket connection monitoring
- Error rate monitoring
- User interaction analytics

---

## 📋 **Next Steps**

1. **Start with Phase 1**: Set up the API client and basic configuration
2. **Implement Phase 2**: Add WebSocket support for real-time features
3. **Integrate Phase 3**: Connect the chat interface to the AI API
4. **Build incrementally**: Add features one by one, testing as you go
5. **Monitor and optimize**: Track performance and user experience

This plan provides a comprehensive roadmap for integrating all existing APIs with your Vite frontend efficiently and systematically.
