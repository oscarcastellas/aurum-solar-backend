import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  X, 
  Send, 
  User, 
  Bot, 
  Zap, 
  Wifi, 
  WifiOff, 
  Calculator,
  MapPin,
  DollarSign,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { useAdvancedChat, useChatAnalytics } from '@/hooks/useAdvancedChat';
import { useAppStore } from '@/store/useAppStore';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

interface AdvancedChatInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AdvancedChatInterface = ({ isOpen, onClose }: AdvancedChatInterfaceProps) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Global state
  const { conversation, startNewConversation, endConversation } = useAppStore();
  
  // Chat hook
  const {
    isConnected,
    connectionRetries,
    sendMessage,
    isSending,
    sendError,
    calculateSolarScore,
    getNYCMarketData,
    createLead,
    qualifyLead,
    messages,
    context,
    qualificationStage,
    clearError
  } = useAdvancedChat(conversation.sessionId);
  
  // Analytics
  const { conversationMetrics, isQualified, hasLead } = useChatAnalytics();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Start new conversation when chat opens
  useEffect(() => {
    if (isOpen && !conversation.isActive) {
      startNewConversation();
    }
  }, [isOpen, conversation.isActive, startNewConversation]);

  const handleSendMessage = () => {
    if (!inputValue.trim() || isSending || !isConnected) return;
    
    sendMessage(inputValue);
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getQualificationStageColor = (stage: string) => {
    switch (stage) {
      case 'initial': return 'bg-gray-500';
      case 'qualifying': return 'bg-yellow-500';
      case 'qualified': return 'bg-green-500';
      case 'converting': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getQualificationStageText = (stage: string) => {
    switch (stage) {
      case 'initial': return 'Getting Started';
      case 'qualifying': return 'Qualifying Lead';
      case 'qualified': return 'Lead Qualified';
      case 'converting': return 'Converting';
      default: return 'Unknown';
    }
  };

  const renderMessage = (message: any) => {
    const isUser = message.sender === 'user';
    const isBot = message.sender === 'bot';
    
    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div
          className={`max-w-[80%] rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground'
          }`}
        >
          <div className="flex items-start gap-2">
            {isBot && <Bot className="h-4 w-4 mt-1 flex-shrink-0" />}
            {isUser && <User className="h-4 w-4 mt-1 flex-shrink-0" />}
            
            <div className="flex-1">
              <div className="text-sm font-medium mb-1">
                {isUser ? 'You' : 'Aurum Solar AI'}
              </div>
              
              <div className="text-sm whitespace-pre-wrap">
                {message.content}
              </div>
              
              {/* Message data for special types */}
              {message.data && (
                <div className="mt-2 space-y-2">
                  {message.type === 'solar_calculation' && (
                    <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="h-4 w-4 text-green-600" />
                        <span className="font-medium text-green-800 dark:text-green-200">
                          Solar Score: {message.data.solar_score}/100
                        </span>
                      </div>
                      <div className="text-sm text-green-700 dark:text-green-300">
                        <div>System Size: {message.data.system_size}kW</div>
                        <div>Estimated Savings: ${message.data.estimated_savings?.toLocaleString()}/year</div>
                        <div>Payback Period: {message.data.payback_period} years</div>
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'lead_qualification' && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="h-4 w-4 text-blue-600" />
                        <span className="font-medium text-blue-800 dark:text-blue-200">
                          Qualification Score: {message.data.qualification_score}/100
                        </span>
                      </div>
                      <div className="text-sm text-blue-700 dark:text-blue-300">
                        <div>Estimated Value: ${message.data.estimated_value?.toLocaleString()}</div>
                        {message.data.next_questions && (
                          <div className="mt-2">
                            <div className="font-medium">Next Questions:</div>
                            <ul className="list-disc list-inside space-y-1">
                              {message.data.next_questions.map((q: string, i: number) => (
                                <li key={i}>{q}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'nyc_market_data' && (
                    <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <MapPin className="h-4 w-4 text-purple-600" />
                        <span className="font-medium text-purple-800 dark:text-purple-200">
                          NYC Market Data
                        </span>
                      </div>
                      <div className="text-sm text-purple-700 dark:text-purple-300">
                        {message.data.borough && <div>Borough: {message.data.borough}</div>}
                        {message.data.market_data && (
                          <div>Market Summary: {message.data.market_data.summary}</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              <div className="text-xs opacity-70 mt-1">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl h-[80vh] flex flex-col">
        <CardHeader className="flex-shrink-0 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Bot className="h-6 w-6 text-primary" />
                  {isConnected ? (
                    <Wifi className="h-3 w-3 text-green-500 absolute -top-1 -right-1" />
                  ) : (
                    <WifiOff className="h-3 w-3 text-red-500 absolute -top-1 -right-1" />
                  )}
                </div>
                <div>
                  <CardTitle className="text-lg">Aurum Solar AI</CardTitle>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Badge 
                      variant="outline" 
                      className={`${getQualificationStageColor(qualificationStage)} text-white`}
                    >
                      {getQualificationStageText(qualificationStage)}
                    </Badge>
                    {isQualified && <CheckCircle className="h-4 w-4 text-green-500" />}
                    {hasLead && <DollarSign className="h-4 w-4 text-green-500" />}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {connectionRetries > 0 && (
                <Badge variant="destructive">
                  Reconnecting... ({connectionRetries}/5)
                </Badge>
              )}
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Progress indicators */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Conversation Progress</span>
              <span>{conversationMetrics.contextCompleteness.toFixed(0)}%</span>
            </div>
            <Progress value={conversationMetrics.contextCompleteness} className="h-2" />
            
            <div className="flex justify-between text-sm">
              <span>Messages: {conversationMetrics.totalMessages}</span>
              <span>Qualification: {qualificationStage}</span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col p-0">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">Welcome to Aurum Solar AI</h3>
                <p className="text-muted-foreground mb-4">
                  I'm here to help you explore solar energy options for your NYC property.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendMessage("What's my monthly electricity bill?")}
                  >
                    <DollarSign className="h-4 w-4 mr-2" />
                    Check My Bill
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendMessage("Calculate my solar savings")}
                  >
                    <Calculator className="h-4 w-4 mr-2" />
                    Calculate Savings
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sendMessage("Show me NYC incentives")}
                  >
                    <MapPin className="h-4 w-4 mr-2" />
                    NYC Incentives
                  </Button>
                </div>
              </div>
            ) : (
              messages.map(renderMessage)
            )}
            
            {isSending && (
              <div className="flex justify-start">
                <div className="bg-muted text-muted-foreground rounded-lg px-4 py-2 flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">AI is thinking...</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Error display */}
          {sendError && (
            <div className="px-4 py-2 border-t">
              <ErrorMessage
                error={sendError}
                onRetry={() => clearError()}
                onDismiss={() => clearError()}
                title="Chat Error"
                showDetails={false}
              />
            </div>
          )}

          {/* Input area */}
          <div className="flex-shrink-0 p-4 border-t">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  isConnected 
                    ? "Ask about solar energy, calculate savings, or get NYC market data..."
                    : "Connecting to AI..."
                }
                disabled={isSending || !isConnected}
                className="flex-1"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isSending || !isConnected}
                size="sm"
              >
                {isSending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            
            {/* Quick actions */}
            <div className="flex flex-wrap gap-2 mt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => sendMessage("What's my solar potential?")}
                disabled={isSending || !isConnected}
              >
                <Zap className="h-3 w-3 mr-1" />
                Solar Potential
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => sendMessage("Show me financing options")}
                disabled={isSending || !isConnected}
              >
                <DollarSign className="h-3 w-3 mr-1" />
                Financing
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => sendMessage("What are the next steps?")}
                disabled={isSending || !isConnected}
              >
                <CheckCircle className="h-3 w-3 mr-1" />
                Next Steps
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
