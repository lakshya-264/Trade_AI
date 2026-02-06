/**
 * Chart Overlay Service
 * Draws Market Structure, Support/Resistance, and Supply/Demand zones
 * directly on Lightweight Charts
 */

import { IChartApi, ISeriesApi, LineStyle, SeriesMarker, Time } from 'lightweight-charts';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface BOSEvent {
  time: number;
  price: number;
  direction: 'bullish' | 'bearish';
  previousLevel: number;
}

export interface CHoCHEvent {
  time: number;
  price: number;
  direction: 'bullish' | 'bearish';
  previousLevel: number;
}

export interface MarketStructureData {
  bos_events?: BOSEvent[];
  choch_events?: CHoCHEvent[];
  current_structure?: 'bullish' | 'bearish' | 'neutral';
}

export interface SRLevel {
  price: number;
  type: 'support' | 'resistance';
  strength: 'strong' | 'medium' | 'weak';
  touches: number;
}

export interface SupportResistanceData {
  support_levels?: SRLevel[];
  resistance_levels?: SRLevel[];
}

export interface SupplyDemandZone {
  zone_low: number;
  zone_high: number;
  type: 'supply' | 'demand';
  status: 'fresh' | 'tested' | 'broken';
  strength: number;
  start_time?: number;
  end_time?: number;
}

export interface SupplyDemandData {
  demand_zones?: SupplyDemandZone[];
  supply_zones?: SupplyDemandZone[];
}

export interface Trendline {
  type: 'uptrend' | 'downtrend' | 'horizontal';
  start_index: number;
  start_price: number;
  end_index: number;
  end_price: number;
  slope: number;
  intercept: number;
  touches: number;
  strength?: 'weak' | 'moderate' | 'strong' | 'very_strong';
  is_broken?: boolean;
  start_time?: number;
  end_time?: number;
}

export interface TrendlineProjection {
  index: number;
  price: number;
  time?: Time;
  bars_ahead: number;
}

export interface TrendlineTargetZone {
  upper: number;
  lower: number;
  center: number;
  width: number;
  width_percentage: number;
}

export interface TrendlineKeyTargets {
  short_term: { bars: number; price: number; time?: Time };
  medium_term: { bars: number; price: number; time?: Time };
  long_term: { bars: number; price: number; time?: Time };
}

export interface TrendlineData {
  trendlines?: Trendline[];
  uptrends?: Trendline[];
  downtrends?: Trendline[];
  horizontal_lines?: Trendline[];
  manual_trendlines?: Trendline[];
  chartData?: Array<{ time: Time; open: number; high: number; low: number; close: number }>; // Optional chart data for time mapping
  projections?: {
    [key: string]: {
      trendline: any;
      projections: TrendlineProjection[];
      target_zone: TrendlineTargetZone;
      key_targets: TrendlineKeyTargets;
      future_bars: number;
    };
  };
}

export interface SwingPoint {
  index: number;
  time: number;
  price: number;
  type: 'high' | 'low';
  label?: 'HH' | 'HL' | 'LH' | 'LL';
  strength?: number;
}

export interface SwingPointData {
  swing_highs?: SwingPoint[];
  swing_lows?: SwingPoint[];
  swingPoints?: SwingPoint[];
}

