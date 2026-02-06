/**
 * Chart Settings Panel
 * Comprehensive chart customization UI
 */

import React, { useState } from 'react';
import { XMarkIcon, PaintBrushIcon, ChartBarIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
import { ChartSettings } from '../types/chartSettings';
import ThemeCustomization from './ThemeCustomization';

interface ChartSettingsPanelProps {
  settings: ChartSettings;
  onSettingsChange: (settings: Partial<ChartSettings>) => void;
  onThemeChange: (theme: ChartSettings['theme']) => void;
  onClose: () => void;
}

const ChartSettingsPanel: React.FC<ChartSettingsPanelProps> = ({
  settings,
  onSettingsChange,
  onThemeChange,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'theme' | 'appearance' | 'candlestick' | 'scale' | 'indicators'>('theme');

  const tabs = [
    { id: 'theme' as const, name: 'Theme', icon: PaintBrushIcon },
    { id: 'appearance' as const, name: 'Appearance', icon: ChartBarIcon },
    { id: 'candlestick' as const, name: 'Candlestick', icon: ChartBarIcon },
    { id: 'scale' as const, name: 'Scale', icon: Cog6ToothIcon },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#1e222d] border border-[#2a2e39] rounded-lg w-[90vw] max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#2a2e39]">
          <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
            <Cog6ToothIcon className="w-6 h-6" />
            Chart Settings
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[#2a2e39] px-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors border-b-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.name}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'theme' && (
            <div>
              <ThemeCustomization
                onThemeChange={onThemeChange}
                currentTheme={settings.theme}
              />
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Grid Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Show Grid Lines</label>
                  <input
                    type="checkbox"
                    checked={settings.appearance.gridVisible}
                    onChange={(e) =>
                      onSettingsChange({
                        appearance: { ...settings.appearance, gridVisible: e.target.checked },
                      })
                    }
                    className="w-5 h-5 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Grid Color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={settings.appearance.gridColor}
                      onChange={(e) =>
                        onSettingsChange({
                          appearance: { ...settings.appearance, gridColor: e.target.value },
                        })
                      }
                      className="w-12 h-8 rounded border border-[#2a2e39] cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.appearance.gridColor}
                      onChange={(e) =>
                        onSettingsChange({
                          appearance: { ...settings.appearance, gridColor: e.target.value },
                        })
                      }
                      className="w-24 px-2 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Grid Style</label>
                  <select
                    value={settings.appearance.gridStyle}
                    onChange={(e) =>
                      onSettingsChange({
                        appearance: {
                          ...settings.appearance,
                          gridStyle: e.target.value as 'solid' | 'dashed' | 'dotted',
                        },
                      })
                    }
                    className="px-3 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                  >
                    <option value="solid">Solid</option>
                    <option value="dashed">Dashed</option>
                    <option value="dotted">Dotted</option>
                  </select>
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Grid Opacity</label>
                  <div className="flex items-center gap-2 flex-1 max-w-xs">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={settings.appearance.gridOpacity}
                      onChange={(e) =>
                        onSettingsChange({
                          appearance: {
                            ...settings.appearance,
                            gridOpacity: parseFloat(e.target.value),
                          },
                        })
                      }
                      className="flex-1"
                    />
                    <span className="text-sm text-gray-400 w-12 text-right">
                      {Math.round(settings.appearance.gridOpacity * 100)}%
                    </span>
                  </div>
                </div>
              </div>

              <h3 className="text-lg font-semibold text-white mb-4 mt-6">Crosshair Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Show Crosshair</label>
                  <input
                    type="checkbox"
                    checked={settings.appearance.crosshairVisible}
                    onChange={(e) =>
                      onSettingsChange({
                        appearance: { ...settings.appearance, crosshairVisible: e.target.checked },
                      })
                    }
                    className="w-5 h-5 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Crosshair Color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={settings.appearance.crosshairColor}
                      onChange={(e) =>
                        onSettingsChange({
                          appearance: { ...settings.appearance, crosshairColor: e.target.value },
                        })
                      }
                      className="w-12 h-8 rounded border border-[#2a2e39] cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.appearance.crosshairColor}
                      onChange={(e) =>
                        onSettingsChange({
                          appearance: { ...settings.appearance, crosshairColor: e.target.value },
                        })
                      }
                      className="w-24 px-2 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Crosshair Style</label>
                  <select
                    value={settings.appearance.crosshairStyle}
                    onChange={(e) =>
                      onSettingsChange({
                        appearance: {
                          ...settings.appearance,
                          crosshairStyle: e.target.value as 'solid' | 'dashed' | 'dotted',
                        },
                      })
                    }
                    className="px-3 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                  >
                    <option value="solid">Solid</option>
                    <option value="dashed">Dashed</option>
                    <option value="dotted">Dotted</option>
                  </select>
                </div>
              </div>

              <h3 className="text-lg font-semibold text-white mb-4 mt-6">Border Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Show Border</label>
                  <input
                    type="checkbox"
                    checked={settings.appearance.borderVisible}
                    onChange={(e) =>
                      onSettingsChange({
                        appearance: { ...settings.appearance, borderVisible: e.target.checked },
                      })
                    }
                    className="w-5 h-5 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Border Color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={settings.appearance.borderColor}
                      onChange={(e) =>
                        onSettingsChange({
                          appearance: { ...settings.appearance, borderColor: e.target.value },
                        })
                      }
                      className="w-12 h-8 rounded border border-[#2a2e39] cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.appearance.borderColor}
                      onChange={(e) =>
                        onSettingsChange({
                          appearance: { ...settings.appearance, borderColor: e.target.value },
                        })
                      }
                      className="w-24 px-2 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'candlestick' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Candlestick Style</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Chart Type</label>
                  <select
                    value={settings.candlestick.style}
                    onChange={(e) =>
                      onSettingsChange({
                        candlestick: {
                          ...settings.candlestick,
                          style: e.target.value as ChartSettings['candlestick']['style'],
                        },
                      })
                    }
                    className="px-3 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                  >
                    <option value="candlestick">Candlestick</option>
                    <option value="hollow">Hollow Candlestick</option>
                    <option value="line">Line</option>
                    <option value="area">Area</option>
                    <option value="bars">Bars</option>
                  </select>
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Up Color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={settings.candlestick.upColor}
                      onChange={(e) =>
                        onSettingsChange({
                          candlestick: { ...settings.candlestick, upColor: e.target.value },
                        })
                      }
                      className="w-12 h-8 rounded border border-[#2a2e39] cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.candlestick.upColor}
                      onChange={(e) =>
                        onSettingsChange({
                          candlestick: { ...settings.candlestick, upColor: e.target.value },
                        })
                      }
                      className="w-24 px-2 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Down Color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={settings.candlestick.downColor}
                      onChange={(e) =>
                        onSettingsChange({
                          candlestick: { ...settings.candlestick, downColor: e.target.value },
                        })
                      }
                      className="w-12 h-8 rounded border border-[#2a2e39] cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.candlestick.downColor}
                      onChange={(e) =>
                        onSettingsChange({
                          candlestick: { ...settings.candlestick, downColor: e.target.value },
                        })
                      }
                      className="w-24 px-2 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Show Border</label>
                  <input
                    type="checkbox"
                    checked={settings.candlestick.borderVisible}
                    onChange={(e) =>
                      onSettingsChange({
                        candlestick: { ...settings.candlestick, borderVisible: e.target.checked },
                      })
                    }
                    className="w-5 h-5 rounded"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'scale' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Price Scale</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Position</label>
                  <select
                    value={settings.scale.priceScalePosition}
                    onChange={(e) =>
                      onSettingsChange({
                        scale: {
                          ...settings.scale,
                          priceScalePosition: e.target.value as 'left' | 'right',
                        },
                      })
                    }
                    className="px-3 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                  >
                    <option value="left">Left</option>
                    <option value="right">Right</option>
                  </select>
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Decimal Places</label>
                  <input
                    type="number"
                    min="0"
                    max="8"
                    value={settings.scale.priceFormat.precision}
                    onChange={(e) =>
                      onSettingsChange({
                        scale: {
                          ...settings.scale,
                          priceFormat: {
                            ...settings.scale.priceFormat,
                            precision: parseInt(e.target.value) || 2,
                          },
                        },
                      })
                    }
                    className="w-20 px-2 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Auto Scale</label>
                  <input
                    type="checkbox"
                    checked={settings.scale.autoScale}
                    onChange={(e) =>
                      onSettingsChange({
                        scale: { ...settings.scale, autoScale: e.target.checked },
                      })
                    }
                    className="w-5 h-5 rounded"
                  />
                </div>
              </div>

              <h3 className="text-lg font-semibold text-white mb-4 mt-6">Time Scale</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Show Time</label>
                  <input
                    type="checkbox"
                    checked={settings.scale.timeVisible}
                    onChange={(e) =>
                      onSettingsChange({
                        scale: { ...settings.scale, timeVisible: e.target.checked },
                      })
                    }
                    className="w-5 h-5 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Time Format</label>
                  <select
                    value={settings.scale.timeFormat}
                    onChange={(e) =>
                      onSettingsChange({
                        scale: {
                          ...settings.scale,
                          timeFormat: e.target.value as ChartSettings['scale']['timeFormat'],
                        },
                      })
                    }
                    className="px-3 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                  >
                    <option value="24h">24 Hour</option>
                    <option value="12h">12 Hour</option>
                    <option value="DD/MM">DD/MM</option>
                    <option value="MM/DD">MM/DD</option>
                  </select>
                </div>
              </div>

              <h3 className="text-lg font-semibold text-white mb-4 mt-6">Scale Margins</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Top Margin</label>
                  <div className="flex items-center gap-2 flex-1 max-w-xs">
                    <input
                      type="range"
                      min="0"
                      max="0.5"
                      step="0.01"
                      value={settings.scale.scaleMargins.top}
                      onChange={(e) =>
                        onSettingsChange({
                          scale: {
                            ...settings.scale,
                            scaleMargins: {
                              ...settings.scale.scaleMargins,
                              top: parseFloat(e.target.value),
                            },
                          },
                        })
                      }
                      className="flex-1"
                    />
                    <span className="text-sm text-gray-400 w-16 text-right">
                      {Math.round(settings.scale.scaleMargins.top * 100)}%
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Bottom Margin</label>
                  <div className="flex items-center gap-2 flex-1 max-w-xs">
                    <input
                      type="range"
                      min="0"
                      max="0.5"
                      step="0.01"
                      value={settings.scale.scaleMargins.bottom}
                      onChange={(e) =>
                        onSettingsChange({
                          scale: {
                            ...settings.scale,
                            scaleMargins: {
                              ...settings.scale.scaleMargins,
                              bottom: parseFloat(e.target.value),
                            },
                          },
                        })
                      }
                      className="flex-1"
                    />
                    <span className="text-sm text-gray-400 w-16 text-right">
                      {Math.round(settings.scale.scaleMargins.bottom * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-6 border-t border-[#2a2e39]">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#2a2e39] hover:bg-[#363a45] text-gray-300 rounded font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChartSettingsPanel;

