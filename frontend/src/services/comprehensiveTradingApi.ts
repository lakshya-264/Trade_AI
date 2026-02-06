import { httpClient } from '../config/api';

export interface ChartDataRequest {
  symbol: string;
  timeframe: string;
  period?: number;
}

export interface PatternAnalyzeRequest {
  symbol: string;
  timeframe: string;
  patterns: string[];
}

export interface VolumeAnalyzeRequest {
  symbol: string;
  timeframe: string;
}

export interface RecommendationRequest {
  symbol: string;
  timeframe?: string;
}

class ComprehensiveTradingApiService {
  private base = '/comprehensive-trading';

  async getSystemStatus() {
    const res = await httpClient.get<any>(`${this.base}/system/status`);
    return (res as any).data ?? res;
  }

  async getSystemPerformance() {
    const res = await httpClient.get<any>(`${this.base}/system/performance`);
    return (res as any).data ?? res;
  }

  async getAvailablePatterns() {
    const res = await httpClient.get<any>(`${this.base}/patterns/available`);
    // Backend returns { success, patterns, count, message }
    return (res as any).patterns ?? (res as any).data ?? [];
  }


  async getChartData(payload: ChartDataRequest) {
    const res = await httpClient.post<any>(`${this.base}/chart-data`, payload);
    // Backend returns { success, data: { candlesticks: [...] }, timestamp, message }
    const chartData = (res as any).data ?? res;
    // Convert candlesticks to candles format if needed
    if (chartData.candlesticks && !chartData.candles) {
      chartData.candles = chartData.candlesticks;
    }
    return chartData;
  }

  async analyzePatterns(payload: PatternAnalyzeRequest) {
    const res = await httpClient.post<any>(`${this.base}/patterns/analyze`, payload);
    // Backend returns { success, symbol, timeframe, detected_patterns, ... }
    // Convert detected_patterns to patterns for frontend
    if ((res as any).detected_patterns && !(res as any).patterns) {
      return { patterns: (res as any).detected_patterns };
    }
    return (res as any).data ?? res;
  }

  async analyzeVolume(payload: VolumeAnalyzeRequest) {
    const res = await httpClient.post<any>(`${this.base}/volume/analyze`, payload);
    return (res as any).data ?? res;
  }

  async generateRecommendation(payload: RecommendationRequest & { analysis_data?: any; user_preferences?: any }) {
    const body = {
      symbol: payload.symbol,
      timeframe: payload.timeframe || '1D',
      analysis_data: payload.analysis_data ?? {},
      user_preferences: payload.user_preferences ?? {},
    };
    const res = await httpClient.post<any>(`${this.base}/recommendations/generate`, body);
    // Backend returns { success, recommendation, timestamp, message }
    return (res as any).recommendation ?? (res as any).data ?? res;
  }

  async optionsSuggestion(payload: RecommendationRequest & { underlying_price?: number; days_to_expiry?: number; option_type?: 'call' | 'put'; risk_tolerance?: 'low' | 'medium' | 'high' }) {
    const q = new URLSearchParams();
    q.set('symbol', payload.symbol);
    q.set('underlying_price', String(payload.underlying_price ?? 100));
    q.set('days_to_expiry', String(payload.days_to_expiry ?? 30));
    q.set('option_type', (payload.option_type ?? 'call'));
    q.set('risk_tolerance', (payload.risk_tolerance ?? 'medium'));
    const res = await httpClient.post<any>(`${this.base}/recommendations/options-suggestion?${q.toString()}`);
    // Backend returns { success, suggestion, timestamp, message }
    return (res as any).suggestion ?? (res as any).data ?? res;
  }

  async getOptionsStrategies() {
    const res = await httpClient.get<any>(`${this.base}/options/strategies`);
    return (res as any).data ?? res;
  }

  async analyzeOptionsChain(payload: { symbol: string }) {
    const res = await httpClient.post<any>(`${this.base}/options/analyze`, payload);
    return (res as any).data ?? res;
  }

  async getAlerts() {
    const res = await httpClient.get<any>(`${this.base}/alerts`);
    // Backend returns { success, alerts, count, message }
    return (res as any).alerts ?? (res as any).data ?? [];
  }

