/**
 * Centralized API Configuration for Trader AI Frontend
 * Handles environment-based configuration and consistent API calls
 */

// Environment configuration
export const ENV = {
  API_URL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000',
  WS_URL: process.env.REACT_APP_WS_URL || 'ws://127.0.0.1:8000/ws',
  ENVIRONMENT: process.env.REACT_APP_ENVIRONMENT || 'development',
  DEBUG: process.env.REACT_APP_ENVIRONMENT === 'development',
  TIMEOUT: parseInt(process.env.REACT_APP_API_TIMEOUT || '30000'),
  RETRY_ATTEMPTS: parseInt(process.env.REACT_APP_RETRY_ATTEMPTS || '3'),
};

// API Configuration
export const API_CONFIG = {
  BASE_URL: ENV.API_URL,
  WS_URL: ENV.WS_URL,
  TIMEOUT: ENV.TIMEOUT,
  RETRY_ATTEMPTS: ENV.RETRY_ATTEMPTS,
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  // API Endpoints
  TRADING_PERFORMANCE: '/api/v1/trading/performance',
  NIFTY50_PERFORMANCE: '/api/nifty50/performance',
};

// Standard API Response Interface
export interface APIResponse<T = any> {
  success: boolean;
  status: 'success' | 'error' | 'warning' | 'info';
  data?: T;
  message?: string;
  error?: string;
  error_code?: string;
  timestamp: string;
  request_id?: string;
  metadata?: Record<string, any>;
  // Auth properties for direct access
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
}

// Error Response Interface
export interface ErrorResponse {
  success: false;
  status: 'error';
  error: string;
  error_code: string;
  details?: Record<string, any>;
  stack_trace?: string;
  timestamp: string;
  request_id?: string;
}

// Paginated Response Interface
export interface PaginatedResponse<T = any> extends APIResponse<T[]> {
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Custom Error Classes
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any,
    public requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TimeoutError';
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public validationErrors?: Array<{
      field: string;
      message: string;
      code: string;
    }>
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Authentication Token Management
export class TokenManager {
  private static readonly TOKEN_KEY = 'trader_ai_token';
  private static readonly REFRESH_TOKEN_KEY = 'trader_ai_refresh_token';

  static getToken(): string | null {
    // Prefer primary key, but fall back to common 'token' key used by AuthContext
    return (
      localStorage.getItem(this.TOKEN_KEY) ||
      localStorage.getItem('token')
    );
  }

  static setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
    // Keep AuthContext storage in sync
    localStorage.setItem('token', token);
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static setRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  static clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem('token');
  }

  static isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      return Date.now() >= exp;
    } catch {
      return true;
    }
  }
}

// HTTP Client Configuration
export class HttpClient {
  private baseURL: string;
  private timeout: number;
  private retryAttempts: number;

  constructor(config: typeof API_CONFIG) {
    this.baseURL = config.BASE_URL.replace(/\/+$|\/+$/g, '');
    this.timeout = config.TIMEOUT;
    this.retryAttempts = config.RETRY_ATTEMPTS;
  }

  private buildUrl(endpoint: string): string {
    if (/^https?:\/\//i.test(endpoint)) {
      return endpoint;
    }

    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

    if (this.baseURL.toLowerCase().endsWith('/api') && normalizedEndpoint.toLowerCase().startsWith('/api/')) {
      return `${this.baseURL}${normalizedEndpoint.slice(4)}`;
    }

    return `${this.baseURL}${normalizedEndpoint}`;
  }

