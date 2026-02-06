import React, { useState } from 'react';
import { 
  SparklesIcon, 
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  LightBulbIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import ChatInterface from './ChatInterface';
import PredictionDisplay from './PredictionDisplay';
import { api } from '../../services/api';

interface AIAssistantProps {
  className?: string;
}

const AIAssistant: React.FC<AIAssistantProps> = ({ className = '' }) => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [showPrediction, setShowPrediction] = useState(false);
  const [predictionData, setPredictionData] = useState<any>(null);

  const handlePredictionRequest = async (symbol: string, type: string = 'price') => {
    try {
      // const data = await api.predictStock(symbol, `Analyze ${symbol} stock`, type);
      const data = { prediction: 'Stock analysis not available', confidence: 0.5 };
      setPredictionData(data);
      setShowPrediction(true);
    } catch (error) {
      console.error('Error getting prediction:', error);
    }
  };

  const quickActions = [
    {
      icon: ChartBarIcon,
      label: 'Market Analysis',
      action: () => {
        setIsChatOpen(true);
        // Auto-send message
        setTimeout(() => {
          const input = document.querySelector('input[placeholder*="Ask me anything"]') as HTMLInputElement;
          if (input) {
            input.value = 'What\'s the current market trend?';
            input.dispatchEvent(new Event('input', { bubbles: true }));
          }
        }, 100);
      },
      color: 'text-blue-600 bg-blue-50 hover:bg-blue-100'
    },
    {
      icon: LightBulbIcon,
      label: 'Portfolio Advice',
      action: () => {
        setIsChatOpen(true);
        setTimeout(() => {
          const input = document.querySelector('input[placeholder*="Ask me anything"]') as HTMLInputElement;
          if (input) {
            input.value = 'Analyze my portfolio and give me advice';
            input.dispatchEvent(new Event('input', { bubbles: true }));
          }
        }, 100);
      },
      color: 'text-green-600 bg-green-50 hover:bg-green-100'
    },
    {
      icon: SparklesIcon,
      label: 'Stock Prediction',
      action: () => {
        const symbol = prompt('Enter stock symbol (e.g., RELIANCE, TCS):');
        if (symbol) {
          handlePredictionRequest(symbol.toUpperCase());
        }
      },
      color: 'text-purple-600 bg-purple-50 hover:bg-purple-100'
    }
  ];

  return (
    <>
      {/* Floating AI Assistant Button */}
      <div className={`fixed bottom-6 right-6 z-40 ${className}`}>
        <div className="relative">
          {/* Quick Actions */}
          <div className="absolute bottom-16 right-0 space-y-2">
            {quickActions.map((action, index) => (
              <button
                key={index}
                onClick={action.action}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105 ${action.color}`}
                style={{
                  animationDelay: `${index * 0.1}s`,
                  animation: 'slideInUp 0.3s ease-out forwards'
                }}
              >
                <action.icon className="w-4 h-4" />
                <span className="text-sm font-medium whitespace-nowrap">
                  {action.label}
                </span>
              </button>
            ))}
          </div>

          {/* Main AI Button */}
          <button
            onClick={() => setIsChatOpen(true)}
            className="w-14 h-14 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center justify-center group"
          >
            <SparklesIcon className="w-6 h-6 group-hover:animate-pulse" />
          </button>

          {/* Notification Badge */}
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
            <span className="text-xs text-white font-bold">AI</span>
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <ChatInterface
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />

      {/* Prediction Display Modal */}
      {showPrediction && predictionData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">AI Prediction</h2>
              <button
                onClick={() => setShowPrediction(false)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              <PredictionDisplay
                symbol={predictionData.symbol}
                predictionType={predictionData.prediction_type}
                data={predictionData.data}
              />
            </div>
          </div>
        </div>
      )}

      {/* CSS for animations */}
      <style>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </>
  );
};

export default AIAssistant;
