// Bundle analysis utilities for performance monitoring
export const analyzeBundle = () => {
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  // Get performance timing information
  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  
  if (!navigation) {
    return null;
  }

  const bundleAnalysis = {
    // Page load metrics
    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
    totalLoadTime: navigation.loadEventEnd - navigation.fetchStart,
    
    // Resource metrics
    resources: performance.getEntriesByType('resource').map((resource: PerformanceEntry) => {
      const resourceTiming = resource as PerformanceResourceTiming;
      return {
        name: resourceTiming.name,
        duration: resourceTiming.duration,
        size: resourceTiming.transferSize,
        type: resourceTiming.initiatorType
      };
    }),
    
    // Memory usage (if available)
    memory: (performance as any).memory ? {
      used: (performance as any).memory.usedJSHeapSize,
      total: (performance as any).memory.totalJSHeapSize,
      limit: (performance as any).memory.jsHeapSizeLimit
    } : null
  };

  return bundleAnalysis;
};

// Log bundle analysis in development
export const logBundleAnalysis = () => {
  if (process.env.NODE_ENV === 'development') {
    const analysis = analyzeBundle();
    if (analysis) {
      console.group('📊 Bundle Analysis');
      console.log('Load Time:', analysis.totalLoadTime.toFixed(2), 'ms');
      console.log('DOM Ready:', analysis.domContentLoaded.toFixed(2), 'ms');
      console.log('Resources:', analysis.resources.length);
      
      if (analysis.memory) {
        console.log('Memory Used:', (analysis.memory.used / 1024 / 1024).toFixed(2), 'MB');
        console.log('Memory Total:', (analysis.memory.total / 1024 / 1024).toFixed(2), 'MB');
      }
      
      console.groupEnd();
    }
  }
};

export default analyzeBundle;
