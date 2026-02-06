/**
 * Candle Data API Service
 * Fetches OHLCV candlestick data from Yahoo Finance web scraper
 */

import { httpClient } from '../config/api';

export interface Candle {
  time: number;  // Unix timestamp
  timestamp: string;  // ISO format
  date: string;  // Human readable
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  symbol: string;
}

export interface CandleDataResponse {
  success: boolean;
  symbol: string;
  interval: string;
  range: string;
  data: Candle[];
  count: number;
  timestamp: string;
  data_source: string;
}

export interface OHLCSummaryResponse {
  success: boolean;
  symbol: string;
  interval: string;
  range: string;
  candle_count: number;
  summary: {
    first_open: number;
    last_close: number;
    highest_high: number;
    lowest_low: number;
    total_volume: number;
    average_volume: number;
    price_change: number;
    price_change_percent: number;
  };
  first_candle: Candle;
  last_candle: Candle;
  highest_candle: Candle;
  lowest_candle: Candle;
}

class CandleDataApiService {
  /**
   * Get historical candlestick data
   * @param symbol Stock symbol (e.g., "RELIANCE", "NIFTY_50")
   * @param interval Candle interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
   * @param range Time range: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
   */
  async getCandles(
    symbol: string,
    interval: string = '1d',
    range: string = '1mo'
  ): Promise<CandleDataResponse> {
    try {
      console.log(`[CandleDataApi] Fetching candles for ${symbol}...`);
      const response = await httpClient.get<any>(
        `/api/candles/${symbol}`,
        { interval, range }
      );
      
      console.log(`[CandleDataApi] Raw response:`, response);
      
      // httpClient may wrap the response, need to extract properly
      let backendResponse = (response as any).data || response;
      
      console.log(`[CandleDataApi] Backend response:`, backendResponse);
      console.log(`[CandleDataApi] Is array?`, Array.isArray(backendResponse));
      
      // If backend response is directly an array, wrap it properly
      if (Array.isArray(backendResponse)) {
        console.log(`[CandleDataApi] Wrapping array response (length: ${backendResponse.length})`);
        backendResponse = {
          success: true,
          symbol: symbol,
          interval: interval,
          range: range,
          data: backendResponse,
          count: backendResponse.length,
          timestamp: new Date().toISOString(),
          data_source: 'YAHOO_FINANCE_API'
        };
      }
      
      console.log(`[CandleDataApi] Final response:`, backendResponse);
      console.log(`[CandleDataApi] Has success?`, backendResponse.success);
      console.log(`[CandleDataApi] Data is array?`, Array.isArray(backendResponse.data));
      console.log(`[CandleDataApi] Data length:`, backendResponse.data?.length);
      
      return backendResponse;
    } catch (error) {
      console.error(`[CandleDataApi] Error fetching candles for ${symbol}:`, error);
      throw error;
    }
  }

  /**
   * Get latest candle for a symbol
   */
  async getLatestCandle(
    symbol: string,
    interval: string = '1d'
  ): Promise<{ success: boolean; symbol: string; data: Candle }> {
    try {
      const response = await httpClient.get(
        `/api/candles/${symbol}/latest`,
        { interval }
      );
      return response as any;
    } catch (error) {
      console.error(`Error fetching latest candle for ${symbol}:`, error);
      throw error;
    }
  }

  /**
   * Get OHLC summary statistics
   */
  async getOHLCSummary(
    symbol: string,
    interval: string = '1d',
    range: string = '1mo'
  ): Promise<OHLCSummaryResponse> {
    try {
      const response = await httpClient.get<OHLCSummaryResponse>(
        `/candles/${symbol}/ohlc`,
        { params: { interval, range } }
      );
      // Handle both wrapped and unwrapped responses
      return (response as any).data || response;
    } catch (error) {
      console.error(`Error fetching OHLC summary for ${symbol}:`, error);
      throw error;
    }
  }

  /**
   * Get candles for multiple symbols (batch)
   */
  async getMultipleCandles(
    symbols: string[],
    interval: string = '1d',
    range: string = '1mo'
  ): Promise<Map<string, CandleDataResponse>> {
    const results = new Map<string, CandleDataResponse>();
    
    // Fetch in parallel with delay to avoid rate limiting
    for (let i = 0; i < symbols.length; i++) {
      try {
        const data = await this.getCandles(symbols[i], interval, range);
        results.set(symbols[i], data);
        
        // Add small delay to avoid rate limiting (only if not last item)
        if (i < symbols.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      } catch (error) {
        console.error(`Failed to fetch ${symbols[i]}:`, error);
      }
    }
    
    return results;
  }

  /**
   * Get NIFTY 50 stocks data
   */
  async getNifty50Candles(
    interval: string = '1d',
    range: string = '1mo'
  ): Promise<Map<string, CandleDataResponse>> {
    const nifty50Symbols = [
      'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
      'ICICIBANK', 'KOTAKBANK', 'ITC', 'BHARTIARTL', 'SBIN',
      'BAJFINANCE', 'ASIANPAINT', 'AXISBANK', 'MARUTI', 'SUNPHARMA',
      'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'POWERGRID', 'NTPC',
      'TECHM', 'WIPRO', 'HCLTECH', 'LT', 'BAJAJFINSV'
    ];
    
    return this.getMultipleCandles(nifty50Symbols, interval, range);
  }

  /**
   * Convert candles to Lightweight Charts format
   */
  convertToLightweightChartsFormat(candles: Candle[]): any[] {
    return candles.map(candle => ({
      time: candle.time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close
    }));
  }

  /**
   * Convert volume data to Lightweight Charts format
   */
  convertVolumeToLightweightChartsFormat(candles: Candle[]): any[] {
    return candles.map(candle => ({
      time: candle.time,
      value: candle.volume,
      color: candle.close >= candle.open ? '#26a69a' : '#ef5350'
    }));
  }
}

// Export singleton instance
const candleDataApi = new CandleDataApiService();
export default candleDataApi;

