/**
 * Synchronized Chart Component
 * Individual chart that participates in multi-chart synchronization
 */

import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, Time, CandlestickData } from 'lightweight-charts';
import { CandleData } from '../services/multiTimeframeApi';
import { chartSyncService } from '../services/chartSyncService';
import { htfLevelService, HTFLevel } from '../services/htfLevelService';
import { deduplicateAndSortCandlestickData } from '../utils/chartDataUtils';

interface SynchronizedChartProps {
  timeframe: string;
  symbol: string;
  data: CandleData[];
  htfLevels?: HTFLevel[];
  showHTFLevels?: boolean;
  syncEnabled?: boolean;
  onChartReady?: (chart: IChartApi, series: ISeriesApi<'Candlestick'>) => void;
  className?: string;
}

export const SynchronizedChart: React.FC<SynchronizedChartProps> = ({
  timeframe,
  symbol,
  data,
  htfLevels = [],
  showHTFLevels = true,
  syncEnabled = true,
  onChartReady,
  className = '',
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const [tooltipData, setTooltipData] = useState<any>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const chartId = `chart-${timeframe}-${symbol}`;

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart instance
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#1e222d' },
        horzLines: { color: '#1e222d' },
      },
      timeScale: {
        borderColor: '#2a2e39',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#2a2e39',
      },
      crosshair: {
        mode: 0, // Normal crosshair
        vertLine: {
          color: '#758696',
          width: 1,
          style: 3,
          labelBackgroundColor: '#2962FF',
        },
        horzLine: {
          color: '#758696',
          width: 1,
          style: 3,
          labelBackgroundColor: '#2962FF',
        },
      },
    });

    // Add candlestick series
    const series = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    chartRef.current = chart;
    seriesRef.current = series;

    // Register with sync service
    if (syncEnabled) {
      chartSyncService.registerChart(chartId, chart, (time, price) => {
        if (time) {
          setTooltipVisible(true);
          // Find data point at this time
          const dataPoint = data.find((d) => d.time === time);
          if (dataPoint) {
            setTooltipData({
              ...dataPoint,
              time, // Override with synced time
              syncedPrice: price, // Add synced price separately
            });
          }
        } else {
          setTooltipVisible(false);
        }
      });
    }

    // Notify parent
    if (onChartReady) {
      onChartReady(chart, series);
    }

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        try {
          chartRef.current.applyOptions({
            width: chartContainerRef.current.clientWidth,
          });
        } catch (error) {
          console.debug('Error resizing chart:', error);
        }
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (syncEnabled) {
        try {
          chartSyncService.unregisterChart(chartId);
        } catch (error) {
          console.debug('Error unregistering chart:', error);
        }
      }
      if (chartRef.current) {
        try {
          chartRef.current.remove();
        } catch (error) {
          console.debug('Error removing chart:', error);
        }
      }
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  // Update data
  useEffect(() => {
    if (!seriesRef.current || !data || data.length === 0 || !chartRef.current) return;

    try {
      // Convert data to lightweight-charts format
      let chartData: CandlestickData<Time>[] = data.map((candle) => ({
        time: candle.time as Time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      }));

      // Deduplicate and sort
      chartData = deduplicateAndSortCandlestickData(chartData, false);

      if (seriesRef.current && chartRef.current) {
        try {
          seriesRef.current.setData(chartData);
        } catch (error) {
          console.debug('Error setting synchronized chart data:', error);
        }
      }

      // Fit content
      if (chartRef.current) {
        try {
          chartRef.current.timeScale().fitContent();
        } catch (error) {
          console.debug('Error fitting content:', error);
        }
      }
    } catch (error) {
      console.error('[SynchronizedChart] Error setting data:', error);
    }
  }, [data]);

  // Update HTF levels
  useEffect(() => {
    if (!chartRef.current || !seriesRef.current) return;

    if (showHTFLevels && htfLevels.length > 0) {
      htfLevelService.drawHTFLevels(chartRef.current, seriesRef.current, htfLevels, {
        showLabels: true,
        opacity: 0.6,
        lineWidth: 2,
      });
    } else {
      htfLevelService.clearHTFLevels(chartRef.current);
    }
  }, [htfLevels, showHTFLevels]);

  return (
    <div className={`relative bg-[#131722] rounded-lg overflow-hidden ${className}`}>
      {/* Timeframe Header */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-[#1e222d] to-transparent px-4 py-2">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">{timeframe}</h3>
            <p className="text-xs text-gray-400">{symbol}</p>
          </div>
          {syncEnabled && (
            <div className="flex items-center gap-1 text-xs text-blue-400">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Synced</span>
            </div>
          )}
        </div>
      </div>

      {/* Chart Container */}
      <div ref={chartContainerRef} className="w-full" />

      {/* Tooltip */}
      {tooltipVisible && tooltipData && (
        <div className="absolute top-16 left-4 bg-[#1e222d] border border-[#2a2e39] rounded-lg p-3 shadow-lg z-20">
          <div className="text-xs space-y-1">
            <div className="text-gray-400">
              {new Date(tooltipData.time).toLocaleString()}
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              <span className="text-gray-400">O:</span>
              <span className="text-white font-mono">₹{tooltipData.open?.toFixed(2)}</span>
              <span className="text-gray-400">H:</span>
              <span className="text-green-400 font-mono">₹{tooltipData.high?.toFixed(2)}</span>
              <span className="text-gray-400">L:</span>
              <span className="text-red-400 font-mono">₹{tooltipData.low?.toFixed(2)}</span>
              <span className="text-gray-400">C:</span>
              <span className="text-white font-mono">₹{tooltipData.close?.toFixed(2)}</span>
              <span className="text-gray-400">V:</span>
              <span className="text-blue-400 font-mono">
                {tooltipData.volume?.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {(!data || data.length === 0) && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#131722]/80">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="text-sm text-gray-400">Loading {timeframe} data...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SynchronizedChart;

