/**
 * Chart Settings Types
 * Comprehensive type definitions for chart customization
 */

export interface Theme {
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

export interface ChartAppearanceSettings {
  gridVisible: boolean;
  gridColor: string;
  gridStyle: 'solid' | 'dashed' | 'dotted';
  gridOpacity: number;
  crosshairVisible: boolean;
  crosshairColor: string;
  crosshairStyle: 'solid' | 'dashed' | 'dotted';
  borderVisible: boolean;
  borderColor: string;
}

export interface CandlestickSettings {
  upColor: string;
  downColor: string;
  wickUpColor: string;
  wickDownColor: string;
  style: 'candlestick' | 'hollow' | 'line' | 'area' | 'bars';
  borderVisible: boolean;
  wickWidth: number;
  bodyWidth: number;
}

export interface ScaleSettings {
  priceScalePosition: 'left' | 'right';
  priceFormat: {
    type: 'price' | 'volume';
    precision: number;
    minMove: number;
  };
  timeVisible: boolean;
  timeFormat: '12h' | '24h' | 'DD/MM' | 'MM/DD';
  autoScale: boolean;
  scaleMargins: {
    top: number;
    bottom: number;
  };
  fontSize: number;
}

export interface IndicatorSettings {
  [key: string]: {
    enabled: boolean;
    color: string;
    lineWidth: number;
    period?: number;
    style?: 'solid' | 'dashed' | 'dotted';
  };
}

export interface ChartSettings {
  theme: Theme;
  appearance: ChartAppearanceSettings;
  candlestick: CandlestickSettings;
  scale: ScaleSettings;
  indicators: IndicatorSettings;
  version: string;
  lastUpdated: string;
}

export const DEFAULT_CHART_SETTINGS: ChartSettings = {
  theme: {
    id: 'dark',
    name: 'Dark Professional',
    colors: {
      background: '#131722',
      grid: '#1e222d',
      text: '#d1d4dc',
      primary: '#3B82F6',
      success: '#10B981',
      danger: '#EF4444',
      candleUp: '#26a69a',
      candleDown: '#ef5350',
    },
  },
  appearance: {
    gridVisible: true,
    gridColor: '#1e222d',
    gridStyle: 'solid',
    gridOpacity: 1.0,
    crosshairVisible: true,
    crosshairColor: '#758696',
    crosshairStyle: 'dashed',
    borderVisible: true,
    borderColor: '#2a2e39',
  },
  candlestick: {
    upColor: '#26a69a',
    downColor: '#ef5350',
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
    style: 'candlestick',
    borderVisible: false,
    wickWidth: 1,
    bodyWidth: 1,
  },
  scale: {
    priceScalePosition: 'right',
    priceFormat: {
      type: 'price',
      precision: 2,
      minMove: 0.01,
    },
    timeVisible: true,
    timeFormat: '24h',
    autoScale: true,
    scaleMargins: {
      top: 0.1,
      bottom: 0.2,
    },
    fontSize: 12,
  },
  indicators: {},
  version: '1.0.0',
  lastUpdated: new Date().toISOString(),
};

