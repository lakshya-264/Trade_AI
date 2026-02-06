import React, { useState, useEffect } from 'react';
import { 
  ArrowTrendingUpIcon, 
  CurrencyDollarIcon,
  ChartBarIcon,
  EyeIcon,
  SparklesIcon,
  FireIcon,
  BoltIcon
} from '@heroicons/react/24/outline';
import { useWebSocket } from '../context/WebSocketContext';
import { useAuth } from '../context/AuthContext';
import { ApiError, NetworkError, TimeoutError } from '../services/api';
import { cachedApi } from '../services/cachedApi';
import { toast } from 'react-hot-toast';
import { PortfolioResponse, TopGainerLoser } from '../types/api';
import { formatINR, formatINRCompact } from '../utils/currency';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorDisplay from '../components/ErrorDisplay';
import ResponsiveCard from '../components/ResponsiveCard';
import ResponsiveChart from '../components/ResponsiveChart';
import RealTimeStockCard from '../components/ui/RealTimeStockCard';
import NewsFeed from '../components/NewsFeed';
import LiveMarketData from '../components/LiveMarketData';
import IndexConstituentsView from '../components/IndexConstituentsView';
import { DashboardLoadingState, StockCardLoadingState } from '../components/LoadingStates';
import { useRetry } from '../hooks/useRetry';
import { usePerformanceMonitor } from '../hooks/usePerformanceMonitor';
import { useDebounce } from '../hooks/useDebounce';

