import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { formatCurrency, formatPercentage } from '../../utils/currency';

interface PortfolioPosition {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  total_value: number;
}

interface RealTimePortfolioRowProps {
  position: PortfolioPosition;
  onRemove: (symbol: string) => void;
}

const RealTimePortfolioRow: React.FC<RealTimePortfolioRowProps> = ({ position, onRemove }) => {
  const [currentQuote, setCurrentQuote] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCurrentPrice = async () => {
      try {
        setLoading(true);
        const quote = await api.getQuote(position.symbol);
        setCurrentQuote(quote);
      } catch (error) {
        console.error(`Failed to fetch current price for ${position.symbol}:`, error);
        // Keep using the position's current_price as fallback
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentPrice();
  }, [position.symbol]);

  // Calculate P&L with real-time price
  const realTimePrice = currentQuote?.last_price || position.current_price;
  const realTimePnl = (realTimePrice - position.average_price) * position.quantity;
  const realTimePnlPercent = ((realTimePrice - position.average_price) / position.average_price) * 100;
  const realTimeTotalValue = realTimePrice * position.quantity;

  const isPositive = realTimePnl >= 0;

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-xs font-medium text-blue-600">
              {position.symbol.charAt(0)}
            </span>
          </div>
          <div className="text-sm font-medium text-gray-900">{position.symbol}</div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">{position.symbol}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">{position.quantity}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">{formatCurrency(position.average_price)}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">
          {loading ? (
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-16"></div>
            </div>
          ) : (
            <div className="flex items-center">
              <span>{formatCurrency(realTimePrice)}</span>
              {currentQuote && (
                <span className={`ml-2 text-xs ${
                  currentQuote.change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {currentQuote.change >= 0 ? '+' : ''}{currentQuote.change_percent?.toFixed(2)}%
                </span>
              )}
            </div>
          )}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex flex-col">
          <div className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {loading ? (
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-16"></div>
              </div>
            ) : (
              formatCurrency(realTimePnl)
            )}
          </div>
          <div className={`text-xs ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {loading ? (
              <div className="animate-pulse">
                <div className="h-3 bg-gray-200 rounded w-12"></div>
              </div>
            ) : (
              formatPercentage(realTimePnlPercent)
            )}
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">
          {loading ? (
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-20"></div>
            </div>
          ) : (
            formatCurrency(realTimeTotalValue)
          )}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        <div className="flex space-x-2">
          <button className="text-blue-600 hover:text-blue-900">Edit</button>
          <button 
            onClick={() => onRemove(position.symbol)}
            className="text-red-600 hover:text-red-900"
          >
            Remove
          </button>
        </div>
      </td>
    </tr>
  );
};

export default RealTimePortfolioRow;
