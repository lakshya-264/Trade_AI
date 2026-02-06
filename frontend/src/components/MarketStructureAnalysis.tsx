/**
 * Market Structure Analysis Component
 * Displays BOS (Break of Structure) and CHoCH (Change of Character)
 * Essential for Smart Money Concepts trading
 */

import React, { useState, useEffect, useCallback } from 'react';
import { BoltIcon, ArrowTrendingUpIcon, ArrowTrendingDownIcon, SignalIcon } from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import LoadingSpinner from './LoadingSpinner';
import { formatChartDataForAnalysis } from '../utils/dataFormatter';

interface MarketStructureProps {
  symbol: string;
  chartData: any[];
  onStructureDetected?: (data: any) => void;
  className?: string;

  onDataUpdate?: (data: any) => void;}

const MarketStructureAnalysis: React.FC<MarketStructureProps> = ({
  symbol,
  chartData,
  onStructureDetected,
  className = ''
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [structureData, setStructureData] = useState<any>(null);
  const [strength, setStrength] = useState(5);

  const analyzeStructure = useCallback(async () => {
    if (!chartData || chartData.length === 0) return;

    try {
      setLoading(true);
      setError(null);

      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/market-structure/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, data: formatChartDataForAnalysis(chartData), strength })
      });

      if (!response.ok) throw new Error('Failed to analyze market structure');

      const result = await response.json();
      
      if (result.success && result.data) {
        setStructureData(result.data);
        onStructureDetected?.(result.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [symbol, chartData, strength, onStructureDetected]);

  // Manual refresh only - removed auto-trigger on chartData change
  // Users must click "Analyze" button to refresh analysis

  const getEventBadge = (type: string) => {
    if (type.includes('Bullish')) return 'bg-green-100 text-green-700 border-green-300';
    return 'bg-red-100 text-red-700 border-red-300';
  };

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', className)}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <SignalIcon className="w-6 h-6 text-purple-600" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Market Structure</h2>
        </div>
        <button
          onClick={analyzeStructure}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          <BoltIcon className="w-4 h-4" />
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {loading && <div className="flex justify-center py-12"><LoadingSpinner /></div>}

      {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}

      {!loading && structureData && (
        <div className="space-y-6">
          {/* Current Structure */}
          {structureData.current_structure && (
            <div className={cn(
              'p-4 rounded-lg border',
              structureData.current_structure.structure === 'bullish' 
                ? 'bg-green-50 border-green-200' 
                : 'bg-red-50 border-red-200'
            )}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-1">Current Structure</div>
                  <div className={cn(
                    'text-lg font-bold',
                    structureData.current_structure.structure === 'bullish' ? 'text-green-700' : 'text-red-700'
                  )}>
                    {structureData.current_structure.structure.toUpperCase()}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600">{structureData.current_structure.message}</div>
                </div>
              </div>
            </div>
          )}

          {/* Trading Signal */}
          {structureData.trading_signals && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-sm font-semibold text-gray-700 mb-2">Trading Signal</div>
              <div className="flex items-center gap-2">
                <span className={cn(
                  'px-3 py-1 rounded-full font-bold text-sm',
                  structureData.trading_signals.signal === 'buy' ? 'bg-green-100 text-green-700' :
                  structureData.trading_signals.signal === 'sell' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                )}>
                  {structureData.trading_signals.signal.toUpperCase()}
                </span>
                <span className="text-xs text-gray-600">
                  {structureData.trading_signals.confidence} confidence
                </span>
              </div>
              <div className="mt-2 text-sm text-gray-700">{structureData.trading_signals.message}</div>
              {structureData.trading_signals.entry_suggestion && (
                <div className="mt-2 text-xs text-gray-600">
                  💡 {typeof structureData.trading_signals.entry_suggestion === 'string' 
                    ? structureData.trading_signals.entry_suggestion 
                    : structureData.trading_signals.entry_suggestion?.text || structureData.trading_signals.entry_suggestion?.message || 'Entry suggestion available'}
                </div>
              )}
            </div>
          )}

          {/* Statistics Grid */}
          {structureData.statistics && (
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{structureData.statistics.total_breaks}</div>
                <div className="text-xs text-gray-600">Total Breaks</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{structureData.statistics.bos_count}</div>
                <div className="text-xs text-gray-600">BOS Events</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{structureData.statistics.choch_count}</div>
                <div className="text-xs text-gray-600">CHoCH Events</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{structureData.statistics.bullish_breaks}</div>
                <div className="text-xs text-gray-600">Bullish Breaks</div>
              </div>
            </div>
          )}

          {/* BOS Events */}
          {structureData.bos_events && structureData.bos_events.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Break of Structure (BOS) - Recent</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {structureData.bos_events.slice(-5).reverse().map((event: any, idx: number) => (
                  <div key={idx} className={cn('p-3 rounded-lg border', getEventBadge(event.type))}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {event.type.includes('Bullish') ? 
                          <ArrowTrendingUpIcon className="w-4 h-4" /> : 
                          <ArrowTrendingDownIcon className="w-4 h-4" />
                        }
                        <span className="font-bold text-sm">{event.type}</span>
                      </div>
                      <span className="text-xs">₹{event.break_price?.toFixed(2)}</span>
                    </div>
                    <div className="text-xs mt-1">{event.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CHoCH Events */}
          {structureData.choch_events && structureData.choch_events.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Change of Character (CHoCH) - Recent</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {structureData.choch_events.slice(-5).reverse().map((event: any, idx: number) => (
                  <div key={idx} className={cn('p-3 rounded-lg border', getEventBadge(event.type))}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {event.type.includes('Bullish') ? 
                          <ArrowTrendingUpIcon className="w-4 h-4" /> : 
                          <ArrowTrendingDownIcon className="w-4 h-4" />
                        }
                        <span className="font-bold text-sm">{event.type}</span>
                      </div>
                      <span className="text-xs">₹{event.break_price?.toFixed(2)}</span>
                    </div>
                    <div className="text-xs mt-1">{event.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MarketStructureAnalysis;