  async createAlert(payload: any) {
    const body = {
      symbol: payload.symbol,
      rule: payload.rule ?? 'price_cross',
      operator: payload.operator ?? 'gt',
      value: payload.value ?? 0,
      notifications: payload.notifications ?? { email: false, sms: false, push: true },
    };
    const res = await httpClient.post<any>(`${this.base}/alerts`, body);
    return (res as any).data ?? res;
  }

  async updateAlert(alertId: string, updates: any) {
    const res = await httpClient.put<any>(`${this.base}/alerts/${alertId}`, updates);
    return (res as any).data ?? res;
  }

  async deleteAlert(alertId: string) {
    const res = await httpClient.delete<any>(`${this.base}/alerts/${alertId}`);
    return (res as any).data ?? res;
  }

  async createWatchlist(payload: { name: string; symbols: string[] }) {
    const q = new URLSearchParams();
    q.set('name', payload.name);
    for (const s of payload.symbols || []) q.append('symbols', s);
    const res = await httpClient.post<any>(`${this.base}/watchlists?${q.toString()}`);
    return (res as any).data ?? res;
  }

  async getWatchlists() {
    const res = await httpClient.get<any>(`${this.base}/watchlists`);
    // Backend returns { success, watchlists, count, message }
    return (res as any).watchlists ?? (res as any).data ?? [];
  }

  async updateWatchlist(watchlistId: string, updates: any) {
    const res = await httpClient.put<any>(`${this.base}/watchlists/${watchlistId}`, updates);
    return (res as any).data ?? res;
  }

  async deleteWatchlist(watchlistId: string) {
    const res = await httpClient.delete<any>(`${this.base}/watchlists/${watchlistId}`);
    return (res as any).data ?? res;
  }

  async addSymbolToWatchlist(watchlistId: string, symbol: string) {
    const q = new URLSearchParams();
    q.set('symbol', symbol);
    const res = await httpClient.post<any>(`${this.base}/watchlists/${watchlistId}/symbols?${q.toString()}`);
    return (res as any).data ?? res;
  }

  async removeSymbolFromWatchlist(watchlistId: string, symbol: string) {
    const q = new URLSearchParams();
    q.set('symbol', symbol);
    const res = await httpClient.delete<any>(`${this.base}/watchlists/${watchlistId}/symbols?${q.toString()}`);
    return (res as any).data ?? res;
  }

  async calculateIndicator(payload: any) {
    const res = await httpClient.post<any>(`${this.base}/indicators/calculate`, payload);
    return (res as any).data ?? res;
  }

  async saveDrawing(payload: any) {
    const res = await httpClient.post<any>(`${this.base}/drawings`, payload);
    return (res as any).data ?? res;
  }

  async getDrawings(chart_id: string) {
    const res = await httpClient.get<any>(`${this.base}/drawings/${encodeURIComponent(chart_id)}`);
    return (res as any).data ?? res;
  }

  // Teaching flows
  async getTeachingFlows() {
    const res = await httpClient.get<any>(`${this.base}/teaching/flows`);
    return (res as any).data ?? res;
  }

  async getTeachingQuiz(flowId: string, level: string = 'beginner') {
    const res = await httpClient.get<any>(`${this.base}/teaching/quiz/${flowId}?level=${level}`);
    return (res as any).data ?? res;
  }

  async submitQuizAnswers(flowId: string, answers: any) {
    const res = await httpClient.post<any>(`${this.base}/teaching/quiz/${flowId}/submit`, answers);
    return (res as any).data ?? res;
  }

  // Options strategy views
  async getOptionsStrategyViews(symbol: string, currentPrice: number, daysToExpiry: number = 30) {
    const res = await httpClient.get<any>(`${this.base}/options/strategy-views?symbol=${symbol}&current_price=${currentPrice}&days_to_expiry=${daysToExpiry}`);
    return (res as any).data ?? res;
  }


