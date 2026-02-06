import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, ChartBarIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { indexData, IndexStock } from '../data/indexStocks';
import { httpClient } from '../config/api';

interface Stock {
  symbol: string;
  name: string;
  category: string;
  sector?: string;
}

interface StockSelectorProps {
  value?: string;
  onChange?: (symbol: string) => void;
  showNavigateButton?: boolean;
  className?: string;
}

const StockSelector: React.FC<StockSelectorProps> = ({ 
  value, 
  onChange, 
  showNavigateButton = true,
  className = '' 
}) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState(value || '');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [allStocksFromAPI, setAllStocksFromAPI] = useState<Stock[]>([]);
  const [loadingStocks, setLoadingStocks] = useState(false);
  const [stocksLoaded, setStocksLoaded] = useState(false);

  // Sync selectedStock with value prop
  useEffect(() => {
    if (value) {
      setSelectedStock(value);
    }
  }, [value]);

  // Get all stocks from all indexes
  const getAllStocksFromIndexes = (): Stock[] => {
    const stocksMap = new Map<string, Stock>();
    
    // Add indices first (all major indices)
    const indices: Stock[] = [
      { symbol: 'NIFTY_50', name: 'NIFTY 50 Index', category: 'Indices', sector: 'Index' },
      { symbol: 'NIFTY', name: 'NIFTY 50', category: 'Indices', sector: 'Index' },
      { symbol: 'NIFTY50', name: 'NIFTY 50', category: 'Indices', sector: 'Index' },
      { symbol: 'SENSEX', name: 'BSE SENSEX', category: 'Indices', sector: 'Index' },
      { symbol: 'NIFTYBANK', name: 'NIFTY Bank Index', category: 'Indices', sector: 'Index' },
      { symbol: 'BANKNIFTY', name: 'BANK NIFTY', category: 'Indices', sector: 'Index' },
      { symbol: 'NIFTY_IT', name: 'NIFTY IT Index', category: 'Indices', sector: 'Index' },
      { symbol: 'NIFTYIT', name: 'NIFTY IT Index', category: 'Indices', sector: 'Index' },
      { symbol: 'NIFTYMIDCAP50', name: 'NIFTY Midcap 50', category: 'Indices', sector: 'Index' },
      { symbol: 'NIFTYFIN', name: 'FIN NIFTY', category: 'Indices', sector: 'Index' },
      { symbol: 'BANKEX', name: 'BSE BANKEX', category: 'Indices', sector: 'Index' },
    ];
    
    indices.forEach(index => stocksMap.set(index.symbol, index));
    
    // Add all stocks from all indexes
    Object.values(indexData).forEach(indexDataItem => {
      indexDataItem.stocks.forEach((stock: IndexStock) => {
        if (!stocksMap.has(stock.symbol)) {
          stocksMap.set(stock.symbol, {
            symbol: stock.symbol,
            name: stock.name,
            category: indexDataItem.name,
            sector: stock.sector
          });
        }
      });
    });
    
    return Array.from(stocksMap.values());
  };

  // Fetch NSE stocks from API
  useEffect(() => {
    const fetchNSEStocks = async () => {
      if (stocksLoaded) return; // Don't fetch if already loaded
      
      setLoadingStocks(true);
      try {
        let nseStocks: Stock[] = [];
        const MIN_NSE_STOCKS_FOR_DB = 1000;

        // Primary: DB-backed Stock Master (fast)
        try {
          const response = await httpClient.get('/api/financial/stock-master?exchange=NSE') as any;
          const rawList = response?.data;
          if (response?.success && Array.isArray(rawList)) {
            nseStocks = rawList.map((stock: any) => ({
              symbol: stock.symbol || stock.symbol_code,
              name: stock.company_name || stock.name || stock.symbol,
              category: 'NSE Stocks',
              sector: stock.sector || 'Unknown'
            })).filter((s: Stock) => !!s.symbol);
          }
        } catch (error) {
          // Ignore and fall back to scraper-backed list
        }

        // Fallback: Scraper-backed NSE list endpoint
        try {
          if (nseStocks.length < MIN_NSE_STOCKS_FOR_DB) {
            const response = await httpClient.get('/api/stocks/nse?force_refresh=true') as any;
            const stocks = response?.data?.stocks;
            if (response?.success && Array.isArray(stocks)) {
              nseStocks = stocks.map((stock: any) => ({
                symbol: stock.symbol || stock.symbol_code || stock.trading_symbol,
                name: stock.name || stock.company_name || stock.symbol,
                category: 'NSE Stocks',
                sector: stock.sector || 'Unknown'
              })).filter((s: Stock) => !!s.symbol);
            }
          }
        } catch (error) {
          // Ignore; UI will still work with index stocks
        }

        if (nseStocks.length > 0) {
          
          // Group by sector for better organization
          const stocksBySector = nseStocks.reduce((acc, stock) => {
            const sector = stock.sector || 'Other';
            if (!acc[sector]) {
              acc[sector] = [];
            }
            acc[sector].push(stock);
            return acc;
          }, {} as Record<string, Stock[]>);
          
          // Sort stocks within each sector by symbol
          Object.keys(stocksBySector).forEach(sector => {
            stocksBySector[sector].sort((a, b) => a.symbol.localeCompare(b.symbol));
          });
          
          setAllStocksFromAPI(nseStocks);
          setStocksLoaded(true);
          console.log(`✅ Loaded ${nseStocks.length} NSE stocks`);
        }
      } catch (error) {
        console.error('Error fetching NSE stocks from API:', error);
        // Continue with index stocks only if API fails
      } finally {
        setLoadingStocks(false);
      }
    };

    fetchNSEStocks();
  }, [stocksLoaded]);

  // Combine index stocks with API stocks
  const getAllStocks = (): Stock[] => {
    const stocksMap = new Map<string, Stock>();
    
    // First, add all stocks from indexes (these are priority/premium stocks)
    const indexStocks = getAllStocksFromIndexes();
    indexStocks.forEach(stock => stocksMap.set(stock.symbol, stock));
    
    // Then, add all stocks from API (these are all available stocks)
    allStocksFromAPI.forEach(stock => {
      if (!stocksMap.has(stock.symbol)) {
        stocksMap.set(stock.symbol, stock);
      }
    });
    
    return Array.from(stocksMap.values());
  };

  const allStocks = getAllStocks();

  // Filter stocks based on search term
  const filteredStocks = allStocks.filter(stock => 
    stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    stock.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (stock.sector && stock.sector.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Group stocks by category
  const groupedStocks = filteredStocks.reduce((acc, stock) => {
    if (!acc[stock.category]) {
      acc[stock.category] = [];
    }
    acc[stock.category].push(stock);
    return acc;
  }, {} as Record<string, Stock[]>);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleStockSelect = (symbol: string, e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    // Update local state
    setSelectedStock(symbol);
    setIsOpen(false);
    setSearchTerm('');
    
    // Call onChange callback to update parent component - use setTimeout to ensure state updates
    // IMPORTANT: Only call onChange, do NOT navigate automatically
    if (onChange) {
      // Use setTimeout to ensure the callback fires after state updates
      setTimeout(() => {
        onChange(symbol);
      }, 0);
    }
    
    // DO NOT navigate automatically - navigation should only happen on explicit button click
  };

  const handleNavigateToChart = (symbol: string) => {
    navigate(`/comprehensive-trading-pro?symbol=${symbol}`);
  };

  const getStockDisplayName = (symbol: string) => {
    const stock = allStocks.find(s => s.symbol === symbol);
    return stock ? stock.name : symbol;
  };

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* Compact Search Input - Inline Design */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />
        </div>
        <input
          type="text"
          value={isOpen ? searchTerm : (selectedStock ? `${selectedStock} - ${getStockDisplayName(selectedStock)}` : '')}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => {
            setIsOpen(true);
            setSearchTerm('');
          }}
          onBlur={(e) => {
            // Check if the blur is due to clicking on a dropdown item
            // If clicking on dropdown, don't close it
            const relatedTarget = e.relatedTarget as HTMLElement;
            if (dropdownRef.current && dropdownRef.current.contains(relatedTarget)) {
              return;
            }
            // Delay closing to allow click on dropdown items
            setTimeout(() => {
              // Double-check if dropdown is still supposed to be open
              if (dropdownRef.current && !dropdownRef.current.contains(document.activeElement)) {
                setIsOpen(false);
              }
            }, 200);
          }}
          placeholder={selectedStock ? `${selectedStock} - ${getStockDisplayName(selectedStock)}` : "Search stocks..."}
          className="w-full pl-9 pr-8 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {searchTerm && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setSearchTerm('');
              setIsOpen(false);
            }}
            className="absolute inset-y-0 right-0 pr-2 flex items-center"
          >
            <XMarkIcon className="h-4 w-4 text-gray-400 hover:text-white" />
          </button>
        )}
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 mt-2 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-2xl max-h-96 overflow-y-auto">
          {loadingStocks && !stocksLoaded ? (
            <div className="px-4 py-8 text-center text-gray-400">
              <p>Loading NSE stocks...</p>
              <p className="text-sm mt-1">Fetching from database ({allStocks.length} loaded so far)</p>
            </div>
          ) : Object.keys(groupedStocks).length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-400">
              <p>No stocks found</p>
              <p className="text-sm mt-1">Try searching by symbol, name, or sector</p>
            </div>
          ) : (
            <>
              {stocksLoaded && (
                <div className="px-4 py-2 text-xs text-gray-500 border-b border-gray-700">
                  {allStocks.length} stocks available ({allStocksFromAPI.length} NSE stocks + {allStocks.length - allStocksFromAPI.length} index stocks) • Search by symbol, name, or sector
                </div>
              )}
              {Object.entries(groupedStocks).map(([category, stocks]) => (
                <div key={category} className="py-2">
                  <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider bg-gray-750">
                    {category} ({stocks.length})
                  </div>
                {stocks.map((stock) => (
                  <div
                    key={stock.symbol}
                    className="px-4 py-3 hover:bg-gray-700 cursor-pointer transition-colors duration-150 flex items-center justify-between group"
                    onMouseDown={(e) => {
                      // Prevent input blur when clicking dropdown item
                      e.preventDefault();
                    }}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      // Only select symbol, do NOT navigate - navigation happens only on explicit button click
                      handleStockSelect(stock.symbol, e);
                    }}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{stock.symbol}</span>
                        {stock.category === 'Indices' ? (
                          <span className="text-xs px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded font-medium">
                            INDEX
                          </span>
                        ) : stock.sector && stock.sector !== 'Index' ? (
                          <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded">
                            {stock.sector}
                          </span>
                        ) : null}
                      </div>
                      <p className="text-sm text-gray-400 truncate mt-0.5">{stock.name}</p>
                    </div>
                    {showNavigateButton && (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          // Navigation ONLY happens on explicit button click, not on symbol selection
                          handleNavigateToChart(stock.symbol);
                        }}
                        className="ml-2 p-2 rounded-lg bg-blue-500/10 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity duration-150 hover:bg-blue-500/20"
                        title="View Chart on Comprehensive Trading Pro"
                      >
                        <ChartBarIcon className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              ))}
            </>
          )}
        </div>
      )}

    </div>
  );
};

export default StockSelector;

