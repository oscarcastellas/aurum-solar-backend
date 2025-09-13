import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'

// Layout Components
import DashboardLayout from './components/layout/DashboardLayout'
import LoginPage from './pages/LoginPage'

// Dashboard Pages
import DashboardHome from './pages/DashboardHome'
import RevenueAnalytics from './pages/RevenueAnalytics'
import ConversationAnalytics from './pages/ConversationAnalytics'
import MarketPerformance from './pages/MarketPerformance'
import OptimizationInsights from './pages/OptimizationInsights'
import LeadManagement from './pages/LeadManagement'
import B2BExports from './pages/B2BExports'
import Settings from './pages/Settings'

// Context
import { AuthProvider, useAuth } from './contexts/AuthContext'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<LoginPage />} />
              
              {/* Protected Routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }>
                <Route index element={<DashboardHome />} />
                <Route path="revenue" element={<RevenueAnalytics />} />
                <Route path="conversations" element={<ConversationAnalytics />} />
                <Route path="market" element={<MarketPerformance />} />
                <Route path="optimization" element={<OptimizationInsights />} />
                <Route path="leads" element={<LeadManagement />} />
                <Route path="exports" element={<B2BExports />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
            
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10B981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#EF4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
