import React, { useState, useEffect, useCallback } from 'react';
import { 
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  BellIcon,
  EyeIcon,
  EyeSlashIcon,
  PlayIcon,
  PauseIcon,
  SignalIcon,
  ClockIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import { TradingSignal } from '../types/api';
import api from '../services/api';

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  close: number;
  timestamp: number;
}

interface RealTimeTradingSignalsProps {
  symbol: string;
  className?: string;
  onSignalGenerated?: (signal: TradingSignal) => void;
  autoTrade?: boolean;
}

const RealTimeTradingSignals: React.FC<RealTimeTradingSignalsProps> = ({
  symbol,
  className = '',
  onSignalGenerated,
  autoTrade = false
}) => {
  
  // Real-time Trading Signals Integration - Added by Critical Issues Fix v2.0
  const [signals, setSignals] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [aiPredictions, setAiPredictions] = useState<any[]>([]);
  const [marketSentiment, setMarketSentiment] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchSignals = async () => {
    try {
      const response = await api.get('/ai/signals');
      return response.data;
    } catch (error) {
      console.error('Error fetching signals:', error);
      return null;
    }
  };

  const fetchAnalysis = async (symbol = 'RELIANCE') => {
    try {
      const response = await api.get(`/ai/analyze/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching analysis:', error);
      return null;
    }
  };

  const fetchAiPredictions = async () => {
    try {
      const response = await api.get('/ai/predictions');
      return response.data;
    } catch (error) {
      console.error('Error fetching AI predictions:', error);
      return null;
    }
  };

  const fetchMarketSentiment = async () => {
    try {
      const response = await api.get('/ai/market-sentiment');
      return response.data;
    } catch (error) {
      console.error('Error fetching market sentiment:', error);
      return null;
    }
  };

  const loadTradingSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [signalsData, analysisData, predictionsData, sentimentData] = await Promise.all([
        fetchSignals(),
        fetchAnalysis(symbol),
        fetchAiPredictions(),
        fetchMarketSentiment()
      ]);
      
      if (signalsData && Array.isArray(signalsData)) {
        setSignals(signalsData);
        localStorage.setItem('tradingSignals', JSON.stringify(signalsData));
      }
      
      if (analysisData) {
        setAnalysis(analysisData);
        localStorage.setItem('analysis', JSON.stringify(analysisData));
      }
      
      if (predictionsData && Array.isArray(predictionsData)) {
        setAiPredictions(predictionsData);
        localStorage.setItem('aiPredictions', JSON.stringify(predictionsData));
      }
      
      if (sentimentData) {
        setMarketSentiment(sentimentData);
        localStorage.setItem('marketSentiment', JSON.stringify(sentimentData));
      }
      
      setLastUpdated(new Date().toISOString());
    } catch (error) {
      console.error('Error loading trading signals:', error);
      setError('Failed to load trading signals');
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    loadTradingSignals();
    
    // Set up interval for real-time updates
    const interval = setInterval(loadTradingSignals, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, [loadTradingSignals]);

  // Load cached data on component mount
  useEffect(() => {
    const cachedSignals = localStorage.getItem('tradingSignals');
    const cachedAnalysis = localStorage.getItem('analysis');
    const cachedPredictions = localStorage.getItem('aiPredictions');
    const cachedSentiment = localStorage.getItem('marketSentiment');
    
    if (cachedSignals) {
      try {
        setSignals(JSON.parse(cachedSignals));
      } catch (error) {
        console.error('Error parsing cached signals:', error);
      }
    }
    
    if (cachedAnalysis) {
      try {
        setAnalysis(JSON.parse(cachedAnalysis));
      } catch (error) {
        console.error('Error parsing cached analysis:', error);
      }
    }
    
    if (cachedPredictions) {
      try {
        setAiPredictions(JSON.parse(cachedPredictions));
      } catch (error) {
        console.error('Error parsing cached predictions:', error);
      }
    }
    
    if (cachedSentiment) {
      try {
        setMarketSentiment(JSON.parse(cachedSentiment));
      } catch (error) {
        console.error('Error parsing cached sentiment:', error);
      }
    }
  }, []);

  const getSignalIcon = (signal: string) => {
    switch (signal?.toLowerCase()) {
      case 'buy':
      case 'strong_buy':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'sell':
      case 'strong_sell':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'hold':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      default:
        return <SignalIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal?.toLowerCase()) {
      case 'buy':
      case 'strong_buy':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'sell':
      case 'strong_sell':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'hold':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={cn("bg-white rounded-lg shadow-sm border border-gray-200", className)}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <ChartBarIcon className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Real-Time Trading Signals
            </h2>
            {loading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={loadTradingSignals}
              disabled={loading}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            >
              <PlayIcon className="w-4 h-4" />
            </button>
            
            {lastUpdated && (
              <div className="flex items-center space-x-1 text-sm text-gray-500">
                <ClockIcon className="w-4 h-4" />
                <span>Updated {new Date(lastUpdated).toLocaleTimeString()}</span>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Trading Signals */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">Trading Signals</h3>
              <SignalIcon className="w-4 h-4 text-gray-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {signals.length}
            </div>
            <div className="text-xs text-gray-500">Active signals</div>
          </div>

          {/* AI Predictions */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">AI Predictions</h3>
              <ChartBarIcon className="w-4 h-4 text-gray-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {aiPredictions.length}
            </div>
            <div className="text-xs text-gray-500">Predictions</div>
          </div>

          {/* Market Sentiment */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">Market Sentiment</h3>
              <BellIcon className="w-4 h-4 text-gray-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {marketSentiment ? 'Active' : 'N/A'}
            </div>
            <div className="text-xs text-gray-500">Sentiment analysis</div>
          </div>

          {/* Analysis Status */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">Analysis</h3>
              <CheckCircleIcon className="w-4 h-4 text-gray-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {analysis ? 'Complete' : 'Pending'}
            </div>
            <div className="text-xs text-gray-500">Technical analysis</div>
          </div>
        </div>

        {/* Signals List */}
        {signals.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Recent Signals</h3>
            {signals.slice(0, 5).map((signal: any, index: number) => (
              <div
                key={index}
                className={cn(
                  "p-4 rounded-lg border",
                  getSignalColor(signal.signal || signal.action)
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getSignalIcon(signal.signal || signal.action)}
                    <div>
                      <div className="font-medium">
                        {signal.symbol || signal.stock || 'N/A'}
                      </div>
                      <div className="text-sm opacity-75">
                        {signal.signal || signal.action || 'No signal'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-medium">
                      ₹{signal.price || signal.current_price || 'N/A'}
                    </div>
                    <div className="text-sm opacity-75">
                      {signal.confidence ? `${signal.confidence}%` : 'N/A'}
                    </div>
                  </div>
                </div>
                
                {signal.reason && (
                  <div className="mt-2 text-sm opacity-75">
                    {signal.reason}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* AI Predictions */}
        {aiPredictions.length > 0 && (
          <div className="mt-6 space-y-3">
            <h3 className="text-lg font-medium text-gray-900 mb-3">AI Predictions</h3>
            {aiPredictions.slice(0, 3).map((prediction: any, index: number) => (
              <div key={index} className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-blue-900">
                      {prediction.symbol || prediction.stock || 'N/A'}
                    </div>
                    <div className="text-sm text-blue-700">
                      {prediction.prediction || prediction.forecast || 'No prediction'}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-medium text-blue-900">
                      {prediction.target_price ? `₹${prediction.target_price}` : 'N/A'}
                    </div>
                    <div className="text-sm text-blue-700">
                      {prediction.timeframe || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Market Sentiment */}
        {marketSentiment && (
          <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <h3 className="text-lg font-medium text-purple-900 mb-2">Market Sentiment</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-900">
                  {marketSentiment.overall_sentiment || 'N/A'}
                </div>
                <div className="text-sm text-purple-700">Overall Sentiment</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-900">
                  {marketSentiment.fear_greed_index || 'N/A'}
                </div>
                <div className="text-sm text-purple-700">Fear & Greed Index</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-900">
                  {marketSentiment.volatility || 'N/A'}
                </div>
                <div className="text-sm text-purple-700">Volatility</div>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Summary */}
        {analysis && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-lg font-medium text-green-900 mb-2">Technical Analysis</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-green-700 mb-1">Trend</div>
                <div className="font-medium text-green-900">
                  {analysis.trend || analysis.trend_direction || 'N/A'}
                </div>
              </div>
              
              <div>
                <div className="text-sm text-green-700 mb-1">Support/Resistance</div>
                <div className="font-medium text-green-900">
                  {analysis.support_resistance || 'N/A'}
                </div>
              </div>
              
              <div>
                <div className="text-sm text-green-700 mb-1">RSI</div>
                <div className="font-medium text-green-900">
                  {analysis.rsi || 'N/A'}
                </div>
              </div>
              
              <div>
                <div className="text-sm text-green-700 mb-1">MACD</div>
                <div className="font-medium text-green-900">
                  {analysis.macd || 'N/A'}
                </div>
              </div>
            </div>
          </div>
        )}

        {signals.length === 0 && aiPredictions.length === 0 && !analysis && !marketSentiment && !loading && (
          <div className="text-center py-8">
            <SignalIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
            <p className="text-gray-500 mb-4">
              No trading signals or analysis data available at the moment.
            </p>
            <button
              onClick={loadTradingSignals}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Load Data
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RealTimeTradingSignals;