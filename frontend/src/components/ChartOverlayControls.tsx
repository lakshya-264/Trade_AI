/**
 * Chart Overlay Controls
 * Toggle visibility of chart overlays (BOS/CHoCH, S&R, Supply/Demand)
 */

import React, { useState } from 'react';
import {
  EyeIcon,
  EyeSlashIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline';
import { OverlaySettings } from '../services/chartOverlayService';

interface ChartOverlayControlsProps {
  settings: OverlaySettings;
  onSettingsChange: (settings: Partial<OverlaySettings>) => void;
  className?: string;
}

const ChartOverlayControls: React.FC<ChartOverlayControlsProps> = ({
  settings,
  onSettingsChange,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const toggleSetting = (key: keyof OverlaySettings) => {
    onSettingsChange({ [key]: !settings[key] });
  };

  const updateMinStrength = (value: number) => {
    onSettingsChange({ minStrength: value });
  };

  return (
    <div className={`bg-gray-800 rounded-lg border border-gray-700 ${className}`}>
      {/* Header */}
      <div
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-750 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <ChartBarIcon className="w-5 h-5 text-blue-400" />
          <span className="font-medium text-white">Chart Overlays</span>
        </div>
        <button
          className="p-1 hover:bg-gray-700 rounded transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
        >
          {isExpanded ? (
            <EyeIcon className="w-5 h-5 text-gray-400" />
          ) : (
            <EyeSlashIcon className="w-5 h-5 text-gray-400" />
          )}
        </button>
      </div>

      {/* Controls */}
      {isExpanded && (
        <div className="p-3 space-y-3 border-t border-gray-700">
          {/* Market Structure */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-purple-400">
              <div className="w-2 h-2 rounded-full bg-purple-400"></div>
              <span>Market Structure</span>
            </div>
            <div className="ml-4 space-y-1.5">
              <ToggleButton
                label="BOS Events"
                checked={settings.showBOS}
                onChange={() => toggleSetting('showBOS')}
                icon="↑"
                color="green"
              />
              <ToggleButton
                label="CHoCH Events"
                checked={settings.showCHoCH}
                onChange={() => toggleSetting('showCHoCH')}
                icon="🔄"
                color="purple"
              />
            </div>
          </div>

          {/* Support & Resistance */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-indigo-400">
              <div className="w-2 h-2 rounded-full bg-indigo-400"></div>
              <span>Support & Resistance</span>
            </div>
            <div className="ml-4 space-y-1.5">
              <ToggleButton
                label="Support Levels"
                checked={settings.showSupport}
                onChange={() => toggleSetting('showSupport')}
                icon="━"
                color="green"
              />
              <ToggleButton
                label="Resistance Levels"
                checked={settings.showResistance}
                onChange={() => toggleSetting('showResistance')}
                icon="━"
                color="red"
              />
            </div>
          </div>

          {/* Supply & Demand */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-orange-400">
              <div className="w-2 h-2 rounded-full bg-orange-400"></div>
              <span>Supply & Demand Zones</span>
            </div>
            <div className="ml-4 space-y-1.5">
              <ToggleButton
                label="Demand Zones"
                checked={settings.showDemandZones}
                onChange={() => toggleSetting('showDemandZones')}
                icon="▭"
                color="green"
              />
              <ToggleButton
                label="Supply Zones"
                checked={settings.showSupplyZones}
                onChange={() => toggleSetting('showSupplyZones')}
                icon="▭"
                color="red"
              />
            </div>
          </div>

          {/* Trendlines */}
          {settings.showTrendlines !== undefined && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-blue-400">
                <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                <span>Trendlines</span>
              </div>
              <div className="ml-4 space-y-1.5">
                <ToggleButton
                  label="Show Trendlines"
                  checked={settings.showTrendlines}
                  onChange={() => toggleSetting('showTrendlines')}
                  icon="/"
                  color="blue"
                />
              </div>
            </div>
          )}

          {/* Swing Points */}
          {settings.showSwingPoints !== undefined && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-yellow-400">
                <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                <span>Swing Points</span>
              </div>
              <div className="ml-4 space-y-1.5">
                <ToggleButton
                  label="Show Swing Points"
                  checked={settings.showSwingPoints}
                  onChange={() => toggleSetting('showSwingPoints')}
                  icon="◆"
                  color="purple"
                />
              </div>
            </div>
          )}

          {/* Advanced Settings */}
          <div className="pt-2 border-t border-gray-700">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              <AdjustmentsHorizontalIcon className="w-4 h-4" />
              <span>Advanced Settings</span>
              <span className="ml-auto text-xs">
                {showAdvanced ? '▼' : '▶'}
              </span>
            </button>

            {showAdvanced && (
              <div className="mt-3 space-y-3">
                <ToggleButton
                  label="Fresh Zones Only"
                  checked={settings.freshZonesOnly}
                  onChange={() => toggleSetting('freshZonesOnly')}
                  description="Show only untested zones"
                />
                <ToggleButton
                  label="Strong Zones Only"
                  checked={settings.strongZonesOnly}
                  onChange={() => toggleSetting('strongZonesOnly')}
                  description="Filter weak levels"
                />

                {/* Minimum Strength Slider */}
                <div className="space-y-2">
                  <label className="flex items-center justify-between text-sm text-gray-300">
                    <span>Minimum Strength</span>
                    <span className="text-blue-400 font-mono">
                      {(settings.minStrength * 100).toFixed(0)}%
                    </span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={settings.minStrength * 100}
                    onChange={(e) => updateMinStrength(Number(e.target.value) / 100)}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Weak</span>
                    <span>Medium</span>
                    <span>Strong</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="flex gap-2 pt-2 border-t border-gray-700">
            <button
              onClick={() =>
                onSettingsChange({
                  showBOS: true,
                  showCHoCH: true,
                  showSupport: true,
                  showResistance: true,
                  showDemandZones: true,
                  showSupplyZones: true,
                  showTrendlines: true,
                  showSwingPoints: true,
                })
              }
              className="flex-1 px-3 py-1.5 text-xs font-medium text-green-400 bg-green-400/10 hover:bg-green-400/20 rounded transition-colors"
            >
              Show All
            </button>
            <button
              onClick={() =>
                onSettingsChange({
                  showBOS: false,
                  showCHoCH: false,
                  showSupport: false,
                  showResistance: false,
                  showDemandZones: false,
                  showSupplyZones: false,
                  showTrendlines: false,
                  showSwingPoints: false,
                })
              }
              className="flex-1 px-3 py-1.5 text-xs font-medium text-red-400 bg-red-400/10 hover:bg-red-400/20 rounded transition-colors"
            >
              Hide All
            </button>
          </div>
        </div>
      )}

      {/* Summary Bar (when collapsed) */}
      {!isExpanded && (
        <div className="px-3 pb-2 flex items-center gap-2 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            {getActiveCount(settings)} active
          </span>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// TOGGLE BUTTON COMPONENT
// =============================================================================

interface ToggleButtonProps {
  label: string;
  checked: boolean;
  onChange: () => void;
  icon?: string;
  color?: 'green' | 'red' | 'purple' | 'blue';
  description?: string;
}

const ToggleButton: React.FC<ToggleButtonProps> = ({
  label,
  checked,
  onChange,
  icon,
  color = 'blue',
  description,
}) => {
  const colorClasses = {
    green: 'bg-green-500',
    red: 'bg-red-500',
    purple: 'bg-purple-500',
    blue: 'bg-blue-500',
  };

  return (
    <div className="flex items-center justify-between group">
      <div className="flex items-center gap-2 flex-1">
        {icon && (
          <span className="text-sm opacity-70">{icon}</span>
        )}
        <label className="flex flex-col cursor-pointer flex-1">
          <span className="text-sm text-gray-300 group-hover:text-white transition-colors">
            {label}
          </span>
          {description && (
            <span className="text-xs text-gray-500">{description}</span>
          )}
        </label>
      </div>
      <button
        onClick={onChange}
        className={`
          relative inline-flex h-5 w-9 items-center rounded-full
          transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800
          ${checked ? colorClasses[color] : 'bg-gray-600'}
        `}
      >
        <span
          className={`
            inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform duration-200
            ${checked ? 'translate-x-5' : 'translate-x-1'}
          `}
        />
      </button>
    </div>
  );
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function getActiveCount(settings: OverlaySettings): number {
  let count = 0;
  if (settings.showBOS) count++;
  if (settings.showCHoCH) count++;
  if (settings.showSupport) count++;
  if (settings.showResistance) count++;
  if (settings.showDemandZones) count++;
  if (settings.showSupplyZones) count++;
  if (settings.showTrendlines) count++;
  if (settings.showSwingPoints) count++;
  return count;
}

export default ChartOverlayControls;