export interface OverlaySettings {
  showBOS: boolean;
  showCHoCH: boolean;
  showSupport: boolean;
  showResistance: boolean;
  showDemandZones: boolean;
  showSupplyZones: boolean;
  showTrendlines?: boolean;
  showSwingPoints?: boolean;
  freshZonesOnly: boolean;
  strongZonesOnly: boolean;
  minStrength: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const COLORS = {
  // Market Structure
  BOS_BULLISH: '#22c55e',
  BOS_BEARISH: '#ef4444',
  CHOCH_BULLISH: '#a78bfa',
  CHOCH_BEARISH: '#7c3aed',
  
  // Support & Resistance
  SUPPORT: '#22c55e',
  RESISTANCE: '#ef4444',
  
  // Supply & Demand
  DEMAND_FRESH: 'rgba(34, 197, 94, 0.15)',
  DEMAND_TESTED: 'rgba(34, 197, 94, 0.08)',
  SUPPLY_FRESH: 'rgba(239, 68, 68, 0.15)',
  SUPPLY_TESTED: 'rgba(239, 68, 68, 0.08)',
  
  DEMAND_BORDER: '#22c55e',
  SUPPLY_BORDER: '#ef4444',
  
  // Trendlines
  UPTREND: '#22c55e',
  DOWNTREND: '#ef4444',
  HORIZONTAL: '#f59e0b',
  TRENDLINE_BROKEN: '#94a3b8',
  
  // Swing Points
  SWING_HIGH: '#ef4444',
  SWING_LOW: '#22c55e',
};

const LINE_STYLES = {
  STRONG: { width: 2 as const, style: LineStyle.Solid },
  MEDIUM: { width: 2 as const, style: LineStyle.Dashed },
  WEAK: { width: 1 as const, style: LineStyle.Dotted },
};

// ============================================================================
// CHART OVERLAY SERVICE
// ============================================================================

export interface OverlayMetadata {
  id: string;
  type: 'bos' | 'choch' | 'support' | 'resistance' | 'demand' | 'supply' | 'trendline' | 'swing';
  title: string;
  price?: number;
  priceRange?: { low: number; high: number };
  data: Record<string, any>;
}

export class ChartOverlayService {
  private chart: IChartApi | null = null;
  private series: ISeriesApi<'Candlestick'> | null = null;
  private priceLines: Map<string, any> = new Map();
  private lineSeries: Map<string, ISeriesApi<'Line'>> = new Map(); // Store line series for angled trendlines
  private projectionSeries: Map<string, ISeriesApi<'Line'>> = new Map(); // Store projection line series
  private markers: SeriesMarker<Time>[] = [];
  private overlayMetadata: Map<string, OverlayMetadata> = new Map();
  private settings: OverlaySettings = {
    showBOS: true,
    showCHoCH: true,
    showSupport: true,
    showResistance: true,
    showDemandZones: true,
    showSupplyZones: true,
    showTrendlines: true,
    showSwingPoints: true,
    freshZonesOnly: false,
    strongZonesOnly: false,
    minStrength: 0.3,
  };
  
  // Store last detected data for redrawing when settings change
  private lastMarketStructureData?: MarketStructureData;
  private lastSupportResistanceData?: SupportResistanceData;
  private lastSupplyDemandData?: SupplyDemandData;
  private lastTrendlineData?: any;
  private lastSwingPointData?: any;

  /**
   * Initialize the service with chart and series references
   */
  public initialize(chart: IChartApi, series: ISeriesApi<'Candlestick'>) {
    this.chart = chart;
    this.series = series;
    console.log('ChartOverlayService initialized');
  }

  /**
   * Update visibility settings
   */
  public updateSettings(newSettings: Partial<OverlaySettings>) {
    this.settings = { ...this.settings, ...newSettings };
    this.redraw();
  }

  /**
   * Get current settings
   */
  public getSettings(): OverlaySettings {
    return { ...this.settings };
  }

  /**
   * Clear all overlays from the chart
   */
  public clearAll() {
    this.clearMarkers();
    this.clearPriceLines();
    console.log('All overlays cleared');
  }

  /**
   * Clear all markers
   */
  private clearMarkers() {
    if (this.series) {
      this.series.setMarkers([]);
      this.markers = [];
    }
  }

  /**
   * Clear all price lines
   */
  private clearPriceLines() {
    this.priceLines.forEach((line) => {
      if (this.series) {
        this.series.removePriceLine(line);
      }
    });
    this.priceLines.clear();
    
    // Clear line series (for angled trendlines)
    this.lineSeries.forEach((lineSeries) => {
      if (this.chart) {
        this.chart.removeSeries(lineSeries);
      }
    });
    this.lineSeries.clear();
    
    // Clear projection series
    this.projectionSeries.forEach((lineSeries: ISeriesApi<'Line'>) => {
      if (this.chart) {
        this.chart.removeSeries(lineSeries);
      }
    });
    this.projectionSeries.clear();
  }

