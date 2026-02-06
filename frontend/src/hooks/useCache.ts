import { useEffect, useCallback } from 'react';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

interface UseCacheOptions {
  ttl?: number; // Default TTL in milliseconds
  maxSize?: number; // Maximum cache size
}

class CacheManager {
  private cache = new Map<string, CacheEntry<any>>();
  private maxSize: number;

  constructor(maxSize: number = 100) {
    this.maxSize = maxSize;
  }

  set<T>(key: string, data: T, ttl: number = 5 * 60 * 1000): void {
    // Remove oldest entries if cache is full
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    // Check if entry has expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    return entry ? Date.now() - entry.timestamp <= entry.ttl : false;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  size(): number {
    return this.cache.size;
  }

  // Clean up expired entries
  cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }
}

// Global cache instance
const globalCache = new CacheManager();

export const useCache = <T>(options: UseCacheOptions = {}) => {
  const { ttl = 5 * 60 * 1000 } = options;

  const get = useCallback((key: string): T | null => {
    return globalCache.get<T>(key);
  }, []);

  const set = useCallback((key: string, data: T, customTtl?: number): void => {
    globalCache.set(key, data, customTtl || ttl);
  }, [ttl]);

  const has = useCallback((key: string): boolean => {
    return globalCache.has(key);
  }, []);

  const clear = useCallback((): void => {
    globalCache.clear();
  }, []);

  const remove = useCallback((key: string): boolean => {
    return globalCache.delete(key);
  }, []);

  // Cleanup expired entries on mount
  useEffect(() => {
    globalCache.cleanup();
  }, []);

  return {
    get,
    set,
    has,
    clear,
    remove,
    size: globalCache.size()
  };
};

export default useCache;
