import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { devtools } from 'zustand/middleware';

// ============================================================================
// GLOBAL STATE MANAGEMENT FOR AURUM SOLAR PLATFORM
// ============================================================================

interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer';
  isAuthenticated: boolean;
}

interface ConversationState {
  sessionId: string;
  leadId?: string;
  messages: any[];
  isActive: boolean;
  qualificationStage: 'initial' | 'qualifying' | 'qualified' | 'converting';
  context: {
    zipCode?: string;
    monthlyBill?: number;
    homeType?: string;
    roofSize?: number;
    solarScore?: number;
  };
}

interface Lead {
  id: string;
  name: string;
  email: string;
  phone: string;
  zip_code: string;
  monthly_bill: number;
  qualification_score: number;
  estimated_value: number;
  status: 'new' | 'qualifying' | 'qualified' | 'converting' | 'converted' | 'exported';
  created_at: string;
  updated_at: string;
  source: string;
  notes?: string;
}

interface RevenueMetrics {
  total_revenue: number;
  monthly_revenue: number;
  revenue_growth: number;
  average_deal_size: number;
  conversion_rate: number;
  period: string;
}

interface Analytics {
  leads: {
    total: number;
    new: number;
    qualified: number;
    conversion_rate: number;
    quality_score: number;
  };
  revenue: RevenueMetrics;
  conversations: {
    total: number;
    average_duration: number;
    qualification_rate: number;
    performance_score: number;
  };
  nyc_market: {
    boroughs: any[];
    total_installs: number;
    avg_savings: number;
    market_growth: number;
  };
}

interface B2BPlatform {
  code: string;
  name: string;
  status: 'active' | 'inactive' | 'maintenance';
  base_price: number;
  commission_rate: number;
  leads_exported: number;
  revenue_generated: number;
}

interface ExportHistory {
  export_id: string;
  lead_id: string;
  platform: string;
  status: 'pending' | 'processing' | 'exported' | 'failed';
  exported_at: string;
  revenue: number;
}

interface AppState {
  // ============================================================================
  // AUTHENTICATION & USER STATE
  // ============================================================================
  user: User | null;
  isAuthenticated: boolean;
  authLoading: boolean;
  authError: string | null;

  // ============================================================================
  // CONVERSATION STATE
  // ============================================================================
  conversation: ConversationState;
  isChatOpen: boolean;
  chatLoading: boolean;
  chatError: string | null;

  // ============================================================================
  // LEADS MANAGEMENT
  // ============================================================================
  leads: Lead[];
  selectedLead: Lead | null;
  leadsLoading: boolean;
  leadsError: string | null;
  leadFilters: {
    status?: string;
    quality?: string;
    date_from?: string;
    date_to?: string;
    zip_code?: string;
    min_score?: number;
    max_score?: number;
  };

  // ============================================================================
  // ANALYTICS & REVENUE
  // ============================================================================
  analytics: Analytics | null;
  analyticsLoading: boolean;
  analyticsError: string | null;
  lastAnalyticsUpdate: Date | null;

  // ============================================================================
  // B2B EXPORT SYSTEM
  // ============================================================================
  b2bPlatforms: B2BPlatform[];
  exportHistory: ExportHistory[];
  selectedPlatform: string | null;
  exportLoading: boolean;
  exportError: string | null;

  // ============================================================================
  // NYC MARKET DATA
  // ============================================================================
  nycData: {
    boroughs: any[];
    marketData: any;
    selectedBorough: string | null;
  };
  nycDataLoading: boolean;
  nycDataError: string | null;

  // ============================================================================
  // SYSTEM STATE
  // ============================================================================
  isOnline: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting';
  lastSync: Date | null;
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message: string;
    timestamp: Date;
    read: boolean;
  }>;

  // ============================================================================
  // UI STATE
  // ============================================================================
  sidebarOpen: boolean;
  currentPage: string;
  theme: 'light' | 'dark';
  mobileMenuOpen: boolean;
}

interface AppActions {
  // ============================================================================
  // AUTHENTICATION ACTIONS
  // ============================================================================
  setUser: (user: User | null) => void;
  setAuthenticated: (isAuthenticated: boolean) => void;
  setAuthLoading: (loading: boolean) => void;
  setAuthError: (error: string | null) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;

