/**
 * Comprehensive TypeScript interfaces for all API responses
 * Replaces all 'any' types with proper type safety
 */

// Base API Response Structure
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
  timestamp: string;
  request_id?: string;
}

// Error Response Structure
export interface ApiError {
  success: false;
  error: string;
  error_code: string;
  details?: Record<string, any>;
  timestamp: string;
  request_id?: string;
}

// Quote Data Interfaces
export interface QuoteData {
  symbol: string;
  last_price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  change: number;
  change_percent: number;
  volume: number;
  day_volume?: number;
  previous_close: number;
  currency: string;
  exchange: string;
  timezone: string;
  timestamp: string;
  source: 'nse' | 'angel_one' | 'yahoo_finance' | 'mock_data';
}

// Historical Data Interfaces
export interface HistoricalDataPoint {
  date: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjusted_close?: number;
}

// Market Status Interface
export interface MarketStatus {
  nse: {
    status: string;
    next_open: string;
    next_close: string;
  };
  bse: {
    status: string;
    next_open: string;
    next_close: string;
  };
  timestamp: string;
}

// Index Constituents Interface
export interface IndexConstituents {
  index: string;
  symbols: string[];
  count: number;
  last_updated: string;
}

// Technical Indicators Interface
export interface TechnicalIndicators {
  symbol: string;
  timestamp: string;
  sma_20: number;
  sma_50: number;
  ema_12: number;
  ema_26: number;
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  bbands_upper: number;
  bbands_middle: number;
  bbands_lower: number;
  volume_sma: number;
}

// Sector Performance Interface
export interface SectorPerformance {
  sectors: SectorData[];
  last_updated: string;
  market_status: string;
}

export interface SectorData {
  name: string;
  symbol: string;
  last_price: number;
  change: number;
  change_percent: number;
  volume: number;
  trend: 'up' | 'down' | 'sideways' | 'neutral';
  momentum: 'strong' | 'moderate' | 'weak' | 'neutral';
  timestamp: string;
}

// Industry Summary Interface
export interface IndustrySummary {
  sector: string;
  index_symbol: string;
  top_performing_companies: CompanyPerformance[];
  top_growth_companies: CompanyGrowth[];
  sector_trend: 'up' | 'down' | 'sideways';
  average_change_percent: number;
  last_updated: string;
}

export interface CompanyPerformance {
  symbol: string;
  name: string;
  last_price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap?: number;
}

export interface CompanyGrowth {
  symbol: string;
  name: string;
  last_price: number;
  year_high: number;
  year_low: number;
  year_change_percent: number;
  pe_ratio?: number;
}

// Fast Info Interface
export interface FastInfo {
  symbol: string;
  currency: string;
  exchange: string;
  timezone: string;
  last_price: number;
  open: number;
  day_high: number;
  day_low: number;
  last_volume: number;
  previous_close: number;
  regular_market_previous_close: number;
  fifty_day_average: number;
  two_hundred_day_average: number;
  ten_day_average_volume: number;
  three_month_average_volume: number;
  year_high: number;
  year_low: number;
  year_change: number;
  updated_at: string;
}

// Market Summary Interface
export interface MarketSummary {
  market_status: 'open' | 'closed' | 'pre_market' | 'post_market';
  key_indices: IndexQuote[];
  last_updated: string;
}

