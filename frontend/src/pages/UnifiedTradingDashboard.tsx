/**
 * Unified Trading Dashboard
 * Combines Comprehensive Trading Pro charting with Unified AI insights
 */

import React, { useState, useRef, useEffect } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import comprehensiveTradingApi from '../services/comprehensiveTradingApi';
import unifiedAiApi from '../services/unifiedAiApi';
import candleDataApi from '../services/candleDataApi';
import { deduplicateAndSortCandlestickData } from '../utils/chartDataUtils';
import AIInsightsPanel from '../components/AIInsightsPanel';
import ChatWidget from '../components/ChatWidget';
import MarketOverviewPanel from '../components/MarketOverviewPanel';
import UnifiedAIWatchlist from '../components/UnifiedAIWatchlist';
import MultiTimeframeComparison from '../components/MultiTimeframeComparison';
import { toast } from 'react-hot-toast';

const UnifiedTradingDashboard: React.FC = () => {
  const [activeSymbol, setActiveSymbol] = useState('RELIANCE');
  const [timeframe, setTimeframe] = useState('1D');
  const [viewMode, setViewMode] = useState<'chart' | 'ai' | 'split'>('split');
  const [loading, setLoading] = useState(false);
  
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const [showChat, setShowChat] = useState(false);
  const [showWatchlist, setShowWatchlist] = useState(true);
  const [showMarketOverview, setShowMarketOverview] = useState(false);

  const timeframes = [
    { value: '1h', label: '1H' },
    { value: '4h', label: '4H' },
    { value: '1D', label: '1D' },
    { value: '1W', label: '1W' },
    { value: '1M', label: '1M' }
  ];

  useEffect(() => {
    if (chartContainerRef.current && viewMode !== 'ai') {
      initializeChart();
      loadChartData();
    }

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, [activeSymbol, timeframe, viewMode]);

  const initializeChart = () => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#131722' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2a2e39' },
        horzLines: { color: '#2a2e39' },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#2a2e39' },
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
  };

  const loadChartData = async () => {
    if (!activeSymbol) return;

    setLoading(true);
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
      
      const data = await candleDataApi.getCandles(activeSymbol, interval, range);
      
      if (data && data.data && candlestickSeriesRef.current) {
        let formattedData: CandlestickData[] = data.data.map((candle: any) => ({
          time: (candle.time as number) as Time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        }));

        // Deduplicate and sort data
        const uniqueData = deduplicateAndSortCandlestickData(formattedData, false);
        candlestickSeriesRef.current.setData(uniqueData);
        if (chartRef.current) {
          chartRef.current.timeScale().fitContent();
        }
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
      toast.error('Failed to load chart data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#131722] text-white">
      {/* Header */}
      <div className="bg-[#1e222d] border-b border-[#2a2e39] px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">Unified Trading Dashboard</h1>
            <input
              type="text"
              value={activeSymbol}
              onChange={(e) => setActiveSymbol(e.target.value.toUpperCase())}
              onKeyPress={(e) => e.key === 'Enter' && loadChartData()}
              className="px-3 py-1.5 bg-[#131722] rounded text-lg font-bold w-32 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Symbol"
            />
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="px-3 py-1.5 bg-[#2a2e39] rounded text-sm"
            >
              {timeframes.map((tf) => (
                <option key={tf.value} value={tf.value}>{tf.label}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('chart')}
              className={`px-3 py-1.5 rounded text-sm ${
                viewMode === 'chart' ? 'bg-blue-600' : 'bg-[#2a2e39]'
              }`}
            >
              Chart
            </button>
            <button
              onClick={() => setViewMode('ai')}
              className={`px-3 py-1.5 rounded text-sm ${
                viewMode === 'ai' ? 'bg-blue-600' : 'bg-[#2a2e39]'
              }`}
            >
              AI
            </button>
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1.5 rounded text-sm ${
                viewMode === 'split' ? 'bg-blue-600' : 'bg-[#2a2e39]'
              }`}
            >
              Split
            </button>
            <button
              onClick={() => setShowWatchlist(!showWatchlist)}
              className="px-3 py-1.5 bg-[#2a2e39] hover:bg-[#363a45] rounded text-sm"
            >
              Watchlist
            </button>
            <button
              onClick={() => setShowMarketOverview(!showMarketOverview)}
              className="px-3 py-1.5 bg-[#2a2e39] hover:bg-[#363a45] rounded text-sm"
            >
              Market
            </button>
            <button
              onClick={() => setShowChat(!showChat)}
              className="px-3 py-1.5 bg-[#2a2e39] hover:bg-[#363a45] rounded text-sm"
            >
              Chat
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Left Sidebar - Watchlist */}
        {showWatchlist && (
          <div className="w-80 border-r border-[#2a2e39]">
            <UnifiedAIWatchlist
              onSymbolSelect={(symbol) => {
                setActiveSymbol(symbol);
                loadChartData();
              }}
              selectedSymbol={activeSymbol}
            />
          </div>
        )}

        {/* Center - Chart/AI Content */}
        <div className="flex-1 flex flex-col">
          {viewMode === 'chart' || viewMode === 'split' ? (
            <div className="flex-1 p-4">
              <div ref={chartContainerRef} className="w-full h-full rounded-lg border border-[#2a2e39]" />
            </div>
          ) : null}

          {viewMode === 'ai' || viewMode === 'split' ? (
            <div className="flex-1 p-4 overflow-y-auto">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <AIInsightsPanel symbol={activeSymbol} timeframe={timeframe} />
                <MultiTimeframeComparison symbol={activeSymbol} />
              </div>
            </div>
          ) : null}
        </div>

        {/* Right Sidebar - Market Overview */}
        {showMarketOverview && (
          <div className="w-80 border-l border-[#2a2e39]">
            <MarketOverviewPanel symbol={activeSymbol} />
          </div>
        )}
      </div>

      {/* Chat Widget */}
      {showChat && (
        <ChatWidget
          symbol={activeSymbol}
          timeframe={timeframe}
          chartContext={{
            currentPrice: undefined,
            chartData: null
          }}
          onClose={() => setShowChat(false)}
        />
      )}
    </div>
  );
};

export default UnifiedTradingDashboard;

