import React, { useState, useEffect } from 'react';
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
  Area,
  AreaChart,
  ReferenceLine
} from 'recharts';
import { 
  ChartBarIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  EyeSlashIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';

interface IndicatorData {
  date: string;
  value: number;
  signal?: 'buy' | 'sell' | 'neutral';
  overbought?: boolean;
  oversold?: boolean;
}

export interface TechnicalIndicatorsProps {
  data: Array<Record<string, any>>;
  symbol: string;
  height?: number;
  className?: string;
  loading?: boolean;
  hideHeader?: boolean;
  horizontalLayout?: boolean;
  /** Callback function to show/hide the enhanced indicator selector modal */
  onShowEnhancedSelector?: (show: boolean) => void;
}

interface Indicator {
  name: string;
  enabled: boolean;
  color: string;
  dataKey: string;
  type: 'line' | 'histogram' | 'area';
  range: [number, number];
  description: string;
}

const TechnicalIndicators: React.FC<TechnicalIndicatorsProps> = ({
  data,
  symbol,
  height = 300,
  className = '',
  loading = false,
  hideHeader = false,
  horizontalLayout = false,
  onShowEnhancedSelector
}) => {
  const [indicators, setIndicators] = useState<Indicator[]>([
    {
      name: 'RSI (14)',
      enabled: true,
      color: '#8B5CF6',
      dataKey: 'rsi',
      type: 'line',
      range: [0, 100],
      description: 'Relative Strength Index - Momentum oscillator'
    },
    {
      name: 'MACD',
      enabled: true,
      color: '#3B82F6',
      dataKey: 'macd',
      type: 'histogram',
      range: [-5, 5],
      description: 'Moving Average Convergence Divergence'
    },
    {
      name: 'MACD Signal',
      enabled: true,
      color: '#EF4444',
      dataKey: 'macdSignal',
      type: 'line',
      range: [-5, 5],
      description: 'MACD Signal Line'
    },
    {
      name: 'Bollinger Upper',
      enabled: false,
      color: '#10B981',
      dataKey: 'bbUpper',
      type: 'line',
      range: [0, 10000],
      description: 'Bollinger Bands Upper Band'
    },
    {
      name: 'Bollinger Lower',
      enabled: false,
      color: '#10B981',
      dataKey: 'bbLower',
      type: 'line',
      range: [0, 10000],
      description: 'Bollinger Bands Lower Band'
    },
    {
      name: 'Williams %R',
      enabled: false,
      color: '#F59E0B',
      dataKey: 'williamsR',
      type: 'line',
      range: [-100, 0],
      description: 'Williams %R - Momentum indicator'
    },
    {
      name: 'Stochastic %K',
      enabled: false,
      color: '#06B6D4',
      dataKey: 'stochK',
      type: 'line',
      range: [0, 100],
      description: 'Stochastic Oscillator %K'
    },
    {
      name: 'Stochastic %D',
      enabled: false,
      color: '#84CC16',
      dataKey: 'stochD',
      type: 'line',
      range: [0, 100],
      description: 'Stochastic Oscillator %D'
    },
    {
      name: 'CCI (20)',
      enabled: false,
      color: '#F97316',
      dataKey: 'cci',
      type: 'line',
      range: [-200, 200],
      description: 'Commodity Channel Index - Trend indicator'
    },
    {
      name: 'ATR (14)',
      enabled: false,
      color: '#EC4899',
      dataKey: 'atr',
      type: 'line',
      range: [0, 1000],
      description: 'Average True Range - Volatility indicator'
    },
    {
      name: 'OBV',
      enabled: false,
      color: '#14B8A6',
      dataKey: 'obv',
      type: 'line',
      range: [0, 10000000],
      description: 'On-Balance Volume - Volume indicator'
    },
    {
      name: 'VWAP',
      enabled: false,
      color: '#8B5CF6',
      dataKey: 'vwap',
      type: 'line',
      range: [0, 100000],
      description: 'Volume Weighted Average Price'
    },
    {
      name: 'ADX (14)',
      enabled: false,
      color: '#06B6D4',
      dataKey: 'adx',
      type: 'line',
      range: [0, 100],
      description: 'Average Directional Index - Trend strength'
    },
    {
      name: 'MFI (14)',
      enabled: false,
      color: '#F59E0B',
      dataKey: 'mfi',
      type: 'line',
      range: [0, 100],
      description: 'Money Flow Index - Volume-weighted RSI'
    },
    {
      name: 'EMA 12',
      enabled: false,
      color: '#3B82F6',
      dataKey: 'ema12',
      type: 'line',
      range: [0, 100000],
      description: 'Exponential Moving Average 12-period'
    },
    {
      name: 'EMA 26',
      enabled: false,
      color: '#10B981',
      dataKey: 'ema26',
      type: 'line',
      range: [0, 100000],
      description: 'Exponential Moving Average 26-period'
    },
    {
      name: 'SMA 20',
      enabled: false,
      color: '#6366F1',
      dataKey: 'sma20',
      type: 'line',
      range: [0, 100000],
      description: 'Simple Moving Average 20-period'
    },
    {
      name: 'SMA 50',
      enabled: false,
      color: '#A855F7',
      dataKey: 'sma50',
      type: 'line',
      range: [0, 100000],
      description: 'Simple Moving Average 50-period'
    },
    {
      name: 'ROC (12)',
      enabled: false,
      color: '#EF4444',
      dataKey: 'roc',
      type: 'line',
      range: [-50, 50],
      description: 'Rate of Change - Momentum indicator'
    },
    {
      name: 'Momentum (10)',
      enabled: false,
      color: '#22C55E',
      dataKey: 'momentum',
      type: 'line',
      range: [-100, 100],
      description: 'Momentum Oscillator'
    },
    {
      name: 'CMF',
      enabled: false,
      color: '#06B6D4',
      dataKey: 'cmf',
      type: 'line',
      range: [-1, 1],
      description: 'Chaikin Money Flow - Volume indicator'
    },
    {
      name: 'A/D Line',
      enabled: false,
      color: '#8B5CF6',
      dataKey: 'adLine',
      type: 'line',
      range: [0, 10000000],
      description: 'Accumulation/Distribution Line'
    }
  ]);

  const [showIndicators, setShowIndicators] = useState(true);
  const [selectedIndicator, setSelectedIndicator] = useState<string | null>(null);

  // Enable default indicators when component mounts in horizontal layout mode
  useEffect(() => {
    if (horizontalLayout && data.length > 0) {
      setIndicators(prev => prev.map(ind => {
        // Enable RSI, MACD, and MACD Signal by default
        if (ind.dataKey === 'rsi' || ind.dataKey === 'macd' || ind.dataKey === 'macdSignal') {
          return { ...ind, enabled: true };
        }
        return ind;
      }));
    }
  }, [horizontalLayout, data.length]);

  // Calculate all technical indicators
  const calculateIndicators = (data: any[]) => {
    if (!data || data.length === 0) return data;

    return data.map((item, index) => {
      const newItem = { ...item };
      
      // RSI Calculation (14-period)
      if (index >= 14) {
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
        
        // RSI signals
        if (newItem.rsi > 70) {
          newItem.rsiOverbought = true;
          newItem.rsiSignal = 'sell';
        } else if (newItem.rsi < 30) {
          newItem.rsiOversold = true;
          newItem.rsiSignal = 'buy';
        } else {
          newItem.rsiSignal = 'neutral';
        }
      }

      // MACD Calculation
      if (index >= 25) {
        // EMA 12
        let ema12 = data[0].close;
        for (let i = 1; i <= index; i++) {
          ema12 = (data[i].close * (2 / 13)) + (ema12 * (1 - 2 / 13));
        }
        
        // EMA 26
        let ema26 = data[0].close;
        for (let i = 1; i <= index; i++) {
          ema26 = (data[i].close * (2 / 27)) + (ema26 * (1 - 2 / 27));
        }
        
        newItem.macd = ema12 - ema26;
        
        // MACD Signal (9-period EMA of MACD)
        if (index >= 33) {
          let macdSignal = data[index - 8].macd;
          for (let i = index - 7; i <= index; i++) {
            macdSignal = (data[i].macd * (2 / 10)) + (macdSignal * (1 - 2 / 10));
          }
          newItem.macdSignal = macdSignal;
          newItem.macdHistogram = newItem.macd - macdSignal;
        }
      }

      // Bollinger Bands (20-period, 2 standard deviations)
      if (index >= 19) {
        const period = 20;
        const prices = data.slice(index - period + 1, index + 1).map(d => d.close);
        const sma = prices.reduce((sum, price) => sum + price, 0) / period;
        const variance = prices.reduce((sum, price) => sum + Math.pow(price - sma, 2), 0) / period;
        const stdDev = Math.sqrt(variance);
        
        newItem.bbMiddle = sma;
        newItem.bbUpper = sma + (2 * stdDev);
        newItem.bbLower = sma - (2 * stdDev);
        newItem.bbWidth = (newItem.bbUpper - newItem.bbLower) / sma;
      }

      // Williams %R (14-period)
      if (index >= 13) {
        const period = 14;
        const prices = data.slice(index - period + 1, index + 1);
        const highestHigh = Math.max(...prices.map(p => p.high));
        const lowestLow = Math.min(...prices.map(p => p.low));
        newItem.williamsR = ((highestHigh - item.close) / (highestHigh - lowestLow)) * -100;
      }

      // Stochastic Oscillator (14-period)
      if (index >= 13) {
        const period = 14;
        const prices = data.slice(index - period + 1, index + 1);
        const highestHigh = Math.max(...prices.map(p => p.high));
        const lowestLow = Math.min(...prices.map(p => p.low));
        const k = ((item.close - lowestLow) / (highestHigh - lowestLow)) * 100;
        newItem.stochK = k;
        
        // %D is 3-period SMA of %K
        if (index >= 15) {
          const kValues = data.slice(index - 2, index + 1).map(d => d.stochK || 0);
          newItem.stochD = kValues.reduce((sum, val) => sum + val, 0) / 3;
        }
      }

      // CCI (Commodity Channel Index) - 20 period
      if (index >= 19) {
        const period = 20;
        const prices = data.slice(index - period + 1, index + 1);
        const typicalPrices = prices.map(p => (p.high + p.low + p.close) / 3);
        const sma = typicalPrices.reduce((sum, tp) => sum + tp, 0) / period;
        const meanDeviation = typicalPrices.reduce((sum, tp) => sum + Math.abs(tp - sma), 0) / period;
        const currentTP = (item.high + item.low + item.close) / 3;
        newItem.cci = meanDeviation !== 0 ? (currentTP - sma) / (0.015 * meanDeviation) : 0;
      }

      // ATR (Average True Range) - 14 period
      if (index >= 14) {
        const period = 14;
        let atrSum = 0;
        for (let i = index - period + 1; i <= index; i++) {
          const high = data[i].high;
          const low = data[i].low;
          const prevClose = i > 0 ? data[i - 1].close : data[i].close;
          const tr = Math.max(
            high - low,
            Math.abs(high - prevClose),
            Math.abs(low - prevClose)
          );
          atrSum += tr;
        }
        newItem.atr = atrSum / period;
      }

      // OBV (On-Balance Volume)
      if (index > 0) {
        const prevOBV = data[index - 1].obv || 0;
        if (item.close > data[index - 1].close) {
          newItem.obv = prevOBV + item.volume;
        } else if (item.close < data[index - 1].close) {
          newItem.obv = prevOBV - item.volume;
        } else {
          newItem.obv = prevOBV;
        }
      } else {
        newItem.obv = item.volume;
      }

      // VWAP (Volume Weighted Average Price) - cumulative
      if (index === 0) {
        newItem.vwap = item.close;
        newItem.cumulativeVolume = item.volume;
        newItem.cumulativePriceVolume = item.close * item.volume;
      } else {
        const prev = data[index - 1];
        const cumulativeVolume = (prev.cumulativeVolume || 0) + item.volume;
        const cumulativePriceVolume = (prev.cumulativePriceVolume || 0) + (item.close * item.volume);
        newItem.cumulativeVolume = cumulativeVolume;
        newItem.cumulativePriceVolume = cumulativePriceVolume;
        newItem.vwap = cumulativeVolume > 0 ? cumulativePriceVolume / cumulativeVolume : item.close;
      }

      // EMA 12
      if (index === 0) {
        newItem.ema12 = item.close;
      } else {
        const prevEMA12 = data[index - 1].ema12 || item.close;
        const multiplier = 2 / (12 + 1);
        newItem.ema12 = (item.close * multiplier) + (prevEMA12 * (1 - multiplier));
      }

      // EMA 26
      if (index === 0) {
        newItem.ema26 = item.close;
      } else {
        const prevEMA26 = data[index - 1].ema26 || item.close;
        const multiplier = 2 / (26 + 1);
        newItem.ema26 = (item.close * multiplier) + (prevEMA26 * (1 - multiplier));
      }

      // SMA 20
      if (index >= 19) {
        const prices = data.slice(index - 19, index + 1).map(d => d.close);
        newItem.sma20 = prices.reduce((sum, price) => sum + price, 0) / 20;
      }

      // SMA 50
      if (index >= 49) {
        const prices = data.slice(index - 49, index + 1).map(d => d.close);
        newItem.sma50 = prices.reduce((sum, price) => sum + price, 0) / 50;
      }

      // ROC (Rate of Change) - 12 period
      if (index >= 12) {
        const prevClose = data[index - 12].close;
        newItem.roc = prevClose !== 0 ? ((item.close - prevClose) / prevClose) * 100 : 0;
      }

      // Momentum - 10 period
      if (index >= 10) {
        const prevClose = data[index - 10].close;
        newItem.momentum = item.close - prevClose;
      }

      // CMF (Chaikin Money Flow) - 20 period
      if (index >= 19) {
        const period = 20;
        let moneyFlowVolume = 0;
        let totalVolume = 0;
        for (let i = index - period + 1; i <= index; i++) {
          const d = data[i];
          const typicalPrice = (d.high + d.low + d.close) / 3;
          const moneyFlowMultiplier = d.volume * ((d.close - d.low) - (d.high - d.close)) / (d.high - d.low || 1);
          moneyFlowVolume += moneyFlowMultiplier;
          totalVolume += d.volume;
        }
        newItem.cmf = totalVolume !== 0 ? moneyFlowVolume / totalVolume : 0;
      }

      // A/D Line (Accumulation/Distribution)
      if (index > 0) {
        const prevAD = data[index - 1].adLine || 0;
        const moneyFlowMultiplier = ((item.close - item.low) - (item.high - item.close)) / (item.high - item.low || 1);
        const moneyFlowVolume = moneyFlowMultiplier * item.volume;
        newItem.adLine = prevAD + moneyFlowVolume;
      } else {
        const moneyFlowMultiplier = ((item.close - item.low) - (item.high - item.close)) / (item.high - item.low || 1);
        newItem.adLine = moneyFlowMultiplier * item.volume;
      }

      // ADX (Average Directional Index) - Simplified version
      if (index >= 27) {
        // Calculate +DI and -DI first
        let plusDM = 0;
        let minusDM = 0;
        let trSum = 0;
        for (let i = index - 13; i <= index; i++) {
          if (i > 0) {
            const upMove = data[i].high - data[i - 1].high;
            const downMove = data[i - 1].low - data[i].low;
            plusDM += upMove > downMove && upMove > 0 ? upMove : 0;
            minusDM += downMove > upMove && downMove > 0 ? downMove : 0;
            
            const tr = Math.max(
              data[i].high - data[i].low,
              Math.abs(data[i].high - data[i - 1].close),
              Math.abs(data[i].low - data[i - 1].close)
            );
            trSum += tr;
          }
        }
        const atr14 = trSum / 14;
        const plusDI = atr14 !== 0 ? (plusDM / atr14) * 100 : 0;
        const minusDI = atr14 !== 0 ? (minusDM / atr14) * 100 : 0;
        const dx = (plusDI + minusDI) !== 0 ? Math.abs(plusDI - minusDI) / (plusDI + minusDI) * 100 : 0;
        
        // ADX is smoothed DX (simplified - using current DX)
        newItem.adx = dx;
      }

      // MFI (Money Flow Index) - 14 period
      if (index >= 14) {
        const period = 14;
        let positiveFlow = 0;
        let negativeFlow = 0;
        for (let i = index - period + 1; i <= index; i++) {
          const d = data[i];
          const typicalPrice = (d.high + d.low + d.close) / 3;
          const moneyFlow = typicalPrice * d.volume;
          if (i > index - period + 1) {
            const prevTP = (data[i - 1].high + data[i - 1].low + data[i - 1].close) / 3;
            if (typicalPrice > prevTP) {
              positiveFlow += moneyFlow;
            } else if (typicalPrice < prevTP) {
              negativeFlow += moneyFlow;
            }
          }
        }
        const moneyRatio = negativeFlow !== 0 ? positiveFlow / negativeFlow : 0;
        newItem.mfi = 100 - (100 / (1 + moneyRatio));
      }

      return newItem;
    });
  };

  const enhancedData = calculateIndicators(data);

  const formatValue = (value: number, indicator: Indicator) => {
    if (indicator.name.includes('RSI') || indicator.name.includes('Williams') || indicator.name.includes('Stochastic')) {
      return value.toFixed(2);
    }
    if (indicator.name.includes('MACD')) {
      return value.toFixed(4);
    }
    return value.toFixed(2);
  };

  const getIndicatorColor = (indicator: Indicator, value: number) => {
    if (indicator.name.includes('RSI')) {
      if (value > 70) return '#EF4444'; // Red for overbought
      if (value < 30) return '#10B981'; // Green for oversold
      return indicator.color;
    }
    if (indicator.name.includes('Williams') || indicator.name.includes('Stochastic')) {
      if (value > -20) return '#EF4444'; // Red for overbought
      if (value < -80) return '#10B981'; // Green for oversold
      return indicator.color;
    }
    return indicator.color;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium text-foreground mb-2">
            {new Date(label).toLocaleDateString()}
          </p>
          {payload.map((entry: any, index: number) => {
            const indicator = indicators.find(ind => ind.dataKey === entry.dataKey);
            return (
              <div key={index} className="flex items-center space-x-2 text-sm">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-muted-foreground">{entry.dataKey}:</span>
                <span className="font-medium text-foreground">
                  {indicator ? formatValue(entry.value, indicator) : entry.value.toFixed(2)}
                </span>
                {entry.payload[`${entry.dataKey}Signal`] && (
                  <span className={cn(
                    "text-xs px-2 py-1 rounded",
                    entry.payload[`${entry.dataKey}Signal`] === 'buy' 
                      ? 'bg-success/10 text-success-600'
                      : entry.payload[`${entry.dataKey}Signal`] === 'sell'
                      ? 'bg-danger/10 text-danger-600'
                      : 'bg-muted/10 text-muted-foreground'
                  )}>
                    {entry.payload[`${entry.dataKey}Signal`]}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      );
    }
    return null;
  };

  const renderIndicatorChart = (indicator: Indicator) => {
    const commonProps = {
      data: enhancedData,
      margin: { top: 20, right: 30, left: 20, bottom: 5 }
    };

    if (indicator.type === 'histogram') {
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
            domain={indicator.range}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey={indicator.dataKey}
            fill={indicator.color}
            opacity={0.7}
          />
          <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="2 2" />
        </ComposedChart>
      );
    }

    if (indicator.type === 'area') {
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
            domain={indicator.range}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={indicator.dataKey}
            stroke={indicator.color}
            fill={`${indicator.color}20`}
            strokeWidth={2}
          />
        </AreaChart>
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
          domain={indicator.range}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey={indicator.dataKey}
          stroke={indicator.color}
          strokeWidth={2}
          dot={false}
        />
        {/* Reference lines for RSI */}
        {indicator.name.includes('RSI') && (
          <>
            <ReferenceLine y={70} stroke="#EF4444" strokeDasharray="2 2" />
            <ReferenceLine y={30} stroke="#10B981" strokeDasharray="2 2" />
          </>
        )}
        {/* Reference lines for Williams %R */}
        {indicator.name.includes('Williams') && (
          <>
            <ReferenceLine y={-20} stroke="#EF4444" strokeDasharray="2 2" />
            <ReferenceLine y={-80} stroke="#10B981" strokeDasharray="2 2" />
          </>
        )}
      </LineChart>
    );
  };

  if (loading) {
    return (
      <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
        <div className="h-8 bg-muted rounded animate-pulse mb-4" />
        <div className="h-64 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  const enabledIndicators = indicators.filter(ind => ind.enabled);

  return (
    <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
      {/* Header */}
      {!hideHeader && (
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-foreground">Technical Indicators</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${enabledIndicators.length > 0 ? 'bg-success-500' : 'bg-danger-500'}`} />
            <span className="text-sm text-muted-foreground">
              {enabledIndicators.length} Active
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowIndicators(!showIndicators)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
            title="Toggle Indicators"
          >
            {showIndicators ? <EyeIcon className="h-5 w-5" /> : <EyeSlashIcon className="h-5 w-5" />}
          </button>
          <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors">
            <AdjustmentsHorizontalIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
      )}

      {/* Indicator Selection */}
      {showIndicators && (
        <div className="mb-4 p-3 bg-muted/30 rounded-lg">
          <div className="flex flex-wrap gap-4">
            {indicators.map((indicator, index) => (
              <label key={index} className="flex items-center space-x-2 cursor-pointer group">
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
                <span className="text-sm text-foreground group-hover:text-primary transition-colors">
                  {indicator.name}
                </span>
                <button
                  onClick={() => setSelectedIndicator(selectedIndicator === indicator.name ? null : indicator.name)}
                  className="p-1 text-muted-foreground hover:text-foreground"
                  title={indicator.description}
                >
                  <InformationCircleIcon className="h-4 w-4" />
                </button>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Indicator Description */}
      {selectedIndicator && (
        <div className="mb-4 p-3 bg-primary/5 border border-primary/20 rounded-lg">
          <p className="text-sm text-foreground">
            <strong>{selectedIndicator}:</strong> {indicators.find(ind => ind.name === selectedIndicator)?.description}
          </p>
        </div>
      )}

      {/* Charts */}
      <div className={cn(
        horizontalLayout 
          ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" 
          : "space-y-6"
      )}>
        {enabledIndicators.map((indicator) => (
          <div key={indicator.dataKey} className={cn(
            "border border-border rounded-lg p-4",
            horizontalLayout ? "min-w-[300px]" : ""
          )}>
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-foreground text-sm">{indicator.name}</h4>
              <div className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: indicator.color }}
                />
                <span className="text-xs text-muted-foreground hidden sm:inline">
                  {indicator.range[0]} - {indicator.range[1]}
                </span>
              </div>
            </div>
            <div style={{ height: horizontalLayout ? 200 : height / 2 }}>
              <ResponsiveContainer width="100%" height="100%">
                {renderIndicatorChart(indicator)}
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>

      {enabledIndicators.length === 0 && (
        <div className="text-center py-8">
          <ChartBarIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No indicators selected</p>
          <p className="text-sm text-muted-foreground">Enable indicators above to view technical analysis</p>
        </div>
      )}
    </div>
  );
};

export default TechnicalIndicators;

