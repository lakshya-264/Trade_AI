/**
 * Pattern Detection Overlay Component
 * Displays detected chart patterns directly on the chart with annotations
 */

import React, { useState, useEffect, useRef } from 'react';
import { IChartApi, ISeriesApi, Time } from 'lightweight-charts';
import { httpClient } from '../config/api';

interface Pattern {
  pattern_name: string;
  confidence: number;
  target_price?: number;
  start_time: Time;
  end_time: Time;
  start_price: number;
  end_price: number;
  description: string;
  signal: 'bullish' | 'bearish' | 'neutral';
}

interface PatternApiResponse {
  patterns?: Array<{
    pattern_name?: string;
    pattern_type?: string;
    name?: string;
    confidence?: number;
    strength?: number;
    target_price?: number;
    start_time?: Time;
    start_date?: Time;
    end_time?: Time;
    end_date?: Time;
    start_price?: number;
    end_price?: number;
    price?: number;
    current_price?: number;
    description?: string;
    signal?: 'bullish' | 'bearish' | 'neutral' | 'BUY' | 'SELL' | 'HOLD';
    pattern_direction?: 'bullish' | 'bearish' | 'neutral';
    trading_implications?: {
      signal?: string;
      target_price?: number;
    };
  }>;
  detected_patterns?: Array<{
    pattern_name?: string;
    pattern_type?: string;
    name?: string;
    confidence?: number;
    strength?: number;
    target_price?: number;
    start_time?: Time;
    start_date?: Time;
    end_time?: Time;
    end_date?: Time;
    start_price?: number;
    end_price?: number;
    price?: number;
    current_price?: number;
    description?: string;
    signal?: 'bullish' | 'bearish' | 'neutral' | 'BUY' | 'SELL' | 'HOLD';
    pattern_direction?: 'bullish' | 'bearish' | 'neutral';
    trading_implications?: {
      signal?: string;
      target_price?: number;
    };
  }>;
}

interface PatternDetectionOverlayProps {
  chartApi: IChartApi | null;
  candlestickSeries: ISeriesApi<'Candlestick'> | null;
  symbol: string;
  timeframe: string;
  visible?: boolean;
}