  /**
   * Redraw all overlays with current settings
   */
  private redraw() {
    // Clear existing overlays
    this.clearAll();
    
    // Re-draw with stored data using current settings
    if (this.lastMarketStructureData) {
      this.drawMarketStructure(this.lastMarketStructureData);
    }
    if (this.lastSupportResistanceData) {
      this.drawSupportResistance(this.lastSupportResistanceData);
    }
    if (this.lastSupplyDemandData) {
      this.drawSupplyDemand(this.lastSupplyDemandData);
    }
    if (this.lastTrendlineData) {
      this.drawTrendlines(this.lastTrendlineData);
    }
    if (this.lastSwingPointData) {
      this.drawSwingPoints(this.lastSwingPointData);
    }
  }

  // ==========================================================================
  // MARKET STRUCTURE (BOS/CHoCH)
  // ==========================================================================

  /**
   * Draw Market Structure markers (BOS and CHoCH)
   */
  public drawMarketStructure(data: MarketStructureData) {
    if (!this.series) {
      console.error('Series not initialized');
      return;
    }

    // Store data for redrawing
    this.lastMarketStructureData = data;

    const newMarkers: SeriesMarker<Time>[] = [];

    // Draw BOS events
    if (this.settings.showBOS && data.bos_events) {
      data.bos_events.forEach((event, index) => {
        const marker = this.createBOSMarker(event);
        if (marker) {
          newMarkers.push(marker);
          
          // Store metadata for interactivity
          this.storeOverlayMetadata({
            id: `bos-${index}-${event.time}`,
            type: 'bos',
            title: `Break of Structure (${event.direction})`,
            price: event.price,
            data: {
              direction: event.direction,
              previous_level: event.previousLevel,
              time: new Date(event.time * 1000).toLocaleString(),
            }
          });
        }
      });
    }

    // Draw CHoCH events
    if (this.settings.showCHoCH && data.choch_events) {
      data.choch_events.forEach((event, index) => {
        const marker = this.createCHoCHMarker(event);
        if (marker) {
          newMarkers.push(marker);
          
          // Store metadata for interactivity
          this.storeOverlayMetadata({
            id: `choch-${index}-${event.time}`,
            type: 'choch',
            title: `Change of Character (${event.direction})`,
            price: event.price,
            data: {
              direction: event.direction,
              previous_level: event.previousLevel,
              time: new Date(event.time * 1000).toLocaleString(),
            }
          });
        }
      });
    }

    // Combine with existing markers and apply
    this.markers = [...this.markers, ...newMarkers];
    this.series.setMarkers(this.markers);

    console.log(`Drew ${newMarkers.length} Market Structure markers`);
  }

  /**
   * Create a BOS marker
   */
  private createBOSMarker(event: BOSEvent): SeriesMarker<Time> | null {
    const isBullish = event.direction === 'bullish';
    
    return {
      time: event.time as Time,
      position: isBullish ? 'belowBar' : 'aboveBar',
      color: isBullish ? COLORS.BOS_BULLISH : COLORS.BOS_BEARISH,
      shape: isBullish ? 'arrowUp' : 'arrowDown',
      text: `BOS ${isBullish ? '↑' : '↓'}`,
      size: 1,
    };
  }

  /**
   * Create a CHoCH marker
   */
  private createCHoCHMarker(event: CHoCHEvent): SeriesMarker<Time> | null {
    const isBullish = event.direction === 'bullish';
    
    return {
      time: event.time as Time,
      position: isBullish ? 'belowBar' : 'aboveBar',
      color: isBullish ? COLORS.CHOCH_BULLISH : COLORS.CHOCH_BEARISH,
      shape: 'circle',
      text: `CHoCH ${isBullish ? '🔄↑' : '🔄↓'}`,
      size: 1,
    };
  }

  // ==========================================================================
  // SUPPORT & RESISTANCE LEVELS
  // ==========================================================================

