import React, { useState, useEffect } from 'react';
import { 
  BriefcaseIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  EyeIcon,
  XMarkIcon,
  PlusIcon,
  MinusIcon,
  MagnifyingGlassIcon,
  GiftIcon,
  HomeIcon,
  ListBulletIcon,
  ClipboardDocumentListIcon,
  ChartPieIcon,
  UserIcon,
  BellIcon
} from '@heroicons/react/24/outline';
import { api, ApiError } from '../services/api';
import { toast } from 'react-hot-toast';
import { PortfolioResponse, PortfolioItem } from '../types/api';
import { useAuth } from '../context/AuthContext';

const Portfolio: React.FC = () => {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [totalValue, setTotalValue] = useState(0);
  const [totalPnL, setTotalPnL] = useState(0);
  const [totalPnLPercentage, setTotalPnLPercentage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'stocks' | 'mutual-funds' | 'gold'>('stocks');
  const [chartPeriod, setChartPeriod] = useState<'1M' | '6M' | '1Y' | 'ALL'>('1M');

  // Fetch real portfolio data
  useEffect(() => {
    const fetchPortfolioData = async () => {
      // Only fetch if user is authenticated
      if (authLoading || !isAuthenticated || !user) {
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const response: PortfolioResponse = await api.getPortfolio();
        
        if (response.portfolio && response.portfolio.length > 0) {
          setPortfolio(response.portfolio);
          setTotalValue(response.total_value || 0);
          setTotalPnL(response.total_pnl || 0);
          
          // Calculate PnL percentage
          const investedValue = totalValue - totalPnL;
          const pnlPercentage = investedValue > 0 ? (totalPnL / investedValue) * 100 : 0;
          setTotalPnLPercentage(pnlPercentage);
        } else {
          // Fallback to mock data if no portfolio
          const mockPortfolio: PortfolioItem[] = [
            {
              symbol: 'RELIANCE',
              quantity: 50,
              average_price: 2400.00,
              current_price: 2450.50,
              pnl: 2525.00,
              pnl_percent: 2.10,
              total_value: 122525.00
            },
            {
              symbol: 'TCS',
              quantity: 25,
              average_price: 3800.00,
              current_price: 3850.25,
              pnl: 1256.25,
              pnl_percent: 1.32,
              total_value: 96256.25
            }
          ];
          
          setPortfolio(mockPortfolio);
          const total = mockPortfolio.reduce((sum, item) => sum + item.total_value, 0);
          const pnl = mockPortfolio.reduce((sum, item) => sum + item.pnl, 0);
          const pnlPercentage = total > 0 ? (pnl / (total - pnl)) * 100 : 0;
          
          setTotalValue(total);
          setTotalPnL(pnl);
          setTotalPnLPercentage(pnlPercentage);
        }

      } catch (error) {
        console.error('Error fetching portfolio data:', error);
        if (error instanceof ApiError) {
          toast.error(`API Error: ${error.message}`);
        } else {
          toast.error('Failed to load portfolio data');
        }
        
        // Fallback to empty portfolio
        setPortfolio([]);
        setTotalValue(0);
        setTotalPnL(0);
        setTotalPnLPercentage(0);
      } finally {
        setLoading(false);
      }
    };

    // Gate on authentication readiness
    if (authLoading) {
      return;
    }
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    fetchPortfolioData();
  }, [authLoading, isAuthenticated, user]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const handleRemovePosition = (symbol: string) => {
    setPortfolio(prev => prev.filter(item => item.symbol !== symbol));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar with User Name and Notifications */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="h-10 w-10 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  Welcome back, {user?.username || 'User'}!
                </h1>
                <p className="text-sm text-gray-500">Track your investments</p>
              </div>
            </div>
            <button className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
              <BellIcon className="h-6 w-6" />
              <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full"></span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Portfolio Summary Card - Large and Prominent */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-xl p-8 mb-8 text-white">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-medium opacity-90 mb-2">Total Portfolio Value</h2>
              <div className="text-5xl font-bold mb-2">{formatCurrency(totalValue)}</div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm opacity-90">Today's P&L:</span>
                  <span className={`text-lg font-semibold ${totalPnL >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                    {formatCurrency(totalPnL)}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm opacity-90">Return:</span>
                  <span className={`text-lg font-semibold ${totalPnLPercentage >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                    {formatPercentage(totalPnLPercentage)}
                  </span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="h-32 w-32 bg-white bg-opacity-10 rounded-full flex items-center justify-center">
                <ChartBarIcon className="h-16 w-16 text-white opacity-50" />
              </div>
            </div>
          </div>
          
          {/* Portfolio Performance Chart Period Selector */}
          <div className="flex space-x-2">
            {(['1M', '6M', '1Y', 'ALL'] as const).map((period) => (
              <button
                key={period}
                onClick={() => setChartPeriod(period)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  chartPeriod === period
                    ? 'bg-white bg-opacity-20 text-white'
                    : 'bg-white bg-opacity-10 text-white hover:bg-opacity-20'
                }`}
              >
                {period}
              </button>
            ))}
          </div>
        </div>

        {/* Quick Action Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <button className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex flex-col items-center space-y-3">
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <PlusIcon className="h-6 w-6 text-green-600" />
              </div>
              <span className="text-sm font-medium text-gray-900">Add Funds</span>
            </div>
          </button>
          
          <button className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex flex-col items-center space-y-3">
              <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center">
                <MinusIcon className="h-6 w-6 text-red-600" />
              </div>
              <span className="text-sm font-medium text-gray-900">Withdraw</span>
            </div>
          </button>
          
          <button className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex flex-col items-center space-y-3">
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <MagnifyingGlassIcon className="h-6 w-6 text-blue-600" />
              </div>
              <span className="text-sm font-medium text-gray-900">Explore</span>
            </div>
          </button>
          
          <button className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex flex-col items-center space-y-3">
              <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
                <GiftIcon className="h-6 w-6 text-purple-600" />
              </div>
              <span className="text-sm font-medium text-gray-900">Gift Stock</span>
            </div>
          </button>
        </div>

        {/* Holdings List Section with Segmented Control */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Holdings</h2>
              <div className="flex space-x-2">
                <button className="btn-secondary">Export</button>
                <button className="btn-primary">Add Position</button>
              </div>
            </div>

            {/* Segmented Control */}
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
              {[
                { key: 'stocks', label: 'Stocks', icon: ChartBarIcon },
                { key: 'mutual-funds', label: 'Mutual Funds', icon: BriefcaseIcon },
                { key: 'gold', label: 'Gold', icon: CurrencyDollarIcon }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setSelectedTab(key as any)}
                  className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    selectedTab === key
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </button>
              ))}
            </div>

            {/* Holdings Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Company
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Current Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      P&L
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {portfolio.map((position) => (
                    <tr key={position.symbol} className="hover:bg-gray-50">
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
                        <div className="text-sm text-gray-900">{formatCurrency(position.current_price)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <div className={`text-sm font-medium ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(position.pnl)}
                          </div>
                          <div className={`text-xs ${position.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatPercentage(position.pnl_percent)}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{formatCurrency(position.total_value)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button className="text-blue-600 hover:text-blue-900">Edit</button>
                          <button 
                            onClick={() => handleRemovePosition(position.symbol)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Portfolio Performance Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Portfolio Performance</h2>
            <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Portfolio performance chart will be displayed here</p>
                <p className="text-sm text-gray-400 mt-2">Period: {chartPeriod}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Navigation Bar - Mobile Only */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 lg:hidden">
        <div className="flex items-center justify-around py-2">
          <button className="flex flex-col items-center space-y-1 p-2 text-blue-600">
            <HomeIcon className="h-6 w-6" />
            <span className="text-xs font-medium">Home</span>
          </button>
          <button className="flex flex-col items-center space-y-1 p-2 text-gray-400">
            <ListBulletIcon className="h-6 w-6" />
            <span className="text-xs font-medium">Watchlist</span>
          </button>
          <button className="flex flex-col items-center space-y-1 p-2 text-gray-400">
            <ClipboardDocumentListIcon className="h-6 w-6" />
            <span className="text-xs font-medium">Orders</span>
          </button>
          <button className="flex flex-col items-center space-y-1 p-2 text-gray-400">
            <ChartPieIcon className="h-6 w-6" />
            <span className="text-xs font-medium">Insights</span>
          </button>
          <button className="flex flex-col items-center space-y-1 p-2 text-gray-400">
            <UserIcon className="h-6 w-6" />
            <span className="text-xs font-medium">Profile</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Portfolio;
