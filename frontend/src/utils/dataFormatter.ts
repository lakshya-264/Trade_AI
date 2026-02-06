/**
 * Data Formatter Utility
 * Ensures data from various sources matches the backend API schema
 */

/**
 * Format chart data for analysis APIs
 * Backend expects: { time: number, open: number, high: number, low: number, close: number, volume: number }
 */
export const formatChartDataForAnalysis = (chartData: any[]): any[] => {
  if (!chartData || !Array.isArray(chartData)) {
    return [];
  }

  const formatted = chartData.map((candle: any) => {
    // Handle different possible field names
    const time = candle.time || candle.timestamp || candle.date || Date.now();
    const open = Number(candle.open || candle.o || 0);
    const high = Number(candle.high || candle.h || 0);
    const low = Number(candle.low || candle.l || 0);
    const close = Number(candle.close || candle.c || 0);
    const volume = Number(candle.volume || candle.v || candle.vol || 0);

    return {
      time: typeof time === 'number' ? time : new Date(time).getTime() / 1000,
      open,
      high,
      low,
      close,
      volume
    };
  });

  // CRITICAL: Sort by time ascending (oldest first) for Lightweight Charts compatibility
  return formatted.sort((a, b) => a.time - b.time);
};

/**
 * Validate that chart data has minimum required candles
 */
export const validateChartData = (chartData: any[], minCandles: number = 20): boolean => {
  return Array.isArray(chartData) && chartData.length >= minCandles;
};