  /**
   * Draw Support & Resistance horizontal lines
   */
  public drawSupportResistance(data: SupportResistanceData) {
    if (!this.series) {
      console.error('Series not initialized');
      return;
    }

    // Store data for redrawing
    this.lastSupportResistanceData = data;

    let linesDrawn = 0;

    // Draw support levels
    if (this.settings.showSupport && data.support_levels) {
      data.support_levels.forEach((level, index) => {
        if (this.shouldDrawLevel(level)) {
          this.drawSRLine(level, `support-${index}`);
          linesDrawn++;
        }
      });
    }

    // Draw resistance levels
    if (this.settings.showResistance && data.resistance_levels) {
      data.resistance_levels.forEach((level, index) => {
        if (this.shouldDrawLevel(level)) {
          this.drawSRLine(level, `resistance-${index}`);
          linesDrawn++;
        }
      });
    }

    console.log(`Drew ${linesDrawn} S&R lines`);
  }

  /**
   * Check if level should be drawn based on settings
   */
  private shouldDrawLevel(level: SRLevel): boolean {
    if (this.settings.strongZonesOnly) {
      // Safely get strength - handle both 'strength' and 'strength_label' fields
      const strengthValue = (level as any).strength_label || level.strength || 'weak';
      const strengthStr = String(strengthValue).toLowerCase();
      
      // Only show strong levels
      if (strengthStr === 'weak' || strengthStr === 'medium' || strengthStr === 'moderate') {
        return false;
      }
    }
    return true;
  }

  /**
   * Draw a single S&R line
   */
  private drawSRLine(level: SRLevel, id: string) {
    if (!this.series) return;

    const isSupport = level.type === 'support';
    
    // Safely get strength - handle both 'strength' and 'strength_label' fields
    // Also handle cases where strength might be undefined or not a string
    const strengthValue = (level as any).strength_label || level.strength || 'weak';
    const strengthStr = String(strengthValue).toLowerCase();
    
    // Map to LINE_STYLES keys (STRONG, MEDIUM, WEAK)
    let strengthKey: 'STRONG' | 'MEDIUM' | 'WEAK' = 'WEAK';
    if (strengthStr === 'strong' || strengthStr === 'very_strong') {
      strengthKey = 'STRONG';
    } else if (strengthStr === 'medium' || strengthStr === 'moderate') {
      strengthKey = 'MEDIUM';
    }
    
    const lineStyle = LINE_STYLES[strengthKey];

    try {
      const priceLine = this.series.createPriceLine({
        price: level.price,
        color: isSupport ? COLORS.SUPPORT : COLORS.RESISTANCE,
        lineWidth: lineStyle.width as 1 | 2 | 3 | 4,
        lineStyle: lineStyle.style,
        axisLabelVisible: true,
        title: `${isSupport ? 'S' : 'R'} ₹${level.price.toFixed(2)} (${level.touches}x)`,
      });

      this.priceLines.set(id, priceLine);
      
      // Store metadata for interactivity
      this.storeOverlayMetadata({
        id,
        type: isSupport ? 'support' : 'resistance',
        title: `${isSupport ? 'Support' : 'Resistance'} Level`,
        price: level.price,
        data: {
          type: level.type,
          strength: level.strength,
          touches: level.touches,
        }
      });
    } catch (error) {
      console.error('Error drawing S&R line:', error);
    }
  }

  // ==========================================================================
  // SUPPLY & DEMAND ZONES
  // ==========================================================================

  /**
   * Draw Supply & Demand zone rectangles
   * Note: Lightweight Charts doesn't have native rectangle support
   * We'll use price lines to simulate zones
   */
  public drawSupplyDemand(data: SupplyDemandData) {
    if (!this.series) {
      console.error('Series not initialized');
      return;
    }

    // Store data for redrawing
    this.lastSupplyDemandData = data;

    let zonesDrawn = 0;

    // Draw demand zones
    if (this.settings.showDemandZones && data.demand_zones) {
      data.demand_zones.forEach((zone, index) => {
        if (this.shouldDrawZone(zone)) {
          this.drawZone(zone, `demand-${index}`);
          zonesDrawn++;
        }
      });
    }

    // Draw supply zones
    if (this.settings.showSupplyZones && data.supply_zones) {
      data.supply_zones.forEach((zone, index) => {
        if (this.shouldDrawZone(zone)) {
          this.drawZone(zone, `supply-${index}`);
          zonesDrawn++;
        }
      });
    }

    console.log(`Drew ${zonesDrawn} Supply/Demand zones`);
  }

