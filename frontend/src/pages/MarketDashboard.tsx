import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import StockCard, { StockCardProps } from '../components/StockCard';
import { toast } from 'react-hot-toast';
import BuySellButton from '../components/BuySellButton';
import ClickableSymbol from '../components/ClickableSymbol';
import { 
  ArrowPathIcon, 
  ChartBarIcon,
  FireIcon,
  SparklesIcon,
  BoltIcon,
  NewspaperIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

// API base URL
const API_BASE = '/api/market';

// Fetch real stock data from backend using web scraper
const fetchScreenerData = async (screenerType: string): Promise<StockCardProps[]> => {
  try {
    // Use the new dashboard endpoints that use web scraper
    const response = await fetch(`${API_BASE}/dashboard/${screenerType}?limit=6`);
    if (!response.ok) {
      console.error(`API Error for ${screenerType}:`, response.status, response.statusText);
      // Try to get error details from response
      let errorMessage = `Failed to fetch ${screenerType}: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.error || errorData.message) {
          errorMessage = errorData.error || errorData.message;
        }
      } catch (e) {
        // Response is not JSON, use status text
        errorMessage = `${response.status} ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }
    const result = await response.json();
    
    console.log(`📊 ${screenerType} data:`, result);
    
    // Handle different response formats
    if (!result.success && result.error) {
      console.warn(`API returned error for ${screenerType}:`, result.error);
      return [];
    }
    
    // Convert backend format to frontend format
    const stocks = (result.data || []).map((stock: any) => ({
      symbol: stock.symbol || stock.Symbol || '',
      name: stock.name || stock.Name || stock.symbol || '',
      price: stock.price || stock.Price || 0,
      change: stock.change || stock.Change || 0,
      changePercent: stock.changePercent || stock.ChangePercent || 0,
      sector: stock.sector || stock.Sector || 'Unknown',
      volume: stock.volume || stock.Volume || 0,
      marketCap: stock.marketCap || stock.MarketCap || 0,
    })).filter((stock: any) => stock.symbol); // Filter out invalid entries
    
    return stocks;
  } catch (error: any) {
    console.error(`Error fetching ${screenerType}:`, error);
    // Return empty array instead of throwing to prevent UI crashes
    return [];
  }
};

// Fetch live indices data
const fetchIndicesData = async (): Promise<any[]> => {
  try {
    const response = await fetch(`${API_BASE}/dashboard/indices`);
    if (!response.ok) {
      console.warn('Failed to fetch indices, status:', response.status);
      throw new Error('Failed to fetch indices');
    }
    const result = await response.json();
    console.log('📊 Indices data:', result);
    return result.data || [];
  } catch (error) {
    console.error('Error fetching indices:', error);
    return [];
  }
};

interface StockCollection {
  title: string;
  icon: string;
  stocks: StockCardProps[];
  viewAllLink: string;
}

const MarketDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Live market indices
  const [indices, setIndices] = useState<any[]>([]);
  
  // Stock collections with real data
  const [collections, setCollections] = useState<StockCollection[]>([
    {
      title: 'Top Gainers',
      icon: '🚀',
      stocks: [],
      viewAllLink: '/stocks/top-gainers',
    },
    {
      title: 'Top Losers',
      icon: '📉',
      stocks: [],
      viewAllLink: '/stocks/top-losers',
    },
    {
      title: 'Only Buyers',
      icon: '💰',
      stocks: [],
      viewAllLink: '/stocks/only-buyers',
    },
    {
      title: 'Only Sellers',
      icon: '🔴',
      stocks: [],
      viewAllLink: '/stocks/only-sellers',
    },
    {
      title: 'Volume Shockers',
      icon: '📊',
      stocks: [],
      viewAllLink: '/stocks/volume-shockers',
    },
    {
      title: 'Most Active',
      icon: '⚡',
      stocks: [],
      viewAllLink: '/stocks/most-active',
    },
  ]);
  
  const [sectors, setSectors] = useState([
    { name: 'Banking', change: 1.2, color: 'text-green-600', bgColor: 'from-green-500 to-emerald-600', routeName: 'banking' },
    { name: 'IT', change: 0.8, color: 'text-green-600', bgColor: 'from-blue-500 to-cyan-600', routeName: 'it' },
    { name: 'Energy', change: -0.5, color: 'text-red-600', bgColor: 'from-orange-500 to-red-600', routeName: 'energy' },
    { name: 'Auto', change: 1.5, color: 'text-green-600', bgColor: 'from-purple-500 to-pink-600', routeName: 'automobile' },
    { name: 'Pharma', change: -0.3, color: 'text-red-600', bgColor: 'from-pink-500 to-rose-600', routeName: 'pharma' },
    { name: 'FMCG', change: 0.4, color: 'text-green-600', bgColor: 'from-indigo-500 to-blue-600', routeName: 'fmcg' },
  ]);

  const [marketIntelligence, setMarketIntelligence] = useState<any>(null);
  const [loadingIntelligence, setLoadingIntelligence] = useState(false);

  // Debug: Log state changes for news_data (only in development)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development' && marketIntelligence) {
      console.log('📰 Market Intelligence State Updated:', {
        hasNewsData: !!marketIntelligence.news_data,
        newsCount: Array.isArray(marketIntelligence.news_data) ? marketIntelligence.news_data.length : 0,
      });
    }
  }, [marketIntelligence]);

  const loadIndicesData = useCallback(async () => {
    const data = await fetchIndicesData();
    if (data.length > 0) {
      setIndices(data);
    }
  }, []);

  const loadScreenersData = useCallback(async () => {
    const screenerTypes = ['top-gainers', 'top-losers', 'only-buyers', 'only-sellers', 'volume-shockers', 'most-active'];
    
    const results = await Promise.all(
      screenerTypes.map(async (type) => {
        try {
          const stocks = await fetchScreenerData(type);
          return { type, stocks };
        } catch (error) {
          console.error(`Error fetching ${type}:`, error);
          return { type, stocks: [] };
        }
      })
    );

    setCollections(prev => prev.map(collection => {
      const result = results.find(r => {
        const typeMap: Record<string, string> = {
          'top-gainers': 'Top Gainers',
          'top-losers': 'Top Losers',
          'only-buyers': 'Only Buyers',
          'only-sellers': 'Only Sellers',
          'volume-shockers': 'Volume Shockers',
          'most-active': 'Most Active'
        };
        return typeMap[r.type] === collection.title;
      });
      return result ? { ...collection, stocks: result.stocks } : collection;
    }));
  }, []);

  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadIndicesData(),
        loadScreenersData(),
      ]);
    } catch (error) {
      console.error('Error loading market data:', error);
      toast.error('Failed to load market data');
    } finally {
      setLoading(false);
    }
  }, [loadIndicesData, loadScreenersData]);

  const loadMarketIntelligence = useCallback(async () => {
    setLoadingIntelligence(true);
    try {
      // Use direct backend URL (CORS is configured in backend)
      const backendUrl = 'http://localhost:8000/api/intelligent-trading/market-intelligence';
      
      console.log('📰 Fetching market intelligence from direct backend URL:', backendUrl);
      const response = await fetch(backendUrl, {
        headers: {
          'Content-Type': 'application/json',
        },
        mode: 'cors',
      });
      
      if (!response.ok) {
        console.error('❌ API Response not OK:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('❌ Error response body:', errorText);
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // CRITICAL: Log the RAW response before any processing
      console.log('📰 RAW API Response (before processing):', JSON.stringify(result, null, 2));
      console.log('📰 RAW news_data value:', result.data?.news_data);
      console.log('📰 RAW news_data type:', typeof result.data?.news_data);
      console.log('📰 RAW news_data isArray:', Array.isArray(result.data?.news_data));
      console.log('📰 RAW news_data length:', Array.isArray(result.data?.news_data) ? result.data.news_data.length : 'N/A');
      
      // CRITICAL FIX: If news_data is empty in the response, force a retry with direct backend URL
      if (!result.data?.news_data || (Array.isArray(result.data.news_data) && result.data.news_data.length === 0)) {
        console.warn('⚠️ CRITICAL: Response has empty news_data, retrying with direct backend URL');
        try {
          const directResponse = await fetch('http://localhost:8000/api/intelligent-trading/market-intelligence', {
            headers: {
              'Content-Type': 'application/json',
            },
            mode: 'cors',
          });
          if (directResponse.ok) {
            const directResult = await directResponse.json();
            console.log('📰 Direct backend response:', {
              hasData: !!directResult.data,
              newsCount: Array.isArray(directResult.data?.news_data) ? directResult.data.news_data.length : 0
            });
            if (directResult.data?.news_data && Array.isArray(directResult.data.news_data) && directResult.data.news_data.length > 0) {
              console.log('✅ Using news from direct backend call');
              result.data = directResult.data; // Replace with direct backend data
            }
          }
        } catch (directError) {
          console.error('❌ Direct backend call also failed:', directError);
        }
      }
      
      console.log('📰 Market Intelligence API Response:', {
        status: response.status,
        ok: response.ok,
        hasSuccess: !!result.success,
        hasData: !!result.data,
        dataKeys: result.data ? Object.keys(result.data) : 'No data',
        newsData: result.data?.news_data,
        newsDataLength: Array.isArray(result.data?.news_data) ? result.data.news_data.length : 'Not an array',
        newsDataType: typeof result.data?.news_data,
        isNewsArray: Array.isArray(result.data?.news_data),
        firstNewsItem: Array.isArray(result.data?.news_data) && result.data.news_data.length > 0 
          ? result.data.news_data[0] 
          : null,
        fullResult: result  // Full result for debugging
      });
      
      // Handle both success and error cases - prioritize news_data
      if (result.data) {
        // CRITICAL: Get news_data directly from result.data - don't transform it yet
        let newsData = result.data.news_data;
        
        console.log('📰 BEFORE normalization - newsData:', {
          value: newsData,
          type: typeof newsData,
          isArray: Array.isArray(newsData),
          length: Array.isArray(newsData) ? newsData.length : 'N/A',
          rawValue: JSON.stringify(newsData).substring(0, 200)
        });
        
        // Ensure news_data is always an array
        if (!newsData) {
          console.warn('⚠️ news_data is null/undefined, setting to empty array');
          newsData = [];
        } else if (!Array.isArray(newsData)) {
          console.warn('⚠️ news_data is not an array, converting:', typeof newsData, newsData);
          // If it's an object, try to convert it
          if (typeof newsData === 'object' && newsData !== null) {
            // Check if it has array-like properties
            if (newsData.length !== undefined) {
              newsData = Array.from(newsData);
            } else {
              // It's a plain object, convert to array
              newsData = [];
            }
          } else {
            newsData = [];
          }
        }
        
        console.log('📰 AFTER normalization - newsData:', {
          value: newsData,
          type: typeof newsData,
          isArray: Array.isArray(newsData),
          length: Array.isArray(newsData) ? newsData.length : 'N/A'
        });
        
        console.log('📰 Market Intelligence received:', {
          success: result.success,
          hasNewsData: !!newsData,
          newsCount: Array.isArray(newsData) ? newsData.length : 0,
          newsDataType: Array.isArray(newsData) ? 'array' : typeof newsData,
          isArray: Array.isArray(newsData),
          newsDataSample: Array.isArray(newsData) && newsData.length > 0 ? newsData[0] : newsData,
          newsDataFull: newsData  // Full array for debugging
        });
        
        // CRITICAL: Ensure newsData is not empty before setting state
        // If newsData is empty, try to get it directly from the raw response
        if (!newsData || !Array.isArray(newsData) || newsData.length === 0) {
          console.error('❌ CRITICAL: newsData is empty after normalization!', {
            newsData,
            type: typeof newsData,
            isArray: Array.isArray(newsData),
            length: Array.isArray(newsData) ? newsData.length : 'N/A',
            originalData: result.data?.news_data,
            originalDataType: typeof result.data?.news_data,
            originalIsArray: Array.isArray(result.data?.news_data),
            originalLength: Array.isArray(result.data?.news_data) ? result.data.news_data.length : 'N/A',
            fullResultData: result.data
          });
          
          // Try to recover from raw response
          const rawNewsData = result.data?.news_data;
          if (rawNewsData && Array.isArray(rawNewsData) && rawNewsData.length > 0) {
            console.log('✅ Recovered newsData from raw response:', rawNewsData.length, 'articles');
            newsData = rawNewsData;
          } else {
            // Force fallback - this should never happen if backend is working
            console.warn('⚠️ Using fallback news - backend returned empty array');
            newsData = [{
              title: "Market Update Available",
              description: "News data is being loaded. Please refresh if this persists.",
              url: "#",
              source: "System",
              published_at: new Date().toISOString(),
              sentiment: "neutral",
              symbols_mentioned: []
            }];
          }
        }
        
        // Update result.data with normalized news_data
        const normalizedData = {
          ...result.data,
          news_data: newsData
        };
        
        console.log('📰 Setting marketIntelligence state with:', {
          newsCount: normalizedData.news_data?.length || 0,
          newsDataType: typeof normalizedData.news_data,
          isArray: Array.isArray(normalizedData.news_data),
          firstItem: normalizedData.news_data?.[0] || null,
          allKeys: Object.keys(normalizedData),
          fullNewsData: normalizedData.news_data  // Full array
        });
        
        setMarketIntelligence(normalizedData);
      } else {
        console.warn('Market intelligence response missing data:', result);
        // Set empty state to prevent undefined errors
        setMarketIntelligence({
          news_data: [],
          market_overview: {},
          market_sentiment: {},
          key_insights: []
        });
      }
    } catch (error: any) {
      console.error('❌ Error fetching market intelligence:', error);
      console.error('❌ Error details:', {
        message: error?.message,
        stack: error?.stack,
        name: error?.name
      });
      // Set empty state on error
      setMarketIntelligence({
        news_data: [],
        market_overview: {},
        market_sentiment: {},
        key_insights: []
      });
    } finally {
      setLoadingIntelligence(false);
    }
  }, []);

  // Load real data on mount
  useEffect(() => {
    loadAllData();
    loadMarketIntelligence();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadIndicesData();
    }, 30000);
    
    // Refresh intelligence every 5 minutes
    const intelligenceInterval = setInterval(() => {
      loadMarketIntelligence();
    }, 5 * 60 * 1000);
    
    return () => {
      clearInterval(interval);
      clearInterval(intelligenceInterval);
    };
  }, [loadAllData, loadMarketIntelligence, loadIndicesData]);
  
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadAllData();
      toast.success('Market data refreshed!');
    } catch (error) {
      toast.error('Failed to refresh data');
    } finally {
      setRefreshing(false);
    }
  };

  const handleStockClick = (symbol: string) => {
    // Navigate to chart with dynamic symbol
    navigate(`/comprehensive-trading-pro?symbol=${symbol}`);
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-10 w-10 border-2 border-primary border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">Loading market dashboard…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Pro Header */}
      <div className="bg-card border border-border rounded-2xl p-5 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-foreground">
              Market Dashboard
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Live overview of indices, movers, sectors, and market intelligence.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-foreground hover:bg-muted transition disabled:opacity-60"
            >
              <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing' : 'Refresh'}
            </button>
            <button
              onClick={() => navigate('/comprehensive-trading-pro')}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-95 transition"
            >
              <ChartBarIcon className="h-4 w-4" />
              Pro Chart
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-10">
        {/* Market Indices - Modern Cards */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-muted rounded-xl border border-border">
                <ChartBarIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Market Indices
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Live market data</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live</span>
              </div>
              <button
                onClick={() => navigate('/stocks')}
                className="ml-4 inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-foreground hover:bg-muted transition"
              >
                <span>View All Indexes</span>
                <span>→</span>
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {indices.map((index, i) => {
              const isPositive = index.change >= 0;
              return (
                <div 
                  key={i} 
                  onClick={() => {
                    // Map index names to index keys for navigation
                    const indexMap: Record<string, string> = {
                      'NIFTY 50': 'NIFTY',
                      'SENSEX': 'SENSEX',
                      'BANK NIFTY': 'BANKNIFTY',
                      'NIFTY IT': 'NIFTYIT'
                    };
                    const indexKey = indexMap[index.name] || 'NIFTY';
                    navigate(`/stocks?index=${indexKey}`);
                  }}
                  className="group rounded-2xl bg-card border border-border shadow-sm hover:shadow-md transition p-5 cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-muted-foreground truncate">{index.name}</div>
                      <div className="mt-2 text-2xl font-semibold text-foreground">
                      {index.value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${isPositive ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'}`}>
                      {isPositive ? '+' : ''}{index.changePercent.toFixed(2)}%
                    </div>
                  </div>
                  <div className={`mt-2 text-sm font-medium ${isPositive ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}`}>
                    {isPositive ? '+' : ''}{index.change.toFixed(2)}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Stock Collections - Enhanced Design */}
        {collections.map((collection, collectionIndex) => (
          <section key={collectionIndex}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl text-2xl">
                  {collection.icon}
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {collection.title}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Top performing stocks</p>
                </div>
              </div>
              <button 
                onClick={() => navigate(collection.viewAllLink)}
                className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl font-semibold shadow-lg transition-all duration-200 flex items-center gap-2"
              >
                <span>View all</span>
                <span>→</span>
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {collection.stocks.map((stock, stockIndex) => (
                <StockCard
                  key={stockIndex}
                  {...stock}
                  onClick={() => handleStockClick(stock.symbol)}
                  onAddToWatchlist={() => toast.success(`Added ${stock.symbol} to watchlist!`)}
                />
              ))}
            </div>
          </section>
        ))}

        {/* Market Cap Categories - Modern Gradient Cards */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl">
              <SparklesIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Browse by Market Cap
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Explore stocks by market capitalization</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {['Large Cap', 'Mid Cap', 'Small Cap'].map((cap, i) => {
              const gradients = [
                'from-blue-500 via-purple-500 to-pink-500',
                'from-purple-500 via-pink-500 to-red-500',
                'from-pink-500 via-red-500 to-orange-500'
              ];
              return (
                <button
                  key={i}
                  onClick={() => navigate(`/stocks/market-cap/${cap.toLowerCase().replace(' ', '-')}`)}
                  className={`group relative overflow-hidden bg-gradient-to-br ${gradients[i]} rounded-2xl p-8 text-left shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02]`}
                >
                  <div className="absolute inset-0 bg-black/10 group-hover:bg-black/20 transition-colors"></div>
                  <div className="relative z-10">
                    <div className="text-4xl mb-3">💎</div>
                    <div className="text-2xl font-bold text-white mb-2">{cap} Stocks</div>
                    <div className="text-sm text-white/90 flex items-center gap-2">
                      <span>Explore {cap.toLowerCase()} stocks</span>
                      <span className="text-lg group-hover:translate-x-1 transition-transform">→</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* Sector Performance - Enhanced */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl">
              <FireIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Sector Performance
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Real-time sector-wise analysis</p>
            </div>
          </div>
          <div className="relative overflow-hidden rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 shadow-2xl p-6">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {sectors.map((sector, i) => (
                <button
                  key={i}
                  onClick={() => navigate(`/stocks/sector/${sector.routeName}`)}
                  className={`group relative overflow-hidden bg-gradient-to-br ${sector.bgColor} rounded-xl p-5 text-center shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1`}
                >
                  <div className="absolute inset-0 bg-black/10 group-hover:bg-black/20 transition-colors"></div>
                  <div className="relative z-10">
                    <div className="text-sm font-semibold text-white mb-2">{sector.name}</div>
                    <div className={`text-xl font-bold text-white`}>
                      {sector.change >= 0 ? '+' : ''}{sector.change.toFixed(1)}%
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Market Intelligence - News & Sentiment */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl">
              <NewspaperIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Market Intelligence
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">News sentiment & market analysis</p>
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Market Sentiment Card */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Market Sentiment</h3>
                <LightBulbIcon className="h-5 w-5 text-yellow-500" />
              </div>
              {loadingIntelligence ? (
                <div className="text-center py-8 text-gray-500">Loading sentiment...</div>
              ) : marketIntelligence?.market_sentiment ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Overall Sentiment</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      marketIntelligence.market_overview?.overall_sentiment === 'bullish' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                        : marketIntelligence.market_overview?.overall_sentiment === 'bearish'
                        ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {marketIntelligence.market_overview?.overall_sentiment?.toUpperCase() || 'NEUTRAL'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Fear & Greed Index</span>
                    <span className="text-lg font-bold text-gray-900 dark:text-white">
                      {marketIntelligence.market_sentiment?.fear_greed_index || 50}/100
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div 
                      className={`h-2.5 rounded-full ${
                        (marketIntelligence.market_sentiment?.fear_greed_index || 50) > 60
                          ? 'bg-green-500'
                          : (marketIntelligence.market_sentiment?.fear_greed_index || 50) < 40
                          ? 'bg-red-500'
                          : 'bg-yellow-500'
                      }`}
                      style={{ width: `${marketIntelligence.market_sentiment?.fear_greed_index || 50}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Market Trend</span>
                    <span className="text-sm font-semibold text-gray-900 dark:text-white capitalize">
                      {marketIntelligence.market_overview?.market_trend || 'Sideways'}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">No sentiment data available</div>
              )}
            </div>

            {/* Key Insights Card */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Key Insights</h3>
                <SparklesIcon className="h-5 w-5 text-purple-500" />
              </div>
              {loadingIntelligence ? (
                <div className="text-center py-8 text-gray-500">Loading insights...</div>
              ) : marketIntelligence?.key_insights && marketIntelligence.key_insights.length > 0 ? (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {marketIntelligence.key_insights.slice(0, 5).map((insight: string, index: number) => (
                    <div key={index} className="flex items-start gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="text-purple-500 mt-1">•</span>
                      <span className="text-sm text-gray-700 dark:text-gray-300">{insight}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">No insights available</div>
              )}
            </div>
          </div>
          
          {/* Market News Section - Debug Info */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-4 p-2 bg-yellow-100 dark:bg-yellow-900/20 text-xs font-mono space-y-1">
              <div>Debug: marketIntelligence exists: {marketIntelligence ? 'Yes' : 'No'}</div>
              <div>news_data exists: {marketIntelligence?.news_data ? 'Yes' : 'No'}</div>
              <div>news_data type: {typeof marketIntelligence?.news_data}</div>
              <div>news_data isArray: {Array.isArray(marketIntelligence?.news_data) ? 'Yes' : 'No'}</div>
              <div>news_data length: {Array.isArray(marketIntelligence?.news_data) ? marketIntelligence.news_data.length : 'N/A'}</div>
              {marketIntelligence?.news_data && (
                <div>news_data sample: {JSON.stringify(Array.isArray(marketIntelligence.news_data) ? marketIntelligence.news_data.slice(0, 1) : marketIntelligence.news_data).substring(0, 200)}</div>
              )}
            </div>
          )}

          {/* Market News Section */}
          <div className="mt-6 bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl p-6 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <NewspaperIcon className="h-5 w-5 text-indigo-500" />
              Latest Market News
              {marketIntelligence?.news_data && Array.isArray(marketIntelligence.news_data) && (
                <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                  ({marketIntelligence.news_data.length} articles)
                </span>
              )}
            </h3>
            
            {loadingIntelligence ? (
              <div className="text-center py-8 text-gray-500">Loading news...</div>
            ) : (() => {
              // Safely check news_data
              const newsData = marketIntelligence?.news_data;
              const isValidNewsArray = Array.isArray(newsData) && newsData.length > 0;
              
              if (!isValidNewsArray) {
                return (
                  <div className="text-center py-8">
                    <p className="text-gray-500 dark:text-gray-400 mb-2">No news available at the moment</p>
                    <button
                      onClick={loadMarketIntelligence}
                      className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      Refresh news
                    </button>
                  </div>
                );
              }
              
              return (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {newsData.slice(0, 10).map((news: any, index: number) => {
                    const symbols = news.symbols_mentioned || [];
                    return (
                      <div key={index} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors border border-gray-200 dark:border-gray-600">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                              {news.title}
                            </h4>
                            {news.description && (
                              <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                                {news.description}
                              </p>
                            )}
                            
                            {/* Stock Symbols with Buy/Sell buttons */}
                            {symbols.length > 0 && (
                              <div className="flex flex-wrap items-center gap-2 mb-3">
                                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Stocks mentioned:</span>
                                {symbols.map((symbol: string) => (
                                  <div key={symbol} className="flex items-center gap-1.5 bg-blue-100 dark:bg-blue-900/30 px-2.5 py-1 rounded-md border border-blue-200 dark:border-blue-800">
                                    <ClickableSymbol symbol={symbol} variant="bold" className="text-xs" />
                                    <BuySellButton
                                      symbol={symbol}
                                      currentPrice={0} // Will fetch current price in modal
                                      size="sm"
                                    />
                                  </div>
                                ))}
                              </div>
                            )}
                            
                            {/* Impact Indicators */}
                            <div className="flex flex-wrap items-center gap-2 mb-3">
                              {news.sentiment && (
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  news.sentiment === 'positive' 
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                    : news.sentiment === 'negative'
                                    ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                                }`}>
                                  {news.sentiment === 'positive' ? '📈' : news.sentiment === 'negative' ? '📉' : '➡️'} {news.sentiment}
                                  {news.sentiment_score !== undefined && (
                                    <span className="ml-1 opacity-75">({(news.sentiment_score * 100).toFixed(0)}%)</span>
                                  )}
                                </span>
                              )}
                              
                              {news.market_impact && news.market_impact !== 'neutral' && (
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  news.market_impact === 'high'
                                    ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
                                    : news.market_impact === 'medium'
                                    ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                                    : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                                }`}>
                                  {news.market_impact === 'high' ? '🔥' : news.market_impact === 'medium' ? '⚡' : '💡'} Market: {news.market_impact}
                                </span>
                              )}
                              
                              {news.impact_score !== undefined && news.impact_score > 0 && (
                                <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                                  Impact: {(news.impact_score * 100).toFixed(0)}%
                                </span>
                              )}
                            </div>
                            
                            {/* Stock-specific Impact */}
                            {news.stock_impact && Object.keys(news.stock_impact).length > 0 && (
                              <div className="mb-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                                <div className="text-xs font-medium text-blue-700 dark:text-blue-300 mb-1">Stock Impact:</div>
                                <div className="flex flex-wrap gap-2">
                                  {Object.entries(news.stock_impact).map(([symbol, impact]: [string, any]) => (
                                    <div key={symbol} className="flex items-center gap-1 text-xs">
                                      <ClickableSymbol symbol={symbol} variant="bold" className="text-xs" />
                                      <span className="text-gray-600 dark:text-gray-400">:</span>
                                      <span className={`px-1.5 py-0.5 rounded ${
                                        impact.impact === 'high'
                                          ? 'bg-orange-200 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300'
                                          : impact.impact === 'medium'
                                          ? 'bg-yellow-200 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300'
                                          : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                                      }`}>
                                        {impact.impact}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-500">
                              <span>{news.source}</span>
                              {news.published_at && (
                                <span>{new Date(news.published_at).toLocaleDateString()}</span>
                              )}
                            </div>
                          </div>
                          {news.url && news.url !== '#' && (
                            <a 
                              href={news.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 text-xs font-medium whitespace-nowrap"
                            >
                              Read →
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })()}
          </div>
        </section>

        {/* Quick Links - Modern Cards */}
        <section className="pb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-xl">
              <BoltIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Quick Access
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Navigate to key features</p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            {[
              { icon: '🎯', title: 'Analysis Tools', path: '/comprehensive-trading', color: 'from-blue-500 to-cyan-600' },
              { icon: '📊', title: 'Pro Charts', path: '/comprehensive-trading-pro', color: 'from-purple-500 to-pink-600' },
              { icon: '⭐', title: 'Watchlist', path: '/watchlist', color: 'from-yellow-500 to-orange-600' },
              { icon: '🔔', title: 'Alerts', path: '/alerts', color: 'from-red-500 to-rose-600' },
            ].map((link, i) => (
              <button
                key={i}
                onClick={() => navigate(link.path)}
                className={`group relative overflow-hidden bg-gradient-to-br ${link.color} rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 hover:scale-[1.02]`}
              >
                <div className="absolute inset-0 bg-black/10 group-hover:bg-black/20 transition-colors"></div>
                <div className="relative z-10 text-center">
                  <div className="text-4xl mb-3">{link.icon}</div>
                  <div className="text-sm font-bold text-white">{link.title}</div>
                </div>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default MarketDashboard;
