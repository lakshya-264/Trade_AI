/**
 * Fibonacci Analysis Component
 * Visualizes Fibonacci retracement and extension levels on charts
 * Provides interactive tools for drawing Fibonacci levels
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ChartBarIcon,
  AdjustmentsHorizontalIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CheckCircleIcon,
  XMarkIcon,
  InformationCircleIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import LoadingSpinner from './LoadingSpinner';

interface FibonacciLevel {
  level: string;
  price: number;
  significance: 'high' | 'medium' | 'low';
}

interface FibonacciSetup {
  type: 'retracement' | 'extension';
  trend_direction: string;
  swing_high: number;
  swing_low: number;
  levels: Record<string, number>;
  key_levels: FibonacciLevel[];
  current_price?: number;
  current_level?: string;
  trading_implications: any;
}

interface FibonacciAnalysisProps {
  symbol: string;
  chartData: any[];
  currentPrice: number;
  onLevelsCalculated?: (levels: FibonacciSetup) => void;
  className?: string;
}

const FibonacciAnalysis: React.FC<FibonacciAnalysisProps> = ({
  symbol,
  chartData,
  currentPrice,
  onLevelsCalculated,
  className = ''
}) => {
  // State
  const [mode, setMode] = useState<'auto' | 'manual'>('auto');
  const [fibSetups, setFibSetups] = useState<FibonacciSetup[]>([]);
  const [selectedSetup, setSelectedSetup] = useState<FibonacciSetup | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Manual mode state
  const [manualHigh, setManualHigh] = useState<string>('');
  const [manualLow, setManualLow] = useState<string>('');
  const [trendDirection, setTrendDirection] = useState<'uptrend' | 'downtrend'>('uptrend');
  const [showSettings, setShowSettings] = useState(false);
  
  // Settings
  const [lookbackPeriod, setLookbackPeriod] = useState(50);
  const [minSwingStrength, setMinSwingStrength] = useState(5);
  const [showAllLevels, setShowAllLevels] = useState(false);

  // Auto-detect Fibonacci levels
  const autoDetectFibonacci = useCallback(async () => {
    if (!chartData || chartData.length === 0) {
      setError('No chart data available');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/fibonacci/auto-detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          data: chartData,
          lookback_period: lookbackPeriod,
          min_swing_strength: minSwingStrength
        })
      });

      if (!response.ok) {
        throw new Error('Failed to detect Fibonacci levels');
      }

      const result = await response.json();
      
      if (result.success && result.data) {
        setFibSetups(result.data);
        if (result.data.length > 0) {
          setSelectedSetup(result.data[0]);
          onLevelsCalculated?.(result.data[0]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect Fibonacci levels');
      console.error('Fibonacci auto-detect error:', err);
    } finally {
      setLoading(false);
    }
  }, [symbol, chartData, lookbackPeriod, minSwingStrength, onLevelsCalculated]);

  // Calculate manual Fibonacci
  const calculateManualFibonacci = useCallback(async () => {
    if (!manualHigh || !manualLow) {
      setError('Please enter both high and low prices');
      return;
    }

    const high = parseFloat(manualHigh);
    const low = parseFloat(manualLow);

    if (isNaN(high) || isNaN(low)) {
      setError('Please enter valid numbers');
      return;
    }

    if (high <= low) {
      setError('High price must be greater than low price');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/fibonacci/retracement', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          high,
          low,
          trend_direction: trendDirection
        })
      });

      if (!response.ok) {
        throw new Error('Failed to calculate Fibonacci levels');
      }

      const result = await response.json();
      
      if (result.success && result.data) {
        const setup = result.data as FibonacciSetup;
        setup.current_price = currentPrice;
        setFibSetups([setup]);
        setSelectedSetup(setup);
        onLevelsCalculated?.(setup);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate Fibonacci levels');
      console.error('Fibonacci manual calculation error:', err);
    } finally {
      setLoading(false);
    }
  }, [manualHigh, manualLow, trendDirection, currentPrice, onLevelsCalculated]);

  // Initial auto-detect
  useEffect(() => {
    if (mode === 'auto' && chartData && chartData.length > 0) {
      autoDetectFibonacci();
    }
  }, [mode, chartData]); // Only run when mode or chartData changes

  // Helper functions
  const getLevelColor = (level: string, significance: string): string => {
    const colors: Record<string, string> = {
      '0.0': 'bg-blue-500',
      '0.236': 'bg-purple-400',
      '0.382': 'bg-yellow-500',
      '0.500': 'bg-green-500',
      '0.618': 'bg-red-500',
      '0.786': 'bg-orange-500',
      '1.0': 'bg-blue-500'
    };
    return colors[level] || 'bg-gray-500';
  };

  const getSignificanceBadge = (significance: string): JSX.Element => {
    const badges: Record<string, { color: string; text: string }> = {
      high: { color: 'bg-red-100 text-red-800', text: 'High' },
      medium: { color: 'bg-yellow-100 text-yellow-800', text: 'Medium' },
      low: { color: 'bg-gray-100 text-gray-800', text: 'Low' }
    };
    const badge = badges[significance] || badges.low;
    return (
      <span className={cn('px-2 py-1 text-xs font-medium rounded', badge.color)}>
        {badge.text}
      </span>
    );
  };

  const formatPrice = (price: number): string => {
    return `₹${price.toFixed(2)}`;
  };

  const getPriceDistance = (level: number, current: number): string => {
    const diff = ((level - current) / current) * 100;
    return `${diff > 0 ? '+' : ''}${diff.toFixed(2)}%`;
  };

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <ChartBarIcon className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Fibonacci Analysis
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
            title="Settings"
          >
            <AdjustmentsHorizontalIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Mode Selector */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setMode('auto')}
          className={cn(
            'flex-1 py-2 px-4 rounded-lg font-medium transition-colors',
            mode === 'auto'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
          )}
        >
          Auto Detect
        </button>
        <button
          onClick={() => setMode('manual')}
          className={cn(
            'flex-1 py-2 px-4 rounded-lg font-medium transition-colors',
            mode === 'manual'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
          )}
        >
          Manual Draw
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white">
            Settings
          </h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Lookback Period: {lookbackPeriod}
              </label>
              <input
                type="range"
                min="20"
                max="200"
                value={lookbackPeriod}
                onChange={(e) => setLookbackPeriod(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Swing Strength: {minSwingStrength}
              </label>
              <input
                type="range"
                min="3"
                max="10"
                value={minSwingStrength}
                onChange={(e) => setMinSwingStrength(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="showAllLevels"
                checked={showAllLevels}
                onChange={(e) => setShowAllLevels(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="showAllLevels" className="text-sm text-gray-700 dark:text-gray-300">
                Show all levels (including minor ones)
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Manual Mode Inputs */}
      {mode === 'manual' && (
        <div className="mb-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Swing High
              </label>
              <input
                type="number"
                value={manualHigh}
                onChange={(e) => setManualHigh(e.target.value)}
                placeholder="e.g., 2850.00"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                step="0.01"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Swing Low
              </label>
              <input
                type="number"
                value={manualLow}
                onChange={(e) => setManualLow(e.target.value)}
                placeholder="e.g., 2650.00"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                step="0.01"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Trend Direction
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setTrendDirection('uptrend')}
                className={cn(
                  'flex-1 py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2',
                  trendDirection === 'uptrend'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                )}
              >
                <ArrowTrendingUpIcon className="w-4 h-4" />
                Uptrend
              </button>
              <button
                onClick={() => setTrendDirection('downtrend')}
                className={cn(
                  'flex-1 py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2',
                  trendDirection === 'downtrend'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                )}
              >
                <ArrowTrendingDownIcon className="w-4 h-4" />
                Downtrend
              </button>
            </div>
          </div>

          <button
            onClick={calculateManualFibonacci}
            disabled={loading}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg font-medium 
                     hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Calculating...' : 'Calculate Fibonacci Levels'}
          </button>
        </div>
      )}

      {/* Auto Mode Button */}
      {mode === 'auto' && (
        <button
          onClick={autoDetectFibonacci}
          disabled={loading}
          className="w-full mb-6 py-2 px-4 bg-blue-600 text-white rounded-lg font-medium 
                   hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" />
              Detecting Levels...
            </>
          ) : (
            'Auto-Detect Fibonacci Levels'
          )}
        </button>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner />
        </div>
      )}

      {/* Fibonacci Levels Display */}
      {!loading && selectedSetup && (
        <div className="space-y-6">
          {/* Setup Info */}
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Setup Range
              </span>
              <span className={cn(
                'px-2 py-1 text-xs font-medium rounded',
                selectedSetup.trend_direction === 'uptrend'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              )}>
                {selectedSetup.trend_direction.toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">High:</span>
                <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                  {formatPrice(selectedSetup.swing_high)}
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Low:</span>
                <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                  {formatPrice(selectedSetup.swing_low)}
                </span>
              </div>
            </div>
            {selectedSetup.current_price && (
              <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                <span className="text-gray-600 dark:text-gray-400">Current Price:</span>
                <span className="ml-2 font-semibold text-blue-600 dark:text-blue-400">
                  {formatPrice(selectedSetup.current_price)}
                </span>
              </div>
            )}
          </div>

          {/* Fibonacci Levels */}
          <div>
            <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white">
              Fibonacci Levels
            </h3>
            <div className="space-y-2">
              {Object.entries(selectedSetup.levels)
                .filter(([level]) => showAllLevels || ['0.0', '0.236', '0.382', '0.500', '0.618', '0.786', '1.0'].includes(level))
                .sort((a, b) => b[1] - a[1]) // Sort by price descending
                .map(([level, price]) => {
                  const significance = selectedSetup.key_levels?.find(kl => kl.level === level)?.significance || 'low';
                  const isNearCurrent = selectedSetup.current_price && 
                    Math.abs(price - selectedSetup.current_price) / selectedSetup.current_price < 0.01;
                  
                  return (
                    <div
                      key={level}
                      className={cn(
                        'p-3 rounded-lg border transition-colors',
                        isNearCurrent
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
                          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={cn('w-3 h-3 rounded-full', getLevelColor(level, significance))} />
                          <div>
                            <div className="font-semibold text-gray-900 dark:text-white">
                              {(parseFloat(level) * 100).toFixed(1)}% - {formatPrice(price)}
                            </div>
                            {selectedSetup.current_price && (
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                {getPriceDistance(price, selectedSetup.current_price)}
                              </div>
                            )}
                          </div>
                        </div>
                        {getSignificanceBadge(significance)}
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Trading Implications */}
          {selectedSetup.trading_implications && (
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-start gap-2">
                <InformationCircleIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-semibold mb-2 text-blue-900 dark:text-blue-100">
                    Trading Implications
                  </h3>
                  <div className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                    {selectedSetup.trading_implications.optimal_entry_zones && (
                      <div>
                        <span className="font-medium">Entry Zones:</span> {selectedSetup.trading_implications.optimal_entry_zones.join(', ')}
                      </div>
                    )}
                    {selectedSetup.trading_implications.stop_loss_suggestion && (
                      <div>
                        <span className="font-medium">Stop Loss:</span> {selectedSetup.trading_implications.stop_loss_suggestion}
                      </div>
                    )}
                    {selectedSetup.trading_implications.confidence && (
                      <div>
                        <span className="font-medium">Confidence:</span> {selectedSetup.trading_implications.confidence}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Data */}
      {!loading && !selectedSetup && !error && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <ChartBarIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No Fibonacci levels calculated yet</p>
          <p className="text-sm mt-1">
            {mode === 'auto' ? 'Click "Auto-Detect" to find levels' : 'Enter high and low prices to calculate'}
          </p>
        </div>
      )}
    </div>
  );
};

export default FibonacciAnalysis;

