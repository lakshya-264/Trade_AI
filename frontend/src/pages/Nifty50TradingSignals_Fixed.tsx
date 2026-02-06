/**
 * Working Nifty 50 Trading Signals Page
 * Fixed JSX structure
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  RefreshCw, TrendingUp, TrendingDown, BarChart3, 
  Gauge, ArrowUpDown, TrendingDown as MeanRevIcon, Zap,
  Search, Download, ExternalLink, AlertCircle, Clock, Target
} from 'lucide-react';
import { httpClient, API_CONFIG } from '../config/api';
import { toast } from 'react-hot-toast';
import { nifty50Stocks } from '../data/indexStocks';
import { AutoTradingStatus } from '../components/AutoTradingStatus';
import { TradingPerformance } from '../components/TradingPerformance';

interface StockSignal {
  symbol: string;
  name?: string;
  price: number;
  current_price: number;
  change_pct: number;
  timeframe: string;
  data_source?: string;
  last_updated?: string;
  vwap_signal: string;
  vwap_strength: string;
  momentum_signal: string;
  momentum_strength: string;
  breakout_signal: string;
  breakout_strength: string;
  mean_reversion_signal: string;
  mean_reversion_strength: string;
  scalping_signal: string;
  scalping_strength: string;
  gap_signal: string;
  gap_strength: string;
  closing_range_signal: string;
  closing_range_strength: string;
  volume_profile_signal: string;
  volume_profile_strength: string;
  news_signal: string;
  news_strength: string;
  news_sentiment: number;
  comprehensive_signal: string;
  comprehensive_strength: string;
  comprehensive_confidence: number;
  buy_count: number;
  sell_count: number;
  hold_count: number;
  entry_price?: number;
  stop_loss?: number;
  exit_price?: number;
  holding_period?: string;
  chart_analysis?: {
    method: string;
    reasoning: string;
    risk_reward_ratio: number;
    volatility: number;
    confidence: string;
    support_level: number;
    resistance_level: number;
    risk_percentage: number;
  };
  error?: string;
  userDecision?: 'BUY' | 'SELL' | 'HOLD' | null;
}

// Get Nifty 50 symbols (matching backend exactly)
const NIFTY50_SYMBOLS = [
  "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "HDFC", "ITC", "BHARTIARTL",
  "SBIN", "BAJFINANCE", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID",
  "NTPC", "TECHM", "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", "TATAMOTORS", "BRITANNIA", "EICHERMOT",
  "SHREECEM", "JSWSTEEL", "TATASTEEL", "INDUSINDBK", "COALINDIA", "GRASIM", "CIPLA", "ONGC", "TATACONSUM", "APOLLOHOSP",
  "ADANIPORTS", "BPCL", "HEROMOTOCO", "DIVISLAB", "UPL", "BAJAJ-AUTO", "TATAPOWER", "ADANIENT", "SBILIFE", "HINDALCO",
  "NMDC", "INFIBEAM", "INDIANREN", "BSE", "TANLA", "BIRLASOFT", "SUZLON", "SAKSOFT", "GAIL",
  "ADANIGREEN", "NHPC", "COCHINSHIP", "IRFC", "IRB", "BAJAJHLDNG", "HGIEL"
];

const Nifty50TradingSignalsWorking: React.FC = () => {
  const navigate = useNavigate();
  const [signals, setSignals] = useState<StockSignal[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState({ 
    current: 0, 
    total: NIFTY50_SYMBOLS.length, 
    loadingStock: '', 
    loaded: [] as string[], 
    failed: [] as string[] 
  });
  const [timeframe, setTimeframe] = useState('5m');
  const [userDecisions, setUserDecisions] = useState<{[key: string]: string}>({});
  const [signalFilter, setSignalFilter] = useState<'ALL' | 'BUY' | 'SELL' | 'HOLD'>('ALL');

  const getStockName = (symbol: string) => {
    const stockNames: { [key: string]: string } = {
      "RELIANCE": "Reliance Industries",
      "TCS": "Tata Consultancy Services", 
      "HDFCBANK": "HDFC Bank",
      "INFY": "Infosys",
      "HINDUNILVR": "Hindustan Unilever",
      "ICICIBANK": "ICICI Bank",
      "KOTAKBANK": "Kotak Mahindra Bank",
      "HDFC": "HDFC Limited",
      "ITC": "ITC Limited",
      "BHARTIARTL": "Bharti Airtel",
      "SBIN": "State Bank of India",
      "BAJFINANCE": "Bajaj Finance",
      "ASIANPAINT": "Asian Paints",
      "AXISBANK": "Axis Bank",
      "MARUTI": "Maruti Suzuki",
      "SUNPHARMA": "Sun Pharma",
      "TITAN": "Titan Company",
      "ULTRACEMCO": "UltraTech Cement",
      "NESTLEIND": "Nestle India",
      "POWERGRID": "Power Grid Corporation",
      "NTPC": "NTPC Limited",
      "TECHM": "Tech Mahindra",
      "WIPRO": "Wipro Limited",
      "HCLTECH": "HCL Technologies",
      "LT": "Larsen & Toubro",
      "BAJAJFINSV": "Bajaj Finserv",
      "DRREDDY": "Dr. Reddy's Laboratories",
      "TATAMOTORS": "Tata Motors",
      "BRITANNIA": "Britannia Industries",
      "EICHERMOT": "Eicher Motors",
      "SHREECEM": "Shree Cement",
      "JSWSTEEL": "JSW Steel",
      "TATASTEEL": "Tata Steel",
      "INDUSINDBK": "IndusInd Bank",
      "COALINDIA": "Coal India",
      "GRASIM": "Grasim Industries",
      "CIPLA": "Cipla Limited",
      "ONGC": "Oil and Natural Gas Corp",
      "TATACONSUM": "Tata Consumer Products",
      "APOLLOHOSP": "Apollo Hospitals",
      "ADANIPORTS": "Adani Ports",
      "BPCL": "Bharat Petroleum",
      "HEROMOTOCO": "Hero MotoCorp",
      "DIVISLAB": "Divi's Laboratories",
      "UPL": "UPL Limited",
      "BAJAJ-AUTO": "Bajaj Auto",
      "TATAPOWER": "Tata Power",
      "ADANIENT": "Adani Enterprises",
      "SBILIFE": "SBI Life Insurance",
      "HINDALCO": "Hindalco Industries",
      "NMDC": "NMDC Limited",
      "INFIBEAM": "Infibeam Avenues",
      "INDIANREN": "Indian Renewable Energy",
      "BSE": "BSE Limited",
      "TANLA": "Tanla Platforms",
      "BIRLASOFT": "Birlasoft",
      "SUZLON": "Suzlon Energy",
      "SAKSOFT": "Saksoft",
      "GAIL": "GAIL India",
      "ADANIGREEN": "Adani Green Energy",
      "NHPC": "NHPC Limited",
      "COCHINSHIP": "Cochin Shipyard",
      "IRFC": "IRFC Limited",
      "IRB": "IRB Infrastructure",
      "BAJAJHLDNG": "Bajaj Holdings",
      "HGIEL": "Hindustan Green Energy"
    };
    
    return stockNames[symbol] || symbol;
  };

  const fetchIndividualSignals = async (allSignals: StockSignal[], loaded: string[], failed: string[]) => {
  for (let i = 0; i < NIFTY50_SYMBOLS.length; i++) {
    const symbol = NIFTY50_SYMBOLS[i];
    
    setLoadingProgress(prev => ({
      ...prev,
      current: i + 1,
      loadingStock: symbol,
      loaded,
      failed
    }));
    
    try {
      const response = await httpClient.get(
        `/api/public/nifty50-signals?timeframe=${timeframe}&days=7&symbol=${symbol}&use_cache=false`
      );
      
      const dataList = Array.isArray(response.data) ? response.data : [response.data];
      const stockData = dataList[0]; // Get first item from the list
      if (response.success && stockData && !stockData.error) {
        allSignals.push(stockData);
        loaded.push(symbol);
      } else {
        failed.push(symbol);
      }
      
      await new Promise(resolve => setTimeout(resolve, 50));
      
    } catch (error: any) {
      failed.push(symbol);
    }
  }
};

const fetchSignals = async () => {
  setLoading(true);
  setLoadingProgress({ current: 0, total: NIFTY50_SYMBOLS.length, loadingStock: 'Loading all stocks...', loaded: [], failed: [] });
  
  try {
    const allSignals: StockSignal[] = [];
    const loaded: string[] = [];
    const failed: string[] = [];
    
    // Use bulk API endpoint to get all Nifty50 signals at once
    setLoadingProgress(prev => ({
      ...prev,
      loadingStock: 'Fetching all Nifty50 signals...'
    }));
    
    try {
      const response = await httpClient.get(
        `/api/public/nifty50-signals?timeframe=${timeframe}&days=7&use_cache=false`
      );
      
      if (response.success && response.data) {
        const signalsData = Array.isArray(response.data) ? response.data : [];
        
        // Process all signals from bulk response
        signalsData.forEach((stockData: any) => {
          if (stockData && !stockData.error && stockData.symbol) {
            allSignals.push(stockData);
            loaded.push(stockData.symbol);
          } else if (stockData && stockData.symbol) {
            failed.push(stockData.symbol);
          }
        });
        
        setLoadingProgress(prev => ({
          ...prev,
          current: NIFTY50_SYMBOLS.length,
          loadingStock: 'Completed',
          loaded,
          failed
        }));
        
      } else {
        // Fallback to individual calls if bulk fails
        console.warn('Bulk API failed, falling back to individual calls');
        await fetchIndividualSignals(allSignals, loaded, failed);
      }
      
    } catch (error: any) {
      console.warn('Bulk API error, falling back to individual calls:', error);
      await fetchIndividualSignals(allSignals, loaded, failed);
    }
      
      setSignals(allSignals);
      setLoadingProgress(prev => ({ ...prev, current: NIFTY50_SYMBOLS.length, loadingStock: '', loaded, failed }));
      
      if (allSignals.length > 0) {
        toast.success(`Loaded ${allSignals.length} stocks (${loaded.length} successful, ${failed.length} failed)`);
      } else {
        toast.error('No stocks loaded successfully');
      }
    } catch (error: any) {
      toast.error('Failed to load signals');
      console.error('Error fetching signals:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, [timeframe]);

  // Filter signals based on selected filter
  const filteredSignals = signals.filter(stock => {
    if (signalFilter === 'ALL') return true;
    return stock.comprehensive_signal === signalFilter;
  });

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-full mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Nifty 50 Trading Signals</h1>
          <p className="text-gray-600">Real-time trading signals for all Nifty 50 stocks across multiple strategies</p>
        </div>

        {loading && (
          <div className="mb-6 bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <div className="flex flex-col items-center justify-center gap-4">
              <div className="flex items-center gap-2">
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>Loading stocks individually...</span>
              </div>
              
              <div className="w-full max-w-md">
                <div className="flex justify-between text-sm mb-1">
                  <span>{loadingProgress.current}/{loadingProgress.total}</span>
                  <span>{Math.round((loadingProgress.current / loadingProgress.total) * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(loadingProgress.current / loadingProgress.total) * 100}%` }}
                  ></div>
                </div>
                {loadingProgress.loadingStock && (
                  <div className="text-xs text-gray-500 mt-1">
                    Currently loading: {loadingProgress.loadingStock}
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-green-600">
                  ✅ Loaded: {loadingProgress.loaded.length}
                </div>
                <div className="text-red-600">
                  ❌ Failed: {loadingProgress.failed.length}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="mb-6 flex gap-4 flex-wrap">
          <button
            onClick={fetchSignals}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="5m">5 Minutes</option>
            <option value="15m">15 Minutes</option>
            <option value="1h">1 Hour</option>
            <option value="1d">1 Day</option>
          </select>

          {/* Signal Filter Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => setSignalFilter('ALL')}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                signalFilter === 'ALL'
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              ALL ({signals.length})
            </button>
            <button
              onClick={() => setSignalFilter('BUY')}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                signalFilter === 'BUY'
                  ? 'bg-green-600 text-white'
                  : 'bg-green-100 text-green-700 hover:bg-green-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              BUY ({signals.filter(s => s.comprehensive_signal === 'BUY').length})
            </button>
            <button
              onClick={() => setSignalFilter('SELL')}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                signalFilter === 'SELL'
                  ? 'bg-red-600 text-white'
                  : 'bg-red-100 text-red-700 hover:bg-red-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              SELL ({signals.filter(s => s.comprehensive_signal === 'SELL').length})
            </button>
            <button
              onClick={() => setSignalFilter('HOLD')}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                signalFilter === 'HOLD'
                  ? 'bg-gray-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              HOLD ({signals.filter(s => s.comprehensive_signal === 'HOLD').length})
            </button>
          </div>
        </div>

        {!loading && signals.length > 0 && (
          <div className="mb-6 bg-white rounded-lg border border-gray-200 shadow-sm p-4">
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {signalFilter === 'ALL' ? signals.length : filteredSignals.length}
                </div>
                <div className="text-sm text-gray-600">
                  {signalFilter === 'ALL' ? 'Total Stocks' : `${signalFilter} Stocks`}
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {signals.filter(s => s.comprehensive_signal === 'BUY').length}
                </div>
                <div className="text-sm text-gray-600">Buy Signals</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {signals.filter(s => s.comprehensive_signal === 'SELL').length}
                </div>
                <div className="text-sm text-gray-600">Sell Signals</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {signals.filter(s => s.comprehensive_signal === 'HOLD').length}
                </div>
                <div className="text-sm text-gray-600">Hold Signals</div>
              </div>
            </div>
            {signalFilter !== 'ALL' && (
              <div className="mt-3 text-center text-sm text-gray-600">
                Showing {filteredSignals.length} of {signals.length} stocks ({signalFilter} filter)
              </div>
            )}
          </div>
        )}

        {!loading && filteredSignals.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredSignals.map((stock) => (
              <div key={stock.symbol} className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="font-semibold text-lg">{stock.symbol}</div>
                    <div className="text-sm text-gray-600">{getStockName(stock.symbol)}</div>
                  </div>
                  <button
                    onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="font-medium">Price:</span>
                    <span className="font-semibold">₹{(stock.current_price || stock.price)?.toFixed(2)}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="font-medium">Change:</span>
                    <span className={`font-semibold ${
                      stock.change_pct >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stock.change_pct >= 0 ? '+' : ''}{stock.change_pct?.toFixed(2) || '0.00'}%
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="font-medium">Signal:</span>
                    <span className={`font-bold text-lg ${
                      stock.comprehensive_signal === 'BUY' ? 'text-green-600' :
                      stock.comprehensive_signal === 'SELL' ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {stock.comprehensive_signal || 'HOLD'}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="font-medium">Strength:</span>
                    <span className={`text-sm font-semibold ${
                      stock.comprehensive_strength === 'STRONG' ? 'text-green-600' :
                      stock.comprehensive_strength === 'MODERATE' ? 'text-yellow-600' :
                      'text-gray-500'
                    }`}>
                      {stock.comprehensive_strength || 'WEAK'}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="font-medium">Confidence:</span>
                    <span className={`text-sm font-semibold ${
                      stock.chart_analysis?.confidence === 'HIGH' ? 'text-green-600' :
                      stock.chart_analysis?.confidence === 'MEDIUM' ? 'text-yellow-600' :
                      'text-gray-500'
                    }`}>
                      {stock.chart_analysis?.confidence || 'LOW'}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="font-medium">Source:</span>
                    <span className={`text-xs font-semibold ${
                      stock.data_source === 'YAHOO_FINANCE_SCRAPER' ? 'text-blue-600' :
                      stock.data_source === 'YAHOO_FINANCE_CURRENT' ? 'text-blue-600' :
                      stock.data_source === 'DATA_SERVICE' ? 'text-green-600' :
                      stock.data_source === 'FALLBACK_DATA' ? 'text-orange-600' :
                      stock.data_source === 'MOCK_FALLBACK' ? 'text-purple-600' :
                      'text-gray-500'
                    }`}>
                      {stock.data_source || 'Unknown'}
                    </span>
                  </div>
                  
                  {stock.entry_price && (
                    <div className="border-t pt-2 mt-2 space-y-2">
                      <div className="text-sm font-semibold text-gray-700">Technical Analysis</div>
                      
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Entry:</span>
                          <span className="font-semibold text-blue-600">
                            {stock.entry_price ? `₹${stock.entry_price.toFixed(2)}` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Stop Loss:</span>
                          <span className="font-semibold text-red-600">
                            {stock.stop_loss ? `₹${stock.stop_loss.toFixed(2)}` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Exit:</span>
                          <span className="font-semibold text-green-600">
                            {stock.exit_price ? `₹${stock.exit_price.toFixed(2)}` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Support:</span>
                          <span className="font-semibold text-purple-600">
                            {stock.chart_analysis?.support_level ? 
                              `₹${stock.chart_analysis.support_level.toFixed(2)}` : 
                              'N/A'
                            }
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Resistance:</span>
                          <span className="font-semibold text-purple-600">
                            {stock.chart_analysis?.resistance_level ? 
                              `₹${stock.chart_analysis.resistance_level.toFixed(2)}` : 
                              'N/A'
                            }
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Risk/Reward:</span>
                          <span className="font-semibold text-indigo-600">
                            {stock.chart_analysis?.risk_reward_ratio ? 
                              `1:${stock.chart_analysis.risk_reward_ratio.toFixed(2)}` : 
                              'N/A'
                            }
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Holding Period:</span>
                          <span className="font-semibold text-gray-700">
                            {stock.holding_period || 'N/A'}
                          </span>
                        </div>
                      </div>
                      
                      {stock.chart_analysis?.method && (
                        <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                          <div className="font-semibold mb-1">Analysis Method:</div>
                          <div>{stock.chart_analysis.method}</div>
                          {stock.chart_analysis.reasoning && (
                            <div className="mt-1 text-gray-700">{stock.chart_analysis.reasoning}</div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {stock.error && (
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                      Error: {stock.error}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && filteredSignals.length === 0 && signals.length > 0 && (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="text-gray-500 text-lg mb-2">No stocks found</div>
            <div className="text-gray-400">
              No stocks with "{signalFilter}" signal. Try selecting a different filter.
            </div>
          </div>
        )}

        <div className="mt-6">
          <AutoTradingStatus />
        </div>

        <div className="mt-6">
          <TradingPerformance symbol="NIFTY_50" />
        </div>
      </div>
    </div>
  );
};

export default Nifty50TradingSignalsWorking;
