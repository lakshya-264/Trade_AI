import React from 'react';
import { 
  ExclamationTriangleIcon, 
  ArrowPathIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';

interface ErrorDisplayProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  type?: 'error' | 'warning' | 'info';
  showRetry?: boolean;
  className?: string;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
  onDismiss,
  type = 'error',
  showRetry = true,
  className = ''
}) => {
  const getTypeStyles = () => {
    switch (type) {
      case 'error':
        return {
          container: 'bg-red-50 border-red-200',
          icon: 'text-red-500',
          title: 'text-red-800',
          message: 'text-red-700',
          button: 'bg-red-600 hover:bg-red-700 text-white'
        };
      case 'warning':
        return {
          container: 'bg-yellow-50 border-yellow-200',
          icon: 'text-yellow-500',
          title: 'text-yellow-800',
          message: 'text-yellow-700',
          button: 'bg-yellow-600 hover:bg-yellow-700 text-white'
        };
      case 'info':
        return {
          container: 'bg-blue-50 border-blue-200',
          icon: 'text-blue-500',
          title: 'text-blue-800',
          message: 'text-blue-700',
          button: 'bg-blue-600 hover:bg-blue-700 text-white'
        };
      default:
        return {
          container: 'bg-gray-50 border-gray-200',
          icon: 'text-gray-500',
          title: 'text-gray-800',
          message: 'text-gray-700',
          button: 'bg-gray-600 hover:bg-gray-700 text-white'
        };
    }
  };

  const styles = getTypeStyles();

  return (
    <div className={`rounded-lg border p-4 ${styles.container} ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <ExclamationTriangleIcon className={`h-5 w-5 ${styles.icon}`} />
        </div>
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${styles.title}`}>
            {title}
          </h3>
          <div className={`mt-2 text-sm ${styles.message}`}>
            <p>{message}</p>
          </div>
          {(showRetry || onDismiss) && (
            <div className="mt-4 flex space-x-3">
              {showRetry && onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className={`inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md ${styles.button} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500`}
                >
                  <ArrowPathIcon className="h-4 w-4 mr-2" />
                  Try Again
                </button>
              )}
              {onDismiss && (
                <button
                  type="button"
                  onClick={onDismiss}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  <XMarkIcon className="h-4 w-4 mr-2" />
                  Dismiss
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay;
