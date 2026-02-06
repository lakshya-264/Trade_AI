/**
 * Chart Synchronization Service
 * Manages crosshair synchronization across multiple charts
 */

import { IChartApi, Time, MouseEventParams } from 'lightweight-charts';

export type SyncCallback = (time: Time | null, price?: number) => void;

class ChartSyncService {
  private charts: Map<string, IChartApi> = new Map();
  private callbacks: Map<string, SyncCallback> = new Map();
  private syncEnabled: boolean = true;
  private activeSyncSource: string | null = null;

  /**
   * Register a chart for synchronization
   */
  registerChart(id: string, chart: IChartApi, callback?: SyncCallback): void {
    this.charts.set(id, chart);
    if (callback) {
      this.callbacks.set(id, callback);
    }

    // Subscribe to crosshair move events
    chart.subscribeCrosshairMove((param) => {
      if (this.syncEnabled && this.activeSyncSource !== id) {
        this.handleCrosshairMove(id, param);
      }
    });

    console.log(`[ChartSync] Registered chart: ${id}`);
  }

  /**
   * Unregister a chart from synchronization
   */
  unregisterChart(id: string): void {
    this.charts.delete(id);
    this.callbacks.delete(id);
    console.log(`[ChartSync] Unregistered chart: ${id}`);
  }

  /**
   * Handle crosshair move event from source chart
   */
  private handleCrosshairMove(sourceId: string, param: MouseEventParams): void {
    if (!param.time) {
      // No time, clear crosshairs on all charts
      this.clearAllCrosshairs(sourceId);
      return;
    }

    const time = param.time;
    const price = param.seriesData.size > 0 
      ? Array.from(param.seriesData.values())[0] 
      : undefined;

    // Sync to other charts
    this.syncCrosshairToTime(sourceId, time, price);
  }

  /**
   * Sync crosshair to specific time on all charts except source
   */
  syncCrosshairToTime(sourceId: string, time: Time, price?: any): void {
    if (!this.syncEnabled) return;

    this.activeSyncSource = sourceId;

    this.charts.forEach((chart, chartId) => {
      if (chartId !== sourceId) {
        try {
          // Just call the callback to update tooltip
          // Lightweight Charts doesn't support programmatic crosshair positioning
          const callback = this.callbacks.get(chartId);
          if (callback) {
            callback(time, price?.value);
          }
        } catch (error) {
          console.warn(`[ChartSync] Error syncing crosshair to ${chartId}:`, error);
        }
      }
    });

    this.activeSyncSource = null;
  }

  /**
   * Clear crosshairs on all charts except source
   */
  clearAllCrosshairs(sourceId: string): void {
    if (!this.syncEnabled) return;

    this.charts.forEach((chart, chartId) => {
      if (chartId !== sourceId) {
        try {
          // Call registered callback with null to hide tooltips
          const callback = this.callbacks.get(chartId);
          if (callback) {
            callback(null);
          }
        } catch (error) {
          console.warn(`[ChartSync] Error clearing crosshair on ${chartId}:`, error);
        }
      }
    });
  }

  /**
   * Enable or disable synchronization
   */
  setSyncEnabled(enabled: boolean): void {
    this.syncEnabled = enabled;
    console.log(`[ChartSync] Sync ${enabled ? 'enabled' : 'disabled'}`);

    if (!enabled) {
      // Clear all tooltips when disabling
      this.callbacks.forEach((callback) => {
        try {
          callback(null);
        } catch (error) {
          // Ignore
        }
      });
    }
  }

  /**
   * Check if sync is enabled
   */
  isSyncEnabled(): boolean {
    return this.syncEnabled;
  }

  /**
   * Get all registered chart IDs
   */
  getRegisteredCharts(): string[] {
    return Array.from(this.charts.keys());
  }

  /**
   * Clear all registered charts
   */
  clearAll(): void {
    this.charts.clear();
    this.callbacks.clear();
    this.activeSyncSource = null;
    console.log('[ChartSync] Cleared all charts');
  }
}

// Export singleton instance
export const chartSyncService = new ChartSyncService();

export default chartSyncService;

