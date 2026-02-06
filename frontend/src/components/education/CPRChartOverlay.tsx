/**
 * CPR Chart Overlay Component
 * Displays Central Pivot Range levels on charts
 */

import React, { useEffect, useRef } from 'react';
import { IChartApi, ISeriesApi, PriceLineOptions, LineStyle } from 'lightweight-charts';
import { httpClient } from '../../config/api';

interface CPRChartOverlayProps {
  symbol: string;
  chartApi: IChartApi;
  candlestickSeries: ISeriesApi<'Candlestick'>;
  visible?: boolean;
}

interface Candlestick {
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface CPRData {
  pivot_point: number;
  cpr_top: number;
  cpr_bottom: number;
  cpr_width: number;
  tc: number;  // Top Central Pivot
  bc: number;  // Bottom Central Pivot
  r1?: number;
  r2?: number;
  s1?: number;
  s2?: number;
}

const CPRChartOverlay: React.FC<CPRChartOverlayProps> = ({
  symbol,
  chartApi,
  candlestickSeries,
  visible = true
}) => {
  const priceLinesRef = useRef<Map<string, any>>(new Map());

  useEffect(() => {
    if (!visible || !symbol) return;

    loadCPRData();

    return () => {
      // Cleanup price lines
      priceLinesRef.current.forEach((line) => {
        try {
          candlestickSeries.removePriceLine(line);
        } catch (e) {
          // Ignore errors during cleanup
        }
      });
      priceLinesRef.current.clear();
    };
  }, [symbol, visible]);

  const loadCPRData = async () => {
    try {
      // Get latest candle data to calculate CPR
      const response = await httpClient.get<{ candlesticks?: Candlestick[] }>(
        `/api/financial/candlestick/${symbol}`,
        { timeframe: '1D', period: 2 }
      );
      
      const candles = response.data?.candlesticks;
      if (!Array.isArray(candles) || candles.length < 1) {
        return;
      }
      const latestCandle = candles[candles.length - 1];
      const previousCandle = candles.length > 1 ? candles[candles.length - 2] : latestCandle;

      // Calculate CPR from previous day's data
      const high = previousCandle.high;
      const low = previousCandle.low;
      const close = previousCandle.close;

      // Calculate CPR
      const pivotPoint = (high + low + close) / 3;
      const tc = (high + low) / 2;
      const bc = (pivotPoint - tc) + pivotPoint;
      const cprTop = Math.max(tc, bc);
      const cprBottom = Math.min(tc, bc);

      const cprData: CPRData = {
        pivot_point: pivotPoint,
        cpr_top: cprTop,
        cpr_bottom: cprBottom,
        cpr_width: cprTop - cprBottom,
        tc: tc,
        bc: bc
      };

      drawCPRLines(cprData);
    } catch (error) {
      console.error('Error loading CPR data:', error);
    }
  };

  const drawCPRLines = (cpr: CPRData) => {
    // Remove existing lines
    priceLinesRef.current.forEach((line) => {
      try {
        candlestickSeries.removePriceLine(line);
      } catch (e) {
        // Ignore
      }
    });
    priceLinesRef.current.clear();

    // Pivot Point (PP) - Blue solid line
    const ppLine: PriceLineOptions = {
      price: cpr.pivot_point,
      color: '#3B82F6',
      lineWidth: 2,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: true,
      title: 'PP',
      lineVisible: true,
      axisLabelColor: '#cbd5f5',
      axisLabelTextColor: '#0f172a'
    };
    const ppPriceLine = candlestickSeries.createPriceLine(ppLine);
    priceLinesRef.current.set('pp', ppPriceLine);

    // CPR Top - Green dashed line
    const cprTopLine: PriceLineOptions = {
      price: cpr.cpr_top,
      color: '#10B981',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: 'CPR Top',
      lineVisible: true,
      axisLabelColor: '#cbd5f5',
      axisLabelTextColor: '#0f172a'
    };
    const cprTopPriceLine = candlestickSeries.createPriceLine(cprTopLine);
    priceLinesRef.current.set('cpr_top', cprTopPriceLine);

    // CPR Bottom - Red dashed line
    const cprBottomLine: PriceLineOptions = {
      price: cpr.cpr_bottom,
      color: '#EF4444',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: 'CPR Bottom',
      lineVisible: true,
      axisLabelColor: '#cbd5f5',
      axisLabelTextColor: '#0f172a'
    };
    const cprBottomPriceLine = candlestickSeries.createPriceLine(cprBottomLine);
    priceLinesRef.current.set('cpr_bottom', cprBottomPriceLine);

    // TC (Top Central) - Light green
    const tcLine: PriceLineOptions = {
      price: cpr.tc,
      color: '#34D399',
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      axisLabelVisible: false,
      title: 'TC',
      lineVisible: true,
      axisLabelColor: '#cbd5f5',
      axisLabelTextColor: '#0f172a'
    };
    const tcPriceLine = candlestickSeries.createPriceLine(tcLine);
    priceLinesRef.current.set('tc', tcPriceLine);

    // BC (Bottom Central) - Light red
    const bcLine: PriceLineOptions = {
      price: cpr.bc,
      color: '#F87171',
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      axisLabelVisible: false,
      title: 'BC',
      lineVisible: true,
      axisLabelColor: '#cbd5f5',
      axisLabelTextColor: '#0f172a'
    };
    const bcPriceLine = candlestickSeries.createPriceLine(bcLine);
    priceLinesRef.current.set('bc', bcPriceLine);
  };

  return null; // This component doesn't render anything visible
};

export default CPRChartOverlay;

