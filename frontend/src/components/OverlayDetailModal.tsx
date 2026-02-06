/**
 * Overlay Detail Modal
 * Shows comprehensive details when clicking on chart overlays
 */

import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';

export interface OverlayDetail {
  type: 'bos' | 'choch' | 'support' | 'resistance' | 'demand' | 'supply' | 'trendline' | 'swing';
  title: string;
  subtitle?: string;
  price?: number;
  priceRange?: { low: number; high: number };
  data: Record<string, any>;
  metadata?: Record<string, any>;
  actions?: Array<{ label: string; onClick: () => void }>;
}

interface OverlayDetailModalProps {
  detail: OverlayDetail | null;
  visible: boolean;
  onClose: () => void;
}

const OverlayDetailModal: React.FC<OverlayDetailModalProps> = ({
  detail,
  visible,
  onClose,
}) => {
  if (!visible || !detail) return null;

  const getHeaderColorClass = () => {
    switch (detail.type) {
      case 'bos':
        return 'bg-gradient-to-r from-green-600 to-green-500';
      case 'choch':
        return 'bg-gradient-to-r from-purple-600 to-purple-500';
      case 'support':
        return 'bg-gradient-to-r from-green-600 to-green-500';
      case 'resistance':
        return 'bg-gradient-to-r from-red-600 to-red-500';
      case 'demand':
        return 'bg-gradient-to-r from-green-600 to-emerald-500';
      case 'supply':
        return 'bg-gradient-to-r from-red-600 to-rose-500';
      case 'trendline':
        return 'bg-gradient-to-r from-blue-600 to-blue-500';
      case 'swing':
        return 'bg-gradient-to-r from-yellow-600 to-yellow-500';
      default:
        return 'bg-gradient-to-r from-gray-600 to-gray-500';
    }
  };

  const getIcon = () => {
    switch (detail.type) {
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
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9998]"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div
          className="bg-[#1e222d] rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden border border-gray-700"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className={cn('px-6 py-4 text-white', getHeaderColorClass())}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{getIcon()}</span>
                <div>
                  <h2 className="text-2xl font-bold">{detail.title}</h2>
                  {detail.subtitle && (
                    <p className="text-sm opacity-90 mt-1">{detail.subtitle}</p>
                  )}
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-6 overflow-y-auto max-h-[calc(80vh-180px)]">
            {/* Price Display */}
            {detail.price && (
              <div className="mb-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                <div className="text-sm text-gray-400 mb-1">Price Level</div>
                <div className="text-3xl font-bold text-white">
                  ₹{detail.price.toFixed(2)}
                </div>
              </div>
            )}

            {/* Price Range Display */}
            {detail.priceRange && (
              <div className="mb-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                <div className="text-sm text-gray-400 mb-2">Price Range</div>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-gray-400">Low</div>
                    <div className="text-xl font-bold text-green-400">
                      ₹{detail.priceRange.low.toFixed(2)}
                    </div>
                  </div>
                  <div className="text-gray-600">━━━</div>
                  <div>
                    <div className="text-xs text-gray-400">High</div>
                    <div className="text-xl font-bold text-red-400">
                      ₹{detail.priceRange.high.toFixed(2)}
                    </div>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-400">
                  Range: ₹{(detail.priceRange.high - detail.priceRange.low).toFixed(2)} (
                  {(((detail.priceRange.high - detail.priceRange.low) / detail.priceRange.low) * 100).toFixed(2)}%)
                </div>
              </div>
            )}

            {/* Main Data */}
            <div className="mb-6">
              <h3 className="text-lg font-bold text-white mb-3">Details</h3>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(detail.data).map(([key, value]) => (
                  <div
                    key={key}
                    className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50"
                  >
                    <div className="text-xs text-gray-400 mb-1 capitalize">
                      {key.replace(/_/g, ' ')}
                    </div>
                    <div className="text-base font-semibold text-white">
                      {typeof value === 'number'
                        ? value.toFixed(2)
                        : typeof value === 'boolean'
                        ? value
                          ? '✅ Yes'
                          : '❌ No'
                        : String(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Metadata */}
            {detail.metadata && Object.keys(detail.metadata).length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-bold text-white mb-3">Additional Info</h3>
                <div className="space-y-2">
                  {Object.entries(detail.metadata).map(([key, value]) => (
                    <div
                      key={key}
                      className="flex justify-between items-center p-2 bg-gray-800/20 rounded"
                    >
                      <span className="text-sm text-gray-400 capitalize">
                        {key.replace(/_/g, ' ')}:
                      </span>
                      <span className="text-sm font-medium text-white">
                        {typeof value === 'number' ? value.toFixed(2) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Trading Tips */}
            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <div className="flex items-start gap-2">
                <span className="text-blue-400 text-xl">💡</span>
                <div>
                  <div className="font-semibold text-blue-300 mb-1">Trading Tip</div>
                  <div className="text-sm text-gray-300">
                    {detail.type === 'demand' &&
                      'Look for price to react at this zone. Consider buying if price tests and holds.'}
                    {detail.type === 'supply' &&
                      'Look for price rejection at this zone. Consider selling if price tests and rejects.'}
                    {detail.type === 'support' &&
                      'Strong support level. Watch for bounces or breakdown below this level.'}
                    {detail.type === 'resistance' &&
                      'Strong resistance level. Watch for rejections or breakout above this level.'}
                    {detail.type === 'bos' &&
                      'Break of Structure indicates trend continuation. Strong momentum signal.'}
                    {detail.type === 'choch' &&
                      'Change of Character suggests potential trend reversal. Watch for confirmation.'}
                    {detail.type === 'trendline' &&
                      'Trendline support/resistance. Watch for bounces or breaks.'}
                    {detail.type === 'swing' &&
                      'Key swing point. Important for market structure analysis.'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="px-6 py-4 bg-gray-800/50 border-t border-gray-700 flex gap-3">
            {detail.actions?.map((action, index) => (
              <button
                key={index}
                onClick={action.onClick}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                {action.label}
              </button>
            ))}
            <button
              onClick={onClose}
              className="ml-auto px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default OverlayDetailModal;

