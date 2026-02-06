/**
 * Enhanced Indicator Selector Component
 * Allows users to select, customize, and manage all technical indicators
 */

import React, { useState, useEffect } from 'react';
import { 
  AdjustmentsHorizontalIcon, 
  EyeIcon, 
  EyeSlashIcon,
  XMarkIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

export interface IndicatorConfig {
  name: string;
  type: 'SMA' | 'EMA' | 'RSI' | 'MACD' | 'BB' | 'ATR' | 'STOCH';
  period: number;
  color: string;
  visible: boolean;
  dataKey?: string; // Optional for compatibility
  enabled?: boolean; // Optional for compatibility
  lineWidth?: number;
  opacity?: number;
  lineStyle?: 'solid' | 'dashed' | 'dotted';
  category?: 'trend' | 'momentum' | 'volatility' | 'volume' | 'other';
  description?: string;
}

interface EnhancedIndicatorSelectorProps {
  indicators: IndicatorConfig[];
  onIndicatorsChange: (indicators: IndicatorConfig[]) => void;
  onClose?: () => void;
}

const EnhancedIndicatorSelector: React.FC<EnhancedIndicatorSelectorProps> = ({
  indicators: initialIndicators,
  onIndicatorsChange,
  onClose
}) => {
  const [indicators, setIndicators] = useState<IndicatorConfig[]>(initialIndicators);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [editingIndicator, setEditingIndicator] = useState<string | null>(null);

  useEffect(() => {
    setIndicators(initialIndicators);
  }, [initialIndicators]);

  const categories = [
    { id: 'all', name: 'All Indicators' },
    { id: 'trend', name: 'Trend' },
    { id: 'momentum', name: 'Momentum' },
    { id: 'volatility', name: 'Volatility' },
    { id: 'volume', name: 'Volume' },
    { id: 'other', name: 'Other' }
  ];

  const filteredIndicators = indicators.filter(ind => {
    const matchesSearch = ind.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         (ind.description || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || (ind.category || 'other') === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleToggleIndicator = (name: string) => {
    const updated = indicators.map(ind => {
      if (ind.name === name) {
        // Toggle visibility
        const newVisible = !ind.visible;
        // For enabled: use original enabled value if it exists, otherwise use the new visible state
        // This ensures enabled reflects the actual state, not the toggled state
        const newEnabled = ind.enabled !== undefined ? ind.enabled : newVisible;
        return { ...ind, visible: newVisible, enabled: newEnabled };
      }
      return ind;
    });
    setIndicators(updated);
    onIndicatorsChange(updated);
  };

  const handleUpdateIndicator = (name: string, updates: Partial<IndicatorConfig>) => {
    const updated = indicators.map(ind => 
      ind.name === name ? { ...ind, ...updates } : ind
    );
    setIndicators(updated);
    onIndicatorsChange(updated);
  };

  const enabledCount = indicators.filter(ind => ind.visible || ind.enabled).length;

  return (
    <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl w-full max-w-4xl max-h-[80vh] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-[#2a2e39] flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <AdjustmentsHorizontalIcon className="w-5 h-5 text-blue-400" />
            Technical Indicators
          </h3>
          <p className="text-sm text-gray-400 mt-1">
            {enabledCount} of {indicators.length} indicators enabled
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Search and Filter */}
      <div className="p-4 border-b border-[#2a2e39] space-y-3">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search indicators..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#131722] border border-[#2a2e39] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === cat.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      {/* Indicators List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {filteredIndicators.map(indicator => {
            const isVisible = indicator.visible || indicator.enabled;
            const indicatorKey = indicator.name || indicator.dataKey || '';
            return (
              <div
              key={indicatorKey}
              className={`bg-[#131722] border rounded-lg p-3 transition-all ${
                isVisible
                  ? 'border-blue-500/50 bg-blue-500/5'
                  : 'border-[#2a2e39]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <button
                    onClick={() => handleToggleIndicator(indicator.name)}
                    className="flex items-center gap-2 text-sm font-medium text-white hover:text-blue-400 transition-colors"
                  >
                    {isVisible ? (
                      <EyeIcon className="w-5 h-5 text-blue-400" />
                    ) : (
                      <EyeSlashIcon className="w-5 h-5 text-gray-500" />
                    )}
                    <span>{indicator.name}</span>
                  </button>
                  {indicator.category && (
                    <span className="text-xs text-gray-500 px-2 py-0.5 bg-[#2a2e39] rounded">
                      {indicator.category}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setEditingIndicator(
                    editingIndicator === indicatorKey ? null : indicatorKey
                  )}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <AdjustmentsHorizontalIcon className="w-5 h-5" />
                </button>
              </div>

              {editingIndicator === indicatorKey && (
                <div className="mt-3 pt-3 border-t border-[#2a2e39] space-y-3">
                  {/* Period */}
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Period</label>
                    <input
                      type="number"
                      min="1"
                      max="200"
                      value={indicator.period}
                      onChange={(e) => handleUpdateIndicator(indicator.name, {
                        period: parseInt(e.target.value) || 14
                      })}
                      className="w-full px-3 py-1.5 bg-[#2a2e39] border border-[#363a45] rounded text-white text-sm"
                    />
                  </div>

                  {/* Color */}
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Color</label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={indicator.color}
                        onChange={(e) => handleUpdateIndicator(indicator.name, {
                          color: e.target.value
                        })}
                        className="w-10 h-10 rounded cursor-pointer"
                      />
                      <input
                        type="text"
                        value={indicator.color}
                        onChange={(e) => handleUpdateIndicator(indicator.name, {
                          color: e.target.value
                        })}
                        className="flex-1 px-3 py-1.5 bg-[#2a2e39] border border-[#363a45] rounded text-white text-sm"
                      />
                    </div>
                  </div>

                  {/* Line Width */}
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">
                      Line Width: {indicator.lineWidth || 2}px
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={indicator.lineWidth || 2}
                      onChange={(e) => handleUpdateIndicator(indicator.name, {
                        lineWidth: parseInt(e.target.value)
                      })}
                      className="w-full"
                    />
                  </div>

                  {/* Opacity */}
                  {indicator.opacity !== undefined && (
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">
                        Opacity: {Math.round((indicator.opacity || 1) * 100)}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={(indicator.opacity || 1) * 100}
                        onChange={(e) => handleUpdateIndicator(indicator.name, {
                          opacity: parseInt(e.target.value) / 100
                        })}
                        className="w-full"
                      />
                    </div>
                  )}

                  {/* Line Style */}
                  {indicator.lineStyle && (
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Line Style</label>
                      <select
                        value={indicator.lineStyle}
                        onChange={(e) => handleUpdateIndicator(indicator.name, {
                          lineStyle: e.target.value as 'solid' | 'dashed' | 'dotted'
                        })}
                        className="w-full px-3 py-1.5 bg-[#2a2e39] border border-[#363a45] rounded text-white text-sm"
                      >
                        <option value="solid">Solid</option>
                        <option value="dashed">Dashed</option>
                        <option value="dotted">Dotted</option>
                      </select>
                    </div>
                  )}

                  {/* Description */}
                  {indicator.description && (
                    <p className="text-xs text-gray-500 mt-2">{indicator.description}</p>
                  )}
                </div>
              )}
            </div>
            );
          })}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-[#2a2e39] flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => {
              const allEnabled = indicators.map(ind => ({ ...ind, enabled: true }));
              setIndicators(allEnabled);
              onIndicatorsChange(allEnabled);
            }}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Enable All
          </button>
          <button
            onClick={() => {
              const allDisabled = indicators.map(ind => ({ ...ind, enabled: false }));
              setIndicators(allDisabled);
              onIndicatorsChange(allDisabled);
            }}
            className="px-4 py-2 bg-[#2a2e39] hover:bg-[#363a45] text-gray-300 rounded-lg text-sm font-medium transition-colors"
          >
            Disable All
          </button>
        </div>
        <button
          onClick={onClose}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  );
};

export default EnhancedIndicatorSelector;

