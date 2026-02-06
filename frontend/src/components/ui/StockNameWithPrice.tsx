import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { formatINR } from '../../utils/currency';
import { cn } from '../../lib/utils';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';

interface StockNameWithPriceProps {
  symbol: string;
  name?: string;
  showChange?: boolean;
  showChangePercent?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
  showPrice?: boolean;
}

const StockNameWithPrice: React.FC<StockNameWithPriceProps> = ({
  symbol,
  name,
  showChange = true,
  showChangePercent = true,
  size = 'md',
  className,
  onClick,
  showPrice = true
}) => {
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchQuote = async () => {
      try {
        setLoading(true);
        const data = await api.getQuote(symbol);
        setQuote(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch price');
        console.error(`Failed to fetch quote for ${symbol}:`, err);
      } finally {
        setLoading(false);
      }
    };

    if (showPrice) {
      fetchQuote();
    }
  }, [symbol, showPrice]);

  const sizeClasses = {
    sm: {
      symbol: 'text-sm font-medium',
      name: 'text-xs text-muted-foreground',
      price: 'text-sm font-semibold',
      change: 'text-xs'
    },
    md: {
      symbol: 'text-base font-semibold',
      name: 'text-sm text-muted-foreground',
      price: 'text-lg font-bold',
      change: 'text-sm'
    },
    lg: {
      symbol: 'text-lg font-bold',
      name: 'text-base text-muted-foreground',
      price: 'text-xl font-bold',
      change: 'text-base'
    }
  };

  const classes = sizeClasses[size];

  const isPositive = quote?.change >= 0;
  const isNegative = quote?.change < 0;

  return (
    <div 
      className={cn(
        "flex items-center justify-between",
        onClick && "cursor-pointer hover:bg-muted/30 p-2 rounded transition-colors",
        className
      )}
      onClick={onClick}
    >
      <div className="flex-1 min-w-0">
        <div className={cn(classes.symbol, "text-foreground truncate")}>
          {symbol}
        </div>
        {name && (
          <div className={cn(classes.name, "truncate")}>
            {name}
          </div>
        )}
      </div>
      
      {showPrice && (
        <div className="text-right ml-3">
          {loading ? (
            <div className="animate-pulse">
              <div className="h-4 bg-muted rounded w-16 mb-1"></div>
              <div className="h-3 bg-muted rounded w-12"></div>
            </div>
          ) : error ? (
            <div className="text-muted-foreground text-xs">
              Price unavailable
            </div>
          ) : quote ? (
            <>
              <div className={cn(classes.price, "text-foreground")}>
                {formatINR(quote.last_price || 0)}
              </div>
              {(showChange || showChangePercent) && (
                <div className={cn(
                  classes.change,
                  "flex items-center justify-end",
                  isPositive ? 'text-success-600' : 'text-danger-600'
                )}>
                  {isPositive ? (
                    <ArrowTrendingUpIcon className="h-3 w-3 mr-1" />
                  ) : (
                    <ArrowTrendingDownIcon className="h-3 w-3 mr-1" />
                  )}
                  <span>
                    {showChange && (
                      <span>
                        {isPositive ? '+' : ''}₹{Math.abs(quote.change || 0).toFixed(2)}
                      </span>
                    )}
                    {showChange && showChangePercent && ' '}
                    {showChangePercent && (
                      <span>
                        ({isPositive ? '+' : ''}{(quote.change_percent || 0).toFixed(2)}%)
                      </span>
                    )}
                  </span>
                </div>
              )}
            </>
          ) : (
            <div className="text-muted-foreground text-xs">
              No data
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StockNameWithPrice;
