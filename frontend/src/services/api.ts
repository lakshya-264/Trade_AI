/**
 * Updated API Service for Trader AI Frontend
 * Uses centralized configuration and standardized response handling
 */

import {
  httpClient,
  APIResponse,
  PaginatedResponse,
  ApiError,
  TokenManager,
  debugLog,
  generateRequestId,
} from '../config/api';

// Import all type definitions
import {
  QuoteData,
  HistoricalDataPoint,
  MarketStatus,
  TopGainerLoser,
  PortfolioResponse,
  OrdersResponse,
  OrderRequest,
  OrderResponse,
  AIAnalysis,
  RiskMetrics,
  IndexConstituents,
  TechnicalIndicators,
  SectorPerformance,
  IndustrySummary,
  FastInfo,
  MarketSummary,
  BatchQuotes,
  ScreenerResult,
  ScreenerQuery,
  HoldersData,
  FundamentalsData,
  FundProfile,
  TradingSignals,
  User,
  AuthResponse,
} from '../types/api';

// Authentication interfaces
interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  mobile_number?: string;
}

// AuthResponse interface is imported from '../types/api'

// API Service Class
class ApiService {
  private requestId: string;

  constructor() {
    this.requestId = generateRequestId();
  }

  // Authentication endpoints
  async login(credentials: LoginCredentials): Promise<APIResponse<any>> {
    debugLog('Login attempt', { username: credentials.username });
    
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await httpClient.post<AuthResponse>('/api/auth/login-form', formData.toString());

    if (response.success && response.data) {
      TokenManager.setToken(response.access_token || '');
      TokenManager.setRefreshToken(response.refresh_token || '');
    }

    return response;
  }

  async register(username: string, email: string, password: string, mobileNumber?: string): Promise<APIResponse<any>> {
    debugLog('Registration attempt', { email });
    
    const userData = {
      username,
      email,
      password,
      mobile_number: mobileNumber
    };
    
    const response = await httpClient.post<AuthResponse>('/api/auth/register', userData);
    
    if (response.success && response.data) {
      TokenManager.setToken(response.access_token || '');
      TokenManager.setRefreshToken(response.refresh_token || '');
    }

    return response;
  }

  // Form-based login for compatibility
  async loginForm(username: string, password: string): Promise<APIResponse<any>> {
    debugLog('Form login attempt', { username });
    
    const loginData = {
      username: username,
      password: password
    };
    
    const response = await httpClient.post('/api/auth/login-form', loginData);

    // Handle direct JWT response from backend (not wrapped in APIResponse)
    if (response && typeof response === 'object' && 'access_token' in response) {
      const jwtResponse = response as any; // Type assertion for direct JWT response
      TokenManager.setToken(jwtResponse.access_token);
      TokenManager.setRefreshToken(jwtResponse.refresh_token);
      
      // Wrap the response in APIResponse format for frontend compatibility
      return {
        success: true,
        status: 'success' as const,
        data: {
          user: {
            id: 1, // We'll get the actual user data from /me endpoint
            username: username,
            email: `${username}@traderai.com`,
            is_active: true,
            role: 'user', // Added missing role property
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          } as User,
          access_token: jwtResponse.access_token,
          refresh_token: jwtResponse.refresh_token,
          expires_in: jwtResponse.expires_in
        },
        timestamp: new Date().toISOString(),
        // Direct access properties
        access_token: jwtResponse.access_token,
        refresh_token: jwtResponse.refresh_token,
        expires_in: jwtResponse.expires_in
      } as APIResponse<any>;
    }

    // If it's already in APIResponse format, return as is
    return response as APIResponse<any>;
  }

