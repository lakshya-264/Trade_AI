/**
 * Fibonacci Retracement Overlay Component
 * Draws Fibonacci retracement levels directly on the chart using lightweight-charts price lines
 */

import React, { useState, useEffect, useRef } from 'react';
import { IChartApi, ISeriesApi, Time } from 'lightweight-charts';
import {
  SparklesIcon,
  XMarkIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

interface FibonacciLevel {
  ratio: number;
  price: number;
  label: string;
  color: string;
}

interface FibonacciDrawing {
  id: string;
  highPrice: number;
  lowPrice: number;
  highTime: Time;
  lowTime: Time;
  levels: FibonacciLevel[];
  priceLines: any[];
  visible: boolean;
  color: string;
}

interface FibonacciOverlayProps {
  chartApi: IChartApi | null;
  candlestickSeries: ISeriesApi<'Candlestick'> | null;
  candles: Array<{
    time: Time;
    open: number;
    high: number;
    low: number;
    close: number;
  }>;
  symbol: string;
  visible?: boolean;
}

const FibonacciOverlay: React.FC<FibonacciOverlayProps> = ({
  chartApi,
  candlestickSeries,
  candles,
  symbol,
  visible = true
}) => {
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawings, setDrawings] = useState<FibonacciDrawing[]>([]);
  const [startPoint, setStartPoint] = useState<{ price: number; time: Time } | null>(null);
  const [endPoint, setEndPoint] = useState<{ price: number; time: Time } | null>(null);
  const [showPanel, setShowPanel] = useState(false);
  const [selectedDrawing, setSelectedDrawing] = useState<string | null>(null);
  const priceLinesRef = useRef<Map<string, any[]>>(new Map());

  // Fibonacci ratios
  const fibonacciRatios = [
    { ratio: 0, label: '0%', color: '#3B82F6', significance: 'high' },
    { ratio: 0.236, label: '23.6%', color: '#8B5CF6', significance: 'medium' },
    { ratio: 0.382, label: '38.2%', color: '#A855F7', significance: 'high' },
    { ratio: 0.5, label: '50%', color: '#EC4899', significance: 'high' },
    { ratio: 0.618, label: '61.8%', color: '#EF4444', significance: 'high' },
    { ratio: 0.786, label: '78.6%', color: '#F59E0B', significance: 'medium' },
    { ratio: 1, label: '100%', color: '#10B981', significance: 'high' },
    { ratio: 1.272, label: '127.2%', color: '#06B6D4', significance: 'low' },
    { ratio: 1.618, label: '161.8%', color: '#84CC16', significance: 'medium' },
    { ratio: 2.618, label: '261.8%', color: '#6366F1', significance: 'low' }
  ];

  // Calculate Fibonacci levels
  const calculateFibonacciLevels = (high: number, low: number): FibonacciLevel[] => {
    const diff = high - low;
    const isUptrend = high > low;
    
    return fibonacciRatios.map(({ ratio, label, color, significance }) => {
      let price: number;
      if (isUptrend) {
        // Retracement from high to low
        price = high - (diff * ratio);
      } else {
        // Retracement from low to high
        price = low + (diff * ratio);
      }
      
      return {
        ratio,
        price,
        label,
        color: significance === 'high' ? color : `${color}80` // Dimmed for less significant levels
      };
    });
  };

  // Draw Fibonacci levels on chart
  const drawFibonacci = (drawing: FibonacciDrawing) => {
    if (!candlestickSeries) return;

    // Remove existing price lines for this drawing
    const existingLines = priceLinesRef.current.get(drawing.id) || [];
    existingLines.forEach(line => candlestickSeries.removePriceLine(line));
    priceLinesRef.current.delete(drawing.id);

    if (!drawing.visible) return;

    const newLines: any[] = [];
    
    drawing.levels.forEach((level, index) => {
      // Only show key levels (0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%)
      const showLevel = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1].includes(level.ratio);
      
      if (showLevel) {
        const priceLine = candlestickSeries.createPriceLine({
          price: level.price,
          color: level.color,
          lineWidth: level.ratio === 0.618 || level.ratio === 0.382 ? 2 : 1,
          lineStyle: level.ratio === 0.618 || level.ratio === 0.382 ? 0 : 2, // Solid for key levels
          axisLabelVisible: true,
          title: `${level.label} (₹${level.price.toFixed(2)})`
        });
        
        newLines.push(priceLine);
      }
    });

    priceLinesRef.current.set(drawing.id, newLines);
  };

  // Handle mouse down - start drawing
  const handleMouseDown = (e: MouseEvent) => {
    if (!isDrawing || !candlestickSeries || !chartApi) return;
    
    const rect = chartApi.chartElement().getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    try {
      const price = candlestickSeries.coordinateToPrice(y);
      const time = chartApi.timeScale().coordinateToTime(x);
      
      if (price !== null && time !== null) {
        if (!startPoint) {
          setStartPoint({ price: price as number, time: time as Time });
        } else if (!endPoint) {
          setEndPoint({ price: price as number, time: time as Time });
          completeFibonacci();
        }
      }
    } catch (error) {
      console.debug('Error getting price/time from coordinates:', error);
    }
  };

  // Complete Fibonacci drawing
  const completeFibonacci = () => {
    if (!startPoint || !endPoint || !candlestickSeries) return;

    const highPrice = Math.max(startPoint.price, endPoint.price);
    const lowPrice = Math.min(startPoint.price, endPoint.price);
    const highTime = startPoint.price > endPoint.price ? startPoint.time : endPoint.time;
    const lowTime = startPoint.price < endPoint.price ? startPoint.time : endPoint.time;

    const levels = calculateFibonacciLevels(highPrice, lowPrice);
    
    const newDrawing: FibonacciDrawing = {
      id: `fib_${Date.now()}_${Math.random()}`,
      highPrice,
      lowPrice,
      highTime,
      lowTime,
      levels,
      priceLines: [],
      visible: true,
      color: '#8B5CF6'
    };

    setDrawings([...drawings, newDrawing]);
    drawFibonacci(newDrawing);
    
    setIsDrawing(false);
    setStartPoint(null);
    setEndPoint(null);
  };

  // Enable drawing mode
  const startDrawing = () => {
    setIsDrawing(true);
    setStartPoint(null);
    setEndPoint(null);
  };

  // Delete drawing
  const deleteDrawing = (id: string) => {
    const existingLines = priceLinesRef.current.get(id) || [];
    existingLines.forEach(line => candlestickSeries?.removePriceLine(line));
    priceLinesRef.current.delete(id);
    setDrawings(drawings.filter(d => d.id !== id));
  };

  // Toggle visibility
  const toggleVisibility = (id: string) => {
    const drawing = drawings.find(d => d.id === id);
    if (drawing) {
      drawing.visible = !drawing.visible;
      setDrawings([...drawings]);
      drawFibonacci(drawing);
    }
  };

  // Auto-detect swing high/low
  const autoDetectFibonacci = () => {
    if (!candles || candles.length < 20) return;

    // Find recent swing high and low
    let swingHigh = { price: candles[0].high, time: candles[0].time, index: 0 };
    let swingLow = { price: candles[0].low, time: candles[0].time, index: 0 };

    // Look for swing points in last 50 candles
    const lookback = Math.min(50, candles.length);
    const recentCandles = candles.slice(-lookback);

    for (let i = 5; i < recentCandles.length - 5; i++) {
      const candle = recentCandles[i];
      
      // Check for swing high
      if (candle.high > swingHigh.price) {
        let isSwingHigh = true;
        for (let j = i - 5; j <= i + 5; j++) {
          if (j !== i && recentCandles[j].high >= candle.high) {
            isSwingHigh = false;
            break;
          }
        }
        if (isSwingHigh) {
          swingHigh = { price: candle.high, time: candle.time, index: i };
        }
      }

      // Check for swing low
      if (candle.low < swingLow.price) {
        let isSwingLow = true;
        for (let j = i - 5; j <= i + 5; j++) {
          if (j !== i && recentCandles[j].low <= candle.low) {
            isSwingLow = false;
            break;
          }
        }
        if (isSwingLow) {
          swingLow = { price: candle.low, time: candle.time, index: i };
        }
      }
    }

    // Create Fibonacci from swing high to swing low
    if (swingHigh.price > swingLow.price) {
      const levels = calculateFibonacciLevels(swingHigh.price, swingLow.price);
      const newDrawing: FibonacciDrawing = {
        id: `fib_auto_${Date.now()}`,
        highPrice: swingHigh.price,
        lowPrice: swingLow.price,
        highTime: swingHigh.time,
        lowTime: swingLow.time,
        levels,
        priceLines: [],
        visible: true,
        color: '#8B5CF6'
      };

      setDrawings([...drawings, newDrawing]);
      drawFibonacci(newDrawing);
    }
  };

  // Redraw all Fibonacci levels when drawings change
  useEffect(() => {
    if (!candlestickSeries) return;
    
    drawings.forEach(drawing => {
      drawFibonacci(drawing);
    });
  }, [drawings, candlestickSeries]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      priceLinesRef.current.forEach((lines) => {
        lines.forEach(line => candlestickSeries?.removePriceLine(line));
      });
      priceLinesRef.current.clear();
    };
  }, []);

  if (!visible || !chartApi || !candlestickSeries) return null;

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-20 right-4 z-50">
        <button
          onClick={() => setShowPanel(!showPanel)}
          className="bg-purple-600 hover:bg-purple-700 text-white p-3 rounded-full shadow-lg flex items-center gap-2"
          title="Fibonacci Tools"
        >
          <SparklesIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Control Panel */}
      {showPanel && (
        <div className="fixed bottom-20 right-4 w-80 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl z-50 max-h-[60vh] overflow-hidden flex flex-col">
          <div className="p-4 border-b border-[#2a2e39] flex items-center justify-between bg-[#131722]">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-purple-400" />
              Fibonacci Retracements
            </h3>
            <button
              onClick={() => setShowPanel(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={startDrawing}
                className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
                  isDrawing
                    ? 'bg-purple-600 text-white'
                    : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
                }`}
              >
                {isDrawing ? 'Click 2 Points' : 'Draw Manual'}
              </button>
              <button
                onClick={autoDetectFibonacci}
                className="px-3 py-2 rounded text-sm font-medium bg-[#2a2e39] text-gray-300 hover:bg-[#363a45] transition-colors"
              >
                Auto Detect
              </button>
            </div>

            {/* Instructions */}
            {isDrawing && (
              <div className="bg-blue-500/20 border border-blue-500/50 rounded p-2 text-xs text-blue-300">
                {!startPoint
                  ? 'Click on chart to set first point (swing high/low)'
                  : 'Click on chart to set second point'}
              </div>
            )}

            {/* Drawings List */}
            {drawings.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-white">Active Drawings ({drawings.length})</h4>
                {drawings.map((drawing) => (
                  <div
                    key={drawing.id}
                    className={`bg-[#131722] p-3 rounded border ${
                      selectedDrawing === drawing.id
                        ? 'border-purple-500'
                        : 'border-[#2a2e39]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs text-gray-400">
                        High: ₹{drawing.highPrice.toFixed(2)} → Low: ₹{drawing.lowPrice.toFixed(2)}
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => toggleVisibility(drawing.id)}
                          className="text-gray-400 hover:text-white"
                          title={drawing.visible ? 'Hide' : 'Show'}
                        >
                          {drawing.visible ? (
                            <EyeIcon className="w-4 h-4" />
                          ) : (
                            <EyeSlashIcon className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => deleteDrawing(drawing.id)}
                          className="text-red-400 hover:text-red-300"
                          title="Delete"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    
                    {/* Key Levels */}
                    <div className="grid grid-cols-3 gap-1 text-xs">
                      {drawing.levels
                        .filter(l => [0.382, 0.5, 0.618].includes(l.ratio))
                        .map(level => (
                          <div
                            key={level.ratio}
                            className="text-center p-1 rounded"
                            style={{ backgroundColor: `${level.color}20`, color: level.color }}
                          >
                            {level.label}
                            <div className="text-[10px]">₹{level.price.toFixed(2)}</div>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {drawings.length === 0 && (
              <div className="text-center text-gray-400 text-sm py-8">
                No Fibonacci drawings yet.
                <br />
                Click "Draw Manual" or "Auto Detect" to start.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mouse event handler */}
      {isDrawing && chartApi && (
        <MouseEventHandler
          chartElement={chartApi.chartElement()}
          onMouseDown={handleMouseDown}
        />
      )}
    </>
  );
};

// Mouse event handler component
const MouseEventHandler: React.FC<{
  chartElement: HTMLElement;
  onMouseDown: (e: MouseEvent) => void;
}> = ({ chartElement, onMouseDown }) => {
  useEffect(() => {
    chartElement.addEventListener('mousedown', onMouseDown);
    return () => {
      chartElement.removeEventListener('mousedown', onMouseDown);
    };
  }, [chartElement, onMouseDown]);

  return null;
};

export default FibonacciOverlay;

