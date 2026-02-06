import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { 
  ChartBarIcon, 
  MagnifyingGlassIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BuildingOffice2Icon,
  ChartPieIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import StockSelector from '../components/StockSelector';
import candleDataApi from '../services/candleDataApi';
import { indexData, getAllSectors, IndexStock } from '../data/indexStocks';
import StockCard, { StockCardProps } from '../components/StockCard';
import { toast } from 'react-hot-toast';
import BuySellButton from '../components/BuySellButton';
import ClickableSymbol from '../components/ClickableSymbol';

interface StockPrice {
  price: number;
  change: number;
  changePercent: number;
}

interface SectorData {
  sector: string;
  totalGain: number;
  totalLoss: number;
  gainCount: number;
  lossCount: number;
  totalValue: number;
}

const API_BASE = '/api/market';

// Fetch screener data - Get ALL stocks (no limit)
const fetchScreenerData = async (screenerType: string): Promise<StockCardProps[]> => {
  try {
    // Request maximum allowed (100) to get all available stocks
    const response = await fetch(`${API_BASE}/dashboard/${screenerType}?limit=100`);
    if (!response.ok) {
      console.error(`API Error for ${screenerType}:`, response.status, response.statusText);
      throw new Error(`Failed to fetch ${screenerType}: ${response.status}`);
    }
    const result = await response.json();
    
    console.log(`📊 Fetched ${screenerType}:`, {
      success: result.success,
      count: result.count || result.data?.length || 0,
      data: result.data?.slice(0, 3) // Log first 3 for debugging
    });
    
    if (!result.success) {
      console.warn(`API returned error for ${screenerType}:`, result.error);
      return [];
    }
    
    const stocks = (result.data || []).map((stock: any) => ({
      symbol: stock.symbol || stock.Symbol || '',
      name: stock.name || stock.Name || stock.symbol || '',
      price: stock.price || stock.Price || stock.last_price || 0,
      change: stock.change || stock.Change || stock.change_amount || 0,
      changePercent: stock.changePercent || stock.change_percent || stock.ChangePercent || 0,
      sector: stock.sector || stock.Sector || 'Others',
      volume: stock.volume || stock.Volume || 0,
      marketCap: stock.marketCap || stock.market_cap || stock.MarketCap || '',
    }));
    
    console.log(`✅ Processed ${stocks.length} stocks for ${screenerType}`);
    return stocks;
  } catch (error) {
    console.error(`❌ Error fetching ${screenerType}:`, error);
    toast.error(`Failed to load ${screenerType}. Please try again.`);
    return [];
  }
};

const Stocks: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const indexFromUrl = searchParams.get('index');
  const [selectedIndex, setSelectedIndex] = useState<string>(indexFromUrl?.toUpperCase() || 'NIFTY');
  const [selectedSector, setSelectedSector] = useState<string>('All');
  const [stockPrices, setStockPrices] = useState<Record<string, StockPrice>>({});
  const [loadingPrices, setLoadingPrices] = useState(false);
  const [indices, setIndices] = useState<Record<string, StockPrice>>({});
  const [loadingIndices, setLoadingIndices] = useState(false);
  const [screenerStocks, setScreenerStocks] = useState<StockCardProps[]>([]);
  const [screenerType, setScreenerType] = useState<string | null>(null);
  const [loadingScreener, setLoadingScreener] = useState(false);
  const [sortField, setSortField] = useState<'price' | 'change' | 'changePercent' | 'volume' | 'symbol' | 'name'>('changePercent');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [indexSortField, setIndexSortField] = useState<'price' | 'change' | 'changePercent' | 'symbol' | 'name' | 'sector'>('changePercent');
  const [indexSortOrder, setIndexSortOrder] = useState<'asc' | 'desc'>('desc');

  const currentIndex = indexData[selectedIndex];
  const currentStocks = currentIndex?.stocks || [];
  
  // Handle index selection from URL parameter
  useEffect(() => {
    const indexFromUrl = searchParams.get('index');
    if (indexFromUrl) {
      const upperIndex = indexFromUrl.toUpperCase();
      if (upperIndex in indexData) {
        setSelectedIndex(upperIndex);
      }
    }
  }, [searchParams]);

  // Debug logging
  useEffect(() => {
    console.log('Current Index:', selectedIndex, 'Stocks:', currentStocks.length);
    console.log('Available Indexes:', Object.keys(indexData));
  }, [selectedIndex, currentStocks.length]);

  // Filter stocks by sector
  const filteredStocks = selectedSector === 'All' 
    ? currentStocks 
    : currentStocks.filter(s => s.sector === selectedSector);

  // Get unique sectors for current index
  const sectors = ['All', ...Array.from(new Set(currentStocks.map(s => s.sector)))].sort();

  // Sort filtered index stocks
  const sortedFilteredStocks = useMemo(() => {
    if (!filteredStocks.length) return [];
    
    const sorted = [...filteredStocks].sort((a, b) => {
      const aPrice = stockPrices[a.symbol];
      const bPrice = stockPrices[b.symbol];
      
      let aValue: number | string = 0;
      let bValue: number | string = 0;
      
      switch (indexSortField) {
        case 'price':
          aValue = aPrice?.price || 0;
          bValue = bPrice?.price || 0;
          break;
        case 'change':
          aValue = aPrice?.change || 0;
          bValue = bPrice?.change || 0;
          break;
        case 'changePercent':
          aValue = aPrice?.changePercent || 0;
          bValue = bPrice?.changePercent || 0;
          break;
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case 'name':
          aValue = a.name;
          bValue = b.name;
          break;
        case 'sector':
          aValue = a.sector;
          bValue = b.sector;
          break;
      }
      
      if (indexSortField === 'symbol' || indexSortField === 'name' || indexSortField === 'sector') {
        const comparison = String(aValue).localeCompare(String(bValue));
        return indexSortOrder === 'asc' ? comparison : -comparison;
      }
      
      return indexSortOrder === 'asc' ? (aValue as number) - (bValue as number) : (bValue as number) - (aValue as number);
    });
    
    return sorted;
  }, [filteredStocks, stockPrices, indexSortField, indexSortOrder]);

  const handleIndexSort = (field: typeof indexSortField) => {
    if (indexSortField === field) {
      setIndexSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setIndexSortField(field);
      setIndexSortOrder('desc');
    }
  };

  // Calculate sector-wise gain/loss data
  const sectorData = useMemo(() => {
    const sectorMap: Record<string, SectorData> = {};

    currentStocks.forEach(stock => {
      if (!sectorMap[stock.sector]) {
        sectorMap[stock.sector] = {
          sector: stock.sector,
          totalGain: 0,
          totalLoss: 0,
          gainCount: 0,
          lossCount: 0,
          totalValue: 0
        };
      }

      const price = stockPrices[stock.symbol];
      if (price) {
        sectorMap[stock.sector].totalValue += Math.abs(price.changePercent);
        if (price.changePercent > 0) {
          sectorMap[stock.sector].totalGain += price.changePercent;
          sectorMap[stock.sector].gainCount++;
        } else if (price.changePercent < 0) {
          sectorMap[stock.sector].totalLoss += Math.abs(price.changePercent);
          sectorMap[stock.sector].lossCount++;
        }
      }
    });

    return Object.values(sectorMap);
  }, [currentStocks, stockPrices]);

  // Prepare data for gain pie chart
  const gainPieData = useMemo(() => {
    return sectorData
      .filter(s => s.totalGain > 0)
      .map(s => ({
        name: s.sector,
        value: s.totalGain,
        count: s.gainCount
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10); // Top 10 sectors
  }, [sectorData]);

  // Prepare data for loss pie chart
  const lossPieData = useMemo(() => {
    return sectorData
      .filter(s => s.totalLoss > 0)
      .map(s => ({
        name: s.sector,
        value: s.totalLoss,
        count: s.lossCount
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10); // Top 10 sectors
  }, [sectorData]);

  // Color palette for pie charts
  const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8',
    '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff'
  ];

  // Detect screener type or sector from URL
  useEffect(() => {
    const path = location.pathname;
    const screenerTypes = ['top-gainers', 'top-losers', 'only-buyers', 'only-sellers', 'volume-shockers', 'most-active'];
    const detectedType = screenerTypes.find(type => path.includes(type));
    
    // Check for sector route: /stocks/sector/{sectorName}
    const sectorMatch = path.match(/\/stocks\/sector\/(.+)/);
    const sectorName = sectorMatch ? sectorMatch[1] : null;
    
    if (detectedType) {
      setScreenerType(detectedType);
      setSelectedSector('All'); // Reset sector filter for screeners
      setLoadingScreener(true);
      fetchScreenerData(detectedType)
        .then(data => {
          console.log(`Loaded ${data.length} stocks for ${detectedType}:`, data);
          setScreenerStocks(data);
          setLoadingScreener(false);
          // Auto-sort by changePercent descending for gainers/losers
          if (detectedType === 'top-gainers' || detectedType === 'top-losers') {
            setSortField('changePercent');
            setSortOrder('desc');
          } else if (detectedType === 'volume-shockers' || detectedType === 'most-active') {
            setSortField('volume');
            setSortOrder('desc');
          }
        })
        .catch(error => {
          console.error('Error loading screener data:', error);
          toast.error(`Failed to load ${detectedType}`);
          setLoadingScreener(false);
        });
    } else if (sectorName) {
      // Sector filter mode - filter all index stocks by sector
      setScreenerType(null);
      setScreenerStocks([]);
      
      // Map route names to actual sector names in data
      const sectorMap: Record<string, string> = {
        'banking': 'Banking',
        'it': 'IT',
        'energy': 'Energy',
        'automobile': 'Automobile',
        'auto': 'Automobile', // Support both 'auto' and 'automobile'
        'pharma': 'Pharma',
        'pharmaceutical': 'Pharma',
        'fmcg': 'FMCG',
        'telecom': 'Telecom',
        'financial-services': 'Financial Services',
        'consumer-durables': 'Consumer Durables',
        'cement': 'Cement',
        'power': 'Power',
        'engineering': 'Engineering',
        'infrastructure': 'Infrastructure',
        'metals': 'Metals',
        'mining': 'Mining',
        'oil-gas': 'Oil & Gas',
        'steel': 'Steel',
        'insurance': 'Insurance',
        'diversified': 'Diversified',
        'chemicals': 'Chemicals'
      };
      
      // Normalize sector name: handle lowercase, uppercase, and special cases
      const normalizedRoute = sectorName.toLowerCase();
      const mappedSector = sectorMap[normalizedRoute] || 
        (normalizedRoute.charAt(0).toUpperCase() + normalizedRoute.slice(1));
      
      // Check if the mapped sector exists in available sectors
      const availableSectors = getAllSectors();
      const finalSector = availableSectors.includes(mappedSector) ? mappedSector : 'All';
      
      setSelectedSector(finalSector);
      // Auto-sort by changePercent descending for sector view
      setIndexSortField('changePercent');
      setIndexSortOrder('desc');
    } else {
      setScreenerType(null);
      setScreenerStocks([]);
      setSelectedSector('All');
    }
  }, [location.pathname]);

  // Sort screener stocks
  const sortedScreenerStocks = useMemo(() => {
    if (!screenerStocks.length) return [];
    
    const sorted = [...screenerStocks].sort((a, b) => {
      let aValue: number = 0;
      let bValue: number = 0;
      
      switch (sortField) {
        case 'price':
          aValue = a.price || 0;
          bValue = b.price || 0;
          break;
        case 'change':
          aValue = a.change || 0;
          bValue = b.change || 0;
          break;
        case 'changePercent':
          aValue = a.changePercent || 0;
          bValue = b.changePercent || 0;
          break;
        case 'volume':
          aValue = a.volume || 0;
          bValue = b.volume || 0;
          break;
        case 'symbol':
          aValue = a.symbol.localeCompare(b.symbol);
          bValue = 0;
          break;
      }
      
      if (sortField === 'symbol') {
        return sortOrder === 'asc' ? aValue : -aValue;
      }
      
      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    });
    
    return sorted;
  }, [screenerStocks, sortField, sortOrder]);

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      // Toggle order if same field
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new field with default descending order
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // Fetch live prices for stocks in current index
  useEffect(() => {
    if (screenerType) return; // Skip if showing screener data
    
    const fetchPrices = async () => {
      setLoadingPrices(true);
      const prices: Record<string, StockPrice> = {};

      try {
        // Fetch prices for current index stocks
        for (const stock of currentStocks) {
          try {
            const response = await candleDataApi.getLatestCandle(stock.symbol);
            
            if (response.success && response.data) {
              const candle = response.data;
              const change = candle.close - candle.open;
              const changePercent = (change / candle.open) * 100;
              
              prices[stock.symbol] = {
                price: candle.close,
                change: change,
                changePercent: changePercent
              };
            }
          } catch (error) {
            console.log(`Could not fetch price for ${stock.symbol}`);
          }
          
          // Small delay to avoid overwhelming the API
          await new Promise(resolve => setTimeout(resolve, 200));
        }
      } catch (error) {
        console.error('Error fetching stock prices:', error);
      } finally {
        setStockPrices(prices);
        setLoadingPrices(false);
      }
    };

    if (currentStocks.length > 0 && !screenerType) {
      console.log(`Fetching prices for ${currentStocks.length} stocks in ${selectedIndex}`);
      fetchPrices();
    } else {
      console.log('Skipping price fetch:', { currentStocksLength: currentStocks.length, screenerType });
    }
  }, [selectedIndex, currentStocks.length, screenerType]);

  // Fetch market indices
  useEffect(() => {
    const fetchIndices = async () => {
      setLoadingIndices(true);
      const marketIndices = [
        { symbol: 'NIFTY_50', name: 'NIFTY 50' },
        { symbol: 'SENSEX', name: 'SENSEX' },
        { symbol: 'NIFTYBANK', name: 'BANK NIFTY' },
        { symbol: 'NIFTYMIDCAP50', name: 'MIDCP NIFTY' },
        { symbol: 'NIFTYFIN', name: 'FIN NIFTY' },
        { symbol: 'BANKEX', name: 'BANKEX' }
      ];

      for (const index of marketIndices) {
        try {
          const response = await candleDataApi.getLatestCandle(index.symbol);
          
          if (response.success && response.data) {
            const candle = response.data;
            const change = candle.close - candle.open;
            const changePercent = (change / candle.open) * 100;
            
            setIndices(prev => ({
              ...prev,
              [index.symbol]: {
                price: candle.close,
                change: change,
                changePercent: changePercent
              }
            }));
          }
        } catch (error) {
          console.log(`Could not fetch index ${index.symbol}`);
        }
        
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      setLoadingIndices(false);
    };

    fetchIndices();
  }, []);

  const handleViewChart = (symbol: string) => {
    navigate(`/comprehensive-trading-pro?symbol=${symbol}`);
  };

  const handleViewUnifiedAI = (symbol: string) => {
    navigate(`/unified-ai?symbol=${symbol}`);
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold">{payload[0].name}</p>
          <p className="text-blue-400">
            Value: {payload[0].value.toFixed(2)}%
          </p>
          <p className="text-gray-400 text-sm">
            Stocks: {payload[0].payload.count}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white flex items-center gap-3">
              <BuildingOffice2Icon className="h-10 w-10 text-blue-500" />
              {screenerType 
                ? screenerType.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())
                : selectedSector !== 'All' 
                  ? `${selectedSector} Stocks`
                  : 'Index Stocks'}
            </h1>
            <p className="text-gray-400 mt-2">
              {screenerType 
                ? `Viewing ${screenerType.replace('-', ' ')} stocks` 
                : selectedSector !== 'All'
                  ? `Viewing ${selectedSector} sector stocks from ${currentIndex?.name || 'selected index'}`
                  : 'Browse stocks organized by index with sector-wise gain/loss analysis'}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-gray-400">Total Stocks</p>
              <p className="text-2xl font-bold text-white">{currentStocks.length}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Sectors</p>
              <p className="text-2xl font-bold text-white">{sectors.length - 1}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Market Indices - Only show if not viewing screener */}
      {!screenerType && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">Market Indices</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(indexData).map(([key, index]) => {
                const indexPrice = indices[index.symbol];
                return (
                  <div 
                    key={key}
                    onClick={() => setSelectedIndex(key)}
                    className={`bg-gray-900/50 rounded-lg p-4 border cursor-pointer transition-all hover:scale-105 ${
                      selectedIndex === key
                        ? 'border-blue-500 bg-blue-500/20'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className={`font-semibold text-sm ${
                        selectedIndex === key ? 'text-blue-400' : 'text-white'
                      }`}>
                        {index.name}
                      </h3>
                    </div>
                    {indexPrice ? (
                      <div>
                        <p className="text-white font-bold text-lg">
                          {indexPrice.price.toFixed(2)}
                        </p>
                        <p className={`text-xs font-medium ${
                          indexPrice.changePercent >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {indexPrice.changePercent >= 0 ? '+' : ''}{indexPrice.changePercent.toFixed(2)}%
                        </p>
                      </div>
                    ) : loadingIndices ? (
                      <div className="h-8 w-16 bg-gray-700 rounded animate-pulse"></div>
                    ) : (
                      <p className="text-gray-500 text-xs">Loading...</p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Sector Pie Charts */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gains Pie Chart */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <ChartPieIcon className="h-6 w-6 text-green-500" />
                Sector Gains
              </h3>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
                {gainPieData.reduce((sum, d) => sum + d.count, 0)} stocks gaining
              </span>
            </div>
            {gainPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={gainPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {gainPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-400">
                No gains data available
              </div>
            )}
          </div>

          {/* Losses Pie Chart */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <ChartPieIcon className="h-6 w-6 text-red-500" />
                Sector Losses
              </h3>
              <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm font-medium">
                {lossPieData.reduce((sum, d) => sum + d.count, 0)} stocks losing
              </span>
            </div>
            {lossPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={lossPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {lossPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-400">
                No losses data available
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Index Info & Sector Filter - Only show if not viewing screener */}
      {!screenerType && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-white">{currentIndex?.name}</h2>
                <p className="text-gray-400 text-sm mt-1">{currentIndex?.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <FunnelIcon className="h-5 w-5 text-gray-400" />
                <span className="text-sm text-gray-400">Filter by Sector:</span>
              </div>
            </div>
            
            {/* Sector Filter */}
            <div className="flex gap-2 flex-wrap mb-4">
              {sectors.map(sector => (
                <button
                  key={sector}
                  onClick={() => setSelectedSector(sector)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors duration-150 ${
                    selectedSector === sector
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white'
                  }`}
                >
                  {sector}
                </button>
              ))}
            </div>

            {/* Sort Controls for Index Stocks */}
            <div className="flex items-center gap-2 flex-wrap pt-4 border-t border-gray-700">
              <span className="text-sm text-gray-400">Sort by:</span>
              {[
                { field: 'changePercent' as const, label: 'Change %' },
                { field: 'change' as const, label: 'Change' },
                { field: 'price' as const, label: 'Price' },
                { field: 'symbol' as const, label: 'Symbol' },
                { field: 'name' as const, label: 'Name' },
                { field: 'sector' as const, label: 'Sector' },
              ].map(({ field, label }) => (
                <button
                  key={field}
                  onClick={() => handleIndexSort(field)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    indexSortField === field
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white'
                  }`}
                >
                  {label}
                  {indexSortField === field && (
                    <span className="ml-1">
                      {indexSortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Screener Stocks Display */}
      {screenerType && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-white capitalize">
                {screenerType.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </h2>
              <div className="text-sm text-gray-400">
                {sortedScreenerStocks.length} stocks
              </div>
            </div>

            {/* Sort Controls */}
            <div className="mb-4 flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-400">Sort by:</span>
              {[
                { field: 'changePercent' as const, label: 'Change %' },
                { field: 'change' as const, label: 'Change' },
                { field: 'price' as const, label: 'Price' },
                { field: 'volume' as const, label: 'Volume' },
                { field: 'symbol' as const, label: 'Symbol' },
              ].map(({ field, label }) => (
                <button
                  key={field}
                  onClick={() => handleSort(field)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    sortField === field
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white'
                  }`}
                >
                  {label}
                  {sortField === field && (
                    <span className="ml-1">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {loadingScreener ? (
              <div className="text-center py-8 text-gray-400">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <p className="mt-2">Loading stocks...</p>
              </div>
            ) : sortedScreenerStocks.length > 0 ? (
              <>
                {/* Table View - Primary Display */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b-2 border-gray-700">
                        <th className="pb-3 px-4 text-sm font-bold text-gray-300 cursor-pointer hover:text-white" onClick={() => handleSort('symbol')}>
                          Symbol {sortField === 'symbol' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th className="pb-3 px-4 text-sm font-bold text-gray-300">Name</th>
                        <th className="pb-3 px-4 text-sm font-bold text-gray-300 text-right cursor-pointer hover:text-white" onClick={() => handleSort('price')}>
                          Price {sortField === 'price' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th className="pb-3 px-4 text-sm font-bold text-gray-300 text-right cursor-pointer hover:text-white" onClick={() => handleSort('change')}>
                          Change {sortField === 'change' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th className="pb-3 px-4 text-sm font-bold text-gray-300 text-right cursor-pointer hover:text-white" onClick={() => handleSort('changePercent')}>
                          Change % {sortField === 'changePercent' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th className="pb-3 px-4 text-sm font-bold text-gray-300 text-right cursor-pointer hover:text-white" onClick={() => handleSort('volume')}>
                          Volume {sortField === 'volume' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th className="pb-3 px-4 text-sm font-bold text-gray-300">Sector</th>
                        <th className="pb-3 px-4 text-sm font-bold text-gray-300 text-center">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedScreenerStocks.map((stock, index) => (
                        <tr
                          key={`${stock.symbol}-${index}`}
                          className="border-b border-gray-700/30 hover:bg-gray-700/40 transition-colors"
                        >
                          <td className="py-4 px-4">
                            <ClickableSymbol symbol={stock.symbol} variant="bold" />
                          </td>
                          <td 
                            className="py-4 px-4 text-gray-300 text-sm max-w-xs truncate cursor-pointer"
                            title={stock.name}
                            onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                          >
                            {stock.name}
                          </td>
                          <td 
                            className="py-4 px-4 text-white text-right font-semibold cursor-pointer"
                            onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                          >
                            ₹{stock.price > 0 ? stock.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                          </td>
                          <td 
                            className={`py-4 px-4 text-right font-semibold cursor-pointer ${
                              stock.change >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}
                            onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                          >
                            {stock.change !== 0 ? (stock.change >= 0 ? '+' : '') + stock.change.toFixed(2) : '-'}
                          </td>
                          <td 
                            className={`py-4 px-4 text-right font-semibold cursor-pointer ${
                              stock.changePercent >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}
                            onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                          >
                            {stock.changePercent !== 0 ? (stock.changePercent >= 0 ? '+' : '') + stock.changePercent.toFixed(2) + '%' : '-'}
                          </td>
                          <td 
                            className="py-4 px-4 text-gray-300 text-right text-sm cursor-pointer"
                            onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                          >
                            {stock.volume && stock.volume > 0 
                              ? (stock.volume >= 1000000 
                                  ? (stock.volume / 1000000).toFixed(2) + 'M' 
                                  : (stock.volume / 1000).toFixed(2) + 'K')
                              : '-'}
                          </td>
                          <td 
                            className="py-4 px-4 cursor-pointer"
                            onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                          >
                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
                              {stock.sector || 'Others'}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                            <BuySellButton
                              symbol={stock.symbol}
                              currentPrice={stock.price || 0}
                              size="sm"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <div className="text-4xl mb-4">📊</div>
                <p className="text-lg font-semibold mb-2">No stocks found for {screenerType}</p>
                <p className="text-sm">The backend API may not be returning data. Check console for details.</p>
                <button
                  onClick={() => {
                    setLoadingScreener(true);
                    fetchScreenerData(screenerType || '')
                      .then(data => {
                        setScreenerStocks(data);
                        setLoadingScreener(false);
                      })
                      .catch(() => setLoadingScreener(false));
                  }}
                  className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium"
                >
                  Retry
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stock Grid - Only show if not viewing screener */}
      {!screenerType && (
        <div className="max-w-7xl mx-auto">
          {/* Table View for Index Stocks */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">
                {currentIndex?.name} Stocks ({sortedFilteredStocks.length})
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="pb-3 text-sm font-semibold text-gray-400 cursor-pointer hover:text-white" onClick={() => handleIndexSort('symbol')}>
                      Symbol {indexSortField === 'symbol' && (indexSortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="pb-3 text-sm font-semibold text-gray-400 cursor-pointer hover:text-white" onClick={() => handleIndexSort('name')}>
                      Name {indexSortField === 'name' && (indexSortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="pb-3 text-sm font-semibold text-gray-400 text-right cursor-pointer hover:text-white" onClick={() => handleIndexSort('price')}>
                      Price {indexSortField === 'price' && (indexSortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="pb-3 text-sm font-semibold text-gray-400 text-right cursor-pointer hover:text-white" onClick={() => handleIndexSort('change')}>
                      Change {indexSortField === 'change' && (indexSortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="pb-3 text-sm font-semibold text-gray-400 text-right cursor-pointer hover:text-white" onClick={() => handleIndexSort('changePercent')}>
                      Change % {indexSortField === 'changePercent' && (indexSortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="pb-3 text-sm font-semibold text-gray-400 cursor-pointer hover:text-white" onClick={() => handleIndexSort('sector')}>
                      Sector {indexSortField === 'sector' && (indexSortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="pb-3 text-sm font-semibold text-gray-400 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedFilteredStocks.map((stock) => {
                    const price = stockPrices[stock.symbol];
                    return (
                      <tr
                        key={stock.symbol}
                        className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors"
                      >
                        <td className="py-3">
                          <ClickableSymbol symbol={stock.symbol} variant="bold" />
                        </td>
                        <td 
                          className="py-3 text-gray-300 text-sm cursor-pointer"
                          onClick={() => handleViewChart(stock.symbol)}
                        >
                          {stock.name}
                        </td>
                        <td 
                          className="py-3 text-white text-right font-medium cursor-pointer"
                          onClick={() => handleViewChart(stock.symbol)}
                        >
                          {price ? `₹${price.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}
                        </td>
                        <td 
                          className={`py-3 text-right font-medium cursor-pointer ${
                            price ? (price.change >= 0 ? 'text-green-400' : 'text-red-400') : 'text-gray-500'
                          }`}
                          onClick={() => handleViewChart(stock.symbol)}
                        >
                          {price ? `${price.change >= 0 ? '+' : ''}${price.change.toFixed(2)}` : '-'}
                        </td>
                        <td 
                          className={`py-3 text-right font-medium cursor-pointer ${
                            price ? (price.changePercent >= 0 ? 'text-green-400' : 'text-red-400') : 'text-gray-500'
                          }`}
                          onClick={() => handleViewChart(stock.symbol)}
                        >
                          {price ? `${price.changePercent >= 0 ? '+' : ''}${price.changePercent.toFixed(2)}%` : '-'}
                        </td>
                        <td 
                          className="py-3 text-gray-400 text-sm cursor-pointer"
                          onClick={() => handleViewChart(stock.symbol)}
                        >
                          {stock.sector}
                        </td>
                        <td className="py-3 text-center" onClick={(e) => e.stopPropagation()}>
                          <BuySellButton
                            symbol={stock.symbol}
                            currentPrice={price?.price || 0}
                            size="sm"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Card View for Index Stocks */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedFilteredStocks.map(stock => {
              const price = stockPrices[stock.symbol];
              return (
            <div
              key={stock.symbol}
              className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-blue-500 transition-all duration-200 group cursor-pointer"
              onClick={() => handleViewChart(stock.symbol)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl">
                    <ClickableSymbol symbol={stock.symbol} variant="bold" className="text-xl" />
                  </h3>
                  <p className="text-sm text-gray-400 mt-1">{stock.name}</p>
                  
                  {/* Live Price Display */}
                  {stockPrices[stock.symbol] ? (
                    <div className="mt-2">
                      <p className="text-2xl font-bold text-white">
                        ₹{stockPrices[stock.symbol].price.toFixed(2)}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {stockPrices[stock.symbol].changePercent >= 0 ? (
                          <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />
                        ) : (
                          <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />
                        )}
                        <span className={`text-sm font-medium ${
                          stockPrices[stock.symbol].changePercent >= 0 
                            ? 'text-green-500' 
                            : 'text-red-500'
                        }`}>
                          {stockPrices[stock.symbol].changePercent >= 0 ? '+' : ''}
                          {stockPrices[stock.symbol].changePercent.toFixed(2)}%
                        </span>
                        <span className="text-xs text-gray-500">
                          ({stockPrices[stock.symbol].change >= 0 ? '+' : ''}
                          {stockPrices[stock.symbol].change.toFixed(2)})
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-2">
                      {loadingPrices ? (
                        <div className="flex items-center gap-2">
                          <div className="animate-pulse bg-gray-700 h-8 w-32 rounded"></div>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">Price loading...</p>
                      )}
                    </div>
                  )}
                </div>
                <ChartBarIcon className="h-6 w-6 text-gray-600 group-hover:text-blue-500 transition-colors flex-shrink-0" />
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-gray-700">
                <div className="flex items-center gap-2">
                  <ChartPieIcon className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-400">{stock.sector}</span>
                </div>
                {stock.marketCap && (
                  <span className="text-sm font-medium text-blue-400">{stock.marketCap}</span>
                )}
                {stock.weight && (
                  <span className="text-xs text-gray-500">({stock.weight}%)</span>
                )}
              </div>

              <div className="mt-4 flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewChart(stock.symbol);
                  }}
                  className="flex-1 px-4 py-2 bg-blue-600/20 text-blue-400 rounded-lg font-medium hover:bg-blue-600 hover:text-white transition-colors duration-150 flex items-center justify-center gap-2 group-hover:bg-blue-600 group-hover:text-white"
                >
                  <ChartBarIcon className="h-5 w-5" />
                  View Chart
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewUnifiedAI(stock.symbol);
                  }}
                  className="flex-1 px-4 py-2 bg-purple-600/20 text-purple-400 rounded-lg font-medium hover:bg-purple-600 hover:text-white transition-colors duration-150 flex items-center justify-center gap-2"
                  title="AI Analysis"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  AI Analysis
                </button>
              </div>
            </div>
            );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default Stocks;

