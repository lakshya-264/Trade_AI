/**
 * Advanced Charting API Service
 * Integrates with backend /api/charting/* endpoints
 */

import { httpClient, APIResponse } from '../config/api';

// Charting API Response Interfaces
export interface TechnicalIndicatorsResponse {
  symbol: string;
  timeframe: string;
  timestamp: string;
  indicators: {
    sma_20?: number;
    sma_50?: number;
    ema_12?: number;
    ema_26?: number;
    rsi?: number;
    macd?: number;
    macd_signal?: number;
    macd_histogram?: number;
    bbands_upper?: number;
    bbands_middle?: number;
    bbands_lower?: number;
    volume_sma?: number;
    stochastic_k?: number;
    stochastic_d?: number;
    williams_r?: number;
    adx?: number;
    di_plus?: number;
    di_minus?: number;
    aroon_up?: number;
    aroon_down?: number;
    obv?: number;
    ad_line?: number;
    mfi?: number;
    vwap?: number;
  };
}

export interface PatternRecognitionResponse {
  symbol: string;
  timeframe: string;
  timestamp: string;
  patterns: Array<{
    pattern: string;
    type: 'bullish' | 'bearish' | 'neutral';
    confidence: number;
    description: string;
    action: 'BUY' | 'SELL' | 'HOLD';
    strength: 'weak' | 'moderate' | 'strong' | 'very_strong';
    timeframe: string;
    price: number;
    target?: number;
    stopLoss?: number;
    riskReward?: number;
  }>;
}

export interface VolumeProfileResponse {
  symbol: string;
  timeframe: string;
  timestamp: string;
  volume_profile: Array<{
    price_level: number;
    volume: number;
    percentage: number;
    poc?: boolean; // Point of Control
    vah?: boolean; // Value Area High
    val?: boolean; // Value Area Low
  }>;
  poc_price: number;
  vah_price: number;
  val_price: number;
}

export interface SupportResistanceResponse {
  symbol: string;
  timestamp: string;
  support_levels: Array<{
    level: number;
    strength: number;
    touches: number;
    last_touch: string;
  }>;
  resistance_levels: Array<{
    level: number;
    strength: number;
    touches: number;
    last_touch: string;
  }>;
  pivot_point: number;
  pivot_resistance_1: number;
  pivot_resistance_2: number;
  pivot_support_1: number;
  pivot_support_2: number;
}

export interface TradingSignalsResponse {
  symbol: string;
  timestamp: string;
  signals: Array<{
    signal: 'BUY' | 'SELL' | 'HOLD';
    strength: 'weak' | 'moderate' | 'strong' | 'very_strong';
    confidence: number;
    price: number;
    target?: number;
    stop_loss?: number;
    timeframe: string;
    reason: string;
    technical_indicators: {
      rsi: number;
      macd: number;
      sma20: number;
      sma50: number;
      volume: number;
      volatility: number;
    };
    risk_reward?: number;
  }>;
}

export interface CandlestickDataResponse {
  symbol: string;
  timeframe: string;
  timestamp: string;
  data: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    timestamp: number;
  }>;
}

export interface MarketOverviewResponse {
  market_status: 'open' | 'closed' | 'pre_market' | 'post_market';
  key_indices: Array<{
    index: string;
    display: string;
    last_price: number;
    change: number;
    change_percent: number;
    volume: number;
    timestamp: string;
  }>;
  sector_performance: Array<{
    sector: string;
    performance: number;
    trend: 'up' | 'down' | 'sideways';
    volume: 'high' | 'medium' | 'low';
    momentum: 'strong' | 'moderate' | 'weak' | 'neutral';
  }>;
  market_sentiment: {
    overall: 'bullish' | 'bearish' | 'neutral';
    fear_greed_index: number;
    put_call_ratio: number;
    vix_level: number;
  };
  last_updated: string;
}

export interface PortfolioPerformanceResponse {
  user_id: number;
  portfolio_return: number;
  benchmark_return: number;
  alpha: number;
  beta: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  performance_data: Array<{
    date: string;
    portfolio_value: number;
    benchmark_value: number;
    pnl: number;
    pnl_percent: number;
  }>;
  last_updated: string;
}

export interface DrawingTool {
  id: string;
  symbol: string;
  tool_type: 'line' | 'horizontal' | 'vertical' | 'rectangle' | 'fibonacci' | 'trend';
  points: Array<{ x: number; y: number }>;
  style: {
    color: string;
    width: number;
    dashArray?: string;
  };
  visible: boolean;
  locked: boolean;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  symbol: string;
  alert_type: 'price' | 'volume' | 'pattern' | 'indicator';
  condition: string;
  value: number;
  is_active: boolean;
  triggered_at?: string;
  created_at: string;
}

export interface ChartTheme {
  id: string;
  name: string;
  description: string;
  colors: {
    background: string;
    grid: string;
    text: string;
    bullish: string;
    bearish: string;
    volume: string;
    indicators: Record<string, string>;
  };
  is_default: boolean;
}

export interface ChartExportData {
  symbol: string;
  timeframe: string;
  format: 'png' | 'pdf' | 'csv' | 'json';
  data: any;
  timestamp: string;
}

