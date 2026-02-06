import { useState, useEffect, useCallback } from 'react';

interface UseVirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number; // Number of items to render outside visible area
}

interface VirtualScrollResult<T> {
  startIndex: number;
  endIndex: number;
  totalHeight: number;
  offsetY: number;
  visibleItems: T[];
}

export const useVirtualScroll = <T>(
  items: T[],
  options: UseVirtualScrollOptions
): VirtualScrollResult<T> => {
  const { itemHeight, containerHeight, overscan = 5 } = options;
  const [scrollTop, setScrollTop] = useState(0);

  const handleScroll = useCallback((e: Event) => {
    const target = e.target as HTMLElement;
    setScrollTop(target.scrollTop);
  }, []);

  useEffect(() => {
    // This would be attached to the scrollable container
    // The actual implementation would depend on how the scroll container is set up
  }, [handleScroll]);

  const totalHeight = items.length * itemHeight;
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = items.slice(startIndex, endIndex + 1);
  const offsetY = startIndex * itemHeight;

  return {
    startIndex,
    endIndex,
    totalHeight,
    offsetY,
    visibleItems
  };
};

export default useVirtualScroll;
