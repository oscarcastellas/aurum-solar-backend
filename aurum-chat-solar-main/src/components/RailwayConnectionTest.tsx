import React, { useState, useEffect } from 'react';
import { completeApiClient } from '../services/apiClient';

/**
 * Railway Connection Test Component
 * Tests the connection to Railway backend and displays status
 */
export const RailwayConnectionTest: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState<{
    isConnected: boolean;
    latency: number;
    error?: string;
    lastChecked: Date | null;
  }>({
    isConnected: false,
    latency: 0,
    lastChecked: null
  });
  
  const [isTesting, setIsTesting] = useState(false);

  const testConnection = async () => {
    setIsTesting(true);
    const startTime = Date.now();
    try {
      const result = await completeApiClient.healthCheck();
      const latency = Date.now() - startTime;
      setConnectionStatus({
        isConnected: result.success,
        latency: latency,
        error: undefined,
        lastChecked: new Date()
      });
    } catch (error) {
      const latency = Date.now() - startTime;
      setConnectionStatus({
        isConnected: false,
        latency: latency,
        error: error instanceof Error ? error.message : 'Unknown error',
        lastChecked: new Date()
      });
    } finally {
      setIsTesting(false);
    }
  };

  // Test connection on mount
  useEffect(() => {
    testConnection();
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 max-w-md mx-auto">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Railway Backend Connection Test
      </h3>
      
      <div className="space-y-3">
        {/* Connection Status */}
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus.isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span className="text-sm font-medium">
            {connectionStatus.isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        
        {/* Latency */}
        {connectionStatus.latency > 0 && (
          <div className="text-sm text-gray-600">
            Latency: {connectionStatus.latency}ms
          </div>
        )}
        
        {/* Error Message */}
        {connectionStatus.error && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
            Error: {connectionStatus.error}
          </div>
        )}
        
        {/* Last Checked */}
        {connectionStatus.lastChecked && (
          <div className="text-xs text-gray-500">
            Last checked: {connectionStatus.lastChecked.toLocaleTimeString()}
          </div>
        )}
        
        {/* Test Button */}
        <button
          onClick={testConnection}
          disabled={isTesting}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isTesting ? 'Testing...' : 'Test Connection'}
        </button>
        
        {/* Backend URL */}
        <div className="text-xs text-gray-500 text-center">
          Backend: aurum-solarv3-production.up.railway.app
        </div>
      </div>
    </div>
  );
};
