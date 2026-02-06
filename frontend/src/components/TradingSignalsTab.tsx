import React, { useState, useEffect } from 'react';
import { SignalIcon, ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';
import comprehensiveTradingApi from '../services/comprehensiveTradingApi';

interface TradingSignalsTabProps {
  symbol: string;
  chartData: any[] | { candles: any[] } | any;
  currentPrice?: number;
  className?: string;
  refreshTrigger?: number; // Trigger refresh when this changes
}

interface SmartRecommendation {
  action: 'BUY' | 'SELL' | 'HOLD';
  entryPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  confidence: number;
  reasoning: string[];
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
}

interface Signal {
  type: 'BUY' | 'SELL' | 'HOLD';
  indicator: string;
  value: number;
  confidence: number;
  message: string;
  timestamp: string;
}

const TradingSignalsTab: React.FC<TradingSignalsTabProps> = ({
  symbol,
  chartData,
  currentPrice,
  className = '',
  refreshTrigger = 0
}) => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(false);
  const [overallSignal, setOverallSignal] = useState<'BUY' | 'SELL' | 'HOLD'>('HOLD');
  const [overallConfidence, setOverallConfidence] = useState(0);
  const [smartRecommendation, setSmartRecommendation] = useState<SmartRecommendation | null>(null);

  useEffect(() => {
    if (chartData && (Array.isArray(chartData) || chartData.candles)) {
      generateSignals();
    }
  }, [symbol, chartData, currentPrice, refreshTrigger]);

  const generateSignals = async () => {
    setLoading(true);
    try {
      // Use fallback: Generate signals from chart data
      // (Backend getTradingSignals method doesn't exist, using local calculation)
      const generatedSignals = generateBasicSignals();
      setSignals(generatedSignals);
      calculateOverallSignal(generatedSignals);
    } catch (error) {
      console.error('Signal generation error:', error);
      const generatedSignals = generateBasicSignals();
      setSignals(generatedSignals);
      calculateOverallSignal(generatedSignals);
    } finally {
      setLoading(false);
    }
  };

  const generateBasicSignals = (): Signal[] => {
    const chartDataArray = Array.isArray(chartData) ? chartData : (chartData as any)?.candles || [];
    // Need at least 30 candles for proper 14-period RSI calculation
    if (!chartDataArray || chartDataArray.length < 30) return [];

    const candles = chartDataArray;
    // Use more data points for accurate RSI (at least 30 candles)
    const recent = candles.slice(-Math.max(30, candles.length));
    const signals: Signal[] = [];

    // RSI Signal - Proper 14-period RSI with Wilder's Smoothing
    const closes = recent.map((c: any) => {
      // Handle both timestamp formats
      const time = c.time;
      if (typeof time === 'number') {
        return c.close;
      }
      return c.close;
    }).filter((v: any) => v != null && !isNaN(v));

    if (closes.length < 15) return [];

    const period = 14; // Standard RSI period
    const gains: number[] = [];
    const losses: number[] = [];

    // Calculate price changes
    for (let i = 1; i < closes.length; i++) {
      const change = closes[i] - closes[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }

    // Initial average gain/loss (simple average for first period)
    let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

    // Wilder's Smoothing: EMA-like calculation for remaining periods
    for (let i = period; i < gains.length; i++) {
      avgGain = (avgGain * (period - 1) + gains[i]) / period;
      avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    }

    // Calculate RSI
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    const rsi = 100 - (100 / (1 + rs));

    // Determine signal based on RSI value
    let rsiType: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    let rsiConfidence = 50;
    let rsiMessage = 'RSI in neutral zone';

    if (rsi < 30) {
      // Oversold - Buy signal
      rsiType = 'BUY';
      rsiConfidence = rsi < 20 ? 85 : rsi < 25 ? 75 : 65;
      rsiMessage = `RSI indicates oversold condition (${rsi.toFixed(2)}) - Buy signal`;
    } else if (rsi > 70) {
      // Overbought - Sell signal
      rsiType = 'SELL';
      rsiConfidence = rsi > 80 ? 85 : rsi > 75 ? 75 : 65;
      rsiMessage = `RSI indicates overbought condition (${rsi.toFixed(2)}) - Sell signal`;
    } else if (rsi < 40) {
      // Lower neutral zone - Slightly bearish, but not oversold
      rsiType = 'HOLD';
      rsiConfidence = 45;
      rsiMessage = `RSI in lower neutral zone (${rsi.toFixed(2)}) - Watch for potential buy opportunity`;
    } else if (rsi > 60) {
      // Upper neutral zone - Slightly bullish, but not overbought
      rsiType = 'HOLD';
      rsiConfidence = 45;
      rsiMessage = `RSI in upper neutral zone (${rsi.toFixed(2)}) - Watch for potential sell opportunity`;
    } else {
      // True neutral zone (40-60)
      rsiType = 'HOLD';
      rsiConfidence = 50;
      rsiMessage = `RSI in neutral zone (${rsi.toFixed(2)})`;
    }

    signals.push({
      type: rsiType,
      indicator: 'RSI',
      value: rsi,
      confidence: rsiConfidence,
      message: rsiMessage,
      timestamp: new Date().toISOString()
    });

    // Calculate Moving Averages
    const currentPrice = closes[closes.length - 1];
    
    // SMA20 (Short-term trend)
    const sma20 = closes.length >= 20
      ? closes.slice(-20).reduce((a: number, b: number) => a + b, 0) / 20
      : null;
    
    // SMA50 (Medium-term trend)
    const sma50 = closes.length >= 50
      ? closes.slice(-50).reduce((a: number, b: number) => a + b, 0) / 50
      : null;
    
    // SMA200 (Long-term trend)
    const sma200 = closes.length >= 200
      ? closes.slice(-200).reduce((a: number, b: number) => a + b, 0) / 200
      : closes.length >= 100
      ? closes.slice(0, closes.length).reduce((a: number, b: number) => a + b, 0) / closes.length // Fallback for insufficient data
      : null;

    // SMA20 Signal (Short-term trend)
    if (sma20 !== null) {
      const priceVsSMA20 = ((currentPrice - sma20) / sma20) * 100;
      
      if (currentPrice > sma20 * 1.02) {
        signals.push({
          type: 'BUY',
          indicator: 'SMA20',
          value: sma20,
          confidence: 60,
          message: `Price above SMA20 (+${priceVsSMA20.toFixed(2)}%) - Short-term bullish`,
          timestamp: new Date().toISOString()
        });
      } else if (currentPrice < sma20 * 0.98) {
        signals.push({
          type: 'SELL',
          indicator: 'SMA20',
          value: sma20,
          confidence: 60,
          message: `Price below SMA20 (${priceVsSMA20.toFixed(2)}%) - Short-term bearish`,
          timestamp: new Date().toISOString()
        });
      }
    }

    // SMA50 Signal (Medium-term trend)
    if (sma50 !== null) {
      const priceVsSMA50 = ((currentPrice - sma50) / sma50) * 100;
      
      if (currentPrice > sma50 * 1.03) {
        signals.push({
          type: 'BUY',
          indicator: 'SMA50',
          value: sma50,
          confidence: 65,
          message: `Price significantly above SMA50 (+${priceVsSMA50.toFixed(2)}%) - Medium-term uptrend`,
          timestamp: new Date().toISOString()
        });
      } else if (currentPrice > sma50) {
        signals.push({
          type: 'BUY',
          indicator: 'SMA50',
          value: sma50,
          confidence: 60,
          message: `Price above SMA50 (+${priceVsSMA50.toFixed(2)}%) - Medium-term uptrend`,
          timestamp: new Date().toISOString()
        });
      } else if (currentPrice < sma50 * 0.97) {
        signals.push({
          type: 'SELL',
          indicator: 'SMA50',
          value: sma50,
          confidence: 65,
          message: `Price significantly below SMA50 (${priceVsSMA50.toFixed(2)}%) - Medium-term downtrend`,
          timestamp: new Date().toISOString()
        });
      } else {
        signals.push({
          type: 'SELL',
          indicator: 'SMA50',
          value: sma50,
          confidence: 60,
          message: `Price below SMA50 (${priceVsSMA50.toFixed(2)}%) - Medium-term downtrend`,
          timestamp: new Date().toISOString()
        });
      }
    }

    // SMA200 Signal (Long-term trend) - Most Important
    if (sma200 !== null) {
      const priceVsSMA200 = ((currentPrice - sma200) / sma200) * 100;
      
      if (currentPrice > sma200 * 1.05) {
        signals.push({
          type: 'BUY',
          indicator: 'SMA200',
          value: sma200,
          confidence: 75,
          message: `Price significantly above SMA200 (+${priceVsSMA200.toFixed(2)}%) - Strong long-term uptrend`,
          timestamp: new Date().toISOString()
        });
      } else if (currentPrice > sma200) {
        signals.push({
          type: 'BUY',
          indicator: 'SMA200',
          value: sma200,
          confidence: 70,
          message: `Price above SMA200 (+${priceVsSMA200.toFixed(2)}%) - Long-term uptrend`,
          timestamp: new Date().toISOString()
        });
      } else if (currentPrice < sma200 * 0.95) {
        signals.push({
          type: 'SELL',
          indicator: 'SMA200',
          value: sma200,
          confidence: 75,
          message: `Price significantly below SMA200 (${priceVsSMA200.toFixed(2)}%) - Strong long-term downtrend`,
          timestamp: new Date().toISOString()
        });
      } else {
        signals.push({
          type: 'SELL',
          indicator: 'SMA200',
          value: sma200,
          confidence: 70,
          message: `Price below SMA200 (${priceVsSMA200.toFixed(2)}%) - Long-term downtrend`,
          timestamp: new Date().toISOString()
        });
      }
    }

    // Golden Cross / Death Cross Detection (SMA50 vs SMA200)
    if (sma50 !== null && sma200 !== null) {
      const previousSMA50 = closes.length >= 51
        ? closes.slice(-51, -1).reduce((a: number, b: number) => a + b, 0) / 50
        : sma50;
      const previousSMA200 = closes.length >= 201
        ? closes.slice(-201, -1).reduce((a: number, b: number) => a + b, 0) / 200
        : sma200;
      
      // Check for Golden Cross (SMA50 crosses above SMA200)
      if (sma50 > sma200 && previousSMA50 <= previousSMA200) {
        signals.push({
          type: 'BUY',
          indicator: 'Golden Cross',
          value: sma50 - sma200,
          confidence: 85,
          message: 'Golden Cross detected! SMA50 crossed above SMA200 - Strong bullish signal',
          timestamp: new Date().toISOString()
        });
      }
      // Check for Death Cross (SMA50 crosses below SMA200)
      else if (sma50 < sma200 && previousSMA50 >= previousSMA200) {
        signals.push({
          type: 'SELL',
          indicator: 'Death Cross',
          value: sma50 - sma200,
          confidence: 85,
          message: 'Death Cross detected! SMA50 crossed below SMA200 - Strong bearish signal',
          timestamp: new Date().toISOString()
        });
      }
    }

    // Multi-MA Alignment Signals (Strongest signals)
    if (sma20 !== null && sma50 !== null && sma200 !== null) {
      // Perfect Bullish Alignment: Price > SMA20 > SMA50 > SMA200
      if (currentPrice > sma20 && sma20 > sma50 && sma50 > sma200) {
        signals.push({
          type: 'BUY',
          indicator: 'Multi-MA Alignment',
          value: currentPrice,
          confidence: 90,
          message: 'Perfect bullish alignment: Price > SMA20 > SMA50 > SMA200 - Very strong buy signal',
          timestamp: new Date().toISOString()
        });
      }
      // Perfect Bearish Alignment: Price < SMA20 < SMA50 < SMA200
      else if (currentPrice < sma20 && sma20 < sma50 && sma50 < sma200) {
        signals.push({
          type: 'SELL',
          indicator: 'Multi-MA Alignment',
          value: currentPrice,
          confidence: 90,
          message: 'Perfect bearish alignment: Price < SMA20 < SMA50 < SMA200 - Very strong sell signal',
          timestamp: new Date().toISOString()
        });
      }
      // Partial Bullish Alignment: Price > SMA20 > SMA50 (SMA200 not aligned)
      else if (currentPrice > sma20 && sma20 > sma50) {
        signals.push({
          type: 'BUY',
          indicator: 'Multi-MA Alignment',
          value: currentPrice,
          confidence: 75,
          message: 'Bullish alignment: Price > SMA20 > SMA50 - Strong buy signal',
          timestamp: new Date().toISOString()
        });
      }
      // Partial Bearish Alignment: Price < SMA20 < SMA50 (SMA200 not aligned)
      else if (currentPrice < sma20 && sma20 < sma50) {
        signals.push({
          type: 'SELL',
          indicator: 'Multi-MA Alignment',
          value: currentPrice,
          confidence: 75,
          message: 'Bearish alignment: Price < SMA20 < SMA50 - Strong sell signal',
          timestamp: new Date().toISOString()
        });
      }
    }

    return signals;
  };

  const calculateOverallSignal = (signals: Signal[]) => {
    if (signals.length === 0) {
      setOverallSignal('HOLD');
      setOverallConfidence(0);
      setSmartRecommendation(null);
      return;
    }

    const buyCount = signals.filter(s => s.type === 'BUY').length;
    const sellCount = signals.filter(s => s.type === 'SELL').length;
    const holdCount = signals.filter(s => s.type === 'HOLD').length;

    const totalConfidence = signals.reduce((sum, s) => sum + s.confidence, 0);
    const avgConfidence = totalConfidence / signals.length;

    let finalSignal: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
    let finalConfidence = 0;

    if (buyCount > sellCount && buyCount > holdCount) {
      finalSignal = 'BUY';
      finalConfidence = avgConfidence;
    } else if (sellCount > buyCount && sellCount > holdCount) {
      finalSignal = 'SELL';
      finalConfidence = avgConfidence;
    } else {
      finalSignal = 'HOLD';
      finalConfidence = avgConfidence * 0.5;
    }

    setOverallSignal(finalSignal);
    setOverallConfidence(finalConfidence);

    // Generate smart recommendation
    generateSmartRecommendation(signals, finalSignal, finalConfidence);
  };

  const generateSmartRecommendation = (
    signals: Signal[],
    signal: 'BUY' | 'SELL' | 'HOLD',
    confidence: number
  ) => {
    const chartDataArray = Array.isArray(chartData) ? chartData : (chartData as any)?.candles || [];
    if (!chartDataArray || chartDataArray.length < 20 || !currentPrice) {
      setSmartRecommendation(null);
      return;
    }

    const candles = chartDataArray;
    const recent = candles.slice(-20);
    const currentClose = currentPrice;
    const recentHigh = Math.max(...recent.map((c: any) => c.high));
    const recentLow = Math.min(...recent.map((c: any) => c.low));
    const atr = (recentHigh - recentLow) / 20; // Simplified ATR

    const reasoning: string[] = [];
    signals.forEach(s => {
      if (s.type === signal) {
        reasoning.push(`${s.indicator}: ${s.message}`);
      }
    });

    let entryPrice: number | undefined;
    let stopLoss: number | undefined;
    let takeProfit: number | undefined;
    let riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' = 'MEDIUM';

    if (signal === 'BUY' && confidence > 60) {
      entryPrice = currentClose;
      stopLoss = currentClose - (atr * 2);
      takeProfit = currentClose + (atr * 3);
      riskLevel = confidence > 80 ? 'LOW' : confidence > 65 ? 'MEDIUM' : 'HIGH';
    } else if (signal === 'SELL' && confidence > 60) {
      entryPrice = currentClose;
      stopLoss = currentClose + (atr * 2);
      takeProfit = currentClose - (atr * 3);
      riskLevel = confidence > 80 ? 'LOW' : confidence > 65 ? 'MEDIUM' : 'HIGH';
    }

    if (entryPrice) {
      setSmartRecommendation({
        action: signal,
        entryPrice,
        stopLoss,
        takeProfit,
        confidence,
        reasoning,
        riskLevel
      });
    } else {
      setSmartRecommendation(null);
    }
  };

  const getSignalColor = (type: string) => {
    switch (type) {
      case 'BUY': return 'text-green-500 bg-green-500/10 border-green-500/30';
      case 'SELL': return 'text-red-500 bg-red-500/10 border-red-500/30';
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/30';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return 'text-green-500';
    if (confidence >= 50) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className={`${className} space-y-4`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <SignalIcon className="w-5 h-5 text-blue-500" />
          Trading Signals
        </h3>
        <button
          onClick={generateSignals}
          disabled={loading}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded text-sm transition-colors"
        >
          {loading ? 'Generating...' : 'Refresh'}
        </button>
      </div>

      {/* Overall Signal */}
      <div className={`p-4 rounded-lg border-2 ${getSignalColor(overallSignal)}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {overallSignal === 'BUY' ? (
              <ArrowTrendingUpIcon className="w-8 h-8 text-green-500" />
            ) : overallSignal === 'SELL' ? (
              <ArrowTrendingDownIcon className="w-8 h-8 text-red-500" />
            ) : (
              <SignalIcon className="w-8 h-8 text-gray-500" />
            )}
            <div>
              <div className="text-sm text-gray-400">Overall Signal</div>
              <div className="text-2xl font-bold">{overallSignal}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">Confidence</div>
            <div className={`text-2xl font-bold ${getConfidenceColor(overallConfidence)}`}>
              {overallConfidence.toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* Smart Recommendations Panel */}
      {smartRecommendation && (
        <div className="mb-4 p-4 bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-lg border border-blue-500/30">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-lg font-semibold text-white flex items-center gap-2">
              <SignalIcon className="w-5 h-5" />
              Smart Recommendation
            </h4>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
              smartRecommendation.riskLevel === 'LOW' ? 'bg-green-500/20 text-green-400' :
              smartRecommendation.riskLevel === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {smartRecommendation.riskLevel} Risk
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-3">
            {smartRecommendation.entryPrice && (
              <div>
                <div className="text-xs text-gray-400 mb-1">Entry Price</div>
                <div className="text-lg font-bold text-white">₹{smartRecommendation.entryPrice.toFixed(2)}</div>
              </div>
            )}
            {smartRecommendation.stopLoss && (
              <div>
                <div className="text-xs text-gray-400 mb-1">Stop Loss</div>
                <div className="text-lg font-bold text-red-400">₹{smartRecommendation.stopLoss.toFixed(2)}</div>
              </div>
            )}
            {smartRecommendation.takeProfit && (
              <div>
                <div className="text-xs text-gray-400 mb-1">Take Profit</div>
                <div className="text-lg font-bold text-green-400">₹{smartRecommendation.takeProfit.toFixed(2)}</div>
              </div>
            )}
            <div>
              <div className="text-xs text-gray-400 mb-1">Confidence</div>
              <div className={`text-lg font-bold ${getConfidenceColor(smartRecommendation.confidence)}`}>
                {smartRecommendation.confidence.toFixed(0)}%
              </div>
            </div>
          </div>

          {smartRecommendation.reasoning.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-700">
              <div className="text-xs text-gray-400 mb-2">Reasoning:</div>
              <ul className="space-y-1">
                {smartRecommendation.reasoning.slice(0, 3).map((reason, idx) => (
                  <li key={idx} className="text-sm text-gray-300">• {reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : signals.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <SignalIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No signals generated</p>
          <p className="text-sm mt-2">Signals will appear here when available</p>
        </div>
      ) : (
        <div className="space-y-3">
          {signals.map((signal, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border ${getSignalColor(signal.type)}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded text-xs font-semibold bg-white/10">
                    {signal.indicator}
                  </span>
                  <span className={`text-sm font-semibold ${getConfidenceColor(signal.confidence)}`}>
                    {signal.confidence}% confidence
                  </span>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(signal.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="text-white font-medium mb-1">{signal.message}</div>
              {signal.value !== 0 && (
                <div className="text-xs text-gray-400">
                  Value: {signal.value.toFixed(2)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TradingSignalsTab;

