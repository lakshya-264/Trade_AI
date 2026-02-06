import React, { Suspense, lazy, ComponentType } from 'react';
import LoadingSpinner from './LoadingSpinner';

interface LazyWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  delay?: number;
}

// Error boundary for chunk loading
class ChunkErrorBoundary extends React.Component<any, { hasError: boolean }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    // Check if it's a chunk loading error
    if (error.message && error.message.includes('Loading chunk')) {
      return { hasError: true };
    }
    return null;
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Chunk loading error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Loading Error
            </h2>
            <p className="text-gray-600 mb-4">
              Failed to load component. Please refresh the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for lazy loading with error handling
export const withLazyLoad = <P extends object>(
  Component: ComponentType<P>,
  fallback?: React.ReactNode
) => {
  return React.forwardRef<any, P>((props, ref) => (
    <ChunkErrorBoundary>
      <Suspense fallback={fallback || <LoadingSpinner size="md" text="Loading..." />}>
        <Component {...(props as P)} />
      </Suspense>
    </ChunkErrorBoundary>
  ));
};

// Lazy wrapper component with error handling
const LazyWrapper: React.FC<LazyWrapperProps> = ({ 
  children, 
  fallback = <LoadingSpinner size="md" text="Loading..." /> 
}) => {
  return (
    <ChunkErrorBoundary>
      <Suspense fallback={fallback}>
        {children}
      </Suspense>
    </ChunkErrorBoundary>
  );
};

// Lazy load pages with retry mechanism
const lazyWithRetry = (importFunc: () => Promise<any>) => {
  return lazy(() => {
    return importFunc().catch((error) => {
      console.error('Chunk loading failed, retrying...', error);
      // Retry once
      return importFunc();
    });
  });
};

export const LazyDashboard = lazyWithRetry(() => import('../pages/Dashboard'));
export const LazyTrading = lazyWithRetry(() => import('../pages/Trading'));
export const LazyPortfolio = lazyWithRetry(() => import('../pages/Portfolio'));
export const LazySettings = lazyWithRetry(() => import('../pages/Settings'));

// Lazy load heavy components
export const LazyChart = lazyWithRetry(() => import('./ResponsiveChart'));
export const LazyDataTable = lazyWithRetry(() => import('./DataTable'));

export default LazyWrapper;
