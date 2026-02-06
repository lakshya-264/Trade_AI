import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';

interface ScannerStock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  sector: string;
  rsi: number;
  macd: number;
}

interface MarketScannerProps {
  className?: string;
}

const MarketScanner: React.FC<MarketScannerProps> = ({ className }) => {
  const [stocks, setStocks] = useState<ScannerStock[]>([]);
  const [filteredStocks, setFilteredStocks] = useState<ScannerStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'change' | 'volume' | 'rsi'>('change');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [sectorFilter, setSectorFilter] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    // Simulate loading scanner data
    const loadScannerData = async () => {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock scanner data
      const mockStocks: ScannerStock[] = [
        {
          symbol: 'RELIANCE',
          name: 'Reliance Industries Ltd',
          price: 2450.50,
          change: 61.25,
          changePercent: 2.56,
          volume: 1234567,
          marketCap: 16500000000000,
          sector: 'Energy',
          rsi: 65.2,
          macd: 12.5
        },
        {
          symbol: 'TCS',
          name: 'Tata Consultancy Services',
          price: 3850.25,
          change: -45.30,
          changePercent: -1.16,
          volume: 987654,
          marketCap: 14100000000000,
          sector: 'Technology',
          rsi: 42.8,
          macd: -8.3
        },
        {
          symbol: 'HDFC',
          name: 'HDFC Bank Ltd',
          price: 1650.75,
          change: 23.45,
          changePercent: 1.44,
          volume: 2345678,
          marketCap: 12300000000000,
          sector: 'Banking',
          rsi: 58.7,
          macd: 5.2
        },
        {
          symbol: 'INFY',
          name: 'Infosys Ltd',
          price: 1450.30,
          change: -12.80,
          changePercent: -0.87,
          volume: 1876543,
          marketCap: 6100000000000,
          sector: 'Technology',
          rsi: 38.5,
          macd: -3.1
        },
        {
          symbol: 'ITC',
          name: 'ITC Ltd',
          price: 425.60,
          change: 8.90,
          changePercent: 2.13,
          volume: 3456789,
          marketCap: 5300000000000,
          sector: 'FMCG',
          rsi: 72.1,
          macd: 15.8
        },
        {
          symbol: 'BHARTI',
          name: 'Bharti Airtel Ltd',
          price: 850.40,
          change: -15.20,
          changePercent: -1.76,
          volume: 1567890,
          marketCap: 4700000000000,
          sector: 'Telecom',
          rsi: 35.2,
          macd: -12.4
        }
      ];
      
      setStocks(mockStocks);
      setFilteredStocks(mockStocks);
      setLoading(false);
    };

    loadScannerData();
  }, []);

  // Filter and sort stocks
  useEffect(() => {
    let filtered = stocks;

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(stock =>
        stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        stock.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Sector filter
    if (sectorFilter !== 'all') {
      filtered = filtered.filter(stock => stock.sector === sectorFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue: number, bValue: number;
      
      switch (sortBy) {
        case 'change':
          aValue = a.changePercent;
          bValue = b.changePercent;
          break;
        case 'volume':
          aValue = a.volume;
          bValue = b.volume;
          break;
        case 'rsi':
          aValue = a.rsi;
          bValue = b.rsi;
          break;
        default:
          aValue = a.changePercent;
          bValue = b.changePercent;
      }

      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    });

    setFilteredStocks(filtered);
  }, [stocks, searchQuery, sectorFilter, sortBy, sortOrder]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatNumber = (value: number) => {
    if (value >= 1000000000) {
      return `${(value / 1000000000).toFixed(1)}B`;
    } else if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getRSIColor = (rsi: number) => {
    if (rsi > 70) return 'text-danger-600';
    if (rsi < 30) return 'text-success-600';
    return 'text-muted-foreground';
  };

  const sectors = ['all', ...Array.from(new Set(stocks.map(stock => stock.sector)))];

  if (loading) {
    return (
      <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
        <div className="space-y-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-16 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Market Scanner</h3>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-lg transition-colors"
        >
          <FunnelIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4 mb-4">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search stocks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted/30 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Sector</label>
              <select
                value={sectorFilter}
                onChange={(e) => setSectorFilter(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {sectors.map(sector => (
                  <option key={sector} value={sector}>
                    {sector === 'all' ? 'All Sectors' : sector}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'change' | 'volume' | 'rsi')}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="change">Change %</option>
                <option value="volume">Volume</option>
                <option value="rsi">RSI</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Order</label>
              <div className="flex space-x-2">
                <button
                  onClick={() => setSortOrder('desc')}
                  className={cn(
                    "flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    sortOrder === 'desc'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <ArrowDownIcon className="h-4 w-4 inline mr-1" />
                  Desc
                </button>
                <button
                  onClick={() => setSortOrder('asc')}
                  className={cn(
                    "flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    sortOrder === 'asc'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <ArrowUpIcon className="h-4 w-4 inline mr-1" />
                  Asc
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stocks List */}
      <div className="space-y-2">
        {filteredStocks.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>No stocks found</p>
          </div>
        ) : (
          filteredStocks.map((stock, index) => (
            <div
              key={index}
              className="p-3 border border-border rounded-lg hover:bg-muted/30 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <div>
                    <div className="font-medium text-foreground">{stock.symbol}</div>
                    <div className="text-sm text-muted-foreground">{stock.name}</div>
                  </div>
                  <div className="text-xs text-muted-foreground bg-muted/50 px-2 py-1 rounded">
                    {stock.sector}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-foreground">
                    {formatCurrency(stock.price)}
                  </div>
                  <div className={cn(
                    "text-sm font-medium",
                    stock.change >= 0 ? 'text-success-600' : 'text-danger-600'
                  )}>
                    {formatPercentage(stock.changePercent)}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-4 text-xs text-muted-foreground">
                <div>
                  <span className="block">Volume</span>
                  <span className="font-medium text-foreground">{formatNumber(stock.volume)}</span>
                </div>
                <div>
                  <span className="block">Market Cap</span>
                  <span className="font-medium text-foreground">{formatNumber(stock.marketCap)}</span>
                </div>
                <div>
                  <span className="block">RSI</span>
                  <span className={cn("font-medium", getRSIColor(stock.rsi))}>
                    {stock.rsi.toFixed(1)}
                  </span>
                </div>
                <div>
                  <span className="block">MACD</span>
                  <span className={cn(
                    "font-medium",
                    stock.macd >= 0 ? 'text-success-600' : 'text-danger-600'
                  )}>
                    {stock.macd.toFixed(1)}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default MarketScanner;
