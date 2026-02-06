import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useWindowSize } from '../hooks/useWindowSize';
import { ChartLoadingState } from './LoadingStates';
import AdvancedChart from './AdvancedChart';

interface ResponsiveChartProps {
  data: Array<Record<string, any>>;
  dataKey: string;
  title: string;
  height?: number;
  className?: string;
  showTimeRange?: boolean;
  onTimeRangeChange?: (range: string) => void;
  loading?: boolean;
  symbol?: string;
  advanced?: boolean;
}

const ResponsiveChart: React.FC<ResponsiveChartProps> = ({
  data,
  dataKey,
  title,
  height,
  className = '',
  showTimeRange = true,
  onTimeRangeChange,
  loading = false,
  symbol = 'STOCK',
  advanced = false
}) => {
  const { width } = useWindowSize();
  const [chartHeight, setChartHeight] = useState(height || 300);
  const [timeRange, setTimeRange] = useState('1M');

  const timeRanges = [
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '1Y', value: '1Y' }
  ];

  useEffect(() => {
    // Adjust chart height based on screen size
    if (width < 640) {
      setChartHeight(200);
    } else if (width < 1024) {
      setChartHeight(250);
    } else {
      setChartHeight(height || 300);
    }
  }, [width, height]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      if (width < 640) {
        // Mobile: show only month and day
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } else {
        // Desktop: show full date
        return date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          year: width > 1024 ? 'numeric' : undefined
        });
      }
    } catch {
      return dateString;
    }
  };

  const handleTimeRangeChange = (range: string) => {
    setTimeRange(range);
    onTimeRangeChange?.(range);
  };

  if (loading) {
    return <ChartLoadingState height={chartHeight} />;
  }

  // Use advanced chart if requested
  if (advanced) {
    return (
      <AdvancedChart
        data={data}
        symbol={symbol}
        height={chartHeight}
        className={className}
        loading={loading}
      />
    );
  }

  return (
    <div className={`w-full ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 space-y-2 sm:space-y-0">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        
        {showTimeRange && (
          <div className="flex space-x-1">
            {timeRanges.map((range) => (
              <button
                key={range.value}
                onClick={() => handleTimeRangeChange(range.value)}
                className={`px-2 py-1 text-xs sm:px-3 sm:py-1 sm:text-sm rounded-md transition-colors ${
                  timeRange === range.value
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Chart */}
      <div style={{ height: chartHeight, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="#f0f0f0"
              vertical={width > 640}
            />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: width < 640 ? 10 : 12 }}
              tickFormatter={formatDate}
              interval={width < 640 ? 'preserveStartEnd' : 'preserveStartEnd'}
            />
            <YAxis 
              tick={{ fontSize: width < 640 ? 10 : 12 }}
              tickFormatter={formatCurrency}
              width={width < 640 ? 50 : 60}
            />
            <Tooltip 
              formatter={(value: any) => [formatCurrency(value), 'Value']}
              labelFormatter={(label: string) => formatDate(label)}
              contentStyle={{
                fontSize: width < 640 ? '12px' : '14px',
                padding: width < 640 ? '8px' : '12px'
              }}
            />
            <Line 
              type="monotone" 
              dataKey={dataKey} 
              stroke="#3B82F6" 
              strokeWidth={width < 640 ? 1.5 : 2}
              dot={false}
              activeDot={{ r: width < 640 ? 3 : 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ResponsiveChart;
