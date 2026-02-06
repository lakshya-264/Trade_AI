/**
 * Intelligent Trading API Service
 * Integrates with backend /api/intelligent-trading/* endpoints
 */

import { httpClient, APIResponse } from '../config/api';

// Intelligent Trading API Response Interfaces
export interface StockRecommendationsRequest {
  user_preferences: {
    risk_tolerance: 'low' | 'medium' | 'high';
    investment_horizon: 'short_term' | 'medium_term' | 'long_term';
    preferred_sectors: string[];
    market_cap_preference: 'small_cap' | 'mid_cap' | 'large_cap';
    volatility_tolerance: 'low' | 'medium' | 'high';
    max_positions: number;
    min_confidence: number;
  };
  market_conditions?: {
    market_trend: 'bullish' | 'bearish' | 'sideways';
    volatility_level: 'low' | 'medium' | 'high';
    sector_rotation: string[];
  };
}

export interface StockRecommendationsResponse {
  recommendations: Array<{
    symbol: string;
    name: string;
    sector: string;
    current_price: number;
    recommendation: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    composite_score: number;
    price_target: number;
    stop_loss: number;
    time_horizon: string;
    reasoning: string;
    timing_recommendation: {
      action: string;
      reason: string;
      next_opportunity?: string;
      confidence?: string;
    };
    risk_level: 'low' | 'medium' | 'high';
    position_sizing: {
      suggested_quantity: number;
      position_value: number;
      risk_percentage: number;
      max_loss: number;
    };
    technical_analysis: {
      trend: string;
      momentum: string;
      volatility: string;
      volume_profile: string;
    };
    fundamental_analysis: {
      pe_ratio: number;
      pb_ratio: number;
      debt_to_equity: number;
      roe: number;
      revenue_growth: number;
    };
    sentiment_analysis: {
      news_sentiment: string;
      social_sentiment: string;
      analyst_ratings: string;
    };
  }>;
  market_insights: {
    overall_sentiment: 'bullish' | 'bearish' | 'neutral';
    sector_rotation: string[];
    volatility_level: 'low' | 'medium' | 'high';
    market_trend: 'up' | 'down' | 'sideways';
    key_themes: string[];
    risk_factors: string[];
  };
  portfolio_suggestions: {
    suggested_allocation: Record<string, number>;
    rebalancing_needed: boolean;
    risk_adjustment: string;
  };
  last_updated: string;
}

export interface OptimalTimingResponse {
  symbol: string;
  current_price: number;
  optimal_entry: {
    price_range: {
      min: number;
      max: number;
    };
    confidence: number;
    reasoning: string;
    timeframe: string;
  };
  optimal_exit: {
    price_range: {
      min: number;
      max: number;
    };
    confidence: number;
    reasoning: string;
    timeframe: string;
  };
  market_timing: {
    current_phase: 'accumulation' | 'markup' | 'distribution' | 'markdown';
    next_phase_probability: number;
    phase_duration_estimate: string;
  };
  technical_signals: {
    entry_signals: string[];
    exit_signals: string[];
    risk_signals: string[];
  };
  fundamental_timing: {
    earnings_calendar: Array<{
      event: string;
      date: string;
      impact: 'positive' | 'negative' | 'neutral';
    }>;
    dividend_calendar: Array<{
      event: string;
      date: string;
      amount: number;
    }>;
  };
  sentiment_timing: {
    news_cycle: 'positive' | 'negative' | 'neutral';
    social_sentiment_trend: 'improving' | 'deteriorating' | 'stable';
    analyst_upgrades_downgrades: Array<{
      analyst: string;
      action: 'upgrade' | 'downgrade' | 'maintain';
      target_price: number;
      date: string;
    }>;
  };
  risk_assessment: {
    timing_risk: 'low' | 'medium' | 'high';
    market_risk: 'low' | 'medium' | 'high';
    sector_risk: 'low' | 'medium' | 'high';
    company_specific_risk: 'low' | 'medium' | 'high';
  };
  last_updated: string;
}

export interface MarketIntelligenceResponse {
  market_overview: {
    current_status: 'open' | 'closed' | 'pre_market' | 'post_market';
    overall_sentiment: 'bullish' | 'bearish' | 'neutral';
    market_trend: 'up' | 'down' | 'sideways';
    volatility_level: 'low' | 'medium' | 'high';
  };
  sector_analysis: Array<{
    sector: string;
    performance: number;
    trend: 'up' | 'down' | 'sideways';
    momentum: 'strong' | 'moderate' | 'weak';
    key_drivers: string[];
    top_performers: string[];
    underperformers: string[];
  }>;
  market_sentiment: {
    fear_greed_index: number;
    put_call_ratio: number;
    vix_level: number;
    investor_sentiment: 'extreme_fear' | 'fear' | 'neutral' | 'greed' | 'extreme_greed';
  };
  economic_indicators: {
    gdp_growth: number;
    inflation_rate: number;
    interest_rates: number;
    currency_strength: string;
    unemployment_rate: number;
  };
  market_events: Array<{
    event: string;
    date: string;
    impact: 'high' | 'medium' | 'low';
    description: string;
  }>;
  ai_insights: {
    market_outlook: string;
    key_themes: string[];
    opportunities: string[];
    risks: string[];
    sector_rotation_signals: string[];
  };
  trading_opportunities: Array<{
    type: 'momentum' | 'mean_reversion' | 'breakout' | 'sector_rotation';
    symbol: string;
    opportunity: string;
    confidence: number;
    timeframe: string;
    risk_level: 'low' | 'medium' | 'high';
  }>;
  last_updated: string;
}

