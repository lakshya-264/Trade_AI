/**
 * Technical Indicators Calculator
 * Computes various technical indicators from chart data
 */

import { ChartData } from '../types/api';

export class TechnicalIndicatorsCalculator {
  /**
   * Calculate Simple Moving Average (SMA)
   */
  static sma(data: ChartData[], period: number, field: keyof ChartData = 'close'): number[] {
    const values = data.map(point => point[field] as number);
    const sma: number[] = [];
    
    for (let i = period - 1; i < values.length; i++) {
      const sum = values.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      sma.push(sum / period);
    }
    
    return sma;
  }

  /**
   * Calculate Exponential Moving Average (EMA)
   */
  static ema(data: ChartData[], period: number, field: keyof ChartData = 'close'): number[] {
    const values = data.map(point => point[field] as number);
    const ema: number[] = [];
    const multiplier = 2 / (period + 1);
    
    // First EMA is SMA
    if (values.length >= period) {
      const firstSMA = values.slice(0, period).reduce((a, b) => a + b, 0) / period;
      ema.push(firstSMA);
      
      // Calculate subsequent EMAs
      for (let i = period; i < values.length; i++) {
        const currentEMA = (values[i] * multiplier) + (ema[ema.length - 1] * (1 - multiplier));
        ema.push(currentEMA);
      }
    }
    
    return ema;
  }

  /**
   * Calculate Relative Strength Index (RSI)
   */
  static rsi(data: ChartData[], period: number = 14): number[] {
    const prices = data.map(point => point.close);
    const rsi: number[] = [];
    
    if (prices.length < period + 1) return rsi;
    
    const gains: number[] = [];
    const losses: number[] = [];
    
    // Calculate price changes
    for (let i = 1; i < prices.length; i++) {
      const change = prices[i] - prices[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }
    
    // Calculate initial average gain and loss
    let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;
    
    // Calculate RSI
    for (let i = period; i < gains.length; i++) {
      avgGain = ((avgGain * (period - 1)) + gains[i]) / period;
      avgLoss = ((avgLoss * (period - 1)) + losses[i]) / period;
      
      const rs = avgGain / avgLoss;
      const rsiValue = 100 - (100 / (1 + rs));
      rsi.push(rsiValue);
    }
    
    return rsi;
  }

  /**
   * Calculate MACD (Moving Average Convergence Divergence)
   */
  static macd(data: ChartData[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9): {
    macd: number[];
    signal: number[];
    histogram: number[];
  } {
    const prices = data.map(point => point.close);
    const ema12 = this.ema(data, fastPeriod);
    const ema26 = this.ema(data, slowPeriod);
    
    const macd: number[] = [];
    const signal: number[] = [];
    const histogram: number[] = [];
    
    // Calculate MACD line
    for (let i = 0; i < Math.min(ema12.length, ema26.length); i++) {
      macd.push(ema12[i] - ema26[i]);
    }
    
    // Calculate signal line (EMA of MACD)
    if (macd.length >= signalPeriod) {
      const macdData = macd.map((value, index) => ({
        close: value,
        timestamp: data[index + slowPeriod - 1]?.timestamp || 0
      }));
      const signalLine = this.ema(macdData as ChartData[], signalPeriod);
      
      // Calculate histogram
      for (let i = 0; i < Math.min(macd.length, signalLine.length); i++) {
        histogram.push(macd[i] - signalLine[i]);
      }
      
      return { macd, signal: signalLine, histogram };
    }
    
    return { macd, signal, histogram };
  }

  /**
   * Calculate Bollinger Bands
   */
  static bollingerBands(data: ChartData[], period: number = 20, stdDev: number = 2): {
    upper: number[];
    middle: number[];
    lower: number[];
  } {
    const prices = data.map(point => point.close);
    const sma = this.sma(data, period);
    
    const upper: number[] = [];
    const middle: number[] = sma;
    const lower: number[] = [];
    
    for (let i = period - 1; i < prices.length; i++) {
      const slice = prices.slice(i - period + 1, i + 1);
      const mean = slice.reduce((a, b) => a + b, 0) / period;
      const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
      const standardDeviation = Math.sqrt(variance);
      
      const upperBand = mean + (stdDev * standardDeviation);
      const lowerBand = mean - (stdDev * standardDeviation);
      
      upper.push(upperBand);
      lower.push(lowerBand);
    }
    
    return { upper, middle, lower };
  }

  /**
   * Calculate Stochastic Oscillator
   */
  static stochastic(data: ChartData[], kPeriod: number = 14, dPeriod: number = 3): {
    k: number[];
    d: number[];
  } {
    const k: number[] = [];
    const d: number[] = [];
    
    for (let i = kPeriod - 1; i < data.length; i++) {
      const slice = data.slice(i - kPeriod + 1, i + 1);
      const highest = Math.max(...slice.map(point => point.high));
      const lowest = Math.min(...slice.map(point => point.low));
      const currentClose = data[i].close;
      
      const kValue = ((currentClose - lowest) / (highest - lowest)) * 100;
      k.push(kValue);
    }
    
    // Calculate %D (SMA of %K)
    if (k.length >= dPeriod) {
      for (let i = dPeriod - 1; i < k.length; i++) {
        const dValue = k.slice(i - dPeriod + 1, i + 1).reduce((a, b) => a + b, 0) / dPeriod;
        d.push(dValue);
      }
    }
    
    return { k, d };
  }

  /**
   * Calculate Williams %R
   */
  static williamsR(data: ChartData[], period: number = 14): number[] {
    const williamsR: number[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const highest = Math.max(...slice.map(point => point.high));
      const lowest = Math.min(...slice.map(point => point.low));
      const currentClose = data[i].close;
      
      const wr = ((highest - currentClose) / (highest - lowest)) * -100;
      williamsR.push(wr);
    }
    
    return williamsR;
  }

  /**
   * Calculate Average True Range (ATR)
   */
  static atr(data: ChartData[], period: number = 14): number[] {
    const trueRanges: number[] = [];
    
    for (let i = 1; i < data.length; i++) {
      const current = data[i];
      const previous = data[i - 1];
      
      const tr1 = current.high - current.low;
      const tr2 = Math.abs(current.high - previous.close);
      const tr3 = Math.abs(current.low - previous.close);
      
      const trueRange = Math.max(tr1, tr2, tr3);
      trueRanges.push(trueRange);
    }
    
    // Calculate ATR as SMA of true ranges
    const atr: number[] = [];
    for (let i = period - 1; i < trueRanges.length; i++) {
      const sum = trueRanges.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      atr.push(sum / period);
    }
    
    return atr;
  }

  /**
   * Calculate On-Balance Volume (OBV)
   */
  static obv(data: ChartData[]): number[] {
    const obv: number[] = [];
    let cumulativeOBV = 0;
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        cumulativeOBV = data[i].volume;
      } else {
        const currentClose = data[i].close;
        const previousClose = data[i - 1].close;
        
        if (currentClose > previousClose) {
          cumulativeOBV += data[i].volume;
        } else if (currentClose < previousClose) {
          cumulativeOBV -= data[i].volume;
        }
        // If close is equal, OBV remains unchanged
      }
      
      obv.push(cumulativeOBV);
    }
    
    return obv;
  }

