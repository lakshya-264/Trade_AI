import React, { useState, useEffect, useCallback } from 'react';
import { 
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  BellIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';

import { CandlestickData, PatternSignal } from '../types/api';

interface CandlestickPatternRecognitionProps {
  data: CandlestickData[];
  symbol: string;
  className?: string;
  onPatternDetected?: (patterns: PatternSignal[]) => void;
  showAlerts?: boolean;
}

interface PatternDefinition {
  name: string;
  description: string;
  bullishPattern: (candles: CandlestickData[], index: number) => boolean;
  bearishPattern: (candles: CandlestickData[], index: number) => boolean;
  confidence: (candles: CandlestickData[], index: number) => number;
  action: 'BUY' | 'SELL' | 'HOLD';
  timeframe: string;
}

const CandlestickPatternRecognition: React.FC<CandlestickPatternRecognitionProps> = ({
  data,
  symbol,
  className = '',
  onPatternDetected,
  showAlerts = true
}) => {
  const [patterns, setPatterns] = useState<PatternSignal[]>([]);
  const [showPatterns, setShowPatterns] = useState(true);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1m');

  // Pattern Definitions
  const patternDefinitions: PatternDefinition[] = [
    {
      name: 'Hammer',
      description: 'Reversal pattern with small body and long lower shadow',
      bullishPattern: (candles, index) => {
        if (index < 1) return false;
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const lowerShadow = Math.min(candle.open, candle.close) - candle.low;
        const upperShadow = candle.high - Math.max(candle.open, candle.close);
        const totalRange = candle.high - candle.low;
        
        return (
          lowerShadow >= 2 * body &&
          upperShadow <= body * 0.1 &&
          body <= totalRange * 0.3 &&
          candle.close > candle.open
        );
      },
      bearishPattern: (candles, index) => {
        if (index < 1) return false;
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const lowerShadow = Math.min(candle.open, candle.close) - candle.low;
        const upperShadow = candle.high - Math.max(candle.open, candle.close);
        const totalRange = candle.high - candle.low;
        
        return (
          lowerShadow >= 2 * body &&
          upperShadow <= body * 0.1 &&
          body <= totalRange * 0.3 &&
          candle.close < candle.open
        );
      },
      confidence: (candles, index) => {
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const lowerShadow = Math.min(candle.open, candle.close) - candle.low;
        const totalRange = candle.high - candle.low;
        return Math.min(100, (lowerShadow / body) * 20 + (body / totalRange) * 30);
      },
      action: 'BUY',
      timeframe: '1m'
    },
    {
      name: 'Evening Star',
      description: 'Three-candle bearish reversal pattern',
      bullishPattern: () => false,
      bearishPattern: (candles, index) => {
        if (index < 2) return false;
        const first = candles[index - 2];
        const second = candles[index - 1];
        const third = candles[index];
        const firstBody = Math.abs(first.close - first.open);
        const secondBody = Math.abs(second.close - second.open);
        return (
          first.close > first.open &&
          secondBody < firstBody * 0.5 &&
          third.close < third.open &&
          third.close < (first.open + first.close) / 2
        );
      },
      confidence: (candles, index) => {
        const first = candles[index - 2];
        const second = candles[index - 1];
        const secondBody = Math.abs(second.close - second.open);
        const firstBody = Math.abs(first.close - first.open);
        return Math.min(100, (1 - secondBody / (firstBody || 1)) * 60);
      },
      action: 'SELL',
      timeframe: '15m'
    },
    {
      name: 'Piercing Pattern',
      description: 'Bullish two-candle reversal where green closes above midpoint of prior red',
      bullishPattern: (candles, index) => {
        if (index < 1) return false;
        const prev = candles[index - 1];
        const cur = candles[index];
        const prevBodyMid = (prev.open + prev.close) / 2;
        return (
          prev.close < prev.open &&
          cur.open < prev.low &&
          cur.close > prevBodyMid &&
          cur.close > cur.open
        );
      },
      bearishPattern: () => false,
      confidence: (candles, index) => {
        const prev = candles[index - 1];
        const cur = candles[index];
        const bodySize = Math.abs(cur.close - cur.open);
        const prevBody = Math.abs(prev.close - prev.open) || 1;
        return Math.min(100, (bodySize / prevBody) * 50 + 30);
      },
      action: 'BUY',
      timeframe: '5m'
    },
    {
      name: 'Dark Cloud Cover',
      description: 'Bearish two-candle reversal where red closes below midpoint of prior green',
      bullishPattern: () => false,
      bearishPattern: (candles, index) => {
        if (index < 1) return false;
        const prev = candles[index - 1];
        const cur = candles[index];
        const prevBodyMid = (prev.open + prev.close) / 2;
        return (
          prev.close > prev.open &&
          cur.open > prev.high &&
          cur.close < prevBodyMid &&
          cur.close < cur.open
        );
      },
      confidence: (candles, index) => {
        const prev = candles[index - 1];
        const cur = candles[index];
        const bodySize = Math.abs(cur.close - cur.open);
        const prevBody = Math.abs(prev.close - prev.open) || 1;
        return Math.min(100, (bodySize / prevBody) * 50 + 30);
      },
      action: 'SELL',
      timeframe: '5m'
    },
    {
      name: 'Harami',
      description: 'Small candle contained within the prior larger candle body',
      bullishPattern: (candles, index) => {
        if (index < 1) return false;
        const prev = candles[index - 1];
        const cur = candles[index];
        const prevLowBody = Math.min(prev.open, prev.close);
        const prevHighBody = Math.max(prev.open, prev.close);
        const curLowBody = Math.min(cur.open, cur.close);
        const curHighBody = Math.max(cur.open, cur.close);
        return (
          prev.close < prev.open &&
          curHighBody <= prevHighBody &&
          curLowBody >= prevLowBody &&
          cur.close > cur.open
        );
      },
      bearishPattern: (candles, index) => {
        if (index < 1) return false;
        const prev = candles[index - 1];
        const cur = candles[index];
        const prevLowBody = Math.min(prev.open, prev.close);
        const prevHighBody = Math.max(prev.open, prev.close);
        const curLowBody = Math.min(cur.open, cur.close);
        const curHighBody = Math.max(cur.open, cur.close);
        return (
          prev.close > prev.open &&
          curHighBody <= prevHighBody &&
          curLowBody >= prevLowBody &&
          cur.close < cur.open
        );
      },
      confidence: (candles, index) => {
        const prev = candles[index - 1];
        const cur = candles[index];
        const ratio = (Math.abs(cur.close - cur.open)) / (Math.abs(prev.close - prev.open) || 1);
        return Math.min(100, (1 - Math.min(1, ratio)) * 60 + 20);
      },
      action: 'HOLD',
      timeframe: '5m'
    },
    {
      name: 'Long-Legged Doji',
      description: 'Indecision with very small body and very long upper and lower shadows',
      bullishPattern: (candles, index) => {
        if (index < 1) return false;
        const c = candles[index];
        const prev = candles[index - 1];
        const body = Math.abs(c.close - c.open);
        const range = c.high - c.low;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        if (range <= 0) return false;
        const isLongLegged = body <= range * 0.08 && upper >= range * 0.4 && lower >= range * 0.4;
        return isLongLegged && c.close >= prev.close; // classify bullish if closing above prev
      },
      bearishPattern: (candles, index) => {
        if (index < 1) return false;
        const c = candles[index];
        const prev = candles[index - 1];
        const body = Math.abs(c.close - c.open);
        const range = c.high - c.low;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        if (range <= 0) return false;
        const isLongLegged = body <= range * 0.08 && upper >= range * 0.4 && lower >= range * 0.4;
        return isLongLegged && c.close < prev.close; // classify bearish if closing below prev
      },
      confidence: (candles, index) => {
        const c = candles[index];
        const body = Math.abs(c.close - c.open);
        const range = c.high - c.low;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        if (range <= 0) return 0;
        const symmetry = 1 - Math.min(1, Math.abs(upper - lower) / range);
        return Math.min(100, (1 - body / range) * 50 + symmetry * 30 + ((upper + lower) / range) * 20);
      },
      action: 'HOLD',
      timeframe: '1m'
    },
    {
      name: 'Spinning Top',
      description: 'Small real body centered with upper and lower shadows of similar length',
      bullishPattern: (candles, index) => {
        const c = candles[index];
        if (!c) return false;
        const body = Math.abs(c.close - c.open);
        const range = c.high - c.low;
        if (range <= 0) return false;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        const smallBody = body <= range * 0.25 && body > range * 0.05; // not a doji, but small
        const decentShadows = upper >= range * 0.2 && lower >= range * 0.2;
        const balanced = Math.abs(upper - lower) <= range * 0.15;
        return smallBody && decentShadows && balanced && c.close >= c.open;
      },
      bearishPattern: (candles, index) => {
        const c = candles[index];
        if (!c) return false;
        const body = Math.abs(c.close - c.open);
        const range = c.high - c.low;
        if (range <= 0) return false;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        const smallBody = body <= range * 0.25 && body > range * 0.05;
        const decentShadows = upper >= range * 0.2 && lower >= range * 0.2;
        const balanced = Math.abs(upper - lower) <= range * 0.15;
        return smallBody && decentShadows && balanced && c.close < c.open;
      },
      confidence: (candles, index) => {
        const c = candles[index];
        const body = Math.abs(c.close - c.open);
        const range = c.high - c.low;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        if (range <= 0) return 0;
        const balance = 1 - Math.min(1, Math.abs(upper - lower) / range);
        return Math.min(100, (1 - body / range) * 40 + balance * 40 + ((upper + lower) / range) * 20);
      },
      action: 'HOLD',
      timeframe: '1m'
    },
    {
      name: 'Rickshaw Man',
      description: 'A long-legged doji with open/close near the midpoint of the range',
      bullishPattern: (candles, index) => {
        if (index < 1) return false;
        const c = candles[index];
        const prev = candles[index - 1];
        const range = c.high - c.low;
        if (range <= 0) return false;
        const body = Math.abs(c.close - c.open);
        const mid = c.low + range / 2;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        const longLegs = upper >= range * 0.4 && lower >= range * 0.4;
        const nearMid = Math.abs(((c.open + c.close) / 2) - mid) <= range * 0.1;
        const tinyBody = body <= range * 0.08;
        return longLegs && nearMid && tinyBody && c.close >= prev.close;
      },
      bearishPattern: (candles, index) => {
        if (index < 1) return false;
        const c = candles[index];
        const prev = candles[index - 1];
        const range = c.high - c.low;
        if (range <= 0) return false;
        const body = Math.abs(c.close - c.open);
        const mid = c.low + range / 2;
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        const longLegs = upper >= range * 0.4 && lower >= range * 0.4;
        const nearMid = Math.abs(((c.open + c.close) / 2) - mid) <= range * 0.1;
        const tinyBody = body <= range * 0.08;
        return longLegs && nearMid && tinyBody && c.close < prev.close;
      },
      confidence: (candles, index) => {
        const c = candles[index];
        const range = c.high - c.low;
        if (range <= 0) return 0;
        const body = Math.abs(c.close - c.open);
        const upper = c.high - Math.max(c.open, c.close);
        const lower = Math.min(c.open, c.close) - c.low;
        const symmetry = 1 - Math.min(1, Math.abs(upper - lower) / range);
        const midpointProximity = 1 - Math.min(1, Math.abs(((c.open + c.close) / 2) - (c.low + range / 2)) / (range / 2));
        return Math.min(100, (1 - body / range) * 40 + symmetry * 30 + midpointProximity * 30);
      },
      action: 'HOLD',
      timeframe: '1m'
    },
    {
      name: 'Doji',
      description: 'Indecision pattern with very small body',
      bullishPattern: (candles, index) => {
        if (index < 1) return false;
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const totalRange = candle.high - candle.low;
        const prevCandle = candles[index - 1];
        
        return (
          body <= totalRange * 0.1 &&
          candle.close > prevCandle.close &&
          totalRange > 0
        );
      },
      bearishPattern: (candles, index) => {
        if (index < 1) return false;
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const totalRange = candle.high - candle.low;
        const prevCandle = candles[index - 1];
        
        return (
          body <= totalRange * 0.1 &&
          candle.close < prevCandle.close &&
          totalRange > 0
        );
      },
      confidence: (candles, index) => {
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const totalRange = candle.high - candle.low;
        return Math.min(100, (1 - body / totalRange) * 50);
      },
      action: 'HOLD',
      timeframe: '1m'
    },
    {
      name: 'Engulfing',
      description: 'Strong reversal pattern where one candle engulfs the previous',
      bullishPattern: (candles, index) => {
        if (index < 1) return false;
        const current = candles[index];
        const previous = candles[index - 1];
        
        return (
          previous.close < previous.open && // Previous was bearish
          current.close > current.open && // Current is bullish
          current.open < previous.close && // Current opens below previous close
          current.close > previous.open // Current closes above previous open
        );
      },
      bearishPattern: (candles, index) => {
        if (index < 1) return false;
        const current = candles[index];
        const previous = candles[index - 1];
        
        return (
          previous.close > previous.open && // Previous was bullish
          current.close < current.open && // Current is bearish
          current.open > previous.close && // Current opens above previous close
          current.close < previous.open // Current closes below previous open
        );
      },
      confidence: (candles, index) => {
        const current = candles[index];
        const previous = candles[index - 1];
        const engulfmentRatio = Math.abs(current.close - current.open) / Math.abs(previous.close - previous.open);
        return Math.min(100, engulfmentRatio * 40);
      },
      action: 'BUY',
      timeframe: '5m'
    },
    {
      name: 'Morning Star',
      description: 'Three-candle bullish reversal pattern',
      bullishPattern: (candles, index) => {
        if (index < 2) return false;
        const first = candles[index - 2];
        const second = candles[index - 1];
        const third = candles[index];
        
        const firstBody = Math.abs(first.close - first.open);
        const secondBody = Math.abs(second.close - second.open);
        const thirdBody = Math.abs(third.close - third.open);
        
        return (
          first.close < first.open && // First candle is bearish
          secondBody < firstBody * 0.5 && // Second candle has small body
          third.close > third.open && // Third candle is bullish
          third.close > (first.open + first.close) / 2 // Third closes above first midpoint
        );
      },
      bearishPattern: (candles, index) => {
        if (index < 2) return false;
        const first = candles[index - 2];
        const second = candles[index - 1];
        const third = candles[index];
        
        const firstBody = Math.abs(first.close - first.open);
        const secondBody = Math.abs(second.close - second.open);
        const thirdBody = Math.abs(third.close - third.open);
        
        return (
          first.close > first.open && // First candle is bullish
          secondBody < firstBody * 0.5 && // Second candle has small body
          third.close < third.open && // Third candle is bearish
          third.close < (first.open + first.close) / 2 // Third closes below first midpoint
        );
      },
      confidence: (candles, index) => {
        const first = candles[index - 2];
        const second = candles[index - 1];
        const third = candles[index];
        const secondBody = Math.abs(second.close - second.open);
        const firstBody = Math.abs(first.close - first.open);
        return Math.min(100, (1 - secondBody / firstBody) * 60);
      },
      action: 'BUY',
      timeframe: '15m'
    },
    {
      name: 'Shooting Star',
      description: 'Bearish reversal pattern with long upper shadow',
      bullishPattern: (candles, index) => {
        if (index < 1) return false;
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const upperShadow = candle.high - Math.max(candle.open, candle.close);
        const lowerShadow = Math.min(candle.open, candle.close) - candle.low;
        const totalRange = candle.high - candle.low;
        
        return (
          upperShadow >= 2 * body &&
          lowerShadow <= body * 0.1 &&
          body <= totalRange * 0.3 &&
          candle.close < candle.open
        );
      },
      bearishPattern: (candles, index) => {
        if (index < 1) return false;
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const upperShadow = candle.high - Math.max(candle.open, candle.close);
        const lowerShadow = Math.min(candle.open, candle.close) - candle.low;
        const totalRange = candle.high - candle.low;
        
        return (
          upperShadow >= 2 * body &&
          lowerShadow <= body * 0.1 &&
          body <= totalRange * 0.3 &&
          candle.close > candle.open
        );
      },
      confidence: (candles, index) => {
        const candle = candles[index];
        const body = Math.abs(candle.close - candle.open);
        const upperShadow = candle.high - Math.max(candle.open, candle.close);
        const totalRange = candle.high - candle.low;
        return Math.min(100, (upperShadow / body) * 20 + (body / totalRange) * 30);
      },
      action: 'SELL',
      timeframe: '1m'
    },
    {
      name: 'Three White Soldiers',
      description: 'Strong bullish continuation pattern',
      bullishPattern: (candles, index) => {
        if (index < 2) return false;
        const first = candles[index - 2];
        const second = candles[index - 1];
        const third = candles[index];
        
        return (
          first.close > first.open &&
          second.close > second.open &&
          third.close > third.open &&
          second.open > first.close &&
          third.open > second.close &&
          second.close > first.close &&
          third.close > second.close
        );
      },
      bearishPattern: () => false, // This is only a bullish pattern
      confidence: (candles, index) => {
        const first = candles[index - 2];
        const second = candles[index - 1];
        const third = candles[index];
        const totalGain = (third.close - first.open) / first.open;
        return Math.min(100, totalGain * 200);
      },
      action: 'BUY',
      timeframe: '5m'
    }
  ];

  // Calculate additional technical indicators for pattern validation
  const calculateTechnicalIndicators = useCallback((candles: CandlestickData[], index: number) => {
    if (index < 20) return { rsi: 50, sma20: 0, volume: 0 };
    
    // RSI calculation
    let gains = 0, losses = 0;
    for (let i = index - 13; i <= index; i++) {
      const change = candles[i].close - candles[i - 1].close;
      if (change > 0) gains += change;
      else losses += Math.abs(change);
    }
    const avgGain = gains / 14;
    const avgLoss = losses / 14;
    const rs = avgGain / (avgLoss || 0.0001);
    const rsi = 100 - (100 / (1 + rs));
    
    // SMA 20
    const sma20 = candles.slice(index - 19, index + 1)
      .reduce((sum, candle) => sum + candle.close, 0) / 20;
    
    // Volume
    const volume = candles[index].volume;
    
    return { rsi, sma20, volume };
  }, []);

  // Detect patterns in the data
  const detectPatterns = useCallback(() => {
    if (!data || data.length < 3) return [];
    
    const detectedPatterns: PatternSignal[] = [];
    
    for (let i = 2; i < data.length; i++) {
      for (const patternDef of patternDefinitions) {
        // Check bullish pattern
        if (patternDef.bullishPattern(data, i)) {
          const confidence = patternDef.confidence(data, i);
          const techIndicators = calculateTechnicalIndicators(data, i);
          const candle = data[i];
          
          // Additional validation based on technical indicators
          let adjustedConfidence = confidence;
          if (techIndicators.rsi > 70) adjustedConfidence *= 0.8; // Overbought
          if (techIndicators.rsi < 30) adjustedConfidence *= 1.2; // Oversold
          if (candle.close > techIndicators.sma20) adjustedConfidence *= 1.1; // Above SMA
          
          const strength = adjustedConfidence > 80 ? 'very_strong' : 
                          adjustedConfidence > 60 ? 'strong' : 
                          adjustedConfidence > 40 ? 'moderate' : 'weak';
          
          const target = candle.close * (1 + (adjustedConfidence / 1000));
          const stopLoss = candle.low * 0.98;
          const riskReward = (target - candle.close) / (candle.close - stopLoss);
          
          detectedPatterns.push({
            pattern: patternDef.name,
            type: 'bullish',
            confidence: Math.round(adjustedConfidence),
            description: patternDef.description,
            action: 'BUY',
            strength,
            timeframe: patternDef.timeframe,
            price: candle.close,
            target,
            stopLoss,
            riskReward: Math.round(riskReward * 100) / 100
          });
        }
        
        // Check bearish pattern
        if (patternDef.bearishPattern(data, i)) {
          const confidence = patternDef.confidence(data, i);
          const techIndicators = calculateTechnicalIndicators(data, i);
          const candle = data[i];
          
          // Additional validation based on technical indicators
          let adjustedConfidence = confidence;
          if (techIndicators.rsi < 30) adjustedConfidence *= 0.8; // Oversold
          if (techIndicators.rsi > 70) adjustedConfidence *= 1.2; // Overbought
          if (candle.close < techIndicators.sma20) adjustedConfidence *= 1.1; // Below SMA
          
          const strength = adjustedConfidence > 80 ? 'very_strong' : 
                          adjustedConfidence > 60 ? 'strong' : 
                          adjustedConfidence > 40 ? 'moderate' : 'weak';
          
          const target = candle.close * (1 - (adjustedConfidence / 1000));
          const stopLoss = candle.high * 1.02;
          const riskReward = (candle.close - target) / (stopLoss - candle.close);
          
          detectedPatterns.push({
            pattern: patternDef.name,
            type: 'bearish',
            confidence: Math.round(adjustedConfidence),
            description: patternDef.description,
            action: 'SELL',
            strength,
            timeframe: patternDef.timeframe,
            price: candle.close,
            target,
            stopLoss,
            riskReward: Math.round(riskReward * 100) / 100
          });
        }
      }
    }
    
    // Sort by confidence and return top patterns
    return detectedPatterns
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 10);
  }, [data, calculateTechnicalIndicators]);

  // Update patterns when data changes
  useEffect(() => {
    const newPatterns = detectPatterns();
    setPatterns(newPatterns);
    onPatternDetected?.(newPatterns);
  }, [data, detectPatterns, onPatternDetected]);

  // Show alerts for high-confidence patterns
  useEffect(() => {
    if (alertsEnabled && patterns.length > 0) {
      const highConfidencePatterns = patterns.filter(p => p.confidence > 70);
      if (highConfidencePatterns.length > 0) {
        // In a real app, you would show browser notifications here
        console.log('High confidence patterns detected:', highConfidencePatterns);
      }
    }
  }, [patterns, alertsEnabled]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const getPatternIcon = (action: string) => {
    switch (action) {
      case 'BUY': return <CheckCircleIcon className="h-5 w-5 text-success-600" />;
      case 'SELL': return <XCircleIcon className="h-5 w-5 text-danger-600" />;
      default: return <InformationCircleIcon className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'very_strong': return 'text-success-600 bg-success/10';
      case 'strong': return 'text-blue-600 bg-blue/10';
      case 'moderate': return 'text-yellow-600 bg-yellow/10';
      case 'weak': return 'text-muted-foreground bg-muted/10';
      default: return 'text-muted-foreground bg-muted/10';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'bullish': return 'text-success-600 bg-success/10';
      case 'bearish': return 'text-danger-600 bg-danger/10';
      case 'neutral': return 'text-muted-foreground bg-muted/10';
      default: return 'text-muted-foreground bg-muted/10';
    }
  };

  return (
    <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-foreground">Pattern Recognition</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${patterns.length > 0 ? 'bg-success-500' : 'bg-danger-500'}`} />
            <span className="text-sm text-muted-foreground">
              {patterns.length} Patterns Detected
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAlertsEnabled(!alertsEnabled)}
            className={cn(
              "p-2 rounded-lg transition-colors",
              alertsEnabled 
                ? 'text-primary bg-primary/10' 
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            )}
            title="Toggle Alerts"
          >
            <BellIcon className="h-5 w-5" />
          </button>
          <button
            onClick={() => setShowPatterns(!showPatterns)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
            title="Toggle Patterns"
          >
            {showPatterns ? <EyeIcon className="h-5 w-5" /> : <EyeSlashIcon className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Pattern List */}
      {showPatterns && (
        <div className="space-y-3">
          {patterns.length === 0 ? (
            <div className="text-center py-8">
              <ChartBarIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No patterns detected</p>
              <p className="text-sm text-muted-foreground">Analyzing candlestick data for trading signals...</p>
            </div>
          ) : (
            patterns.map((pattern, index) => (
              <div key={index} className="border border-border rounded-lg p-4 hover:bg-muted/30 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getPatternIcon(pattern.action)}
                    <div>
                      <h4 className="font-medium text-foreground">{pattern.pattern}</h4>
                      <p className="text-sm text-muted-foreground">{pattern.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-foreground">
                      {formatCurrency(pattern.price)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {pattern.timeframe}
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                  <div>
                    <span className="text-xs text-muted-foreground">Confidence</span>
                    <div className="text-sm font-medium text-foreground">
                      {pattern.confidence}%
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Strength</span>
                    <div className={cn("text-xs px-2 py-1 rounded", getStrengthColor(pattern.strength))}>
                      {pattern.strength.replace('_', ' ')}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Type</span>
                    <div className={cn("text-xs px-2 py-1 rounded", getTypeColor(pattern.type))}>
                      {pattern.type}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Action</span>
                    <div className={cn(
                      "text-xs px-2 py-1 rounded font-medium",
                      pattern.action === 'BUY' 
                        ? 'text-success-600 bg-success/10'
                        : pattern.action === 'SELL'
                        ? 'text-danger-600 bg-danger/10'
                        : 'text-muted-foreground bg-muted/10'
                    )}>
                      {pattern.action}
                    </div>
                  </div>
                </div>

                {(pattern.target || pattern.stopLoss) && (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-3 border-t border-border">
                    {pattern.target && (
                      <div>
                        <span className="text-xs text-muted-foreground">Target</span>
                        <div className="text-sm font-medium text-success-600">
                          {formatCurrency(pattern.target)}
                        </div>
                      </div>
                    )}
                    {pattern.stopLoss && (
                      <div>
                        <span className="text-xs text-muted-foreground">Stop Loss</span>
                        <div className="text-sm font-medium text-danger-600">
                          {formatCurrency(pattern.stopLoss)}
                        </div>
                      </div>
                    )}
                    {pattern.riskReward && (
                      <div>
                        <span className="text-xs text-muted-foreground">Risk/Reward</span>
                        <div className="text-sm font-medium text-foreground">
                          1:{pattern.riskReward}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Summary Stats */}
      {patterns.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Buy Signals:</span>
              <span className="ml-2 font-medium text-success-600">
                {patterns.filter(p => p.action === 'BUY').length}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Sell Signals:</span>
              <span className="ml-2 font-medium text-danger-600">
                {patterns.filter(p => p.action === 'SELL').length}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">High Confidence:</span>
              <span className="ml-2 font-medium text-foreground">
                {patterns.filter(p => p.confidence > 70).length}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Avg Confidence:</span>
              <span className="ml-2 font-medium text-foreground">
                {Math.round(patterns.reduce((sum, p) => sum + p.confidence, 0) / patterns.length)}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CandlestickPatternRecognition;