  /**
   * Check if zone should be drawn based on settings
   */
  private shouldDrawZone(zone: SupplyDemandZone): boolean {
    // Filter by fresh only
    if (this.settings.freshZonesOnly && zone.status !== 'fresh') {
      return false;
    }

    // Filter by minimum strength
    if (zone.strength < this.settings.minStrength) {
      return false;
    }

    // Don't draw broken zones
    if (zone.status === 'broken') {
      return false;
    }

    return true;
  }

  /**
   * Draw a supply/demand zone using price lines
   * (Top and bottom border + label)
   */
  private drawZone(zone: SupplyDemandZone, id: string) {
    if (!this.series) return;

    const isDemand = zone.type === 'demand';
    const isFresh = zone.status === 'fresh';
    const color = isDemand ? COLORS.DEMAND_BORDER : COLORS.SUPPLY_BORDER;
    const lineStyle = isFresh ? LineStyle.Solid : LineStyle.Dashed;

    try {
      // Draw top border
      const topLine = this.series.createPriceLine({
        price: zone.zone_high,
        color: color,
        lineWidth: (isFresh ? 2 : 1) as 1 | 2 | 3 | 4,
        lineStyle: lineStyle,
        axisLabelVisible: false,
        title: ``,
      });

      // Draw bottom border with label
      const bottomLine = this.series.createPriceLine({
        price: zone.zone_low,
        color: color,
        lineWidth: (isFresh ? 2 : 1) as 1 | 2 | 3 | 4,
        lineStyle: lineStyle,
        axisLabelVisible: true,
        title: `${isDemand ? 'D' : 'S'} ₹${zone.zone_low.toFixed(2)}-${zone.zone_high.toFixed(2)} ${isFresh ? '⭐' : ''}`,
      });

      this.priceLines.set(`${id}-top`, topLine);
      this.priceLines.set(`${id}-bottom`, bottomLine);
      
      // Store metadata for interactivity
      this.storeOverlayMetadata({
        id,
        type: isDemand ? 'demand' : 'supply',
        title: `${isDemand ? 'Demand' : 'Supply'} Zone`,
        priceRange: { low: zone.zone_low, high: zone.zone_high },
        data: {
          type: zone.type,
          status: zone.status,
          strength: zone.strength,
          fresh: zone.status === 'fresh',
        }
      });
    } catch (error) {
      console.error('Error drawing zone:', error);
    }
  }

  // ==========================================================================
  // TRENDLINE DRAWING
  // ==========================================================================

  /**
   * Map index to time value from chart data
   */
  private mapIndexToTime(index: number, chartData?: Array<{ time: Time }>): Time | null {
    if (!chartData || chartData.length === 0) {
      return null;
    }
    
    // If index is within bounds, return the time at that index
    if (index >= 0 && index < chartData.length) {
      return chartData[index].time;
    }
    
    // If index is out of bounds, try to extrapolate
    if (index < 0) {
      // Before start - extrapolate backwards
      const firstTime = chartData[0].time as number;
      const timeDiff = (chartData[1]?.time as number) - firstTime;
      return (firstTime + (index * timeDiff)) as Time;
    } else {
      // After end - extrapolate forwards
      const lastTime = chartData[chartData.length - 1].time as number;
      const timeDiff = lastTime - (chartData[chartData.length - 2]?.time as number);
      return (lastTime + ((index - chartData.length + 1) * timeDiff)) as Time;
    }
  }