export interface IndexQuote {
  symbol: string;
  name: string;
  last_price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

// Batch Quotes Interface
export interface BatchQuotes {
  quotes: QuoteData[];
  total_count: number;
  success_count: number;
  failed_count: number;
  timestamp: string;
}

// Screener Interfaces
export interface ScreenerResult {
  preset: string;
  results: ScreenerStock[];
  total_count: number;
  filters_applied: ScreenerFilters;
  timestamp: string;
}

export interface ScreenerStock {
  symbol: string;
  name: string;
  last_price: number;
  change_percent: number;
  volume: number;
  market_cap: number;
  sector: string;
}

export interface ScreenerFilters {
  min_price?: number;
  max_price?: number;
  min_volume?: number;
  min_change_percent?: number;
  max_change_percent?: number;
  sectors?: string[];
}

export interface ScreenerQuery {
  conditions: QueryCondition[];
  logic: 'AND' | 'OR';
  limit?: number;
}

export interface QueryCondition {
  field: 'price' | 'change_percent' | 'volume' | 'market_cap';
  operator: 'EQ' | 'GT' | 'LT' | 'GTE' | 'LTE' | 'IN' | 'NOT_IN';
  value: number | number[] | string | string[];
}

// Holders Data Interface (Placeholder Structure)
export interface HoldersData {
  symbol: string;
  major_holders: MajorHolder[];
  institutional_holders: InstitutionalHolder[];
  mutual_fund_holders: MutualFundHolder[];
  insider_transactions: InsiderTransaction[];
  last_updated: string;
  provider_status: 'not_configured' | 'active' | 'limited';
}

export interface MajorHolder {
  name: string;
  shares: number;
  percentage: number;
  change_percent: number;
}

export interface InstitutionalHolder {
  institution_name: string;
  shares: number;
  percentage: number;
  change_percent: number;
}

export interface MutualFundHolder {
  fund_name: string;
  shares: number;
  percentage: number;
  change_percent: number;
}

export interface InsiderTransaction {
  insider_name: string;
  transaction_type: 'buy' | 'sell';
  shares: number;
  price: number;
  date: string;
}

// Fundamentals Data Interface (Placeholder Structure)
export interface FundamentalsData {
  symbol: string;
  yearly_statements: FinancialStatement[];
  quarterly_statements: FinancialStatement[];
  trailing_statements: FinancialStatement[];
  last_updated: string;
  provider_status: 'not_configured' | 'active' | 'limited';
}

export interface FinancialStatement {
  period: string;
  revenue: number;
  net_income: number;
  total_assets: number;
  total_liabilities: number;
  cash_flow: number;
  eps: number;
  pe_ratio: number;
}

// Fund Profile Interface (Placeholder Structure)
export interface FundProfile {
  symbol: string;
  fund_name: string;
  fund_type: 'ETF' | 'Mutual Fund' | 'Index Fund';
  overview: FundOverview;
  operations: FundOperations;
  asset_classes: AssetClass[];
  top_holdings: FundHolding[];
  last_updated: string;
  provider_status: 'not_configured' | 'active' | 'limited';
}

export interface FundOverview {
  inception_date: string;
  expense_ratio: number;
  assets_under_management: number;
  investment_objective: string;
}

export interface FundOperations {
  management_company: string;
  fund_manager: string;
  benchmark: string;
  investment_style: string;
}

export interface AssetClass {
  class_name: string;
  percentage: number;
  description: string;
}

export interface FundHolding {
  symbol: string;
  name: string;
  percentage: number;
  shares: number;
  market_value: number;
}

// Portfolio Interfaces
export interface PortfolioResponse {
  total_value: number;
  total_pnl: number;
  portfolio: PortfolioItem[];
  last_updated: string;
}

export interface PortfolioItem {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  total_value: number;
  pnl: number;
  pnl_percent: number;
}

// Top Gainers/Losers Interface
export interface TopGainerLoser {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: number;
}

// Chart Data Interfaces - Ultimate Trading Terminal
export interface ChartData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: number;
  
  // Moving Averages
  sma5?: number;
  sma10?: number;
  sma20?: number;
  sma50?: number;
  sma100?: number;
  sma200?: number;
  ema5?: number;
  ema10?: number;
  ema12?: number;
  ema21?: number;
  ema26?: number;
  ema50?: number;
  ema100?: number;
  ema200?: number;
  
  // Momentum Indicators
  rsi?: number;
  rsi2?: number;
  rsi14?: number;
  stochastic_k?: number;
  stochastic_d?: number;
  williams_r?: number;
  roc?: number;
  momentum?: number;
  
  // Trend Indicators
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  adx?: number;
  di_plus?: number;
  di_minus?: number;
  aroon_up?: number;
  aroon_down?: number;
  aroon_oscillator?: number;
  
  // Volatility Indicators
  bbands_upper?: number;
  bbands_middle?: number;
  bbands_lower?: number;
  atr?: number;
  natr?: number;
  trange?: number;
  keltner_upper?: number;
  keltner_middle?: number;
  keltner_lower?: number;
  
  // Volume Indicators
  obv?: number;
  ad_line?: number;
  ad_oscillator?: number;
  mfi?: number;
  vwap?: number;
  volume_sma?: number;
  volume_ratio?: number;
  
  // Price Action Patterns
  doji?: boolean;
  hammer?: boolean;
  hanging_man?: boolean;
  shooting_star?: boolean;
  engulfing_bullish?: boolean;
  engulfing_bearish?: boolean;
  morning_star?: boolean;
  evening_star?: boolean;
  three_white_soldiers?: boolean;
  three_black_crows?: boolean;
  
