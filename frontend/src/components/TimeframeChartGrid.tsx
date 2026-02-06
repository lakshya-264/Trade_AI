/**
 * Timeframe Chart Grid Component
 * Manages responsive grid layout for 1, 2, or 4 charts
 */

import React from 'react';
import { IChartApi, ISeriesApi } from 'lightweight-charts';
import { SynchronizedChart } from './SynchronizedChart';
import { CandleData } from '../services/multiTimeframeApi';
import { HTFLevel } from '../services/htfLevelService';
import { ChartLayout } from './ChartLayoutSwitcher';

interface TimeframeChartGridProps {
  layout: ChartLayout;
  symbol: string;
  timeframes: string[];
  chartData: Record<string, CandleData[]>;
  htfLevels?: Record<string, HTFLevel[]>;
  showHTFLevels?: boolean;
  syncEnabled?: boolean;
  onChartReady?: (timeframe: string, chart: IChartApi, series: ISeriesApi<'Candlestick'>) => void;
  className?: string;
}

export const TimeframeChartGrid: React.FC<TimeframeChartGridProps> = ({
  layout,
  symbol,
  timeframes,
  chartData,
  htfLevels = {},
  showHTFLevels = true,
  syncEnabled = true,
  onChartReady,
  className = '',
}) => {
  const getLayoutClasses = (): string => {
    switch (layout) {
      case 1:
        return 'grid-cols-1 grid-rows-1';
      case 2:
        return 'grid-cols-1 md:grid-cols-2 grid-rows-1';
      case 4:
        return 'grid-cols-1 md:grid-cols-2 grid-rows-2';
      default:
        return 'grid-cols-1';
    }
  };

  // Determine which timeframes to show based on layout
  const visibleTimeframes = timeframes.slice(0, layout);

  // No timeframes to display
  if (visibleTimeframes.length === 0) {
    return (
      <div className={`flex items-center justify-center p-8 bg-[#1e222d] rounded-lg ${className}`}>
        <p className="text-gray-400">No timeframes selected</p>
      </div>
    );
  }

  return (
    <div className={`grid gap-4 ${getLayoutClasses()} ${className}`}>
      {visibleTimeframes.map((tf) => {
        const data = chartData[tf] || [];
        const levels = htfLevels[tf] || [];

        return (
          <SynchronizedChart
            key={tf}
            timeframe={tf}
            symbol={symbol}
            data={data}
            htfLevels={levels}
            showHTFLevels={showHTFLevels}
            syncEnabled={syncEnabled}
            onChartReady={(chart, series) => {
              if (onChartReady) {
                onChartReady(tf, chart, series);
              }
            }}
          />
        );
      })}
    </div>
  );
};

export default TimeframeChartGrid;

