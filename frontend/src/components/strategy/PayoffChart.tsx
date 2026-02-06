/**
 * Payoff Chart Component
 * Visualizes strategy payoff at different underlying prices
 * Draggable and resizable with mouse
 */

import React, { useMemo, useRef, useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { Move, Maximize2, Minimize2 } from 'lucide-react';
import { StrategyLeg, StrategyMetrics } from './StrategyBuilder';

interface PayoffChartProps {
  legs: StrategyLeg[];
  currentPrice: number;
  metrics: StrategyMetrics | null;
  symbol: string;
}

const PayoffChart: React.FC<PayoffChartProps> = ({ legs, currentPrice, metrics }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const chartRef = useRef<HTMLDivElement>(null);
  const chartData = useMemo(() => {
    if (legs.length === 0) return [];

    // Calculate payoff for a range of prices
    const minStrike = Math.min(...legs.map(l => l.strike));
    const maxStrike = Math.max(...legs.map(l => l.strike));
    const priceRange = maxStrike - minStrike;
    const startPrice = Math.max(0, minStrike - priceRange * 0.3);
    const endPrice = maxStrike + priceRange * 0.3;
    const step = (endPrice - startPrice) / 100;

    const data = [];
    for (let price = startPrice; price <= endPrice; price += step) {
      let totalPayoff = 0;

      legs.forEach(leg => {
        let legPayoff = 0;
        const multiplier = leg.lotSize || 50;
        const totalQuantity = leg.quantity * multiplier;

        if (leg.instrument === 'CE') {
          // Call option payoff
          const intrinsicValue = Math.max(0, price - leg.strike);
          if (leg.action === 'BUY') {
            legPayoff = (intrinsicValue - leg.price) * totalQuantity;
          } else {
            legPayoff = (leg.price - intrinsicValue) * totalQuantity;
          }
        } else if (leg.instrument === 'PE') {
          // Put option payoff
          const intrinsicValue = Math.max(0, leg.strike - price);
          if (leg.action === 'BUY') {
            legPayoff = (intrinsicValue - leg.price) * totalQuantity;
          } else {
            legPayoff = (leg.price - intrinsicValue) * totalQuantity;
          }
        } else if (leg.instrument === 'FUT') {
          // Future payoff
          const pnl = price - leg.price;
          if (leg.action === 'BUY') {
            legPayoff = pnl * totalQuantity;
          } else {
            legPayoff = -pnl * totalQuantity;
          }
        }

        totalPayoff += legPayoff;
      });

      data.push({
        price: Math.round(price),
        payoff: totalPayoff,
        payoffInLakhs: totalPayoff / 100000
      });
    }

    return data;
  }, [legs]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#2a2e39] border border-gray-600 rounded p-3 shadow-lg">
          <p className="text-white font-medium">Price: ₹{data.price}</p>
          <p className={`font-semibold ${data.payoff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            P&L: ₹{data.payoff.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-gray-400 text-sm">
            ({data.payoffInLakhs >= 0 ? '+' : ''}{data.payoffInLakhs.toFixed(2)}L)
          </p>
        </div>
      );
    }
    return null;
  };

  // Drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!isMaximized && e.target instanceof HTMLElement && e.target.closest('.chart-header')) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
      e.preventDefault();
    }
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging && !isMaximized) {
        setPosition({
          x: e.clientX - dragStart.x,
          y: e.clientY - dragStart.y
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart, isMaximized]);

  const handleMaximize = () => {
    setIsMaximized(!isMaximized);
    if (!isMaximized) {
      // Reset position when maximizing
      setPosition({ x: 0, y: 0 });
    }
  };

  return (
    <div
      ref={chartRef}
      className={`bg-[#1a1d28] rounded-lg border border-gray-700 transition-all duration-200 ${
        isMaximized ? 'fixed inset-4 z-50' : 'relative'
      }`}
      style={!isMaximized ? { transform: `translate(${position.x}px, ${position.y}px)` } : {}}
    >
      {/* Chart Header - Draggable */}
      <div
        className={`chart-header flex items-center justify-between p-4 border-b border-gray-700 ${
          isMaximized ? 'cursor-default' : 'cursor-move'
        } ${
          isDragging ? 'bg-[#2a2e39]' : 'bg-[#1a1d28]'
        }`}
        onMouseDown={handleMouseDown}
      >
        <div className="flex items-center gap-2">
          {!isMaximized && <Move className="w-4 h-4 text-gray-400" />}
          <h3 className="text-lg font-semibold">Payoff Chart</h3>
          {!isMaximized && (
            <span className="text-xs text-gray-500 ml-2">(Drag to move)</span>
          )}
        </div>
        <button
          onClick={handleMaximize}
          className="p-2 hover:bg-[#2a2e39] rounded transition-colors"
          title={isMaximized ? 'Minimize' : 'Maximize'}
        >
          {isMaximized ? (
            <Minimize2 className="w-4 h-4 text-gray-400" />
          ) : (
            <Maximize2 className="w-4 h-4 text-gray-400" />
          )}
        </button>
      </div>

      {/* Chart Content */}
      <div className={`p-4 ${isMaximized ? 'h-[calc(100vh-120px)]' : 'h-[500px]'}`}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
            <defs>
              <linearGradient id="payoffGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.3} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="price" 
              stroke="#9ca3af"
              label={{ value: 'Underlying Price', position: 'insideBottom', offset: -5, fill: '#9ca3af' }}
            />
            <YAxis 
              stroke="#9ca3af"
              label={{ value: 'Profit/Loss (₹)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
              tickFormatter={(value) => `${(value / 100000).toFixed(1)}L`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine 
              x={currentPrice} 
              stroke="#3b82f6" 
              strokeDasharray="5 5"
              label={{ value: 'Current Price', position: 'top', fill: '#3b82f6' }}
            />
            <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
            {metrics?.breakevenPoints && metrics.breakevenPoints.length > 0 && metrics.breakevenPoints.map((be, idx) => (
              <ReferenceLine
                key={idx}
                x={be}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{ value: `BE ${idx + 1}`, position: 'top', fill: '#f59e0b' }}
              />
            ))}
            <Area
              type="monotone"
              dataKey="payoff"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#payoffGradient)"
              fillOpacity={0.6}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Chart Info */}
      <div className="px-4 pb-4 space-y-2 text-sm">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500"></div>
            <span className="text-gray-400">Payoff Line</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 border border-blue-500 border-dashed"></div>
            <span className="text-gray-400">Current Price</span>
          </div>
          {metrics?.breakevenPoints && metrics.breakevenPoints.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 border border-yellow-500 border-dashed"></div>
              <span className="text-gray-400">Breakeven</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PayoffChart;

