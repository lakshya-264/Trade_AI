import React, { useEffect, useRef, useMemo } from 'react';
import { ISeriesApi, IChartApi, Time } from 'lightweight-charts';

interface IndicatorConfig {
  name: string;
  type: 'SMA' | 'EMA' | 'RSI' | 'MACD' | 'BB' | 'ATR' | 'STOCH';
  period: number;
  color: string;
  visible: boolean;
  params?: Record<string, any>;
}

interface LightweightChartIndicatorsProps {
  chart: IChartApi | null;
  candlestickSeries: ISeriesApi<'Candlestick'> | null;
  data: Array<{ time: number; open: number; high: number; low: number; close: number; volume: number }>;
  indicators: IndicatorConfig[];
  onIndicatorsChange?: (indicators: IndicatorConfig[]) => void;
}

const LightweightChartIndicators: React.FC<LightweightChartIndicatorsProps> = ({
  chart,
  candlestickSeries,
  data,
  indicators,
  onIndicatorsChange
}) => {
  const seriesRefs = useRef<Map<string, ISeriesApi<'Line' | 'Histogram'>>>(new Map());
  const lastDataHashRef = useRef<string>('');
  const lastIndicatorsHashRef = useRef<string>('');

  // Memoize visible indicators to prevent unnecessary recalculations
  const visibleIndicators = useMemo(() => {
    return indicators.filter(ind => ind.visible);
  }, [indicators]);

  // Create hash of data to detect changes
  const dataHash = useMemo(() => {
    if (!data || data.length === 0) return '';
    return `${data.length}-${data[0]?.time}-${data[data.length - 1]?.time}`;
  }, [data]);

  // Create hash of indicators to detect changes
  const indicatorsHash = useMemo(() => {
    return visibleIndicators.map(ind => `${ind.name}-${ind.type}-${ind.period}-${ind.color}-${ind.visible}`).join('|');
  }, [visibleIndicators]);

  // Calculate SMA
  const calculateSMA = (data: number[], period: number): number[] => {
    const result: number[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(NaN);
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / period);
      }
    }
    return result;
  };

  // Calculate EMA
  const calculateEMA = (data: number[], period: number): number[] => {
    const result: number[] = [];
    const multiplier = 2 / (period + 1);
    let ema = data[0];
    result.push(ema);
    
    for (let i = 1; i < data.length; i++) {
      ema = (data[i] - ema) * multiplier + ema;
      result.push(ema);
    }
    return result;
  };

  // Calculate RSI
  const calculateRSI = (closes: number[], period: number = 14): number[] => {
    const result: number[] = [];
    const gains: number[] = [];
    const losses: number[] = [];

    for (let i = 1; i < closes.length; i++) {
      const change = closes[i] - closes[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }

    let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

    for (let i = 0; i < period; i++) {
      result.push(NaN);
    }

    for (let i = period; i < closes.length; i++) {
      avgGain = (avgGain * (period - 1) + gains[i - 1]) / period;
      avgLoss = (avgLoss * (period - 1) + losses[i - 1]) / period;
      const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      result.push(100 - (100 / (1 + rs)));
    }

    return result;
  };

  // Calculate MACD
  const calculateMACD = (closes: number[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) => {
    const fastEMA = calculateEMA(closes, fastPeriod);
    const slowEMA = calculateEMA(closes, slowPeriod);
    const macdLine = fastEMA.map((fast, i) => fast - slowEMA[i]);
    const signalLine = calculateEMA(macdLine.filter(v => !isNaN(v)), signalPeriod);
    const histogram = macdLine.map((macd, i) => {
      const signal = signalLine[i] || 0;
      return isNaN(macd) ? NaN : macd - signal;
    });

    return { macdLine, signalLine, histogram };
  };

  // Calculate Bollinger Bands
  const calculateBollingerBands = (closes: number[], period: number = 20, stdDev: number = 2) => {
    const sma = calculateSMA(closes, period);
    const result: { upper: number[]; middle: number[]; lower: number[] } = {
      upper: [],
      middle: sma,
      lower: []
    };

    for (let i = 0; i < closes.length; i++) {
      if (i < period - 1) {
        result.upper.push(NaN);
        result.lower.push(NaN);
      } else {
        const slice = closes.slice(i - period + 1, i + 1);
        const mean = sma[i];
        const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period;
        const std = Math.sqrt(variance);
        result.upper.push(mean + stdDev * std);
        result.lower.push(mean - stdDev * std);
      }
    }

    return result;
  };

  useEffect(() => {
    if (!chart || !candlestickSeries || !data.length) return;

    // Skip if data and indicators haven't changed
    if (dataHash === lastDataHashRef.current && indicatorsHash === lastIndicatorsHashRef.current) {
      return;
    }

    // Update refs
    lastDataHashRef.current = dataHash;
    lastIndicatorsHashRef.current = indicatorsHash;

    // Clear existing indicators
    seriesRefs.current.forEach(series => {
      try {
        chart.removeSeries(series);
      } catch (e) {
        console.warn('Error removing series:', e);
      }
    });
    seriesRefs.current.clear();

    // Add indicators - only process visible ones
    visibleIndicators.forEach(indicator => {

      const closes = data.map(d => d.close);
      let indicatorData: Array<{ time: Time; value: number }> = [];

      switch (indicator.type) {
        case 'SMA':
          const smaValues = calculateSMA(closes, indicator.period);
          indicatorData = data.map((d, i) => ({
            time: d.time as Time,
            value: smaValues[i]
          })).filter(d => !isNaN(d.value));
          
          if (indicatorData.length > 0) {
            const series = chart.addLineSeries({
              color: indicator.color,
              lineWidth: 2,
              title: `${indicator.name} (${indicator.period})`,
              priceLineVisible: false,
              lastValueVisible: true,
            });
            series.setData(indicatorData as any);
            seriesRefs.current.set(indicator.name, series);
          }
          break;

        case 'EMA':
          const emaValues = calculateEMA(closes, indicator.period);
          indicatorData = data.map((d, i) => ({
            time: d.time as Time,
            value: emaValues[i]
          })).filter(d => !isNaN(d.value));
          
          if (indicatorData.length > 0) {
            const series = chart.addLineSeries({
              color: indicator.color,
              lineWidth: 2,
              title: `${indicator.name} (${indicator.period})`,
              priceLineVisible: false,
              lastValueVisible: true,
            });
            series.setData(indicatorData as any);
            seriesRefs.current.set(indicator.name, series);
          }
          break;

        case 'RSI':
          const rsiValues = calculateRSI(closes, indicator.period);
          indicatorData = data.map((d, i) => ({
            time: d.time as Time,
            value: rsiValues[i]
          })).filter(d => !isNaN(d.value));
          
          if (indicatorData.length > 0) {
            // Create separate pane for RSI
            const series = chart.addLineSeries({
              color: indicator.color,
              lineWidth: 2,
              title: `${indicator.name} (${indicator.period})`,
              priceScaleId: 'rsi',
              priceFormat: {
                type: 'price',
                precision: 2,
                minMove: 0.01,
              },
            });
            series.setData(indicatorData as any);
            
            // Add overbought/oversold lines
            chart.priceScale('rsi').applyOptions({
              scaleMargins: {
                top: 0.1,
                bottom: 0.1,
              },
            });
            
            seriesRefs.current.set(indicator.name, series);
          }
          break;

        case 'MACD':
          const macd = calculateMACD(closes, 12, 26, 9);
          // Map MACD data - filter NaN values
          const macdData = data.map((d, i) => ({
            time: d.time as Time,
            value: macd.macdLine[i]
          })).filter(d => !isNaN(d.value));
          
          // Map signal data - filter NaN values (signal line is already aligned with MACD line)
          const signalData = data.map((d, i) => ({
            time: d.time as Time,
            value: macd.signalLine[i]
          })).filter(d => !isNaN(d.value));
          
          // Map histogram data - filter NaN values (histogram is already aligned with MACD line)
          const histogramData = data.map((d, i) => ({
            time: d.time as Time,
            value: macd.histogram[i],
            color: !isNaN(macd.histogram[i]) && macd.histogram[i] >= 0 ? '#26a69a' : '#ef5350'
          })).filter(d => !isNaN(d.value));
          
          if (macdData.length > 0) {
            const macdSeries = chart.addLineSeries({
              color: indicator.color,
              lineWidth: 2,
              title: 'MACD',
            });
            macdSeries.setData(macdData as any);
            seriesRefs.current.set('MACD', macdSeries);

            const signalSeries = chart.addLineSeries({
              color: '#ef5350',
              lineWidth: 1,
              title: 'Signal',
            });
            signalSeries.setData(signalData as any);
            seriesRefs.current.set('MACD Signal', signalSeries);

            const histogramSeries = chart.addHistogramSeries({
              color: '#26a69a',
              title: 'Histogram',
            });
            histogramSeries.setData(histogramData as any);
            seriesRefs.current.set('MACD Histogram', histogramSeries);
          }
          break;

        case 'BB':
          const bb = calculateBollingerBands(closes, indicator.period, 2);
          const upperData: Array<{ time: Time; value: number }> = data.map((d, i) => ({
            time: d.time as Time,
            value: bb.upper[i]
          })).filter(d => !isNaN(d.value));
          
          const lowerData: Array<{ time: Time; value: number }> = data.map((d, i) => ({
            time: d.time as Time,
            value: bb.lower[i]
          })).filter(d => !isNaN(d.value));
          
          if (upperData.length > 0) {
            const upperSeries = chart.addLineSeries({
              color: indicator.color,
              lineWidth: 1,
              title: 'BB Upper',
              lineStyle: 2, // Dashed
            });
            upperSeries.setData(upperData as any);
            seriesRefs.current.set('BB Upper', upperSeries);

            const lowerSeries = chart.addLineSeries({
              color: indicator.color,
              lineWidth: 1,
              title: 'BB Lower',
              lineStyle: 2, // Dashed
            });
            lowerSeries.setData(lowerData as any);
            seriesRefs.current.set('BB Lower', lowerSeries);
          }
          break;
      }
    });

    return () => {
      seriesRefs.current.forEach(series => {
        try {
          chart.removeSeries(series);
        } catch (e) {
          console.warn('Error cleaning up series:', e);
        }
      });
      seriesRefs.current.clear();
    };
  }, [chart, candlestickSeries, data, visibleIndicators, dataHash, indicatorsHash]);

  return null; // This component doesn't render anything
};

export default LightweightChartIndicators;
