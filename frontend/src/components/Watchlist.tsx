import React, { useState, useEffect } from 'react';
import { StarIcon, XMarkIcon, MagnifyingGlassIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import comprehensiveTradingApi from '../services/comprehensiveTradingApi';
import ClickableSymbol from './ClickableSymbol';

interface WatchlistProps {
  onSymbolSelect: (symbol: string) => void;
  currentSymbol?: string;
}

interface WatchlistItem {
  symbol: string;
  price?: number;
  change?: number;
  changePercent?: number;
  signal?: 'BUY' | 'SELL' | 'HOLD';
  confidence?: number;
  pattern?: string;
}

const Watchlist: React.FC<WatchlistProps> = ({ onSymbolSelect, currentSymbol }) => {
  const [watchlist, setWatchlist] = useState<string[]>(() => {
    // Load from localStorage
    const saved = localStorage.getItem('trading_watchlist');
    return saved ? JSON.parse(saved) : ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK'];
  });
  
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [showSearch, setShowSearch] = useState(false);
  const [watchlistData, setWatchlistData] = useState<Record<string, WatchlistItem>>({});
  const [autoAnalysisEnabled, setAutoAnalysisEnabled] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  // Save to localStorage when watchlist changes
  useEffect(() => {
    localStorage.setItem('trading_watchlist', JSON.stringify(watchlist));
  }, [watchlist]);

  // Auto-analyze watchlist symbols
  useEffect(() => {
    if (!autoAnalysisEnabled || watchlist.length === 0) return;

    const analyzeWatchlist = async () => {
      setAnalyzing(true);
      const analysisResults: Record<string, WatchlistItem> = {};

      for (const symbol of watchlist) {
        try {
          // Get pattern analysis
          const patternResponse = await comprehensiveTradingApi.analyzePatterns({
            symbol,
            timeframe: '1D',
            patterns: ['all']
          });

          // Get trading signals (basic)
          // For now, we'll use pattern data to infer signals
          let signal: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
          let confidence = 50;
          let pattern = 'None';

          if (patternResponse && patternResponse.patterns && patternResponse.patterns.length > 0) {
            const highConfidencePatterns = patternResponse.patterns.filter((p: any) => 
              p.significance === 'high'
            );
            
            if (highConfidencePatterns.length > 0) {
              const latestPattern = highConfidencePatterns[highConfidencePatterns.length - 1];
              pattern = latestPattern.name || latestPattern.pattern || 'Pattern';
              signal = latestPattern.type === 'bullish' ? 'BUY' : 
                      latestPattern.type === 'bearish' ? 'SELL' : 'HOLD';
              confidence = latestPattern.significance === 'high' ? 80 : 
                          latestPattern.significance === 'medium' ? 60 : 40;
            }
          }

          analysisResults[symbol] = {
            symbol,
            signal,
            confidence,
            pattern
          };
        } catch (error) {
          console.error(`Error analyzing ${symbol}:`, error);
          analysisResults[symbol] = {
            symbol,
            signal: 'HOLD',
            confidence: 0,
            pattern: 'Error'
          };
        }
      }

      setWatchlistData(analysisResults);
      setAnalyzing(false);
    };

    // Initial analysis
    analyzeWatchlist();

    // Auto-refresh every 5 minutes
    const interval = setInterval(analyzeWatchlist, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [watchlist, autoAnalysisEnabled]);

  // Popular Indian stocks for search suggestions
  const popularStocks = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'KOTAKBANK',
    'ITC', 'BHARTIARTL', 'SBIN', 'BAJFINANCE', 'ASIANPAINT', 'AXISBANK', 'MARUTI',
    'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'POWERGRID', 'NTPC', 'TECHM',
    'WIPRO', 'HCLTECH', 'LT', 'BAJAJFINSV', 'DRREDDY', 'TATAMOTORS', 'BRITANNIA'
  ];

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.length >= 2) {
      const filtered = popularStocks.filter(
        stock => stock.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(filtered.slice(0, 10));
      setShowSearch(true);
    } else {
      setSearchResults([]);
      setShowSearch(false);
    }
  };

  const addToWatchlist = (symbol: string) => {
    if (!watchlist.includes(symbol)) {
      setWatchlist([...watchlist, symbol]);
      toast.success(`${symbol} added to watchlist`);
    }
    setSearchQuery('');
    setShowSearch(false);
  };

  const removeFromWatchlist = (symbol: string) => {
    setWatchlist(watchlist.filter(s => s !== symbol));
    toast.success(`${symbol} removed from watchlist`);
  };

  const toggleFavorite = (symbol: string) => {
    if (watchlist.includes(symbol)) {
      removeFromWatchlist(symbol);
    } else {
      addToWatchlist(symbol);
    }
  };

  return (
    <div className="w-full bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <StarIconSolid className="w-5 h-5 text-yellow-500" />
            Watchlist
          </h3>
          {analyzing && (
            <span className="text-xs text-blue-400 flex items-center gap-1">
              <div className="animate-spin h-3 w-3 border-2 border-blue-400 border-t-transparent rounded-full"></div>
              Analyzing...
            </span>
          )}
        </div>
        <button
          onClick={() => setAutoAnalysisEnabled(!autoAnalysisEnabled)}
          className={`text-xs px-2 py-1 rounded ${
            autoAnalysisEnabled 
              ? 'bg-green-500/20 text-green-400' 
              : 'bg-gray-700 text-gray-400'
          }`}
          title={autoAnalysisEnabled ? 'Auto-analysis enabled' : 'Auto-analysis disabled'}
        >
          <ChartBarIcon className="w-4 h-4" />
        </button>
        <div className="relative flex-1 max-w-xs ml-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => searchQuery.length >= 2 && setShowSearch(true)}
              placeholder="Search symbol..."
              className="w-full pl-10 pr-4 py-2 bg-[#131722] border border-[#2a2e39] rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* Search Results Dropdown */}
          {showSearch && searchResults.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-xl max-h-60 overflow-y-auto">
              {searchResults.map((symbol) => (
                <div
                  key={symbol}
                  onClick={() => addToWatchlist(symbol)}
                  className="px-4 py-2 hover:bg-[#2a2e39] cursor-pointer flex items-center justify-between text-sm text-white"
                >
                  <span>{symbol}</span>
                  {watchlist.includes(symbol) && (
                    <StarIconSolid className="w-4 h-4 text-yellow-500" />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Watchlist Items */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {watchlist.length === 0 ? (
          <div className="text-center py-8 text-gray-400 text-sm">
            No symbols in watchlist. Search and add symbols above.
          </div>
        ) : (
          watchlist.map((symbol) => (
            <div
              key={symbol}
              onClick={() => onSymbolSelect(symbol)}
              className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                currentSymbol === symbol
                  ? 'bg-blue-600/20 border border-blue-500/50'
                  : 'bg-[#131722] border border-[#2a2e39] hover:bg-[#2a2e39]'
              }`}
            >
              <div className="flex items-center gap-3 flex-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFavorite(symbol);
                  }}
                  className="text-yellow-500 hover:text-yellow-400 transition-colors"
                >
                  <StarIconSolid className="w-5 h-5" />
                </button>
                <div className="flex-1">
                  <ClickableSymbol symbol={symbol} variant="bold" onClick={onSymbolSelect} />
                  {watchlistData[symbol] && (
                    <>
                      <div className="text-xs text-gray-400">
                        {watchlistData[symbol].price?.toFixed(2) || '--'}
                        {watchlistData[symbol].changePercent !== undefined && (
                          <span
                            className={`ml-2 ${
                              watchlistData[symbol].changePercent! >= 0
                                ? 'text-green-500'
                                : 'text-red-500'
                            }`}
                          >
                            {watchlistData[symbol].changePercent! >= 0 ? '+' : ''}
                            {watchlistData[symbol].changePercent!.toFixed(2)}%
                          </span>
                        )}
                      </div>
                      {/* Auto-analysis summary */}
                      {autoAnalysisEnabled && (
                        <div className="flex items-center gap-2 mt-1">
                          {watchlistData[symbol].signal && watchlistData[symbol].signal !== 'HOLD' && (
                            <span className={`text-xs px-1.5 py-0.5 rounded ${
                              watchlistData[symbol].signal === 'BUY' 
                                ? 'bg-green-500/20 text-green-400'
                                : 'bg-red-500/20 text-red-400'
                            }`}>
                              {watchlistData[symbol].signal}
                            </span>
                          )}
                          {watchlistData[symbol].pattern && watchlistData[symbol].pattern !== 'None' && watchlistData[symbol].pattern !== 'Error' && (
                            <span className="text-xs text-blue-400">
                              {watchlistData[symbol].pattern}
                            </span>
                          )}
                          {watchlistData[symbol]?.confidence !== undefined && watchlistData[symbol]?.confidence! > 0 && (
                            <span className="text-xs text-gray-500">
                              {watchlistData[symbol]?.confidence}%
                            </span>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFromWatchlist(symbol);
                }}
                className="text-gray-400 hover:text-red-500 transition-colors p-1"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Quick Add Popular Stocks */}
      <div className="mt-4 pt-4 border-t border-[#2a2e39]">
        <div className="text-xs text-gray-400 mb-2">Quick Add:</div>
        <div className="flex flex-wrap gap-2">
          {popularStocks.slice(0, 8).map((symbol) => (
            <button
              key={symbol}
              onClick={() => toggleFavorite(symbol)}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                watchlist.includes(symbol)
                  ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/50'
                  : 'bg-[#131722] text-gray-400 border border-[#2a2e39] hover:bg-[#2a2e39] hover:text-white'
              }`}
            >
              {symbol}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Watchlist;

