import React from 'react';

interface LoadingSkeletonProps {
  className?: string;
  height?: string;
  width?: string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ 
  className = '', 
  height = 'h-4', 
  width = 'w-full' 
}) => {
  return (
    <div 
      className={`${width} ${height} bg-gray-700/50 rounded animate-pulse ${className}`}
      aria-label="Loading..."
    />
  );
};

export const LoadingSpinner: React.FC<{ size?: string; className?: string }> = ({ 
  size = 'h-8 w-8', 
  className = '' 
}) => {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div className={`${size} border-2 border-blue-500 border-t-transparent rounded-full animate-spin`} />
    </div>
  );
};

export const ComponentLoader: React.FC<{ message?: string }> = ({ 
  message = 'Loading...' 
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <LoadingSpinner />
      <p className="mt-4 text-gray-400 text-sm">{message}</p>
    </div>
  );
};

export default LoadingSkeleton;
