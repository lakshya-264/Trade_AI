
import React from 'react';
import StockListItem from './StockListItem';
import { cn } from '../../lib/utils';

interface Stock {
  symbol: string;
  name?: string;
}

interface StockListProps {
  stocks: Stock[];
  title?: string;
  showChange?: boolean;
  showChangePercent?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onStockClick?: (symbol: string) => void;
  showPrice?: boolean;
  showIndicator?: boolean;
  emptyMessage?: string;
}

const StockList: React.FC<StockListProps> = ({
  stocks,
  title,
  showChange = true,
  showChangePercent = true,
  size = 'md',
  className,
  onStockClick,
  showPrice = true,
  showIndicator = true,
  emptyMessage = "No stocks available"
}) => {
  if (stocks.length === 0) {
    return (
      <div className={cn("text-center py-8 text-muted-foreground", className)}>
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      {title && (
        <h3 className="text-lg font-semibold text-foreground mb-4">{title}</h3>
      )}
      {stocks.map((stock) => (
        <StockListItem
          key={stock.symbol}
          symbol={stock.symbol}
          name={stock.name}
          showChange={showChange}
          showChangePercent={showChangePercent}
          size={size}
          onClick={() => onStockClick?.(stock.symbol)}
          showPrice={showPrice}
          showIndicator={showIndicator}
        />
      ))}
    </div>
  );
};

export default StockList;