const Dashboard: React.FC = () => {
  const { isConnected, lastMessage } = useWebSocket();
  const { isAuthenticated, user } = useAuth();
  const [marketData, setMarketData] = useState<any[]>([]);
  const [topGainers, setTopGainers] = useState<TopGainerLoser[]>([]);
  const [topLosers, setTopLosers] = useState<TopGainerLoser[]>([]);
  const [portfolioValue, setPortfolioValue] = useState(0);
  const [todayPnL, setTodayPnL] = useState(0);
  const [marketSummary, setMarketSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'error' | 'warning' | 'info'>('error');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Performance monitoring
  const { 
    startMonitoring, 
    stopMonitoring, 
    trackRenderTime, 
    trackCacheMiss
  } = usePerformanceMonitor({
    trackMemory: true,
    trackNetwork: true,
    trackCache: true
  });

  // Debounced refresh trigger
  const debouncedRefreshTrigger = useDebounce(refreshTrigger, 1000);

  const { executeWithRetry, isRetrying, retryCount } = useRetry({
    maxRetries: 3,
    retryDelay: 1000,
    onRetry: (attempt) => {
      console.log(`Retrying API call (attempt ${attempt})`);
    },
    onMaxRetriesReached: () => {
      toast.error('Maximum retry attempts reached. Please check your connection.');
    }
  });

  // Fetch real data from API with caching
  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!isAuthenticated) {
        setLoading(false);
        return;
      }

      const startTime = performance.now();
      startMonitoring();

      try {
        setLoading(true);
        setError(null);
        
        // Fetch portfolio data with caching
        const portfolioResponse = await executeWithRetry(() => {
          trackCacheMiss();
          return cachedApi.getPortfolio();
        }) as PortfolioResponse;
        setPortfolioValue(portfolioResponse.total_value || 0);
        setTodayPnL(portfolioResponse.total_pnl || 0);

        // Fetch market summary and top gainers/losers with caching
        const [marketSummaryResponse, gainersResponse, losersResponse] = await Promise.all([
          executeWithRetry(() => {
            trackCacheMiss();
            return cachedApi.getMarketSummary();
          }),
          executeWithRetry(() => {
            trackCacheMiss();
            return cachedApi.getTopGainers();
          }),
          executeWithRetry(() => {
            trackCacheMiss();
            return cachedApi.getTopLosers();
          })
        ]);
        
        setMarketSummary(marketSummaryResponse);
        setTopGainers((gainersResponse as TopGainerLoser[]) || []);
        setTopLosers((losersResponse as TopGainerLoser[]) || []);

        // Generate portfolio performance chart data
        if (portfolioResponse.portfolio && portfolioResponse.portfolio.length > 0) {
          const chartData = portfolioResponse.portfolio.map((item, index: number) => ({
            date: new Date(Date.now() - (portfolioResponse.portfolio.length - index - 1) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            value: item.total_value || 0,
            volume: item.quantity || 0
          }));
          setMarketData(chartData);
        } else {
          // Fallback to mock data if no portfolio data
          const generateMockData = () => {
            const data = [];
            const now = new Date();
            for (let i = 29; i >= 0; i--) {
              const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
              data.push({
                date: date.toISOString().split('T')[0],
                value: 50000 + Math.random() * 10000 + i * 100,
                volume: Math.floor(Math.random() * 1000000) + 100000
              });
            }
            return data;
          };
          setMarketData(generateMockData());
        }

        // Track performance
        trackRenderTime('Dashboard', startTime);
        stopMonitoring();

      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        
        let errorMessage = 'Failed to load dashboard data';
        let errorType: 'error' | 'warning' | 'info' = 'error';
        
        if (error instanceof ApiError) {
          if (error.status === 401) {
            errorMessage = 'Authentication failed. Please login again.';
            errorType = 'warning';
          } else if (error.status === 403) {
            errorMessage = 'Access denied. You do not have permission to view this data.';
            errorType = 'warning';
          } else if (error.status >= 500) {
            errorMessage = 'Server error. Please try again later.';
            errorType = 'error';
          } else {
            errorMessage = `API Error: ${error.message}`;
          }
        } else if (error instanceof NetworkError) {
          errorMessage = 'Network error. Please check your internet connection.';
          errorType = 'warning';
        } else if (error instanceof TimeoutError) {
          errorMessage = 'Request timed out. Please try again.';
          errorType = 'warning';
        }
        
        setError(errorMessage);
        setErrorType(errorType);
        toast.error(errorMessage);
        
        // Fallback to mock data on error
        setPortfolioValue(125000);
        setTodayPnL(2500);
        setTopGainers([
          { symbol: 'RELIANCE', name: 'Reliance Industries', change: 2.5, change_percent: 2.5, price: 2450.50, volume: 1000000, market_cap: 16500000000000 },
          { symbol: 'TCS', name: 'Tata Consultancy Services', change: 1.8, change_percent: 1.8, price: 3850.25, volume: 800000, market_cap: 14000000000000 },
          { symbol: 'HDFC', name: 'HDFC Bank', change: 1.5, change_percent: 1.5, price: 1650.75, volume: 1200000, market_cap: 12000000000000 },
          { symbol: 'INFY', name: 'Infosys', change: 1.2, change_percent: 1.2, price: 1450.30, volume: 900000, market_cap: 6000000000000 },
          { symbol: 'ITC', name: 'ITC Limited', change: 0.9, change_percent: 0.9, price: 425.60, volume: 1500000, market_cap: 5000000000000 }
        ]);
        setTopLosers([
          { symbol: 'BHARTI', name: 'Bharti Airtel', change: -2.1, change_percent: -2.1, price: 850.40, volume: 1100000, market_cap: 4800000000000 },
          { symbol: 'SBI', name: 'State Bank of India', change: -1.8, change_percent: -1.8, price: 520.25, volume: 2000000, market_cap: 4600000000000 },
          { symbol: 'ONGC', name: 'Oil and Natural Gas Corp', change: -1.5, change_percent: -1.5, price: 180.75, volume: 3000000, market_cap: 2200000000000 },
          { symbol: 'NTPC', name: 'NTPC Limited', change: -1.2, change_percent: -1.2, price: 165.30, volume: 2500000, market_cap: 1600000000000 },
          { symbol: 'POWERGRID', name: 'Power Grid Corporation', change: -0.9, change_percent: -0.9, price: 225.60, volume: 1800000, market_cap: 2100000000000 }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [isAuthenticated, executeWithRetry, debouncedRefreshTrigger, startMonitoring, stopMonitoring, trackCacheMiss, trackRenderTime]);

  // Update data when WebSocket message is received
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'price_update') {
      // Update market data with new price
      setMarketData(prev => {
        const newData = [...prev];
        const lastData = newData[newData.length - 1];
        newData[newData.length - 1] = {
          ...lastData,
          value: lastMessage.data.last_price || lastData.value
        };
        return newData;
      });
    }
  }, [lastMessage]);

  const formatCurrency = (value: number) => {
    return formatINR(value);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center max-w-md">
          <div className="mb-6">
            <div className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
              <ChartBarIcon className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              Welcome to Trader AI
            </h2>
            <p className="text-gray-600 dark:text-gray-400">Please login to view your dashboard and trading data.</p>
          </div>
          
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-6 mb-6 border border-blue-200 dark:border-blue-800">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Features Available After Login:</h3>
            <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-2">
              <li className="flex items-center gap-2">
                <SparklesIcon className="h-4 w-4 text-blue-600" />
                <span>Real-time portfolio tracking</span>
              </li>
              <li className="flex items-center gap-2">
                <BoltIcon className="h-4 w-4 text-purple-600" />
                <span>Market data and analytics</span>
              </li>
              <li className="flex items-center gap-2">
                <FireIcon className="h-4 w-4 text-orange-600" />
                <span>AI-powered trading signals</span>
              </li>
              <li className="flex items-center gap-2">
                <ChartBarIcon className="h-4 w-4 text-green-600" />
                <span>Risk management tools</span>
              </li>
            </ul>
          </div>
          
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <p>Click the "Login" button in the header to get started.</p>
          </div>
        </div>
      </div>
    );
  }

  const handleRetry = () => {
    setError(null);
    window.location.reload();
  };

  const handleDismissError = () => {
    setError(null);
  };

  if (loading) {
    return <DashboardLoadingState />;
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        </div>
        
        <ErrorDisplay
          title="Failed to Load Dashboard"
          message={error}
          type={errorType}
          onRetry={handleRetry}
          onDismiss={handleDismissError}
          showRetry={true}
        />
        
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
          <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
            Showing Demo Data
          </h3>
          <p className="text-sm text-yellow-700 dark:text-yellow-300">
            Unable to load real data. Displaying sample data for demonstration purposes.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900/20">
      <div className="space-y-8 p-6">
        {/* Modern Header with Gradient */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 p-8 shadow-2xl">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
              <div>
                <h1 className="text-4xl sm:text-5xl font-bold text-white mb-2 drop-shadow-lg">
                  Welcome back, {user?.username}! 👋
                </h1>
                <p className="text-blue-100 text-lg">
                  Here's what's happening in the market today
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className={`px-4 py-2 rounded-full text-sm font-semibold backdrop-blur-md ${
                  isConnected 
                    ? 'bg-green-500/90 text-white shadow-lg' 
                    : 'bg-red-500/90 text-white shadow-lg'
                }`}>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-white animate-pulse' : 'bg-white'}`}></div>
                    {isConnected ? 'Live Data' : 'Offline'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Portfolio Summary Cards - Modern Design */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Portfolio Value Card */}
          <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 p-6 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                  <CurrencyDollarIcon className="h-6 w-6 text-white" />
                </div>
                <SparklesIcon className="h-5 w-5 text-white/80" />
              </div>
              <p className="text-blue-100 text-sm font-medium mb-1">Portfolio Value</p>
              <p className="text-3xl font-bold text-white">{formatCurrency(portfolioValue)}</p>
            </div>
          </div>

          {/* Today's P&L Card */}
          <div className={`group relative overflow-hidden rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 ${
            todayPnL >= 0 
              ? 'bg-gradient-to-br from-green-500 to-emerald-600' 
              : 'bg-gradient-to-br from-red-500 to-rose-600'
          }`}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                  <ArrowTrendingUpIcon className={`h-6 w-6 ${todayPnL >= 0 ? 'text-white' : 'text-white rotate-180'}`} />
                </div>
                <FireIcon className="h-5 w-5 text-white/80" />
              </div>
              <p className="text-white/90 text-sm font-medium mb-1">Today's P&L</p>
              <p className="text-3xl font-bold text-white">{formatCurrency(todayPnL)}</p>
            </div>
          </div>

          {/* Total Return Card */}
          <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 p-6 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                  <ChartBarIcon className="h-6 w-6 text-white" />
                </div>
                <BoltIcon className="h-5 w-5 text-white/80" />
              </div>
              <p className="text-purple-100 text-sm font-medium mb-1">Total Return</p>
              <p className="text-3xl font-bold text-white">+12.5%</p>
            </div>
          </div>

          {/* Active Positions Card */}
          <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-orange-500 to-amber-600 p-6 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                  <EyeIcon className="h-6 w-6 text-white" />
                </div>
                <SparklesIcon className="h-5 w-5 text-white/80" />
              </div>
              <p className="text-orange-100 text-sm font-medium mb-1">Active Positions</p>
              <p className="text-3xl font-bold text-white">8</p>
            </div>
          </div>
        </div>

        {/* Live Market Data - Glassmorphism Card */}
        <div className="relative overflow-hidden rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5"></div>
          <div className="relative p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                Live Market Data
              </h3>
              <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                <span>Real-time</span>
              </div>
            </div>
            <LiveMarketData />
          </div>
        </div>

        {/* Index Constituents - Modern Card */}
        <div className="relative overflow-hidden rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 to-pink-500/5"></div>
          <div className="relative p-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <ChartBarIcon className="h-5 w-5 text-purple-600" />
              Index Constituents
            </h3>
            <IndexConstituentsView />
          </div>
        </div>

        {/* Market Chart - Enhanced */}
        <div className="relative overflow-hidden rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 shadow-2xl p-6">
          <div className="absolute inset-0 bg-gradient-to-r from-green-500/5 to-blue-500/5"></div>
          <div className="relative">
            <ResponsiveChart
              data={marketData}
              dataKey="value"
              title="Portfolio Performance"
              height={350}
              loading={loading}
              symbol="PORTFOLIO"
              advanced={true}
            />
          </div>
        </div>

        {/* Market Overview - Top Gainers & Losers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Gainers - Modern Card */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200/50 dark:border-green-800/50 shadow-xl">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <ArrowTrendingUpIcon className="h-5 w-5 text-green-600" />
                Top Gainers
              </h3>
              <div className="space-y-3">
                {topGainers.slice(0, 5).map((stock, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-xl border border-green-200/30 dark:border-green-800/30 hover:shadow-md transition-all duration-200 hover:scale-[1.02]">
                    <div className="flex-1">
                      <p className="text-base font-bold text-gray-900 dark:text-white">{stock.symbol}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{formatCurrency(stock.price)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-base font-bold text-green-600 dark:text-green-400">{formatPercentage(stock.change)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Top Losers - Modern Card */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20 border border-red-200/50 dark:border-red-800/50 shadow-xl">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <ArrowTrendingUpIcon className="h-5 w-5 text-red-600 rotate-180" />
                Top Losers
              </h3>
              <div className="space-y-3">
                {topLosers.slice(0, 5).map((stock, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-xl border border-red-200/30 dark:border-red-800/30 hover:shadow-md transition-all duration-200 hover:scale-[1.02]">
                    <div className="flex-1">
                      <p className="text-base font-bold text-gray-900 dark:text-white">{stock.symbol}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{formatCurrency(stock.price)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-base font-bold text-red-600 dark:text-red-400">{formatPercentage(stock.change)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Professional Stock Cards */}
        {loading ? (
          <StockCardLoadingState count={4} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <RealTimeStockCard
              symbol="RELIANCE"
              name="Reliance Industries Ltd"
            />
            <RealTimeStockCard
              symbol="TCS"
              name="Tata Consultancy Services"
            />
            <RealTimeStockCard
              symbol="HDFC"
              name="HDFC Bank Ltd"
            />
            <RealTimeStockCard
              symbol="INFY"
              name="Infosys Ltd"
            />
          </div>
        )}

        {/* News Feed & Market Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="relative overflow-hidden rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 shadow-2xl p-6">
              <NewsFeed />
            </div>
          </div>
          <div className="space-y-6">
            <div className="relative overflow-hidden rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 shadow-2xl p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <ChartBarIcon className="h-5 w-5 text-blue-600" />
                Market Summary
              </h3>
              {marketSummary ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Market Status:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      marketSummary.market_status === 'open' 
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400' 
                        : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-400'
                    }`}>
                      {marketSummary.market_status === 'open' ? 'Open' : 'Closed'}
                    </span>
                  </div>
                  {marketSummary.key_indices && marketSummary.key_indices.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Key Indices:</h4>
                      {marketSummary.key_indices.map((index: any, idx: number) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{index.name || index.symbol}</span>
                          <div className="flex items-center space-x-3">
                            <span className="font-semibold text-gray-900 dark:text-white">{formatINR(index.last_price)}</span>
                            <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                              (index.change_percent || 0) >= 0 
                                ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400' 
                                : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-400'
                            }`}>
                              {formatPercentage(index.change_percent || 0)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Loading market summary...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