// Charting API Service Class
class ChartingApiService {
  
  // Technical Indicators
  async getTechnicalIndicators(
    symbol: string,
    indicators: string[] = ['RSI', 'MACD', 'SMA', 'EMA', 'BBANDS'],
    timeframe: string = '1D'
  ): Promise<TechnicalIndicatorsResponse> {
    const response = await httpClient.get<TechnicalIndicatorsResponse>(
      `/charting/indicators/${symbol}`,
      { indicators: indicators.join(','), timeframe }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch technical indicators');
    }
    
    return response.data;
  }

  // Pattern Recognition
  async getPatternRecognition(
    symbol: string,
    patterns: string[] = ['doji', 'hammer', 'engulfing', 'morning_star', 'evening_star'],
    timeframe: string = '1D'
  ): Promise<PatternRecognitionResponse> {
    const response = await httpClient.get<PatternRecognitionResponse>(
      `/charting/pattern-recognition/${symbol}`,
      { patterns: patterns.join(','), timeframe }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch pattern recognition');
    }
    
    return response.data;
  }

  // Volume Profile
  async getVolumeProfile(
    symbol: string,
    timeframe: string = '1D',
    period: number = 30
  ): Promise<VolumeProfileResponse> {
    const response = await httpClient.get<VolumeProfileResponse>(
      `/charting/volume-profile/${symbol}`,
      { timeframe, period }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch volume profile');
    }
    
    return response.data;
  }

  // Support and Resistance
  async getSupportResistance(
    symbol: string,
    lookback: number = 50
  ): Promise<SupportResistanceResponse> {
    const response = await httpClient.get<SupportResistanceResponse>(
      `/charting/support-resistance/${symbol}`,
      { lookback }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch support/resistance levels');
    }
    
    return response.data;
  }

  // Trading Signals
  async getTradingSignals(
    symbol: string,
    signalType: string = 'comprehensive'
  ): Promise<TradingSignalsResponse> {
    const response = await httpClient.post<TradingSignalsResponse>(
      `/charting/trading-signals/${symbol}`,
      { signal_type: signalType }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch trading signals');
    }
    
    return response.data;
  }

  // Candlestick Data
  async getCandlestickData(
    symbol: string,
    timeframe: string = '1D',
    period: number = 100
  ): Promise<CandlestickDataResponse> {
    const response = await httpClient.get<CandlestickDataResponse>(
      `/charting/candlestick/${symbol}`,
      { timeframe, period }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch candlestick data');
    }
    
    return response.data;
  }

  // Market Overview
  async getMarketOverview(): Promise<MarketOverviewResponse> {
    const response = await httpClient.get<MarketOverviewResponse>('/charting/market-overview');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch market overview');
    }
    
    return response.data;
  }

  // Portfolio Performance
  async getPortfolioPerformance(
    userId: number,
    period: string = '1Y',
    benchmark: string = 'NIFTY50'
  ): Promise<PortfolioPerformanceResponse> {
    const response = await httpClient.get<PortfolioPerformanceResponse>(
      `/charting/portfolio-performance/${userId}`,
      { period, benchmark }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch portfolio performance');
    }
    
    return response.data;
  }

  // Drawing Tools
  async saveDrawingTool(toolData: Omit<DrawingTool, 'id' | 'created_at' | 'updated_at'>): Promise<DrawingTool> {
    const response = await httpClient.post<DrawingTool>('/charting/drawing-tools', toolData);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to save drawing tool');
    }
    
    return response.data;
  }

  async getDrawingTools(symbol: string): Promise<DrawingTool[]> {
    const response = await httpClient.get<DrawingTool[]>(`/charting/drawing-tools/${symbol}`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch drawing tools');
    }
    
    return response.data;
  }

  // Alerts
  async createAlert(alertData: Omit<Alert, 'id' | 'created_at' | 'triggered_at'>): Promise<Alert> {
    const response = await httpClient.post<Alert>('/charting/alerts', alertData);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to create alert');
    }
    
    return response.data;
  }

  async getAlerts(): Promise<Alert[]> {
    const response = await httpClient.get<Alert[]>('/charting/alerts');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch alerts');
    }
    
    return response.data;
  }

  async deleteAlert(alertId: string): Promise<void> {
    const response = await httpClient.delete<void>(`/charting/alerts/${alertId}`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to delete alert');
    }
  }

  // Chart Themes
  async getChartThemes(): Promise<ChartTheme[]> {
    const response = await httpClient.get<ChartTheme[]>('/charting/chart-themes');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to fetch chart themes');
    }
    
    return response.data;
  }

  // Chart Export
  async exportChart(
    symbol: string,
    format: 'png' | 'pdf' | 'csv' | 'json' = 'png',
    timeframe: string = '1D',
    period: number = 100
  ): Promise<ChartExportData> {
    const response = await httpClient.get<ChartExportData>(
      `/charting/export-chart/${symbol}`,
      { format, timeframe, period }
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to export chart');
    }
    
    return response.data;
  }
}

// Create and export service instance
export const chartingApi = new ChartingApiService();
export default chartingApi;
