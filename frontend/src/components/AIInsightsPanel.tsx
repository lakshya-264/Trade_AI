/**
 * AI Insights Panel Component
 * Displays Unified AI analysis insights alongside charts in Comprehensive Trading Pro
 */

import React, { useState, useEffect } from 'react';
import { unifiedAiApi } from '../services/unifiedAiApi';
import { toast } from 'react-hot-toast';
import {
  CpuChipIcon,
  ChartBarIcon,
  LightBulbIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface AIInsightsPanelProps {
  symbol: string;
  timeframe?: string;
  onClose?: () => void;
  compact?: boolean;
}

interface AIInsight {
  type: 'recommendation' | 'signal' | 'sentiment' | 'ml_prediction' | 'risk';
  title: string;
  value: string | number;
  confidence?: number;
  direction?: 'up' | 'down' | 'neutral';
  description?: string;
  timestamp?: string;
}

const AIInsightsPanel: React.FC<AIInsightsPanelProps> = ({
  symbol,
  timeframe = '1D',
  onClose,
  compact = false
}) => {
  const [loading, setLoading] = useState(false);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loadingTimeout, setLoadingTimeout] = useState<NodeJS.Timeout | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);

  useEffect(() => {
    if (symbol) {
      fetchAIInsights();
      if (autoRefresh) {
        const interval = setInterval(fetchAIInsights, 60000); // Refresh every minute
        return () => {
          clearInterval(interval);
          // Cleanup timeout on unmount
          if (loadingTimeout) {
            clearTimeout(loadingTimeout);
          }
        };
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, timeframe, autoRefresh]);

  const fetchAIInsights = async () => {
    if (!symbol) return;
    
    setLoading(true);
    setError(null);
    
    // Set timeout to prevent stuck loading (30 seconds)
    const timeout = setTimeout(() => {
      if (loading) {
        console.warn('AI Insights loading timeout - taking too long');
        setError('Loading is taking longer than expected. You can close this panel and try again later.');
        setLoading(false);
      }
    }, 30000); // 30 seconds
    
    setLoadingTimeout(timeout);
    
    try {
      // Fetch comprehensive analysis
      const analysisResponse = await unifiedAiApi.analyzeStock({
        symbol,
        user_query: `Analyze ${symbol} for ${timeframe} timeframe`,
        analysis_depth: 'STANDARD',
        include_charts: false,
        include_news: true
      });

      // analyzeStock returns UnifiedAnalysisResponse directly
      if (analysisResponse) {
        const data = analysisResponse;
        setAnalysisData(data);

        // Extract insights from analysis
        const extractedInsights: AIInsight[] = [];

        // Recommendation
        if (data.recommendation) {
          extractedInsights.push({
            type: 'recommendation',
            title: 'AI Recommendation',
            value: data.recommendation,
            confidence: data.confidence_score / 100, // Convert percentage to decimal
            direction: data.recommendation === 'BUY' ? 'up' : 
                      data.recommendation === 'SELL' ? 'down' : 'neutral',
            description: data.analysis_result?.ai_reasoning || data.analysis_result?.natural_language_explanation || '',
            timestamp: data.analysis_timestamp
          });
        }

        // Sentiment
        if (data.analysis_result?.sentiment_analysis) {
          const sentiment = data.analysis_result.sentiment_analysis.news_sentiment || 
                           data.analysis_result.sentiment_analysis.overall_sentiment || 'neutral';
          extractedInsights.push({
            type: 'sentiment',
            title: 'Market Sentiment',
            value: sentiment,
            confidence: (data.analysis_result.sentiment_analysis.sentiment_score || 0) / 100,
            direction: sentiment === 'positive' ? 'up' : 
                      sentiment === 'negative' ? 'down' : 'neutral',
            description: `Sentiment score: ${data.analysis_result.sentiment_analysis.sentiment_score || 0}`
          });
        }

        // ML Signals
        if (data.analysis_result?.ml_signals) {
          extractedInsights.push({
            type: 'ml_prediction',
            title: 'ML Prediction',
            value: data.analysis_result.ml_signals.prediction || 'HOLD',
            confidence: (data.analysis_result.ml_signals.confidence || 0) / 100,
            direction: data.analysis_result.ml_signals.prediction === 'BUY' ? 'up' : 
                      data.analysis_result.ml_signals.prediction === 'SELL' ? 'down' : 'neutral',
            description: `ML model confidence: ${((data.analysis_result.ml_signals.confidence || 0) / 100 * 100).toFixed(1)}%`
          });
        }

        // Risk Level
        if (data.risk_level) {
          extractedInsights.push({
            type: 'risk',
            title: 'Risk Assessment',
            value: data.risk_level,
            direction: data.risk_level === 'HIGH' ? 'down' : 
                      data.risk_level === 'LOW' ? 'up' : 'neutral',
            description: `Price Target: ${data.price_target || 'N/A'}, Stop Loss: ${data.stop_loss || 'N/A'}`
          });
        }

        setInsights(extractedInsights);
      }
    } catch (err: any) {
      console.error('Error fetching AI insights:', err);
      setError(err.message || 'Failed to fetch AI insights');
      toast.error('Failed to load AI insights');
    } finally {
      // Clear timeout
      if (loadingTimeout) {
        clearTimeout(loadingTimeout);
        setLoadingTimeout(null);
      }
      setLoading(false);
    }
  };

  // Cancel loading
  const cancelLoading = () => {
    if (loadingTimeout) {
      clearTimeout(loadingTimeout);
      setLoadingTimeout(null);
    }
    setLoading(false);
    setError('Loading cancelled by user');
  };

  const getIcon = (type: string, direction?: string) => {
    switch (type) {
      case 'recommendation':
        return direction === 'up' ? ArrowTrendingUpIcon : 
               direction === 'down' ? ArrowTrendingDownIcon : 
               InformationCircleIcon;
      case 'sentiment':
        return LightBulbIcon;
      case 'ml_prediction':
        return CpuChipIcon;
      case 'risk':
        return ExclamationTriangleIcon;
      default:
        return ChartBarIcon;
    }
  };

  const getColor = (type: string, direction?: string) => {
    if (direction === 'up') return 'text-green-400';
    if (direction === 'down') return 'text-red-400';
    return 'text-yellow-400';
  };

  const getBgColor = (type: string, direction?: string) => {
    if (direction === 'up') return 'bg-green-500/10 border-green-500/20';
    if (direction === 'down') return 'bg-red-500/10 border-red-500/20';
    return 'bg-yellow-500/10 border-yellow-500/20';
  };

  if (compact) {
    return (
      <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <CpuChipIcon className="w-4 h-4 text-blue-400" />
            <span className="text-xs font-semibold text-gray-300">AI Insights</span>
          </div>
          {loading && (
            <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          )}
        </div>
        {insights.length > 0 && (
          <div className="space-y-1">
            {insights.slice(0, 2).map((insight, idx) => {
              const Icon = getIcon(insight.type, insight.direction);
              return (
                <div key={idx} className={`text-xs ${getBgColor(insight.type, insight.direction)} rounded p-1.5`}>
                  <div className="flex items-center gap-1.5">
                    <Icon className={`w-3 h-3 ${getColor(insight.type, insight.direction)}`} />
                    <span className="text-gray-300 font-medium">{insight.title}:</span>
                    <span className={getColor(insight.type, insight.direction)}>
                      {insight.value}
                    </span>
                    {insight.confidence && (
                      <span className="text-gray-500 text-[10px]">
                        ({Math.round(insight.confidence * 100)}%)
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <CpuChipIcon className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">AI Insights</h3>
          <span className="text-xs text-gray-400">({symbol})</span>
        </div>
        <div className="flex items-center gap-2">
          {!isMinimized && (
            <>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`text-xs px-2 py-1 rounded ${autoRefresh ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-700 text-gray-400'}`}
                title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
              >
                Auto
              </button>
              <button
                onClick={loading ? cancelLoading : fetchAIInsights}
                className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 disabled:opacity-50"
                title={loading ? 'Cancel loading' : 'Refresh insights'}
              >
                {loading ? 'Cancel' : 'Refresh'}
              </button>
            </>
          )}
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-gray-400 hover:text-white"
            title={isMinimized ? 'Expand' : 'Minimize'}
          >
            {isMinimized ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            )}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white"
              title="Close panel"
            >
              <XCircleIcon className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Minimized State */}
      {isMinimized ? (
        <div className="text-center py-4">
          <p className="text-sm text-gray-400">AI Insights minimized</p>
          <button
            onClick={() => setIsMinimized(false)}
            className="mt-2 text-xs text-blue-400 hover:text-blue-300"
          >
            Click to expand
          </button>
        </div>
      ) : (
        <>
          {/* Loading State */}
          {loading && !analysisData && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-sm text-gray-400 mb-3">Analyzing {symbol}...</p>
                <button
                  onClick={cancelLoading}
                  className="text-xs px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

      {/* Error State */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded p-3 mb-4">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Insights List */}
      {insights.length > 0 && (
        <div className="space-y-3 flex-1 overflow-y-auto">
          {insights.map((insight, idx) => {
            const Icon = getIcon(insight.type, insight.direction);
            return (
              <div
                key={idx}
                className={`${getBgColor(insight.type, insight.direction)} border rounded-lg p-3`}
              >
                <div className="flex items-start gap-3">
                  <Icon className={`w-5 h-5 ${getColor(insight.type, insight.direction)} mt-0.5`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="text-sm font-semibold text-white">{insight.title}</h4>
                      {insight.confidence !== undefined && (
                        <span className="text-xs text-gray-400">
                          {Math.round(insight.confidence * 100)}% confidence
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-lg font-bold ${getColor(insight.type, insight.direction)}`}>
                        {insight.value}
                      </span>
                      {insight.direction && (
                        <span className={`text-xs ${getColor(insight.type, insight.direction)}`}>
                          {insight.direction === 'up' ? '↑' : insight.direction === 'down' ? '↓' : '→'}
                        </span>
                      )}
                    </div>
                    {insight.description && (
                      <p className="text-xs text-gray-400 line-clamp-2">{insight.description}</p>
                    )}
                    {insight.timestamp && (
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(insight.timestamp).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

          {/* No Insights */}
          {!loading && insights.length === 0 && !error && (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-sm text-gray-400">No AI insights available</p>
            </div>
          )}

          {/* Analysis Summary */}
          {analysisData && (
            <div className="mt-4 pt-4 border-t border-[#2a2e39]">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-400">Price Target:</span>
                  <span className="text-white ml-1">{analysisData.price_target || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-400">Stop Loss:</span>
                  <span className="text-white ml-1">{analysisData.stop_loss || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-400">Risk Level:</span>
                  <span className={`ml-1 ${
                    analysisData.risk_level === 'HIGH' ? 'text-red-400' :
                    analysisData.risk_level === 'LOW' ? 'text-green-400' :
                    'text-yellow-400'
                  }`}>
                    {analysisData.risk_level || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Confidence:</span>
                  <span className="text-white ml-1">
                    {analysisData.confidence_score || 0}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AIInsightsPanel;

