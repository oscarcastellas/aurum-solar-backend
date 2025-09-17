import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { completeApiClient } from '../services/apiClientComplete';
import { useAppStore } from '../store/useAppStore';
import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * ADVANCED CHAT HOOK - Real-time AI conversation with lead qualification
 * Integrates with Railway backend for complete lead generation workflow
 */
export const useAdvancedChat = (sessionId: string) => {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionRetries, setConnectionRetries] = useState(0);
  const [lastMessageTime, setLastMessageTime] = useState<Date | null>(null);
  
  // Global state
  const {
    conversation,
    addMessage,
    updateConversationContext,
    setChatLoading,
    setChatError,
    addNotification,
    updateLead,
    createLead
  } = useAppStore();

  // ============================================================================
  // WEBSOCKET CONNECTION MANAGEMENT
  // ============================================================================
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      wsRef.current = completeApiClient.createWebSocketConnection(sessionId);
      
      wsRef.current.onopen = () => {
        console.log('Advanced chat WebSocket connected');
        setIsConnected(true);
        setConnectionRetries(0);
        setChatError(null);
        
        // Send welcome message
        addMessage({
          id: `system_${Date.now()}`,
          type: 'system',
          content: 'Connected to Aurum Solar AI. How can I help you with solar energy today?',
          sender: 'bot',
          timestamp: new Date(),
          sessionId
        });
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessageTime(new Date());
          
          // Handle different message types
          switch (data.type) {
            case 'welcome':
              addMessage({
                id: `bot_${Date.now()}`,
                type: 'welcome',
                content: data.message,
                sender: 'bot',
                timestamp: new Date(data.timestamp * 1000),
                sessionId,
                data: data.data
              });
              break;
              
            case 'ai_response':
              addMessage({
                id: `bot_${Date.now()}`,
                type: 'ai_response',
                content: data.message,
                sender: 'bot',
                timestamp: new Date(data.timestamp * 1000),
                sessionId,
                data: data.data
              });
              
              // Update conversation context if provided
              if (data.context) {
                updateConversationContext(data.context);
              }
              
              // Check if lead was created
              if (data.lead_created) {
                addNotification({
                  type: 'success',
                  title: 'Lead Created',
                  message: `New lead created with ID: ${data.lead_created.id}`,
                  read: false
                });
              }
              break;
              
            case 'lead_qualification':
              addMessage({
                id: `bot_${Date.now()}`,
                type: 'lead_qualification',
                content: data.message,
                sender: 'bot',
                timestamp: new Date(),
                sessionId,
                data: {
                  qualification_score: data.qualification_score,
                  estimated_value: data.estimated_value,
                  next_questions: data.next_questions
                }
              });
              
              // Update lead if exists
              if (data.lead_id) {
                updateLead(data.lead_id, {
                  qualification_score: data.qualification_score,
                  estimated_value: data.estimated_value,
                  status: data.qualification_score > 70 ? 'qualified' : 'qualifying'
                });
              }
              break;
              
            case 'solar_calculation':
              addMessage({
                id: `bot_${Date.now()}`,
                type: 'solar_calculation',
                content: data.message,
                sender: 'bot',
                timestamp: new Date(),
                sessionId,
                data: {
                  solar_score: data.solar_score,
                  system_size: data.system_size,
                  estimated_savings: data.estimated_savings,
                  payback_period: data.payback_period,
                  recommendations: data.recommendations
                }
              });
              
              // Update conversation context with solar data
              updateConversationContext({
                solarScore: data.solar_score,
                systemSize: data.system_size,
                estimatedSavings: data.estimated_savings
              });
              break;
              
            case 'nyc_market_data':
              addMessage({
                id: `bot_${Date.now()}`,
                type: 'nyc_market_data',
                content: data.message,
                sender: 'bot',
                timestamp: new Date(),
                sessionId,
                data: {
                  borough: data.borough,
                  market_data: data.market_data,
                  incentives: data.incentives,
                  competition: data.competition
                }
              });
              break;
              
            case 'error':
              addMessage({
                id: `bot_${Date.now()}`,
                type: 'error',
                content: data.message,
                sender: 'bot',
                timestamp: new Date(),
                sessionId
              });
              setChatError(data.message);
              break;
              
            default:
              addMessage({
                id: `bot_${Date.now()}`,
                type: 'message',
                content: data.message || data.content,
                sender: 'bot',
                timestamp: new Date(data.timestamp * 1000),
                sessionId,
                data: data.data
              });
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
          addMessage({
            id: `error_${Date.now()}`,
            type: 'error',
            content: 'Failed to process message from server',
            sender: 'bot',
            timestamp: new Date(),
            sessionId
          });
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('Advanced chat WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        
        // Auto-reconnect logic
        if (event.code !== 1000 && connectionRetries < 5) {
          setConnectionRetries(prev => prev + 1);
          setTimeout(() => {
            console.log(`Attempting to reconnect advanced chat (${connectionRetries + 1}/5)`);
            connectWebSocket();
          }, 5000 * (connectionRetries + 1));
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Advanced chat WebSocket error:', error);
        setIsConnected(false);
        setChatError('WebSocket connection error');
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setChatError('Failed to connect to chat server');
    }
  }, [sessionId, connectionRetries, addMessage, updateConversationContext, setChatError, updateLead]);

  // ============================================================================
  // CHAT MESSAGE HANDLING
  // ============================================================================
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      setChatLoading(true);
      setChatError(null);
      
      // Add user message to local state
      const userMessage = {
        id: `user_${Date.now()}`,
        type: 'user_message',
        content: message,
        sender: 'user',
        timestamp: new Date(),
        sessionId
      };
      addMessage(userMessage);
      
      // Send via WebSocket if connected, otherwise fallback to HTTP
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'user_message',
          message,
          session_id: sessionId,
          context: conversation.context,
          timestamp: new Date().toISOString()
        }));
        return { success: true };
      } else {
        // Fallback to HTTP API
        const response = await completeApiClient.sendChatMessage(message, sessionId, conversation.context);
        return response;
      }
    },
    onSuccess: (data) => {
      setChatLoading(false);
      if (data.success) {
        setLastMessageTime(new Date());
      }
    },
    onError: (error) => {
      setChatLoading(false);
      setChatError(error.message || 'Failed to send message');
      addNotification({
        type: 'error',
        title: 'Chat Error',
        message: 'Failed to send message. Please try again.',
        read: false
      });
    }
  });

  // ============================================================================
  // AI FEATURES
  // ============================================================================
  const calculateSolarScoreMutation = useMutation({
    mutationFn: async (input: any) => {
      return completeApiClient.calculateSolarScore(input);
    },
    onSuccess: (data) => {
      addMessage({
        id: `solar_score_${Date.now()}`,
        type: 'solar_calculation',
        content: `Solar Score: ${data.data.solar_score}/100. ${data.data.recommendations.join(' ')}`,
        sender: 'bot',
        timestamp: new Date(),
        sessionId,
        data: data.data
      });
      
      updateConversationContext({
        solarScore: data.data.solar_score,
        systemSize: data.data.system_size_recommendation,
        estimatedSavings: data.data.estimated_savings
      });
    },
    onError: (error) => {
      setChatError('Failed to calculate solar score');
    }
  });

  const getNYCMarketDataMutation = useMutation({
    mutationFn: async (zipCode: string) => {
      return completeApiClient.getNYCMarketData(zipCode);
    },
    onSuccess: (data) => {
      addMessage({
        id: `nyc_data_${Date.now()}`,
        type: 'nyc_market_data',
        content: `NYC Market Data for ${zipCode}: ${data.data.market_data?.summary || 'Data retrieved'}`,
        sender: 'bot',
        timestamp: new Date(),
        sessionId,
        data: data.data
      });
    },
    onError: (error) => {
      setChatError('Failed to get NYC market data');
    }
  });

  // ============================================================================
  // LEAD MANAGEMENT
  // ============================================================================
  const createLeadMutation = useMutation({
    mutationFn: async (leadData: any) => {
      return completeApiClient.createLead(leadData);
    },
    onSuccess: (data) => {
      addNotification({
        type: 'success',
        title: 'Lead Created',
        message: `New lead created: ${data.data.name}`,
        read: false
      });
      
      // Update conversation with lead ID
      updateConversationContext({ leadId: data.data.id });
    },
    onError: (error) => {
      setChatError('Failed to create lead');
    }
  });

  const qualifyLeadMutation = useMutation({
    mutationFn: async (leadId: string) => {
      return completeApiClient.qualifyLead(leadId);
    },
    onSuccess: (data) => {
      addMessage({
        id: `qualification_${Date.now()}`,
        type: 'lead_qualification',
        content: `Lead qualification complete. Score: ${data.data.qualification_score}/100`,
        sender: 'bot',
        timestamp: new Date(),
        sessionId,
        data: data.data
      });
    },
    onError: (error) => {
      setChatError('Failed to qualify lead');
    }
  });

  // ============================================================================
  // CONNECTION MANAGEMENT
  // ============================================================================
  useEffect(() => {
    if (sessionId) {
      connectWebSocket();
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [sessionId, connectWebSocket]);

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (isConnected && wsRef.current) {
      const heartbeat = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'heartbeat',
            session_id: sessionId,
            timestamp: new Date().toISOString()
          }));
        }
      }, 30000); // 30 seconds
      
      return () => clearInterval(heartbeat);
    }
  }, [isConnected, sessionId]);

  // ============================================================================
  // RETURN HOOK INTERFACE
  // ============================================================================
  return {
    // Connection status
    isConnected,
    connectionRetries,
    lastMessageTime,
    
    // Chat functionality
    sendMessage: sendMessageMutation.mutate,
    isSending: sendMessageMutation.isPending,
    sendError: sendMessageMutation.error,
    
    // AI features
    calculateSolarScore: calculateSolarScoreMutation.mutate,
    isCalculatingSolarScore: calculateSolarScoreMutation.isPending,
    getNYCMarketData: getNYCMarketDataMutation.mutate,
    isGettingNYCData: getNYCMarketDataMutation.isPending,
    
    // Lead management
    createLead: createLeadMutation.mutate,
    isCreatingLead: createLeadMutation.isPending,
    qualifyLead: qualifyLeadMutation.mutate,
    isQualifyingLead: qualifyLeadMutation.isPending,
    
    // Conversation state
    messages: conversation.messages,
    context: conversation.context,
    qualificationStage: conversation.qualificationStage,
    
    // Connection management
    reconnect: connectWebSocket,
    disconnect: () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setIsConnected(false);
    },
    
    // Utilities
    clearError: () => {
      sendMessageMutation.reset();
      setChatError(null);
    }
  };
};

/**
 * Hook for monitoring chat performance and analytics
 */
export const useChatAnalytics = () => {
  const { conversation, analytics } = useAppStore();
  
  const getConversationMetrics = () => {
    const messages = conversation.messages;
    const userMessages = messages.filter(m => m.sender === 'user');
    const botMessages = messages.filter(m => m.sender === 'bot');
    
    return {
      totalMessages: messages.length,
      userMessages: userMessages.length,
      botMessages: botMessages.length,
      averageResponseTime: 0, // Would calculate from timestamps
      qualificationProgress: conversation.qualificationStage,
      contextCompleteness: Object.keys(conversation.context).length / 6 * 100 // 6 key context fields
    };
  };
  
  return {
    conversationMetrics: getConversationMetrics(),
    analytics: analytics?.conversations,
    isQualified: conversation.qualificationStage === 'qualified',
    hasLead: !!conversation.leadId
  };
};
