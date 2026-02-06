import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../services/api';
import { cn } from '../lib/utils';
import { Search, RefreshCw, TrendingUp, TrendingDown, Building, Database } from 'lucide-react';
import StockListItem from './ui/StockListItem';

interface StockData {
  symbol: string;
  name: string;
  exchange: 'NSE' | 'BSE';
  sector?: string;
  market_cap?: number;
  last_price?: string;
  change?: number;
  change_percent?: number;
  volume?: number;
  yahoo_symbol?: string;
}

interface StockBrowserProps {
  className?: string;
  onStockSelect?: (stock: StockData) => void;
}

const StockBrowser: React.FC<StockBrowserProps> = ({ className, onStockSelect }) => {
  const [allStocks, setAllStocks] = useState<StockData[]>([]);
  const [nseStocks, setNseStocks] = useState<StockData[]>([]);
  const [bseStocks, setBseStocks] = useState<StockData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [exchangeFilter, setExchangeFilter] = useState<'ALL' | 'NSE' | 'BSE'>('ALL');
  const [sectorFilter, setSectorFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'symbol' | 'name' | 'change_percent' | 'volume'>('symbol');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [activeTab, setActiveTab] = useState<'all' | 'nse' | 'bse'>('all');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [searchActive, setSearchActive] = useState(false);
  const [searchResults, setSearchResults] = useState<StockData[]>([]);

  // Fetch all stocks data
  const fetchStocksData = async () => {
    setLoading(true);
    setError(null);

    try {
      const results = await Promise.allSettled([
        api.getAllStocks(),
        api.getNSEStocks(),
        api.getBSEStocks()
      ]);

      const [allRes, nseRes, bseRes] = results;

      let anySuccess = false;

      if (allRes.status === 'fulfilled' && allRes.value?.success && allRes.value.data) {
        const allData = allRes.value.data as any;
        const combinedStocks = [
          ...(allData.nse || []).map((stock: any) => ({ ...stock, exchange: 'NSE' as const })),
          ...(allData.bse || []).map((stock: any) => ({ ...stock, exchange: 'BSE' as const }))
        ];
        setAllStocks(combinedStocks);
        setLastUpdated(new Date());
        anySuccess = true;
      }

      if (nseRes.status === 'fulfilled' && nseRes.value?.success && nseRes.value.data) {
        const nseData = (nseRes.value.data as any).stocks || nseRes.value.data;
        setNseStocks(Array.isArray(nseData) ? nseData.map((stock: any) => ({ ...stock, exchange: 'NSE' as const })) : []);
        anySuccess = true;
      }

      if (bseRes.status === 'fulfilled' && bseRes.value?.success && bseRes.value.data) {
        const bseData = (bseRes.value.data as any).stocks || bseRes.value.data;
        setBseStocks(Array.isArray(bseData) ? bseData.map((stock: any) => ({ ...stock, exchange: 'BSE' as const })) : []);
        anySuccess = true;
      }

      if (!anySuccess) {
        console.error('Stock API calls failed:', { results });
        setError('Failed to fetch stock data. Please try again.');
      }
    } catch (err) {
      console.error('Error fetching stocks:', err);
      setError('Failed to fetch stock data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStocksData();
  }, []);

  // Get current stocks based on active tab
  const currentStocks = useMemo(() => {
    if (searchActive) {
      return searchResults;
    }
    switch (activeTab) {
      case 'nse':
        return nseStocks;
      case 'bse':
        return bseStocks;
      default:
        return allStocks;
    }
  }, [activeTab, allStocks, nseStocks, bseStocks, searchActive, searchResults]);

  // Get unique sectors for filter
  const sectors = useMemo(() => {
    const sectorSet = new Set<string>();
    currentStocks.forEach(stock => {
      if (stock.sector && stock.sector.trim()) {
        sectorSet.add(stock.sector);
      }
    });
    return Array.from(sectorSet).sort();
  }, [currentStocks]);

  // Filter and sort stocks
  const filteredStocks = useMemo(() => {
    let filtered = currentStocks;

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(stock =>
        stock.symbol.toLowerCase().includes(query) ||
        stock.name.toLowerCase().includes(query) ||
        (stock.sector && stock.sector.toLowerCase().includes(query))
      );
    }

    // Exchange filter
    if (exchangeFilter !== 'ALL') {
      filtered = filtered.filter(stock => stock.exchange === exchangeFilter);
    }

    // Sector filter
    if (sectorFilter !== 'ALL') {
      filtered = filtered.filter(stock => stock.sector === sectorFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortBy) {
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case 'name':
          aValue = a.name;
          bValue = b.name;
          break;
        case 'change_percent':
          aValue = a.change_percent || 0;
          bValue = b.change_percent || 0;
          break;
        case 'volume':
          aValue = a.volume || 0;
          bValue = b.volume || 0;
          break;
        default:
          aValue = a.symbol;
          bValue = b.symbol;
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      } else {
        return sortOrder === 'asc' 
          ? (aValue as number) - (bValue as number)
          : (bValue as number) - (aValue as number);
      }
    });

    return filtered;
  }, [currentStocks, searchQuery, exchangeFilter, sectorFilter, sortBy, sortOrder]);

  const handleStockClick = (stock: StockData) => {
    if (onStockSelect) {
      onStockSelect(stock);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000000) {
      return `${(num / 1000000000).toFixed(1)}B`;
    } else if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const getExchangeIcon = (exchange: string) => {
    return exchange === 'NSE' ? <Building className="h-4 w-4" /> : <Database className="h-4 w-4" />;
  };

  const getExchangeColor = (exchange: string) => {
    return exchange === 'NSE' ? 'text-blue-600' : 'text-green-600';
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Stock Browser</h2>
          <p className="text-muted-foreground">
            Browse all NSE & BSE stocks with real-time data
            {lastUpdated && (
              <span className="ml-2 text-xs">
                (Updated: {lastUpdated.toLocaleTimeString()})
              </span>
            )}
          </p>
        </div>
        <button
          onClick={fetchStocksData}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <Building className="h-5 w-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">NSE Stocks</p>
              <p className="text-2xl font-bold">{nseStocks.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <Database className="h-5 w-5 text-green-600" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">BSE Stocks</p>
              <p className="text-2xl font-bold">{bseStocks.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-success-600" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Stocks</p>
              <p className="text-2xl font-bold">{allStocks.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search stocks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Exchange Filter */}
          <select
            value={exchangeFilter}
            onChange={(e) => setExchangeFilter(e.target.value as 'ALL' | 'NSE' | 'BSE')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Exchanges</option>
            <option value="NSE">NSE Only</option>
            <option value="BSE">BSE Only</option>
          </select>

          {/* Sector Filter */}
          <select
            value={sectorFilter}
            onChange={(e) => setSectorFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Sectors</option>
            {sectors.map(sector => (
              <option key={sector} value={sector}>{sector}</option>
            ))}
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'symbol' | 'name' | 'change_percent' | 'volume')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="symbol">Symbol</option>
            <option value="name">Name</option>
            <option value="change_percent">Change %</option>
            <option value="volume">Volume</option>
          </select>

          {/* Sort Order */}
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="flex items-center justify-center space-x-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {sortOrder === 'asc' ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            <span>{sortOrder === 'asc' ? 'Asc' : 'Desc'}</span>
          </button>
          {/* Search actions */}
          <div className="flex items-center space-x-2">
            <button
              onClick={async () => {
                const query = searchQuery.trim();
                if (!query) {
                  setSearchActive(false);
                  setSearchResults([]);
                  return;
                }
                try {
                  setLoading(true);
                  setError(null);
                  const res = await api.searchStocks(query, exchangeFilter, 200);
                  if (res.success && res.data) {
                    const rows: any[] = (res.data as any).stocks || [];
                    const mapped = rows.map((s: any) => ({
                      ...s,
                      exchange: (s.exchange || exchangeFilter || 'ALL') === 'ALL' ? (s.exchange || 'NSE') : s.exchange || exchangeFilter
                    })) as StockData[];
                    setSearchResults(mapped);
                    setSearchActive(true);
                    setActiveTab('all');
                  } else {
                    setSearchResults([]);
                    setSearchActive(true);
                  }
                } catch (err) {
                  console.error('Search error:', err);
                  setError('Search failed. Please try again.');
                } finally {
                  setLoading(false);
                }
              }}
              className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Search
            </button>
            {searchActive && (
              <button
                onClick={() => { setSearchActive(false); setSearchResults([]); }}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('all')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm",
                activeTab === 'all'
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              All Stocks ({allStocks.length})
            </button>
            <button
              onClick={() => setActiveTab('nse')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm",
                activeTab === 'nse'
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              NSE ({nseStocks.length})
            </button>
            <button
              onClick={() => setActiveTab('bse')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm",
                activeTab === 'bse'
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              BSE ({bseStocks.length})
            </button>
          </nav>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-600">{error}</p>
            </div>
          ) : filteredStocks.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">{searchActive ? 'No results for your search.' : 'No stocks found matching your criteria.'}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {searchActive && (
                <div className="text-sm text-gray-500 pb-2">Showing search results ({filteredStocks.length})</div>
              )}
              {filteredStocks.map((stock) => (
                <div
                  key={`${stock.exchange}-${stock.symbol}`}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                  onClick={() => handleStockClick(stock)}
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className={cn("flex items-center space-x-1", getExchangeColor(stock.exchange))}>
                      {getExchangeIcon(stock.exchange)}
                      <span className="text-xs font-medium px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded">
                        {stock.exchange}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h3 className="font-semibold text-foreground truncate">{stock.symbol}</h3>
                        {stock.sector && (
                          <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                            {stock.sector}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground truncate">{stock.name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-foreground">
                      {stock.last_price ? `₹${stock.last_price}` : 'N/A'}
                    </div>
                    {stock.change_percent !== undefined && (
                      <div className={cn(
                        "text-sm flex items-center justify-end",
                        stock.change_percent >= 0 ? "text-green-600" : "text-red-600"
                      )}>
                        {stock.change_percent >= 0 ? (
                          <TrendingUp className="h-3 w-3 mr-1" />
                        ) : (
                          <TrendingDown className="h-3 w-3 mr-1" />
                        )}
                        {stock.change_percent >= 0 ? '+' : ''}{stock.change_percent.toFixed(2)}%
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StockBrowser;