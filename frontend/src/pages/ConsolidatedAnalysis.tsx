/**
 * Consolidated Analysis Page
 * Single page combining all analysis features:
 * - Chart with overlays
 * - Price Action (Support/Resistance, Pivot Points)
 * - Levels (HH/HL/LH/LL)
 * - Gap Filling Detection & Signals
 * - Trendline Retesting Signals
 * - News Integration
 */

import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { httpClient } from '../config/api';
import { toast } from 'react-hot-toast';
import ResponsiveCard from '../components/ResponsiveCard';
import LoadingSpinner from '../components/LoadingSpinner';
import NewsFeed from '../components/NewsFeed';
import StockSelector from '../components/StockSelector';
import UnifiedAIChart from '../components/UnifiedAIChart';
import { formatINR } from '../utils/currency';
import { 
  TrendingUp, TrendingDown, Minus, 
  ArrowUp, ArrowDown, AlertCircle,
  BarChart3, Activity, Target, Zap
} from 'lucide-react';

interface GapInfo {
  type: 'UPWARD' | 'DOWNWARD';
  start: number;
  end: number;
  size: number;
  size_pct: number;
  is_filled: boolean;
  filled_at?: string;
  date: string;
}

interface TrendlineInfo {
  id: string;
  type: string;
  strength: string;
  is_broken: boolean;
  retest_info?: {
    retested: boolean;
    retest_price?: number;
    retest_type?: string;
  };
  retest_signal?: {
    type: string;
    message: string;
    strength: string;
    timestamp: string;
  };
}

interface SignalInfo {
  type: string;
  message: string;
  timestamp: string;
  strength: string;
  price?: number;
}

const toFiniteNumber = (value: any): number | null => {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : null;
};

const toDateMs = (value: any): number | null => {
  if (value === null || value === undefined) return null;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return null;
    return value < 10_000_000_000 ? value * 1000 : value;
  }
  const parsed = new Date(String(value)).getTime();
  return Number.isFinite(parsed) ? parsed : null;
};

const normalizeConsolidatedChartData = (raw: any[]): any[] => {
  if (!Array.isArray(raw)) return [];

  const normalized = raw
    .map((candle: any) => {
      const tsMs =
        toDateMs(candle?.timestamp) ??
        toDateMs(candle?.time) ??
        toDateMs(candle?.date) ??
        toDateMs(candle?.datetime);

      const open = toFiniteNumber(candle?.open ?? candle?.o);
      const high = toFiniteNumber(candle?.high ?? candle?.h);
      const low = toFiniteNumber(candle?.low ?? candle?.l);
      const close = toFiniteNumber(candle?.close ?? candle?.c);
      const volume = toFiniteNumber(candle?.volume ?? candle?.v ?? candle?.vol) ?? 0;

      if (tsMs === null || open === null || high === null || low === null || close === null) {
        return null;
      }

      return {
        ...candle,
        date: new Date(tsMs).toISOString(),
        timestamp: Math.floor(tsMs / 1000),
        open,
        high,
        low,
        close,
        volume,
      };
    })
    .filter(Boolean) as any[];

  normalized.sort((a, b) => (a.timestamp ?? 0) - (b.timestamp ?? 0));

  const seen = new Set<number>();
  const deduped: any[] = [];
  for (let i = normalized.length - 1; i >= 0; i--) {
    const t = normalized[i].timestamp;
    if (!seen.has(t)) {
      seen.add(t);
      deduped.unshift(normalized[i]);
    }
  }

  return deduped;
};

