/**
 * Pattern Visualization Component
 * Draws detected chart patterns on Lightweight Charts
 */

import React, { useEffect, useRef, useState } from 'react';
import { IChartApi, ISeriesApi, PriceLineOptions, LineStyle, Time } from 'lightweight-charts';
import { httpClient } from '../config/api';

interface PatternVisualizationProps {
  symbol: string;
  timeframe?: string;
  chartApi: IChartApi;
  candlestickSeries: ISeriesApi<'Candlestick'>;
  visible?: boolean;
}

interface PatternLine {
  type: 'horizontal' | 'trendline';
  price?: number;
  color: string;
  style: 'solid' | 'dashed' | 'dotted';
  width: number;
  label?: string;
  points?: Array<{ index: number; price: number; time?: Time }>;
  start_index?: number;
  end_index?: number;
}

interface PatternAnnotation {
  index: number;
  price: number;
  label: string;
  color: string;
  position: 'aboveBar' | 'belowBar';
}

interface PatternVisualization {
  pattern_type: string;
  lines: PatternLine[];
  annotations: PatternAnnotation[];
  target_levels: Array<{ price: number; label: string }>;
}

interface PatternVisualizationApiResponse {
  patterns?: PatternVisualization[];
  visualizations?: PatternVisualization[];
  symbol?: string;
  timeframe?: string;
}

