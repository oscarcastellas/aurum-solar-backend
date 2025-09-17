import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { railwayApiClient } from '../services/railwayApiClient';
import { useState, useEffect } from 'react';

/**
 * Railway-optimized chat hooks
 * Enhanced for Railway backend with connection monitoring and retry logic
 */
export const useRailwayChat = (sessionId: string) => {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  
  // Health check query with Railway optimization
  const healthQuery = useQuery({
    queryKey: ['railway-health'],
    queryFn: () => railwayApiClient.healthCheck(),
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
    retryDelay: 1000,
    staleTime: 10000, // 10 seconds
    onSuccess: (isHealthy) => {
      setIsConnected(isHealthy);
    },
    onError: () => {
      setIsConnected(false);
    }
  });
  
  // Connection test query
  const connectionTestQuery = useQuery({
    queryKey: ['railway-connection-test'],
    queryFn: () => railwayApiClient.testConnection(),
    enabled: false, // Manual trigger
    retry: 1,
    retryDelay: 2000
  });
  
  // Send message mutation with Railway retry logic
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) => railwayApiClient.sendChatMessage(message, sessionId),
    onSuccess: (data) => {
      // Update chat history in cache
      queryClient.setQueryData(['chat', sessionId], (old: any) => [
        ...(old || []),
        {
          id: `bot_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          content: data.response,
          sender: 'bot',
          timestamp: new Date(data.timestamp * 1000),
          sessionId: sessionId
        }
      ]);
    },
    onError: (error) => {
      console.error('Failed to send message to Railway backend:', error);
    },
    retry: 2,
    retryDelay: 1000
  });
  
  // Get chat history query
  const chatHistoryQuery = useQuery({
    queryKey: ['chat', sessionId],
    queryFn: () => [], // Placeholder - would fetch from backend
    enabled: false, // Disabled for now
    staleTime: 30000
  });
  
  // Monitor connection status
  useEffect(() => {
    const interval = setInterval(() => {
      const status = railwayApiClient.getConnectionStatus();
      setIsConnected(status.isConnected);
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  return {
    // Connection status
    isHealthy: healthQuery.data,
    isHealthLoading: healthQuery.isLoading,
    isConnected,
    connectionError: healthQuery.error,
    
    // Chat functionality
    sendMessage: sendMessageMutation.mutate,
    isSending: sendMessageMutation.isPending,
    sendError: sendMessageMutation.error,
    latestBotMessage: sendMessageMutation.data?.response || null,
    
    // Chat history
    messages: chatHistoryQuery.data || [],
    isHistoryLoading: chatHistoryQuery.isLoading,
    
    // Connection testing
    testConnection: connectionTestQuery.refetch,
    connectionTestData: connectionTestQuery.data,
    isTestingConnection: connectionTestQuery.isLoading,
    
    // Utilities
    refetchHealth: healthQuery.refetch,
    clearError: () => {
      sendMessageMutation.reset();
      healthQuery.refetch();
    }
  };
};

/**
 * Hook for Railway backend monitoring
 */
export const useRailwayMonitoring = () => {
  const [metrics, setMetrics] = useState({
    connectionAttempts: 0,
    lastConnectionTime: null as Date | null,
    averageLatency: 0,
    errorCount: 0
  });
  
  // Monitor performance
  useEffect(() => {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.name.includes('backend-production-3f24.up.railway.app')) {
          setMetrics(prev => ({
            ...prev,
            averageLatency: (prev.averageLatency + entry.duration) / 2,
            lastConnectionTime: new Date()
          }));
        }
      });
    });
    
    observer.observe({ entryTypes: ['resource', 'navigation'] });
    
    return () => observer.disconnect();
  }, []);
  
  return {
    metrics,
    updateMetrics: setMetrics
  };
};

/**
 * Hook for Railway WebSocket connection
 */
export const useRailwayWebSocket = (sessionId: string) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  
  useEffect(() => {
    if (sessionId) {
      const websocket = railwayApiClient.createWebSocketConnection(sessionId);
      
      websocket.onopen = () => {
        setIsConnected(true);
        console.log('Railway WebSocket connected');
      };
      
      websocket.onclose = () => {
        setIsConnected(false);
        console.log('Railway WebSocket disconnected');
      };
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setMessages(prev => [...prev, data]);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      websocket.onerror = (error) => {
        console.error('Railway WebSocket error:', error);
        setIsConnected(false);
      };
      
      setWs(websocket);
      
      return () => {
        websocket.close();
        setWs(null);
      };
    }
  }, [sessionId]);
  
  const sendMessage = (message: any) => {
    if (ws && isConnected) {
      ws.send(JSON.stringify(message));
    }
  };
  
  return {
    ws,
    isConnected,
    messages,
    sendMessage
  };
};
