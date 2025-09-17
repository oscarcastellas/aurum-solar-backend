import { railwayApiClient } from '@/services/railwayApiClient';

/**
 * Test Railway Backend Connection
 * Comprehensive connection testing for Railway backend
 */
export const testRailwayConnection = async (): Promise<{
  success: boolean;
  latency: number;
  error?: string;
  details?: {
    status: string;
    version: string;
    environment: string;
    responseTime: number;
  };
}> => {
  const startTime = Date.now();
  
  try {
    const result = await railwayApiClient.testConnection();
    const latency = Date.now() - startTime;
    
    if (result.success) {
      return {
        success: true,
        latency: result.latency,
        details: {
          status: 'healthy',
          version: '1.0.0',
          environment: 'production',
          responseTime: result.latency
        }
      };
    } else {
      return {
        success: false,
        latency: result.latency,
        error: result.error
      };
    }
  } catch (error) {
    return {
      success: false,
      latency: Date.now() - startTime,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};

/**
 * Test Chat Functionality
 * Tests sending a message to Railway backend
 */
export const testChatFunctionality = async (): Promise<{
  messageSent: boolean;
  responseReceived: boolean;
  latency: number;
  error?: string;
}> => {
  const testMessage = "Test message for Railway backend";
  const sessionId = crypto.randomUUID();
  const startTime = Date.now();
  
  try {
    const response = await railwayApiClient.sendChatMessage(testMessage, sessionId);
    const latency = Date.now() - startTime;
    
    return {
      messageSent: true,
      responseReceived: !!response,
      latency
    };
  } catch (error) {
    return {
      messageSent: false,
      responseReceived: false,
      latency: Date.now() - startTime,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};

/**
 * Comprehensive Railway Backend Test Suite
 */
export const runRailwayTestSuite = async () => {
  console.log('🧪 Starting Railway Backend Test Suite...');
  
  const results = {
    connection: await testRailwayConnection(),
    chat: await testChatFunctionality(),
    timestamp: new Date().toISOString()
  };
  
  console.log('📊 Test Results:', results);
  
  // Overall health check
  const isHealthy = results.connection.success && results.chat.messageSent;
  
  console.log(`✅ Railway Backend Status: ${isHealthy ? 'HEALTHY' : 'UNHEALTHY'}`);
  
  return {
    ...results,
    isHealthy,
    summary: {
      connectionWorking: results.connection.success,
      chatWorking: results.chat.messageSent,
      averageLatency: (results.connection.latency + results.chat.latency) / 2,
      overallHealth: isHealthy
    }
  };
};

/**
 * Performance Monitoring
 * Monitors API response times and performance
 */
export const monitorPerformance = () => {
  const observer = new PerformanceObserver((list) => {
    list.getEntries().forEach((entry) => {
        if (entry.name.includes('aurum-solarv3-production.up.railway.app')) {
        console.log(`🚀 API Call: ${entry.name} - ${entry.duration.toFixed(2)}ms`);
        
        // Log slow requests
        if (entry.duration > 2000) {
          console.warn(`⚠️ Slow API call detected: ${entry.name} - ${entry.duration.toFixed(2)}ms`);
        }
      }
    });
  });
  
  observer.observe({ entryTypes: ['resource', 'navigation'] });
  
  return () => observer.disconnect();
};

/**
 * Connection Health Check
 * Quick health check for Railway backend
 */
export const quickHealthCheck = async (): Promise<boolean> => {
  try {
    const response = await fetch('https://aurum-solarv3-production.up.railway.app/health', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(5000)
    });
    
    return response.ok;
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};
