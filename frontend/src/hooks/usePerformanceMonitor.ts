import { useState, useEffect, useCallback } from 'react';

interface PerformanceMetrics {
  loadTime: number;
  renderTime: number;
  memoryUsage?: number;
  networkRequests: number;
  cacheHits: number;
  cacheMisses: number;
}

interface UsePerformanceMonitorOptions {
  trackMemory?: boolean;
  trackNetwork?: boolean;
  trackCache?: boolean;
  reportInterval?: number; // Report interval in milliseconds
}

export const usePerformanceMonitor = (options: UsePerformanceMonitorOptions = {}) => {
  const {
    trackMemory = false,
    trackNetwork = true,
    trackCache = true,
    reportInterval = 30000 // 30 seconds
  } = options;

  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    loadTime: 0,
    renderTime: 0,
    memoryUsage: 0,
    networkRequests: 0,
    cacheHits: 0,
    cacheMisses: 0
  });

  const [isMonitoring, setIsMonitoring] = useState(false);

  // Track component render time
  const trackRenderTime = useCallback((componentName: string, startTime: number) => {
    const renderTime = performance.now() - startTime;
    
    setMetrics(prev => ({
      ...prev,
      renderTime: prev.renderTime + renderTime
    }));

    if (process.env.NODE_ENV === 'development') {
      console.log(`${componentName} rendered in ${renderTime.toFixed(2)}ms`);
    }
  }, []);

  // Track network requests
  const trackNetworkRequest = useCallback((url: string, method: string) => {
    if (!trackNetwork) return;

    setMetrics(prev => ({
      ...prev,
      networkRequests: prev.networkRequests + 1
    }));
  }, [trackNetwork]);

  // Track cache performance
  const trackCacheHit = useCallback(() => {
    if (!trackCache) return;

    setMetrics(prev => ({
      ...prev,
      cacheHits: prev.cacheHits + 1
    }));
  }, [trackCache]);

  const trackCacheMiss = useCallback(() => {
    if (!trackCache) return;

    setMetrics(prev => ({
      ...prev,
      cacheMisses: prev.cacheMisses + 1
    }));
  }, [trackCache]);

  // Get memory usage (if available)
  const getMemoryUsage = useCallback((): number | undefined => {
    if (!trackMemory || !('memory' in performance)) {
      return undefined;
    }

    const memory = (performance as any).memory;
    return memory ? memory.usedJSHeapSize / 1024 / 1024 : undefined; // MB
  }, [trackMemory]);

  // Start monitoring
  const startMonitoring = useCallback(() => {
    setIsMonitoring(true);
    const startTime = performance.now();
    
    setMetrics(prev => ({
      ...prev,
      loadTime: startTime
    }));
  }, []);

  // Stop monitoring
  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
    const endTime = performance.now();
    
    setMetrics(prev => ({
      ...prev,
      loadTime: endTime - prev.loadTime,
      memoryUsage: getMemoryUsage()
    }));
  }, [getMemoryUsage]);

  // Reset metrics
  const resetMetrics = useCallback(() => {
    setMetrics({
      loadTime: 0,
      renderTime: 0,
      memoryUsage: 0,
      networkRequests: 0,
      cacheHits: 0,
      cacheMisses: 0
    });
  }, []);

  // Get performance report
  const getReport = useCallback(() => {
    const cacheHitRate = metrics.cacheHits + metrics.cacheMisses > 0 
      ? (metrics.cacheHits / (metrics.cacheHits + metrics.cacheMisses) * 100).toFixed(2)
      : '0';

    return {
      ...metrics,
      cacheHitRate: `${cacheHitRate}%`,
      averageRenderTime: metrics.renderTime > 0 ? (metrics.renderTime / 10).toFixed(2) : '0' // Assuming 10 renders
    };
  }, [metrics]);

  // Periodic reporting
  useEffect(() => {
    if (!isMonitoring) return;

    const interval = setInterval(() => {
      const report = getReport();
      
      if (process.env.NODE_ENV === 'development') {
        console.log('Performance Report:', report);
      }
    }, reportInterval);

    return () => clearInterval(interval);
  }, [isMonitoring, getReport, reportInterval]);

  // Update memory usage periodically
  useEffect(() => {
    if (!trackMemory || !isMonitoring) return;

    const interval = setInterval(() => {
      const memoryUsage = getMemoryUsage();
      if (memoryUsage !== undefined) {
        setMetrics(prev => ({
          ...prev,
          memoryUsage
        }));
      }
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, [trackMemory, isMonitoring, getMemoryUsage]);

  return {
    metrics,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    resetMetrics,
    trackRenderTime,
    trackNetworkRequest,
    trackCacheHit,
    trackCacheMiss,
    getReport
  };
};

export default usePerformanceMonitor;
