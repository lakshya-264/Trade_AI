/**
 * Unified AI Chart Component
 * Integrates Lightweight Charts for Unified AI analysis visualization
 */

import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import candleDataApi from '../services/candleDataApi';
import { deduplicateAndSortCandlestickData } from '../utils/chartDataUtils';
import ChartDrawingTools from './ChartDrawingTools';
import PatternVisualization from './PatternVisualization';

interface UnifiedAIChartProps {
  symbol: string;
  timeframe?: string;
  height?: number;
  showDrawingTools?: boolean;
  showPatternVisualization?: boolean;
}

const UnifiedAIChart: React.FC<UnifiedAIChartProps> = ({
  symbol,
  timeframe = '1D',
  height = 400,
  showDrawingTools = true,
  showPatternVisualization = true
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Initialize chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: '#131722' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2a2e39' },
        horzLines: { color: '#2a2e39' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2a2e39',
      },
      timeScale: {
        borderColor: '#2a2e39',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Load chart data
    loadChartData();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        try {
          // Check if chart container still exists before removing
          if (chartContainerRef.current) {
            chartRef.current.remove();
          }
        } catch (error) {
          // Chart might already be disposed, ignore the error
          console.debug('Chart already disposed:', error);
        }
      }
      chartRef.current = null;
      candlestickSeriesRef.current = null;
    };
  }, [symbol, timeframe, height]);

  const loadChartData = async () => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      // Map timeframe to interval and range
      const intervalMap: Record<string, string> = {
        '1h': '1h',
        '4h': '4h',
        '1D': '1d',
        '1W': '1wk',
        '1M': '1mo'
      };
      const interval = intervalMap[timeframe] || '1d';
      const range = '3mo'; // Default range
      
      const data = await candleDataApi.getCandles(symbol, interval, range);
      
      if (data && data.data && candlestickSeriesRef.current && chartRef.current) {
        let formattedData: CandlestickData[] = data.data.map((candle: any) => ({
          time: (candle.time as number) as Time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        }));

        // Deduplicate and sort data
        const uniqueData = deduplicateAndSortCandlestickData(formattedData, false);
        
        try {
          candlestickSeriesRef.current.setData(uniqueData);
          
          // Fit content
          try {
            chartRef.current.timeScale().fitContent();
          } catch (error) {
            console.debug('Error fitting content:', error);
          }
        } catch (error) {
          console.debug('Error setting chart data:', error);
        }
      }
    } catch (err: any) {
      console.error('Error loading chart data:', err);
      setError(err.message || 'Failed to load chart data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative w-full bg-[#131722] rounded-lg border border-[#2a2e39]">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-[#2a2e39]">
        <div className="flex items-center gap-2">
          <span className="text-white font-semibold">{symbol}</span>
          <span className="text-gray-400 text-sm">{timeframe}</span>
        </div>
        <button
          onClick={loadChartData}
          disabled={loading}
          className="px-2 py-1 text-xs bg-[#2a2e39] hover:bg-[#363a45] text-gray-300 rounded disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Chart Container */}
      <div className="relative" style={{ height: `${height}px` }}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#131722]/50 z-10">
            <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#131722]/50 z-10">
            <div className="text-red-400 text-sm">{error}</div>
          </div>
        )}

        <div ref={chartContainerRef} className="w-full h-full" />

        {/* Drawing Tools */}
        {showDrawingTools && chartRef.current && (
          <div className="absolute top-2 left-2 z-20">
            <ChartDrawingTools
              chartContainerRef={chartContainerRef}
              onDrawingComplete={(drawing) => {
                console.log('Drawing completed:', drawing);
              }}
            />
          </div>
        )}

        {/* Pattern Visualization */}
        {showPatternVisualization && chartRef.current && candlestickSeriesRef.current && (
          <PatternVisualization
            symbol={symbol}
            timeframe={timeframe}
            chartApi={chartRef.current}
            candlestickSeries={candlestickSeriesRef.current}
            visible={showPatternVisualization}
          />
        )}
      </div>
    </div>
  );
};

export default UnifiedAIChart;

