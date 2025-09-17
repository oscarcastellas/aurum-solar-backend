import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Frontend Error:', error, errorInfo);
    this.setState({ error, errorInfo });
    
    // Log to external service in production
    if (process.env.NODE_ENV === 'production') {
      // Here you would log to Sentry, LogRocket, etc.
      console.error('Production Error:', {
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      });
    }
  }
  
  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };
  
  handleReload = () => {
    window.location.reload();
  };
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-red-50 p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="h-8 w-8 text-red-600" />
              </div>
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Something went wrong
            </h2>
            
            <p className="text-gray-600 mb-6">
              We're having trouble connecting to our servers. This might be a temporary issue.
            </p>
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-4 bg-gray-100 rounded-lg text-left">
                <h3 className="font-semibold text-sm text-gray-700 mb-2">Error Details:</h3>
                <pre className="text-xs text-gray-600 overflow-auto">
                  {this.state.error.message}
                </pre>
              </div>
            )}
            
            <div className="space-y-3">
              <Button 
                onClick={this.handleRetry}
                className="w-full"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Try Again
              </Button>
              
              <Button 
                variant="outline"
                onClick={this.handleReload}
                className="w-full"
              >
                Reload Page
              </Button>
            </div>
            
            <div className="mt-6 text-xs text-gray-500">
              <p>If this problem persists, please contact support.</p>
              <p className="mt-1">Error ID: {Date.now().toString(36)}</p>
            </div>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}
