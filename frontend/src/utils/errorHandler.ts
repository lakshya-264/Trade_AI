/**
 * Error Handling Utility
 * Centralized error handling for API errors across the application
 */

import { ApiError } from '../config/api';
import { toast } from 'react-hot-toast';

/**
 * Extract error message from various error types
 */
export function getErrorMessage(error: any, defaultMessage: string): string {
  // Handle ApiError from httpClient
  if (error instanceof ApiError) {
    return error.details?.detail || error.details?.error || error.message || defaultMessage;
  }
  
  // Handle standard Error objects
  if (error instanceof Error) {
    return error.message || defaultMessage;
  }
  
  // Handle error objects with response data (axios-style)
  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  if (error?.response?.data?.message) {
    return error.response.data.message;
  }
  
  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }
  
  // Fallback to default message
  return defaultMessage;
}

/**
 * Handle API error and show toast notification
 */
export function handleApiError(
  error: any,
  defaultMessage: string,
  showToast: boolean = true
): string {
  const errorMessage = getErrorMessage(error, defaultMessage);
  
  if (showToast) {
    toast.error(errorMessage);
  }
  
  return errorMessage;
}

/**
 * Handle API error with console logging
 */
export function handleApiErrorWithLog(
  error: any,
  defaultMessage: string,
  context: string = 'API call',
  showToast: boolean = true
): string {
  const errorMessage = getErrorMessage(error, defaultMessage);
  
  console.error(`Error in ${context}:`, error);
  
  if (showToast) {
    toast.error(errorMessage);
  }
  
  return errorMessage;
}

/**
 * Wrapper for async functions with error handling
 */
export async function withErrorHandling<T>(
  asyncFn: () => Promise<T>,
  defaultMessage: string,
  context: string = 'Operation',
  showToast: boolean = true
): Promise<T | null> {
  try {
    return await asyncFn();
  } catch (error) {
    handleApiErrorWithLog(error, defaultMessage, context, showToast);
    return null;
  }
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: any): boolean {
  return (
    error?.message?.includes('Network') ||
    error?.message?.includes('fetch') ||
    error?.name === 'NetworkError' ||
    error?.code === 'NETWORK_ERROR'
  );
}

/**
 * Check if error is a timeout error
 */
export function isTimeoutError(error: any): boolean {
  return (
    error?.message?.includes('timeout') ||
    error?.name === 'TimeoutError' ||
    error?.code === 'TIMEOUT'
  );
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error: any): boolean {
  return (
    error instanceof ApiError && error.status === 401 ||
    error?.response?.status === 401 ||
    error?.status === 401
  );
}

