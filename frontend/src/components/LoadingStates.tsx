import React from 'react';
import { Skeleton, SkeletonCard, SkeletonStockCard, SkeletonChart, SkeletonTable, SkeletonNewsItem, SkeletonMarketTicker } from './ui/Skeleton';

export const DashboardLoadingState: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-8 w-24 rounded-full" />
      </div>

      {/* Portfolio Summary Cards Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <Skeleton className="h-8 w-8 rounded" />
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-6 w-24" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Chart Skeleton */}
      <div className="bg-card border border-border rounded-lg p-6">
        <SkeletonChart />
      </div>

      {/* Market Overview Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-card border border-border rounded-lg p-6">
          <Skeleton className="h-6 w-32 mb-4" />
          <SkeletonTable rows={5} columns={1} />
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <Skeleton className="h-6 w-32 mb-4" />
          <SkeletonTable rows={5} columns={1} />
        </div>
      </div>

      {/* Stock Cards Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-lg">
            <SkeletonStockCard />
          </div>
        ))}
      </div>

      {/* News Feed Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-24" />
            </div>
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <SkeletonNewsItem key={i} />
              ))}
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <div className="bg-card border border-border rounded-lg p-6">
            <Skeleton className="h-6 w-32 mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex justify-between items-center">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-12" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const StockCardLoadingState: React.FC<{ count?: number }> = ({ count = 4 }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-card border border-border rounded-lg">
          <SkeletonStockCard />
        </div>
      ))}
    </div>
  );
};

export const NewsFeedLoadingState: React.FC = () => {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonNewsItem key={i} />
        ))}
      </div>
    </div>
  );
};

export const MarketTickerLoadingState: React.FC = () => {
  return (
    <div className="bg-muted/30 border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
        <SkeletonMarketTicker />
      </div>
    </div>
  );
};

export const ChartLoadingState: React.FC<{ height?: number }> = ({ height = 300 }) => {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-8 w-24 rounded-full" />
      </div>
      <div style={{ height }} className="w-full">
        <Skeleton className="h-full w-full" />
      </div>
    </div>
  );
};

export const TableLoadingState: React.FC<{ 
  rows?: number; 
  columns?: number; 
  showHeader?: boolean 
}> = ({ rows = 5, columns = 4, showHeader = true }) => {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      {showHeader && <Skeleton className="h-6 w-32 mb-4" />}
      <SkeletonTable rows={rows} columns={columns} />
    </div>
  );
};
