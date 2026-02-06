import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ComposedChart,
  Bar,
  ReferenceLine,
  ReferenceDot,
  Cell
} from 'recharts';
import { 
  ChartBarIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  EyeSlashIcon,
  MagnifyingGlassIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  PaintBrushIcon,
  CursorArrowRaysIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import PatternCheatsheet from './PatternCheatsheet';
import { CandlestickData } from '../types/api';
// Import charting API types
import {
  TechnicalIndicatorsResponse,
  PatternRecognitionResponse,
  VolumeProfileResponse,
  SupportResistanceResponse,
  ChartTheme
} from '../services/chartingApi';

interface ProfessionalCandlestickChartProps {
  data: CandlestickData[];
  symbol: string;
  timeframe: string;
  height?: number;
  className?: string;
  showIndicators?: boolean;
  showPatterns?: boolean;
  showVolume?: boolean;
  showSupportResistance?: boolean;
  technicalIndicators?: TechnicalIndicatorsResponse | null;
  patternRecognition?: PatternRecognitionResponse | null;
  volumeProfile?: VolumeProfileResponse | null;
  supportResistance?: SupportResistanceResponse | null;
  theme?: ChartTheme | null;
  isLive?: boolean;
  loading?: boolean;
  onTimeframeChange?: (timeframe: string) => void;
  onChartTypeChange?: (type: string) => void;
}

interface TechnicalIndicator {
  name: string;
  enabled: boolean;
  color: string;
  dataKey: string;
  type: 'line' | 'histogram' | 'area';
}

const ProfessionalCandlestickChart: React.FC<ProfessionalCandlestickChartProps> = ({
  data,
  symbol,
  height = 500,
  className = '',
  loading = false,
  onTimeframeChange,
  onChartTypeChange
}) => {
  const [chartType, setChartType] = useState<'candlestick' | 'line' | 'area' | 'heikin-ashi'>('candlestick');
  const [timeframe, setTimeframe] = useState('1D');
  const [indicators, setIndicators] = useState<TechnicalIndicator[]>([
    { name: 'SMA 20', enabled: true, color: '#3B82F6', dataKey: 'sma20', type: 'line' },
    { name: 'SMA 50', enabled: false, color: '#10B981', dataKey: 'sma50', type: 'line' },
    { name: 'EMA 12', enabled: false, color: '#F59E0B', dataKey: 'ema12', type: 'line' },
    { name: 'RSI', enabled: false, color: '#8B5CF6', dataKey: 'rsi', type: 'line' },
    { name: 'MACD', enabled: false, color: '#EF4444', dataKey: 'macd', type: 'histogram' },
    { name: 'Volume', enabled: true, color: '#6B7280', dataKey: 'volume', type: 'histogram' }
  ]);
  const [showIndicators, setShowIndicators] = useState(true);
  const [showVolume, setShowVolume] = useState(true);
  const [showPatterns, setShowPatterns] = useState(true);
  const [showTodayOnly, setShowTodayOnly] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [crosshairEnabled, setCrosshairEnabled] = useState(true);
  const [chartTheme, setChartTheme] = useState<'light' | 'dark'>('light');
  const [selectedRange, setSelectedRange] = useState<{start: number, end: number} | null>(null);
  const [showCheatsheet, setShowCheatsheet] = useState(false);

  const chartRef = useRef<HTMLDivElement>(null);

  // Calculate technical indicators
  const calculateIndicators = useCallback((data: CandlestickData[]) => {
    if (!data || data.length === 0) return data;

    return data.map((item, index) => {
      const newItem = { ...item };
      
      // Simple Moving Averages
      if (index >= 19) {
        const sma20 = data.slice(index - 19, index + 1)
          .reduce((sum, d) => sum + d.close, 0) / 20;
        newItem.sma20 = sma20;
      }

      if (index >= 49) {
        const sma50 = data.slice(index - 49, index + 1)
          .reduce((sum, d) => sum + d.close, 0) / 50;
        newItem.sma50 = sma50;
      }

      // Exponential Moving Average
      if (index === 0) {
        newItem.ema12 = item.close;
      } else {
        const prevEma = newItem.ema12 || item.close;
        const multiplier = 2 / (12 + 1);
        newItem.ema12 = (item.close * multiplier) + (prevEma * (1 - multiplier));
      }

      // RSI Calculation
      if (index >= 13) {
        const gains = [];
        const losses = [];
        for (let i = index - 13; i <= index; i++) {
          const change = data[i].close - data[i - 1].close;
          gains.push(change > 0 ? change : 0);
          losses.push(change < 0 ? Math.abs(change) : 0);
        }
        const avgGain = gains.reduce((sum, gain) => sum + gain, 0) / 14;
        const avgLoss = losses.reduce((sum, loss) => sum + loss, 0) / 14;
        const rs = avgGain / (avgLoss || 0.0001);
        newItem.rsi = 100 - (100 / (1 + rs));
      }

      // MACD Calculation (simplified)
      if (index >= 25) {
        const ema12 = newItem.ema12 || item.close;
        const ema26 = data.slice(index - 25, index + 1)
          .reduce((sum, d) => sum + d.close, 0) / 26;
        newItem.macd = ema12 - ema26;
      }

      return newItem;
    });
  }, []);

  const enhancedData = calculateIndicators(data);

  // Lightweight pattern detection markers (Doji, Long-Legged Doji, Spinning Top, Morning Star, Evening Star, Engulfing, Piercing, Dark Cloud)
  const patternMarkers = React.useMemo(() => {
    const markers: { x: string; y: number; color: string; label: string }[] = [];
    if (!enhancedData || enhancedData.length < 3) return markers;
    const today = new Date();
    const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
    for (let i = 0; i < enhancedData.length; i++) {
      const c = enhancedData[i];
      const ts = new Date(c.date).getTime();
      if (showTodayOnly && ts < todayStart) continue;
      const range = c.high - c.low;
      if (range <= 0) continue;
      const body = Math.abs(c.close - c.open);
      const upper = c.high - Math.max(c.open, c.close);
      const lower = Math.min(c.open, c.close) - c.low;

      // Doji
      if (body <= range * 0.1) {
        markers.push({ x: c.date, y: c.high, color: '#6B7280', label: 'Doji' });
      }

      // Long-Legged Doji
      if (body <= range * 0.08 && upper >= range * 0.4 && lower >= range * 0.4) {
        markers.push({ x: c.date, y: c.high, color: '#A855F7', label: 'Long-Legged Doji' });
      }

      // Spinning Top
      if (body > range * 0.05 && body <= range * 0.25 && upper >= range * 0.2 && lower >= range * 0.2 && Math.abs(upper - lower) <= range * 0.15) {
        markers.push({ x: c.date, y: c.high, color: '#10B981', label: 'Spinning Top' });
      }

      // Morning Star (look-back 2)
      if (i >= 2) {
        const first = enhancedData[i - 2];
        const second = enhancedData[i - 1];
        const third = enhancedData[i];
        const firstBody = Math.abs(first.close - first.open);
        const secondBody = Math.abs(second.close - second.open);
        if (
          first.close < first.open &&
          secondBody < firstBody * 0.5 &&
          third.close > third.open &&
          third.close > (first.open + first.close) / 2
        ) {
          markers.push({ x: third.date, y: third.low, color: '#3B82F6', label: 'Morning Star' });
        }

        // Evening Star
        if (
          first.close > first.open &&
          secondBody < firstBody * 0.5 &&
          third.close < third.open &&
          third.close < (first.open + first.close) / 2
        ) {
          markers.push({ x: third.date, y: third.high, color: '#F97316', label: 'Evening Star' });
        }
      }

      // Engulfing / Piercing / Dark Cloud Cover (look-back 1)
      if (i >= 1) {
        const prev = enhancedData[i - 1];
        const cur = enhancedData[i];
        const prevMid = (prev.open + prev.close) / 2;

        if (
          prev.close < prev.open &&
          cur.close > cur.open &&
          cur.open < prev.close &&
          cur.close > prev.open
        ) {
          markers.push({ x: cur.date, y: cur.low, color: '#22C55E', label: 'Bullish Engulfing' });
        }

        if (
          prev.close > prev.open &&
          cur.close < cur.open &&
          cur.open > prev.close &&
          cur.close < prev.open
        ) {
          markers.push({ x: cur.date, y: cur.high, color: '#EF4444', label: 'Bearish Engulfing' });
        }

        // Piercing Pattern
        if (
          prev.close < prev.open &&
          cur.open < prev.low &&
          cur.close > prevMid &&
          cur.close > cur.open
        ) {
          markers.push({ x: cur.date, y: cur.low, color: '#16A34A', label: 'Piercing' });
        }

        // Dark Cloud Cover
        if (
          prev.close > prev.open &&
          cur.open > prev.high &&
          cur.close < prevMid &&
          cur.close < cur.open
        ) {
          markers.push({ x: cur.date, y: cur.high, color: '#DC2626', label: 'Dark Cloud Cover' });
        }
      }
    }
    return markers;
  }, [enhancedData, showTodayOnly]);

  const timeframes = [
    { label: '1m', value: '1m' },
    { label: '5m', value: '5m' },
    { label: '15m', value: '15m' },
    { label: '1h', value: '1h' },
    { label: '4h', value: '4h' },
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
    { label: '1M', value: '1M' }
  ];

  const chartTypes = [
    { label: 'Candlestick', value: 'candlestick' },
    { label: 'Line', value: 'line' },
    { label: 'Area', value: 'area' },
    { label: 'Heikin-Ashi', value: 'heikin-ashi' }
  ];

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatVolume = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Custom Candlestick Component
  const CustomCandlestick = (props: any) => {
    const { payload, x, y, width, height } = props;
    if (!payload) return null;

    const { open, high, low, close } = payload;
    const isGreen = close >= open;
    const bodyHeight = Math.abs(close - open);
    const bodyY = y + (isGreen ? close - Math.min(open, close) : open - Math.min(open, close));
    const wickTop = y + (high - Math.max(open, close));
    const wickBottom = y + (low - Math.min(open, close));

    return (
      <g>
        {/* High-Low Wick */}
        <line
          x1={x + width / 2}
          y1={wickTop}
          x2={x + width / 2}
          y2={wickBottom}
          stroke={isGreen ? '#10B981' : '#EF4444'}
          strokeWidth={1}
        />
        {/* Open-Close Body */}
        <rect
          x={x + width * 0.2}
          y={bodyY}
          width={width * 0.6}
          height={Math.max(bodyHeight, 1)}
          fill={isGreen ? '#10B981' : '#EF4444'}
          stroke={isGreen ? '#059669' : '#DC2626'}
          strokeWidth={1}
        />
      </g>
    );
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border rounded-lg p-4 shadow-xl min-w-[200px]">
          <p className="text-sm font-medium text-foreground mb-3">
            {formatDate(label)}
          </p>
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Open:</span>
                <span className="font-medium text-foreground">{formatCurrency(data.open)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">High:</span>
                <span className="font-medium text-success-600">{formatCurrency(data.high)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Low:</span>
                <span className="font-medium text-danger-600">{formatCurrency(data.low)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Close:</span>
                <span className="font-medium text-foreground">{formatCurrency(data.close)}</span>
              </div>
            </div>
            <div className="border-t border-border pt-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Volume:</span>
                <span className="font-medium text-foreground">{formatVolume(data.volume)}</span>
              </div>
              {data.change && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Change:</span>
                  <span className={`font-medium ${data.change >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                    {data.change >= 0 ? '+' : ''}{data.change.toFixed(2)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const renderChart = (): React.ReactElement => {
    const commonProps = {
      data: enhancedData,
      margin: { top: 20, right: 30, left: 20, bottom: 5 }
    };

    if (chartType === 'candlestick') {
      return (
        <ComposedChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 12 }}
            tickFormatter={formatDate}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatCurrency(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          {showVolume && (
            <Bar 
              dataKey="volume" 
              fill="hsl(var(--muted-foreground))" 
              opacity={0.3}
              yAxisId="volume"
            />
          )}
          <YAxis yAxisId="volume" orientation="right" hide />
          {/* Custom Candlestick rendering would go here */}
          {showPatterns && patternMarkers.map((m, idx) => (
            <ReferenceDot key={`pat-${idx}`} x={m.x} y={m.y} r={4} fill={m.color} stroke={m.color} />
          ))}
        </ComposedChart>
      );
    }

    if (chartType === 'area') {
      return (
        <ComposedChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 12 }}
            tickFormatter={formatDate}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatCurrency(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            type="monotone"
            dataKey="close"
            stroke="#3B82F6"
            fill="url(#colorGradient)"
            strokeWidth={2}
          />
          <defs>
            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
            </linearGradient>
          </defs>
        </ComposedChart>
      );
    }

    // Default line chart
    return (
      <ComposedChart {...commonProps}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis 
          dataKey="date" 
          stroke="hsl(var(--muted-foreground))"
          tick={{ fontSize: 12 }}
          tickFormatter={formatDate}
        />
        <YAxis 
          stroke="hsl(var(--muted-foreground))"
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => formatCurrency(value)}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="close"
          stroke="#3B82F6"
          strokeWidth={2}
          dot={false}
        />
        {indicators.map((indicator) => (
          indicator.enabled && (
            <Line
              key={indicator.dataKey}
              type="monotone"
              dataKey={indicator.dataKey}
              stroke={indicator.color}
              strokeWidth={1.5}
              dot={false}
              strokeDasharray={indicator.dataKey.includes('sma') ? '5 5' : '0'}
            />
          )
        ))}
      </ComposedChart>
    );
  };

  if (loading) {
    return (
      <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
        <div className="h-8 bg-muted rounded animate-pulse mb-4" />
        <div className="h-96 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className={cn("bg-card border border-border rounded-lg p-4", className)} ref={chartRef}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-foreground">{symbol} Chart</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${data.length > 0 ? 'bg-success-500' : 'bg-danger-500'}`} />
            <span className="text-sm text-muted-foreground">
              {data.length > 0 ? 'Live Data' : 'No Data'}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCrosshairEnabled(!crosshairEnabled)}
            className={cn(
              "p-2 rounded-lg transition-colors",
              crosshairEnabled 
                ? 'text-primary bg-primary/10' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            )}
            title="Toggle Crosshair"
          >
            <CursorArrowRaysIcon className="h-5 w-5" />
          </button>
          <button
            onClick={() => setShowIndicators(!showIndicators)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
            title="Toggle Indicators"
          >
            {showIndicators ? <EyeIcon className="h-5 w-5" /> : <EyeSlashIcon className="h-5 w-5" />}
          </button>
          <button
            onClick={() => setShowPatterns(!showPatterns)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
            title="Toggle Pattern Overlays"
          >
            <ChartBarIcon className="h-5 w-5" />
          </button>
          <button
            onClick={() => setShowTodayOnly(!showTodayOnly)}
            className={cn(
              "p-2 rounded-lg transition-colors",
              showTodayOnly 
                ? 'text-primary bg-primary/10' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            )}
            title="Show Today's Patterns Only"
          >
            T
          </button>
          <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors">
            <AdjustmentsHorizontalIcon className="h-5 w-5" />
          </button>
          <button
            onClick={() => setShowCheatsheet(true)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
            title="Open Pattern Cheatsheet"
          >
            <ChartBarIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 mb-4">
        {/* Timeframe Selector */}
        <div className="flex space-x-1">
          {timeframes.map((tf) => (
            <button
              key={tf.value}
              onClick={() => {
                setTimeframe(tf.value);
                onTimeframeChange?.(tf.value);
              }}
              className={cn(
                "px-3 py-1 text-sm rounded-lg transition-colors",
                timeframe === tf.value
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
              )}
            >
              {tf.label}
            </button>
          ))}
        </div>

        {/* Chart Type Selector */}
        <div className="flex space-x-1">
          {chartTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => {
                setChartType(type.value as any);
                onChartTypeChange?.(type.value);
              }}
              className={cn(
                "px-3 py-1 text-sm rounded-lg transition-colors",
                chartType === type.value
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
              )}
            >
              {type.label}
            </button>
          ))}
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.1))}
            className="p-1 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded"
          >
            <ArrowsPointingInIcon className="h-4 w-4" />
          </button>
          <span className="text-sm text-muted-foreground">{Math.round(zoomLevel * 100)}%</span>
          <button
            onClick={() => setZoomLevel(Math.min(3, zoomLevel + 0.1))}
            className="p-1 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded"
          >
            <ArrowsPointingOutIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Indicators Panel */}
      {showIndicators && (
        <div className="mb-4 p-3 bg-muted/30 rounded-lg">
          <div className="flex flex-wrap gap-4">
            {indicators.map((indicator, index) => (
              <label key={index} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={indicator.enabled}
                  onChange={(e) => {
                    const newIndicators = [...indicators];
                    newIndicators[index].enabled = e.target.checked;
                    setIndicators(newIndicators);
                  }}
                  className="rounded border-border text-primary focus:ring-primary"
                />
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: indicator.color }}
                />
                <span className="text-sm text-foreground">{indicator.name}</span>
              </label>
            ))}
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showVolume}
                onChange={(e) => setShowVolume(e.target.checked)}
                className="rounded border-border text-primary focus:ring-primary"
              />
              <div className="w-3 h-3 rounded-full bg-muted-foreground" />
              <span className="text-sm text-foreground">Volume</span>
            </label>
          </div>
        </div>
      )}

      {/* Chart */}
      <div style={{ height, transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>

      {/* Chart Info */}
      <div className="mt-4 pt-4 border-t border-border">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Open:</span>
            <span className="ml-2 font-medium text-foreground">
              {formatCurrency(data[data.length - 1]?.open || 0)}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">High:</span>
            <span className="ml-2 font-medium text-success-600">
              {formatCurrency(data[data.length - 1]?.high || 0)}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Low:</span>
            <span className="ml-2 font-medium text-danger-600">
              {formatCurrency(data[data.length - 1]?.low || 0)}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Close:</span>
            <span className="ml-2 font-medium text-foreground">
              {formatCurrency(data[data.length - 1]?.close || 0)}
            </span>
          </div>
        </div>
      </div>
      {/* Cheatsheet Modal */}
      <PatternCheatsheet isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />
    </div>
  );
};

export default ProfessionalCandlestickChart;