const PatternDetectionOverlay: React.FC<PatternDetectionOverlayProps> = ({
  chartApi,
  candlestickSeries,
  symbol,
  timeframe,
  visible = true
}) => {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(false);
  const markersRef = useRef<any[]>([]);

  // Fetch patterns
  useEffect(() => {
    if (!visible || !symbol) return;

    const fetchPatterns = async () => {
      setLoading(true);
      try {
        const response = await httpClient.get<PatternApiResponse>(`/api/comprehensive-trading/pattern-analysis`, {
          params: {
            symbol,
            timeframe,
            min_confidence: 0.6
          }
        });

        // Handle both 'patterns' and 'detected_patterns' response formats
        const patternsData = response.data?.patterns || response.data?.detected_patterns || [];
        
        if (Array.isArray(patternsData) && patternsData.length > 0) {
          const detectedPatterns: Pattern[] = patternsData
            .filter((p: any) => p && (p.pattern_name || p.pattern_type || p.name)) // Filter out invalid patterns
            .map((p: any) => {
              // Determine signal from pattern direction or trading implications
              let signal: 'bullish' | 'bearish' | 'neutral' = 'neutral';
              if (p.pattern_direction) {
                signal = p.pattern_direction === 'bullish' ? 'bullish' : p.pattern_direction === 'bearish' ? 'bearish' : 'neutral';
              } else if (p.trading_implications?.signal) {
                const implSignal = p.trading_implications.signal.toUpperCase();
                signal = implSignal === 'BUY' ? 'bullish' : implSignal === 'SELL' ? 'bearish' : 'neutral';
              } else if (p.signal) {
                signal = p.signal === 'BUY' || p.signal === 'bullish' ? 'bullish' : 
                         p.signal === 'SELL' || p.signal === 'bearish' ? 'bearish' : 'neutral';
              }
              
              // Get pattern name
              const patternName = p.pattern_name || p.pattern_type?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) || p.name || 'Unknown Pattern';
              
              // Get description
              const description = p.description || 
                                `${patternName} pattern detected${p.confidence ? ` (${(p.confidence * 100).toFixed(0)}% confidence)` : ''}`;
              
              // Get time/price coordinates
              const startTime = p.start_time || p.start_date || (Date.now() / 1000);
              const endTime = p.end_time || p.end_date || (Date.now() / 1000);
              const startPrice = p.start_price || p.current_price || p.price || 0;
              const endPrice = p.end_price || p.current_price || p.price || 0;
              
              return {
                pattern_name: patternName,
                confidence: p.confidence || p.strength || 0.7,
                target_price: p.target_price || p.trading_implications?.target_price,
                start_time: startTime as Time,
                end_time: endTime as Time,
                start_price: startPrice,
                end_price: endPrice,
                description: description,
                signal: signal
              };
            });
          setPatterns(detectedPatterns);
        } else {
          setPatterns([]);
        }
      } catch (error) {
        console.error('Error fetching patterns:', error);
        // Set empty patterns on error to avoid showing stale data
        setPatterns([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPatterns();
  }, [symbol, timeframe, visible]);

  // Draw pattern markers and visualizations on chart
  useEffect(() => {
    if (!candlestickSeries || !chartApi || patterns.length === 0) return;

    // Clear existing markers
    markersRef.current.forEach(marker => {
      try {
        if (marker.priceLine) candlestickSeries.removePriceLine(marker.priceLine);
        if (marker.lineSeries) chartApi.removeSeries(marker.lineSeries);
      } catch (e) {
        // Ignore errors
      }
    });
    markersRef.current = [];

    // Add markers and visualizations for each pattern
    patterns.forEach((pattern, index) => {
      try {
        const patternType = (pattern as any).pattern_type || pattern.pattern_name?.toLowerCase().replace(/\s+/g, '_') || '';
        
        // Add price line at pattern completion/current price
        const priceLine = candlestickSeries.createPriceLine({
          price: pattern.end_price || pattern.start_price,
          color: pattern.signal === 'bullish' ? '#10B981' : pattern.signal === 'bearish' ? '#EF4444' : '#6B7280',
          lineWidth: 1,
          lineStyle: 2, // Dashed
          axisLabelVisible: true,
          title: `${pattern.pattern_name} (${(pattern.confidence * 100).toFixed(0)}%)`
        });

        markersRef.current.push({ priceLine, pattern });

        // Add target price line if available
        if (pattern.target_price) {
          const targetLine = candlestickSeries.createPriceLine({
            price: pattern.target_price,
            color: pattern.signal === 'bullish' ? '#10B98180' : '#EF444480',
            lineWidth: 1,
            lineStyle: 3, // Dotted
            axisLabelVisible: true,
            title: `Target: ₹${pattern.target_price.toFixed(2)}`
          });

          markersRef.current.push({ priceLine: targetLine, pattern });
        }

        // Draw complex patterns with lines/shapes
        const patternData = pattern as any;
        if (patternData.key_points) {
          // Draw pattern shape using line series for complex patterns
          const keyPoints = patternData.key_points;
          const points: Array<{ time: Time; value: number }> = [];
          
          // Extract points based on pattern type
          if (patternType.includes('head_shoulder') || patternType.includes('double')) {
            // For Head & Shoulders and Double Top/Bottom
            if (keyPoints.left_shoulder) points.push({ time: keyPoints.left_shoulder.time as Time, value: keyPoints.left_shoulder.price });
            if (keyPoints.head) points.push({ time: keyPoints.head.time as Time, value: keyPoints.head.price });
            if (keyPoints.right_shoulder) points.push({ time: keyPoints.right_shoulder.time as Time, value: keyPoints.right_shoulder.price });
            if (keyPoints.neckline && points.length > 0) {
              // Draw neckline
              const necklineSeries = chartApi.addLineSeries({
                color: pattern.signal === 'bullish' ? '#10B981' : '#EF4444',
                lineWidth: 2,
                lineStyle: 1, // Solid
                priceLineVisible: false,
                lastValueVisible: false
              });
              necklineSeries.setData([
                { time: points[0].time, value: keyPoints.neckline.price },
                { time: points[points.length - 1].time, value: keyPoints.neckline.price }
              ]);
              markersRef.current.push({ lineSeries: necklineSeries, pattern });
            }
          } else if (patternType.includes('triangle')) {
            // For Triangles - draw converging lines
            if (keyPoints.upper_start && keyPoints.upper_end && keyPoints.lower_start && keyPoints.lower_end) {
              // Upper trendline
              const upperSeries = chartApi.addLineSeries({
                color: pattern.signal === 'bullish' ? '#10B981' : '#EF4444',
                lineWidth: 1,
                lineStyle: 2, // Dashed
                priceLineVisible: false
              });
              upperSeries.setData([
                { time: keyPoints.upper_start.time as Time, value: keyPoints.upper_start.price },
                { time: keyPoints.upper_end.time as Time, value: keyPoints.upper_end.price }
              ]);
              markersRef.current.push({ lineSeries: upperSeries, pattern });
              
              // Lower trendline
              const lowerSeries = chartApi.addLineSeries({
                color: pattern.signal === 'bullish' ? '#10B981' : '#EF4444',
                lineWidth: 1,
                lineStyle: 2, // Dashed
                priceLineVisible: false
              });
              lowerSeries.setData([
                { time: keyPoints.lower_start.time as Time, value: keyPoints.lower_start.price },
                { time: keyPoints.lower_end.time as Time, value: keyPoints.lower_end.price }
              ]);
              markersRef.current.push({ lineSeries: lowerSeries, pattern });
            }
          } else if (patternType.includes('wedge')) {
            // For Wedges - similar to triangles
            if (keyPoints.upper_start && keyPoints.upper_end && keyPoints.lower_start && keyPoints.lower_end) {
              const upperSeries = chartApi.addLineSeries({
                color: pattern.signal === 'bullish' ? '#10B981' : '#EF4444',
                lineWidth: 1,
                lineStyle: 2,
                priceLineVisible: false
              });
              upperSeries.setData([
                { time: keyPoints.upper_start.time as Time, value: keyPoints.upper_start.price },
                { time: keyPoints.upper_end.time as Time, value: keyPoints.upper_end.price }
              ]);
              markersRef.current.push({ lineSeries: upperSeries, pattern });
              
              const lowerSeries = chartApi.addLineSeries({
                color: pattern.signal === 'bullish' ? '#10B981' : '#EF4444',
                lineWidth: 1,
                lineStyle: 2,
                priceLineVisible: false
              });
              lowerSeries.setData([
                { time: keyPoints.lower_start.time as Time, value: keyPoints.lower_start.price },
                { time: keyPoints.lower_end.time as Time, value: keyPoints.lower_end.price }
              ]);
              markersRef.current.push({ lineSeries: lowerSeries, pattern });
            }
          } else if (patternType.includes('cup_handle')) {
            // For Cup & Handle - draw U-shape approximation
            if (keyPoints.cup_start && keyPoints.cup_bottom && keyPoints.cup_rim && keyPoints.handle_end) {
              const cupSeries = chartApi.addLineSeries({
                color: '#10B981',
                lineWidth: 2,
                lineStyle: 1,
                priceLineVisible: false
              });
              // Approximate cup shape with multiple points
              cupSeries.setData([
                { time: keyPoints.cup_start.time as Time, value: keyPoints.cup_start.price },
                { time: keyPoints.cup_bottom.time as Time, value: keyPoints.cup_bottom.price },
                { time: keyPoints.cup_rim.time as Time, value: keyPoints.cup_rim.price },
                { time: keyPoints.handle_end.time as Time, value: keyPoints.handle_end.price }
              ]);
              markersRef.current.push({ lineSeries: cupSeries, pattern });
            }
          } else if (patternType.includes('flag') || patternType.includes('pennant')) {
            // For Flags & Pennants - draw pole and flag/pennant
            if (keyPoints.pole_start && keyPoints.pole_end && keyPoints.flag_start && keyPoints.flag_end) {
              // Pole line
              const poleSeries = chartApi.addLineSeries({
                color: pattern.signal === 'bullish' ? '#10B981' : '#EF4444',
                lineWidth: 2,
                lineStyle: 1,
                priceLineVisible: false
              });
              poleSeries.setData([
                { time: keyPoints.pole_start.time as Time, value: keyPoints.pole_start.price },
                { time: keyPoints.pole_end.time as Time, value: keyPoints.pole_end.price }
              ]);
              markersRef.current.push({ lineSeries: poleSeries, pattern });
              
              // Flag/Pennant lines
              const flagSeries = chartApi.addLineSeries({
                color: pattern.signal === 'bullish' ? '#10B981' : '#EF4444',
                lineWidth: 1,
                lineStyle: 2,
                priceLineVisible: false
              });
              flagSeries.setData([
                { time: keyPoints.flag_start.time as Time, value: keyPoints.flag_start.price },
                { time: keyPoints.flag_end.time as Time, value: keyPoints.flag_end.price }
              ]);
              markersRef.current.push({ lineSeries: flagSeries, pattern });
            }
          }
        }
      } catch (error) {
        console.debug('Error adding pattern visualization:', error);
      }
    });

    return () => {
      markersRef.current.forEach(marker => {
        try {
          if (marker.priceLine) candlestickSeries.removePriceLine(marker.priceLine);
          if (marker.lineSeries) chartApi.removeSeries(marker.lineSeries);
        } catch (e) {
          // Ignore errors
        }
      });
      markersRef.current = [];
    };
  }, [patterns, candlestickSeries, chartApi]);

  if (!visible) return null;

  return (
    <div className="absolute top-4 left-4 bg-[#1e222d]/90 border border-[#2a2e39] rounded-lg p-3 z-10 max-w-xs">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-white">Detected Patterns</h4>
        {loading && (
          <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
        )}
      </div>
      
      {patterns.length > 0 ? (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {patterns.map((pattern, index) => (
            <div
              key={index}
              className={`p-2 rounded text-xs border ${
                pattern.signal === 'bullish'
                  ? 'bg-green-500/20 border-green-500/50'
                  : pattern.signal === 'bearish'
                  ? 'bg-red-500/20 border-red-500/50'
                  : 'bg-gray-500/20 border-gray-500/50'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-white">{pattern.pattern_name}</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                  pattern.signal === 'bullish'
                    ? 'bg-green-500 text-white'
                    : pattern.signal === 'bearish'
                    ? 'bg-red-500 text-white'
                    : 'bg-gray-500 text-white'
                }`}>
                  {(pattern.confidence * 100).toFixed(0)}%
                </span>
              </div>
              {pattern.target_price && (
                <div className="text-gray-300 text-[10px]">
                  Target: ₹{pattern.target_price.toFixed(2)}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-gray-400 text-xs text-center py-2">
          {loading ? 'Detecting patterns...' : 'No patterns detected'}
        </div>
      )}
    </div>
  );
};

export default PatternDetectionOverlay;

