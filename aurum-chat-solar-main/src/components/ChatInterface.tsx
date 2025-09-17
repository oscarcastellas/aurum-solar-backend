import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { X, MessageCircle, Send, User, Bot, Zap, Wifi, WifiOff } from 'lucide-react';
import { useRailwayChat } from '@/hooks/useRailwayChat';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface ChatInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChatInterface = ({ isOpen, onClose }: ChatInterfaceProps) => {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Generate a unique session ID for this chat session
  const sessionId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  const {
    isHealthy,
    isHealthLoading,
    isConnected,
    sendMessage,
    isSending,
    sendError,
    latestBotMessage,
    testConnection,
    connectionTestData
  } = useRailwayChat(sessionId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle bot responses
  useEffect(() => {
    if (latestBotMessage) {
      const botMessage: Message = {
        id: `bot_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        content: latestBotMessage,
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
    }
  }, [latestBotMessage]);

  const handleSendMessage = () => {
    if (!inputValue.trim() || isSending || !isConnected) return;
    
    // Add user message to local state
    const userMessage: Message = {
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      content: inputValue,
      sender: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Send to Railway backend
    sendMessage(inputValue);
    setInputValue('');
  };

  // Initialize with welcome message if no messages exist
  useEffect(() => {
    if (messages.length === 0 && isConnected) {
      const welcomeMessage: Message = {
        id: 'welcome',
        content: "Hi! I'm your NYC Solar Assistant. I'll help you discover your home's solar potential and savings. What's your ZIP code?",
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
    }
  }, [isConnected]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md h-[600px] flex flex-col chat-expand shadow-2xl">
        <CardHeader className="gradient-solar text-white flex-shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <MessageCircle className="mr-2 h-5 w-5" />
              NYC Solar Chat
            </CardTitle>
            <div className="flex items-center gap-2">
              {/* Connection Status */}
              <div className="flex items-center gap-1 text-xs">
                {isHealthLoading ? (
                  <LoadingSpinner size="sm" />
                ) : isConnected ? (
                  <>
                    <Wifi className="h-3 w-3" />
                    <span>Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-3 w-3" />
                    <span>Disconnected</span>
                  </>
                )}
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={onClose}
                className="text-white hover:bg-white/20"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Connection Test Button */}
          {!isConnected && (
            <div className="mt-3">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => testConnection()}
                className="text-white border-white/30 hover:bg-white/20"
              >
                Test Connection
              </Button>
            </div>
          )}
        </CardHeader>

        <CardContent className="flex-1 p-4 overflow-hidden flex flex-col">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-3">
            {messages.length === 0 && (
              <div className="flex justify-start">
                <div className="flex items-start gap-2 max-w-[80%]">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-secondary text-primary">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="p-3 rounded-lg bg-muted text-foreground">
                    <p className="text-sm">Hi! I'm your NYC Solar Assistant. I'll help you discover your home's solar potential and savings. What's your ZIP code?</p>
                  </div>
                </div>
              </div>
            )}
            
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-start gap-2 max-w-[80%] ${
                  message.sender === 'user' ? 'flex-row-reverse' : ''
                }`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    message.sender === 'user' 
                      ? 'bg-primary text-white' 
                      : 'bg-secondary text-primary'
                  }`}>
                    {message.sender === 'user' ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                  </div>
                  <div className={`p-3 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-muted text-foreground'
                  }`}>
                    <p className="text-sm">{message.content}</p>
                  </div>
                </div>
              </div>
            ))}
            
            {isSending && (
              <div className="flex justify-start">
                <div className="flex items-start gap-2 max-w-[80%]">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-secondary text-primary">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="p-3 rounded-lg bg-muted text-foreground">
                    <div className="flex items-center gap-2">
                      <LoadingSpinner size="sm" />
                      <span className="text-sm">AI is thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {sendError && (
              <div className="flex justify-start">
                <div className="flex items-start gap-2 max-w-[80%]">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-destructive text-white">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="p-3 rounded-lg bg-destructive/10 text-destructive">
                    <p className="text-sm">Sorry, I encountered an error connecting to the Railway backend. Please try again.</p>
                  </div>
                </div>
              </div>
            )}
            
            {!isConnected && !isHealthLoading && (
              <div className="flex justify-start">
                <div className="flex items-start gap-2 max-w-[80%]">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-orange-500 text-white">
                    <WifiOff className="h-4 w-4" />
                  </div>
                  <div className="p-3 rounded-lg bg-orange-50 text-orange-700">
                    <p className="text-sm">Unable to connect to Railway backend. Please check your connection and try again.</p>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="flex gap-2">
            <Input
              id="chat-message-input"
              name="chat-message"
              placeholder={isConnected ? "Type your message..." : "Connecting to Railway backend..."}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              className="flex-1"
              disabled={isSending || !isConnected}
              aria-label="Type your message"
            />
            <Button 
              onClick={handleSendMessage} 
              disabled={!inputValue.trim() || isSending || !isConnected}
            >
              {isSending ? (
                <LoadingSpinner size="sm" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Quick Actions */}
          <div className="flex flex-wrap gap-2 mt-3">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                setInputValue("What incentives are available?");
                handleSendMessage();
              }}
              disabled={isSending || !isConnected}
            >
              <Zap className="mr-1 h-3 w-3" />
              Incentives
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                setInputValue("How much will I save?");
                handleSendMessage();
              }}
              disabled={isSending || !isConnected}
            >
              Savings
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                setInputValue("Get quotes now");
                handleSendMessage();
              }}
              disabled={isSending || !isConnected}
            >
              Get Quotes
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};