  // ============================================================================
  // CONVERSATION ACTIONS
  // ============================================================================
  setConversation: (conversation: Partial<ConversationState>) => void;
  addMessage: (message: any) => void;
  updateConversationContext: (context: Partial<ConversationState['context']>) => void;
  setChatOpen: (isOpen: boolean) => void;
  setChatLoading: (loading: boolean) => void;
  setChatError: (error: string | null) => void;
  startNewConversation: () => void;
  endConversation: () => void;

  // ============================================================================
  // LEADS ACTIONS
  // ============================================================================
  setLeads: (leads: Lead[]) => void;
  addLead: (lead: Lead) => void;
  updateLead: (leadId: string, updates: Partial<Lead>) => void;
  deleteLead: (leadId: string) => void;
  setSelectedLead: (lead: Lead | null) => void;
  setLeadsLoading: (loading: boolean) => void;
  setLeadsError: (error: string | null) => void;
  setLeadFilters: (filters: Partial<AppState['leadFilters']>) => void;
  createLead: (leadData: Partial<Lead>) => Promise<void>;
  qualifyLead: (leadId: string) => Promise<void>;
  exportLead: (leadId: string, platform: string) => Promise<void>;

  // ============================================================================
  // ANALYTICS ACTIONS
  // ============================================================================
  setAnalytics: (analytics: Analytics) => void;
  setAnalyticsLoading: (loading: boolean) => void;
  setAnalyticsError: (error: string | null) => void;
  refreshAnalytics: () => Promise<void>;

  // ============================================================================
  // B2B EXPORT ACTIONS
  // ============================================================================
  setB2BPlatforms: (platforms: B2BPlatform[]) => void;
  setExportHistory: (history: ExportHistory[]) => void;
  addExportRecord: (record: ExportHistory) => void;
  setSelectedPlatform: (platform: string | null) => void;
  setExportLoading: (loading: boolean) => void;
  setExportError: (error: string | null) => void;
  exportToB2B: (leadIds: string[], platform: string) => Promise<void>;

  // ============================================================================
  // NYC MARKET ACTIONS
  // ============================================================================
  setNYCData: (data: Partial<AppState['nycData']>) => void;
  setSelectedBorough: (borough: string | null) => void;
  setNYCDataLoading: (loading: boolean) => void;
  setNYCDataError: (error: string | null) => void;
  refreshNYCData: () => Promise<void>;

  // ============================================================================
  // SYSTEM ACTIONS
  // ============================================================================
  setOnline: (isOnline: boolean) => void;
  setConnectionStatus: (status: AppState['connectionStatus']) => void;
  setLastSync: (date: Date) => void;
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;

  // ============================================================================
  // UI ACTIONS
  // ============================================================================
  setSidebarOpen: (open: boolean) => void;
  setCurrentPage: (page: string) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setMobileMenuOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  toggleMobileMenu: () => void;

  // ============================================================================
  // UTILITY ACTIONS
  // ============================================================================
  reset: () => void;
  syncWithBackend: () => Promise<void>;
}

const initialState: AppState = {
  // Authentication
  user: null,
  isAuthenticated: false,
  authLoading: false,
  authError: null,

  // Conversation
  conversation: {
    sessionId: '',
    leadId: undefined,
    messages: [],
    isActive: false,
    qualificationStage: 'initial',
    context: {}
  },
  isChatOpen: false,
  chatLoading: false,
  chatError: null,

  // Leads
  leads: [],
  selectedLead: null,
  leadsLoading: false,
  leadsError: null,
  leadFilters: {},

  // Analytics
  analytics: null,
  analyticsLoading: false,
  analyticsError: null,
  lastAnalyticsUpdate: null,

  // B2B Export
  b2bPlatforms: [],
  exportHistory: [],
  selectedPlatform: null,
  exportLoading: false,
  exportError: null,

  // NYC Market
  nycData: {
    boroughs: [],
    marketData: null,
    selectedBorough: null
  },
  nycDataLoading: false,
  nycDataError: null,

  // System
  isOnline: true,
  connectionStatus: 'connected',
  lastSync: null,
  notifications: [],

  // UI
  sidebarOpen: false,
  currentPage: 'dashboard',
  theme: 'light',
  mobileMenuOpen: false
};

