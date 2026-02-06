import React from 'react';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';

interface StockCardProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
  marketCap?: number;
  className?: string;
}

const StockCard: React.FC<StockCardProps> = ({
  symbol,
  name,
  price,
  change,
  changePercent,
  volume,
  marketCap,
  className
}) => {
  const isPositive = change >= 0;
  const isNegative = change < 0;

  return (
    <div className={cn(
      "bg-card border border-border rounded-lg p-4 hover:shadow-md transition-all duration-200",
      "hover:border-primary/20 hover:scale-[1.02]",
      className
    )}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-foreground text-lg">{symbol}</h3>
          <p className="text-sm text-muted-foreground truncate max-w-[200px]">{name}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-foreground">
            ₹{price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <div className={cn(
          "flex items-center space-x-1 px-2 py-1 rounded-full text-sm font-medium",
          isPositive ? "bg-success/10 text-success-600" : "bg-danger/10 text-danger-600"
        )}>
          {isPositive ? (
            <ArrowTrendingUpIcon className="h-4 w-4" />
          ) : (
            <ArrowTrendingDownIcon className="h-4 w-4" />
          )}
          <span>
            {isPositive ? '+' : ''}₹{Math.abs(change).toFixed(2)}
          </span>
          <span>
            ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
          </span>
        </div>
      </div>

      {(volume || marketCap) && (
        <div className="pt-3 border-t border-border">
          <div className="grid grid-cols-2 gap-4 text-sm">
            {volume && (
              <div>
                <p className="text-muted-foreground">Volume</p>
                <p className="font-medium text-foreground">
                  {volume.toLocaleString('en-IN')}
                </p>
              </div>
            )}
            {marketCap && (
              <div>
                <p className="text-muted-foreground">Market Cap</p>
                <p className="font-medium text-foreground">
                  ₹{(marketCap / 10000000).toFixed(1)}Cr
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StockCard;
