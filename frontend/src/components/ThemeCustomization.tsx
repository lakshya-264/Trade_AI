import React, { useState } from 'react';
import { PaintBrushIcon, XMarkIcon, CheckIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

interface Theme {
  id: string;
  name: string;
  colors: {
    background: string;
    grid: string;
    text: string;
    primary: string;
    success: string;
    danger: string;
    candleUp: string;
    candleDown: string;
  };
}

interface ThemeCustomizationProps {
  onThemeChange?: (theme: Theme) => void;
  currentTheme?: Theme;
}

const ThemeCustomization: React.FC<ThemeCustomizationProps> = ({
  onThemeChange,
  currentTheme
}) => {
  const themes: Theme[] = [
    {
      id: 'dark',
      name: 'Dark Professional',
      colors: {
        background: '#131722',
        grid: '#2a2e39',
        text: '#d1d5db',
        primary: '#3B82F6',
        success: '#10B981',
        danger: '#EF4444',
        candleUp: '#26a69a',
        candleDown: '#ef5350'
      }
    },
    {
      id: 'light',
      name: 'Light Professional',
      colors: {
        background: '#ffffff',
        grid: '#e5e7eb',
        text: '#1f2937',
        primary: '#3B82F6',
        success: '#10B981',
        danger: '#EF4444',
        candleUp: '#26a69a',
        candleDown: '#ef5350'
      }
    },
    {
      id: 'dark-blue',
      name: 'Dark Blue',
      colors: {
        background: '#0f172a',
        grid: '#1e293b',
        text: '#cbd5e1',
        primary: '#60a5fa',
        success: '#34d399',
        danger: '#f87171',
        candleUp: '#34d399',
        candleDown: '#f87171'
      }
    },
    {
      id: 'dark-green',
      name: 'Dark Green',
      colors: {
        background: '#0a1f0a',
        grid: '#1a3a1a',
        text: '#d1fae5',
        primary: '#10b981',
        success: '#34d399',
        danger: '#f87171',
        candleUp: '#34d399',
        candleDown: '#f87171'
      }
    },
    {
      id: 'custom',
      name: 'Custom',
      colors: {
        background: '#131722',
        grid: '#2a2e39',
        text: '#d1d5db',
        primary: '#3B82F6',
        success: '#10B981',
        danger: '#EF4444',
        candleUp: '#26a69a',
        candleDown: '#ef5350'
      }
    }
  ];

  const getDefaultTheme = (): Theme => {
    const saved = localStorage.getItem('chart_theme');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return themes[0];
      }
    }
    return themes[0];
  };

  const [showThemePanel, setShowThemePanel] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<Theme>(currentTheme || getDefaultTheme());

  const applyTheme = (theme: Theme) => {
    setSelectedTheme(theme);
    localStorage.setItem('chart_theme', JSON.stringify(theme));
    
    // Apply CSS variables
    const root = document.documentElement;
    root.style.setProperty('--chart-bg', theme.colors.background);
    root.style.setProperty('--chart-grid', theme.colors.grid);
    root.style.setProperty('--chart-text', theme.colors.text);
    root.style.setProperty('--chart-primary', theme.colors.primary);
    root.style.setProperty('--chart-success', theme.colors.success);
    root.style.setProperty('--chart-danger', theme.colors.danger);
    
    onThemeChange?.(theme);
    toast.success(`Theme changed to ${theme.name}`);
  };

  const handleColorChange = (colorKey: keyof Theme['colors'], value: string) => {
    const updatedTheme: Theme = {
      ...selectedTheme,
      colors: {
        ...selectedTheme.colors,
        [colorKey]: value
      }
    };
    setSelectedTheme(updatedTheme);
  };

  const saveCustomTheme = () => {
    const customTheme: Theme = {
      ...selectedTheme,
      id: 'custom',
      name: 'Custom'
    };
    applyTheme(customTheme);
  };

  return (
    <>
      <button
        onClick={() => setShowThemePanel(!showThemePanel)}
        className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm text-gray-300 hover:text-white transition-colors"
        title="Theme Settings"
      >
        <PaintBrushIcon className="w-5 h-5" />
        Theme
      </button>

      {showThemePanel && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                <PaintBrushIcon className="w-6 h-6" />
                Theme Customization
              </h3>
              <button
                onClick={() => setShowThemePanel(false)}
                className="text-gray-400 hover:text-white"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Preset Themes */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Preset Themes</h4>
              <div className="grid grid-cols-2 gap-3">
                {themes.filter(t => t.id !== 'custom').map((theme) => (
                  <button
                    key={theme.id}
                    onClick={() => applyTheme(theme)}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      selectedTheme.id === theme.id
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-[#2a2e39] bg-[#131722] hover:border-[#363a45]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">{theme.name}</span>
                      {selectedTheme.id === theme.id && (
                        <CheckIcon className="w-5 h-5 text-blue-500" />
                      )}
                    </div>
                    <div className="flex gap-1">
                      {Object.values(theme.colors).slice(0, 4).map((color, idx) => (
                        <div
                          key={idx}
                          className="w-6 h-6 rounded border border-[#2a2e39]"
                          style={{ backgroundColor: color }}
                        />
                      ))}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Color Editor */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Customize Colors</h4>
              <div className="space-y-3">
                {Object.entries(selectedTheme.colors).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <label className="text-sm text-gray-400 capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={value}
                        onChange={(e) => handleColorChange(key as keyof Theme['colors'], e.target.value)}
                        className="w-12 h-8 rounded border border-[#2a2e39] cursor-pointer"
                      />
                      <input
                        type="text"
                        value={value}
                        onChange={(e) => handleColorChange(key as keyof Theme['colors'], e.target.value)}
                        className="w-24 px-2 py-1 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-4 border-t border-[#2a2e39]">
              <button
                onClick={saveCustomTheme}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors"
              >
                Apply Custom Theme
              </button>
              <button
                onClick={() => {
                  applyTheme(themes[0]);
                  setShowThemePanel(false);
                }}
                className="px-4 py-2 bg-[#2a2e39] hover:bg-[#363a45] text-gray-300 rounded font-medium transition-colors"
              >
                Reset to Default
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ThemeCustomization;

