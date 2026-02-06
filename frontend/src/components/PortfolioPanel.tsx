/**
 * Portfolio Panel Component
 * Displays portfolio holdings, P&L, and performance for Comprehensive Trading Pro
 */

import React, { useState, useEffect } from 'react';
import {
  BriefcaseIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  XMarkIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import { httpClient } from '../config/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-hot-toast';
import ClickableSymbol from './ClickableSymbol';

interface PortfolioPanelProps {
  visible?: boolean;
  onClose?: () => void;
  className?: string;
}

interface PortfolioItem {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  total_value: number;
}

interface PortfolioData {
  portfolio: PortfolioItem[];
  total_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  available_balance: number;
  invested_value: number;
}

const PortfolioPanel: React.FC<PortfolioPanelProps> = ({
  visible = true,
  onClose,
  className = ''
}) => {
  const { user, isAuthenticated } = useAuth();
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(true);

  useEffect(() => {
    if (visible && isAuthenticated && user) {
      fetchPortfolio();
    }
  }, [visible, isAuthenticated, user]);

  const fetchPortfolio = async () => {
    setLoading(true);
    try {
      const response = await httpClient.get<PortfolioData>('/api/trading/portfolio');
      if (response.data && Array.isArray(response.data.portfolio)) {
        setPortfolio(response.data);
      } else {
        // Use empty portfolio if no data
        const emptyPortfolio: PortfolioData = {
          portfolio: [],
          total_value: 0,
          total_pnl: 0,
          total_pnl_percent: 0,
          available_balance: 1000000,
          invested_value: 0
        };
        setPortfolio(emptyPortfolio);
      }
    } catch (error: any) {
      console.error('Error fetching portfolio:', error);
      // Use empty portfolio for demo
      const emptyPortfolio: PortfolioData = {
        portfolio: [],
        total_value: 0,
        total_pnl: 0,
        total_pnl_percent: 0,
        available_balance: 1000000,
        invested_value: 0
      };
      setPortfolio(emptyPortfolio);
    } finally {
      setLoading(false);
    }
  };

  if (!visible) return null;

  if (!isAuthenticated) {
    return (
      <div className={`bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4 ${className}`}>
        <div className="text-center text-gray-400 py-8">
          <BriefcaseIcon className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p>Please login to view portfolio</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-[#2a2e39] rounded w-1/3"></div>
          <div className="h-4 bg-[#2a2e39] rounded"></div>
          <div className="h-4 bg-[#2a2e39] rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  const data = portfolio || {
    portfolio: [],
    total_value: 0,
    total_pnl: 0,
    total_pnl_percent: 0,
    available_balance: 1000000,
    invested_value: 0
  };

  return (
    <div className={`bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[#2a2e39]">
        <div className="flex items-center gap-2">
          <BriefcaseIcon className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Portfolio</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-gray-400 hover:text-white transition-colors"
            title={showDetails ? 'Hide details' : 'Show details'}
          >
            {showDetails ? <EyeIcon className="w-5 h-5" /> : <EyeSlashIcon className="w-5 h-5" />}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="p-4 space-y-4">
        {/* Total Value */}
        <div className="bg-[#131722] border border-[#2a2e39] rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Total Portfolio Value</span>
            <CurrencyDollarIcon className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            ₹{data.total_value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        {/* P&L */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-[#131722] border border-[#2a2e39] rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">Total P&L</div>
            <div className={`text-lg font-semibold ${
              data.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {data.total_pnl >= 0 ? '+' : ''}₹{Math.abs(data.total_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
          <div className="bg-[#131722] border border-[#2a2e39] rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">P&L %</div>
            <div className={`text-lg font-semibold ${
              data.total_pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {data.total_pnl_percent >= 0 ? '+' : ''}{data.total_pnl_percent.toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Available Balance */}
        <div className="bg-[#131722] border border-[#2a2e39] rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm text-gray-400">Available Balance</span>
              <p className="text-xs text-gray-500 mt-0.5">Demo Trading Mode</p>
            </div>
            <span className="text-lg font-semibold text-white">
              ₹{data.available_balance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>

        {/* Holdings List */}
        {showDetails && (
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-white">Holdings ({data.portfolio.length})</h4>
            </div>
            
            {data.portfolio.length === 0 ? (
              <div className="text-center text-gray-400 py-8 text-sm">
                <ChartBarIcon className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                <p>No holdings yet</p>
                <p className="text-xs mt-1">Start trading to build your portfolio</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {data.portfolio.map((item, index) => (
                  <div
                    key={index}
                    className="bg-[#131722] border border-[#2a2e39] rounded-lg p-3 hover:border-blue-500/50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <ClickableSymbol symbol={item.symbol} variant="bold" />
                      <span className={`text-sm font-medium ${
                        item.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {item.pnl >= 0 ? '+' : ''}₹{Math.abs(item.pnl).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-400">Qty: </span>
                        <span className="text-white">{item.quantity}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Avg: </span>
                        <span className="text-white">₹{item.average_price.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">LTP: </span>
                        <span className="text-white">₹{item.current_price.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">P&L%: </span>
                        <span className={item.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}>
                          {item.pnl_percent >= 0 ? '+' : ''}{item.pnl_percent.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioPanel;

