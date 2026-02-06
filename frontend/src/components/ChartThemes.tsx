import React, { useState, useEffect } from 'react';
import { 
  PaintBrushIcon,
  SunIcon,
  MoonIcon,
  EyeIcon,
  EyeSlashIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';

interface ChartTheme {
  id: string;
  name: string;
  description: string;
  colors: {
    background: string;
    grid: string;
    text: string;
    primary: string;
    success: string;
    danger: string;
    warning: string;
    muted: string;
  };
  chart: {
    candlestick: {
      bullish: string;
      bearish: string;
      wick: string;
    };
    line: {
      color: string;
      width: number;
    };
    volume: {
      color: string;
      opacity: number;
    };
  };
  indicators: {
    sma20: string;
    sma50: string;
    ema12: string;
    rsi: string;
    macd: string;
    bollinger: string;
  };
}

interface ChartThemesProps {
  onThemeChange?: (theme: ChartTheme) => void;
  className?: string;
}

const ChartThemes: React.FC<ChartThemesProps> = ({
  onThemeChange,
  className = ''
}) => {
  const [selectedTheme, setSelectedTheme] = useState<string>('dark');
  const [showThemes, setShowThemes] = useState(true);
  const [customTheme, setCustomTheme] = useState<Partial<ChartTheme>>({});

  const themes: ChartTheme[] = [
    {
      id: 'dark',
      name: 'Dark Professional',
      description: 'Professional dark theme for trading',
      colors: {
        background: '#0F172A',
        grid: '#334155',
        text: '#F8FAFC',
        primary: '#3B82F6',
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
        muted: '#64748B'
      },
      chart: {
        candlestick: {
          bullish: '#10B981',
          bearish: '#EF4444',
          wick: '#F8FAFC'
        },
        line: {
          color: '#3B82F6',
          width: 2
        },
        volume: {
          color: '#64748B',
          opacity: 0.3
        }
      },
      indicators: {
        sma20: '#3B82F6',
        sma50: '#10B981',
        ema12: '#F59E0B',
        rsi: '#8B5CF6',
        macd: '#EF4444',
        bollinger: '#06B6D4'
      }
    },
    {
      id: 'light',
      name: 'Light Professional',
      description: 'Clean light theme for daytime trading',
      colors: {
        background: '#FFFFFF',
        grid: '#E2E8F0',
        text: '#1E293B',
        primary: '#3B82F6',
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
        muted: '#64748B'
      },
      chart: {
        candlestick: {
          bullish: '#10B981',
          bearish: '#EF4444',
          wick: '#1E293B'
        },
        line: {
          color: '#3B82F6',
          width: 2
        },
        volume: {
          color: '#64748B',
          opacity: 0.3
        }
      },
      indicators: {
        sma20: '#3B82F6',
        sma50: '#10B981',
        ema12: '#F59E0B',
        rsi: '#8B5CF6',
        macd: '#EF4444',
        bollinger: '#06B6D4'
      }
    },
    {
      id: 'neon',
      name: 'Neon Cyber',
      description: 'High contrast neon theme for night trading',
      colors: {
        background: '#000000',
        grid: '#00FF00',
        text: '#00FF00',
        primary: '#00FFFF',
        success: '#00FF00',
        danger: '#FF0000',
        warning: '#FFFF00',
        muted: '#808080'
      },
      chart: {
        candlestick: {
          bullish: '#00FF00',
          bearish: '#FF0000',
          wick: '#00FFFF'
        },
        line: {
          color: '#00FFFF',
          width: 2
        },
        volume: {
          color: '#808080',
          opacity: 0.5
        }
      },
      indicators: {
        sma20: '#00FFFF',
        sma50: '#00FF00',
        ema12: '#FFFF00',
        rsi: '#FF00FF',
        macd: '#FF0000',
        bollinger: '#00FFFF'
      }
    },
    {
      id: 'minimal',
      name: 'Minimal Clean',
      description: 'Minimalist theme with subtle colors',
      colors: {
        background: '#FAFAFA',
        grid: '#E5E7EB',
        text: '#374151',
        primary: '#6366F1',
        success: '#059669',
        danger: '#DC2626',
        warning: '#D97706',
        muted: '#9CA3AF'
      },
      chart: {
        candlestick: {
          bullish: '#059669',
          bearish: '#DC2626',
          wick: '#374151'
        },
        line: {
          color: '#6366F1',
          width: 1.5
        },
        volume: {
          color: '#9CA3AF',
          opacity: 0.2
        }
      },
      indicators: {
        sma20: '#6366F1',
        sma50: '#059669',
        ema12: '#D97706',
        rsi: '#7C3AED',
        macd: '#DC2626',
        bollinger: '#0891B2'
      }
    },
    {
      id: 'trading',
      name: 'Trading Pro',
      description: 'Professional trading theme with optimal contrast',
      colors: {
        background: '#1A1A1A',
        grid: '#333333',
        text: '#FFFFFF',
        primary: '#00D4FF',
        success: '#00FF88',
        danger: '#FF3366',
        warning: '#FFB800',
        muted: '#666666'
      },
      chart: {
        candlestick: {
          bullish: '#00FF88',
          bearish: '#FF3366',
          wick: '#FFFFFF'
        },
        line: {
          color: '#00D4FF',
          width: 2
        },
        volume: {
          color: '#666666',
          opacity: 0.4
        }
      },
      indicators: {
        sma20: '#00D4FF',
        sma50: '#00FF88',
        ema12: '#FFB800',
        rsi: '#FF6B9D',
        macd: '#FF3366',
        bollinger: '#00D4FF'
      }
    }
  ];

  const [currentTheme, setCurrentTheme] = useState<ChartTheme>(themes[0]);

  useEffect(() => {
    const theme = themes.find(t => t.id === selectedTheme) || themes[0];
    setCurrentTheme(theme);
    onThemeChange?.(theme);
  }, [selectedTheme, onThemeChange]);

  const handleThemeSelect = (themeId: string) => {
    setSelectedTheme(themeId);
  };

  const handleCustomizeTheme = (property: string, value: string) => {
    const newCustomTheme = {
      ...customTheme,
      [property]: value
    };
    setCustomTheme(newCustomTheme);
  };

  const applyCustomTheme = () => {
    if (Object.keys(customTheme).length > 0) {
      const customThemeData: ChartTheme = {
        id: 'custom',
        name: 'Custom Theme',
        description: 'Your custom theme',
        ...themes.find(t => t.id === selectedTheme),
        ...customTheme
      } as ChartTheme;
      
      onThemeChange?.(customThemeData);
    }
  };

  const resetCustomTheme = () => {
    setCustomTheme({});
    const theme = themes.find(t => t.id === selectedTheme) || themes[0];
    onThemeChange?.(theme);
  };

  return (
    <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-foreground">Chart Themes</h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-success-500" />
            <span className="text-sm text-muted-foreground">
              {currentTheme.name}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowThemes(!showThemes)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
            title="Toggle Themes"
          >
            {showThemes ? <EyeIcon className="h-5 w-5" /> : <EyeSlashIcon className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Theme Selection */}
      {showThemes && (
        <div className="space-y-4">
          {/* Preset Themes */}
          <div>
            <h4 className="text-sm font-medium text-foreground mb-3">Preset Themes</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {themes.map((theme) => (
                <div
                  key={theme.id}
                  onClick={() => handleThemeSelect(theme.id)}
                  className={cn(
                    "p-4 rounded-lg border cursor-pointer transition-colors",
                    selectedTheme === theme.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/30'
                  )}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="flex space-x-1">
                      <div
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: theme.colors.primary }}
                      />
                      <div
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: theme.colors.success }}
                      />
                      <div
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: theme.colors.danger }}
                      />
                    </div>
                    <h5 className="font-medium text-foreground">{theme.name}</h5>
                  </div>
                  <p className="text-sm text-muted-foreground">{theme.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Theme Preview */}
          <div>
            <h4 className="text-sm font-medium text-foreground mb-3">Theme Preview</h4>
            <div
              className="p-4 rounded-lg border"
              style={{
                backgroundColor: currentTheme.colors.background,
                color: currentTheme.colors.text,
                borderColor: currentTheme.colors.grid
              }}
            >
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span style={{ color: currentTheme.colors.muted }}>Background:</span>
                  <div
                    className="w-8 h-4 rounded inline-block ml-2"
                    style={{ backgroundColor: currentTheme.colors.background }}
                  />
                </div>
                <div>
                  <span style={{ color: currentTheme.colors.muted }}>Primary:</span>
                  <div
                    className="w-8 h-4 rounded inline-block ml-2"
                    style={{ backgroundColor: currentTheme.colors.primary }}
                  />
                </div>
                <div>
                  <span style={{ color: currentTheme.colors.muted }}>Success:</span>
                  <div
                    className="w-8 h-4 rounded inline-block ml-2"
                    style={{ backgroundColor: currentTheme.colors.success }}
                  />
                </div>
                <div>
                  <span style={{ color: currentTheme.colors.muted }}>Danger:</span>
                  <div
                    className="w-8 h-4 rounded inline-block ml-2"
                    style={{ backgroundColor: currentTheme.colors.danger }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Custom Theme Options */}
          <div>
            <h4 className="text-sm font-medium text-foreground mb-3">Customize Theme</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Background</label>
                <input
                  type="color"
                  value={customTheme.colors?.background || currentTheme.colors.background}
                  onChange={(e) => handleCustomizeTheme('colors.background', e.target.value)}
                  className="w-full h-8 rounded border border-border"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Primary</label>
                <input
                  type="color"
                  value={customTheme.colors?.primary || currentTheme.colors.primary}
                  onChange={(e) => handleCustomizeTheme('colors.primary', e.target.value)}
                  className="w-full h-8 rounded border border-border"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Success</label>
                <input
                  type="color"
                  value={customTheme.colors?.success || currentTheme.colors.success}
                  onChange={(e) => handleCustomizeTheme('colors.success', e.target.value)}
                  className="w-full h-8 rounded border border-border"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Danger</label>
                <input
                  type="color"
                  value={customTheme.colors?.danger || currentTheme.colors.danger}
                  onChange={(e) => handleCustomizeTheme('colors.danger', e.target.value)}
                  className="w-full h-8 rounded border border-border"
                />
              </div>
            </div>
            <div className="flex space-x-2 mt-3">
              <button
                onClick={applyCustomTheme}
                className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90"
              >
                Apply Custom
              </button>
              <button
                onClick={resetCustomTheme}
                className="px-3 py-1 bg-muted text-muted-foreground rounded text-sm hover:bg-muted/80"
              >
                Reset
              </button>
            </div>
          </div>

          {/* Chart Type Customization */}
          <div>
            <h4 className="text-sm font-medium text-foreground mb-3">Chart Customization</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Candlestick Bullish</label>
                <input
                  type="color"
                  value={customTheme.chart?.candlestick?.bullish || currentTheme.chart.candlestick.bullish}
                  onChange={(e) => handleCustomizeTheme('chart.candlestick.bullish', e.target.value)}
                  className="w-full h-8 rounded border border-border"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Candlestick Bearish</label>
                <input
                  type="color"
                  value={customTheme.chart?.candlestick?.bearish || currentTheme.chart.candlestick.bearish}
                  onChange={(e) => handleCustomizeTheme('chart.candlestick.bearish', e.target.value)}
                  className="w-full h-8 rounded border border-border"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Line Color</label>
                <input
                  type="color"
                  value={customTheme.chart?.line?.color || currentTheme.chart.line.color}
                  onChange={(e) => handleCustomizeTheme('chart.line.color', e.target.value)}
                  className="w-full h-8 rounded border border-border"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChartThemes;

