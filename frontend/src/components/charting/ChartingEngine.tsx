import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time, UTCTimestamp } from 'lightweight-charts';
import { 
  ChartBarIcon, 
  Cog6ToothIcon, 
  PlusIcon, 
  XMarkIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon
} from '@heroicons/react/24/outline';

// Types
export interface ChartLayout {
  id: string;
  name: string;
  charts: ChartConfig[];
  isFullscreen: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface ChartConfig {
  id: string;
  symbol: string;
  interval: string;
  timeframe: string;
  indicators: IndicatorConfig[];
  drawings: DrawingConfig[];
  layout: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface IndicatorConfig {
  id: string;
  type: string;
  parameters: Record<string, any>;
  visible: boolean;
  color?: string;
}

export interface DrawingConfig {
  id: string;
  type: string;
  points: Array<{ time: Time; price: number }>;
  style: Record<string, any>;
  visible: boolean;
}

export interface ChartingEngineProps {
  initialLayout?: ChartLayout;
  onLayoutChange?: (layout: ChartLayout) => void;
  className?: string;
}

// Charting Engine Component
const ChartingEngine: React.FC<ChartingEngineProps> = ({
  initialLayout,
  onLayoutChange,
  className = ''
}) => {
  const [currentLayout, setCurrentLayout] = useState<ChartLayout>(
    initialLayout || {
      id: 'default',
      name: 'Default Layout',
      charts: [],
      isFullscreen: false,
      createdAt: new Date(),
      updatedAt: new Date()
    }
  );

  const [activeChartId, setActiveChartId] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartsRef = useRef<Map<string, IChartApi>>(new Map());
  const seriesRef = useRef<Map<string, ISeriesApi<'Candlestick'>>>(new Map());

  // Initialize chart
  const createNewChart = useCallback((config: ChartConfig) => {
    if (!chartContainerRef.current) return;

    const container = document.createElement('div');
    container.id = `chart-${config.id}`;
    container.style.position = 'absolute';
    container.style.left = `${config.layout.x}px`;
    container.style.top = `${config.layout.y}px`;
    container.style.width = `${config.layout.width}px`;
    container.style.height = `${config.layout.height}px`;
    container.style.border = '1px solid #2a2a2a';
    container.style.borderRadius = '4px';

    chartContainerRef.current.appendChild(container);

    const chart = createChart(container, {
      width: config.layout.width,
      height: config.layout.height,
      layout: {
        background: { color: '#1e1e1e' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2a2a2a',
      },
      timeScale: {
        borderColor: '#2a2a2a',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    chartsRef.current.set(config.id, chart);
    seriesRef.current.set(config.id, candlestickSeries);

    // Load sample data
    loadChartData(config.id, config.symbol, config.interval);

    return chart;
  }, []);

  // Load chart data
  const loadChartData = useCallback(async (chartId: string, symbol: string, interval: string) => {
    try {
      // Mock data for now - replace with actual API call
      const mockData: CandlestickData[] = generateMockCandlestickData(100);
      
      const series = seriesRef.current.get(chartId);
      if (series) {
        series.setData(mockData);
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  }, []);

  // Generate mock candlestick data
  const generateMockCandlestickData = (count: number): CandlestickData[] => {
    const data: CandlestickData[] = [];
    let basePrice = 100;
    const now = Date.now();
    
    for (let i = 0; i < count; i++) {
      const time = (now - (count - i) * 24 * 60 * 60 * 1000) as UTCTimestamp;
      const open = basePrice + (Math.random() - 0.5) * 2;
      const close = open + (Math.random() - 0.5) * 4;
      const high = Math.max(open, close) + Math.random() * 2;
      const low = Math.min(open, close) - Math.random() * 2;
      
      data.push({
        time,
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
      });
      
      basePrice = close;
    }
    
    return data;
  };

  // Add new chart
  const addChart = useCallback(() => {
    const newChartConfig: ChartConfig = {
      id: `chart-${Date.now()}`,
      symbol: 'RELIANCE',
      interval: '1D',
      timeframe: '1D',
      indicators: [],
      drawings: [],
      layout: {
        x: 0,
        y: 0,
        width: 800,
        height: 400,
      },
    };

    const updatedLayout = {
      ...currentLayout,
      charts: [...currentLayout.charts, newChartConfig],
      updatedAt: new Date(),
    };

    setCurrentLayout(updatedLayout);
    onLayoutChange?.(updatedLayout);
    
    // Create the actual chart
    setTimeout(() => createNewChart(newChartConfig), 100);
  }, [currentLayout, onLayoutChange, createNewChart]);

  // Remove chart
  const removeChart = useCallback((chartId: string) => {
    const chart = chartsRef.current.get(chartId);
    if (chart) {
      chart.remove();
      chartsRef.current.delete(chartId);
      seriesRef.current.delete(chartId);
    }

    const updatedLayout = {
      ...currentLayout,
      charts: currentLayout.charts.filter(chart => chart.id !== chartId),
      updatedAt: new Date(),
    };

    setCurrentLayout(updatedLayout);
    onLayoutChange?.(updatedLayout);
  }, [currentLayout, onLayoutChange]);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  // Initialize charts on mount
  useEffect(() => {
    if (currentLayout.charts.length === 0) {
      addChart();
    } else {
      currentLayout.charts.forEach(chartConfig => {
        if (!chartsRef.current.has(chartConfig.id)) {
          createNewChart(chartConfig);
        }
      });
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      chartsRef.current.forEach(chart => chart.remove());
      chartsRef.current.clear();
      seriesRef.current.clear();
    };
  }, []);

  return (
    <div className={`charting-engine ${className} ${isFullscreen ? 'fullscreen' : ''}`}>
      {/* Toolbar */}
      <div className="charting-toolbar bg-gray-800 border-b border-gray-700 p-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={addChart}
            className="flex items-center space-x-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Add Chart</span>
          </button>
          
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center space-x-1 px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm"
          >
            <Cog6ToothIcon className="w-4 h-4" />
            <span>Settings</span>
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-300">
            Layout: {currentLayout.name}
          </span>
          
          <button
            onClick={toggleFullscreen}
            className="p-1 hover:bg-gray-700 rounded"
          >
            {isFullscreen ? (
              <ArrowsPointingInIcon className="w-5 h-5 text-gray-300" />
            ) : (
              <ArrowsPointingOutIcon className="w-5 h-5 text-gray-300" />
            )}
          </button>
        </div>
      </div>

      {/* Chart Container */}
      <div 
        ref={chartContainerRef}
        className="chart-container relative w-full h-full bg-gray-900"
        style={{ height: isFullscreen ? 'calc(100vh - 60px)' : '600px' }}
      >
        {/* Chart tabs */}
        {currentLayout.charts.length > 1 && (
          <div className="chart-tabs absolute top-2 left-2 z-10 flex space-x-1">
            {currentLayout.charts.map((chart) => (
              <div
                key={chart.id}
                className={`chart-tab px-3 py-1 rounded-t cursor-pointer text-sm ${
                  activeChartId === chart.id
                    ? 'bg-gray-800 text-white border-b-2 border-blue-500'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                onClick={() => setActiveChartId(chart.id)}
              >
                <span>{chart.symbol}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeChart(chart.id);
                  }}
                  className="ml-2 hover:text-red-400"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel absolute top-16 right-4 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-20">
          <div className="p-4">
            <h3 className="text-lg font-semibold text-white mb-4">Chart Settings</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Layout Name
                </label>
                <input
                  type="text"
                  value={currentLayout.name}
                  onChange={(e) => {
                    const updatedLayout = {
                      ...currentLayout,
                      name: e.target.value,
                      updatedAt: new Date(),
                    };
                    setCurrentLayout(updatedLayout);
                    onLayoutChange?.(updatedLayout);
                  }}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Charts ({currentLayout.charts.length})
                </label>
                <div className="space-y-2">
                  {currentLayout.charts.map((chart) => (
                    <div key={chart.id} className="flex items-center justify-between p-2 bg-gray-700 rounded">
                      <span className="text-sm text-gray-300">{chart.symbol}</span>
                      <button
                        onClick={() => removeChart(chart.id)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChartingEngine;
