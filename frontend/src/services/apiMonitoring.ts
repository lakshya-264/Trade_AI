// API Call Monitoring System
// Added by Critical Issues Fix v2.0

interface ApiCall {
  endpoint: string;
  method: string;
  timestamp: number;
  duration: number;
  status: 'success' | 'error';
  responseSize?: number;
  userAgent?: string;
  ipAddress?: string;
}

interface ApiStats {
  totalCalls: number;
  successfulCalls: number;
  errorCalls: number;
  successRate: number;
  avgDuration: number;
  calls: ApiCall[];
  endpointStats: Record<string, {
    count: number;
    successRate: number;
    avgDuration: number;
  }>;
}

class ApiMonitoringService {
  private calls: ApiCall[] = [];
  private maxCalls = 1000; // Keep last 1000 calls

  logCall(call: ApiCall) {
    this.calls.push(call);
    
    // Keep only recent calls
    if (this.calls.length > this.maxCalls) {
      this.calls = this.calls.slice(-this.maxCalls);
    }
    
    // Store in localStorage for persistence
    localStorage.setItem('apiCalls', JSON.stringify(this.calls));
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] ${call.method} ${call.endpoint} - ${call.status} (${call.duration}ms)`);
    }
    
    // Send to backend for server-side monitoring
    this.sendToBackend(call);
  }

  private async sendToBackend(call: ApiCall) {
    try {
      // Send API call data to backend for monitoring
      await fetch('/api/monitoring/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...call,
          timestamp: new Date(call.timestamp).toISOString()
        })
      });
    } catch (error) {
      // Silently fail - monitoring shouldn't break the app
      console.debug('Failed to send API call to backend monitoring:', error);
    }
  }

  getStats(): ApiStats {
    const totalCalls = this.calls.length;
    const successfulCalls = this.calls.filter(call => call.status === 'success').length;
    const errorCalls = this.calls.filter(call => call.status === 'error').length;
    const avgDuration = this.calls.reduce((sum, call) => sum + call.duration, 0) / totalCalls;
    
    // Calculate endpoint-specific stats
    const endpointStats: Record<string, { count: number; successRate: number; avgDuration: number }> = {};
    this.calls.forEach(call => {
      if (!endpointStats[call.endpoint]) {
        endpointStats[call.endpoint] = { count: 0, successRate: 0, avgDuration: 0 };
      }
      endpointStats[call.endpoint].count++;
    });
    
    // Calculate success rates and avg durations per endpoint
    Object.keys(endpointStats).forEach(endpoint => {
      const endpointCalls = this.calls.filter(call => call.endpoint === endpoint);
      const successfulEndpointCalls = endpointCalls.filter(call => call.status === 'success').length;
      const avgEndpointDuration = endpointCalls.reduce((sum, call) => sum + call.duration, 0) / endpointCalls.length;
      
      endpointStats[endpoint].successRate = endpointCalls.length > 0 ? (successfulEndpointCalls / endpointCalls.length) * 100 : 0;
      endpointStats[endpoint].avgDuration = avgEndpointDuration || 0;
    });
    
    return {
      totalCalls,
      successfulCalls,
      errorCalls,
      successRate: totalCalls > 0 ? (successfulCalls / totalCalls) * 100 : 0,
      avgDuration: avgDuration || 0,
      calls: this.calls.slice(-50), // Last 50 calls
      endpointStats
    };
  }

  getCallsByEndpoint(endpoint: string): ApiCall[] {
    return this.calls.filter(call => call.endpoint.includes(endpoint));
  }

  getCallsByTimeRange(startTime: number, endTime: number): ApiCall[] {
    return this.calls.filter(call => call.timestamp >= startTime && call.timestamp <= endTime);
  }

  getErrorCalls(): ApiCall[] {
    return this.calls.filter(call => call.status === 'error');
  }

  getSlowCalls(threshold: number = 1000): ApiCall[] {
    return this.calls.filter(call => call.duration > threshold);
  }

  clearHistory() {
    this.calls = [];
    localStorage.removeItem('apiCalls');
  }

  exportData() {
    return {
      calls: this.calls,
      stats: this.getStats(),
      exportedAt: new Date().toISOString()
    };
  }
}

// Global instance
export const apiMonitoring = new ApiMonitoringService();

// Enhanced API wrapper with monitoring
export const monitoredApi = {
  async get(endpoint: string, options?: any) {
    const startTime = Date.now();
    try {
      const response = await fetch(endpoint, {
        method: 'GET',
        ...options
      });
      const duration = Date.now() - startTime;
      
      apiMonitoring.logCall({
        endpoint,
        method: 'GET',
        timestamp: startTime,
        duration,
        status: response.ok ? 'success' : 'error',
        responseSize: response.headers.get('content-length') ? parseInt(response.headers.get('content-length')!) : undefined
      });
      
      return response;
    } catch (error) {
      const duration = Date.now() - startTime;
      apiMonitoring.logCall({
        endpoint,
        method: 'GET',
        timestamp: startTime,
        duration,
        status: 'error'
      });
      throw error;
    }
  },

  async post(endpoint: string, data?: any, options?: any) {
    const startTime = Date.now();
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers
        },
        body: data ? JSON.stringify(data) : undefined,
        ...options
      });
      const duration = Date.now() - startTime;
      
      apiMonitoring.logCall({
        endpoint,
        method: 'POST',
        timestamp: startTime,
        duration,
        status: response.ok ? 'success' : 'error',
        responseSize: response.headers.get('content-length') ? parseInt(response.headers.get('content-length')!) : undefined
      });
      
      return response;
    } catch (error) {
      const duration = Date.now() - startTime;
      apiMonitoring.logCall({
        endpoint,
        method: 'POST',
        timestamp: startTime,
        duration,
        status: 'error'
      });
      throw error;
    }
  },

  async put(endpoint: string, data?: any, options?: any) {
    const startTime = Date.now();
    try {
      const response = await fetch(endpoint, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers
        },
        body: data ? JSON.stringify(data) : undefined,
        ...options
      });
      const duration = Date.now() - startTime;
      
      apiMonitoring.logCall({
        endpoint,
        method: 'PUT',
        timestamp: startTime,
        duration,
        status: response.ok ? 'success' : 'error',
        responseSize: response.headers.get('content-length') ? parseInt(response.headers.get('content-length')!) : undefined
      });
      
      return response;
    } catch (error) {
      const duration = Date.now() - startTime;
      apiMonitoring.logCall({
        endpoint,
        method: 'PUT',
        timestamp: startTime,
        duration,
        status: 'error'
      });
      throw error;
    }
  },

  async delete(endpoint: string, options?: any) {
    const startTime = Date.now();
    try {
      const response = await fetch(endpoint, {
        method: 'DELETE',
        ...options
      });
      const duration = Date.now() - startTime;
      
      apiMonitoring.logCall({
        endpoint,
        method: 'DELETE',
        timestamp: startTime,
        duration,
        status: response.ok ? 'success' : 'error',
        responseSize: response.headers.get('content-length') ? parseInt(response.headers.get('content-length')!) : undefined
      });
      
      return response;
    } catch (error) {
      const duration = Date.now() - startTime;
      apiMonitoring.logCall({
        endpoint,
        method: 'DELETE',
        timestamp: startTime,
        duration,
        status: 'error'
      });
      throw error;
    }
  }
};

export default apiMonitoring;
