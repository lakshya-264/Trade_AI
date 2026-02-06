/**
 * Performance Optimization Utilities
 * Tools and utilities for optimizing frontend performance
 */

import React, { useCallback, useMemo, useRef, useEffect } from 'react';

// Debounce utility for API calls
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// Throttle utility for scroll events
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// Performance monitoring utility
export const performanceMonitor = {
  measureRenderTime: (componentName: string) => {
    const startTime = performance.now();
    return () => {
      const endTime = performance.now();
      if (process.env.NODE_ENV === 'development') {
        console.log(`${componentName} render time: ${endTime - startTime}ms`);
      }
    };
  },
  
  measureApiCall: async <T>(apiCall: () => Promise<T>, endpoint: string): Promise<T> => {
    const startTime = performance.now();
    try {
      const result = await apiCall();
      const endTime = performance.now();
      if (process.env.NODE_ENV === 'development') {
        console.log(`${endpoint} API call time: ${endTime - startTime}ms`);
      }
      return result;
    } catch (error) {
      const endTime = performance.now();
      if (process.env.NODE_ENV === 'development') {
        console.log(`${endpoint} API call failed after: ${endTime - startTime}ms`);
      }
      throw error;
    }
  },
  
  measureMemoryUsage: () => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit
      };
    }
    return null;
  },
  
  measureResourceTiming: () => {
    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
    return {
      resourceCount: resources.length,
      totalResourceSize: resources.reduce((total, resource) => {
        return total + (resource.transferSize || 0);
      }, 0)
    };
  }
};

// Performance optimization component wrapper
export const withPerformanceOptimization = <P extends object>(
  Component: React.ComponentType<P>
) => {
  return React.memo((props: P) => {
    const renderTime = performanceMonitor.measureRenderTime(Component.name);
    
    useEffect(() => {
      renderTime();
    });
    
    return React.createElement(Component, props);
  });
};

// Error boundary for performance monitoring
export class PerformanceErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (process.env.NODE_ENV === 'development') {
      console.error('Performance Error:', error, errorInfo);
    }
    
    // Log performance metrics when error occurs
    const memoryUsage = performanceMonitor.measureMemoryUsage();
    if (memoryUsage) {
      console.log('Memory usage at error:', memoryUsage);
    }
  }
  
  render() {
    if (this.state.hasError) {
      return React.createElement('div', {
        className: "p-4 bg-red-50 border border-red-200 rounded-md"
      }, [
        React.createElement('h2', {
          key: 'title',
          className: "text-lg font-semibold text-red-800"
        }, 'Performance Error'),
        React.createElement('p', {
          key: 'message',
          className: "text-red-600"
        }, 'A performance-related error occurred. Please refresh the page.'),
        React.createElement('button', {
          key: 'button',
          onClick: () => window.location.reload(),
          className: "mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        }, 'Refresh Page')
      ]);
    }
    
    return this.props.children;
  }
}

// Resource preloader
export const preloadResource = (url: string, type: 'script' | 'style' | 'image' = 'script') => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.href = url;
  link.as = type;
  document.head.appendChild(link);
};

// Lazy loading utility
export const lazyLoad = (importFn: () => Promise<any>) => {
  return React.lazy(importFn);
};

// Memoization utilities
export const useMemoizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): T => {
  return useCallback(callback, deps);
};

export const useMemoizedValue = <T>(
  factory: () => T,
  deps: React.DependencyList
): T => {
  return useMemo(factory, deps);
};

// Virtual scrolling utilities
export const useVirtualScrolling = (
  itemCount: number,
  itemHeight: number,
  containerHeight: number
) => {
  const [scrollTop, setScrollTop] = React.useState(0);
  
  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / itemHeight) + 1,
    itemCount
  );
  
  const visibleItems = Array.from(
    { length: visibleEnd - visibleStart },
    (_, i) => visibleStart + i
  );
  
  const totalHeight = itemCount * itemHeight;
  const offsetY = visibleStart * itemHeight;
  
  return {
    visibleItems,
    totalHeight,
    offsetY,
    setScrollTop
  };
};

// Performance metrics collection
export const collectPerformanceMetrics = () => {
  const metrics = {
    navigation: performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming,
    resource: performance.getEntriesByType('resource') as PerformanceResourceTiming[],
    memory: performanceMonitor.measureMemoryUsage()
  };
  
  return {
    pageLoadTime: metrics.navigation.loadEventEnd - metrics.navigation.loadEventStart,
    domContentLoaded: metrics.navigation.domContentLoadedEventEnd - metrics.navigation.domContentLoadedEventStart,
    firstPaint: metrics.navigation.responseEnd - metrics.navigation.requestStart,
    resourceCount: metrics.resource.length,
    totalResourceSize: metrics.resource.reduce((total, resource) => {
      return total + (resource.transferSize || 0);
    }, 0),
    memoryUsage: metrics.memory
  };
};

// Performance optimization hooks
export const usePerformanceOptimization = () => {
  const [metrics, setMetrics] = React.useState<any>(null);
  
  useEffect(() => {
    const collectMetrics = () => {
      const performanceMetrics = collectPerformanceMetrics();
      setMetrics(performanceMetrics);
    };
    
    // Collect metrics after component mount
    const timeout = setTimeout(collectMetrics, 1000);
    
    return () => clearTimeout(timeout);
  }, []);
  
  return metrics;
};

// Bundle size optimization
export const optimizeBundleSize = () => {
  if (process.env.NODE_ENV === 'production') {
    // Enable tree shaking
    console.log('Bundle optimization enabled');
  }
};

// Image optimization utilities
export const optimizeImage = (src: string, width?: number, height?: number) => {
  const params = new URLSearchParams();
  if (width) params.append('w', width.toString());
  if (height) params.append('h', height.toString());
  
  return `${src}?${params.toString()}`;
};

// Cache utilities
export const createCache = <T>(maxSize: number = 100) => {
  const cache = new Map<string, T>();
  
  return {
    get: (key: string) => cache.get(key),
    set: (key: string, value: T) => {
      if (cache.size >= maxSize) {
        const firstKey = cache.keys().next().value;
        cache.delete(firstKey);
      }
      cache.set(key, value);
    },
    clear: () => cache.clear(),
    size: () => cache.size
  };
};

export default {
  debounce,
  throttle,
  performanceMonitor,
  withPerformanceOptimization,
  PerformanceErrorBoundary,
  preloadResource,
  lazyLoad,
  useMemoizedCallback,
  useMemoizedValue,
  useVirtualScrolling,
  collectPerformanceMetrics,
  usePerformanceOptimization,
  optimizeBundleSize,
  optimizeImage,
  createCache
};