/**
 * Market Overview Panel Component
 * Displays market-wide context and trends
 */

import React, { useState, useEffect } from 'react';
import { unifiedAiApi } from '../services/unifiedAiApi';
import { toast } from 'react-hot-toast';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface MarketOverviewPanelProps {
  symbol?: string;
  onClose?: () => void;
  compact?: boolean;
}

interface MarketOverview {
  market_trend: string;
  volatility_level: string;
  sector_performance: Array<{
    sector: string;
    performance: number;
    trend: 'up' | 'down' | 'neutral';
  }>;
  market_sentiment: string;
  key_events?: string[];
}

const MarketOverviewPanel: React.FC<MarketOverviewPanelProps> = ({
  symbol,
  onClose,
  compact = false
}) => {
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchMarketOverview();
    if (autoRefresh) {
      const interval = setInterval(fetchMarketOverview, 300000); // 5 minutes
      return () => clearInterval(interval);
    }
  }, [symbol, autoRefresh]);

  const fetchMarketOverview = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // getMarketOverview returns MarketOverviewResponse directly
      const response = await unifiedAiApi.getMarketOverview();
      
      if (response) {
        // Map the response to our component's expected structure
        const sectorPerf = (response.sector_performance || []).map(sector => ({
          sector: sector.sector,
          performance: sector.performance,
          trend: sector.trend === 'up' ? 'up' as const :
                 sector.trend === 'down' ? 'down' as const : 'neutral' as const
        }));

        // Extract market trend from AI insights or use default
        const marketTrend = response.ai_insights?.market_outlook?.toLowerCase().includes('bull') ? 'bullish' :
                           response.ai_insights?.market_outlook?.toLowerCase().includes('bear') ? 'bearish' :
                           response.overall_sentiment === 'bullish' ? 'bullish' :
                           response.overall_sentiment === 'bearish' ? 'bearish' : 'sideways';

        // Extract volatility from market sentiment VIX level
        const volatilityLevel = response.market_sentiment?.vix_level 
          ? (response.market_sentiment.vix_level > 20 ? 'high' : 
             response.market_sentiment.vix_level > 15 ? 'medium' : 'low')
          : 'medium';

        setOverview({
          market_trend: marketTrend,
          volatility_level: volatilityLevel,
          sector_performance: sectorPerf,
          market_sentiment: response.overall_sentiment || 'neutral',
          key_events: response.ai_insights?.key_themes || []
        });
      }
    } catch (err: any) {
      console.error('Error fetching market overview:', err);
      setError(err.message || 'Failed to fetch market overview');
      toast.error('Failed to load market overview');
    } finally {
      setLoading(false);
    }
  };

  const getTrendColor = (trend: string) => {
    if (trend === 'bullish' || trend === 'up') return 'text-green-400';
    if (trend === 'bearish' || trend === 'down') return 'text-red-400';
    return 'text-yellow-400';
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'bullish' || trend === 'up') return ArrowTrendingUpIcon;
    if (trend === 'bearish' || trend === 'down') return ArrowTrendingDownIcon;
    return InformationCircleIcon;
  };

  if (compact) {
    return (
      <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ChartBarIcon className="w-4 h-4 text-blue-400" />
            <span className="text-xs font-semibold text-gray-300">Market</span>
          </div>
          {loading && (
            <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          )}
        </div>
        {overview && (
          <div className="space-y-1">
            <div className="text-xs">
              <span className="text-gray-400">Trend: </span>
              <span className={getTrendColor(overview.market_trend)}>
                {overview.market_trend.toUpperCase()}
              </span>
            </div>
            <div className="text-xs">
              <span className="text-gray-400">Volatility: </span>
              <span className="text-white">{overview.volatility_level}</span>
            </div>
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
          <ChartBarIcon className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Market Overview</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`text-xs px-2 py-1 rounded ${autoRefresh ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-700 text-gray-400'}`}
          >
            Auto
          </button>
          <button
            onClick={fetchMarketOverview}
            disabled={loading}
            className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 disabled:opacity-50"
          >
            {loading ? '...' : 'Refresh'}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {loading && !overview && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-400">Loading market data...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded p-3 mb-4">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Market Overview Content */}
      {overview && (
        <div className="space-y-4 flex-1 overflow-y-auto">
          {/* Market Trend */}
          <div className="bg-[#131722] rounded-lg p-3 border border-[#2a2e39]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-300">Market Trend</span>
              {(() => {
                const Icon = getTrendIcon(overview.market_trend);
                return <Icon className={`w-5 h-5 ${getTrendColor(overview.market_trend)}`} />;
              })()}
            </div>
            <p className={`text-lg font-bold ${getTrendColor(overview.market_trend)}`}>
              {overview.market_trend.toUpperCase()}
            </p>
          </div>

          {/* Volatility */}
          <div className="bg-[#131722] rounded-lg p-3 border border-[#2a2e39]">
            <span className="text-sm font-semibold text-gray-300">Volatility Level</span>
            <p className="text-lg font-bold text-white mt-1">
              {overview.volatility_level.toUpperCase()}
            </p>
          </div>

          {/* Market Sentiment */}
          <div className="bg-[#131722] rounded-lg p-3 border border-[#2a2e39]">
            <span className="text-sm font-semibold text-gray-300">Market Sentiment</span>
            <p className={`text-lg font-bold mt-1 ${
              overview.market_sentiment === 'positive' ? 'text-green-400' :
              overview.market_sentiment === 'negative' ? 'text-red-400' :
              'text-yellow-400'
            }`}>
              {overview.market_sentiment.toUpperCase()}
            </p>
          </div>

          {/* Sector Performance */}
          {overview.sector_performance.length > 0 && (
            <div className="bg-[#131722] rounded-lg p-3 border border-[#2a2e39]">
              <span className="text-sm font-semibold text-gray-300 mb-2 block">Sector Performance</span>
              <div className="space-y-2">
                {overview.sector_performance.slice(0, 5).map((sector, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">{sector.sector}</span>
                    <div className="flex items-center gap-2">
                      {sector.trend === 'up' && (
                        <ArrowTrendingUpIcon className="w-4 h-4 text-green-400" />
                      )}
                      {sector.trend === 'down' && (
                        <ArrowTrendingDownIcon className="w-4 h-4 text-red-400" />
                      )}
                      <span className={`text-sm font-semibold ${
                        sector.performance >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {sector.performance >= 0 ? '+' : ''}{sector.performance.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Events */}
          {overview.key_events && overview.key_events.length > 0 && (
            <div className="bg-[#131722] rounded-lg p-3 border border-[#2a2e39]">
              <span className="text-sm font-semibold text-gray-300 mb-2 block">Key Events</span>
              <ul className="space-y-1">
                {overview.key_events.slice(0, 3).map((event, idx) => (
                  <li key={idx} className="text-xs text-gray-400 flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span>{event}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* No Data */}
      {!loading && !overview && !error && (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-gray-400">No market data available</p>
        </div>
      )}
    </div>
  );
};

export default MarketOverviewPanel;

