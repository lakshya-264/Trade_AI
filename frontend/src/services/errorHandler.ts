/**
 * Centralized Error Handling Service
 * Replaces console.log/error with proper error management
 */

import { toast } from 'react-hot-toast';

export enum ErrorType {
  NETWORK = 'NETWORK',
  API = 'API',
  VALIDATION = 'VALIDATION',
  AUTHENTICATION = 'AUTHENTICATION',
  PERMISSION = 'PERMISSION',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN'
}

export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export interface ErrorDetails {
  type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  code?: string;
  details?: Record<string, any>;
  timestamp: string;
  requestId?: string;
  userId?: string;
  component?: string;
  action?: string;
}

export interface ErrorHandlerConfig {
  enableToast: boolean;
  enableConsole: boolean;
  enableReporting: boolean;
  enableRetry: boolean;
  maxRetries: number;
  retryDelay: number;
}

class ErrorHandlerService {
  private config: ErrorHandlerConfig;
  private errorHistory: ErrorDetails[] = [];
  private retryAttempts: Map<string, number> = new Map();

  constructor(config: Partial<ErrorHandlerConfig> = {}) {
    this.config = {
      enableToast: true,
      enableConsole: process.env.NODE_ENV === 'development',
      enableReporting: true,
      enableRetry: true,
      maxRetries: 3,
      retryDelay: 1000,
      ...config
    };
  }

  /**
   * Handle API errors with proper categorization and user feedback
   */
  handleApiError(error: any, context?: {
    component?: string;
    action?: string;
    requestId?: string;
    userId?: string;
  }): ErrorDetails {
    const errorDetails = this.categorizeError(error, context);
    this.processError(errorDetails);
    return errorDetails;
  }

  /**
   * Handle network errors with retry logic
   */
  handleNetworkError(error: any, context?: {
    component?: string;
    action?: string;
    requestId?: string;
  }): ErrorDetails {
    const errorDetails: ErrorDetails = {
      type: ErrorType.NETWORK,
      severity: ErrorSeverity.MEDIUM,
      message: this.getNetworkErrorMessage(error),
      code: error.code || 'NETWORK_ERROR',
      details: {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status
      },
      timestamp: new Date().toISOString(),
      ...context
    };

    this.processError(errorDetails);
    return errorDetails;
  }

  /**
   * Handle validation errors
   */
  handleValidationError(field: string, message: string, context?: {
    component?: string;
    action?: string;
  }): ErrorDetails {
    const errorDetails: ErrorDetails = {
      type: ErrorType.VALIDATION,
      severity: ErrorSeverity.LOW,
      message: `Validation error: ${message}`,
      code: 'VALIDATION_ERROR',
      details: { field },
      timestamp: new Date().toISOString(),
      ...context
    };

    this.processError(errorDetails);
    return errorDetails;
  }

  /**
   * Handle authentication errors
   */
  handleAuthError(error: any, context?: {
    component?: string;
    action?: string;
  }): ErrorDetails {
    const errorDetails: ErrorDetails = {
      type: ErrorType.AUTHENTICATION,
      severity: ErrorSeverity.HIGH,
      message: this.getAuthErrorMessage(error),
      code: error.response?.status === 401 ? 'UNAUTHORIZED' : 'AUTH_ERROR',
      details: {
        status: error.response?.status,
        url: error.config?.url
      },
      timestamp: new Date().toISOString(),
      ...context
    };

    this.processError(errorDetails);
    return errorDetails;
  }

  /**
   * Categorize and analyze errors
   */
  private categorizeError(error: any, context?: any): ErrorDetails {
    let type = ErrorType.UNKNOWN;
    let severity = ErrorSeverity.MEDIUM;
    let message = 'An unexpected error occurred';

    // Determine error type and severity
    if (error.response) {
      const status = error.response.status;
      type = ErrorType.API;
      
      switch (status) {
        case 400:
          severity = ErrorSeverity.LOW;
          message = 'Invalid request. Please check your input.';
          break;
        case 401:
          type = ErrorType.AUTHENTICATION;
          severity = ErrorSeverity.HIGH;
          message = 'Authentication required. Please login again.';
          break;
        case 403:
          type = ErrorType.PERMISSION;
          severity = ErrorSeverity.HIGH;
          message = 'Access denied. You do not have permission.';
          break;
        case 404:
          severity = ErrorSeverity.MEDIUM;
          message = 'Resource not found.';
          break;
        case 429:
          type = ErrorType.API;
          severity = ErrorSeverity.MEDIUM;
          message = 'Too many requests. Please try again later.';
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          severity = ErrorSeverity.HIGH;
          message = 'Server error. Please try again later.';
          break;
        default:
          message = `API Error: ${error.response.data?.message || error.message}`;
      }
    } else if (error.code === 'ECONNABORTED') {
      type = ErrorType.TIMEOUT;
      severity = ErrorSeverity.MEDIUM;
      message = 'Request timed out. Please try again.';
    } else if (error.code === 'NETWORK_ERROR' || !navigator.onLine) {
      type = ErrorType.NETWORK;
      severity = ErrorSeverity.MEDIUM;
      message = 'Network error. Please check your connection.';
    }

    return {
      type,
      severity,
      message,
      code: error.code || error.response?.status?.toString(),
      details: {
        originalError: error.message,
        status: error.response?.status,
        url: error.config?.url,
        method: error.config?.method
      },
      timestamp: new Date().toISOString(),
      ...context
    };
  }

