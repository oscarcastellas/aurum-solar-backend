import { API_CONFIG } from '@/config/api';

/**
 * Ultra Simple API Client - Just for chat functionality
 */
class SimpleAPIClient {
  private baseURL: string;

  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
  }

  // Simple health check
  async healthCheck(): Promise<{ success: boolean; data?: any }> {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000)
      });
      
      if (response.ok) {
        const data = await response.json();
        return { success: true, data };
      }
      return { success: false };
    } catch (error) {
      console.error('Health check failed:', error);
      return { success: false };
    }
  }

  // Simple chat message
  async sendChatMessage(message: string, sessionId: string): Promise<{ data: any }> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/chat/message`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          timestamp: new Date().toISOString()
        }),
        signal: AbortSignal.timeout(10000)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error('Chat message failed:', error);
      // Return a fallback response
      return {
        data: {
          response: "I'm having trouble connecting right now. Please try again in a moment, or feel free to ask me about solar energy for your NYC home!",
          session_id: sessionId,
          timestamp: Math.floor(Date.now() / 1000)
        }
      };
    }
  }
}

export const simpleApiClient = new SimpleAPIClient();
