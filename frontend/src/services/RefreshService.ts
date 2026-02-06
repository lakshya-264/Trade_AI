/**
 * Centralized Refresh Service
 * Manages all auto-refresh intervals across the application to prevent duplicate API calls
 */

class RefreshService {
  private static instance: RefreshService;
  private intervals: Map<string, NodeJS.Timeout> = new Map();
  private callbacks: Map<string, () => void> = new Map();
  private globalEnabled: boolean = true;
  private defaultInterval: number = 30000; // 30 seconds

  private constructor() {
    // Private constructor for singleton
  }

  public static getInstance(): RefreshService {
    if (!RefreshService.instance) {
      RefreshService.instance = new RefreshService();
    }
    return RefreshService.instance;
  }

  /**
   * Register a refresh callback with a unique ID
   * @param id Unique identifier for this refresh task
   * @param callback Function to call on refresh
   * @param interval Refresh interval in milliseconds (default: 30s)
   * @param immediate Whether to call immediately on registration
   */
  public register(
    id: string,
    callback: () => void,
    interval: number = this.defaultInterval,
    immediate: boolean = false
  ): void {
    // Clear existing interval if any
    this.clear(id);

    // Store callback
    this.callbacks.set(id, callback);

    // Call immediately if requested
    if (immediate && this.globalEnabled) {
      try {
        callback();
      } catch (error) {
        console.error(`Error in immediate refresh callback for ${id}:`, error);
      }
    }

    // Set up interval if globally enabled
    if (this.globalEnabled) {
      const intervalId = setInterval(() => {
        if (this.globalEnabled) {
          try {
            const cb = this.callbacks.get(id);
            if (cb) {
              cb();
            }
          } catch (error) {
            console.error(`Error in refresh callback for ${id}:`, error);
          }
        }
      }, interval);

      this.intervals.set(id, intervalId);
    }
  }

  /**
   * Clear a specific refresh interval
   */
  public clear(id: string): void {
    const interval = this.intervals.get(id);
    if (interval) {
      clearInterval(interval);
      this.intervals.delete(id);
    }
    this.callbacks.delete(id);
  }

  /**
   * Clear all refresh intervals
   */
  public clearAll(): void {
    this.intervals.forEach((interval) => clearInterval(interval));
    this.intervals.clear();
    this.callbacks.clear();
  }

  /**
   * Enable/disable all refresh intervals globally
   */
  public setGlobalEnabled(enabled: boolean): void {
    this.globalEnabled = enabled;

    if (!enabled) {
      // Pause all intervals
      this.intervals.forEach((interval) => clearInterval(interval));
      this.intervals.clear();
    } else {
      // Restart all intervals
      const callbacks = Array.from(this.callbacks.entries());
      callbacks.forEach(([id, callback]) => {
        // Re-register with default interval
        this.register(id, callback, this.defaultInterval, false);
      });
    }
  }

  /**
   * Get global enabled state
   */
  public isGlobalEnabled(): boolean {
    return this.globalEnabled;
  }

  /**
   * Set default interval for new registrations
   */
  public setDefaultInterval(interval: number): void {
    this.defaultInterval = interval;
  }

  /**
   * Get all registered refresh IDs
   */
  public getRegisteredIds(): string[] {
    return Array.from(this.intervals.keys());
  }

  /**
   * Manually trigger a refresh for a specific ID
   */
  public trigger(id: string): void {
    const callback = this.callbacks.get(id);
    if (callback) {
      try {
        callback();
      } catch (error) {
        console.error(`Error triggering refresh for ${id}:`, error);
      }
    }
  }

  /**
   * Update interval for an existing registration
   */
  public updateInterval(id: string, newInterval: number): void {
    const callback = this.callbacks.get(id);
    if (callback) {
      this.clear(id);
      this.register(id, callback, newInterval, false);
    }
  }
}

// Export singleton instance
export const refreshService = RefreshService.getInstance();
export default refreshService;

