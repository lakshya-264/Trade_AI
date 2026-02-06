/**
 * Supply & Demand Zone Analysis Component
 * Displays institutional order blocks and zones
 */

import React, { useState, useEffect, useCallback } from 'react';
import { BoltIcon, CubeIcon } from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import LoadingSpinner from './LoadingSpinner';
import { formatChartDataForAnalysis } from '../utils/dataFormatter';

interface SDProps {
  symbol: string;
  chartData: any[];
  onZonesDetected?: (data: any) => void;
  className?: string;

  onDataUpdate?: (data: any) => void;}

const SupplyDemandAnalysis: React.FC<SDProps> = ({
  symbol,
  chartData,
  onZonesDetected,
  className = ''
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sdData, setSDData] = useState<any>(null);

  const analyzeZones = useCallback(async () => {
    if (!chartData || chartData.length === 0) return;

    try {
      setLoading(true);
      setError(null);

      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/supply-demand/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          symbol, 
          data: formatChartDataForAnalysis(chartData),
          lookback_period: 100,
          min_zone_strength: 0.5
        })
      });

      if (!response.ok) throw new Error('Failed to analyze zones');

      const result = await response.json();
      
      if (result.success && result.data) {
        setSDData(result.data);
        onZonesDetected?.(result.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [symbol, chartData, onZonesDetected]);

  // Manual refresh only - removed auto-trigger on chartData change
  // Users must click "Detect Zones" button to refresh analysis

  const getStatusBadge = (status: string) => {
    if (status === 'fresh') return 'bg-green-100 text-green-700 border-green-300';
    if (status === 'tested') return 'bg-yellow-100 text-yellow-700 border-yellow-300';
    return 'bg-gray-100 text-gray-700 border-gray-300';
  };

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', className)}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <CubeIcon className="w-6 h-6 text-orange-600" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Supply & Demand Zones</h2>
        </div>
        <button
          onClick={analyzeZones}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
        >
          <BoltIcon className="w-4 h-4" />
          {loading ? 'Analyzing...' : 'Detect Zones'}
        </button>
      </div>

      {loading && <div className="flex justify-center py-12"><LoadingSpinner /></div>}

      {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}

      {!loading && sdData && (
        <div className="space-y-6">
          {/* Statistics */}
          {sdData.statistics && (
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {sdData.statistics.active_demand_zones + sdData.statistics.active_supply_zones}
                </div>
                <div className="text-xs text-gray-600">Active Zones</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{sdData.statistics.fresh_demand}</div>
                <div className="text-xs text-gray-600">Fresh Demand</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{sdData.statistics.fresh_supply}</div>
                <div className="text-xs text-gray-600">Fresh Supply</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{sdData.statistics.strong_demand + sdData.statistics.strong_supply}</div>
                <div className="text-xs text-gray-600">Strong Zones</div>
              </div>
            </div>
          )}

          {/* Trading Signal */}
          {sdData.trading_signals && sdData.trading_signals.signal !== 'neutral' && (
            <div className={cn(
              'p-4 rounded-lg border',
              sdData.trading_signals.signal === 'buy' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
            )}>
              <div className="text-sm font-semibold text-gray-700 mb-2">Trading Signal</div>
              <div className="flex items-center gap-2">
                <span className={cn(
                  'px-3 py-1 rounded-full font-bold text-sm',
                  sdData.trading_signals.signal === 'buy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                )}>
                  {sdData.trading_signals.signal.toUpperCase()}
                </span>
                <span className="text-xs text-gray-600">{sdData.trading_signals.confidence} confidence</span>
              </div>
              <div className="mt-2 text-sm text-gray-700">{sdData.trading_signals.message}</div>
              {sdData.trading_signals.entry_suggestion && (
                <div className="mt-2 text-xs text-gray-600">
                  💡 {typeof sdData.trading_signals.entry_suggestion === 'string' 
                    ? sdData.trading_signals.entry_suggestion 
                    : sdData.trading_signals.entry_suggestion?.text || sdData.trading_signals.entry_suggestion?.message || 'Entry suggestion available'}
                </div>
              )}
            </div>
          )}

          {/* Active Demand Zones */}
          {sdData.active_demand_zones && sdData.active_demand_zones.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                Active Demand Zones ({sdData.active_demand_zones.length})
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {sdData.active_demand_zones.slice(0, 5).map((zone: any, idx: number) => (
                  <div key={idx} className="p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-green-700">
                        ₹{zone.bottom?.toFixed(2)} - ₹{zone.top?.toFixed(2)}
                      </span>
                      <span className={cn('px-2 py-0.5 rounded text-xs border', getStatusBadge(zone.status))}>
                        {zone.status_label}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-600">
                      <span>Strength: {zone.strength_label}</span>
                      <span>Move: +{zone.explosion_candle?.move_percent?.toFixed(2)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active Supply Zones */}
          {sdData.active_supply_zones && sdData.active_supply_zones.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                Active Supply Zones ({sdData.active_supply_zones.length})
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {sdData.active_supply_zones.slice(0, 5).map((zone: any, idx: number) => (
                  <div key={idx} className="p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-red-700">
                        ₹{zone.bottom?.toFixed(2)} - ₹{zone.top?.toFixed(2)}
                      </span>
                      <span className={cn('px-2 py-0.5 rounded text-xs border', getStatusBadge(zone.status))}>
                        {zone.status_label}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-600">
                      <span>Strength: {zone.strength_label}</span>
                      <span>Move: -{zone.explosion_candle?.move_percent?.toFixed(2)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Nearest Zones */}
          <div className="grid grid-cols-2 gap-4">
            {sdData.nearest_demand && (
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="text-xs text-green-700 font-semibold mb-1">Nearest Demand</div>
                <div className="text-lg font-bold text-green-700">
                  ₹{sdData.nearest_demand.mid?.toFixed(2)}
                </div>
                <div className="text-xs text-gray-600">{sdData.nearest_demand.status_label}</div>
              </div>
            )}
            {sdData.nearest_supply && (
              <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="text-xs text-red-700 font-semibold mb-1">Nearest Supply</div>
                <div className="text-lg font-bold text-red-700">
                  ₹{sdData.nearest_supply.mid?.toFixed(2)}
                </div>
                <div className="text-xs text-gray-600">{sdData.nearest_supply.status_label}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SupplyDemandAnalysis;

