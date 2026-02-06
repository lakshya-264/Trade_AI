/**
 * Request Deduplication Utility
 * Prevents duplicate concurrent API requests
 */

interface PendingRequest {
  promise: Promise<any>;
  timestamp: number;
}

class RequestDeduplicator {
  private pendingRequests: Map<string, PendingRequest> = new Map();
  private readonly REQUEST_TIMEOUT = 30000; // 30 seconds

  /**
   * Deduplicate requests - if a request with the same key is already pending,
   * return the existing promise instead of making a new request
   */
  async deduplicate<T>(
    key: string,
    requestFn: () => Promise<T>,
    timeout: number = this.REQUEST_TIMEOUT
  ): Promise<T> {
    // Check if there's already a pending request
    const existing = this.pendingRequests.get(key);
    if (existing) {
      // Check if request is still valid (not too old)
      const age = Date.now() - existing.timestamp;
      if (age < timeout) {
        console.log(`[RequestDeduplicator] Reusing pending request for: ${key}`);
        return existing.promise as Promise<T>;
      } else {
        // Request is too old, remove it
        this.pendingRequests.delete(key);
      }
    }

    // Create new request
    const promise = requestFn().finally(() => {
      // Clean up after request completes
      setTimeout(() => {
        this.pendingRequests.delete(key);
      }, 1000); // Keep for 1 second after completion for rapid re-requests
    });

    this.pendingRequests.set(key, {
      promise,
      timestamp: Date.now(),
    });

    return promise;
  }

  /**
   * Cancel a pending request
   */
  cancel(key: string): void {
    this.pendingRequests.delete(key);
  }

  /**
   * Clear all pending requests
   */
  clear(): void {
    this.pendingRequests.clear();
  }

  /**
   * Get count of pending requests
   */
  getPendingCount(): number {
    return this.pendingRequests.size;
  }
}

// Singleton instance
export const requestDeduplicator = new RequestDeduplicator();

/**
 * React hook for request deduplication
 */
export function useRequestDeduplication() {
  return requestDeduplicator;
}
