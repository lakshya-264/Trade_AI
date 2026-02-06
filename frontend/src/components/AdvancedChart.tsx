import React, { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  ComposedChart,
  Bar,
  ReferenceLine
} from 'recharts';
import { 
  ChartBarIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';

interface AdvancedChartProps {
  data: Array<Record<string, any>>;
  symbol: string;
  height?: number;
  className?: string;
  loading?: boolean;
}

interface TechnicalIndicator {
  name: string;
  enabled: boolean;
  color: string;
  dataKey: string;
}

const AdvancedChart: React.FC<AdvancedChartProps> = ({
  data,
  symbol,
  height = 400,
  className = '',
  loading = false
}) => {
  const [chartType, setChartType] = useState<'line' | 'area' | 'candlestick'>('line');
  const [timeframe, setTimeframe] = useState('1D');
  const [indicators, setIndicators] = useState<TechnicalIndicator[]>([
    { name: 'SMA 20', enabled: true, color: '#3B82F6', dataKey: 'sma20' },
    { name: 'SMA 50', enabled: false, color: '#10B981', dataKey: 'sma50' },
    { name: 'EMA 12', enabled: false, color: '#F59E0B', dataKey: 'ema12' },
    { name: 'Volume', enabled: true, color: '#6B7280', dataKey: 'volume' }
  ]);
  const [showIndicators, setShowIndicators] = useState(true);
  const [showVolume, setShowVolume] = useState(true);

  // Calculate technical indicators
  const calculateIndicators = (data: any[]) => {
    if (!data || data.length === 0) return data;

    return data.map((item, index) => {
      const newItem = { ...item };
      
      // Simple Moving Average 20
      if (index >= 19) {
        const sma20 = data.slice(index - 19, index + 1)
          .reduce((sum, d) => sum + d.close, 0) / 20;
        newItem.sma20 = sma20;
      }

      // Simple Moving Average 50
      if (index >= 49) {
        const sma50 = data.slice(index - 49, index + 1)
          .reduce((sum, d) => sum + d.close, 0) / 50;
        newItem.sma50 = sma50;
      }

      // Exponential Moving Average 12
      if (index === 0) {
        newItem.ema12 = item.close;
      } else {
        const prevEma = newItem.ema12 || item.close;
        const multiplier = 2 / (12 + 1);
        newItem.ema12 = (item.close * multiplier) + (prevEma * (1 - multiplier));
      }

      return newItem;
    });
  };

  const enhancedData = calculateIndicators(data);

  const timeframes = [
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '1Y', value: '1Y' }
  ];

  const chartTypes = [
    { label: 'Line', value: 'line' },
    { label: 'Area', value: 'area' },
    { label: 'Candlestick', value: 'candlestick' }
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

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium text-foreground mb-2">
            {new Date(label).toLocaleDateString()}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center space-x-2 text-sm">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-muted-foreground">{entry.dataKey}:</span>
              <span className="font-medium text-foreground">
                {entry.dataKey === 'volume' 
                  ? formatVolume(entry.value)
                  : formatCurrency(entry.value)
                }
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      data: enhancedData,
      margin: { top: 20, right: 30, left: 20, bottom: 5 }
    };

    if (chartType === 'area') {
      return (
        <AreaChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatCurrency(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
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
        </AreaChart>
      );
    }

    if (chartType === 'candlestick') {
      return (
        <ComposedChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
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
        </ComposedChart>
      );
    }

    // Default line chart
    return (
      <LineChart {...commonProps}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis 
          dataKey="date" 
          stroke="hsl(var(--muted-foreground))"
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => new Date(value).toLocaleDateString()}
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
      </LineChart>
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
    <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">{symbol} Chart</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowIndicators(!showIndicators)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
          >
            {showIndicators ? <EyeIcon className="h-5 w-5" /> : <EyeSlashIcon className="h-5 w-5" />}
          </button>
          <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors">
            <AdjustmentsHorizontalIcon className="h-5 w-5" />
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
              onClick={() => setTimeframe(tf.value)}
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
              onClick={() => setChartType(type.value as any)}
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
      <div style={{ height }}>
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
    </div>
  );
};

export default AdvancedChart;
