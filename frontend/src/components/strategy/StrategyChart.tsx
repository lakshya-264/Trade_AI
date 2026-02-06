/**
 * Strategy Chart Component
 * Shows strategy price over time vs underlying price
 */

import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp } from 'lucide-react';
import { StrategyLeg } from './StrategyBuilder';

interface StrategyChartProps {
  legs: StrategyLeg[];
  currentPrice: number;
  symbol: string;
  invertPrice: boolean;
  onToggleInvert: () => void;
}

const StrategyChart: React.FC<StrategyChartProps> = ({
  legs,
  currentPrice,
  symbol,
  invertPrice,
  onToggleInvert
}) => {
  const chartData = useMemo(() => {
    if (legs.length === 0) return [];

    // Generate time series data (last 30 days)
    const data = [];
    const today = new Date();
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      // Simulate underlying price movement (random walk)
      const priceChange = (Math.random() - 0.5) * 200;
      const underlyingPrice = currentPrice + priceChange;
      
      // Calculate strategy price at this underlying price
      let strategyPrice = 0;
      legs.forEach(leg => {
        const multiplier = leg.lotSize || 50;
        const totalQuantity = leg.quantity * multiplier;
        
        if (leg.instrument === 'CE') {
          const intrinsicValue = Math.max(0, underlyingPrice - leg.strike);
          if (leg.action === 'BUY') {
            strategyPrice += (intrinsicValue - leg.price) * totalQuantity;
          } else {
            strategyPrice += (leg.price - intrinsicValue) * totalQuantity;
          }
        } else if (leg.instrument === 'PE') {
          const intrinsicValue = Math.max(0, leg.strike - underlyingPrice);
          if (leg.action === 'BUY') {
            strategyPrice += (intrinsicValue - leg.price) * totalQuantity;
          } else {
            strategyPrice += (leg.price - intrinsicValue) * totalQuantity;
          }
        } else if (leg.instrument === 'FUT') {
          const pnl = underlyingPrice - leg.price;
          if (leg.action === 'BUY') {
            strategyPrice += pnl * totalQuantity;
          } else {
            strategyPrice -= pnl * totalQuantity;
          }
        }
      });
      
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
        strategyPrice: invertPrice ? -strategyPrice : strategyPrice,
        underlyingPrice: underlyingPrice
      });
    }
    
    return data;
  }, [legs, currentPrice, invertPrice]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-300 rounded p-3 shadow-lg">
          <p className="text-gray-600 mb-1">{payload[0].payload.date}</p>
          <p className="text-blue-600 font-semibold">
            Strategy Price: ₹{payload[0].value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-gray-600">
            {symbol} FUT: ₹{payload[1]?.value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
          </p>
        </div>
      );
    }
    return null;
  };

  if (legs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <div className="text-center">
          <TrendingUp className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg mb-2">No strategy legs added</p>
          <p className="text-sm">Add legs to see strategy chart</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Strategy Price Over Time</h3>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={invertPrice}
            onChange={onToggleInvert}
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-700">Invert Price</span>
        </label>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <ResponsiveContainer width="100%" height={500}>
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              stroke="#6b7280"
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              yAxisId="left"
              stroke="#3b82f6"
              label={{ value: 'Strategy Price', angle: -90, position: 'insideLeft', fill: '#3b82f6' }}
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              stroke="#6b7280"
              label={{ value: 'Future Price', angle: 90, position: 'insideRight', fill: '#6b7280' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="strategyPrice"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="Strategy Price"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="underlyingPrice"
              stroke="#6b7280"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name={`${symbol} Dec FUT`}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default StrategyChart;

