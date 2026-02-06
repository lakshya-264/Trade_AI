import React, { useState, useEffect, useCallback } from 'react';
import { 
  MagnifyingGlassIcon, 
  PlusIcon, 
  XMarkIcon,
  StarIcon,
  ChartBarIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

// Types
export interface Symbol {
  symbol: string;
  name: string;
  exchange: string;
  sector?: string;
  marketCap?: number;
  lastPrice?: number;
  change?: number;
  changePercent?: number;
  volume?: number;
  isFavorite?: boolean;
}

export interface Watchlist {
  id: string;
  name: string;
  symbols: string[];
  isDefault: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface SymbolSearchResult {
  symbol: string;
  name: string;
  exchange: string;
  sector?: string;
  marketCap?: number;
}

// Mock data for Indian stocks
const MOCK_SYMBOLS: Symbol[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries Ltd', exchange: 'NSE', sector: 'Oil & Gas', marketCap: 15000000, lastPrice: 2450.50, change: 25.30, changePercent: 1.04, volume: 1500000, isFavorite: true },
  { symbol: 'TCS', name: 'Tata Consultancy Services Ltd', exchange: 'NSE', sector: 'IT', marketCap: 12000000, lastPrice: 3850.75, change: -15.25, changePercent: -0.39, volume: 800000, isFavorite: true },
  { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd', exchange: 'NSE', sector: 'Banking', marketCap: 8000000, lastPrice: 1650.20, change: 8.50, changePercent: 0.52, volume: 1200000, isFavorite: false },
  { symbol: 'INFY', name: 'Infosys Ltd', exchange: 'NSE', sector: 'IT', marketCap: 7000000, lastPrice: 1850.40, change: -5.80, changePercent: -0.31, volume: 900000, isFavorite: false },
  { symbol: 'HINDUNILVR', name: 'Hindustan Unilever Ltd', exchange: 'NSE', sector: 'FMCG', marketCap: 6000000, lastPrice: 2650.80, change: 12.40, changePercent: 0.47, volume: 500000, isFavorite: true },
  { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd', exchange: 'NSE', sector: 'Banking', marketCap: 5500000, lastPrice: 950.60, change: -3.20, changePercent: -0.34, volume: 1100000, isFavorite: false },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank Ltd', exchange: 'NSE', sector: 'Banking', marketCap: 4500000, lastPrice: 1850.30, change: 18.70, changePercent: 1.02, volume: 600000, isFavorite: false },
  { symbol: 'ITC', name: 'ITC Ltd', exchange: 'NSE', sector: 'FMCG', marketCap: 4000000, lastPrice: 450.25, change: 2.15, changePercent: 0.48, volume: 800000, isFavorite: true },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel Ltd', exchange: 'NSE', sector: 'Telecom', marketCap: 3500000, lastPrice: 850.40, change: -8.30, changePercent: -0.97, volume: 700000, isFavorite: false },
  { symbol: 'SBIN', name: 'State Bank of India', exchange: 'NSE', sector: 'Banking', marketCap: 3000000, lastPrice: 580.75, change: 5.25, changePercent: 0.91, volume: 1000000, isFavorite: false },
];

// Watchlist Manager
export class WatchlistManager {
  private watchlists: Map<string, Watchlist> = new Map();
  private listeners: Array<(watchlists: Watchlist[]) => void> = [];

  constructor() {
    // Initialize with default watchlist
    const defaultWatchlist: Watchlist = {
      id: 'default',
      name: 'My Watchlist',
      symbols: ['RELIANCE', 'TCS', 'HINDUNILVR', 'ITC'],
      isDefault: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.watchlists.set('default', defaultWatchlist);
  }

  getWatchlists(): Watchlist[] {
    return Array.from(this.watchlists.values());
  }

  getWatchlist(id: string): Watchlist | undefined {
    return this.watchlists.get(id);
  }

  createWatchlist(name: string): Watchlist {
    const watchlist: Watchlist = {
      id: `watchlist-${Date.now()}`,
      name,
      symbols: [],
      isDefault: false,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.watchlists.set(watchlist.id, watchlist);
    this.notifyListeners();
    return watchlist;
  }

  updateWatchlist(id: string, updates: Partial<Watchlist>): void {
    const watchlist = this.watchlists.get(id);
    if (watchlist) {
      this.watchlists.set(id, { ...watchlist, ...updates, updatedAt: new Date() });
      this.notifyListeners();
    }
  }

  deleteWatchlist(id: string): void {
    if (id === 'default') return; // Cannot delete default watchlist
    this.watchlists.delete(id);
    this.notifyListeners();
  }

  addSymbolToWatchlist(watchlistId: string, symbol: string): void {
    const watchlist = this.watchlists.get(watchlistId);
    if (watchlist && !watchlist.symbols.includes(symbol)) {
      watchlist.symbols.push(symbol);
      this.watchlists.set(watchlistId, { ...watchlist, updatedAt: new Date() });
      this.notifyListeners();
    }
  }

  removeSymbolFromWatchlist(watchlistId: string, symbol: string): void {
    const watchlist = this.watchlists.get(watchlistId);
    if (watchlist) {
      watchlist.symbols = watchlist.symbols.filter(s => s !== symbol);
      this.watchlists.set(watchlistId, { ...watchlist, updatedAt: new Date() });
      this.notifyListeners();
    }
  }

  subscribe(listener: (watchlists: Watchlist[]) => void) {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.getWatchlists()));
  }
}

// Symbol Search Component
interface SymbolSearchProps {
  onSymbolSelect?: (symbol: Symbol) => void;
  onAddToWatchlist?: (symbol: Symbol) => void;
  className?: string;
}

const SymbolSearch: React.FC<SymbolSearchProps> = ({
  onSymbolSelect,
  onAddToWatchlist,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SymbolSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const searchSymbols = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    
    // Simulate API call with mock data
    setTimeout(() => {
      const results = MOCK_SYMBOLS
        .filter(symbol => 
          symbol.symbol.toLowerCase().includes(query.toLowerCase()) ||
          symbol.name.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, 10)
        .map(symbol => ({
          symbol: symbol.symbol,
          name: symbol.name,
          exchange: symbol.exchange,
          sector: symbol.sector,
          marketCap: symbol.marketCap
        }));
      
      setSearchResults(results);
      setIsSearching(false);
    }, 300);
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchSymbols(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, searchSymbols]);

  const handleSymbolClick = useCallback((result: SymbolSearchResult) => {
    const fullSymbol = MOCK_SYMBOLS.find(s => s.symbol === result.symbol);
    if (fullSymbol) {
      onSymbolSelect?.(fullSymbol);
      setShowResults(false);
      setSearchQuery('');
    }
  }, [onSymbolSelect]);

  const handleAddToWatchlist = useCallback((result: SymbolSearchResult) => {
    const fullSymbol = MOCK_SYMBOLS.find(s => s.symbol === result.symbol);
    if (fullSymbol) {
      onAddToWatchlist?.(fullSymbol);
    }
  }, [onAddToWatchlist]);

  return (
    <div className={`symbol-search relative ${className}`}>
      <div className="search-input-container relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setShowResults(true);
          }}
          onFocus={() => setShowResults(true)}
          placeholder="Search symbols (e.g., RELIANCE, TCS)..."
          className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
        />
        {isSearching && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>

      {/* Search Results */}
      {showResults && searchResults.length > 0 && (
        <div className="search-results absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
          {searchResults.map((result) => (
            <div
              key={`${result.symbol}-${result.exchange}`}
              className="search-result-item flex items-center justify-between p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-700 last:border-b-0"
              onClick={() => handleSymbolClick(result)}
            >
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-white">{result.symbol}</span>
                  <span className="text-xs text-gray-400">{result.exchange}</span>
                </div>
                <div className="text-sm text-gray-300">{result.name}</div>
                {result.sector && (
                  <div className="text-xs text-gray-400">{result.sector}</div>
                )}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleAddToWatchlist(result);
                }}
                className="p-1 text-gray-400 hover:text-blue-400"
                title="Add to watchlist"
              >
                <PlusIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* No Results */}
      {showResults && searchQuery && searchResults.length === 0 && !isSearching && (
        <div className="no-results absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50 p-4 text-center text-gray-400">
          No symbols found for "{searchQuery}"
        </div>
      )}
    </div>
  );
};

// Watchlist Component
interface WatchlistProps {
  watchlistManager: WatchlistManager;
  symbols: Symbol[];
  onSymbolClick?: (symbol: Symbol) => void;
  onRemoveSymbol?: (symbol: string) => void;
  className?: string;
}

const Watchlist: React.FC<WatchlistProps> = ({
  watchlistManager,
  symbols,
  onSymbolClick,
  onRemoveSymbol,
  className = ''
}) => {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [activeWatchlistId, setActiveWatchlistId] = useState<string>('default');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState('');

  useEffect(() => {
    const unsubscribe = watchlistManager.subscribe(setWatchlists);
    setWatchlists(watchlistManager.getWatchlists());
    return unsubscribe;
  }, [watchlistManager]);

  const activeWatchlist = watchlistManager.getWatchlist(activeWatchlistId);
  const watchlistSymbols = symbols.filter(symbol => 
    activeWatchlist?.symbols.includes(symbol.symbol)
  );

  const handleCreateWatchlist = useCallback(() => {
    if (newWatchlistName.trim()) {
      watchlistManager.createWatchlist(newWatchlistName.trim());
      setNewWatchlistName('');
      setShowCreateForm(false);
    }
  }, [watchlistManager, newWatchlistName]);

  const handleRemoveSymbol = useCallback((symbol: string) => {
    watchlistManager.removeSymbolFromWatchlist(activeWatchlistId, symbol);
    onRemoveSymbol?.(symbol);
  }, [watchlistManager, activeWatchlistId, onRemoveSymbol]);

  const formatPrice = (price?: number) => {
    if (price === undefined) return 'N/A';
    return `₹${price.toFixed(2)}`;
  };

  const formatChange = (change?: number, changePercent?: number) => {
    if (change === undefined || changePercent === undefined) return 'N/A';
    const isPositive = change >= 0;
    return (
      <span className={`text-sm ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
        {isPositive ? '+' : ''}{change.toFixed(2)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
      </span>
    );
  };

  return (
    <div className={`watchlist ${className}`}>
      {/* Watchlist Header */}
      <div className="watchlist-header p-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-white">Watchlists</h3>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="p-1 text-gray-400 hover:text-blue-400"
            title="Create new watchlist"
          >
            <PlusIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Watchlist Tabs */}
        <div className="flex space-x-1 overflow-x-auto">
          {watchlists.map((watchlist) => (
            <button
              key={watchlist.id}
              onClick={() => setActiveWatchlistId(watchlist.id)}
              className={`px-3 py-1 rounded text-sm whitespace-nowrap ${
                activeWatchlistId === watchlist.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {watchlist.name}
              {watchlist.symbols.length > 0 && (
                <span className="ml-1 text-xs opacity-75">({watchlist.symbols.length})</span>
              )}
            </button>
          ))}
        </div>

        {/* Create Watchlist Form */}
        {showCreateForm && (
          <div className="mt-2 p-2 bg-gray-700 rounded">
            <input
              type="text"
              value={newWatchlistName}
              onChange={(e) => setNewWatchlistName(e.target.value)}
              placeholder="Enter watchlist name..."
              className="w-full px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white text-sm"
              onKeyPress={(e) => e.key === 'Enter' && handleCreateWatchlist()}
            />
            <div className="flex space-x-2 mt-2">
              <button
                onClick={handleCreateWatchlist}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
              >
                Create
              </button>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setNewWatchlistName('');
                }}
                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Watchlist Symbols */}
      <div className="watchlist-symbols max-h-96 overflow-y-auto">
        {watchlistSymbols.length === 0 ? (
          <div className="p-4 text-center text-gray-400">
            <ChartBarIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No symbols in this watchlist</p>
            <p className="text-sm">Use the search above to add symbols</p>
          </div>
        ) : (
          watchlistSymbols.map((symbol) => (
            <div
              key={symbol.symbol}
              className="symbol-item p-3 border-b border-gray-700 hover:bg-gray-800 cursor-pointer"
              onClick={() => onSymbolClick?.(symbol)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-white">{symbol.symbol}</span>
                    <span className="text-xs text-gray-400">{symbol.exchange}</span>
                    {symbol.isFavorite && (
                      <StarIcon className="w-4 h-4 text-yellow-400" />
                    )}
                  </div>
                  <div className="text-sm text-gray-300 truncate">{symbol.name}</div>
                </div>
                
                <div className="text-right">
                  <div className="text-white font-medium">{formatPrice(symbol.lastPrice)}</div>
                  {formatChange(symbol.change, symbol.changePercent)}
                </div>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveSymbol(symbol.symbol);
                  }}
                  className="ml-2 p-1 text-gray-400 hover:text-red-400"
                  title="Remove from watchlist"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Main Watchlist and Search Component
interface WatchlistAndSearchProps {
  onSymbolSelect?: (symbol: Symbol) => void;
  className?: string;
}

const WatchlistAndSearch: React.FC<WatchlistAndSearchProps> = ({
  onSymbolSelect,
  className = ''
}) => {
  const watchlistManager = new WatchlistManager();
  const [symbols] = useState<Symbol[]>(MOCK_SYMBOLS);

  const handleSymbolSelect = useCallback((symbol: Symbol) => {
    onSymbolSelect?.(symbol);
  }, [onSymbolSelect]);

  const handleAddToWatchlist = useCallback((symbol: Symbol) => {
    const defaultWatchlist = watchlistManager.getWatchlist('default');
    if (defaultWatchlist) {
      watchlistManager.addSymbolToWatchlist('default', symbol.symbol);
    }
  }, [watchlistManager]);

  return (
    <div className={`watchlist-and-search ${className}`}>
      <SymbolSearch
        onSymbolSelect={handleSymbolSelect}
        onAddToWatchlist={handleAddToWatchlist}
        className="mb-4"
      />
      <Watchlist
        watchlistManager={watchlistManager}
        symbols={symbols}
        onSymbolClick={handleSymbolSelect}
      />
    </div>
  );
};

export default WatchlistAndSearch;
