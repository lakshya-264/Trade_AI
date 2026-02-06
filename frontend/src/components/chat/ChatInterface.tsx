import React, { useState, useEffect, useRef } from 'react';
import { 
  PaperAirplaneIcon, 
  XMarkIcon, 
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  ChartBarIcon,
  LightBulbIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';
import { api } from '../../services/api';

interface ChatMessage {
  id: number;
  message_type: 'user' | 'assistant' | 'system' | 'prediction';
  content: string;
  metadata?: any;
  timestamp: string;
  is_ai_generated: boolean;
  confidence_score?: number;
}

interface ChatInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ isOpen, onClose, className }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
      message_type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
      is_ai_generated: false
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      const data = await api.sendMessage(inputMessage, sessionId || undefined);
      
      if (!sessionId && data.data?.session_id) {
        setSessionId(data.data.session_id);
      }

      const aiMessage: ChatMessage = {
        id: Date.now() + 1,
        message_type: 'assistant',
        content: data.data?.response || data.data?.message || 'No response received',
        metadata: data.data?.metadata,
        timestamp: data.data?.timestamp || new Date().toISOString(),
        is_ai_generated: true,
        confidence_score: data.data?.metadata?.confidence
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        message_type: 'system',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        is_ai_generated: false
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (message: ChatMessage) => {
    // Convert markdown-like formatting to HTML
    let content = message.content;
    
    // Bold text
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Code blocks
    content = content.replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>');
    
    // Line breaks
    content = content.replace(/\n/g, '<br>');
    
    return content;
  };

  const getMessageIcon = (message: ChatMessage) => {
    if (message.message_type === 'user') {
      return <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">U</div>;
    } else if (message.message_type === 'assistant') {
      return <SparklesIcon className="w-8 h-8 text-purple-600" />;
    } else if (message.message_type === 'prediction') {
      return <ChartBarIcon className="w-8 h-8 text-green-600" />;
    } else {
      return <ExclamationTriangleIcon className="w-8 h-8 text-yellow-600" />;
    }
  };

  const getIntentIcon = (intent: string) => {
    switch (intent) {
      case 'prediction':
        return <ChartBarIcon className="w-4 h-4 text-green-600" />;
      case 'portfolio':
        return <LightBulbIcon className="w-4 h-4 text-blue-600" />;
      case 'market':
        return <ChartBarIcon className="w-4 h-4 text-orange-600" />;
      case 'education':
        return <LightBulbIcon className="w-4 h-4 text-purple-600" />;
      default:
        return <ChatBubbleLeftRightIcon className="w-4 h-4 text-gray-600" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className={cn("fixed inset-0 z-50 flex items-end justify-end p-4", className)}>
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      
      {/* Chat Container */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md h-[600px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="w-6 h-6 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">AI Trading Assistant</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <SparklesIcon className="mx-auto h-12 w-12 text-primary mb-2" />
              <p>Start a conversation with your AI Trading Assistant!</p>
              <p className="text-sm">Ask me about stock predictions, trading signals, or market analysis.</p>
              <div className="mt-4 space-x-2 flex flex-wrap justify-center gap-2">
                <button
                  onClick={() => setInputMessage('Should I buy RELIANCE?')}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  <ChartBarIcon className="-ml-0.5 mr-2 h-4 w-4" /> Buy RELIANCE?
                </button>
                <button
                  onClick={() => setInputMessage('Predict TCS price for tomorrow')}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-secondary-foreground bg-secondary hover:bg-secondary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary"
                >
                  <ChartBarIcon className="-ml-0.5 mr-2 h-4 w-4" /> Predict TCS
                </button>
                <button
                  onClick={() => setInputMessage('What is my portfolio summary?')}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-accent-foreground bg-accent hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent"
                >
                  <SparklesIcon className="-ml-0.5 mr-2 h-4 w-4" /> Portfolio Summary
                </button>
                <button
                  onClick={() => setInputMessage('Should I sell HDFC?')}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-destructive-foreground bg-destructive hover:bg-destructive/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-destructive"
                >
                  <ChartBarIcon className="-ml-0.5 mr-2 h-4 w-4" /> Sell HDFC?
                </button>
              </div>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex space-x-3",
                message.message_type === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              {message.message_type !== 'user' && (
                <div className="flex-shrink-0">
                  {getMessageIcon(message)}
                </div>
              )}
              
              <div
                className={cn(
                  "max-w-xs lg:max-w-md px-4 py-2 rounded-lg",
                  message.message_type === 'user'
                    ? 'bg-blue-600 text-white'
                    : message.message_type === 'assistant'
                    ? 'bg-gray-100 text-gray-900'
                    : message.message_type === 'prediction'
                    ? 'bg-green-50 text-green-900 border border-green-200'
                    : 'bg-yellow-50 text-yellow-900 border border-yellow-200'
                )}
              >
                <div
                  dangerouslySetInnerHTML={{ __html: formatMessage(message) }}
                  className="text-sm"
                />
                
                {message.metadata?.intent && (
                  <div className="flex items-center space-x-1 mt-2 text-xs opacity-75">
                    {getIntentIcon(message.metadata.intent.type)}
                    <span className="capitalize">{message.metadata.intent.type}</span>
                  </div>
                )}
                
                {message.confidence_score && (
                  <div className="text-xs mt-1 opacity-75">
                    Confidence: {Math.round(message.confidence_score * 100)}%
                  </div>
                )}
              </div>
              
              {message.message_type === 'user' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">U</div>
                </div>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div className="flex space-x-3">
              <div className="flex-shrink-0">
                <SparklesIcon className="w-8 h-8 text-purple-600" />
              </div>
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about trading..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
