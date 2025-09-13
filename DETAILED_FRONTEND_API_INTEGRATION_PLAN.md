# 🎯 Detailed Frontend API Integration Plan: Vite React App

## 📋 **Frontend Analysis Summary**

### **Current Frontend Architecture**
- **Framework**: Vite + React 18 + TypeScript
- **UI Library**: Shadcn/ui + Radix UI + Tailwind CSS
- **State Management**: React Query (TanStack Query) + React Hooks
- **Routing**: React Router DOM
- **Styling**: Tailwind CSS with custom design system
- **Icons**: Lucide React

### **Key Components Identified**
1. **HeroSection** - Landing page with CTA buttons
2. **ChatInterface** - AI-powered solar assistant chat
3. **SavingsCalculator** - Solar savings calculation tool
4. **NYCStatsPanel** - Borough-specific solar statistics
5. **TrustSection** - Customer testimonials and trust badges

---

## 🔌 **API Integration Requirements**

### **1. Chat Interface Integration**
**Current State**: Mock responses with hardcoded bot responses
**Integration Needed**: Real AI conversation with backend

**API Endpoints Required**:
- `POST /api/v1/ai/chat` - Send user message, get AI response
- `POST /api/v1/ai/analyze-lead` - Analyze lead quality and solar potential
- `GET /api/v1/ai/solar-score` - Get real-time solar score calculation

**Data Flow**:
```typescript
// Current mock implementation
const generateBotResponse = (userInput: string, messageCount: number) => {
  // Replace with real API call
}

// New implementation
const sendMessageToAI = async (message: string) => {
  const response = await apiClient.post('/ai/chat', {
    message,
    sessionId,
    context: { zipCode, monthlyBill, homeType }
  });
  return response.data;
}
```

### **2. Savings Calculator Integration**
**Current State**: Client-side mock calculations
**Integration Needed**: Real-time calculations with NYC-specific data

**API Endpoints Required**:
- `POST /api/v1/analytics/savings-calculation` - Calculate solar savings
- `GET /api/v1/analytics/nyc-incentives` - Get NYC-specific incentives
- `GET /api/v1/analytics/electricity-rates` - Get current electricity rates by ZIP

**Data Flow**:
```typescript
// Current mock implementation
const calculateSavings = () => {
  // Client-side calculations
}

// New implementation
const calculateSavings = async () => {
  const response = await apiClient.post('/analytics/savings-calculation', {
    zipCode,
    monthlyBill,
    homeType,
    roofSize: estimatedRoofSize
  });
  setResults(response.data);
}
```

### **3. NYC Stats Panel Integration**
**Current State**: Hardcoded borough data
**Integration Needed**: Real-time NYC market data

**API Endpoints Required**:
- `GET /api/v1/analytics/nyc-borough-stats` - Get borough-specific statistics
- `GET /api/v1/analytics/nyc-market-trends` - Get market trends and insights
- `GET /api/v1/analytics/installation-data` - Get installation counts by borough

**Data Flow**:
```typescript
// Current hardcoded data
const boroughData = {
  manhattan: { installs: 420, avgSavings: '$2,800' }
}

// New implementation
const [boroughData, setBoroughData] = useState({});
useEffect(() => {
  const fetchBoroughData = async () => {
    const response = await apiClient.get('/analytics/nyc-borough-stats');
    setBoroughData(response.data);
  };
  fetchBoroughData();
}, []);
```

### **4. Lead Generation Integration**
**Current State**: No lead capture
**Integration Needed**: Lead capture and qualification

**API Endpoints Required**:
- `POST /api/v1/leads` - Create new lead
- `PUT /api/v1/leads/{id}` - Update lead information
- `GET /api/v1/leads/{id}/qualification` - Get lead qualification status

---

## 🛠️ **Implementation Plan**

### **Phase 1: API Client Setup**
```typescript
// src/services/apiClient.ts
class ApiClient {
  private baseURL: string;
  private token: string | null = null;
  
  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }
  
  // Authentication
  async login(credentials: LoginRequest): Promise<AuthResponse>
  async refreshToken(): Promise<AuthResponse>
  
  // AI Chat
  async sendMessage(message: ChatMessage): Promise<ChatResponse>
  async getSolarScore(data: SolarData): Promise<SolarScoreResponse>
  
  // Analytics
  async calculateSavings(input: SavingsInput): Promise<SavingsResult>
  async getNYCBoroughStats(): Promise<BoroughStats[]>
  async getNYCIncentives(zipCode: string): Promise<IncentiveData[]>
  
  // Leads
  async createLead(leadData: LeadData): Promise<Lead>
  async updateLead(leadId: string, updates: Partial<Lead>): Promise<Lead>
}
```

### **Phase 2: React Query Integration**
```typescript
// src/hooks/useChat.ts
export const useChat = (sessionId: string) => {
  const queryClient = useQueryClient();
  
  const sendMessage = useMutation({
    mutationFn: (message: string) => apiClient.sendMessage({ message, sessionId }),
    onSuccess: (data) => {
      queryClient.setQueryData(['messages', sessionId], (old: Message[]) => 
        [...(old || []), data.message]
      );
    }
  });
  
  return { sendMessage, isLoading: sendMessage.isPending };
};

// src/hooks/useSavingsCalculator.ts
export const useSavingsCalculator = () => {
  const calculateSavings = useMutation({
    mutationFn: (input: SavingsInput) => apiClient.calculateSavings(input),
    onSuccess: (data) => {
      // Update UI with results
    }
  });
  
  return { calculateSavings, isLoading: calculateSavings.isPending };
};
```