  /**
   * Draw trendlines on the chart
   * Now supports both angled trendlines (using LineSeries) and horizontal lines (using PriceLine)
   */
  public drawTrendlines(data: TrendlineData) {
    if (!this.series || !this.chart) {
      return;
    }

    // Store data for redrawing
    this.lastTrendlineData = data;

    if (!this.settings.showTrendlines) {
      return;
    }

    const chartData = data.chartData || [];

    // Combine all trendlines (including manual)
    const allTrendlines = [
      ...(data.trendlines || []),
      ...(data.uptrends || []),
      ...(data.downtrends || []),
      ...(data.horizontal_lines || []),
      ...(data.manual_trendlines || []).map((mt: any) => ({
        ...mt,
        type: mt.type || 'manual',
        touches: 2, // Manual trendlines have 2 points
        strength: 'moderate',
        is_manual: true
      }))
    ];

    allTrendlines.forEach((trendline, index) => {
      try {
        const id = `trendline-${index}-${trendline.type}`;
        
        // Determine color based on type and broken status
        let color = COLORS.HORIZONTAL;
        if (trendline.is_broken) {
          color = COLORS.TRENDLINE_BROKEN;
        } else if (trendline.type === 'uptrend') {
          color = COLORS.UPTREND;
        } else if (trendline.type === 'downtrend') {
          color = COLORS.DOWNTREND;
        }

        // Determine line style based on strength
        let lineWidth: 1 | 2 | 3 | 4 = 2;
        let lineStyle = LineStyle.Solid;
        
        if (trendline.strength === 'very_strong' || trendline.strength === 'strong') {
          lineWidth = 3;
          lineStyle = LineStyle.Solid;
        } else if (trendline.strength === 'moderate') {
          lineWidth = 2;
          lineStyle = LineStyle.Solid;
        } else if (trendline.strength === 'weak') {
          lineWidth = 1;
          lineStyle = LineStyle.Dashed;
        }

        // For horizontal lines, use PriceLine (existing behavior)
        if (trendline.type === 'horizontal') {
          const priceLine = this.series!.createPriceLine({
            price: trendline.start_price, // Use start_price for horizontal
            color: color,
            lineWidth: lineWidth,
            lineStyle: lineStyle,
            axisLabelVisible: true,
            title: `HORIZONTAL (${trendline.touches}x)`,
          });
          this.priceLines.set(id, priceLine);
        } 
        // For angled trendlines (uptrend/downtrend), use LineSeries
        else {
          // Map indices to time values
          const startTime = trendline.start_time 
            ? (trendline.start_time as Time)
            : this.mapIndexToTime(trendline.start_index, chartData);
          
          const endTime = trendline.end_time 
            ? (trendline.end_time as Time)
            : this.mapIndexToTime(trendline.end_index, chartData);

          // If we have valid time values, draw angled line
          if (startTime && endTime && this.chart) {
            // Create line series for angled trendline
            const lineSeries = this.chart.addLineSeries({
              color: color,
              lineWidth: lineWidth,
              lineStyle: lineStyle,
              priceLineVisible: false,
              lastValueVisible: false,
              title: `${trendline.type.toUpperCase()} (${trendline.touches}x)`,
            });

            // Set data points for the trendline
            lineSeries.setData([
              { time: startTime, value: trendline.start_price },
              { time: endTime, value: trendline.end_price }
            ]);

            // Store reference for cleanup
            this.lineSeries.set(id, lineSeries);
          } else {
            // Fallback: If time mapping fails, use horizontal price line
            console.warn(`Could not map trendline ${id} to time values, using horizontal line fallback`);
            const priceLine = this.series!.createPriceLine({
              price: trendline.end_price,
              color: color,
              lineWidth: lineWidth,
              lineStyle: lineStyle,
              axisLabelVisible: true,
              title: `${trendline.type.toUpperCase()} (${trendline.touches}x)`,
            });
            this.priceLines.set(id, priceLine);
          }
        }

        // Store metadata
        this.storeOverlayMetadata({
          id,
          type: 'trendline',
          title: `${trendline.type.toUpperCase()} Trendline`,
          price: trendline.end_price,
          data: {
            type: trendline.type,
            strength: trendline.strength,
            touches: trendline.touches,
            is_broken: trendline.is_broken,
            start_price: trendline.start_price,
            end_price: trendline.end_price,
          }
        });
      } catch (error) {
        console.error('Error drawing trendline:', error);
      }
    });

    console.log(`Drew ${allTrendlines.length} trendlines (${this.lineSeries.size} angled, ${this.priceLines.size} horizontal)`);
    
    // Draw projections if available
    if (data.projections) {
      this.drawTrendlineProjections(data.projections, chartData);
    }
  }
  
