import { useState, useCallback } from 'react';

interface UseRetryOptions {
  maxRetries?: number;
  retryDelay?: number;
  onRetry?: (attempt: number) => void;
  onMaxRetriesReached?: () => void;
}

interface UseRetryReturn {
  isRetrying: boolean;
  retryCount: number;
  executeWithRetry: <T>(fn: () => Promise<T>) => Promise<T>;
  reset: () => void;
}

export const useRetry = (options: UseRetryOptions = {}): UseRetryReturn => {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    onRetry,
    onMaxRetriesReached
  } = options;

  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const executeWithRetry = useCallback(async <T>(fn: () => Promise<T>): Promise<T> => {
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          setIsRetrying(true);
          setRetryCount(attempt);
          onRetry?.(attempt);
          await delay(retryDelay * attempt); // Exponential backoff
        }
        
        const result = await fn();
        setIsRetrying(false);
        setRetryCount(0);
        return result;
      } catch (error) {
        lastError = error as Error;
        
        if (attempt === maxRetries) {
          setIsRetrying(false);
          onMaxRetriesReached?.();
          throw lastError;
        }
      }
    }
    
    // This should never be reached, but TypeScript needs it
    throw lastError || new Error('Retry failed');
  }, [maxRetries, retryDelay, onRetry, onMaxRetriesReached]);

  const reset = useCallback(() => {
    setIsRetrying(false);
    setRetryCount(0);
  }, []);

  return {
    isRetrying,
    retryCount,
    executeWithRetry,
    reset
  };
};