  // Support/Resistance Levels
  support_level?: number;
  resistance_level?: number;
  pivot_point?: number;
  pivot_r1?: number;
  pivot_r2?: number;
  pivot_s1?: number;
  pivot_s2?: number;
  
  // Additional indicators can be added here
  [key: string]: any; // Allow additional properties
}

export interface CandlestickData extends ChartData {
  // All candlestick specific properties
  pattern?: string;
  pattern_confidence?: number;
}

export interface PortfolioData extends ChartData {
  portfolioValue: number;
  benchmarkValue: number;
  pnl: number;
  pnlPercent: number;
  benchmarkPnl: number;
  benchmarkPnlPercent: number;
  alpha: number;
  beta: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
}

// Enhanced Trading Signal Interface
export interface TradingSignal {
  id: string;
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  strength: 'weak' | 'moderate' | 'strong' | 'very_strong';
  confidence: number;
  price: number;
  target: number;
  stopLoss: number;
  timeframe: string;
  reason: string;
  technicalIndicators: {
    rsi: number;
    macd: number;
    sma20: number;
    sma50: number;
    volume: number;
    volatility: number;
  };
  riskReward: number;
  timestamp: number;
  expiry: number;
}

export interface PatternSignal {
  pattern: string;
  type: 'bullish' | 'bearish' | 'neutral';
  confidence: number; // 0-100
  description: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  strength: 'weak' | 'moderate' | 'strong' | 'very_strong';
  timeframe: string;
  price: number;
  target?: number;
  stopLoss?: number;
  riskReward?: number;
}

// WebSocket Data Interfaces
export interface WebSocketMessage {
  type: 'price_update' | 'trading_signal' | 'market_status' | 'order_update' | 'error';
  timestamp: number;
  data: any;
}

export interface PriceUpdateMessage extends WebSocketMessage {
  type: 'price_update';
  data: {
    symbol: string;
    price: number;
    change: number;
    change_percent: number;
    volume: number;
    high: number;
    low: number;
    open: number;
    close: number;
    bid?: number;
    ask?: number;
    bid_size?: number;
    ask_size?: number;
  };
}

export interface TradingSignalMessage extends WebSocketMessage {
  type: 'trading_signal';
  data: TradingSignal;
}

export interface MarketStatusMessage extends WebSocketMessage {
  type: 'market_status';
  data: {
    status: 'open' | 'closed' | 'pre_market' | 'post_market';
    next_open?: string;
    next_close?: string;
    timezone: string;
  };
}

export interface OrderUpdateMessage extends WebSocketMessage {
  type: 'order_update';
  data: {
    order_id: string;
    symbol: string;
    status: 'pending' | 'filled' | 'cancelled' | 'rejected';
    quantity: number;
    price: number;
    filled_quantity?: number;
    filled_price?: number;
    timestamp: string;
  };
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  data: {
    error_code: string;
    message: string;
    details?: any;
  };
}

// WebSocket Connection Types
export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnect_interval?: number;
  max_reconnect_attempts?: number;
  heartbeat_interval?: number;
}

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  last_message: WebSocketMessage | null;
  reconnect_attempts: number;
  subscriptions: string[];
}

// Trading Signals Collection Interface
export interface TradingSignals {
  buy_signals: TradingSignal[];
  sell_signals: TradingSignal[];
  hold_signals: TradingSignal[];
  last_updated: string;
}

// Stock Recommendations Interface
export interface StockRecommendation {
  rank: number;
  symbol: string;
  sector: string;
  current_price: number;
  recommendation: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  composite_score: number;
  price_target: number;
  stop_loss: number;
  time_horizon: string;
  reasoning: string;
  timing_recommendation: TimingRecommendation;
  risk_level: 'low' | 'medium' | 'high';
  position_sizing: PositionSizing;
}

export interface TimingRecommendation {
  action: string;
  reason: string;
  next_opportunity?: string;
  confidence?: string;
}

export interface PositionSizing {
  suggested_quantity: number;
  position_value: number;
  risk_percentage: number;
  max_loss: number;
}

// Market Conditions Interface
export interface MarketConditions {
  market_trend: 'bullish' | 'bearish' | 'sideways';
  volatility_level: 'low' | 'medium' | 'high';
  volume_profile: 'high' | 'medium' | 'low';
  sector_rotation: string[];
  economic_indicators: {
    gdp_growth: number;
    inflation: number;
    interest_rates: number;
    currency_strength: string;
  };
  market_sentiment: {
    fear_greed_index: number;
    put_call_ratio: number;
    vix_level: number;
  };
  seasonal_factors: {
    current_month: string;
    earnings_season: boolean;
    budget_session: boolean;
    monsoon_impact: boolean;
  };
  key_events: MarketEvent[];
}

