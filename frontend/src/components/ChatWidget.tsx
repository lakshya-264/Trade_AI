/**
 * Chat Widget Component
 * Allows users to ask questions about charts in Comprehensive Trading Pro
 */

import React, { useState, useRef, useEffect } from 'react';
import { unifiedAiApi } from '../services/unifiedAiApi';
import { toast } from 'react-hot-toast';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  XMarkIcon,
  ArrowUpIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

interface ChatWidgetProps {
  symbol: string;
  timeframe?: string;
  chartContext?: any; // Chart data context for better AI responses
  onClose?: () => void;
  minimized?: boolean;
  onMinimize?: (minimized: boolean) => void;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  loading?: boolean;
}

const ChatWidget: React.FC<ChatWidgetProps> = ({
  symbol,
  timeframe = '1D',
  chartContext,
  onClose,
  minimized = false,
  onMinimize
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>(`chat-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Initialize with welcome message
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: `Hello! I'm your AI trading assistant. I can help you understand ${symbol}'s chart, analyze patterns, explain indicators, and answer trading questions. What would you like to know?`,
        timestamp: new Date()
      }]);
    }
  }, [symbol]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    // Add loading message
    const loadingMessage: ChatMessage = {
      id: `loading-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      loading: true
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Build context-aware query
      const contextQuery = chartContext 
        ? `${input.trim()}\n\nContext: Analyzing ${symbol} on ${timeframe} timeframe. Current price: ${chartContext.currentPrice || 'N/A'}.`
        : `${input.trim()}\n\nContext: Analyzing ${symbol} on ${timeframe} timeframe.`;

      const response = await unifiedAiApi.chatWithAI({
        message: contextQuery,
        session_id: sessionId || undefined,
        context_symbol: symbol
      });

      // Update session ID if returned
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      // Remove loading message and add response
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.loading);
        return [...filtered, {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: response.response || 'I apologize, but I couldn\'t generate a response. Please try again.',
          timestamp: new Date()
        }];
      });
    } catch (error: any) {
      console.error('Chat error:', error);
      toast.error('Failed to get AI response');
      
      // Remove loading message and add error message
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.loading);
        return [...filtered, {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again or rephrase your question.',
          timestamp: new Date()
        }];
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickQuestions = [
    `What's the current trend for ${symbol}?`,
    `Explain the RSI indicator for ${symbol}`,
    `What patterns do you see in ${symbol}?`,
    `Should I buy or sell ${symbol}?`,
    `What's the support and resistance for ${symbol}?`
  ];

  if (minimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => onMinimize?.(false)}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg flex items-center gap-2"
        >
          <ChatBubbleLeftRightIcon className="w-6 h-6" />
          <span className="hidden sm:inline">Chat</span>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 h-[600px] bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[#2a2e39] bg-[#131722]">
        <div className="flex items-center gap-2">
          <SparklesIcon className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">AI Assistant</h3>
          <span className="text-xs text-gray-400">({symbol})</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onMinimize?.(true)}
            className="text-gray-400 hover:text-white transition-colors"
            title="Minimize"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
              title="Close"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-[#2a2e39] text-gray-200'
              }`}
            >
              {message.loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                </div>
              ) : (
                <>
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Questions */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2">
          <p className="text-xs text-gray-400 mb-2">Quick questions:</p>
          <div className="flex flex-wrap gap-2">
            {quickQuestions.slice(0, 3).map((question, idx) => (
              <button
                key={idx}
                onClick={() => setInput(question)}
                className="text-xs px-2 py-1 bg-[#2a2e39] hover:bg-[#363a45] text-gray-300 rounded transition-colors"
              >
                {question.replace(symbol, 'this stock')}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-[#2a2e39] bg-[#131722]">
        <div className="flex items-end gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about the chart..."
            disabled={loading}
            className="flex-1 px-3 py-2 bg-[#2a2e39] border border-[#363a45] rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:opacity-50 text-white rounded-lg transition-colors"
            title="Send"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <PaperAirplaneIcon className="w-5 h-5" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};

export default ChatWidget;

