/**
 * Advanced Chart Analysis Component
 * Provides professional-grade chart analysis features:
 * - Technical Indicators Overlay (RSI, MACD, Bollinger Bands on chart)
 * - Volume Profile
 * - Advanced Pattern Detection Overlay
 * - Multi-Timeframe Comparison
 * - Price Action Analysis
 * - Smart Money Concepts Visualization
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { IChartApi, ISeriesApi, LineData, HistogramData, Time } from 'lightweight-charts';
import { deduplicateAndSortLineData, deduplicateAndSortHistogramData } from '../utils/chartDataUtils';
import {
  ChartBarIcon,
  AdjustmentsHorizontalIcon,
  ArrowsPointingOutIcon,
  ViewfinderCircleIcon,
  SparklesIcon,
  CpuChipIcon,
  Bars3Icon
} from '@heroicons/react/24/outline';

interface AdvancedChartAnalysisProps {
  chartApi: IChartApi | null;
  candlestickSeries: ISeriesApi<'Candlestick'> | null;
  candles: Array<{
    time: Time;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  symbol: string;
  timeframe: string;
}

interface IndicatorSettings {
  rsi: { enabled: boolean; period: number; overbought: number; oversold: number };
  macd: { enabled: boolean; fast: number; slow: number; signal: number };
  bollinger: { enabled: boolean; period: number; stdDev: number };
  stochastic: { enabled: boolean; period: number; kPeriod: number; dPeriod: number };
  volumeProfile: { enabled: boolean; bins: number };
}

const AdvancedChartAnalysis: React.FC<AdvancedChartAnalysisProps> = ({
  chartApi,
  candlestickSeries,
  candles,
  symbol,
  timeframe
}) => {
  const [showPanel, setShowPanel] = useState(true);
  const [activeTab, setActiveTab] = useState<'indicators' | 'patterns' | 'volume' | 'multi'>('indicators');
  
  // Helper to check if chart is valid
  const isChartValid = (): boolean => {
    return !!(chartApi && candlestickSeries);
  };
  
  // Indicator settings
  const [indicatorSettings, setIndicatorSettings] = useState<IndicatorSettings>({
    rsi: { enabled: true, period: 14, overbought: 70, oversold: 30 },
    macd: { enabled: false, fast: 12, slow: 26, signal: 9 },
    bollinger: { enabled: false, period: 20, stdDev: 2 },
    stochastic: { enabled: false, period: 14, kPeriod: 3, dPeriod: 3 },
    volumeProfile: { enabled: false, bins: 50 }
  });

  // Indicator series refs
  const rsiSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdSignalSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdHistogramRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const bbUpperRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbMiddleRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbLowerRef = useRef<ISeriesApi<'Line'> | null>(null);
  const stochKRef = useRef<ISeriesApi<'Line'> | null>(null);
  const stochDRef = useRef<ISeriesApi<'Line'> | null>(null);

  // Calculate RSI
  const calculateRSI = (data: number[], period: number): number[] => {
    const rsi: number[] = [];
    const gains: number[] = [];
    const losses: number[] = [];

    for (let i = 1; i < data.length; i++) {
      const change = data[i] - data[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? -change : 0);
    }

    let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

    for (let i = period; i < data.length; i++) {
      if (avgLoss === 0) {
        rsi.push(100);
      } else {
        const rs = avgGain / avgLoss;
        rsi.push(100 - (100 / (1 + rs)));
      }

      if (i < data.length - 1) {
        avgGain = (avgGain * (period - 1) + gains[i]) / period;
        avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
      }
    }

    return rsi;
  };

  // Calculate MACD
  const calculateMACD = (data: number[], fast: number, slow: number, signal: number) => {
    const emaFast = calculateEMA(data, fast);
    const emaSlow = calculateEMA(data, slow);
    const macdLine = emaFast.map((val, i) => val - emaSlow[i]);
    const signalLine = calculateEMA(macdLine, signal);
    const histogram = macdLine.map((val, i) => val - signalLine[i]);

    return { macdLine, signalLine, histogram };
  };

  // Calculate EMA
  const calculateEMA = (data: number[], period: number): number[] => {
    const multiplier = 2 / (period + 1);
    const ema: number[] = [];
    let sum = 0;

    for (let i = 0; i < period; i++) {
      sum += data[i];
      ema.push(sum / (i + 1));
    }

    for (let i = period; i < data.length; i++) {
      ema.push((data[i] - ema[i - 1]) * multiplier + ema[i - 1]);
    }

    return ema;
  };

  // Calculate Bollinger Bands
  const calculateBollingerBands = (data: number[], period: number, stdDev: number) => {
    const sma = calculateSMA(data, period);
    const upper: number[] = [];
    const lower: number[] = [];

    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const mean = sma[i];
      const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period;
      const std = Math.sqrt(variance);

      upper.push(mean + stdDev * std);
      lower.push(mean - stdDev * std);
    }

    return { middle: sma, upper, lower };
  };

  // Calculate SMA
  const calculateSMA = (data: number[], period: number): number[] => {
    const sma: number[] = [];
    for (let i = period - 1; i < data.length; i++) {
      const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      sma.push(sum / period);
    }
    return sma;
  };

  // Calculate Stochastic
  const calculateStochastic = (highs: number[], lows: number[], closes: number[], period: number, kPeriod: number, dPeriod: number) => {
    const kValues: number[] = [];
    const dValues: number[] = [];

    for (let i = period - 1; i < closes.length; i++) {
      const highSlice = highs.slice(i - period + 1, i + 1);
      const lowSlice = lows.slice(i - period + 1, i + 1);
      const highestHigh = Math.max(...highSlice);
      const lowestLow = Math.min(...lowSlice);

      if (highestHigh === lowestLow) {
        kValues.push(50);
      } else {
        kValues.push(((closes[i] - lowestLow) / (highestHigh - lowestLow)) * 100);
      }
    }

    // Calculate %K smoothed
    const kSmoothed: number[] = [];
    for (let i = kPeriod - 1; i < kValues.length; i++) {
      const sum = kValues.slice(i - kPeriod + 1, i + 1).reduce((a, b) => a + b, 0);
      kSmoothed.push(sum / kPeriod);
    }

    // Calculate %D (SMA of %K)
    for (let i = dPeriod - 1; i < kSmoothed.length; i++) {
      const sum = kSmoothed.slice(i - dPeriod + 1, i + 1).reduce((a, b) => a + b, 0);
      dValues.push(sum / dPeriod);
    }

    return { k: kSmoothed, d: dValues };
  };

  // Calculate Volume Profile
  const calculateVolumeProfile = () => {
    if (!candles.length) return null;

    const prices = candles.flatMap(c => [c.high, c.low, c.close]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice;
    const binSize = priceRange / indicatorSettings.volumeProfile.bins;

    const bins: Record<number, number> = {};
    for (let i = 0; i < indicatorSettings.volumeProfile.bins; i++) {
      bins[i] = 0;
    }

    candles.forEach(candle => {
      const priceLevel = Math.floor((candle.close - minPrice) / binSize);
      const binIndex = Math.min(Math.max(priceLevel, 0), indicatorSettings.volumeProfile.bins - 1);
      bins[binIndex] += candle.volume;
    });

    return { bins, minPrice, maxPrice, binSize };
  };

  // Memoized indicator calculations
  const indicators = useMemo(() => {
    if (!candles.length) return null;

    const closes = candles.map(c => c.close);
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    const times = candles.map(c => c.time);

    const rsi = indicatorSettings.rsi.enabled
      ? calculateRSI(closes, indicatorSettings.rsi.period)
      : null;

    const macd = indicatorSettings.macd.enabled
      ? calculateMACD(closes, indicatorSettings.macd.fast, indicatorSettings.macd.slow, indicatorSettings.macd.signal)
      : null;

    const bollinger = indicatorSettings.bollinger.enabled
      ? calculateBollingerBands(closes, indicatorSettings.bollinger.period, indicatorSettings.bollinger.stdDev)
      : null;

    const stochastic = indicatorSettings.stochastic.enabled
      ? calculateStochastic(highs, lows, closes, indicatorSettings.stochastic.period, indicatorSettings.stochastic.kPeriod, indicatorSettings.stochastic.dPeriod)
      : null;

    return {
      rsi,
      macd,
      bollinger,
      stochastic,
      times: times.slice(Math.max(...[
        indicatorSettings.rsi.enabled ? indicatorSettings.rsi.period : 0,
        indicatorSettings.macd.enabled ? indicatorSettings.macd.slow : 0,
        indicatorSettings.bollinger.enabled ? indicatorSettings.bollinger.period : 0,
        indicatorSettings.stochastic.enabled ? indicatorSettings.stochastic.period : 0
      ]))
    };
  }, [candles, indicatorSettings]);

  // Initialize indicator series
  useEffect(() => {
    if (!chartApi || !indicators || !isChartValid()) return;

    // RSI Series (on separate price scale)
    if (indicatorSettings.rsi.enabled && indicators.rsi && !rsiSeriesRef.current) {
      try {
        rsiSeriesRef.current = chartApi.addLineSeries({
          color: '#8B5CF6',
          lineWidth: 2,
          title: 'RSI',
          priceScaleId: 'rsi',
          priceFormat: {
            type: 'price',
            precision: 2,
            minMove: 0.01
          }
        });

      try {
        chartApi.priceScale('rsi').applyOptions({
          scaleMargins: {
            top: 0.8,
            bottom: 0.1
          }
        });
      } catch (error) {
        console.debug('Error applying RSI price scale options:', error);
      }
      } catch (error) {
        console.debug('Error creating RSI series:', error);
      }
    }

    // MACD Series
    if (indicatorSettings.macd.enabled && indicators.macd && !macdSeriesRef.current) {
      macdSeriesRef.current = chartApi.addLineSeries({
        color: '#3B82F6',
        lineWidth: 2,
        title: 'MACD',
        priceScaleId: 'macd'
      });

      macdSignalSeriesRef.current = chartApi.addLineSeries({
        color: '#EF4444',
        lineWidth: 1,
        title: 'Signal',
        priceScaleId: 'macd'
      });

      macdHistogramRef.current = chartApi.addHistogramSeries({
        color: '#10B981',
        priceScaleId: 'macd'
      });

      try {
        chartApi.priceScale('macd').applyOptions({
          scaleMargins: {
            top: 0.7,
            bottom: 0.1
          }
        });
      } catch (error) {
        console.debug('Error applying MACD price scale options:', error);
      }
    }

    // Bollinger Bands
    if (indicatorSettings.bollinger.enabled && indicators.bollinger && !bbUpperRef.current) {
      bbUpperRef.current = chartApi.addLineSeries({
        color: '#10B981',
        lineWidth: 1,
        title: 'BB Upper',
        lineStyle: 2
      });

      bbMiddleRef.current = chartApi.addLineSeries({
        color: '#6B7280',
        lineWidth: 1,
        title: 'BB Middle',
        lineStyle: 2
      });

      bbLowerRef.current = chartApi.addLineSeries({
        color: '#EF4444',
        lineWidth: 1,
        title: 'BB Lower',
        lineStyle: 2
      });
    }

    // Stochastic
    if (indicatorSettings.stochastic.enabled && indicators.stochastic && !stochKRef.current) {
      stochKRef.current = chartApi.addLineSeries({
        color: '#F59E0B',
        lineWidth: 2,
        title: '%K',
        priceScaleId: 'stoch',
        priceFormat: {
          type: 'price',
          precision: 2,
          minMove: 0.01
        }
      });

      stochDRef.current = chartApi.addLineSeries({
        color: '#8B5CF6',
        lineWidth: 1,
        title: '%D',
        priceScaleId: 'stoch'
      });

      try {
        chartApi.priceScale('stoch').applyOptions({
          scaleMargins: {
            top: 0.8,
            bottom: 0.1
          }
        });
      } catch (error) {
        console.debug('Error applying Stochastic price scale options:', error);
      }
    }

    return () => {
      // Cleanup will be handled by chart removal
    };
  }, [chartApi, indicators, indicatorSettings]);

  // Update indicator data
  useEffect(() => {
    if (!indicators || !candles.length) return;

    const startIndex = Math.max(...[
      indicatorSettings.rsi.enabled ? indicatorSettings.rsi.period : 0,
      indicatorSettings.macd.enabled ? indicatorSettings.macd.slow : 0,
      indicatorSettings.bollinger.enabled ? indicatorSettings.bollinger.period : 0,
      indicatorSettings.stochastic.enabled ? indicatorSettings.stochastic.period : 0
    ]);

    // Update RSI
    if (indicatorSettings.rsi.enabled && indicators.rsi && rsiSeriesRef.current && isChartValid()) {
      let rsiData: LineData[] = indicators.rsi.map((value, i) => ({
        time: indicators.times[i] as Time,
        value: value
      }));
      rsiData = deduplicateAndSortLineData(rsiData, false);
      
      try {
        rsiSeriesRef.current.setData(rsiData);

        // Add overbought/oversold lines
        try {
          rsiSeriesRef.current.createPriceLine({
            price: indicatorSettings.rsi.overbought,
            color: '#EF4444',
            lineWidth: 1,
            lineStyle: 2,
            axisLabelVisible: true,
            title: 'Overbought'
          });

          rsiSeriesRef.current.createPriceLine({
            price: indicatorSettings.rsi.oversold,
            color: '#10B981',
            lineWidth: 1,
            lineStyle: 2,
            axisLabelVisible: true,
            title: 'Oversold'
          });
        } catch (error) {
          console.debug('Error creating RSI price lines:', error);
        }
      } catch (error) {
        console.debug('Error setting RSI data:', error);
      }
    }

    // Update MACD
    if (indicatorSettings.macd.enabled && indicators.macd && macdSeriesRef.current && isChartValid()) {
      let macdData: LineData[] = indicators.macd.macdLine.map((value, i) => ({
        time: indicators.times[i] as Time,
        value: value
      }));
      macdData = deduplicateAndSortLineData(macdData, false);
      if (macdSeriesRef.current && isChartValid()) {
        try {
          macdSeriesRef.current.setData(macdData);
        } catch (error) {
          console.debug('Error setting MACD data:', error);
        }
      }

      if (macdSignalSeriesRef.current && isChartValid()) {
        let signalData: LineData[] = indicators.macd.signalLine.map((value, i) => ({
          time: indicators.times[i] as Time,
          value: value
        }));
        signalData = deduplicateAndSortLineData(signalData, false);
        try {
          macdSignalSeriesRef.current.setData(signalData);
        } catch (error) {
          console.debug('Error setting MACD signal data:', error);
        }
      }

      if (macdHistogramRef.current && isChartValid()) {
        let histogramData: HistogramData[] = indicators.macd.histogram.map((value, i) => ({
          time: indicators.times[i] as Time,
          value: value,
          color: value >= 0 ? '#10B98180' : '#EF444480'
        }));
        histogramData = deduplicateAndSortHistogramData(histogramData, false);
        try {
          macdHistogramRef.current.setData(histogramData);
        } catch (error) {
          console.debug('Error setting MACD histogram data:', error);
        }
      }
    }

    // Update Bollinger Bands
    if (indicatorSettings.bollinger.enabled && indicators.bollinger && bbUpperRef.current && isChartValid()) {
      const bbStartIndex = indicatorSettings.bollinger.period - 1;
      const bbTimes = candles.slice(bbStartIndex).map(c => c.time);

      if (bbUpperRef.current) {
        let upperData: LineData[] = indicators.bollinger.upper.map((value, i) => ({
          time: bbTimes[i] as Time,
          value: value
        }));
        upperData = deduplicateAndSortLineData(upperData, false);
        if (bbUpperRef.current && isChartValid()) {
          try {
            bbUpperRef.current.setData(upperData);
          } catch (error) {
            console.debug('Error setting BB upper data:', error);
          }
        }
      }

      if (bbMiddleRef.current && isChartValid()) {
        let middleData: LineData[] = indicators.bollinger.middle.map((value, i) => ({
          time: bbTimes[i] as Time,
          value: value
        }));
        middleData = deduplicateAndSortLineData(middleData, false);
        try {
          bbMiddleRef.current.setData(middleData);
        } catch (error) {
          console.debug('Error setting BB middle data:', error);
        }
      }

      if (bbLowerRef.current && isChartValid()) {
        let lowerData: LineData[] = indicators.bollinger.lower.map((value, i) => ({
          time: bbTimes[i] as Time,
          value: value
        }));
        lowerData = deduplicateAndSortLineData(lowerData, false);
        try {
          bbLowerRef.current.setData(lowerData);
        } catch (error) {
          console.debug('Error setting BB lower data:', error);
        }
      }
    }

    // Update Stochastic
    if (indicatorSettings.stochastic.enabled && indicators.stochastic && stochKRef.current && isChartValid()) {
      const stochStartIndex = indicatorSettings.stochastic.period + indicatorSettings.stochastic.kPeriod - 1;
      const stochTimes = candles.slice(stochStartIndex).map(c => c.time);

      if (stochKRef.current) {
        let kData: LineData[] = indicators.stochastic.k.map((value, i) => ({
          time: stochTimes[i] as Time,
          value: value
        }));
        kData = deduplicateAndSortLineData(kData, false);
        if (stochKRef.current && isChartValid()) {
          try {
            stochKRef.current.setData(kData);
          } catch (error) {
            console.debug('Error setting Stochastic K data:', error);
          }
        }
      }

      if (stochDRef.current && isChartValid()) {
        const dStartIndex = stochStartIndex + indicatorSettings.stochastic.dPeriod - 1;
        const dTimes = candles.slice(dStartIndex).map(c => c.time);
        let dData: LineData[] = indicators.stochastic.d.map((value, i) => ({
          time: dTimes[i] as Time,
          value: value
        }));
        dData = deduplicateAndSortLineData(dData, false);
        try {
          stochDRef.current.setData(dData);
          
          // Add overbought/oversold lines
          try {
            stochDRef.current.createPriceLine({
              price: 80,
              color: '#EF4444',
              lineWidth: 1,
              lineStyle: 2,
              axisLabelVisible: true,
              title: 'Overbought'
            });

            stochDRef.current.createPriceLine({
              price: 20,
              color: '#10B981',
              lineWidth: 1,
              lineStyle: 2,
              axisLabelVisible: true,
              title: 'Oversold'
            });
          } catch (error) {
            console.debug('Error creating Stochastic price lines:', error);
          }
        } catch (error) {
          console.debug('Error setting Stochastic D data:', error);
        }
      }
    }
  }, [indicators, candles, indicatorSettings]);

  const volumeProfile = useMemo(() => {
    if (!indicatorSettings.volumeProfile.enabled) return null;
    return calculateVolumeProfile();
  }, [candles, indicatorSettings.volumeProfile]);

  if (!showPanel) {
    return (
      <button
        onClick={() => setShowPanel(true)}
        className="fixed bottom-4 right-4 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-full shadow-lg z-50"
        title="Show Advanced Analysis"
      >
        <SparklesIcon className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl z-50 max-h-[80vh] overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-[#2a2e39] flex items-center justify-between bg-[#131722]">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <SparklesIcon className="w-5 h-5 text-blue-400" />
          Advanced Analysis
        </h3>
        <button
          onClick={() => setShowPanel(false)}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#2a2e39] bg-[#131722]">
        {[
          { id: 'indicators', label: 'Indicators', icon: ChartBarIcon },
          { id: 'patterns', label: 'Patterns', icon: ViewfinderCircleIcon },
          { id: 'volume', label: 'Volume', icon: Bars3Icon },
          { id: 'multi', label: 'Multi-TF', icon: ArrowsPointingOutIcon }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-blue-400 border-b-2 border-blue-400 bg-[#1e222d]'
                : 'text-gray-400 hover:text-white hover:bg-[#1e222d]'
            }`}
          >
            <tab.icon className="w-4 h-4 mx-auto mb-1" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'indicators' && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white mb-3">Technical Indicators</h4>
            
            {/* RSI */}
            <div className="bg-[#131722] p-3 rounded border border-[#2a2e39]">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-300 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={indicatorSettings.rsi.enabled}
                    onChange={(e) => setIndicatorSettings(prev => ({
                      ...prev,
                      rsi: { ...prev.rsi, enabled: e.target.checked }
                    }))}
                    className="w-4 h-4"
                  />
                  RSI (Relative Strength Index)
                </label>
              </div>
              {indicatorSettings.rsi.enabled && (
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <div>
                    <label className="text-xs text-gray-400">Period</label>
                    <input
                      type="number"
                      value={indicatorSettings.rsi.period}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        rsi: { ...prev.rsi, period: parseInt(e.target.value) || 14 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Overbought</label>
                    <input
                      type="number"
                      value={indicatorSettings.rsi.overbought}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        rsi: { ...prev.rsi, overbought: parseInt(e.target.value) || 70 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Oversold</label>
                    <input
                      type="number"
                      value={indicatorSettings.rsi.oversold}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        rsi: { ...prev.rsi, oversold: parseInt(e.target.value) || 30 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* MACD */}
            <div className="bg-[#131722] p-3 rounded border border-[#2a2e39]">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-300 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={indicatorSettings.macd.enabled}
                    onChange={(e) => setIndicatorSettings(prev => ({
                      ...prev,
                      macd: { ...prev.macd, enabled: e.target.checked }
                    }))}
                    className="w-4 h-4"
                  />
                  MACD
                </label>
              </div>
              {indicatorSettings.macd.enabled && (
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <div>
                    <label className="text-xs text-gray-400">Fast</label>
                    <input
                      type="number"
                      value={indicatorSettings.macd.fast}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        macd: { ...prev.macd, fast: parseInt(e.target.value) || 12 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Slow</label>
                    <input
                      type="number"
                      value={indicatorSettings.macd.slow}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        macd: { ...prev.macd, slow: parseInt(e.target.value) || 26 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Signal</label>
                    <input
                      type="number"
                      value={indicatorSettings.macd.signal}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        macd: { ...prev.macd, signal: parseInt(e.target.value) || 9 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Bollinger Bands */}
            <div className="bg-[#131722] p-3 rounded border border-[#2a2e39]">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-300 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={indicatorSettings.bollinger.enabled}
                    onChange={(e) => setIndicatorSettings(prev => ({
                      ...prev,
                      bollinger: { ...prev.bollinger, enabled: e.target.checked }
                    }))}
                    className="w-4 h-4"
                  />
                  Bollinger Bands
                </label>
              </div>
              {indicatorSettings.bollinger.enabled && (
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <div>
                    <label className="text-xs text-gray-400">Period</label>
                    <input
                      type="number"
                      value={indicatorSettings.bollinger.period}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        bollinger: { ...prev.bollinger, period: parseInt(e.target.value) || 20 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Std Dev</label>
                    <input
                      type="number"
                      step="0.1"
                      value={indicatorSettings.bollinger.stdDev}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        bollinger: { ...prev.bollinger, stdDev: parseFloat(e.target.value) || 2 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Stochastic */}
            <div className="bg-[#131722] p-3 rounded border border-[#2a2e39]">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-300 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={indicatorSettings.stochastic.enabled}
                    onChange={(e) => setIndicatorSettings(prev => ({
                      ...prev,
                      stochastic: { ...prev.stochastic, enabled: e.target.checked }
                    }))}
                    className="w-4 h-4"
                  />
                  Stochastic
                </label>
              </div>
              {indicatorSettings.stochastic.enabled && (
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <div>
                    <label className="text-xs text-gray-400">Period</label>
                    <input
                      type="number"
                      value={indicatorSettings.stochastic.period}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        stochastic: { ...prev.stochastic, period: parseInt(e.target.value) || 14 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">%K</label>
                    <input
                      type="number"
                      value={indicatorSettings.stochastic.kPeriod}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        stochastic: { ...prev.stochastic, kPeriod: parseInt(e.target.value) || 3 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">%D</label>
                    <input
                      type="number"
                      value={indicatorSettings.stochastic.dPeriod}
                      onChange={(e) => setIndicatorSettings(prev => ({
                        ...prev,
                        stochastic: { ...prev.stochastic, dPeriod: parseInt(e.target.value) || 3 }
                      }))}
                      className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'volume' && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white mb-3">Volume Analysis</h4>
            
            <div className="bg-[#131722] p-3 rounded border border-[#2a2e39]">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-300 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={indicatorSettings.volumeProfile.enabled}
                    onChange={(e) => setIndicatorSettings(prev => ({
                      ...prev,
                      volumeProfile: { ...prev.volumeProfile, enabled: e.target.checked }
                    }))}
                    className="w-4 h-4"
                  />
                  Volume Profile
                </label>
              </div>
              {indicatorSettings.volumeProfile.enabled && (
                <div className="mt-2">
                  <label className="text-xs text-gray-400">Bins</label>
                  <input
                    type="number"
                    value={indicatorSettings.volumeProfile.bins}
                    onChange={(e) => setIndicatorSettings(prev => ({
                      ...prev,
                      volumeProfile: { ...prev.volumeProfile, bins: parseInt(e.target.value) || 50 }
                    }))}
                    className="w-full px-2 py-1 bg-[#1e222d] border border-[#2a2e39] rounded text-sm text-white mt-1"
                  />
                  {volumeProfile && (
                    <div className="mt-3 text-xs text-gray-400">
                      <p>Price Range: ₹{volumeProfile.minPrice.toFixed(2)} - ₹{volumeProfile.maxPrice.toFixed(2)}</p>
                      <p>Bin Size: ₹{volumeProfile.binSize.toFixed(2)}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'patterns' && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white mb-3">Pattern Detection</h4>
            <div className="bg-[#131722] p-4 rounded border border-[#2a2e39] text-center text-gray-400 text-sm">
              Pattern detection overlay coming soon...
            </div>
          </div>
        )}

        {activeTab === 'multi' && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white mb-3">Multi-Timeframe</h4>
            <div className="bg-[#131722] p-4 rounded border border-[#2a2e39] text-center text-gray-400 text-sm">
              Multi-timeframe comparison coming soon...
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedChartAnalysis;