### **Phase 3: Component Updates**

#### **ChatInterface.tsx Updates**
```typescript
// Replace mock responses with real API calls
const sendMessage = async () => {
  if (!inputValue.trim()) return;
  
  const userMessage: Message = {
    id: Date.now().toString(),
    content: inputValue,
    sender: 'user',
    timestamp: new Date()
  };
  
  setMessages(prev => [...prev, userMessage]);
  setInputValue('');
  
  try {
    const response = await apiClient.sendMessage({
      message: inputValue,
      sessionId: sessionId,
      context: { zipCode, monthlyBill, homeType }
    });
    
    const botMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: response.message,
      sender: 'bot',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, botMessage]);
    setSolarScore(response.solarScore);
  } catch (error) {
    // Handle error
  }
};
```

#### **SavingsCalculator.tsx Updates**
```typescript
// Replace mock calculations with real API calls
const calculateSavings = async () => {
  const bill = parseFloat(monthlyBill);
  if (!bill || !zipCode || !homeType) return;
  
  try {
    const results = await apiClient.calculateSavings({
      zipCode,
      monthlyBill: bill,
      homeType,
      roofSize: estimatedRoofSize
    });
    
    setResults(results);
  } catch (error) {
    // Handle error
  }
};
```

#### **NYCStatsPanel.tsx Updates**
```typescript
// Replace hardcoded data with real API calls
export const NYCStatsPanel = () => {
  const [selectedBorough, setSelectedBorough] = useState('brooklyn');
  
  const { data: boroughStats, isLoading } = useQuery({
    queryKey: ['nyc-borough-stats'],
    queryFn: () => apiClient.getNYCBoroughStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  const currentData = boroughStats?.[selectedBorough];
  
  if (isLoading) return <div>Loading...</div>;
  
  // Rest of component...
};
```

### **Phase 4: Environment Configuration**
```typescript
// src/config/api.ts
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  ENDPOINTS: {
    AUTH: '/api/v1/auth',
    AI: '/api/v1/ai',
    ANALYTICS: '/api/v1/analytics',
    LEADS: '/api/v1/leads',
  }
};
```

### **Phase 5: Error Handling & Loading States**
```typescript
// src/components/ErrorBoundary.tsx
export const ErrorBoundary = ({ children }: { children: React.ReactNode }) => {
  // Error boundary implementation
};

// src/components/LoadingSpinner.tsx
export const LoadingSpinner = () => {
  // Loading spinner component
};

// Update components with loading states
const { data, isLoading, error } = useQuery({
  queryKey: ['savings-calculation'],
  queryFn: () => apiClient.calculateSavings(input)
});

if (isLoading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
```

---

## 🚀 **Implementation Timeline**

### **Week 1: Foundation**
- [ ] Set up API client service
- [ ] Configure environment variables
- [ ] Set up React Query
- [ ] Create error handling components

### **Week 2: Core Features**
- [ ] Integrate ChatInterface with AI API
- [ ] Connect SavingsCalculator to analytics API
- [ ] Update NYCStatsPanel with real data
- [ ] Add loading states and error handling

### **Week 3: Advanced Features**
- [ ] Add lead capture functionality
- [ ] Implement real-time solar scoring
- [ ] Add WebSocket support for live updates
- [ ] Optimize performance and caching

### **Week 4: Polish & Testing**
- [ ] Add comprehensive error handling
- [ ] Implement retry logic
- [ ] Add offline support
- [ ] Performance optimization

---

## 📊 **Data Flow Architecture**

```
Frontend (Vite + React)          Backend (FastAPI)
┌─────────────────────┐          ┌─────────────────────┐
│ 1. User Input      │          │ 1. API Endpoints    │
│ 2. React Query     │ ────────►│ 2. AI Services      │
│ 3. State Management│          │ 3. Analytics Engine │
│ 4. UI Updates      │◄─────────│ 4. Database         │
└─────────────────────┘          └─────────────────────┘
```

## 🔧 **Technical Considerations**

### **Performance**
- Use React Query for caching and background updates
- Implement optimistic updates for better UX
- Add request debouncing for search inputs

### **Error Handling**
- Global error boundary for unhandled errors
- Per-component error states
- Retry logic for failed requests
- Offline support with cached data

### **Security**
- JWT token management
- Request/response validation with Zod
- CORS configuration
- Input sanitization

### **Monitoring**
- API response time tracking
- Error rate monitoring
- User interaction analytics
- Performance metrics

---

## ✅ **Success Metrics**

1. **Functionality**: All components connected to real APIs
2. **Performance**: < 200ms API response times
3. **Reliability**: 99.9% uptime for API calls
4. **User Experience**: Smooth loading states and error handling
5. **Lead Generation**: Seamless lead capture and qualification

This plan provides a comprehensive roadmap for integrating the Vite frontend with the FastAPI backend, ensuring a seamless user experience while maintaining code quality and performance.
