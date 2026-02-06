import React, { useState, useEffect, useCallback } from 'react';
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
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import { TrendingUpIcon } from 'lucide-react';
import { cn } from '../lib/utils';

interface PortfolioData {
  date: string;
  portfolioValue: number;
  benchmarkValue: number;
  pnl: number;
  pnlPercent: number;
  benchmarkPnl: number;
  benchmarkPnlPercent: number;
  alpha: number;
  beta: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
  volume: number;
}

interface PortfolioPerformanceChartProps {
  data: PortfolioData[];
  benchmark?: string;
  className?: string;
  loading?: boolean;
}

const PortfolioPerformanceChart: React.FC<PortfolioPerformanceChartProps> = ({
  data,
  benchmark = 'NIFTY 50',
  className = '',
  loading = false
}) => {
  const [chartType, setChartType] = useState<'performance' | 'returns' | 'drawdown' | 'volatility'>('performance');
  const [timeframe, setTimeframe] = useState('1Y');
  const [showBenchmark, setShowBenchmark] = useState(true);
  const [showIndicators, setShowIndicators] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  const timeframes = [
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '6M', value: '6M' },
    { label: '1Y', value: '1Y' },
    { label: '2Y', value: '2Y' },
    { label: '5Y', value: '5Y' },
    { label: 'ALL', value: 'ALL' }
  ];

  const chartTypes = [
    { id: 'performance', name: 'Performance', description: 'Portfolio vs Benchmark' },
    { id: 'returns', name: 'Returns', description: 'Daily returns comparison' },
    { id: 'drawdown', name: 'Drawdown', description: 'Maximum drawdown analysis' },
    { id: 'volatility', name: 'Volatility', description: 'Risk metrics over time' }
  ];

  const metrics = [
    { key: 'alpha', name: 'Alpha', value: data[data.length - 1]?.alpha || 0, unit: '%', color: '#10B981' },
    { key: 'beta', name: 'Beta', value: data[data.length - 1]?.beta || 0, unit: '', color: '#3B82F6' },
    { key: 'sharpeRatio', name: 'Sharpe Ratio', value: data[data.length - 1]?.sharpeRatio || 0, unit: '', color: '#8B5CF6' },
    { key: 'maxDrawdown', name: 'Max Drawdown', value: data[data.length - 1]?.maxDrawdown || 0, unit: '%', color: '#EF4444' },
    { key: 'volatility', name: 'Volatility', value: data[data.length - 1]?.volatility || 0, unit: '%', color: '#F59E0B' }
  ];

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-4 shadow-xl min-w-[300px]">
          <p className="text-sm font-medium text-foreground mb-3">
            {formatDate(label)}
          </p>
          <div className="space-y-2">
            {payload.map((entry: any, index: number) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-muted-foreground">{entry.dataKey}:</span>
                </div>
                <span className="font-medium text-foreground">
                  {entry.dataKey.includes('Value') 
                    ? formatCurrency(entry.value)
                    : formatPercentage(entry.value)
                  }
                </span>
              </div>
            ))}
            <div className="border-t border-border pt-2 mt-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Portfolio P&L:</span>
                <span className={`font-medium ${payload[0]?.payload?.pnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                  {formatCurrency(payload[0]?.payload?.pnl || 0)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Benchmark P&L:</span>
                <span className={`font-medium ${payload[0]?.payload?.benchmarkPnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                  {formatCurrency(payload[0]?.payload?.benchmarkPnl || 0)}
                </span>
              </div>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const renderChart = (): React.ReactElement => {
    const commonProps = {
      data,
      margin: { top: 20, right: 30, left: 20, bottom: 5 }
    };

    if (chartType === 'performance') {
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
            dataKey="portfolioValue"
            stroke="#3B82F6"
            strokeWidth={3}
            dot={false}
            name="Portfolio"
          />
          {showBenchmark && (
            <Line
              type="monotone"
              dataKey="benchmarkValue"
              stroke="#10B981"
              strokeWidth={2}
              dot={false}
              strokeDasharray="5 5"
              name={benchmark}
            />
          )}
        </ComposedChart>
      );
    }

    if (chartType === 'returns') {
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
            tickFormatter={(value) => formatPercentage(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="pnlPercent"
            fill="#3B82F6"
            opacity={0.7}
            name="Portfolio Returns"
          />
          {showBenchmark && (
            <Bar 
              dataKey="benchmarkPnlPercent"
              fill="#10B981"
              opacity={0.7}
              name={`${benchmark} Returns`}
            />
          )}
          <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="2 2" />
        </ComposedChart>
      );
    }

    if (chartType === 'drawdown') {
      return (
        <AreaChart {...commonProps}>
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
            tickFormatter={(value) => formatPercentage(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="maxDrawdown"
            stroke="#EF4444"
            fill="url(#drawdownGradient)"
            strokeWidth={2}
            name="Max Drawdown"
          />
          <defs>
            <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
        </AreaChart>
      );
    }

    if (chartType === 'volatility') {
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
            tickFormatter={(value) => formatPercentage(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="volatility"
            stroke="#F59E0B"
            strokeWidth={2}
            dot={false}
            name="Volatility"
          />
          <ReferenceLine y={15} stroke="hsl(var(--muted-foreground))" strokeDasharray="2 2" />
        </ComposedChart>
      );
    }

    // Fallback chart type
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
          dataKey="portfolioValue"
          stroke="#3B82F6"
          strokeWidth={3}
          dot={false}
          name="Portfolio"
        />
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

  const totalReturn = data[data.length - 1]?.pnlPercent || 0;
  const benchmarkReturn = data[data.length - 1]?.benchmarkPnlPercent || 0;
  const outperformance = totalReturn - benchmarkReturn;

  return (
    <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-foreground">Portfolio Performance</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${totalReturn >= 0 ? 'bg-success-500' : 'bg-danger-500'}`} />
            <span className="text-sm text-muted-foreground">
              {formatPercentage(totalReturn)} vs {benchmark}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowBenchmark(!showBenchmark)}
            className={cn(
              "p-2 rounded-lg transition-colors",
              showBenchmark 
                ? 'text-primary bg-primary/10' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            )}
            title="Toggle Benchmark"
          >
            <ChartBarIcon className="h-5 w-5" />
          </button>
          <button
            onClick={() => setShowIndicators(!showIndicators)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
            title="Toggle Indicators"
          >
            {showIndicators ? <EyeIcon className="h-5 w-5" /> : <EyeSlashIcon className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-4 bg-muted/30 rounded-lg">
          <div className="text-2xl font-bold text-foreground">
            {formatCurrency(data[data.length - 1]?.portfolioValue || 0)}
          </div>
          <div className="text-sm text-muted-foreground">Portfolio Value</div>
        </div>
        <div className="text-center p-4 bg-muted/30 rounded-lg">
          <div className={`text-2xl font-bold ${totalReturn >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            {formatPercentage(totalReturn)}
          </div>
          <div className="text-sm text-muted-foreground">Total Return</div>
        </div>
        <div className="text-center p-4 bg-muted/30 rounded-lg">
          <div className={`text-2xl font-bold ${outperformance >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            {formatPercentage(outperformance)}
          </div>
          <div className="text-sm text-muted-foreground">vs {benchmark}</div>
        </div>
        <div className="text-center p-4 bg-muted/30 rounded-lg">
          <div className="text-2xl font-bold text-foreground">
            {formatCurrency(data[data.length - 1]?.pnl || 0)}
          </div>
          <div className="text-sm text-muted-foreground">P&L</div>
        </div>
      </div>

      {/* Chart Type Selector */}
      <div className="flex flex-wrap gap-2 mb-4">
        {chartTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => setChartType(type.id as any)}
            className={cn(
              "px-3 py-1 text-sm rounded-lg transition-colors",
              chartType === type.id
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
            )}
            title={type.description}
          >
            {type.name}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="h-96 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>

      {/* Risk Metrics */}
      {showIndicators && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {metrics.map((metric) => (
            <div
              key={metric.key}
              onClick={() => setSelectedMetric(selectedMetric === metric.key ? null : metric.key)}
              className={cn(
                "p-3 rounded-lg border cursor-pointer transition-colors",
                selectedMetric === metric.key
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:bg-muted/30'
              )}
            >
              <div className="text-sm text-muted-foreground mb-1">{metric.name}</div>
              <div 
                className="text-lg font-bold"
                style={{ color: metric.color }}
              >
                {metric.value.toFixed(2)}{metric.unit}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Metric Details */}
      {selectedMetric && (
        <div className="mt-4 p-3 bg-muted/30 rounded-lg">
          <p className="text-sm text-foreground">
            <strong>{metrics.find(m => m.key === selectedMetric)?.name}:</strong> {
              selectedMetric === 'alpha' ? 'Measures excess return relative to benchmark' :
              selectedMetric === 'beta' ? 'Measures portfolio volatility relative to market' :
              selectedMetric === 'sharpeRatio' ? 'Risk-adjusted return measure' :
              selectedMetric === 'maxDrawdown' ? 'Maximum peak-to-trough decline' :
              'Annualized volatility measure'
            }
          </p>
        </div>
      )}
    </div>
  );
};

export default PortfolioPerformanceChart;