export const useAppStore = create<AppState & AppActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // ============================================================================
        // AUTHENTICATION ACTIONS
        // ============================================================================
        setUser: (user) => set({ user, isAuthenticated: !!user }),
        setAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
        setAuthLoading: (authLoading) => set({ authLoading }),
        setAuthError: (authError) => set({ authError }),
        
        login: async (email, password) => {
          set({ authLoading: true, authError: null });
          try {
            // This would call the actual API
            // const response = await completeApiClient.login(email, password);
            // set({ user: response.data.user, isAuthenticated: true });
            console.log('Login attempt:', { email, password });
          } catch (error) {
            set({ authError: 'Login failed' });
          } finally {
            set({ authLoading: false });
          }
        },

        logout: () => {
          set({
            user: null,
            isAuthenticated: false,
            conversation: initialState.conversation,
            leads: [],
            selectedLead: null
          });
        },

        // ============================================================================
        // CONVERSATION ACTIONS
        // ============================================================================
        setConversation: (conversation) => set((state) => ({
          conversation: { ...state.conversation, ...conversation }
        })),

        addMessage: (message) => set((state) => ({
          conversation: {
            ...state.conversation,
            messages: [...state.conversation.messages, message]
          }
        })),

        updateConversationContext: (context) => set((state) => ({
          conversation: {
            ...state.conversation,
            context: { ...state.conversation.context, ...context }
          }
        })),

        setChatOpen: (isChatOpen) => set({ isChatOpen }),
        setChatLoading: (chatLoading) => set({ chatLoading }),
        setChatError: (chatError) => set({ chatError }),

        startNewConversation: () => {
          const sessionId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          set({
            conversation: {
              ...initialState.conversation,
              sessionId,
              isActive: true
            },
            isChatOpen: true
          });
        },

        endConversation: () => set({
          conversation: initialState.conversation,
          isChatOpen: false
        }),

        // ============================================================================
        // LEADS ACTIONS
        // ============================================================================
        setLeads: (leads) => set({ leads }),
        addLead: (lead) => set((state) => ({ leads: [...state.leads, lead] })),
        updateLead: (leadId, updates) => set((state) => ({
          leads: state.leads.map(lead => 
            lead.id === leadId ? { ...lead, ...updates } : lead
          ),
          selectedLead: state.selectedLead?.id === leadId 
            ? { ...state.selectedLead, ...updates }
            : state.selectedLead
        })),
        deleteLead: (leadId) => set((state) => ({
          leads: state.leads.filter(lead => lead.id !== leadId),
          selectedLead: state.selectedLead?.id === leadId ? null : state.selectedLead
        })),
        setSelectedLead: (selectedLead) => set({ selectedLead }),
        setLeadsLoading: (leadsLoading) => set({ leadsLoading }),
        setLeadsError: (leadsError) => set({ leadsError }),
        setLeadFilters: (leadFilters) => set((state) => ({
          leadFilters: { ...state.leadFilters, ...leadFilters }
        })),

        createLead: async (leadData) => {
          set({ leadsLoading: true, leadsError: null });
          try {
            // This would call the actual API
            // const response = await completeApiClient.createLead(leadData);
            // set((state) => ({ leads: [...state.leads, response.data] }));
            console.log('Create lead:', leadData);
          } catch (error) {
            set({ leadsError: 'Failed to create lead' });
          } finally {
            set({ leadsLoading: false });
          }
        },

        qualifyLead: async (leadId) => {
          try {
            // This would call the actual API
            // const response = await completeApiClient.qualifyLead(leadId);
            // updateLead(leadId, response.data);
            console.log('Qualify lead:', leadId);
          } catch (error) {
            console.error('Failed to qualify lead:', error);
          }
        },

        exportLead: async (leadId, platform) => {
          set({ exportLoading: true, exportError: null });
          try {
            // This would call the actual API
            // const response = await completeApiClient.exportLead(leadId, platform);
            // addExportRecord(response.data);
            console.log('Export lead:', { leadId, platform });
          } catch (error) {
            set({ exportError: 'Failed to export lead' });
          } finally {
            set({ exportLoading: false });
          }
        },

        // ============================================================================
        // ANALYTICS ACTIONS
        // ============================================================================
        setAnalytics: (analytics) => set({ analytics, lastAnalyticsUpdate: new Date() }),
        setAnalyticsLoading: (analyticsLoading) => set({ analyticsLoading }),
        setAnalyticsError: (analyticsError) => set({ analyticsError }),

        refreshAnalytics: async () => {
          set({ analyticsLoading: true, analyticsError: null });
          try {
            // This would call the actual API
            // const [revenue, leads, conversations, nyc] = await Promise.all([
            //   completeApiClient.getRevenueAnalytics(),
            //   completeApiClient.getLeadAnalytics(),
            //   completeApiClient.getConversationPerformance(),
            //   completeApiClient.getNYCBoroughStats()
            // ]);
            // setAnalytics({ revenue: revenue.data, leads: leads.data, conversations: conversations.data, nyc_market: nyc.data });
            console.log('Refresh analytics');
          } catch (error) {
            set({ analyticsError: 'Failed to refresh analytics' });
          } finally {
            set({ analyticsLoading: false });
          }
        },

        // ============================================================================
        // B2B EXPORT ACTIONS
        // ============================================================================
        setB2BPlatforms: (b2bPlatforms) => set({ b2bPlatforms }),
        setExportHistory: (exportHistory) => set({ exportHistory }),
        addExportRecord: (record) => set((state) => ({
          exportHistory: [record, ...state.exportHistory]
        })),
        setSelectedPlatform: (selectedPlatform) => set({ selectedPlatform }),
        setExportLoading: (exportLoading) => set({ exportLoading }),
        setExportError: (exportError) => set({ exportError }),

        exportToB2B: async (leadIds, platform) => {
          set({ exportLoading: true, exportError: null });
          try {
            // This would call the actual API
            // const response = await completeApiClient.bulkExport(leadIds, platform);
            // addExportRecord(response.data);
            console.log('Export to B2B:', { leadIds, platform });
          } catch (error) {
            set({ exportError: 'Failed to export to B2B' });
          } finally {
            set({ exportLoading: false });
          }
        },

        // ============================================================================
        // NYC MARKET ACTIONS
        // ============================================================================
        setNYCData: (nycData) => set((state) => ({
          nycData: { ...state.nycData, ...nycData }
        })),
        setSelectedBorough: (selectedBorough) => set((state) => ({
          nycData: { ...state.nycData, selectedBorough }
        })),
        setNYCDataLoading: (nycDataLoading) => set({ nycDataLoading }),
        setNYCDataError: (nycDataError) => set({ nycDataError }),

        refreshNYCData: async () => {
          set({ nycDataLoading: true, nycDataError: null });
          try {
            // This would call the actual API
            // const response = await completeApiClient.getNYCBoroughStats();
            // setNYCData({ boroughs: response.data.boroughs });
            console.log('Refresh NYC data');
          } catch (error) {
            set({ nycDataError: 'Failed to refresh NYC data' });
          } finally {
            set({ nycDataLoading: false });
          }
        },

        // ============================================================================
        // SYSTEM ACTIONS
        // ============================================================================
        setOnline: (isOnline) => set({ isOnline }),
        setConnectionStatus: (connectionStatus) => set({ connectionStatus }),
        setLastSync: (lastSync) => set({ lastSync }),

        addNotification: (notification) => {
          const id = `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          const newNotification = {
            ...notification,
            id,
            timestamp: new Date()
          };
          set((state) => ({
            notifications: [newNotification, ...state.notifications]
          }));
        },

        removeNotification: (id) => set((state) => ({
          notifications: state.notifications.filter(n => n.id !== id)
        })),

        markNotificationRead: (id) => set((state) => ({
          notifications: state.notifications.map(n => 
            n.id === id ? { ...n, read: true } : n
          )
        })),

        clearNotifications: () => set({ notifications: [] }),

        // ============================================================================
        // UI ACTIONS
        // ============================================================================
        setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
        setCurrentPage: (currentPage) => set({ currentPage }),
        setTheme: (theme) => set({ theme }),
        setMobileMenuOpen: (mobileMenuOpen) => set({ mobileMenuOpen }),
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        toggleMobileMenu: () => set((state) => ({ mobileMenuOpen: !state.mobileMenuOpen })),

        // ============================================================================
        // UTILITY ACTIONS
        // ============================================================================
        reset: () => set(initialState),

        syncWithBackend: async () => {
          set({ connectionStatus: 'reconnecting' });
          try {
            // This would sync all data with the backend
            // await Promise.all([
            //   get().refreshAnalytics(),
            //   get().refreshNYCData(),
            //   // ... other sync operations
            // ]);
            set({ connectionStatus: 'connected', lastSync: new Date() });
          } catch (error) {
            set({ connectionStatus: 'disconnected' });
          }
        }
      }),
      {
        name: 'aurum-solar-store',
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
          conversation: state.conversation,
          theme: state.theme,
          sidebarOpen: state.sidebarOpen
        })
      }
    ),
    {
      name: 'aurum-solar-store'
    }
  )
);