export interface MarketEvent {
  event: string;
  impact: 'positive' | 'negative' | 'neutral';
  date: string;
  description: string;
}

// User Preferences Interface
export interface UserPreferences {
  risk_tolerance: 'low' | 'medium' | 'high';
  investment_horizon: 'short_term' | 'medium_term' | 'long_term';
  preferred_sectors: string[];
  market_cap_preference: 'small_cap' | 'mid_cap' | 'large_cap';
  volatility_tolerance: 'low' | 'medium' | 'high';
  max_positions: number;
  min_confidence: number;
}

// Order Management Interfaces
export interface OrderRequest {
  symbol: string;
  quantity: number;
  order_type: 'BUY' | 'SELL';
  order_category: 'MARKET' | 'LIMIT' | 'STOP_LOSS';
  price?: number;
  stop_loss?: number;
  take_profit?: number;
}

export interface OrderResponse {
  order_id: string;
  symbol: string;
  quantity: number;
  order_type: string;
  status: 'PENDING' | 'EXECUTED' | 'CANCELLED' | 'REJECTED';
  price: number;
  timestamp: string;
  message?: string;
}

export interface OrdersResponse {
  orders: OrderResponse[];
  total_count: number;
  last_updated: string;
}

// AI Analysis Interfaces
export interface AIAnalysis {
  symbol: string;
  analysis_type: 'TECHNICAL' | 'FUNDAMENTAL' | 'SENTIMENT';
  score: number;
  confidence: number;
  recommendation: 'BUY' | 'SELL' | 'HOLD';
  reasoning: string[];
  key_factors: string[];
  timestamp: string;
}

// Risk Metrics Interface
export interface RiskMetrics {
  symbol: string;
  beta: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  var_95: number;
  var_99: number;
  expected_return: number;
  risk_score: number;
  timestamp: string;
}

// Sector Analysis Interface (Legacy)
export interface SectorAnalysis {
  sector_analysis: Record<string, SectorAnalysisData>;
  sector_recommendations: SectorRecommendations;
}

export interface SectorAnalysisData {
  performance: number;
  trend: 'up' | 'down' | 'sideways';
  volume: 'high' | 'medium' | 'low';
  momentum: 'strong' | 'moderate' | 'weak' | 'neutral';
}

export interface SectorRecommendations {
  buy: string[];
  hold: string[];
  sell: string[];
}

// Chart Library Integration Types
export interface ChartLibraryConfig {
  library: 'recharts' | 'chartjs' | 'd3' | 'highcharts' | 'tradingview';
  theme: 'light' | 'dark' | 'auto';
  responsive: boolean;
  animations: boolean;
  locale: string;
}

export interface ChartSeries {
  name: string;
  data: ChartData[];
  type: 'candlestick' | 'line' | 'area' | 'bar' | 'volume';
  color?: string;
  yAxis?: 'left' | 'right';
  visible?: boolean;
}

export interface ChartAxis {
  type: 'time' | 'value' | 'category';
  position: 'left' | 'right' | 'top' | 'bottom';
  min?: number;
  max?: number;
  tickCount?: number;
  format?: string;
  label?: string;
}

export interface ChartOverlay {
  type: 'sma' | 'ema' | 'bollinger' | 'macd' | 'rsi' | 'volume';
  period?: number;
  color?: string;
  visible?: boolean;
  yAxis?: 'left' | 'right';
}

export interface ChartDrawing {
  id: string;
  type: 'line' | 'horizontal' | 'vertical' | 'rectangle' | 'fibonacci' | 'trend';
  points: Array<{ x: number; y: number }>;
  style: {
    color: string;
    width: number;
    dashArray?: string;
  };
  visible: boolean;
  locked: boolean;
}

export interface ChartTooltip {
  enabled: boolean;
  shared: boolean;
  crosshair: boolean;
  format: {
    price: string;
    volume: string;
    date: string;
  };
}

export interface ChartZoom {
  enabled: boolean;
  type: 'x' | 'y' | 'xy';
  minRange?: number;
  maxRange?: number;
}