export interface PortfolioOptimizationRequest {
  current_portfolio: Array<{
    symbol: string;
    quantity: number;
    current_price: number;
    target_allocation: number;
  }>;
  constraints: {
    max_positions: number;
    max_sector_allocation: number;
    max_single_stock_allocation: number;
    min_liquidity_requirement: number;
  };
  objectives: {
    target_return: number;
    max_risk_tolerance: number;
    investment_horizon: 'short_term' | 'medium_term' | 'long_term';
    rebalancing_frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  };
  market_conditions: {
    expected_volatility: 'low' | 'medium' | 'high';
    market_trend: 'bullish' | 'bearish' | 'sideways';
    sector_rotation: string[];
  };
}

export interface PortfolioOptimizationResponse {
  optimized_portfolio: Array<{
    symbol: string;
    current_allocation: number;
    recommended_allocation: number;
    recommended_quantity: number;
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    reasoning: string;
  }>;
  portfolio_metrics: {
    expected_return: number;
    expected_volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
    var_95: number;
    diversification_ratio: number;
  };
  risk_analysis: {
    portfolio_beta: number;
    sector_concentration: Record<string, number>;
    single_stock_risks: Array<{
      symbol: string;
      risk_contribution: number;
      concentration_risk: 'low' | 'medium' | 'high';
    }>;
    correlation_analysis: Record<string, Record<string, number>>;
  };
  rebalancing_recommendations: {
    rebalancing_needed: boolean;
    priority_trades: Array<{
      symbol: string;
      action: 'BUY' | 'SELL';
      quantity: number;
      priority: 'high' | 'medium' | 'low';
      reasoning: string;
    }>;
    estimated_transaction_costs: number;
    tax_implications: string;
  };
  scenario_analysis: {
    bull_market_scenario: {
      expected_return: number;
      probability: number;
      key_drivers: string[];
    };
    bear_market_scenario: {
      expected_return: number;
      probability: number;
      risk_factors: string[];
    };
    sideways_market_scenario: {
      expected_return: number;
      probability: number;
      strategy: string;
    };
  };
  last_updated: string;
}

export interface TradingSignalsResponse {
  signals: Array<{
    symbol: string;
    signal_type: 'BUY' | 'SELL' | 'HOLD';
    strength: 'weak' | 'moderate' | 'strong' | 'very_strong';
    confidence: number;
    price: number;
    target?: number;
    stop_loss?: number;
    timeframe: string;
    reasoning: string;
    technical_indicators: {
      rsi: number;
      macd: number;
      sma20: number;
      sma50: number;
      volume: number;
      volatility: number;
      change_percent?: number;
      volume_ratio?: number;
      bb_position?: number;
    };
    risk_reward?: number;
    entry_strategy: string;
    exit_strategy: string;
    position_sizing: {
      suggested_quantity: number;
      position_value: number;
      risk_percentage: number;
    };
  }>;
  market_context: {
    overall_sentiment: 'bullish' | 'bearish' | 'neutral';
    volatility_level: 'low' | 'medium' | 'high';
    sector_rotation: string[];
  };
  last_updated: string;
}

// Intelligent Trading API Service Class
class IntelligentTradingApiService {
  
  // Stock Recommendations
  async getStockRecommendations(request: StockRecommendationsRequest): Promise<StockRecommendationsResponse> {
    const response = await httpClient.post<StockRecommendationsResponse>('/intelligent-trading/stock-recommendations', request);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get stock recommendations');
    }
    
    return response.data;
  }

  // Optimal Timing
  async getOptimalTiming(symbol: string): Promise<OptimalTimingResponse> {
    const response = await httpClient.get<OptimalTimingResponse>(`/intelligent-trading/optimal-timing/${symbol}`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get optimal timing');
    }
    
    return response.data;
  }

  // Market Intelligence
  async getMarketIntelligence(): Promise<MarketIntelligenceResponse> {
    const response = await httpClient.get<MarketIntelligenceResponse>('/intelligent-trading/market-intelligence');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get market intelligence');
    }
    
    return response.data;
  }

  // Portfolio Optimization
  async optimizePortfolio(request: PortfolioOptimizationRequest): Promise<PortfolioOptimizationResponse> {
    const response = await httpClient.post<PortfolioOptimizationResponse>('/intelligent-trading/portfolio-optimization', request);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to optimize portfolio');
    }
    
    return response.data;
  }

  // Trading Signals
  async getTradingSignals(): Promise<TradingSignalsResponse> {
    const response = await httpClient.get<TradingSignalsResponse>('/intelligent-trading/signals');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get trading signals');
    }
    
    return response.data;
  }
}

// Create and export service instance
export const intelligentTradingApi = new IntelligentTradingApiService();
export default intelligentTradingApi;
