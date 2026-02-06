/**
 * Multi-Timeframe Comparison Component
 * Compare AI analysis across different timeframes
 */

import React, { useState, useEffect } from 'react';
import { unifiedAiApi } from '../services/unifiedAiApi';
import { toast } from 'react-hot-toast';
import {
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface MultiTimeframeComparisonProps {
  symbol: string;
  onTimeframeSelect?: (timeframe: string) => void;
}

interface TimeframeAnalysis {
  timeframe: string;
  recommendation: string;
  confidence: number;
  risk_level: string;
  price_target?: number;
  stop_loss?: number;
  trend: 'up' | 'down' | 'neutral';
}

const timeframes = [
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1D', label: 'Daily' },
  { value: '1W', label: 'Weekly' },
  { value: '1M', label: 'Monthly' }
];

const MultiTimeframeComparison: React.FC<MultiTimeframeComparisonProps> = ({
  symbol,
  onTimeframeSelect
}) => {
  const [analyses, setAnalyses] = useState<TimeframeAnalysis[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('1D');

  useEffect(() => {
    if (symbol) {
      fetchMultiTimeframeAnalysis();
    }
  }, [symbol]);

  const fetchMultiTimeframeAnalysis = async () => {
    if (!symbol) return;

    setLoading(true);
    try {
      const analysisPromises = timeframes.map(async (tf): Promise<TimeframeAnalysis | null> => {
        try {
          // analyzeStock returns UnifiedAnalysisResponse directly
          const response = await unifiedAiApi.analyzeStock({
            symbol,
            user_query: `Analyze ${symbol} on ${tf.label} timeframe`,
            analysis_depth: 'STANDARD',
            include_charts: false,
            include_news: false
          });

          if (response) {
            return {
              timeframe: tf.value,
              recommendation: response.recommendation || 'HOLD',
              confidence: response.confidence_score / 100, // Convert percentage to decimal
              risk_level: response.risk_level || 'MEDIUM',
              price_target: response.price_target,
              stop_loss: response.stop_loss,
              trend: response.recommendation === 'BUY' ? 'up' as const :
                     response.recommendation === 'SELL' ? 'down' as const :
                     'neutral' as const
            };
          }
        } catch (error) {
          console.error(`Error analyzing ${tf.value}:`, error);
          return null;
        }
        return null;
      });

      const results = await Promise.all(analysisPromises);
      setAnalyses(results.filter((r): r is TimeframeAnalysis => r !== null && r !== undefined));
    } catch (error) {
      console.error('Error fetching multi-timeframe analysis:', error);
      toast.error('Failed to fetch multi-timeframe analysis');
    } finally {
      setLoading(false);
    }
  };

  const getTrendColor = (trend: string) => {
    if (trend === 'up') return 'text-green-400';
    if (trend === 'down') return 'text-red-400';
    return 'text-yellow-400';
  };

  const getTrendBgColor = (trend: string) => {
    if (trend === 'up') return 'bg-green-500/10 border-green-500/20';
    if (trend === 'down') return 'bg-red-500/10 border-red-500/20';
    return 'bg-yellow-500/10 border-yellow-500/20';
  };

  return (
    <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ClockIcon className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Multi-Timeframe Analysis</h3>
          <span className="text-xs text-gray-400">({symbol})</span>
        </div>
        <button
          onClick={fetchMultiTimeframeAnalysis}
          disabled={loading}
          className="px-3 py-1 text-xs bg-[#2a2e39] hover:bg-[#363a45] text-gray-300 rounded disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Refresh'}
        </button>
      </div>

      {loading && analyses.length === 0 ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-400">Analyzing across timeframes...</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {analyses.map((analysis) => (
            <div
              key={analysis.timeframe}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedTimeframe === analysis.timeframe
                  ? 'ring-2 ring-blue-500'
                  : ''
              } ${getTrendBgColor(analysis.trend)}`}
              onClick={() => {
                setSelectedTimeframe(analysis.timeframe);
                onTimeframeSelect?.(analysis.timeframe);
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <ChartBarIcon className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-semibold text-white">
                    {timeframes.find(tf => tf.value === analysis.timeframe)?.label}
                  </span>
                </div>
                {analysis.trend === 'up' && (
                  <ArrowTrendingUpIcon className={`w-5 h-5 ${getTrendColor(analysis.trend)}`} />
                )}
                {analysis.trend === 'down' && (
                  <ArrowTrendingDownIcon className={`w-5 h-5 ${getTrendColor(analysis.trend)}`} />
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-400">Recommendation: </span>
                  <span className={`font-semibold ${getTrendColor(analysis.trend)}`}>
                    {analysis.recommendation}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Confidence: </span>
                  <span className="text-white font-semibold">
                    {Math.round(analysis.confidence * 100)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Risk: </span>
                  <span className={`font-semibold ${
                    analysis.risk_level === 'HIGH' ? 'text-red-400' :
                    analysis.risk_level === 'LOW' ? 'text-green-400' :
                    'text-yellow-400'
                  }`}>
                    {analysis.risk_level}
                  </span>
                </div>
                {analysis.price_target && (
                  <div>
                    <span className="text-gray-400">Target: </span>
                    <span className="text-white font-semibold">
                      ₹{analysis.price_target.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && analyses.length === 0 && (
        <div className="text-center py-8">
          <p className="text-sm text-gray-400">No analysis data available</p>
        </div>
      )}
    </div>
  );
};

export default MultiTimeframeComparison;