  private async fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeout: number = this.timeout
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new TimeoutError(`Request timed out after ${timeout}ms`);
      }
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        // Provide more detailed error message
        const errorMsg = error.message || '';
        let detailedMsg = 'Network error - please check your connection';
        
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
          detailedMsg = `Cannot connect to backend server at ${url}. Please ensure the backend is running on ${ENV.API_URL}`;
        } else if (errorMsg.includes('CORS')) {
          detailedMsg = 'CORS error - backend may not be configured correctly';
        }
        
        console.error(`[httpClient] Network error for ${url}:`, error);
        throw new NetworkError(detailedMsg);
      }
      
      throw error;
    }
  }

  private async handleResponse<T>(response: Response): Promise<APIResponse<T>> {
    // Handle 401 Unauthorized - Session invalidated
    if (response.status === 401) {
      // Clear tokens and trigger logout
      TokenManager.clearTokens();
      // Dispatch custom event for AuthContext to handle
      window.dispatchEvent(new CustomEvent('session-invalidated', {
        detail: { message: 'Your session has been invalidated. Please login again.' }
      }));
      throw new ApiError(
        'Session expired or invalidated. Please login again.',
        401,
        'SESSION_INVALIDATED'
      );
    }
    
    let responseData: APIResponse<T>;
    
    try {
      responseData = await response.json();
    } catch {
      responseData = {
        success: false,
        status: 'error',
        error: 'Invalid JSON response',
        error_code: 'INVALID_JSON',
        timestamp: new Date().toISOString(),
      } as APIResponse<T>;
    }

    if (!response.ok) {
      const errorMessage = responseData.error || responseData.message || 'Request failed';
      const errorCode = responseData.error_code || 'HTTP_ERROR';
      
      throw new ApiError(
        errorMessage,
        response.status,
        errorCode,
        responseData,
        responseData.request_id
      );
    }

    return responseData;
  }

  private createHeaders(additionalHeaders: Record<string, string> = {}): HeadersInit {
    const token = TokenManager.getToken();
    const headers: HeadersInit = {
      ...API_CONFIG.HEADERS,
      ...additionalHeaders,
    };

    if (token && !TokenManager.isTokenExpired(token)) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount: number = 0
  ): Promise<APIResponse<T>> {
    const url = this.buildUrl(endpoint);
    
    // Debug log in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[httpClient] Request URL: ${url}`);
    }
    const requestOptions: RequestInit = {
      ...options,
      headers: this.createHeaders(options.headers as Record<string, string>),
    };

    try {
      const response = await this.fetchWithTimeout(url, requestOptions);
      return await this.handleResponse<T>(response);
    } catch (error) {
      // Retry logic for network errors
      if (
        retryCount < this.retryAttempts &&
        (error instanceof NetworkError || error instanceof TimeoutError)
      ) {
        console.warn(`Request failed, retrying (${retryCount + 1}/${this.retryAttempts}):`, error);
        await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
        return this.request<T>(endpoint, options, retryCount + 1);
      }

      throw error;
    }
  }

  async get<T>(endpoint: string, paramsOrOptions?: Record<string, any> | { params?: Record<string, any> }): Promise<APIResponse<T>> {
    let url = this.buildUrl(endpoint);
    
    // Handle both { params: {...} } and { ... } formats
    let params: Record<string, any> | undefined;
    if (paramsOrOptions) {
      if ('params' in paramsOrOptions && paramsOrOptions.params) {
        // Handle { params: {...} } format
        params = paramsOrOptions.params;
      } else {
        // Handle { ... } format (direct params)
        params = paramsOrOptions as Record<string, any>;
      }
    }
    
    // Build query string manually to avoid URL constructor issues
    if (params) {
      const queryParams: string[] = [];
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          // Only add primitive values, skip objects/arrays
          if (typeof value !== 'object' || value instanceof Date) {
            queryParams.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
          }
        }
      });
      if (queryParams.length > 0) {
        const separator = url.includes('?') ? '&' : '?';
        url = `${url}${separator}${queryParams.join('&')}`;
      }
    }
    
    return this.request<T>(url);
  }

  async post<T>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

// Create HTTP client instance
export const httpClient = new HttpClient(API_CONFIG);

// Utility functions
export const createApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

export const createWsUrl = (endpoint: string): string => {
  return `${API_CONFIG.WS_URL}${endpoint}`;
};

// Error handling utilities
export const isApiError = (error: any): error is ApiError => {
  return error instanceof ApiError;
};

export const isNetworkError = (error: any): error is NetworkError => {
  return error instanceof NetworkError;
};

export const isTimeoutError = (error: any): error is TimeoutError => {
  return error instanceof TimeoutError;
};

export const isValidationError = (error: any): error is ValidationError => {
  return error instanceof ValidationError;
};

// Request ID generator
export const generateRequestId = (): string => {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Debug logging
export const debugLog = (message: string, data?: any): void => {
  if (ENV.DEBUG) {
    console.log(`[API Debug] ${message}`, data);
  }
};

// Export everything
export default {
  ENV,
  API_CONFIG,
  httpClient,
  TokenManager,
  ApiError,
  NetworkError,
  TimeoutError,
  ValidationError,
  createApiUrl,
  createWsUrl,
  isApiError,
  isNetworkError,
  isTimeoutError,
  isValidationError,
  generateRequestId,
  debugLog,
};