const PatternVisualization: React.FC<PatternVisualizationProps> = ({
  symbol,
  timeframe = '1W',
  chartApi,
  candlestickSeries,
  visible = true
}) => {
  const priceLinesRef = useRef<Map<string, any>>(new Map());
  const lineSeriesRef = useRef<Map<string, ISeriesApi<'Line'>>>(new Map());
  const markersRef = useRef<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<PatternVisualization[]>([]);

  useEffect(() => {
    if (!visible || !symbol) return;

    loadPatternVisualization();

    return () => {
      // Cleanup on unmount
      clearVisualizations();
    };
  }, [symbol, timeframe, visible]);

  const loadPatternVisualization = async () => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      const response = await httpClient.get<PatternVisualizationApiResponse>(
        `/api/charting/pattern-visualization/${symbol}`,
        {
          timeframe,
          period: '1y'
        }
      );

      const payload = response.data;

      if (response.success && payload?.visualizations) {
        setPatterns(payload.visualizations);
        drawPatterns(payload.visualizations);
      }
    } catch (err: any) {
      console.error('Error loading pattern visualization:', err);
      setError(err.message || 'Failed to load pattern visualization');
    } finally {
      setLoading(false);
    }
  };

  const clearVisualizations = () => {
    // Remove all price lines
    priceLinesRef.current.forEach((priceLine) => {
      try {
        candlestickSeries.removePriceLine(priceLine);
      } catch (e) {
        // Ignore errors
      }
    });
    priceLinesRef.current.clear();

    // Remove all line series
    lineSeriesRef.current.forEach((lineSeries) => {
      try {
        chartApi.removeSeries(lineSeries);
      } catch (e) {
        // Ignore errors
      }
    });
    lineSeriesRef.current.clear();

    // Clear markers
    if (markersRef.current.length > 0) {
      candlestickSeries.setMarkers([]);
      markersRef.current = [];
    }
  };

  const drawPatterns = (visualizations: PatternVisualization[]) => {
    if (!visualizations || visualizations.length === 0) return;

    clearVisualizations();

    visualizations.forEach((viz, vizIndex) => {
      // Draw horizontal lines (necklines, targets, etc.)
      viz.lines.forEach((line, lineIndex) => {
        if (line.type === 'horizontal' && line.price) {
          try {
            const lineStyle = line.style === 'dashed' 
              ? LineStyle.Dashed 
              : line.style === 'dotted'
              ? LineStyle.Dotted
              : LineStyle.Solid;

            const priceLine = candlestickSeries.createPriceLine({
              price: line.price,
              color: line.color,
              lineWidth: line.width as 1 | 2 | 3 | 4,
              lineStyle: lineStyle,
              axisLabelVisible: true,
              title: line.label || `${viz.pattern_type}: ₹${line.price.toFixed(2)}`,
            });

            const key = `price-line-${vizIndex}-${lineIndex}`;
            priceLinesRef.current.set(key, priceLine);
          } catch (e) {
            console.error('Error drawing horizontal line:', e);
          }
        } else if (line.type === 'trendline' && line.points && line.points.length >= 2) {
          // Draw trendlines using line series
          // Note: Trendlines require time values. If indices are provided, we'll skip for now
          // as we need access to the actual chart data to map indices to times.
          // This is a known limitation - horizontal lines (necklines, targets) work perfectly.
          try {
            // Check if we have time values in points
            const hasTimeValues = line.points.some(p => p.time !== undefined);
            
            if (!hasTimeValues) {
              // Skip trendlines without time values for now
              // TODO: Fetch chart data to map indices to times
              console.warn('Trendline skipped: No time values provided. Indices need to be mapped to chart times.');
              return;
            }

            const lineSeries = chartApi.addLineSeries({
              color: line.color,
              lineWidth: line.width as 1 | 2 | 3 | 4,
              lineStyle: line.style === 'dashed' 
                ? LineStyle.Dashed 
                : line.style === 'dotted'
                ? LineStyle.Dotted
                : LineStyle.Solid,
              priceLineVisible: false,
              lastValueVisible: false,
            });

            // Convert points to chart data format
            const trendlineData = line.points
              .filter(p => p.time !== undefined)
              .map((point) => ({
                time: point.time as Time,
                value: point.price
              }));

            if (trendlineData.length >= 2) {
              lineSeries.setData(trendlineData);
              const key = `trendline-${vizIndex}-${lineIndex}`;
              lineSeriesRef.current.set(key, lineSeries);
            }
          } catch (e) {
            console.error('Error drawing trendline:', e);
          }
        }
      });

      // Draw annotations as markers
      // Note: Markers also need time values. If only index is provided, skip for now.
      viz.annotations.forEach((annotation, annIndex) => {
        try {
          // Check if we have a time value (not just index)
          // For now, skip annotations without proper time mapping
          // TODO: Map indices to times from chart data
          if (typeof annotation.index === 'number' && annotation.index > 1000000000) {
            // Likely a timestamp, use as time
            markersRef.current.push({
              time: annotation.index as Time,
              position: annotation.position,
              color: annotation.color,
              shape: 'circle',
              text: annotation.label,
              size: 1
            });
          } else {
            // Skip - need proper time mapping
            console.warn('Annotation skipped: Index needs to be mapped to chart time');
          }
        } catch (e) {
          console.error('Error adding annotation:', e);
        }
      });

      // Draw target levels as horizontal lines
      viz.target_levels.forEach((target, targetIndex) => {
        try {
          const priceLine = candlestickSeries.createPriceLine({
            price: target.price,
            color: '#F59E0B', // Orange for targets
            lineWidth: 2,
            lineStyle: LineStyle.Dashed,
            axisLabelVisible: true,
            title: target.label || `Target: ₹${target.price.toFixed(2)}`,
          });

          const key = `target-${vizIndex}-${targetIndex}`;
          priceLinesRef.current.set(key, priceLine);
        } catch (e) {
          console.error('Error drawing target level:', e);
        }
      });
    });

    // Apply all markers at once
    if (markersRef.current.length > 0) {
      candlestickSeries.setMarkers(markersRef.current);
    }
  };

  // Redraw when patterns change
  useEffect(() => {
    if (patterns.length > 0 && visible) {
      drawPatterns(patterns);
    }
  }, [patterns, visible]);

  // Don't render anything - this component only draws on the chart
  return null;
};

export default PatternVisualization;

