/**
 * Overlay Tooltip Component
 * Shows information when hovering over chart overlays
 */

import React from 'react';
import { createPortal } from 'react-dom';

interface TooltipData {
  x: number;
  y: number;
  type: 'bos' | 'choch' | 'support' | 'resistance' | 'demand' | 'supply';
  title: string;
  price: number | string;
  details: { [key: string]: any };
}

interface OverlayTooltipProps {
  tooltip: TooltipData | null;
}

const OverlayTooltip: React.FC<OverlayTooltipProps> = ({ tooltip }) => {
  if (!tooltip) return null;

  const getColorByType = (type: string) => {
    switch (type) {
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
      default:
        return 'border-gray-500 bg-gray-500/10';
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'bos':
        return '↑';
      case 'choch':
        return '🔄';
      case 'support':
        return '━';
      case 'resistance':
        return '━';
      case 'demand':
        return '▭';
      case 'supply':
        return '▭';
      default:
        return '•';
    }
  };

  return createPortal(
    <div
      className={`
        fixed pointer-events-none z-[9999]
        min-w-[200px] max-w-[300px]
        border-2 rounded-lg shadow-xl
        backdrop-blur-sm
        ${getColorByType(tooltip.type)}
      `}
      style={{
        left: `${tooltip.x + 15}px`,
        top: `${tooltip.y - 10}px`,
      }}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-current/20">
        <div className="flex items-center gap-2">
          <span className="text-lg">{getIcon(tooltip.type)}</span>
          <span className="font-semibold text-white text-sm">
            {tooltip.title}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="px-3 py-2 space-y-1.5">
        {/* Price */}
        <div className="flex justify-between text-xs">
          <span className="text-gray-300">Price:</span>
          <span className="font-mono text-white">
            {typeof tooltip.price === 'number'
              ? `₹${tooltip.price.toFixed(2)}`
              : tooltip.price}
          </span>
        </div>

        {/* Additional Details */}
        {Object.entries(tooltip.details).map(([key, value]) => (
          <div key={key} className="flex justify-between text-xs">
            <span className="text-gray-300 capitalize">
              {key.replace(/_/g, ' ')}:
            </span>
            <span className="font-mono text-white">
              {typeof value === 'number' ? value.toFixed(2) : value}
            </span>
          </div>
        ))}
      </div>

      {/* Footer hint */}
      <div className="px-3 py-1.5 border-t border-current/20 text-[10px] text-gray-400">
        Click for more details
      </div>
    </div>,
    document.body
  );
};

export default OverlayTooltip;

