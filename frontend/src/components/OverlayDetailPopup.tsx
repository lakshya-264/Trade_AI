/**
 * Overlay Detail Popup Component
 * Shows detailed information when clicking on chart overlays
 */

import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface PopupData {
  type: 'bos' | 'choch' | 'support' | 'resistance' | 'demand' | 'supply';
  title: string;
  price: number | string;
  data: { [key: string]: any };
}

interface OverlayDetailPopupProps {
  popup: PopupData | null;
  onClose: () => void;
}

const OverlayDetailPopup: React.FC<OverlayDetailPopupProps> = ({
  popup,
  onClose,
}) => {
  if (!popup) return null;

  const getBgColor = (type: string) => {
    switch (type) {
      case 'bos':
        return 'bg-gradient-to-br from-green-900/90 to-green-800/90';
      case 'choch':
        return 'bg-gradient-to-br from-purple-900/90 to-purple-800/90';
      case 'support':
        return 'bg-gradient-to-br from-green-900/90 to-green-800/90';
      case 'resistance':
        return 'bg-gradient-to-br from-red-900/90 to-red-800/90';
      case 'demand':
        return 'bg-gradient-to-br from-green-900/90 to-green-800/90';
      case 'supply':
        return 'bg-gradient-to-br from-red-900/90 to-red-800/90';
      default:
        return 'bg-gradient-to-br from-gray-900/90 to-gray-800/90';
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'bos':
        return '↑ BOS';
      case 'choch':
        return '🔄 CHoCH';
      case 'support':
        return '━ Support';
      case 'resistance':
        return '━ Resistance';
      case 'demand':
        return '▭ Demand Zone';
      case 'supply':
        return '▭ Supply Zone';
      default:
        return '• Info';
    }
  };

  const getTradingSuggestion = (type: string) => {
    switch (type) {
      case 'bos':
        return 'Trend continuation likely. Consider adding to position.';
      case 'choch':
        return 'Potential trend reversal. Watch for confirmation.';
      case 'support':
        return 'Look for buying opportunities near this level.';
      case 'resistance':
        return 'Look for selling opportunities near this level.';
      case 'demand':
        return 'Strong buying zone. Buy on retest, stop below zone.';
      case 'supply':
        return 'Strong selling zone. Sell on retest, stop above zone.';
      default:
        return 'Monitor price action at this level.';
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9998]"
        onClick={onClose}
      />

      {/* Popup */}
      <div
        className={`
          fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2
          z-[9999] w-full max-w-md
          ${getBgColor(popup.type)}
          border border-white/20 rounded-xl shadow-2xl
          overflow-hidden
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getIcon(popup.type).split(' ')[0]}</span>
            <div>
              <h3 className="text-lg font-bold text-white">
                {popup.title}
              </h3>
              <p className="text-sm text-white/70">
                {getIcon(popup.type).split(' ').slice(1).join(' ')}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-4">
          {/* Price Display */}
          <div className="bg-white/5 rounded-lg p-4 text-center">
            <p className="text-sm text-white/70 mb-1">Price Level</p>
            <p className="text-3xl font-bold text-white font-mono">
              {typeof popup.price === 'number'
                ? `₹${popup.price.toFixed(2)}`
                : popup.price}
            </p>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(popup.data).map(([key, value]) => {
              if (key === 'tradingSuggestion' || key === 'description') return null;
              return (
                <div
                  key={key}
                  className="bg-white/5 rounded-lg p-3"
                >
                  <p className="text-xs text-white/70 mb-1 capitalize">
                    {key.replace(/_/g, ' ')}
                  </p>
                  <p className="text-sm font-semibold text-white">
                    {typeof value === 'number' 
                      ? value.toFixed(2)
                      : value || 'N/A'}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Trading Suggestion */}
          <div className="bg-white/10 rounded-lg p-4">
            <p className="text-xs font-semibold text-white/90 mb-2">
              💡 Trading Suggestion:
            </p>
            <p className="text-sm text-white/80">
              {popup.data.tradingSuggestion || getTradingSuggestion(popup.type)}
            </p>
          </div>

          {/* Historical Performance (if available) */}
          {popup.data.successRate !== undefined && (
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-xs font-semibold text-white/90 mb-2">
                📊 Historical Performance:
              </p>
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-xs text-white/70">Success Rate</p>
                  <p className="text-lg font-bold text-white">
                    {popup.data.successRate}%
                  </p>
                </div>
                {popup.data.avgBounce && (
                  <div>
                    <p className="text-xs text-white/70">Avg Bounce</p>
                    <p className="text-lg font-bold text-white">
                      {popup.data.avgBounce}%
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white font-medium transition-colors"
          >
            Close
          </button>
          <button
            className="flex-1 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-white font-medium transition-colors"
            onClick={() => {
              // TODO: Add to watchlist functionality
              console.log('Add alert for:', popup.title);
              onClose();
            }}
          >
            Set Alert
          </button>
        </div>
      </div>
    </>
  );
};

export default OverlayDetailPopup;

