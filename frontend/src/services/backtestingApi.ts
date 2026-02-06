/**
 * Backtesting API
 * Run historical backtests and analyze strategy performance
 */

import { httpClient } from '../config/api';

export interface BacktestRequest {
  symbol: string;
  strategy_type: 'sd_zones' | 'sr_levels' | 'structure_breaks';
  start_date?: string;
  end_date?: string;
  entry_threshold: number;
  stop_loss: number;
  take_profit: number;
}

export interface Trade {
  entry_time: string | number;
  entry_price: number;
  exit_time: string | number;
  exit_price: number;
  direction: 'long' | 'short';
  result: 'win' | 'loss';
  pnl_percent: number;
  zone_type?: string;
  level_type?: string;
}

export interface BacktestMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  total_return_percent: number;
  final_capital: number;
  max_consecutive_wins?: number;
  max_consecutive_losses?: number;
  // Professional metrics (NEW!)
  max_drawdown: number;
  avg_drawdown: number;
  max_dd_duration?: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  expectancy: number;
  recovery_factor: number;
}

export interface BacktestResponse {
  success: boolean;
  symbol: string;
  strategy: string;
  metrics: BacktestMetrics;
  trades: Trade[];
  equity_curve: Array<{
    date: string | number;
    equity: number;
  }>;
}

export interface ZoneSuccessRateResponse {
  success: boolean;
  symbol: string;
  timeframe: string;
  results: {
    demand_zones: {
      total_touches: number;
      successful_bounces: number;
      success_rate: number;
    };
    supply_zones: {
      total_touches: number;
      successful_rejections: number;
      success_rate: number;
    };
    overall_success_rate: number;
  };
  timestamp: string;
}

class BacktestingApi {
  private readonly baseUrl = '/api/backtesting';

  /**
   * Run a backtest
   */
  async runBacktest(request: BacktestRequest): Promise<BacktestResponse> {
    const response = await httpClient.post<BacktestResponse>(`${this.baseUrl}/run`, request);
    
    // Handle different response structures
    if (!response.success) {
      throw new Error(response.error || 'Backtest failed');
    }
    
    // Extract the actual BacktestResponse data
    // httpClient.post returns APIResponse<T>, so data is in response.data
    let backtestData: any = null;
    
    if (response.data) {
      // Wrapped in APIResponse structure (normal case)
      backtestData = response.data;
    } else if ('trades' in response && 'symbol' in response && 'metrics' in response) {
      // Direct BacktestResponse (unlikely but handle it)
      backtestData = response as unknown as BacktestResponse;
    } else {
      throw new Error('Invalid backtest response format: missing data');
    }
    
    if (!backtestData || typeof backtestData !== 'object') {
      throw new Error('Backtest returned empty or invalid response');
    }
    
    // Ensure trades array exists and return properly typed response
    const validatedResponse: BacktestResponse = {
      success: backtestData.success !== false,
      symbol: backtestData.symbol || request.symbol,
      strategy: backtestData.strategy || request.strategy_type,
      metrics: backtestData.metrics || {
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        win_rate: 0,
        avg_win: 0,
        avg_loss: 0,
        profit_factor: 0,
        total_return_percent: 0,
        final_capital: 0,
        max_drawdown: 0,
        avg_drawdown: 0,
        sharpe_ratio: 0,
        sortino_ratio: 0,
        calmar_ratio: 0,
        expectancy: 0,
        recovery_factor: 0,
      },
      trades: Array.isArray(backtestData.trades) ? backtestData.trades : [],
      equity_curve: Array.isArray(backtestData.equity_curve) ? backtestData.equity_curve : [],
    };
    
    return validatedResponse;
  }

  /**
   * Calculate zone success rate
   */
  async calculateZoneSuccessRate(
    symbol: string,
    timeframe: string = '1d',
    lookbackDays: number = 90
  ): Promise<ZoneSuccessRateResponse> {
    const response = await httpClient.post<ZoneSuccessRateResponse>(`${this.baseUrl}/zone-success-rate`, {
      symbol,
      timeframe,
      lookback_days: lookbackDays,
    });
    return response.data!;
  }

  /**
   * Calculate pattern win rate
   */
  async calculatePatternWinrate(
    symbol: string,
    patternType: string,
    lookbackDays: number = 90
  ): Promise<any> {
    const response = await httpClient.post<any>(`${this.baseUrl}/pattern-winrate`, {
      symbol,
      pattern_type: patternType,
      lookback_days: lookbackDays,
    });
    return response.data!;
  }

  /**
   * Get available strategies
   */
  async getAvailableStrategies(): Promise<any> {
    const response = await httpClient.get<any>(`${this.baseUrl}/strategies`);
    return response.data!;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<any> {
    const response = await httpClient.get<any>(`${this.baseUrl}/health`);
    return response.data!;
  }
}

export const backtestingApi = new BacktestingApi();

