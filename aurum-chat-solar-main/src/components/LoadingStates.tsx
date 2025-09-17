import React from 'react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Wifi, WifiOff, Server } from 'lucide-react';

/**
 * Backend Connection Loader
 * Shows when connecting to Railway backend
 */
export const BackendConnectionLoader: React.FC = () => (
  <div className="flex items-center justify-center h-64">
    <div className="text-center">
      <div className="flex justify-center mb-4">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
          <Server className="h-8 w-8 text-green-600" />
        </div>
      </div>
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
      <p className="text-gray-600 font-medium">Connecting to Railway backend...</p>
      <p className="text-sm text-gray-500 mt-2">This may take a few seconds</p>
    </div>
  </div>
);

/**
 * Chat Loading State
 * Shows when AI is processing a message
 */
export const ChatLoadingState: React.FC = () => (
  <div className="flex items-center space-x-2 p-4">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-green-600 rounded-full animate-bounce"></div>
      <div className="w-2 h-2 bg-green-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
      <div className="w-2 h-2 bg-green-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
    </div>
    <span className="text-gray-600">AI is thinking...</span>
  </div>
);

/**
 * Connection Status Indicator
 * Shows real-time connection status
 */
interface ConnectionStatusProps {
  isConnected: boolean;
  isConnecting: boolean;
  latency?: number;
  error?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ 
  isConnected, 
  isConnecting, 
  latency, 
  error 
}) => {
  if (isConnecting) {
    return (
      <div className="flex items-center space-x-2 text-blue-600">
        <LoadingSpinner size="sm" />
        <span className="text-sm">Connecting...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center space-x-2 text-red-600">
        <WifiOff className="h-4 w-4" />
        <span className="text-sm">Connection Error</span>
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="flex items-center space-x-2 text-green-600">
        <Wifi className="h-4 w-4" />
        <span className="text-sm">
          Connected{latency && ` (${latency}ms)`}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-gray-500">
      <WifiOff className="h-4 w-4" />
      <span className="text-sm">Disconnected</span>
    </div>
  );
};

/**
 * Railway Backend Status
 * Shows detailed Railway backend status
 */
interface RailwayStatusProps {
  isHealthy: boolean;
  isChecking: boolean;
  latency?: number;
  lastChecked?: Date;
  onRetry?: () => void;
}

export const RailwayStatus: React.FC<RailwayStatusProps> = ({
  isHealthy,
  isChecking,
  latency,
  lastChecked,
  onRetry
}) => {
  return (
    <div className="bg-white rounded-lg border p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">Railway Backend Status</h3>
        {onRetry && (
          <button
            onClick={onRetry}
            disabled={isChecking}
            className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
          >
            {isChecking ? 'Checking...' : 'Retry'}
          </button>
        )}
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Status:</span>
          <ConnectionStatus 
            isConnected={isHealthy}
            isConnecting={isChecking}
            latency={latency}
          />
        </div>
        
        {latency && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Latency:</span>
            <span className="text-sm font-mono">{latency}ms</span>
          </div>
        )}
        
        {lastChecked && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Last Checked:</span>
            <span className="text-sm text-gray-500">
              {lastChecked.toLocaleTimeString()}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Skeleton Loader for Chat Messages
 */
export const ChatMessageSkeleton: React.FC = () => (
  <div className="flex justify-start">
    <div className="flex items-start gap-2 max-w-[80%]">
      <div className="w-8 h-8 rounded-full bg-gray-200 animate-pulse"></div>
      <div className="p-3 rounded-lg bg-gray-100 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-24"></div>
      </div>
    </div>
  </div>
);

/**
 * Full Page Loading State
 */
export const FullPageLoader: React.FC<{ message?: string }> = ({ 
  message = "Loading..." 
}) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
      <p className="text-gray-600 font-medium">{message}</p>
    </div>
  </div>
);