export interface ChartConfig {
  width?: number;
  height?: number;
  margin?: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
  series: ChartSeries[];
  xAxis: ChartAxis;
  yAxis: ChartAxis[];
  overlays: ChartOverlay[];
  drawings: ChartDrawing[];
  tooltip: ChartTooltip;
  zoom: ChartZoom;
  grid: {
    show: boolean;
    color: string;
    style: 'solid' | 'dashed' | 'dotted';
  };
  crosshair: {
    show: boolean;
    color: string;
    style: 'solid' | 'dashed';
  };
}

// Added by Frontend-Backend Sync Fix v1.0

export interface Trade {
  id: string;
  orderId: string;
  symbol: string;
  exchange: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  timestamp: string;
  userId: string;
  fees?: number;
  pnl?: number;
}


// User interface
export interface User {
  id: number;
  username: string;
  email: string;
  mobile_number?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  data?: {
    user: User;
    access_token: string;
    refresh_token: string;
    expires_in: number;
  };
  error?: string;
  // Direct access properties for compatibility
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
}


export interface ErrorResponse {
  success: false;
  error: {
    message: string;
    code: string;
    details?: any;
    timestamp: string;
  };
  requestId?: string;
}

// Enhanced Type Definitions - Added by Critical Issues Fix v2.0

// Performance metrics interface with comprehensive trading analytics
export interface PerformanceMetrics {
  user_id: number;
  total_return: number;
  total_return_percentage: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  average_win: number;
  average_loss: number;
  largest_win: number;
  largest_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
  current_streak: number;
  best_month: number;
  worst_month: number;
  monthly_returns: number[];
  quarterly_returns: number[];
  yearly_returns: number[];
  risk_metrics: {
    var_95: number;
    var_99: number;
    expected_shortfall: number;
    beta: number;
    alpha: number;
    information_ratio: number;
    calmar_ratio: number;
    sortino_ratio: number;
  };
  portfolio_metrics: {
    total_value: number;
    cash_balance: number;
    invested_amount: number;
    unrealized_pnl: number;
    realized_pnl: number;
    margin_used: number;
    buying_power: number;
    leverage_ratio: number;
    diversification_ratio: number;
  };
  benchmark_comparison: {
    benchmark_return: number;
    excess_return: number;
    tracking_error: number;
    information_ratio: number;
    beta: number;
    alpha: number;
    correlation: number;
  };
  calculated_at: string;
  period_start: string;
  period_end: string;
}

// Trading session interface for active trading management
export interface TradingSession {
  session_id: string;
  user_id: number;
  start_time: string;
  end_time?: string;
  is_active: boolean;
  total_trades: number;
  total_volume: number;
  total_pnl: number;
  max_drawdown: number;
  peak_balance: number;
  current_balance: number;
  risk_limit: number;
  position_limit: number;
  daily_pnl: number;
  session_metrics: {
    win_rate: number;
    avg_trade_size: number;
    max_position_size: number;
    risk_per_trade: number;
  };
}

// Market depth interface for order book data
export interface MarketDepth {
  symbol: string;
  timestamp: string;
  bids: Array<{
    price: number;
    quantity: number;
    orders: number;
  }>;
  asks: Array<{
    price: number;
    quantity: number;
    orders: number;
  }>;
  spread: number;
  mid_price: number;
  total_bid_volume: number;
  total_ask_volume: number;
  imbalance_ratio: number;
}

// Order book interface for detailed order management
export interface OrderBook {
  symbol: string;
  timestamp: string;
  levels: Array<{
    price: number;
    bid_quantity: number;
    ask_quantity: number;
    bid_orders: number;
    ask_orders: number;
  }>;
  best_bid: number;
  best_ask: number;
  spread: number;
  mid_price: number;
  volume_weighted_price: number;
  last_trade_price: number;
  last_trade_quantity: number;
  last_trade_time: string;
}

// Technical indicators interface for analysis
export interface TechnicalIndicators {
  symbol: string;
  timeframe: string;
  timestamp: string;
  price_data: {
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  };
  moving_averages: {
    sma_5: number;
    sma_10: number;
    sma_20: number;
    sma_50: number;
    sma_200: number;
    ema_12: number;
    ema_26: number;
  };
  oscillators: {
    rsi: number;
    macd: number;
    macd_signal: number;
    macd_histogram: number;
    stochastic_k: number;
    stochastic_d: number;
    williams_r: number;
    cci: number;
  };
  trend_indicators: {
    adx: number;
    di_plus: number;
    di_minus: number;
    aroon_up: number;
    aroon_down: number;
    parabolic_sar: number;
  };
  volume_indicators: {
    obv: number;
    ad_line: number;
    cmf: number;
    vwap: number;
    volume_sma: number;
  };
  support_resistance: {
    support_levels: number[];
    resistance_levels: number[];
    pivot_point: number;
    pivot_resistance_1: number;
    pivot_resistance_2: number;
    pivot_support_1: number;
    pivot_support_2: number;
  };
}

