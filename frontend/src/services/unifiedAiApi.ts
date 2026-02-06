/**
 * Unified AI API Service
 * Integrates with backend /api/unified-ai/* endpoints
 */

import { httpClient, APIResponse } from '../config/api';

// Unified AI API Response Interfaces
export interface UnifiedAnalysisRequest {
  symbol: string;
  user_query?: string;
  analysis_depth?: 'QUICK' | 'STANDARD' | 'COMPREHENSIVE';
  include_charts?: boolean;
  include_news?: boolean;
}

export interface UnifiedAnalysisResponse {
  symbol: string;
  analysis_result: {
    technical_analysis: {
      rsi?: number;
      macd?: string;
      signal?: string;
      sma_20?: number;
      sma_50?: number;
      ema_12?: number;
      ema_26?: number;
      bbands_upper?: number;
      bbands_middle?: number;
      bbands_lower?: number;
      volume_sma?: number;
    };
    sentiment_analysis: {
      news_sentiment?: string;
      social_sentiment?: string;
      overall_sentiment?: string;
      sentiment_score?: number;
    };
    volume_analysis: {
      volume_trend?: string;
      volume_signal?: string;
      volume_strength?: string;
      volume_ratio?: number;
    };
    pattern_analysis: {
      candlestick_patterns?: string[];
      chart_patterns?: string[];
      pattern_signals?: string[];
      pattern_confidence?: number;
    };
    ml_signals: {
      prediction?: string;
      confidence?: number;
      model_performance?: string;
      feature_importance?: Record<string, number>;
    };
    ai_reasoning: string;
    natural_language_explanation: string;
    conversational_response: string;
    ai_methods_used: string[];
  };
  confidence_score: number;
  recommendation: 'BUY' | 'SELL' | 'HOLD';
  analysis_timestamp: string;
  processing_time_ms: number;
  price_target?: number;
  stop_loss?: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  entry_price?: number;
  exit_price?: number;
  holding_period?: string;
  holding_days_min?: number;
  holding_days_max?: number;
}

export interface BatchAnalysisRequest {
  symbols: string[];
  analysis_depth?: 'QUICK' | 'STANDARD' | 'COMPREHENSIVE';
  user_query?: string;
}

export interface BatchAnalysisResponse {
  batch_analysis: Record<string, {
    symbol: string;
    recommendation: 'BUY' | 'SELL' | 'HOLD';
    confidence_score: number;
    ai_reasoning: string;
    natural_language_explanation: string;
    price_target?: number;
    stop_loss?: number;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
    analysis_timestamp: string;
    processing_time_ms: number;
    status: 'success' | 'error';
  }>;
  total_symbols: number;
  successful_analyses: number;
  failed_analyses: number;
  analysis_depth: string;
  user_query?: string;
  timestamp: string;
}

export interface AIStatusResponse {
  service_status: 'healthy' | 'degraded' | 'unhealthy';
  traditional_ai: {
    status: 'active' | 'inactive';
    capabilities: string[];
    performance_metrics: {
      accuracy: number;
      response_time_ms: number;
      uptime_percentage: number;
    };
  };
  generative_ai: {
    status: 'active' | 'inactive' | 'limited';
    model: string;
    capabilities: string[];
    performance_metrics: {
      response_time_ms: number;
      token_usage: number;
      uptime_percentage: number;
    };
  };
  database_status: 'connected' | 'disconnected';
  last_updated: string;
}

export interface AIRecommendationsRequest {
  limit?: number;
  min_confidence?: number;
  sectors?: string[];
  market_cap?: 'small' | 'mid' | 'large';
  risk_tolerance?: 'low' | 'medium' | 'high';
}

export interface AIRecommendationsResponse {
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
  }>;
  market_conditions: {
    overall_sentiment: 'bullish' | 'bearish' | 'neutral';
    sector_rotation: string[];
    volatility_level: 'low' | 'medium' | 'high';
    market_trend: 'up' | 'down' | 'sideways';
  };
  last_updated: string;
}

export interface StockInsightsRequest {
  insight_type?: 'quick' | 'comprehensive' | 'technical' | 'fundamental' | 'sentiment';
}

export interface StockInsightsResponse {
  symbol: string;
  insight_type: string;
  timestamp: string;
  overall_sentiment: 'bullish' | 'bearish' | 'neutral';
  key_insights: string[];
  risk_assessment: {
    level: 'LOW' | 'MEDIUM' | 'HIGH';
    factors: string[];
  };
  recommendations: {
    primary: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    reasoning: string;
  };
  technical_insights: {
    rsi: number;
    macd_signal: string;
    trend: string;
    strength: string;
  };
  sentiment_insights: {
    news_sentiment: string;
    social_sentiment: string;
    overall_sentiment: string;
  };
  volume_insights: {
    trend: string;
    signal: string;
    strength: string;
  };
  pattern_insights: {
    patterns: string[];
    significance: string;
  };
  ml_insights: {
    prediction: string;
    confidence: number;
    model_performance: string;
  };
}

