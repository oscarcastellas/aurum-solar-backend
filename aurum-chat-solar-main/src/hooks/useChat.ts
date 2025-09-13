import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, type ChatRequest, type ChatResponse, type ChatMessage } from '@/services/apiClient';

export const useChat = (sessionId: string) => {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [solarScore, setSolarScore] = useState(0);

  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const request: ChatRequest = {
        message,
        sessionId,
        context: {
          // Extract context from current messages if available
          zipCode: extractZipCodeFromMessages(messages),
          monthlyBill: extractMonthlyBillFromMessages(messages),
          homeType: extractHomeTypeFromMessages(messages),
          roofType: extractRoofTypeFromMessages(messages),
          roofSize: extractRoofSizeFromMessages(messages),
          shading: extractShadingFromMessages(messages),
          orientation: extractOrientationFromMessages(messages),
          roofAge: extractRoofAgeFromMessages(messages),
        },
      };
      
      return apiClient.sendMessage(request);
    },
    onSuccess: (data: ChatResponse) => {
      // Add bot response to messages
      const botMessage: ChatMessage = {
        id: Date.now().toString(),
        content: data.message,
        sender: 'bot',
        timestamp: new Date(),
        sessionId: data.sessionId,
      };
      
      setMessages(prev => [...prev, botMessage]);
      setSolarScore(data.solarScore);
      
      // Update query cache
      queryClient.setQueryData(['messages', sessionId], (old: ChatMessage[]) => 
        [...(old || []), botMessage]
      );
    },
    onError: (error) => {
      console.error('Chat error:', error);
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
        sessionId,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    },
  });

  const addUserMessage = useCallback((content: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
      sessionId,
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // Trigger API call
    sendMessage.mutate(content);
  }, [sendMessage, sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSolarScore(0);
    queryClient.removeQueries({ queryKey: ['messages', sessionId] });
  }, [queryClient, sessionId]);

  return {
    messages,
    solarScore,
    sendMessage: addUserMessage,
    clearMessages,
    isLoading: sendMessage.isPending,
    error: sendMessage.error,
  };
};

// Helper functions to extract context from messages
function extractZipCodeFromMessages(messages: ChatMessage[]): string | undefined {
  const zipCodeMessage = messages.find(msg => 
    msg.sender === 'user' && 
    /^\d{5}(-\d{4})?$/.test(msg.content.trim())
  );
  return zipCodeMessage?.content.trim();
}

function extractMonthlyBillFromMessages(messages: ChatMessage[]): number | undefined {
  const billMessage = messages.find(msg => 
    msg.sender === 'user' && 
    /\$\d+|\d+.*dollar|\d+.*bill/i.test(msg.content)
  );
  
  if (billMessage) {
    const match = billMessage.content.match(/\$?(\d+)/);
    return match ? parseFloat(match[1]) : undefined;
  }
  
  return undefined;
}

function extractHomeTypeFromMessages(messages: ChatMessage[]): string | undefined {
  const homeTypeMessage = messages.find(msg => 
    msg.sender === 'user' && 
    /(own|rent|house|condo|townhouse|co-op|apartment)/i.test(msg.content)
  );
  
  if (homeTypeMessage) {
    const content = homeTypeMessage.content.toLowerCase();
    if (content.includes('own') || content.includes('house')) return 'single-family';
    if (content.includes('condo') || content.includes('co-op')) return 'condo';
    if (content.includes('townhouse')) return 'townhouse';
  }
  
  return undefined;
}
