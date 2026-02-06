import { api } from './api';
import { TokenManager } from '../config/api';

// Cache TTL constants (in milliseconds)
const CACHE_TTL = {
  QUOTE: 30 * 1000, // 30 seconds
  PORTFOLIO: 60 * 1000, // 1 minute
  GAINERS_LOSERS: 2 * 60 * 1000, // 2 minutes
  MARKET_DATA: 5 * 60 * 1000, // 5 minutes
  ANALYTICS: 10 * 60 * 1000, // 10 minutes
  USER_DATA: 15 * 60 * 1000, // 15 minutes
};

// Simple cache implementation for service layer
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class SimpleCache {
  private cache = new Map<string, CacheEntry<any>>();

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  set<T>(key: string, data: T, ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  remove(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  get size(): number {
    return this.cache.size;
  }
}

class CachedApiService {
  private cache = new SimpleCache();

  // Generate cache key
  private getCacheKey(endpoint: string, params?: Record<string, any>): string {
    const paramString = params ? JSON.stringify(params) : '';
    return `${endpoint}${paramString}`;
  }

  // Cached API calls
  async getQuote(symbol: string, exchange: string = 'NSE') {
    const cacheKey = this.getCacheKey('quote', { symbol, exchange });
    
    // Check cache first
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Fetch from API
    const data = await api.getQuote(symbol, exchange);
    
    // Cache the result
    this.cache.set(cacheKey, data, CACHE_TTL.QUOTE);
    
    return data;
  }

  async getPortfolio() {
    const cacheKey = this.getCacheKey('portfolio');
    
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Avoid unauthenticated calls that would return 403
    const token = TokenManager.getToken();
    if (!token) {
      return { portfolio: [], total_value: 0, total_pnl: 0 } as any;
    }

    const data = await api.getPortfolio();
    this.cache.set(cacheKey, data, CACHE_TTL.PORTFOLIO);
    
    return data;
  }

  async getTopGainers() {
    const cacheKey = this.getCacheKey('top-gainers');
    
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    const data = await api.getTopGainers();
    this.cache.set(cacheKey, data, CACHE_TTL.GAINERS_LOSERS);
    
    return data;
  }

  async getTopLosers() {
    const cacheKey = this.getCacheKey('top-losers');
    
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    const data = await api.getTopLosers();
    this.cache.set(cacheKey, data, CACHE_TTL.GAINERS_LOSERS);
    
    return data;
  }

  async getMarketSummary() {
    const cacheKey = this.getCacheKey('market-summary');
    
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    const data = await api.getMarketSummary();
    this.cache.set(cacheKey, data, CACHE_TTL.MARKET_DATA);
    
    return data;
  }

  async getMarketData(symbol: string, timeframe: string = '1d') {
    const cacheKey = this.getCacheKey('market-data', { symbol, timeframe });
    
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Use getHistoricalData as fallback since getMarketData doesn't exist
    const data = await api.getHistoricalData(symbol, 'NSE');
    this.cache.set(cacheKey, data, CACHE_TTL.MARKET_DATA);
    
    return data;
  }

  async getAnalytics() {
    const cacheKey = this.getCacheKey('analytics');
    
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Use getTradingSignals as fallback since getAnalytics doesn't exist
    const data = await api.getTradingSignals();
    this.cache.set(cacheKey, data, CACHE_TTL.ANALYTICS);
    
    return data;
  }

  async getRiskMetrics() {
    const cacheKey = this.getCacheKey('risk-metrics');
    
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    const data = await api.getRiskMetrics();
    this.cache.set(cacheKey, data, CACHE_TTL.ANALYTICS);
    
    return data;
  }

  // Invalidate specific cache entries
  invalidateQuote(symbol: string, exchange: string = 'NSE') {
    const cacheKey = this.getCacheKey('quote', { symbol, exchange });
    this.cache.remove(cacheKey);
  }

  invalidatePortfolio() {
    this.cache.remove(this.getCacheKey('portfolio'));
  }

  invalidateMarketData() {
    this.cache.remove(this.getCacheKey('top-gainers'));
    this.cache.remove(this.getCacheKey('top-losers'));
  }

  // Clear all cache
  clearCache() {
    this.cache.clear();
  }

  // Get cache statistics
  getCacheStats() {
    return {
      size: this.cache.size,
      // Add more stats as needed
    };
  }
}

// Export singleton instance
export const cachedApi = new CachedApiService();
export default cachedApi;