  // OTP methods
  async sendOTP(phoneOrEmail: string, purpose: string = 'login', isEmail: boolean = false): Promise<APIResponse<any>> {
    const requestId = generateRequestId();
    debugLog(`Send OTP request: ${requestId}`, { phoneOrEmail, purpose, isEmail });
    
    try {
      // httpClient.post returns APIResponse<T> directly (not response.data)
      const response = await httpClient.post<APIResponse<any>>('/api/auth/send-otp', {
        phone_or_email: phoneOrEmail,
        purpose: purpose,
        is_email: isEmail
      });
      debugLog(`Send OTP response: ${requestId}`, response);
      
      // Ensure response has success field (backend should return it, but handle gracefully)
      if (response && typeof response.success === 'boolean') {
        return response;
      } else {
        // If response doesn't have success, normalize it
        console.warn('Unexpected response format from backend:', response);
        return {
          success: (response as any)?.success ?? true, // Default to true if backend returned 200
          status: (response as any)?.status || 'success',
          message: (response as any)?.message || 'OTP sent',
          error: (response as any)?.error,
          timestamp: (response as any)?.timestamp || new Date().toISOString(),
          request_id: requestId
        } as APIResponse<any>;
      }
    } catch (error: any) {
      debugLog(`Send OTP error: ${requestId}`, error);
      // Re-throw with more context
      throw error;
    }
  }

  async verifyOTP(phoneOrEmail: string, otp: string, purpose: string = 'login', isEmail: boolean = false): Promise<APIResponse<any>> {
    const requestId = generateRequestId();
    debugLog(`Verify OTP request: ${requestId}`, { phoneOrEmail, otp, purpose, isEmail });
    
    try {
      const response = await httpClient.post('/api/auth/verify-otp', {
        phone_or_email: phoneOrEmail,
        otp: otp,
        purpose: purpose
      });
      debugLog(`Verify OTP response: ${requestId}`, response);
      return response as APIResponse<any>;
    } catch (error) {
      debugLog(`Verify OTP error: ${requestId}`, error);
      throw error;
    }
  }

  async resendOTP(phoneOrEmail: string, purpose: string = 'login', isEmail: boolean = false): Promise<APIResponse<any>> {
    const requestId = generateRequestId();
    debugLog(`Resend OTP request: ${requestId}`, { phoneOrEmail, purpose, isEmail });
    
    try {
      const response = await httpClient.post('/api/auth/send-otp', {
        phone_or_email: phoneOrEmail,
        purpose: purpose,
        is_email: isEmail
      });
      debugLog(`Resend OTP response: ${requestId}`, response);
      return response as APIResponse<any>;
    } catch (error) {
      debugLog(`Resend OTP error: ${requestId}`, error);
      throw error;
    }
  }

  async logout(): Promise<APIResponse<void>> {
    debugLog('Logout attempt');
    
    TokenManager.clearTokens();
    return httpClient.post<void>('/api/auth/logout');
  }

  async getCurrentUser(): Promise<APIResponse<any>> {
    return httpClient.get<any>('/api/auth/me');
  }

  async refreshToken(): Promise<APIResponse<{ access_token: string }>> {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) {
      throw new ApiError('No refresh token available', 401, 'NO_REFRESH_TOKEN');
    }

    const response = await httpClient.post<{ access_token: string }>('/api/auth/refresh', {
      refresh_token: refreshToken,
    });

    if (response.success && response.data) {
      TokenManager.setToken(response.data?.access_token || '');
    }