  // WebSocket connections
  connectRealTimeQuotes() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host.replace('3000', '8000')}/api/comprehensive-trading/ws/real-time-quotes`;
    return new WebSocket(wsUrl);
  }

  connectMarketAlerts() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host.replace('3000', '8000')}/api/comprehensive-trading/ws/market-alerts`;
    return new WebSocket(wsUrl);
  }

  connectChartData(symbol: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host.replace('3000', '8000')}/api/comprehensive-trading/ws/chart-data/${symbol}`;
    return new WebSocket(wsUrl);
  }

  connectTradingSignals() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host.replace('3000', '8000')}/api/comprehensive-trading/ws/trading-signals`;
    return new WebSocket(wsUrl);
  }

  // Smart Money Volume Activity
  async getSmartMoneyVolumeActivity(params: { symbol: string; timeframe?: string; lower_timeframe?: string; z_len?: number; threshold_abs?: number; who?: 'Both'|'Retail'|'Smart Money'; }) {
    const { symbol, timeframe = '1D', lower_timeframe = '5m', z_len = 50, threshold_abs = 2.0, who = 'Both' } = params;
    const q = `symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&lower_timeframe=${encodeURIComponent(lower_timeframe)}&z_len=${z_len}&threshold_abs=${threshold_abs}&who=${encodeURIComponent(who)}`;
    const res = await httpClient.get<any>(`${this.base}/smart-money/volume-activity?${q}`);
    // Backend returns { success, data: { levels, bubble, pl, count }, message }
    return (res as any).data ?? res;
  }



  
  // Smart Money Volume Alerts
  async createSmartMoneyAlert(symbol: string, activityType: string, notifications: any = { in_app: true, email: false }, cooldownMinutes: number = 30) {
    const res = await httpClient.post<any>(`${this.base}/smart-money-alerts/create`, {
      symbol,
      activity_type: activityType,
      notifications,
      cooldown_minutes: cooldownMinutes
    });
    return (res as any).data ?? res;
  }

  async testSmartMoneyAlert(symbol: string) {
    const res = await httpClient.post<any>(`${this.base}/smart-money-alerts/test/${symbol}`);
    return (res as any).data ?? res;
  }

  // WebSocket connections for SMV alerts
  connectSmartMoneyAlerts(userId: string, onAlert?: (alert: any) => void) {
    const ws = new WebSocket(`ws://127.0.0.1:8000/api/comprehensive-trading/ws/smart-money-alerts/${userId}`);
    ws.onopen = () => console.log('SMV Alerts WebSocket connected');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'smart_money_volume_alert') {
        // Handle SMV alert
        console.log('SMV Alert received:', data);
        if (onAlert) {
          onAlert(data);
        }
      }
    };
    ws.onclose = () => console.log('SMV Alerts WebSocket disconnected');
    ws.onerror = (error) => console.error('SMV Alerts WebSocket error:', error);
    return ws;
  }

  // Symbol Search
  async searchSymbols(query: string, limit: number = 10) {
    const res = await httpClient.get<any>(`${this.base}/search?query=${encodeURIComponent(query)}&limit=${limit}`);
    return (res as any).data ?? res;
  }

  async getVolumeProfile(params: { symbol: string; timeframe: string; price_bins?: number }) {
    const q = new URLSearchParams();
    q.set('symbol', params.symbol);
    q.set('timeframe', params.timeframe);
    if (params.price_bins) q.set('price_bins', String(params.price_bins));
    const res = await httpClient.get<any>(`${this.base}/charts/volume-profile?${q.toString()}`);
    return (res as any).data ?? res;
  }

  async getOrderFlow(params: { symbol: string; timeframe: string }) {
    const q = new URLSearchParams();
    q.set('symbol', params.symbol);
    q.set('timeframe', params.timeframe);
    const res = await httpClient.get<any>(`${this.base}/charts/order-flow?${q.toString()}`);
    return (res as any).data ?? res;
  }

  async getMarketProfile(params: { symbol: string; timeframe: string; time_period?: string }) {
    const q = new URLSearchParams();
    q.set('symbol', params.symbol);
    q.set('timeframe', params.timeframe);
    if (params.time_period) q.set('time_period', params.time_period);
    const res = await httpClient.get<any>(`${this.base}/charts/market-profile?${q.toString()}`);
    return (res as any).data ?? res;
  }
}

export const comprehensiveTradingApi = new ComprehensiveTradingApiService();
export default comprehensiveTradingApi;