  /**
   * Draw projected trendlines into the future
   */
  private drawTrendlineProjections(
    projections: TrendlineData['projections'],
    chartData: Array<{ time: Time }>
  ) {
    if (!this.chart || !projections) {
      return;
    }

    Object.entries(projections).forEach(([key, projectionData]) => {
      try {
        const trendline = projectionData.trendline;
        const projections = projectionData.projections;
        const targetZone = projectionData.target_zone;
        
        if (!projections || projections.length === 0) {
          return;
        }

        // Get the end time of the original trendline
        const endTime = trendline.end_time 
          ? (trendline.end_time as Time)
          : (chartData.length > 0 ? chartData[chartData.length - 1].time : null);
        
        if (!endTime) {
          return;
        }

        // Determine color based on trendline type
        let color = COLORS.HORIZONTAL;
        if (trendline.type === 'uptrend') {
          color = COLORS.UPTREND;
        } else if (trendline.type === 'downtrend') {
          color = COLORS.DOWNTREND;
        }

        // Create projected line series (dashed to distinguish from actual trendline)
        if (!this.chart) return;
        
        const projectionSeries = this.chart.addLineSeries({
          color: color,
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          priceLineVisible: false,
          lastValueVisible: false,
          title: `Projected ${trendline.type}`,
        });

        // Build projection data points
        const projectionPoints: Array<{ time: Time; value: number }> = [];
        
        // Start from end of original trendline
        projectionPoints.push({
          time: endTime,
          value: trendline.current_price || trendline.end_price
        });

        // Add projected points
        projections.forEach((proj) => {
          if (proj.time) {
            projectionPoints.push({
              time: proj.time,
              value: proj.price
            });
          }
        });

        if (projectionPoints.length >= 2) {
          projectionSeries.setData(projectionPoints);
          this.projectionSeries.set(`projection-${key}`, projectionSeries);
        }

        // Draw target zone (upper and lower bounds)
        if (targetZone && this.chart) {
          // Upper bound
          const upperSeries = this.chart.addLineSeries({
            color: color,
            lineWidth: 1,
            lineStyle: LineStyle.Dotted,
            priceLineVisible: false,
            lastValueVisible: false,
            title: `Target Zone Upper`,
          });

          // Lower bound
          const lowerSeries = this.chart.addLineSeries({
            color: color,
            lineWidth: 1,
            lineStyle: LineStyle.Dotted,
            priceLineVisible: false,
            lastValueVisible: false,
            title: `Target Zone Lower`,
          });

          // Create zone lines
          const zonePoints = projectionPoints.map(p => ({
            time: p.time,
            value: p.value
          }));

          if (zonePoints.length >= 2) {
            upperSeries.setData(zonePoints.map(p => ({
              time: p.time,
              value: targetZone.upper
            })));
            
            lowerSeries.setData(zonePoints.map(p => ({
              time: p.time,
              value: targetZone.lower
            })));

            this.projectionSeries.set(`projection-${key}-upper`, upperSeries);
            this.projectionSeries.set(`projection-${key}-lower`, lowerSeries);
          }
        }
      } catch (error) {
        console.error(`Error drawing projection ${key}:`, error);
      }
    });

    console.log(`Drew ${Object.keys(projections).length} trendline projections`);
  }

  // ==========================================================================
  // SWING POINT DRAWING
  // ==========================================================================

