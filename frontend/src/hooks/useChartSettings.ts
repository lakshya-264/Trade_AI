/**
 * Chart Settings Hook
 * Manages chart settings state and persistence
 */

import { useState, useEffect, useCallback } from 'react';
import { ChartSettings, DEFAULT_CHART_SETTINGS, Theme } from '../types/chartSettings';

const SETTINGS_STORAGE_KEY = 'chart_settings_v1';

export const useChartSettings = () => {
  const [settings, setSettings] = useState<ChartSettings>(() => {
    // Load from localStorage on mount
    try {
      const saved = localStorage.getItem(SETTINGS_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Merge with defaults to handle new fields
        return { ...DEFAULT_CHART_SETTINGS, ...parsed };
      }
    } catch (error) {
      console.error('Failed to load chart settings:', error);
    }
    return DEFAULT_CHART_SETTINGS;
  });

  // Save to localStorage whenever settings change
  useEffect(() => {
    try {
      const settingsToSave = {
        ...settings,
        lastUpdated: new Date().toISOString(),
      };
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settingsToSave));
    } catch (error) {
      console.error('Failed to save chart settings:', error);
    }
  }, [settings]);

  const updateSettings = useCallback((partialSettings: Partial<ChartSettings>) => {
    setSettings((prev) => ({
      ...prev,
      ...partialSettings,
    }));
  }, []);

  const updateTheme = useCallback((theme: Theme) => {
    setSettings((prev) => ({
      ...prev,
      theme,
      // Auto-update appearance colors from theme
      appearance: {
        ...prev.appearance,
        gridColor: theme.colors.grid,
        borderColor: theme.colors.grid,
      },
      candlestick: {
        ...prev.candlestick,
        upColor: theme.colors.candleUp,
        downColor: theme.colors.candleDown,
        wickUpColor: theme.colors.candleUp,
        wickDownColor: theme.colors.candleDown,
      },
    }));
  }, []);

  const updateAppearance = useCallback((appearance: Partial<ChartSettings['appearance']>) => {
    setSettings((prev) => ({
      ...prev,
      appearance: {
        ...prev.appearance,
        ...appearance,
      },
    }));
  }, []);

  const updateCandlestick = useCallback((candlestick: Partial<ChartSettings['candlestick']>) => {
    setSettings((prev) => ({
      ...prev,
      candlestick: {
        ...prev.candlestick,
        ...candlestick,
      },
    }));
  }, []);

  const updateScale = useCallback((scale: Partial<ChartSettings['scale']>) => {
    setSettings((prev) => ({
      ...prev,
      scale: {
        ...prev.scale,
        ...scale,
      },
    }));
  }, []);

  const updateIndicator = useCallback((indicatorKey: string, indicatorSettings: Partial<ChartSettings['indicators'][string]>) => {
    setSettings((prev) => ({
      ...prev,
      indicators: {
        ...prev.indicators,
        [indicatorKey]: {
          ...prev.indicators[indicatorKey],
          ...indicatorSettings,
        },
      },
    }));
  }, []);

  const resetToDefaults = useCallback(() => {
    setSettings(DEFAULT_CHART_SETTINGS);
  }, []);

  const exportSettings = useCallback((): string => {
    return JSON.stringify(settings, null, 2);
  }, [settings]);

  const importSettings = useCallback((settingsJson: string) => {
    try {
      const imported = JSON.parse(settingsJson);
      setSettings({ ...DEFAULT_CHART_SETTINGS, ...imported });
      return true;
    } catch (error) {
      console.error('Failed to import settings:', error);
      return false;
    }
  }, []);

  return {
    settings,
    updateSettings,
    updateTheme,
    updateAppearance,
    updateCandlestick,
    updateScale,
    updateIndicator,
    resetToDefaults,
    exportSettings,
    importSettings,
  };
};

