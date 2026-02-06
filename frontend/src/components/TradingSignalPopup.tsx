import React, { useState, useEffect } from 'react';
import { 
  XMarkIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { useWebSocket } from '../context/WebSocketContext';

import { TradingSignal } from '../types/api';

const TradingSignalPopup: React.FC = () => {
  const { lastMessage } = useWebSocket();
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [showPopup, setShowPopup] = useState(false);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'trading_signal') {
      const newSignal: TradingSignal = {
        id: `signal_${Date.now()}`,
        symbol: lastMessage.symbol,
        signal: lastMessage.signal.signal,
        strength: 'moderate',
        confidence: lastMessage.signal.confidence,
        price: lastMessage.signal.current_price || 0,
        target: lastMessage.signal.price_target,
        stopLoss: lastMessage.signal.stop_loss,
        timeframe: '1d',
        reason: lastMessage.signal.reasoning || 'AI analysis indicates trading opportunity',
        technicalIndicators: {
          rsi: 50,
          macd: 0,
          sma20: lastMessage.signal.current_price || 0,
          sma50: lastMessage.signal.current_price || 0,
          volume: 1000000,
          volatility: 0.2
        },
        riskReward: 2.0,
        timestamp: Date.now(),
        expiry: Date.now() + 24 * 60 * 60 * 1000 // 24 hours
      };

      setSignals(prev => [newSignal, ...prev.slice(0, 4)]); // Keep only last 5 signals
      setShowPopup(true);

      // Auto-hide popup after 10 seconds
      setTimeout(() => {
        setShowPopup(false);
      }, 10000);
    }
  }, [lastMessage]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return <ArrowUpIcon className="h-6 w-6 text-green-600" />;
      case 'SELL':
        return <ArrowDownIcon className="h-6 w-6 text-red-600" />;
      case 'HOLD':
        return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />;
      default:
        return <CheckCircleIcon className="h-6 w-6 text-gray-600" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return 'border-green-200 bg-green-50';
      case 'SELL':
        return 'border-red-200 bg-red-50';
      case 'HOLD':
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handlePlaceOrder = (signal: TradingSignal) => {
    // Place order logic
    console.log('Placing order based on signal:', signal);
    // This would integrate with the trading API
  };

  const handleDismiss = (index: number) => {
    setSignals(prev => prev.filter((_, i) => i !== index));
    if (signals.length === 1) {
      setShowPopup(false);
    }
  };

  const handleDismissAll = () => {
    setSignals([]);
    setShowPopup(false);
  };

  if (!showPopup || signals.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-3 max-w-sm">
      {signals.map((signal, index) => (
        <div
          key={`${signal.symbol}-${signal.timestamp}-${index}`}
          className={`border rounded-lg shadow-lg p-4 ${getSignalColor(signal.signal)} animate-slide-in`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              {getSignalIcon(signal.signal)}
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-semibold text-gray-900">{signal.symbol}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    signal.signal === 'BUY' ? 'bg-green-100 text-green-800' :
                    signal.signal === 'SELL' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {signal.signal}
                  </span>
                </div>
                
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Confidence:</span>
                    <span className={`font-medium ${getConfidenceColor(signal.confidence)}`}>
                      {formatPercentage(signal.confidence)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Current Price:</span>
                    <span className="font-medium">{formatCurrency(signal.price)}</span>
                  </div>
                  
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Target Price:</span>
                    <span className="font-medium text-green-600">{formatCurrency(signal.target)}</span>
                  </div>
                  
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Stop Loss:</span>
                    <span className="font-medium text-red-600">{formatCurrency(signal.stopLoss)}</span>
                  </div>
                </div>
                
                <p className="mt-2 text-sm text-gray-600">{signal.reason}</p>
                
                <div className="mt-3 flex space-x-2">
                  <button
                    onClick={() => handlePlaceOrder(signal)}
                    className={`px-3 py-1 rounded text-sm font-medium ${
                      signal.signal === 'BUY' 
                        ? 'bg-green-600 text-white hover:bg-green-700'
                        : signal.signal === 'SELL'
                        ? 'bg-red-600 text-white hover:bg-red-700'
                        : 'bg-gray-600 text-white hover:bg-gray-700'
                    }`}
                  >
                    {signal.signal === 'BUY' ? 'Buy Now' : signal.signal === 'SELL' ? 'Sell Now' : 'View Details'}
                  </button>
                  <button
                    onClick={() => handleDismiss(index)}
                    className="px-3 py-1 rounded text-sm font-medium text-gray-600 hover:bg-gray-100"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
            
            <button
              onClick={() => handleDismiss(index)}
              className="ml-2 text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      ))}
      
      {signals.length > 1 && (
        <div className="flex justify-end">
          <button
            onClick={handleDismissAll}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Dismiss All
          </button>
        </div>
      )}
    </div>
  );
};

export default TradingSignalPopup;
