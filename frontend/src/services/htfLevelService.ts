/**
 * Higher Timeframe (HTF) Level Overlay Service
 * Draws HTF levels (S&R, S&D zones, BOS/CHoCH) on Lower Timeframe charts
 */

import { IChartApi, ISeriesApi, Time, LineStyle, SeriesMarker } from 'lightweight-charts';

export interface HTFLevel {
  type: 'support' | 'resistance' | 'demand' | 'supply' | 'bos' | 'choch';
  timeframe: string;
  price?: number;
  priceFrom?: number;
  priceTo?: number;
  time?: string;
  touches?: number;
  strength?: string;
  direction?: string;
  label?: string;
}

export interface HTFLevelDrawOptions {
  showLabels?: boolean;
  opacity?: number;
  lineWidth?: number;
  timeframeColors?: Record<string, string>;
}

const DEFAULT_TF_COLORS: Record<string, string> = {
  '1D': '#2962FF',
  '4H': '#00897B',
  '1H': '#F57C00',
  '15m': '#E91E63',
  '5m': '#9C27B0',
  '1W': '#1976D2',
  '1M': '#0D47A1',
};

const DEFAULT_OPTIONS: HTFLevelDrawOptions = {
  showLabels: true,
  opacity: 0.5,
  lineWidth: 2,
  timeframeColors: DEFAULT_TF_COLORS,
};

class HTFLevelService {
  private drawnLevels: Map<string, any[]> = new Map();

  /**
   * Draw HTF levels on a chart
   */
  drawHTFLevels(
    chart: IChartApi,
    candleSeries: ISeriesApi<'Candlestick'>,
    levels: HTFLevel[],
    options: HTFLevelDrawOptions = {}
  ): void {
    const opts = { ...DEFAULT_OPTIONS, ...options };

    // Clear existing HTF levels for this chart
    this.clearHTFLevels(chart);

    const drawnItems: any[] = [];

    levels.forEach((level) => {
      try {
        if (level.type === 'support' || level.type === 'resistance') {
          const line = this.drawHTFLine(chart, candleSeries, level, opts);
          if (line) drawnItems.push(line);
        } else if (level.type === 'demand' || level.type === 'supply') {
          const zone = this.drawHTFZone(chart, candleSeries, level, opts);
          if (zone) drawnItems.push(zone);
        } else if (level.type === 'bos' || level.type === 'choch') {
          const marker = this.drawHTFMarker(candleSeries, level, opts);
          if (marker) drawnItems.push(marker);
        }
      } catch (error) {
        console.warn(`[HTFLevel] Error drawing level:`, level, error);
      }
    });

    // Store drawn items for later cleanup
    const chartId = (chart as any).__htf_id__ || Math.random().toString();
    (chart as any).__htf_id__ = chartId;
    this.drawnLevels.set(chartId, drawnItems);

    console.log(`[HTFLevel] Drew ${drawnItems.length} HTF levels`);
  }

  /**
   * Draw HTF Support/Resistance line
   */
  private drawHTFLine(
    chart: IChartApi,
    candleSeries: ISeriesApi<'Candlestick'>,
    level: HTFLevel,
    options: HTFLevelDrawOptions
  ): ISeriesApi<'Line'> | null {
    if (!level.price) return null;

    const color = this.getTimeframeColor(level.timeframe, options.timeframeColors);
    const isSupport = level.type === 'support';

    try {
      const lineSeries = chart.addLineSeries({
        color: color,
        lineWidth: options.lineWidth as 1 | 2 | 3 | 4,
        lineStyle: LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
        title: options.showLabels
          ? `[${level.timeframe}] ${isSupport ? 'S' : 'R'} ₹${level.price.toFixed(2)}`
          : undefined,
      });

      // Draw horizontal line by setting data points at start and end
      const timeScale = chart.timeScale();
      const visibleRange = timeScale.getVisibleRange();
      
      if (visibleRange) {
        lineSeries.setData([
          { time: visibleRange.from as Time, value: level.price },
          { time: visibleRange.to as Time, value: level.price },
        ]);
      }

      return lineSeries;
    } catch (error) {
      console.error('[HTFLevel] Error creating line series:', error);
      return null;
    }
  }

  /**
   * Draw HTF Supply/Demand zone
   */
  private drawHTFZone(
    chart: IChartApi,
    candleSeries: ISeriesApi<'Candlestick'>,
    level: HTFLevel,
    options: HTFLevelDrawOptions
  ): any | null {
    if (!level.priceFrom || !level.priceTo) return null;

    const color = this.getTimeframeColor(level.timeframe, options.timeframeColors);
    const isDemand = level.type === 'demand';

    try {
      // Create two line series for top and bottom of zone
      const topLine = chart.addLineSeries({
        color: color,
        lineWidth: 1,
        lineStyle: LineStyle.Solid,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });

      const bottomLine = chart.addLineSeries({
        color: color,
        lineWidth: 1,
        lineStyle: LineStyle.Solid,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });

      const timeScale = chart.timeScale();
      const visibleRange = timeScale.getVisibleRange();

      if (visibleRange) {
        topLine.setData([
          { time: visibleRange.from as Time, value: level.priceTo },
          { time: visibleRange.to as Time, value: level.priceTo },
        ]);

        bottomLine.setData([
          { time: visibleRange.from as Time, value: level.priceFrom },
          { time: visibleRange.to as Time, value: level.priceFrom },
        ]);
      }

      return { topLine, bottomLine, type: 'zone' };
    } catch (error) {
      console.error('[HTFLevel] Error creating zone:', error);
      return null;
    }
  }

