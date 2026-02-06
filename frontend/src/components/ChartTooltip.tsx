/**
 * Chart Tooltip Component
 * Shows detailed information when hovering over chart elements
 */

import React from 'react';
import { cn } from '../lib/utils';

export interface TooltipData {
  type: 'bos' | 'choch' | 'support' | 'resistance' | 'demand' | 'supply' | 'trendline' | 'swing';
  title: string;
  price?: number;
  data: Record<string, any>;
  position: { x: number; y: number };
}

interface ChartTooltipProps {
  data: TooltipData | null;
  visible: boolean;
}

const ChartTooltip: React.FC<ChartTooltipProps> = ({ data, visible }) => {
  if (!visible || !data) return null;

  const getColorClass = () => {
    switch (data.type) {
      case 'bos':
        return 'border-green-500 bg-green-500/10';
      case 'choch':
        return 'border-purple-500 bg-purple-500/10';
      case 'support':
        return 'border-green-500 bg-green-500/10';
      case 'resistance':
        return 'border-red-500 bg-red-500/10';
      case 'demand':
        return 'border-green-500 bg-green-500/10';
      case 'supply':
        return 'border-red-500 bg-red-500/10';
      case 'trendline':
        return 'border-blue-500 bg-blue-500/10';
      case 'swing':
        return 'border-yellow-500 bg-yellow-500/10';
      default:
        return 'border-gray-500 bg-gray-500/10';
    }
  };

  const getIcon = () => {
    switch (data.type) {
      case 'bos':
        return '⚡';
      case 'choch':
        return '🔄';
      case 'support':
        return '⬆️';
      case 'resistance':
        return '⬇️';
      case 'demand':
        return '📈';
      case 'supply':
        return '📉';
      case 'trendline':
        return '📊';
      case 'swing':
        return '📍';
      default:
        return '•';
    }
  };

  return (
    <div
      className={cn(
        'fixed z-[9999] pointer-events-none',
        'border-2 rounded-lg shadow-2xl backdrop-blur-sm',
        'p-3 min-w-[200px] max-w-[300px]',
        getColorClass()
      )}
      style={{
        left: `${data.position.x + 15}px`,
        top: `${data.position.y - 10}px`,
        transform: 'translateY(-50%)',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-600">
        <span className="text-lg">{getIcon()}</span>
        <span className="font-bold text-white text-sm">{data.title}</span>
      </div>

      {/* Price (if available) */}
      {data.price && (
        <div className="mb-2">
          <span className="text-xl font-bold text-white">
            ₹{data.price.toFixed(2)}
          </span>
        </div>
      )}

      {/* Details */}
      <div className="space-y-1">
        {Object.entries(data.data).map(([key, value]) => (
          <div key={key} className="flex justify-between text-xs">
            <span className="text-gray-300 capitalize">
              {key.replace(/_/g, ' ')}:
            </span>
            <span className="text-white font-medium ml-2">
              {typeof value === 'number' ? value.toFixed(2) : String(value)}
            </span>
          </div>
        ))}
      </div>

      {/* Click hint */}
      <div className="mt-2 pt-2 border-t border-gray-600">
        <span className="text-xs text-gray-400 italic">
          Click for more details
        </span>
      </div>
    </div>
  );
};

export default ChartTooltip;

