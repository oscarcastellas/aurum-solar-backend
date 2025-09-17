import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  Wifi, 
  MessageCircle, 
  Server,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { completeApiClient } from '@/services/apiClient';

interface TestResult {
  name: string;
  status: 'pending' | 'running' | 'success' | 'error';
  latency?: number;
  error?: string;
  details?: any;
}

export const RailwayTestSuite: React.FC = () => {
  const [tests, setTests] = useState<TestResult[]>([
    { name: 'Connection Test', status: 'pending' },
    { name: 'Chat Functionality', status: 'pending' },
    { name: 'Health Check', status: 'pending' }
  ]);
  
  const [isRunning, setIsRunning] = useState(false);
  const [overallStatus, setOverallStatus] = useState<'pending' | 'success' | 'error'>('pending');
  const [lastRun, setLastRun] = useState<Date | null>(null);

  const runTests = async () => {
    setIsRunning(true);
    setOverallStatus('pending');
    
    // Reset test states
    setTests(prev => prev.map(test => ({ ...test, status: 'pending' })));
    
    try {
      // Test 1: Connection Test
      setTests(prev => prev.map(test => 
        test.name === 'Connection Test' ? { ...test, status: 'running' } : test
      ));
      
      const startTime1 = Date.now();
      try {
        const connectionResult = await completeApiClient.healthCheck();
        const latency1 = Date.now() - startTime1;
        setTests(prev => prev.map(test => 
          test.name === 'Connection Test' 
            ? { 
                ...test, 
                status: connectionResult.success ? 'success' : 'error',
                latency: latency1,
                error: connectionResult.success ? undefined : 'Health check failed',
                details: connectionResult.data
              } 
            : test
        ));
      } catch (error) {
        const latency1 = Date.now() - startTime1;
        setTests(prev => prev.map(test => 
          test.name === 'Connection Test' 
            ? { 
                ...test, 
                status: 'error',
                latency: latency1,
                error: error instanceof Error ? error.message : 'Unknown error'
              } 
            : test
        ));
      }
      
      // Test 2: Chat Functionality
      setTests(prev => prev.map(test => 
        test.name === 'Chat Functionality' ? { ...test, status: 'running' } : test
      ));
      
      const startTime2 = Date.now();
      try {
        const sessionId = `test_${Date.now()}`;
        const chatResult = await completeApiClient.sendChatMessage('Test message', sessionId);
        const latency2 = Date.now() - startTime2;
        setTests(prev => prev.map(test => 
          test.name === 'Chat Functionality' 
            ? { 
                ...test, 
                status: chatResult.success ? 'success' : 'error',
                latency: latency2,
                error: chatResult.success ? undefined : 'Chat test failed'
              } 
            : test
        ));
      } catch (error) {
        const latency2 = Date.now() - startTime2;
        setTests(prev => prev.map(test => 
          test.name === 'Chat Functionality' 
            ? { 
                ...test, 
                status: 'error',
                latency: latency2,
                error: error instanceof Error ? error.message : 'Unknown error'
              } 
            : test
        ));
      }
      
      // Test 3: System Info
      setTests(prev => prev.map(test => 
        test.name === 'Health Check' ? { ...test, status: 'running' } : test
      ));
      
      const startTime3 = Date.now();
      try {
        const systemResult = await completeApiClient.getSystemInfo();
        const latency3 = Date.now() - startTime3;
        setTests(prev => prev.map(test => 
          test.name === 'Health Check' 
            ? { 
                ...test, 
                status: systemResult.success ? 'success' : 'error',
                latency: latency3,
                error: systemResult.success ? undefined : 'System info failed',
                details: systemResult.data
              } 
            : test
        ));
      } catch (error) {
        const latency3 = Date.now() - startTime3;
        setTests(prev => prev.map(test => 
          test.name === 'Health Check' 
            ? { 
                ...test, 
                status: 'error',
                latency: latency3,
                error: error instanceof Error ? error.message : 'Unknown error'
              } 
            : test
        ));
      }
      
      // Determine overall status
      const allPassed = tests.every(test => test.status === 'success');
      setOverallStatus(allPassed ? 'success' : 'error');
      setLastRun(new Date());
      
    } catch (error) {
      console.error('Test suite failed:', error);
      setOverallStatus('error');
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'running':
        return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: TestResult['status']) => {
    switch (status) {
      case 'success':
        return <Badge variant="default" className="bg-green-100 text-green-800">Passed</Badge>;
      case 'error':
        return <Badge variant="destructive">Failed</Badge>;
      case 'running':
        return <Badge variant="secondary">Running</Badge>;
      default:
        return <Badge variant="outline">Pending</Badge>;
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Railway Backend Test Suite
          </CardTitle>
          <div className="flex items-center gap-2">
            {overallStatus === 'success' && (
              <Badge variant="default" className="bg-green-100 text-green-800">
                All Tests Passed
              </Badge>
            )}
            {overallStatus === 'error' && (
              <Badge variant="destructive">
                Some Tests Failed
              </Badge>
            )}
            <Button 
              onClick={runTests} 
              disabled={isRunning}
              size="sm"
            >
              {isRunning ? (
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              {isRunning ? 'Running Tests...' : 'Run Tests'}
            </Button>
          </div>
        </div>
        
        {lastRun && (
          <p className="text-sm text-gray-500">
            Last run: {lastRun.toLocaleString()}
          </p>
        )}
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {tests.map((test, index) => (
            <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3">
                {getStatusIcon(test.status)}
                <div>
                  <h3 className="font-medium">{test.name}</h3>
                  {test.latency && (
                    <p className="text-sm text-gray-500">
                      Latency: {test.latency}ms
                    </p>
                  )}
                  {test.error && (
                    <p className="text-sm text-red-600">
                      Error: {test.error}
                    </p>
                  )}
                  {test.details && (
                    <div className="text-xs text-gray-500 mt-1">
                      <p>Status: {test.details.status}</p>
                      <p>Version: {test.details.version}</p>
                      <p>Environment: {test.details.environment}</p>
                    </div>
                  )}
                </div>
              </div>
              {getStatusBadge(test.status)}
            </div>
          ))}
          
          {/* Summary */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium mb-2">Test Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {tests.filter(t => t.status === 'success').length}
                </div>
                <div className="text-gray-500">Passed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {tests.filter(t => t.status === 'error').length}
                </div>
                <div className="text-gray-500">Failed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {tests.filter(t => t.status === 'running').length}
                </div>
                <div className="text-gray-500">Running</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">
                  {tests.length}
                </div>
                <div className="text-gray-500">Total</div>
              </div>
            </div>
          </div>
          
          {/* Backend URL */}
          <div className="text-center text-sm text-gray-500">
            <p>Testing against: aurum-solarv3-production.up.railway.app</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