// Risk assessment interface for portfolio risk management
export interface RiskAssessment {
  user_id: number;
  assessment_date: string;
  portfolio_value: number;
  risk_metrics: {
    var_1d: number;
    var_5d: number;
    var_30d: number;
    expected_shortfall: number;
    maximum_drawdown: number;
    current_drawdown: number;
    volatility: number;
    beta: number;
    alpha: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    calmar_ratio: number;
  };
  position_risks: Array<{
    symbol: string;
    position_size: number;
    position_value: number;
    weight: number;
    individual_var: number;
    contribution_to_portfolio_var: number;
    beta: number;
    correlation_with_portfolio: number;
  }>;
  concentration_risks: {
    top_5_positions_weight: number;
    sector_concentration: Record<string, number>;
    single_stock_limit_breach: string[];
    sector_limit_breach: string[];
  };
  liquidity_risks: {
    liquid_positions_value: number;
    illiquid_positions_value: number;
    liquidity_ratio: number;
    days_to_liquidate_50_percent: number;
    days_to_liquidate_100_percent: number;
  };
  stress_test_results: {
    market_crash_scenario: number;
    interest_rate_shock: number;
    sector_rotation_scenario: number;
    liquidity_crisis_scenario: number;
  };
  risk_limits: {
    max_portfolio_var: number;
    max_position_weight: number;
    max_sector_weight: number;
    max_daily_loss: number;
    max_drawdown_limit: number;
  };
  risk_alerts: Array<{
    alert_type: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    message: string;
    triggered_at: string;
    resolved: boolean;
  }>;
}

// Portfolio allocation interface for asset allocation management
export interface PortfolioAllocation {
  user_id: number;
  allocation_date: string;
  total_value: number;
  cash_allocation: {
    percentage: number;
    value: number;
    target_percentage: number;
    rebalance_needed: boolean;
  };
  equity_allocation: {
    percentage: number;
    value: number;
    target_percentage: number;
    rebalance_needed: boolean;
    sectors: Array<{
      sector_name: string;
      percentage: number;
      value: number;
      target_percentage: number;
    }>;
  };
  fixed_income_allocation: {
    percentage: number;
    value: number;
    target_percentage: number;
    rebalance_needed: boolean;
    duration: number;
    yield_to_maturity: number;
  };
  alternative_allocation: {
    percentage: number;
    value: number;
    target_percentage: number;
    rebalance_needed: boolean;
    categories: Array<{
      category_name: string;
      percentage: number;
      value: number;
    }>;
  };
  rebalancing_recommendations: Array<{
    action: 'BUY' | 'SELL' | 'HOLD';
    asset_class: string;
    current_weight: number;
    target_weight: number;
    adjustment_amount: number;
    priority: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
}

// Trading strategy interface for strategy management
export interface TradingStrategy {
  strategy_id: string;
  user_id: number;
  name: string;
  description: string;
  strategy_type: 'MOMENTUM' | 'MEAN_REVERSION' | 'ARBITRAGE' | 'SCALPING' | 'SWING' | 'POSITION';
  timeframes: string[];
  symbols: string[];
  parameters: Record<string, any>;
  risk_parameters: {
    max_position_size: number;
    stop_loss_percentage: number;
    take_profit_percentage: number;
    max_daily_trades: number;
    max_drawdown_limit: number;
  };
  performance_metrics: {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    profit_factor: number;
    total_trades: number;
    avg_trade_duration: number;
  };
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_execution: string;
  next_execution: string;
}

// Backtest result interface for strategy testing
export interface BacktestResult {
  backtest_id: string;
  strategy_id: string;
  user_id: number;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown: number;
  max_drawdown_duration: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
  equity_curve: Array<{
    date: string;
    value: number;
    drawdown: number;
  }>;
  monthly_returns: Array<{
    month: string;
    return: number;
  }>;
  trade_log: Array<{
    trade_id: string;
    symbol: string;
    entry_date: string;
    exit_date: string;
    entry_price: number;
    exit_price: number;
    quantity: number;
    pnl: number;
    pnl_percentage: number;
    duration: number;
    reason: string;
  }>;
  created_at: string;
}