import React from 'react';
import BuySellButton from './BuySellButton';

export interface StockCardProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  sector?: string;
  volume?: number;
  marketCap?: string;
  onClick?: () => void;
  onAddToWatchlist?: () => void;
  onOrderPlaced?: () => void;
}

const StockCard: React.FC<StockCardProps> = ({
  symbol,
  name,
  price,
  change,
  changePercent,
  sector,
  volume,
  marketCap,
  onClick,
  onAddToWatchlist,
  onOrderPlaced,
}) => {
  const isPositive = change >= 0;
  const changeColor = isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
  const bgGradient = isPositive 
    ? 'from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20' 
    : 'from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20';
  
  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-200 dark:border-gray-700 group cursor-pointer transform hover:-translate-y-1"
    >
      {/* Header */}
      <div className="p-4 pb-3">
        <div className="flex justify-between items-start mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white truncate">
              {symbol}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
              {name}
            </p>
          </div>
          <button 
            onClick={(e) => {
              e.stopPropagation();
              onAddToWatchlist?.();
            }}
            className="ml-2 text-gray-300 hover:text-yellow-500 dark:text-gray-600 dark:hover:text-yellow-400 transition-colors text-lg"
            title="Add to Watchlist"
          >
            ⭐
          </button>
        </div>
        
        {/* Sector Tag */}
        {sector && (
          <div className="mb-3">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
              🏷️ {sector}
            </span>
          </div>
        )}
      </div>
      
      {/* Price Section with Gradient Background */}
      <div className={`px-4 py-3 bg-gradient-to-r ${bgGradient}`}>
        <div className="flex items-baseline justify-between">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            ₹{price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className={`text-sm font-bold ${changeColor} flex items-center gap-1`}>
            <span className="text-base">{isPositive ? '↗' : '↘'}</span>
            <span>
              {isPositive ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>
      
      {/* Stats */}
      {(volume !== undefined || marketCap) && (
        <div className="px-4 py-3 flex justify-between text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/50">
          {volume !== undefined && (
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Vol:</span>{' '}
              <span className="font-semibold">{(volume / 1000000).toFixed(2)}M</span>
            </div>
          )}
          {marketCap && (
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">MCap:</span>{' '}
              <span className="font-semibold">{marketCap}</span>
            </div>
          )}
        </div>
      )}
      
      {/* Actions */}
      <div className="p-3 flex gap-2">
        <button 
          onClick={(e) => {
            e.stopPropagation();
            onClick?.();
          }}
          className="flex-1 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-all duration-200 flex items-center justify-center gap-1 shadow-sm hover:shadow-md"
        >
          <span>📊</span>
          <span>Chart</span>
        </button>
        <div className="flex-1" onClick={(e) => e.stopPropagation()}>
          <BuySellButton
            symbol={symbol}
            currentPrice={price}
            size="sm"
            onOrderPlaced={onOrderPlaced}
          />
        </div>
        <button 
          onClick={(e) => {
            e.stopPropagation();
            onAddToWatchlist?.();
          }}
          className="py-2 px-3 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md"
          title="Add to Watchlist"
        >
          ➕
        </button>
      </div>
    </div>
  );
};

export default StockCard;

