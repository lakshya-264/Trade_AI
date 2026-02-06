import React from 'react';
import { cn } from '../../lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'default' | 'circular' | 'rectangular';
  animation?: 'pulse' | 'wave' | 'none';
}

const Skeleton: React.FC<SkeletonProps> = ({ 
  className, 
  variant = 'default',
  animation = 'pulse' 
}) => {
  const baseClasses = "bg-muted animate-pulse";
  
  const variantClasses = {
    default: "rounded-md",
    circular: "rounded-full",
    rectangular: "rounded-none"
  };

  const animationClasses = {
    pulse: "animate-pulse",
    wave: "animate-pulse",
    none: ""
  };

  return (
    <div
      className={cn(
        baseClasses,
        variantClasses[variant],
        animationClasses[animation],
        className
      )}
    />
  );
};

// Pre-built skeleton components for common use cases
export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("p-4 space-y-3", className)}>
    <Skeleton className="h-4 w-3/4" />
    <Skeleton className="h-4 w-1/2" />
    <Skeleton className="h-8 w-1/3" />
  </div>
);

export const SkeletonStockCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("p-4 space-y-3", className)}>
    <div className="flex justify-between items-start">
      <div className="space-y-2">
        <Skeleton className="h-5 w-16" />
        <Skeleton className="h-4 w-24" />
      </div>
      <Skeleton className="h-6 w-20" />
    </div>
    <div className="flex justify-between items-center">
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
    <div className="pt-3 border-t border-border">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-4 w-16" />
        </div>
        <div className="space-y-1">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-4 w-20" />
        </div>
      </div>
    </div>
  </div>
);

export const SkeletonChart: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("p-4 space-y-4", className)}>
    <div className="flex justify-between items-center">
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-8 w-24 rounded-full" />
    </div>
    <div className="h-64 w-full">
      <Skeleton className="h-full w-full" />
    </div>
  </div>
);

export const SkeletonTable: React.FC<{ 
  rows?: number; 
  columns?: number; 
  className?: string 
}> = ({ rows = 5, columns = 4, className }) => (
  <div className={cn("space-y-3", className)}>
    {/* Header */}
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div key={rowIndex} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, colIndex) => (
          <Skeleton key={colIndex} className="h-4 w-full" />
        ))}
      </div>
    ))}
  </div>
);

export const SkeletonNewsItem: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("p-4 space-y-3", className)}>
    <div className="flex items-center space-x-2">
      <Skeleton className="h-4 w-4 rounded-full" />
      <Skeleton className="h-4 w-16 rounded-full" />
      <Skeleton className="h-4 w-20 rounded-full" />
    </div>
    <Skeleton className="h-5 w-3/4" />
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-2/3" />
    <div className="flex justify-between items-center">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-3 w-16" />
    </div>
  </div>
);

export const SkeletonMarketTicker: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("flex items-center space-x-4 p-2", className)}>
    <div className="flex items-center space-x-2">
      <Skeleton className="h-4 w-4 rounded-full" />
      <Skeleton className="h-4 w-12" />
    </div>
    <div className="flex items-center space-x-3">
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-5 w-20" />
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
    <div className="flex space-x-1">
      <Skeleton className="h-2 w-2 rounded-full" />
      <Skeleton className="h-2 w-2 rounded-full" />
      <Skeleton className="h-2 w-2 rounded-full" />
    </div>
  </div>
);

export { Skeleton };
export default Skeleton;