    return response;
  }

  // Real-time data endpoints
  async getQuote(symbol: string, exchange: string = 'NSE'): Promise<QuoteData> {
    debugLog('Fetching quote', { symbol, exchange });
    
    const response = await httpClient.get<QuoteData>(`/realtime/quote/${symbol}`, {
      exchange,
    });

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch quote',
        404,
        'QUOTE_NOT_FOUND',
        { symbol, exchange }
      );
    }

    return response.data;
  }

  async getBatchQuotes(symbols: string[]): Promise<QuoteData[]> {
    debugLog('Fetching batch quotes', { symbols });
    
    const response = await httpClient.get<QuoteData[]>('/realtime/quotes', {
      symbols: symbols.join(','),
    });

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch batch quotes',
        500,
        'BATCH_QUOTES_ERROR'
      );
    }

    return response.data;
  }

  async getMarketSummary(): Promise<MarketSummary> {
    debugLog('Fetching market summary');
    
    const response = await httpClient.get<MarketSummary>('/realtime/market/summary');

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch market summary',
        500,
        'MARKET_SUMMARY_ERROR'
      );
    }

    return response.data;
  }

  async getMarketStatus(): Promise<MarketStatus> {
    debugLog('Fetching market status');
    
    // Backend route is mounted under /api/realtime/market-status
    const response = await httpClient.get<MarketStatus>('/api/realtime/market-status');

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch market status',
        500,
        'MARKET_STATUS_ERROR'
      );
    }

    return response.data;
  }

  async getTopGainers(exchange: string = 'NSE'): Promise<TopGainerLoser[]> {
    debugLog('Fetching top gainers', { exchange });
    
    const response = await httpClient.get<TopGainerLoser[]>('/realtime/top-gainers', {
      exchange,
    });

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch top gainers',
        500,
        'TOP_GAINERS_ERROR'
      );
    }

    return response.data;
  }

  async getTopLosers(exchange: string = 'NSE'): Promise<TopGainerLoser[]> {
    debugLog('Fetching top losers', { exchange });
    
    const response = await httpClient.get<TopGainerLoser[]>('/realtime/top-losers', {
      exchange,
    });

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch top losers',
        500,
        'TOP_LOSERS_ERROR'
      );
    }

    return response.data;
  }

  async getHistoricalData(
    symbol: string,
    exchange: string = 'NSE',
    timeframe?: string,
    fromDate?: string,
    toDate?: string
  ): Promise<HistoricalDataPoint[]> {
    debugLog('Fetching historical data', { symbol, exchange, timeframe });
    
    const params: Record<string, any> = { exchange };
    if (timeframe) params.timeframe = timeframe;
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;

    const response = await httpClient.get<HistoricalDataPoint[]>(
      `/realtime/historical/${symbol}`,
      params
    );

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch historical data',
        500,
        'HISTORICAL_DATA_ERROR',
        { symbol, exchange }
      );
    }

    return response.data;
  }

  async getTechnicalIndicators(
    symbol: string,
    indicator: string,
    params?: {
      period?: number;
      fastperiod?: number;
      slowperiod?: number;
      signalperiod?: number;
      timeframe?: string;
    }
  ): Promise<TechnicalIndicators> {
    debugLog('Fetching technical indicators', { symbol, indicator });
    
    const queryParams: Record<string, any> = { indicator };
    if (params) {
      Object.assign(queryParams, params);
    }

    const response = await httpClient.get<TechnicalIndicators>(
      `/realtime/indicators/${symbol}`,
      queryParams
    );

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch technical indicators',
        500,
        'TECHNICAL_INDICATORS_ERROR',
        { symbol, indicator }
      );
    }

    return response.data;
  }

  // Trading endpoints
  async getPortfolio(): Promise<PortfolioResponse> {
    debugLog('Fetching portfolio (using unified endpoint)');
    
    // Use new unified endpoint - /api/portfolio-allocation/holdings
    const response = await httpClient.get<any>('/portfolio-allocation/holdings');

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch portfolio',
        500,
        'PORTFOLIO_ERROR'
      );
    }

    // Transform new format to old format for backward compatibility
    const data = response.data;
    return {
      portfolio: data.holdings || [],
      total_value: data.total_value || 0.0,
      total_pnl: data.total_pnl || 0.0,
      last_updated: data.last_updated || new Date().toISOString()
    };
  }
  
  async getUnifiedPortfolio(): Promise<any> {
    debugLog('Fetching unified portfolio (holdings + allocation)');
    
    const response = await httpClient.get<any>('/portfolio-allocation/portfolio');

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch unified portfolio',
        500,
        'PORTFOLIO_ERROR'
      );
    }

    return response.data;
  }

  async getOrders(userId: number = 1): Promise<OrdersResponse> {
    debugLog('Fetching orders', { userId });
    
    const response = await httpClient.get<OrdersResponse>('/trading/orders', {
      user_id: userId,
    });

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch orders',
        500,
        'ORDERS_ERROR'
      );
    }

    return response.data;
  }

  async placeOrder(orderData: OrderRequest, userId: number = 1): Promise<OrderResponse> {
    debugLog('Placing order', { orderData, userId });
    
    const response = await httpClient.post<OrderResponse>('/trading/place-order', orderData);

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to place order',
        500,
        'PLACE_ORDER_ERROR',
        orderData
      );
    }

    return response.data;
  }

  async cancelOrder(orderId: number, userId: number = 1): Promise<OrderResponse> {
    debugLog('Cancelling order', { orderId, userId });
    
    const response = await httpClient.delete<OrderResponse>(`/trading/cancel-order/${orderId}`);

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to cancel order',
        500,
        'CANCEL_ORDER_ERROR',
        { orderId }
      );
    }

    return response.data;
  }

  // Unified AI Analysis endpoints (Combines Traditional AI + GenAI)
  async getUnifiedAIAnalysis(symbol: string, userQuery?: string, analysisDepth: string = 'COMPREHENSIVE'): Promise<APIResponse<any>> {
    debugLog('Fetching unified AI analysis', { symbol, userQuery, analysisDepth });
    
    return httpClient.post<any>('/unified-ai/analyze', {
      symbol,
      user_query: userQuery,
      analysis_depth: analysisDepth,
    });
  }

  async chatWithUnifiedAI(message: string, sessionId?: string, contextSymbol?: string): Promise<APIResponse<any>> {
    debugLog('Chatting with unified AI', { sessionId, contextSymbol });
    
    return httpClient.post<any>('/unified-ai/chat', {
      message,
      session_id: sessionId,
      context_symbol: contextSymbol,
    });
  }

  async batchAnalyzeStocks(symbols: string[], analysisDepth: string = 'STANDARD', userQuery?: string): Promise<APIResponse<any>> {
    debugLog('Batch analyzing stocks', { symbols, analysisDepth });
    
    return httpClient.post<any>('/unified-ai/batch-analyze', {
      symbols,
      analysis_depth: analysisDepth,
      user_query: userQuery,
    });
  }

  async getUnifiedAIStatus(): Promise<APIResponse<any>> {
    debugLog('Fetching unified AI status');
    
    return httpClient.get<any>('/api/unified-ai/status');
  }

  async getAIRecommendations(symbol: string = "RELIANCE", limit: number = 10): Promise<APIResponse<any>> {
    debugLog('Fetching AI recommendations', { symbol, limit });
    
    return httpClient.get<any>(`/api/unified-ai/recommendations/${symbol}`, {
      limit,
    });
  }

  async getStockInsights(symbol: string, insightType: string = 'comprehensive'): Promise<APIResponse<any>> {
    debugLog('Fetching stock insights', { symbol, insightType });
    
    return httpClient.get<any>(`/api/unified-ai/insights/${symbol}`, {
      insight_type: insightType,
    });
  }

  // AI Analysis endpoints
  async getAIAnalysis(symbol: string): Promise<AIAnalysis> {
    debugLog('Fetching AI analysis', { symbol });
    
    const response = await httpClient.get<AIAnalysis>(`/ai/analyze/${symbol}`);

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch AI analysis',
        500,
        'AI_ANALYSIS_ERROR',
        { symbol }
      );
    }

    return response.data;
  }

  async getTradingSignals(): Promise<TradingSignals> {
    debugLog('Fetching trading signals');
    
    const response = await httpClient.get<TradingSignals>('/ai/signals');

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch trading signals',
        500,
        'TRADING_SIGNALS_ERROR'
      );
    }

    return response.data;
  }

  // Risk Management endpoints
  async getRiskMetrics(userId: number = 1): Promise<RiskMetrics> {
    debugLog('Fetching risk metrics', { userId });
    
    const response = await httpClient.get<RiskMetrics>('/risk/metrics', {
      user_id: userId,
    });

    if (!response.success || !response.data) {
      throw new ApiError(
        response.error || 'Failed to fetch risk metrics',
        500,
        'RISK_METRICS_ERROR'
      );
    }

    return response.data;
  }

  // Chat endpoints
  async sendMessage(message: string, sessionId?: string): Promise<APIResponse<any>> {
    debugLog('Sending chat message', { sessionId });
    
    // Use Unified AI chat endpoint (does not require /api/chat auth flow).
    return httpClient.post<any>('/api/unified-ai/chat', {
      message,
      session_id: sessionId,
      context_symbol: null
    });
  }

  async createChatSession(): Promise<APIResponse<any>> {
    debugLog('Creating chat session');
    
    return httpClient.post<any>('/chat/session');
  }

  async getChatHistory(sessionId: string): Promise<APIResponse<any>> {
    debugLog('Fetching chat history', { sessionId });
    
    return httpClient.get<any>(`/chat/history/${sessionId}`);
  }

  async getChatSessions(): Promise<APIResponse<any>> {
    debugLog('Fetching chat sessions');
    
    return httpClient.get<any>('/chat/sessions');
  }

  // Education endpoints
  async getLearningPaths(level: string = 'beginner'): Promise<APIResponse<any>> {
    debugLog('Fetching learning paths', { level });
    
    return httpClient.get<any>('/education/learning-paths', { level });
  }

  async getTradingStrategies(): Promise<APIResponse<any>> {
    debugLog('Fetching trading strategies');
    
    return httpClient.get<any>('/education/trading-strategies');
  }

  async getIndexConstituents(indexId: string): Promise<APIResponse<any>> {
    debugLog('Fetching index constituents', { indexId });
    
    return httpClient.get<any>(`/market/index-constituents/${indexId}`);
  }

  // Intelligence and Analysis endpoints
  async getComprehensiveAnalysis(symbol: string): Promise<APIResponse<any>> {
    debugLog('Fetching comprehensive analysis', { symbol });
    
    return httpClient.get<any>(`/intelligence/comprehensive-analysis/${symbol}`);
  }

  async getStockRecommendations(userPreferences: any): Promise<APIResponse<any>> {
    debugLog('Fetching stock recommendations', { userPreferences });
    
    return httpClient.post<any>('/intelligence/stock-recommendations', userPreferences);
  }

  async getMarketOverview(): Promise<APIResponse<any>> {
    debugLog('Fetching market overview');
    
    return httpClient.get<any>('/intelligence/market-overview');
  }

  async getSectorRotation(): Promise<APIResponse<any>> {
    debugLog('Fetching sector rotation');
    
    return httpClient.get<any>('/intelligence/sector-rotation');
  }

  async getSectorPerformance(): Promise<APIResponse<any>> {
    debugLog('Fetching sector performance');
    
    return httpClient.get<any>('/intelligence/sector-performance');
  }

  async getIndustrySummary(sector: string): Promise<APIResponse<any>> {
    debugLog('Fetching industry summary', { sector });
    
    return httpClient.get<any>(`/intelligence/industry-summary/${sector}`);
  }

  // Password reset methods
  async forgotPassword(payload: { email?: string; mobile_number?: string }): Promise<APIResponse<any>> {
    const requestId = generateRequestId();
    debugLog(`Forgot password request: ${requestId}`, payload);
    
    try {
      // httpClient.post returns APIResponse<T> directly (not response.data)
      const response = await httpClient.post<APIResponse<any>>('/api/auth/forgot-password', payload);
      debugLog(`Forgot password response: ${requestId}`, response);
      
      // Ensure response has success field (backend should return it, but handle gracefully)
      if (response && typeof response.success === 'boolean') {
        return response;
      } else {
        // If response doesn't have success, normalize it
        console.warn('Unexpected response format from backend:', response);
        return {
          success: (response as any)?.success ?? true, // Default to true if backend returned 200
          status: (response as any)?.status || 'success',
          message: (response as any)?.message || 'OTP sent',
          error: (response as any)?.error,
          timestamp: (response as any)?.timestamp || new Date().toISOString(),
          request_id: requestId
        } as APIResponse<any>;
      }
    } catch (error: any) {
      debugLog(`Forgot password error: ${requestId}`, error);
      throw error;
    }
  }

  async verifyResetOtp(identifier: string, otp: string): Promise<APIResponse<any>> {
    const requestId = generateRequestId();
    debugLog(`Verify reset OTP request: ${requestId}`, { identifier, otp });
    
    try {
      // httpClient.post returns APIResponse<T> directly (not response.data)
      const response = await httpClient.post<APIResponse<any>>('/api/auth/verify-reset-otp', { identifier, otp });
      debugLog(`Verify reset OTP response: ${requestId}`, response);
      
      // Ensure response has success field (backend should return it, but handle gracefully)
      if (response && typeof response.success === 'boolean') {
        return response;
      } else {
        // If response doesn't have success, normalize it
        console.warn('Unexpected response format from backend:', response);
        return {
          success: (response as any)?.success ?? true, // Default to true if backend returned 200
          status: (response as any)?.status || 'success',
          message: (response as any)?.message || 'OTP verified',
          error: (response as any)?.error,
          timestamp: (response as any)?.timestamp || new Date().toISOString(),
          request_id: requestId
        } as APIResponse<any>;
      }
    } catch (error: any) {
      debugLog(`Verify reset OTP error: ${requestId}`, error);
      throw error;
    }
  }

  async resetPassword(identifier: string, otp: string, password: string): Promise<APIResponse<any>> {
    const requestId = generateRequestId();
    debugLog(`Reset password request: ${requestId}`, { identifier, otp: '***' });
    
    try {
      // httpClient.post returns APIResponse<T> directly (not response.data)
      const response = await httpClient.post<APIResponse<any>>('/api/auth/reset-password', { identifier, otp, new_password: password });
      debugLog(`Reset password response: ${requestId}`, response);
      
      // Ensure response has success field (backend should return it, but handle gracefully)
      if (response && typeof response.success === 'boolean') {
        return response;
      } else {
        // If response doesn't have success, normalize it
        console.warn('Unexpected response format from backend:', response);
        return {
          success: (response as any)?.success ?? true, // Default to true if backend returned 200
          status: (response as any)?.status || 'success',
          message: (response as any)?.message || 'Password reset successful',
          error: (response as any)?.error,
          timestamp: (response as any)?.timestamp || new Date().toISOString(),
          request_id: requestId
        } as APIResponse<any>;
      }
    } catch (error: any) {
      debugLog(`Reset password error: ${requestId}`, error);
      throw error;
    }
  }

  // Stock List API methods (Webscraper Integration)
  async getAllStocks(): Promise<APIResponse<any>> {
    debugLog('Fetching all stocks from webscraper');
    
    const response = await httpClient.get<any>('/stocks/all');
    return response;
  }

  async getNSEStocks(): Promise<APIResponse<any>> {
    debugLog('Fetching NSE stocks from webscraper');
    
    const response = await httpClient.get<any>('/stocks/nse');
    return response;
  }

  async getBSEStocks(): Promise<APIResponse<any>> {
    debugLog('Fetching BSE stocks from webscraper');
    
    const response = await httpClient.get<any>('/stocks/bse');
    return response;
  }

  async searchStocks(query: string, exchange: string = 'ALL', limit: number = 50): Promise<APIResponse<any>> {
    debugLog('Searching stocks', { query, exchange, limit });
    
    const response = await httpClient.get<any>('/stocks/search', {
      query,
      exchange,
      limit
    });
    return response;
  }

  async getStockDetails(symbol: string, exchange: string = 'ALL'): Promise<APIResponse<any>> {
    debugLog('Fetching stock details', { symbol, exchange });
    
    const response = await httpClient.get<any>(`/stocks/${symbol}`, {
      exchange
    });
    return response;
  }

  // Additional methods
  async getFastInfo(symbol: string): Promise<APIResponse<FastInfo>> {
    const requestId = generateRequestId();
    debugLog(`Get fast info request: ${requestId}`, { symbol });
    
    try {
      const response = await httpClient.get(`/realtime/fast-info/${symbol}`);
      debugLog(`Get fast info response: ${requestId}`, response.data);
      return response.data as APIResponse<any>;
    } catch (error) {
      debugLog(`Get fast info error: ${requestId}`, error);
      throw error;
    }
  }

  async getIndicator(symbol: string, indicator: string): Promise<APIResponse<TechnicalIndicators>> {
    const requestId = generateRequestId();
    debugLog(`Get indicator request: ${requestId}`, { symbol, indicator });
    
    try {
      const response = await httpClient.get(`/realtime/indicators/${symbol}/${indicator}`);
      debugLog(`Get indicator response: ${requestId}`, response.data);
      return response.data as APIResponse<any>;
    } catch (error) {
      debugLog(`Get indicator error: ${requestId}`, error);
      throw error;
    }
  }

  // Generic HTTP methods for new endpoints
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<APIResponse<T>> {
    return httpClient.get<T>(endpoint, params);
  }

  async post<T>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return httpClient.post<T>(endpoint, data);
  }

  async put<T>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return httpClient.put<T>(endpoint, data);
  }

  async delete<T>(endpoint: string): Promise<APIResponse<T>> {
    return httpClient.delete<T>(endpoint);
  }

  async patch<T>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return httpClient.patch<T>(endpoint, data);
  }
}

// Create and export API service instance
export const api = new ApiService();

// Export error classes for external use
export { ApiError, NetworkError, TimeoutError, ValidationError } from '../config/api';

// Export default
export default api;