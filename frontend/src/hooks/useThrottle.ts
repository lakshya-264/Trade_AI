import { useRef, useCallback } from 'react';

/**
 * Throttle hook - limits function execution to once per delay period
 * Unlike debounce, throttle executes immediately and then waits
 */
export function useThrottle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  const lastRun = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRun.current;

      if (timeSinceLastRun >= delay) {
        // Enough time has passed, execute immediately
        lastRun.current = now;
        func(...args);
      } else {
        // Schedule execution for the remaining time
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = setTimeout(() => {
          lastRun.current = Date.now();
          func(...args);
        }, delay - timeSinceLastRun);
      }
    }) as T,
    [func, delay]
  );
}