  /**
   * Calculate Money Flow Index (MFI)
   */
  static mfi(data: ChartData[], period: number = 14): number[] {
    const mfi: number[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      let positiveFlow = 0;
      let negativeFlow = 0;
      
      for (let j = 1; j < slice.length; j++) {
        const current = slice[j];
        const previous = slice[j - 1];
        
        const typicalPrice = (current.high + current.low + current.close) / 3;
        const previousTypicalPrice = (previous.high + previous.low + previous.close) / 3;
        
        const moneyFlow = typicalPrice * current.volume;
        
        if (typicalPrice > previousTypicalPrice) {
          positiveFlow += moneyFlow;
        } else if (typicalPrice < previousTypicalPrice) {
          negativeFlow += moneyFlow;
        }
      }
      
      const moneyFlowRatio = positiveFlow / negativeFlow;
      const mfiValue = 100 - (100 / (1 + moneyFlowRatio));
      mfi.push(mfiValue);
    }
    
    return mfi;
  }

  /**
   * Calculate all indicators for a dataset
   */
  static calculateAllIndicators(data: ChartData[]): ChartData[] {
    if (data.length < 50) return data; // Need sufficient data
    
    const enhancedData = [...data];
    
    // Calculate moving averages
    const sma20 = this.sma(data, 20);
    const sma50 = this.sma(data, 50);
    const ema12 = this.ema(data, 12);
    const ema26 = this.ema(data, 26);
    
    // Calculate momentum indicators
    const rsi = this.rsi(data, 14);
    const stochastic = this.stochastic(data, 14, 3);
    const williamsR = this.williamsR(data, 14);
    
    // Calculate trend indicators
    const macd = this.macd(data, 12, 26, 9);
    
    // Calculate volatility indicators
    const bollinger = this.bollingerBands(data, 20, 2);
    const atr = this.atr(data, 14);
    
    // Calculate volume indicators
    const obv = this.obv(data);
    const mfi = this.mfi(data, 14);
    
    // Apply indicators to data
    enhancedData.forEach((point, index) => {
      // Moving averages
      if (index >= 19) point.sma20 = sma20[index - 19];
      if (index >= 49) point.sma50 = sma50[index - 49];
      if (index >= 11) point.ema12 = ema12[index - 11];
      if (index >= 25) point.ema26 = ema26[index - 25];
      
      // Momentum indicators
      if (index >= 13) point.rsi = rsi[index - 13];
      if (index >= 13) point.stochastic_k = stochastic.k[index - 13];
      if (index >= 15) point.stochastic_d = stochastic.d[index - 15];
      if (index >= 13) point.williams_r = williamsR[index - 13];
      
      // Trend indicators
      if (index >= 25) {
        point.macd = macd.macd[index - 25];
        point.macd_signal = macd.signal[index - 25];
        point.macd_histogram = macd.histogram[index - 25];
      }
      
      // Volatility indicators
      if (index >= 19) {
        point.bbands_upper = bollinger.upper[index - 19];
        point.bbands_middle = bollinger.middle[index - 19];
        point.bbands_lower = bollinger.lower[index - 19];
      }
      if (index >= 13) point.atr = atr[index - 13];
      
      // Volume indicators
      point.obv = obv[index];
      if (index >= 13) point.mfi = mfi[index - 13];
    });
    
    return enhancedData;
  }
}

export default TechnicalIndicatorsCalculator;