  /**
   * Draw swing points on the chart
   */
  public drawSwingPoints(data: SwingPointData) {
    if (!this.series) {
      return;
    }

    // Store data for redrawing
    this.lastSwingPointData = data;

    if (!this.settings.showSwingPoints) {
      return;
    }

    const newMarkers: SeriesMarker<Time>[] = [];

    // Combine all swing points
    const allSwingPoints = [
      ...(data.swingPoints || []),
      ...(data.swing_highs || []).map(p => ({ ...p, type: 'high' as const })),
      ...(data.swing_lows || []).map(p => ({ ...p, type: 'low' as const }))
    ];

    allSwingPoints.forEach((point) => {
      try {
        const isHigh = point.type === 'high';
        
        const marker: SeriesMarker<Time> = {
          time: point.time as Time,
          position: isHigh ? 'aboveBar' : 'belowBar',
          color: isHigh ? COLORS.SWING_HIGH : COLORS.SWING_LOW,
          shape: isHigh ? 'arrowDown' : 'arrowUp',
          text: point.label || (isHigh ? 'H' : 'L'),
          size: point.strength ? Math.min(3, Math.max(1, point.strength)) : 1,
        };

        newMarkers.push(marker);
      } catch (error) {
        console.error('Error creating swing point marker:', error);
      }
    });

    // Update markers
    if (newMarkers.length > 0) {
      const existingMarkers = this.series.markers();
      this.series.setMarkers([...existingMarkers, ...newMarkers]);
      this.markers.push(...newMarkers);
    }
  }

  // ==========================================================================
  // COMBINED DRAWING
  // ==========================================================================

  /**
   * Draw all overlays at once
   */
  public drawAll(
    marketStructure: MarketStructureData,
    supportResistance: SupportResistanceData,
    supplyDemand: SupplyDemandData,
    trendlines?: TrendlineData,
    swingPoints?: SwingPointData
  ) {
    this.clearAll();
    this.drawMarketStructure(marketStructure);
    this.drawSupportResistance(supportResistance);
    this.drawSupplyDemand(supplyDemand);
    if (trendlines) this.drawTrendlines(trendlines);
    if (swingPoints) this.drawSwingPoints(swingPoints);
  }

  // ==========================================================================
  // UTILITY METHODS
  // ==========================================================================

  /**
   * Remove specific overlay by ID
   */
  public removeOverlay(id: string) {
    const priceLine = this.priceLines.get(id);
    if (priceLine && this.series) {
      this.series.removePriceLine(priceLine);
      this.priceLines.delete(id);
    }
  }

  /**
   * Get overlay statistics
   */
  public getStats() {
    return {
      markers: this.markers.length,
      priceLines: this.priceLines.size,
      overlays: this.overlayMetadata.size,
      settings: this.settings,
    };
  }

  // ==========================================================================
  // INTERACTIVE FEATURES
  // ==========================================================================

  /**
   * Store overlay metadata for interactive features
   */
  private storeOverlayMetadata(metadata: OverlayMetadata) {
    this.overlayMetadata.set(metadata.id, metadata);
  }

  /**
   * Get all overlays metadata
   */
  public getAllOverlays(): OverlayMetadata[] {
    return Array.from(this.overlayMetadata.values());
  }

  /**
   * Get overlay at specific price level
   */
  public getOverlayAtPrice(price: number, tolerance: number = 0.5): OverlayMetadata | null {
    const overlays = Array.from(this.overlayMetadata.values());
    
    for (const overlay of overlays) {
      // Check single price overlays
      if (overlay.price) {
        const diff = Math.abs(overlay.price - price);
        const percentDiff = (diff / price) * 100;
        if (percentDiff <= tolerance) {
          return overlay;
        }
      }
      
      // Check price range overlays
      if (overlay.priceRange) {
        if (price >= overlay.priceRange.low && price <= overlay.priceRange.high) {
          return overlay;
        }
      }
    }
    
    return null;
  }

  /**
   * Get overlays by type
   */
  public getOverlaysByType(type: OverlayMetadata['type']): OverlayMetadata[] {
    return Array.from(this.overlayMetadata.values()).filter(o => o.type === type);
  }

  /**
   * Clear overlay metadata
   */
  public clearOverlayMetadata() {
    this.overlayMetadata.clear();
  }

  /**
   * Cleanup
   */
  public destroy() {
    this.clearAll();
    this.clearOverlayMetadata();
    this.chart = null;
    this.series = null;
    console.log('ChartOverlayService destroyed');
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const chartOverlayService = new ChartOverlayService();

export default chartOverlayService;