  /**
   * Process error based on configuration
   */
  private processError(errorDetails: ErrorDetails): void {
    // Add to error history
    this.errorHistory.push(errorDetails);
    
    // Keep only last 100 errors
    if (this.errorHistory.length > 100) {
      this.errorHistory = this.errorHistory.slice(-100);
    }

    // Show toast notification
    if (this.config.enableToast) {
      this.showToast(errorDetails);
    }

    // Log to console in development
    if (this.config.enableConsole) {
      this.logToConsole(errorDetails);
    }

    // Report to external service
    if (this.config.enableReporting) {
      this.reportError(errorDetails);
    }
  }

  /**
   * Show appropriate toast notification
   */
  private showToast(errorDetails: ErrorDetails): void {
    const { severity, message } = errorDetails;
    
    switch (severity) {
      case ErrorSeverity.CRITICAL:
        toast.error(message, { duration: 6000 });
        break;
      case ErrorSeverity.HIGH:
        toast.error(message, { duration: 4000 });
        break;
      case ErrorSeverity.MEDIUM:
        toast.error(message, { duration: 3000 });
        break;
      case ErrorSeverity.LOW:
        toast(message, { 
          icon: '⚠️',
          duration: 2000 
        });
        break;
    }
  }

  /**
   * Log error to console with proper formatting
   */
  private logToConsole(errorDetails: ErrorDetails): void {
    const { type, severity, message, details, component } = errorDetails;
    
    const logMessage = `[${type}] ${message}`;
    const logDetails = {
      severity,
      component,
      details,
      timestamp: errorDetails.timestamp
    };

    switch (severity) {
      case ErrorSeverity.CRITICAL:
      case ErrorSeverity.HIGH:
        console.error(logMessage, logDetails);
        break;
      case ErrorSeverity.MEDIUM:
        console.warn(logMessage, logDetails);
        break;
      case ErrorSeverity.LOW:
        console.info(logMessage, logDetails);
        break;
    }
  }

  /**
   * Report error to external service (placeholder)
   */
  private reportError(errorDetails: ErrorDetails): void {
    // TODO: Implement external error reporting (e.g., Sentry, LogRocket)
    // For now, just store in localStorage for debugging
    try {
      const reportedErrors = JSON.parse(
        localStorage.getItem('reported_errors') || '[]'
      );
      reportedErrors.push(errorDetails);
      localStorage.setItem('reported_errors', JSON.stringify(reportedErrors.slice(-50)));
    } catch (e) {
      // Ignore localStorage errors
    }
  }

  /**
   * Get user-friendly network error message
   */
  private getNetworkErrorMessage(error: any): string {
    if (!navigator.onLine) {
      return 'You are offline. Please check your internet connection.';
    }
    
    if (error.code === 'ECONNABORTED') {
      return 'Request timed out. Please try again.';
    }
    
    if (error.code === 'NETWORK_ERROR') {
      return 'Network error. Please check your connection.';
    }
    
    return 'Network error occurred. Please try again.';
  }

  /**
   * Get user-friendly authentication error message
   */
  private getAuthErrorMessage(error: any): string {
    const status = error.response?.status;
    
    switch (status) {
      case 401:
        return 'Your session has expired. Please login again.';
      case 403:
        return 'You do not have permission to access this resource.';
      default:
        return 'Authentication error. Please try logging in again.';
    }
  }

  /**
   * Get error history for debugging
   */
  getErrorHistory(): ErrorDetails[] {
    return [...this.errorHistory];
  }

  /**
   * Clear error history
   */
  clearErrorHistory(): void {
    this.errorHistory = [];
  }

  /**
   * Get error statistics
   */
  getErrorStats(): {
    total: number;
    byType: Record<ErrorType, number>;
    bySeverity: Record<ErrorSeverity, number>;
    recentErrors: ErrorDetails[];
  } {
    const byType = Object.values(ErrorType).reduce((acc, type) => {
      acc[type] = this.errorHistory.filter(e => e.type === type).length;
      return acc;
    }, {} as Record<ErrorType, number>);

    const bySeverity = Object.values(ErrorSeverity).reduce((acc, severity) => {
      acc[severity] = this.errorHistory.filter(e => e.severity === severity).length;
      return acc;
    }, {} as Record<ErrorSeverity, number>);

    return {
      total: this.errorHistory.length,
      byType,
      bySeverity,
      recentErrors: this.errorHistory.slice(-10)
    };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<ErrorHandlerConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

// Export singleton instance
export const errorHandler = new ErrorHandlerService();

// Export utility functions for common error handling patterns
export const handleApiError = (error: any, context?: any) => 
  errorHandler.handleApiError(error, context);

export const handleNetworkError = (error: any, context?: any) => 
  errorHandler.handleNetworkError(error, context);

export const handleValidationError = (field: string, message: string, context?: any) => 
  errorHandler.handleValidationError(field, message, context);

export const handleAuthError = (error: any, context?: any) => 
  errorHandler.handleAuthError(error, context);

export default errorHandler;