const ConsolidatedAnalysis: React.FC = () => {
  const { symbol: symbolFromUrl } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const symbol = symbolFromUrl || searchParams.get('symbol') || 'RELIANCE';
  const timeframe = searchParams.get('timeframe') || '1D';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [priceAction, setPriceAction] = useState<any>(null);
  const [levels, setLevels] = useState<any>(null);
  const [gaps, setGaps] = useState<GapInfo[]>([]);
  const [trendlines, setTrendlines] = useState<TrendlineInfo[]>([]);
  const [signals, setSignals] = useState<SignalInfo[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);

  // Fetch consolidated analysis
  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!symbol) return;

      setLoading(true);
      setError(null);

      try {
        const response = await httpClient.get('/api/analysis/consolidated', {
          params: {
            symbol,
            timeframe,
            days: 100
          }
        }) as any;

        if (response.success && response.data) {
          const data = response.data;
          setAnalysisData(data);
          setCurrentPrice(toFiniteNumber(data.current_price) ?? 0);
          setPriceAction(data.price_action || {});
          setLevels(data.levels || {});
          setGaps(data.gaps || []);
          setTrendlines(data.trendlines || []);
          setSignals(data.signals || []);

          const normalizedChartData = normalizeConsolidatedChartData(data.chart_data || []);
          setChartData(normalizedChartData);
        } else {
          throw new Error(response.error || 'Failed to fetch analysis');
        }
      } catch (err: any) {
        console.error('Error fetching consolidated analysis:', err);
        setError(err.message || 'Failed to load analysis');
        toast.error('Failed to load consolidated analysis');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [symbol, timeframe]);

  // Note: Chart overlays will be handled by AdvancedChart component internally
  // Support/Resistance and other levels are displayed in panels below

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  const pivotPoint = toFiniteNumber(priceAction?.pivot_point);
  const support1 = toFiniteNumber(priceAction?.support_1);
  const resistance1 = toFiniteNumber(priceAction?.resistance_1);
  const supportLevels = Array.isArray(priceAction?.support_levels)
    ? (priceAction.support_levels
        .map((v: any) => toFiniteNumber(v))
        .filter((v: number | null): v is number => v !== null)
        .slice(0, 3) as number[])
    : [];
  const resistanceLevels = Array.isArray(priceAction?.resistance_levels)
    ? (priceAction.resistance_levels
        .map((v: any) => toFiniteNumber(v))
        .filter((v: number | null): v is number => v !== null)
        .slice(0, 3) as number[])
    : [];

  const totalHH = toFiniteNumber(levels?.total_hh) ?? 0;
  const totalHL = toFiniteNumber(levels?.total_hl) ?? 0;
  const totalLH = toFiniteNumber(levels?.total_lh) ?? 0;
  const totalLL = toFiniteNumber(levels?.total_ll) ?? 0;

  const timeRanges = [
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '1Y', value: '1Y' }
  ];

  return (
    <div className="space-y-4 p-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-2xl font-bold mb-2">Consolidated Analysis</h1>
          <div className="max-w-md">
            <StockSelector
              value={symbol}
              onChange={(newSymbol) => {
                if (newSymbol && newSymbol !== symbol) {
                  navigate(`/consolidated-analysis/${newSymbol}?timeframe=${timeframe}`, { replace: true });
                }
              }}
              showNavigateButton={false}
              className="w-full"
            />
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-600">
            {formatINR(currentPrice)}
          </div>
          <div className={`text-sm flex items-center gap-1 ${
            priceAction?.trend === 'UPTREND' ? 'text-green-600' : 
            priceAction?.trend === 'DOWNTREND' ? 'text-red-600' : 
            'text-gray-600'
          }`}>
            {priceAction?.trend === 'UPTREND' && <TrendingUp className="w-4 h-4" />}
            {priceAction?.trend === 'DOWNTREND' && <TrendingDown className="w-4 h-4" />}
            {priceAction?.trend === 'SIDEWAYS' && <Minus className="w-4 h-4" />}
            {priceAction?.trend || 'Loading...'}
          </div>
        </div>
      </div>

      {/* Main Chart */}
      <ResponsiveCard padding="lg">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 space-y-2 sm:space-y-0">
          <h3 className="text-lg font-semibold text-gray-900">{`${symbol} Chart`}</h3>
          <div className="flex space-x-1">
            {timeRanges.map((range) => (
              <button
                key={range.value}
                onClick={() => {
                  const next = new URLSearchParams(searchParams);
                  next.set('timeframe', range.value);
                  setSearchParams(next, { replace: true });
                }}
                className={`px-2 py-1 text-xs sm:px-3 sm:py-1 sm:text-sm rounded-md transition-colors ${
                  timeframe === range.value
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        <UnifiedAIChart
          symbol={symbol}
          timeframe={timeframe}
          height={500}
          showDrawingTools={false}
          showPatternVisualization={false}
        />
      </ResponsiveCard>

      {/* Feature Panels Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Price Action Panel */}
        <ResponsiveCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold">Price Action</h3>
          </div>
          {priceAction && (
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-600">Pivot Point:</span>
                <span className="ml-2 font-medium">{formatINR(pivotPoint ?? 0)}</span>
              </div>
              <div>
                <span className="text-gray-600">Support 1:</span>
                <span className="ml-2 font-medium text-green-600">
                  {formatINR(support1 ?? 0)}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Resistance 1:</span>
                <span className="ml-2 font-medium text-red-600">
                  {formatINR(resistance1 ?? 0)}
                </span>
              </div>
              <div className="pt-2 border-t">
                <span className="text-gray-600">Key Supports:</span>
                <div className="mt-1 space-y-1">
                  {supportLevels.map((level: number, idx: number) => (
                    <div key={idx} className="text-xs text-green-600">
                      S{idx + 1}: {formatINR(level)}
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <span className="text-gray-600">Key Resistances:</span>
                <div className="mt-1 space-y-1">
                  {resistanceLevels.map((level: number, idx: number) => (
                    <div key={idx} className="text-xs text-red-600">
                      R{idx + 1}: {formatINR(level)}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </ResponsiveCard>

        {/* Levels Panel (HH/HL/LH/LL) */}
        <ResponsiveCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold">Market Structure</h3>
          </div>
          {levels && (
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-green-50 p-2 rounded">
                  <div className="flex items-center gap-1 text-green-700">
                    <ArrowUp className="w-4 h-4" />
                    <span className="font-medium">HH</span>
                  </div>
                  <div className="text-lg font-bold text-green-700">{totalHH}</div>
                </div>
                <div className="bg-green-50 p-2 rounded">
                  <div className="flex items-center gap-1 text-green-700">
                    <ArrowUp className="w-4 h-4" />
                    <span className="font-medium">HL</span>
                  </div>
                  <div className="text-lg font-bold text-green-700">{totalHL}</div>
                </div>
                <div className="bg-red-50 p-2 rounded">
                  <div className="flex items-center gap-1 text-red-700">
                    <ArrowDown className="w-4 h-4" />
                    <span className="font-medium">LH</span>
                  </div>
                  <div className="text-lg font-bold text-red-700">{totalLH}</div>
                </div>
                <div className="bg-red-50 p-2 rounded">
                  <div className="flex items-center gap-1 text-red-700">
                    <ArrowDown className="w-4 h-4" />
                    <span className="font-medium">LL</span>
                  </div>
                  <div className="text-lg font-bold text-red-700">{totalLL}</div>
                </div>
              </div>
              <div className="pt-2 border-t">
                <span className="text-gray-600">Trend:</span>
                <span className={`ml-2 font-medium ${
                  levels.trend_structure === 'uptrend' ? 'text-green-600' :
                  levels.trend_structure === 'downtrend' ? 'text-red-600' :
                  'text-gray-600'
                }`}>
                  {levels.trend_structure?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
            </div>
          )}
        </ResponsiveCard>

        {/* Gaps Panel */}
        <ResponsiveCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-5 h-5 text-orange-600" />
            <h3 className="font-semibold">Gap Analysis</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Total Gaps:</span>
              <span className="font-medium">{gaps.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Filled:</span>
              <span className="font-medium text-green-600">
                {gaps.filter(g => g.is_filled).length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Active:</span>
              <span className="font-medium text-orange-600">
                {gaps.filter(g => !g.is_filled).length}
              </span>
            </div>
            {gaps.filter(g => !g.is_filled).length > 0 && (
              <div className="pt-2 border-t space-y-1">
                <div className="text-xs font-medium text-gray-600">Active Gaps:</div>
                {gaps.filter(g => !g.is_filled).slice(0, 3).map((gap, idx) => (
                  <div key={idx} className="text-xs">
                    <span className={gap.type === 'UPWARD' ? 'text-green-600' : 'text-red-600'}>
                      {gap.type} Gap: {formatINR(gap.start)} - {formatINR(gap.end)}
                    </span>
                    <span className="text-gray-500 ml-1">({(toFiniteNumber(gap.size_pct) ?? 0).toFixed(2)}%)</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </ResponsiveCard>

        {/* Trendlines Panel */}
        <ResponsiveCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-5 h-5 text-indigo-600" />
            <h3 className="font-semibold">Trendlines</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Active:</span>
              <span className="font-medium">
                {trendlines.filter(tl => !tl.is_broken).length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Broken:</span>
              <span className="font-medium text-red-600">
                {trendlines.filter(tl => tl.is_broken).length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Retested:</span>
              <span className="font-medium text-blue-600">
                {trendlines.filter(tl => tl.retest_info?.retested).length}
              </span>
            </div>
            {trendlines.filter(tl => tl.retest_signal).length > 0 && (
              <div className="pt-2 border-t">
                <div className="text-xs font-medium text-gray-600 mb-1">Retest Signals:</div>
                {trendlines.filter(tl => tl.retest_signal).slice(0, 2).map((tl, idx) => (
                  <div key={idx} className="text-xs text-blue-600 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {tl.retest_signal?.message}
                  </div>
                ))}
              </div>
            )}
          </div>
        </ResponsiveCard>

        {/* Signals Panel */}
        <ResponsiveCard padding="md">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-5 h-5 text-yellow-600" />
            <h3 className="font-semibold">Trading Signals</h3>
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {signals.length === 0 ? (
              <div className="text-sm text-gray-500">No signals at this time</div>
            ) : (
              signals.slice(0, 10).map((signal, idx) => (
                <div
                  key={idx}
                  className={`text-xs p-2 rounded border-l-2 ${
                    signal.strength === 'HIGH' ? 'bg-red-50 border-red-500' :
                    signal.strength === 'MEDIUM' ? 'bg-yellow-50 border-yellow-500' :
                    'bg-blue-50 border-blue-500'
                  }`}
                >
                  <div className="font-medium">{signal.type}</div>
                  <div className="text-gray-600">{signal.message}</div>
                  {signal.price && (
                    <div className="text-gray-500 mt-1">Price: {formatINR(signal.price)}</div>
                  )}
                </div>
              ))
            )}
          </div>
        </ResponsiveCard>

        {/* News Panel */}
        <ResponsiveCard padding="md" className="md:col-span-2 lg:col-span-1">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold">News & Sentiment</h3>
          </div>
          <div className="text-sm text-gray-600">
            <p className="mb-2">Latest news for <strong>{symbol}</strong>:</p>
            <NewsFeed />
          </div>
        </ResponsiveCard>
      </div>

      {/* Detailed Gaps Table */}
      {gaps.length > 0 && (
        <ResponsiveCard padding="md">
          <h3 className="font-semibold mb-3">Gap Details</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Start</th>
                  <th className="text-left p-2">End</th>
                  <th className="text-left p-2">Size</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Filled At</th>
                </tr>
              </thead>
              <tbody>
                {gaps.slice(0, 10).map((gap, idx) => (
                  <tr key={idx} className="border-b">
                    <td className={`p-2 font-medium ${
                      gap.type === 'UPWARD' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {gap.type}
                    </td>
                    <td className="p-2">{formatINR(gap.start)}</td>
                    <td className="p-2">{formatINR(gap.end)}</td>
                    <td className="p-2">{gap.size_pct.toFixed(2)}%</td>
                    <td className="p-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        gap.is_filled ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
                      }`}>
                        {gap.is_filled ? 'Filled' : 'Active'}
                      </span>
                    </td>
                    <td className="p-2 text-gray-600">
                      {gap.filled_at ? new Date(gap.filled_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ResponsiveCard>
      )}
    </div>
  );
};

export default ConsolidatedAnalysis;
