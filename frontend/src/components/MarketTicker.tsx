import React, { useState, useEffect } from 'react';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import { MarketTickerLoadingState } from './LoadingStates';

interface MarketIndex {
  name: string;
  value: number;
  change: number;
  changePercent: number;
}

const MarketTicker: React.FC = () => {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading data
    const loadData = async () => {
      setLoading(true);
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setIndices([
        { name: 'NIFTY 50', value: 24654.70, change: -236.15, changePercent: -0.95 },
        { name: 'SENSEX', value: 80847.25, change: -789.45, changePercent: -0.97 },
        { name: 'NIFTY BANK', value: 51234.50, change: -456.78, changePercent: -0.88 },
        { name: 'NIFTY IT', value: 34567.89, change: 123.45, changePercent: 0.36 },
      ]);
      setLoading(false);
    };

    loadData();
  }, []);

  useEffect(() => {
    if (indices.length === 0) return;
    
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % indices.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [indices.length]);

  if (loading) {
    return <MarketTickerLoadingState />;
  }

  const current = indices[currentIndex];
  const isPositive = current.change >= 0;

  return (
    <div className="flex items-center space-x-4 bg-card border border-border rounded-lg px-4 py-2">
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
        <span className="text-sm font-medium text-muted-foreground">LIVE</span>
      </div>
      
      <div className="flex items-center space-x-3">
        <span className="text-sm font-semibold text-foreground">{current.name}</span>
        <span className="text-lg font-bold text-foreground">
          {current.value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
        </span>
        <div className={cn(
          "flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium",
          isPositive ? "bg-success/10 text-success-600" : "bg-danger/10 text-danger-600"
        )}>
          {isPositive ? (
            <ArrowTrendingUpIcon className="h-3 w-3" />
          ) : (
            <ArrowTrendingDownIcon className="h-3 w-3" />
          )}
          <span>
            {isPositive ? '+' : ''}{current.change.toFixed(2)}
          </span>
          <span>
            ({isPositive ? '+' : ''}{current.changePercent.toFixed(2)}%)
          </span>
        </div>
      </div>

      <div className="flex space-x-1">
        {indices.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={cn(
              "w-2 h-2 rounded-full transition-colors",
              index === currentIndex ? "bg-primary" : "bg-muted-foreground/30"
            )}
          />
        ))}
      </div>
    </div>
  );
};

export default MarketTicker;