export interface MarketOverviewResponse {
  market_status: 'open' | 'closed' | 'pre_market' | 'post_market';
  overall_sentiment: 'bullish' | 'bearish' | 'neutral';
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
    fear_greed_index: number;
    put_call_ratio: number;
    vix_level: number;
  };
  ai_insights: {
    market_outlook: string;
    key_themes: string[];
    risk_factors: string[];
    opportunities: string[];
  };
  last_updated: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  context_symbol?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  context_symbol?: string;
  timestamp: string;
}

export interface NotificationPreferences {
  email_alerts: boolean;
  sms_alerts: boolean;
  push_notifications: boolean;
  price_alerts: boolean;
  pattern_alerts: boolean;
  signal_alerts: boolean;
  news_alerts: boolean;
  alert_frequency: 'immediate' | 'hourly' | 'daily';
}

// Unified AI API Service Class
class UnifiedAiApiService {
  
  // Single Symbol Analysis
  async analyzeStock(request: UnifiedAnalysisRequest): Promise<UnifiedAnalysisResponse> {
    try {
      const response = await httpClient.post<UnifiedAnalysisResponse>('/api/unified-ai/analyze', request);
      
      console.log('🔍 API Response:', response);
      console.log('🔍 Response Success:', response.success);
      console.log('🔍 Response Data:', response.data);
      
      if (!response.success) {
        console.error('❌ API Error:', response.error);
        throw new Error(response.error || 'Failed to analyze stock');
      }
      
      if (!response.data) {
        console.error('❌ No data in response');
        throw new Error('No data returned from analysis');
      }
      
      console.log('✅ Analysis Result:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ analyzeStock Error:', error);
      throw error;
    }
  }

  // Batch Analysis
  async batchAnalyzeStocks(request: BatchAnalysisRequest): Promise<BatchAnalysisResponse> {
    const response = await httpClient.post<BatchAnalysisResponse>('/api/unified-ai/batch-analyze', request);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to batch analyze stocks');
    }
    
    return response.data;
  }

  // Service Status
  async getServiceStatus(): Promise<AIStatusResponse> {
    const response = await httpClient.get<AIStatusResponse>('/api/unified-ai/status');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get service status');
    }
    
    return response.data;
  }

  // AI Recommendations
  async getAIRecommendations(request: AIRecommendationsRequest = {}): Promise<AIRecommendationsResponse> {
    // Use the symbol-specific endpoint with a default symbol
    const defaultSymbol = "RELIANCE";
    const response = await httpClient.get<AIRecommendationsResponse>(`/api/unified-ai/recommendations/${defaultSymbol}`, {
      limit: request.limit || 10
    });
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get AI recommendations');
    }
    
    return response.data;
  }

  // Stock Insights
  async getStockInsights(symbol: string, request: StockInsightsRequest = {}): Promise<StockInsightsResponse> {
    const response = await httpClient.get<StockInsightsResponse>(
      `/api/unified-ai/insights/${symbol}`,
      request
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get stock insights');
    }
    
    return response.data;
  }

  // Market Overview
  async getMarketOverview(): Promise<MarketOverviewResponse> {
    const response = await httpClient.get<MarketOverviewResponse>('/api/unified-ai/market-overview');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get market overview');
    }
    
    return response.data;
  }

  // AI Chat
  async chatWithAI(request: ChatRequest): Promise<ChatResponse> {
    const response = await httpClient.post<ChatResponse>('/api/unified-ai/chat', request);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to chat with AI');
    }
    
    return response.data;
  }

  // Test Notification
  async testNotification(message: string = 'Test notification from Unified AI'): Promise<{ success: boolean; message: string }> {
    const response = await httpClient.post<{ success: boolean; message: string }>('/api/unified-ai/test-notification', {
      message
    });
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to test notification');
    }
    
    return response.data;
  }

  // Notification Preferences
  async getNotificationPreferences(): Promise<NotificationPreferences> {
    const response = await httpClient.get<NotificationPreferences>('/api/unified-ai/notification-preferences');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get notification preferences');
    }
    
    return response.data;
  }

  async updateNotificationPreferences(preferences: Partial<NotificationPreferences>): Promise<NotificationPreferences> {
    const response = await httpClient.post<NotificationPreferences>('/api/unified-ai/notification-preferences', preferences);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to update notification preferences');
    }
    
    return response.data;
  }

  // Health Check
  async getHealthStatus(): Promise<{ status: string; timestamp: string }> {
    const response = await httpClient.get<{ status: string; timestamp: string }>('/api/unified-ai/health');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get health status');
    }
    
    return response.data;
  }
}

// Create and export service instance
export const unifiedAiApi = new UnifiedAiApiService();
export default unifiedAiApi;