  /**
   * Draw HTF BOS/CHoCH marker
   */
  private drawHTFMarker(
    candleSeries: ISeriesApi<'Candlestick'>,
    level: HTFLevel,
    options: HTFLevelDrawOptions
  ): SeriesMarker<Time> | null {
    if (!level.time || !level.price) return null;

    const color = this.getTimeframeColor(level.timeframe, options.timeframeColors);
    const isBullish = level.direction === 'bullish';
    const isBOS = level.type === 'bos';

    try {
      const marker: SeriesMarker<Time> = {
        time: level.time as Time,
        position: isBullish ? 'belowBar' : 'aboveBar',
        color: color,
        shape: isBullish ? 'arrowUp' : 'arrowDown',
        text: options.showLabels
          ? `[${level.timeframe}] ${isBOS ? 'BOS' : 'CHoCH'} ${isBullish ? '↑' : '↓'}`
          : undefined,
        size: 0.8,
      };

      // Add marker to series
      const existingMarkers = (candleSeries as any).markers() || [];
      candleSeries.setMarkers([...existingMarkers, marker]);

      return marker;
    } catch (error) {
      console.error('[HTFLevel] Error creating marker:', error);
      return null;
    }
  }

  /**
   * Get color for a specific timeframe
   */
  private getTimeframeColor(
    timeframe: string,
    timeframeColors?: Record<string, string>
  ): string {
    const colors = timeframeColors || DEFAULT_TF_COLORS;
    return colors[timeframe] || '#999999';
  }

  /**
   * Clear HTF levels from a chart
   */
  clearHTFLevels(chart: IChartApi): void {
    const chartId = (chart as any).__htf_id__;
    if (!chartId) return;

    const drawnItems = this.drawnLevels.get(chartId);
    if (!drawnItems) return;

    drawnItems.forEach((item) => {
      try {
        if (item.type === 'zone') {
          // Remove zone lines
          chart.removeSeries(item.topLine);
          chart.removeSeries(item.bottomLine);
        } else if (item.setData) {
          // Remove series
          chart.removeSeries(item);
        }
      } catch (error) {
        // Ignore errors during cleanup
      }
    });

    this.drawnLevels.delete(chartId);
    console.log(`[HTFLevel] Cleared HTF levels for chart ${chartId}`);
  }

  /**
   * Clear all HTF levels from all charts
   */
  clearAll(): void {
    this.drawnLevels.clear();
    console.log('[HTFLevel] Cleared all HTF levels');
  }

  /**
   * Extract HTF levels from multi-timeframe analysis
   */
  extractHTFLevels(
    analyses: Record<string, any>,
    currentTimeframe: string,
    includeTimeframes: string[]
  ): HTFLevel[] {
    const levels: HTFLevel[] = [];

    includeTimeframes.forEach((tf) => {
      // Skip if this is the current timeframe (not HTF)
      if (tf === currentTimeframe) return;

      const analysis = analyses[tf];
      if (!analysis) return;

      // Extract S&R levels
      if (analysis.sr) {
        const supportLevels = analysis.sr.support_levels || [];
        const resistanceLevels = analysis.sr.resistance_levels || [];

        supportLevels.forEach((level: any) => {
          levels.push({
            type: 'support',
            timeframe: tf,
            price: level.price,
            touches: level.touches,
            strength: level.strength,
            label: `[${tf}] S ₹${level.price.toFixed(2)}`,
          });
        });

        resistanceLevels.forEach((level: any) => {
          levels.push({
            type: 'resistance',
            timeframe: tf,
            price: level.price,
            touches: level.touches,
            strength: level.strength,
            label: `[${tf}] R ₹${level.price.toFixed(2)}`,
          });
        });
      }

      // Extract S&D zones
      if (analysis.sd) {
        const demandZones = analysis.sd.demand_zones || [];
        const supplyZones = analysis.sd.supply_zones || [];

        demandZones.forEach((zone: any) => {
          levels.push({
            type: 'demand',
            timeframe: tf,
            priceFrom: zone.bottom,
            priceTo: zone.top,
            strength: zone.strength,
            label: `[${tf}] Demand ₹${zone.bottom.toFixed(2)}-${zone.top.toFixed(2)}`,
          });
        });

        supplyZones.forEach((zone: any) => {
          levels.push({
            type: 'supply',
            timeframe: tf,
            priceFrom: zone.bottom,
            priceTo: zone.top,
            strength: zone.strength,
            label: `[${tf}] Supply ₹${zone.bottom.toFixed(2)}-${zone.top.toFixed(2)}`,
          });
        });
      }

      // Extract BOS/CHoCH
      if (analysis.structure && analysis.structure.structure) {
        const bosEvents = analysis.structure.structure.bos_events || [];
        const chochEvents = analysis.structure.structure.choch_events || [];

        bosEvents.forEach((event: any) => {
          levels.push({
            type: 'bos',
            timeframe: tf,
            time: event.time,
            price: event.price,
            direction: event.direction,
            label: `[${tf}] BOS ${event.direction}`,
          });
        });

        chochEvents.forEach((event: any) => {
          levels.push({
            type: 'choch',
            timeframe: tf,
            time: event.time,
            price: event.price,
            direction: event.direction,
            label: `[${tf}] CHoCH ${event.direction}`,
          });
        });
      }
    });

    console.log(`[HTFLevel] Extracted ${levels.length} HTF levels from ${includeTimeframes.length} timeframes`);
    return levels;
  }
}

// Export singleton instance
export const htfLevelService = new HTFLevelService();

export default htfLevelService;

