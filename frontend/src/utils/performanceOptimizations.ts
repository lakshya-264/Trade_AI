/**
 * Performance Optimization Utilities
 * Common optimizations for React components
 */

import { useMemo, useCallback, useRef, useEffect } from 'react';

/**
 * Debounce function calls
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };
    
    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function calls
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Memoize expensive calculations
 */
export function useExpensiveCalculation<T>(
  calculation: () => T,
  deps: React.DependencyList
): T {
  return useMemo(() => calculation(), deps);
}

/**
 * Optimize array operations
 */
export function optimizeArrayOperation<T, R>(
  array: T[],
  operation: (item: T, index: number) => R,
  shouldProcess: (item: T, index: number) => boolean = () => true
): R[] {
  const result: R[] = [];
  for (let i = 0; i < array.length; i++) {
    if (shouldProcess(array[i], i)) {
      result.push(operation(array[i], i));
    }
  }
  return result;
}

/**
 * Batch state updates to prevent multiple re-renders
 */
export function useBatchedUpdates() {
  const updatesRef = useRef<Array<() => void>>([]);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const batchUpdate = useCallback((update: () => void) => {
    updatesRef.current.push(update);
    
    if (!timeoutRef.current) {
      timeoutRef.current = setTimeout(() => {
        updatesRef.current.forEach(update => update());
        updatesRef.current = [];
        timeoutRef.current = null;
      }, 0);
    }
  }, []);
  
  return batchUpdate;
}

/**
 * Check if component should re-render based on props
 */
export function shouldComponentUpdate<T extends Record<string, any>>(
  prevProps: T,
  nextProps: T,
  keysToCompare: (keyof T)[]
): boolean {
  return keysToCompare.some(key => prevProps[key] !== nextProps[key]);
}

/**
 * Optimize chart data processing
 */
export function optimizeChartDataProcessing<T>(
  data: T[],
  processor: (item: T) => T | null
): T[] {
  // Use for loop instead of map+filter for better performance
  const result: T[] = [];
  for (let i = 0; i < data.length; i++) {
    const processed = processor(data[i]);
    if (processed !== null) {
      result.push(processed);
    }
  }
  return result;
}

/**
 * Virtual scrolling helper
 */
export function getVisibleRange(
  scrollTop: number,
  itemHeight: number,
  containerHeight: number,
  totalItems: number
): { start: number; end: number } {
  const start = Math.floor(scrollTop / itemHeight);
  const end = Math.min(
    start + Math.ceil(containerHeight / itemHeight) + 1,
    totalItems
  );
  return { start, end };
}

/**
 * Prevent memory leaks by cleaning up intervals/timeouts
 */
export function useCleanup() {
  const cleanupRef = useRef<Array<() => void>>([]);
  
  const addCleanup = useCallback((cleanup: () => void) => {
    cleanupRef.current.push(cleanup);
  }, []);
  
  useEffect(() => {
    return () => {
      cleanupRef.current.forEach(cleanup => cleanup());
      cleanupRef.current = [];
    };
  }, []);
  
  return addCleanup;
}
