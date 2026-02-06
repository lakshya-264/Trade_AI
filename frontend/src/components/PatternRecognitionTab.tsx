import React, { useState, useEffect, useRef } from 'react';
import { SparklesIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import comprehensiveTradingApi from '../services/comprehensiveTradingApi';
import { toast } from 'react-hot-toast';

interface PatternRecognitionTabProps {
  symbol: string;
  chartData: any[] | { candles: any[] } | any;
  className?: string;
  refreshTrigger?: number;
}

interface Pattern {
  name: string;
  type: 'bullish' | 'bearish' | 'neutral';
  significance: 'high' | 'medium' | 'low';
  count: number;
  description: string;
}

const PatternRecognitionTab: React.FC<PatternRecognitionTabProps> = ({
  symbol,
  chartData,
  className = '',
  refreshTrigger = 0
}) => {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);
  const previousPatternsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (chartData && (Array.isArray(chartData) || chartData.candles)) {
      detectPatterns();
    }
  }, [symbol, chartData, refreshTrigger]);

  const detectPatterns = async () => {
    setLoading(true);
    try {
      // Call backend pattern recognition API
      const response = await comprehensiveTradingApi.analyzePatterns({
        symbol,
        timeframe: '1D',
        patterns: ['all']
      });

      if (response && response.patterns) {
        const detectedPatterns: Pattern[] = response.patterns.map((p: any) => ({
          name: p.name || p.pattern,
          type: p.type || (p.significance === 'high' ? 'bullish' : 'neutral'),
          significance: p.significance || 'medium',
          count: p.count || 1,
          description: p.description || `${p.name} pattern detected`
        }));
        
        // Check for new high-confidence patterns
        const currentPatternSet = new Set(detectedPatterns.map(p => p.name));
        const newHighConfidencePatterns = detectedPatterns.filter(p => 
          p.significance === 'high' && !previousPatternsRef.current.has(p.name)
        );
        
        // Show notifications for new high-confidence patterns
        newHighConfidencePatterns.forEach(pattern => {
          toast.success(
            `🔍 ${pattern.name} pattern detected! ${pattern.description || ''}`,
            {
              icon: pattern.type === 'bullish' ? '📈' : pattern.type === 'bearish' ? '📉' : '📊',
              duration: 4000
            }
          );
        });
        
        previousPatternsRef.current = currentPatternSet;
        setPatterns(detectedPatterns);
      } else {
        // Fallback: Basic pattern detection
        setPatterns(detectBasicPatterns());
      }
    } catch (error) {
      console.error('Pattern detection error:', error);
      setPatterns(detectBasicPatterns());
    } finally {
      setLoading(false);
    }
  };

  const detectBasicPatterns = (): Pattern[] => {
    const chartDataArray = Array.isArray(chartData) ? chartData : (chartData as any)?.candles || [];
    if (!chartDataArray || chartDataArray.length < 3) return [];

    const detected: Pattern[] = [];
    const candles = chartDataArray;

    // Detect Doji
    for (let i = 1; i < candles.length; i++) {
      const candle = candles[i];
      const body = Math.abs(candle.close - candle.open);
      const range = candle.high - candle.low;
      if (range > 0 && body / range < 0.1) {
        detected.push({
          name: 'Doji',
          type: 'neutral',
          significance: 'medium',
          count: 1,
          description: 'Indecision pattern - potential reversal'
        });
        break;
      }
    }

    // Detect Hammer
    for (let i = 1; i < candles.length; i++) {
      const candle = candles[i];
      const body = Math.abs(candle.close - candle.open);
      const lowerShadow = Math.min(candle.open, candle.close) - candle.low;
      const upperShadow = candle.high - Math.max(candle.open, candle.close);
      if (lowerShadow > body * 2 && upperShadow < body * 0.5) {
        detected.push({
          name: 'Hammer',
          type: candle.close > candle.open ? 'bullish' : 'bearish',
          significance: 'high',
          count: 1,
          description: 'Reversal pattern - potential trend change'
        });
        break;
      }
    }

    return detected;
  };

  const getPatternColor = (type: string) => {
    switch (type) {
      case 'bullish': return 'text-green-500 bg-green-500/10 border-green-500/30';
      case 'bearish': return 'text-red-500 bg-red-500/10 border-red-500/30';
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/30';
    }
  };

  const getSignificanceBadge = (significance: string) => {
    switch (significance) {
      case 'high': return 'bg-red-500 text-white';
      case 'medium': return 'bg-yellow-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  return (
    <div className={`${className} space-y-4`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <SparklesIcon className="w-5 h-5 text-purple-500" />
          Pattern Recognition
        </h3>
        <button
          onClick={detectPatterns}
          disabled={loading}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded text-sm transition-colors"
        >
          {loading ? 'Detecting...' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : patterns.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <SparklesIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No patterns detected</p>
          <p className="text-sm mt-2">Patterns will appear here when detected</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patterns.map((pattern, index) => (
            <div
              key={index}
              onClick={() => setSelectedPattern(selectedPattern === pattern.name ? null : pattern.name)}
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                selectedPattern === pattern.name
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-[#2a2e39] bg-[#131722] hover:bg-[#1a1e29]'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getPatternColor(pattern.type)}`}>
                    {pattern.type.toUpperCase()}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getSignificanceBadge(pattern.significance)}`}>
                    {pattern.significance.toUpperCase()}
                  </span>
                </div>
                {pattern.count > 1 && (
                  <span className="text-xs text-gray-400">×{pattern.count}</span>
                )}
              </div>
              <h4 className="text-white font-semibold mb-1">{pattern.name}</h4>
              <p className="text-sm text-gray-400">{pattern.description}</p>
              {selectedPattern === pattern.name && (
                <div className="mt-3 pt-3 border-t border-[#2a2e39]">
                  <div className="flex items-start gap-2 text-xs text-gray-300">
                    <InformationCircleIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium mb-1">Trading Implications:</p>
                      <ul className="list-disc list-inside space-y-1 text-gray-400">
                        {pattern.type === 'bullish' && (
                          <>
                            <li>Potential upward price movement</li>
                            <li>Consider long positions</li>
                            <li>Watch for confirmation</li>
                          </>
                        )}
                        {pattern.type === 'bearish' && (
                          <>
                            <li>Potential downward price movement</li>
                            <li>Consider short positions</li>
                            <li>Watch for confirmation</li>
                          </>
                        )}
                        {pattern.type === 'neutral' && (
                          <>
                            <li>Market indecision</li>
                            <li>Wait for clearer direction</li>
                            <li>Monitor for breakout</li>
                          </>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PatternRecognitionTab;

