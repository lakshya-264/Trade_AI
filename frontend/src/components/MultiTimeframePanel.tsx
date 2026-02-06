/**
 * Multi-Timeframe Comparison Panel
 * Shows multiple timeframes side-by-side for comprehensive analysis
 */

import React, { useState, useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import candleDataApi from '../services/candleDataApi';
import { deduplicateAndSortCandlestickData } from '../utils/chartDataUtils';
import {
  ArrowsPointingOutIcon,
  XMarkIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface MultiTimeframePanelProps {
  symbol: string;
  mainTimeframe: string;
  onClose: () => void;
}

interface TimeframeConfig {
  value: string;
  label: string;
  interval: string;
  range: string;
}

const MultiTimeframePanel: React.FC<MultiTimeframePanelProps> = ({
  symbol,
  mainTimeframe,
  onClose
}) => {
  const [timeframes, setTimeframes] = useState<string[]>(['1D', '1W', '1M']);
  const [charts, setCharts] = useState<Map<string, { chart: IChartApi; series: ISeriesApi<'Candlestick'>; container: HTMLDivElement }>>(new Map());
  const [loading, setLoading] = useState<Map<string, boolean>>(new Map());
  const containerRefs = useRef<Map<string, React.RefObject<HTMLDivElement>>>(new Map());
  
  // Helper to get or create ref
  const getContainerRef = (tf: string): React.RefObject<HTMLDivElement> => {
    if (!containerRefs.current.has(tf)) {
      containerRefs.current.set(tf, React.createRef<HTMLDivElement>());
    }
    return containerRefs.current.get(tf)!;
  };

  const timeframeConfigs: Record<string, TimeframeConfig> = {
    '1m': { value: '1m', label: '1 Min', interval: '1m', range: '1d' },
    '5m': { value: '5m', label: '5 Min', interval: '5m', range: '5d' },
    '15m': { value: '15m', label: '15 Min', interval: '15m', range: '5d' },
    '1H': { value: '1H', label: '1 Hour', interval: '1h', range: '1mo' },
    '4H': { value: '4H', label: '4 Hour', interval: '4h', range: '3mo' },
    '1D': { value: '1D', label: '1 Day', interval: '1d', range: '1y' },
    '1W': { value: '1W', label: '1 Week', interval: '1wk', range: '2y' },
    '1M': { value: '1M', label: '1 Month', interval: '1mo', range: '5y' }
  };

  // Initialize chart containers - refs are created on-demand

  // Load data and create charts
  useEffect(() => {
    const loadCharts = async () => {
      for (const tf of timeframes) {
        const config = timeframeConfigs[tf];
        if (!config) continue;

        const containerRef = getContainerRef(tf);
        if (!containerRef?.current) continue;

        setLoading(prev => new Map(prev).set(tf, true));

        try {
          const response = await candleDataApi.getCandles(symbol, config.interval, config.range);
          
          if (response.success && response.data.length > 0) {
            let candles = response.data
              .map(c => ({
                time: c.time as Time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close
              }))
              .sort((a, b) => (a.time as number) - (b.time as number));
            
            // Remove duplicates by time
            candles = deduplicateAndSortCandlestickData(candles, false);

            // Create chart if doesn't exist
            if (!charts.has(tf)) {
              const chart = createChart(containerRef.current, {
                width: containerRef.current.clientWidth,
                height: 200,
                layout: {
                  background: { color: '#131722' },
                  textColor: '#d1d4dc'
                },
                grid: {
                  vertLines: { color: '#1e222d' },
                  horzLines: { color: '#1e222d' }
                },
                timeScale: {
                  borderColor: '#2a2e39',
                  timeVisible: true
                }
              });

              const series = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350'
              });

              setCharts(prev => {
                const newMap = new Map(prev);
                newMap.set(tf, { chart, series, container: containerRef.current! });
                return newMap;
              });

              series.setData(candles as CandlestickData[]);
              chart.timeScale().fitContent();
            } else {
              const chartData = charts.get(tf);
              if (chartData) {
                chartData.series.setData(candles as CandlestickData[]);
                chartData.chart.timeScale().fitContent();
              }
            }
          }
        } catch (error) {
          console.error(`Error loading ${tf} data:`, error);
        } finally {
          setLoading(prev => {
            const newMap = new Map(prev);
            newMap.set(tf, false);
            return newMap;
          });
        }
      }
    };

    loadCharts();
  }, [symbol, timeframes]);

  // Cleanup charts
  useEffect(() => {
    return () => {
      charts.forEach(({ chart }) => {
        try {
          chart.remove();
        } catch (e) {
          // Ignore
        }
      });
    };
  }, []);

  const addTimeframe = (tf: string) => {
    if (!timeframes.includes(tf)) {
      setTimeframes([...timeframes, tf]);
    }
  };

  const removeTimeframe = (tf: string) => {
    const chartData = charts.get(tf);
    if (chartData) {
      try {
        chartData.chart.remove();
      } catch (e) {
        // Ignore
      }
      setCharts(prev => {
        const newMap = new Map(prev);
        newMap.delete(tf);
        return newMap;
      });
    }
    setTimeframes(timeframes.filter(t => t !== tf));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl w-[90vw] h-[85vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-[#2a2e39] flex items-center justify-between">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <ArrowsPointingOutIcon className="w-6 h-6 text-blue-400" />
            Multi-Timeframe Analysis - {symbol}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Timeframe Selector */}
        <div className="p-4 border-b border-[#2a2e39] bg-[#131722]">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-gray-400">Add Timeframe:</span>
            {Object.values(timeframeConfigs).map(config => (
              <button
                key={config.value}
                onClick={() => addTimeframe(config.value)}
                disabled={timeframes.includes(config.value)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  timeframes.includes(config.value)
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
                }`}
              >
                {config.label}
              </button>
            ))}
          </div>
        </div>

        {/* Charts Grid */}
        <div className="flex-1 overflow-y-auto p-4 grid grid-cols-1 gap-4">
            {timeframes.map(tf => {
            const config = timeframeConfigs[tf];
            const isLoading = loading.get(tf);
            const containerRef = getContainerRef(tf);

            return (
              <div
                key={tf}
                className="bg-[#131722] border border-[#2a2e39] rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-white">
                    {config?.label || tf} Timeframe
                  </h4>
                  <div className="flex items-center gap-2">
                    {isLoading && (
                      <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
                    )}
                    <button
                      onClick={() => removeTimeframe(tf)}
                      className="text-red-400 hover:text-red-300"
                      title="Remove"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div
                  ref={containerRef}
                  className="w-full h-[200px]"
                />
              </div>
            );
          })}
        </div>

        {/* Summary */}
        <div className="p-4 border-t border-[#2a2e39] bg-[#131722]">
          <div className="text-xs text-gray-400">
            Comparing {timeframes.length} timeframes. Higher timeframes show broader trends.
          </div>
        </div>
      </div>
    </div>
  );
};

export default MultiTimeframePanel;

