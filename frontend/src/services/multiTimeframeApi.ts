/**
 * Multi-Timeframe Analysis API Service
 * Handles fetching and analyzing data across multiple timeframes
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface TimeframeConfig {
  value: string;
  label: string;
  interval: string;
  period: string;
  weight: number;
  category: 'intraday' | 'daily';
}

export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MultiTimeframeDataResponse {
  success: boolean;
  symbol: string;
  data: Record<string, CandleData[]>;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface TimeframeAnalysis {
  timeframe: string;
  structure?: any;
  sr?: any;
  sd?: any;
  trendlines?: any;
  swings?: any;
  trend?: string;
  confidence?: number;
  last_bos?: string;
}

export interface MultiTimeframeAnalysisResponse {
  success: boolean;
  symbol: string;
  analyses: Record<string, TimeframeAnalysis>;
  timestamp: string;
}

export interface AlignmentData {
  timeframes: Record<string, {
    trend: string;
    confidence: number;
    structure: string;
    last_bos: string;
  }>;
  overall: {
    verdict: string;
    confidence: number;
    alignment_pct: number;
    bullish_count: number;
    bearish_count: number;
    total_count: number;
    agreement: string;
    recommendation: string;
  };
}

export interface TimeframeAlignmentResponse {
  success: boolean;
  symbol: string;
  alignment: AlignmentData;
  timestamp: string;
}

export const multiTimeframeApi = {
  /**
   * Fetch candlestick data for multiple timeframes
   */
  async getMultiTimeframeData(
    symbol: string,
    timeframes: string[],
    limit: number = 500
  ): Promise<MultiTimeframeDataResponse> {
    try {
      const response = await axios.post<MultiTimeframeDataResponse>(
        `${API_BASE_URL}/multi-timeframe/data`,
        {
          symbol,
          timeframes,
          limit,
        }
      );
      return response.data;
    } catch (error: any) {
      console.error('Error fetching multi-timeframe data:', error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch multi-timeframe data');
    }
  },

  /**
   * Analyze multiple timeframes with specified analysis types
   */
  async analyzeMultiTimeframe(
    symbol: string,
    timeframes: string[],
    analysisTypes: string[] = ['structure', 'sr', 'sd']
  ): Promise<MultiTimeframeAnalysisResponse> {
    try {
      const response = await axios.post<MultiTimeframeAnalysisResponse>(
        `${API_BASE_URL}/multi-timeframe/analyze`,
        {
          symbol,
          timeframes,
          analysis_types: analysisTypes,
        }
      );
      return response.data;
    } catch (error: any) {
      console.error('Error analyzing multi-timeframe:', error);
      throw new Error(error.response?.data?.detail || 'Failed to analyze multi-timeframe');
    }
  },

  /**
   * Calculate timeframe alignment and trend agreement
   */
  async getTimeframeAlignment(
    symbol: string,
    timeframes: string[]
  ): Promise<TimeframeAlignmentResponse> {
    try {
      const response = await axios.post<TimeframeAlignmentResponse>(
        `${API_BASE_URL}/multi-timeframe/alignment`,
        {
          symbol,
          timeframes,
        }
      );
      return response.data;
    } catch (error: any) {
      console.error('Error getting timeframe alignment:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get timeframe alignment');
    }
  },

  /**
   * Get list of available timeframes
   */
  async getAvailableTimeframes(): Promise<{ success: boolean; timeframes: TimeframeConfig[] }> {
    try {
      const response = await axios.get<{ success: boolean; timeframes: TimeframeConfig[] }>(
        `${API_BASE_URL}/multi-timeframe/timeframes`
      );
      return response.data;
    } catch (error: any) {
      console.error('Error fetching available timeframes:', error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch available timeframes');
    }
  },
};

export default multiTimeframeApi;

