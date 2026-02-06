/**
 * Support & Resistance Analysis Component
 * Displays key price levels where price tends to react
 */

import React, { useState, useEffect, useCallback } from 'react';
import { BoltIcon, MinusIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import LoadingSpinner from './LoadingSpinner';
import { formatChartDataForAnalysis } from '../utils/dataFormatter';

interface SRProps {
  symbol: string;
  chartData: any[];
  onLevelsDetected?: (data: any) => void;
  className?: string;

  onDataUpdate?: (data: any) => void;}

const SupportResistanceAnalysis: React.FC<SRProps> = ({
  symbol,
  chartData,
  onLevelsDetected,
  className = ''
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [srData, setSRData] = useState<any>(null);
  const [minTouches, setMinTouches] = useState(2);

  const analyzeLevels = useCallback(async () => {
    console.log('[S&R Analysis] chartData:', chartData);
    console.log('[S&R Analysis] chartData type:', typeof chartData);
    console.log('[S&R Analysis] chartData is array?:', Array.isArray(chartData));
    console.log('[S&R Analysis] chartData length:', chartData?.length);
    
    if (!chartData || chartData.length === 0) {
      console.log('[S&R Analysis] ❌ No chartData - skipping analysis');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const formattedData = formatChartDataForAnalysis(chartData);
      console.log('[S&R Analysis] Formatted data:', formattedData);
      console.log('[S&R Analysis] Formatted data length:', formattedData.length);

      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/support-resistance/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          symbol, 
          data: formattedData, 
          min_touches: minTouches,
          tolerance_percent: 0.5,
          lookback_period: 100
        })
      });

      if (!response.ok) throw new Error('Failed to analyze S&R levels');

      const result = await response.json();
      
      if (result.success && result.data) {
        setSRData(result.data);
        onLevelsDetected?.(result.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [symbol, chartData, minTouches, onLevelsDetected]);

  // Manual refresh only - removed auto-trigger on chartData change
  // Users must click "Analyze" button to refresh analysis

  const getStrengthColor = (strength: any) => {
    const strengthStr = String(strength || '').toLowerCase();
    if (strengthStr === 'strong') return 'text-green-600 bg-green-50';
    if (strengthStr === 'medium') return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', className)}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <MinusIcon className="w-6 h-6 text-indigo-600" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Support & Resistance</h2>
        </div>
        <button
          onClick={analyzeLevels}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          <BoltIcon className="w-4 h-4" />
          {loading ? 'Analyzing...' : 'Detect Levels'}
        </button>
      </div>

      {loading && <div className="flex justify-center py-12"><LoadingSpinner /></div>}

      {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}

      {!loading && srData && (
        <div className="space-y-6">
          {/* Statistics */}
          {srData.statistics && (
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{srData.statistics.total_levels}</div>
                <div className="text-xs text-gray-600">Total Levels</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{srData.statistics.support_count}</div>
                <div className="text-xs text-gray-600">Support</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{srData.statistics.resistance_count}</div>
                <div className="text-xs text-gray-600">Resistance</div>
              </div>
            </div>
          )}

          {/* Current Price Zone */}
          {srData.trading_zones && srData.trading_zones.status === 'active' && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-sm font-semibold text-gray-700 mb-2">Price Zone</div>
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 font-bold text-sm">
                  {String(srData.trading_zones.zone || 'NEUTRAL').toUpperCase()}
                </span>
                <span className="text-xs text-gray-600">{srData.trading_zones.message || 'Analyzing...'}</span>
              </div>
              <div className="mt-2 text-xs text-gray-600">
                Range: ₹{srData.trading_zones.support?.toFixed(2)} - ₹{srData.trading_zones.resistance?.toFixed(2)}
                ({srData.trading_zones.range_percent?.toFixed(2)}%)
              </div>
            </div>
          )}

          {/* Nearest Levels */}
          <div className="grid grid-cols-2 gap-4">
            {/* Nearest Support */}
            {srData.nearest_support && (
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="text-sm font-semibold text-green-700 mb-2">Nearest Support</div>
                <div className="text-2xl font-bold text-green-700">₹{srData.nearest_support.price?.toFixed(2)}</div>
                <div className="text-xs text-gray-600 mt-1">
                  {srData.nearest_support.touches} touches | {srData.nearest_support.strength_label}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {srData.nearest_support.distance_percent?.toFixed(2)}% away
                </div>
              </div>
            )}

            {/* Nearest Resistance */}
            {srData.nearest_resistance && (
              <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                <div className="text-sm font-semibold text-red-700 mb-2">Nearest Resistance</div>
                <div className="text-2xl font-bold text-red-700">₹{srData.nearest_resistance.price?.toFixed(2)}</div>
                <div className="text-xs text-gray-600 mt-1">
                  {srData.nearest_resistance.touches} touches | {srData.nearest_resistance.strength_label}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {srData.nearest_resistance.distance_percent?.toFixed(2)}% away
                </div>
              </div>
            )}
          </div>

          {/* Support Levels List */}
          {srData.support_levels && srData.support_levels.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Support Levels (Top 5)</h3>
              <div className="space-y-2">
                {srData.support_levels.slice(0, 5).map((level: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-green-50 rounded">
                    <div>
                      <span className="font-bold text-green-700">₹{level.price?.toFixed(2)}</span>
                      <span className={cn('ml-2 px-2 py-0.5 rounded text-xs', getStrengthColor(level.strength_label))}>
                        {level.strength_label}
                      </span>
                    </div>
                    <span className="text-xs text-gray-600">{level.touches} touches</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Resistance Levels List */}
          {srData.resistance_levels && srData.resistance_levels.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Resistance Levels (Top 5)</h3>
              <div className="space-y-2">
                {srData.resistance_levels.slice(0, 5).map((level: any, idx: number) => (
                  <div key={idx} className={cn(
                    "flex items-center justify-between p-2 rounded",
                    level.is_double_top ? "bg-red-100 border-2 border-red-400" : "bg-red-50"
                  )}>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-red-700">₹{level.price?.toFixed(2)}</span>
                        {level.is_double_top && (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-600 text-white">
                            DOUBLE TOP
                          </span>
                        )}
                        <span className={cn('px-2 py-0.5 rounded text-xs', getStrengthColor(level.strength_label))}>
                          {level.strength_label}
                        </span>
                      </div>
                      {level.is_double_top && level.double_top_info && (
                        <div className="text-xs text-gray-600 mt-1">
                          Peaks: ₹{level.double_top_info.first_peak?.toFixed(2)} / ₹{level.double_top_info.second_peak?.toFixed(2)}
                        </div>
                      )}
                    </div>
                    <span className="text-xs text-gray-600">{level.touches} touches</span>
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

export default SupportResistanceAnalysis;

