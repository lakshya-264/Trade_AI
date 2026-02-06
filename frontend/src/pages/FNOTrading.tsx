/**
 * F&O Trading Page
 * Complete UI for Futures & Options trading with real-time signals
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  TrendingUp, TrendingDown, Activity, BarChart3, 
  AlertCircle, CheckCircle, XCircle, RefreshCw, 
  Calculator, Target, Zap, Shield
} from 'lucide-react';
import { httpClient } from '../config/api';
import { toast } from 'react-hot-toast';
import StockSelector from '../components/StockSelector';
import StrategyBuilder from '../components/strategy/StrategyBuilder';
import EnhancedStrategyBuilder from '../components/strategy/EnhancedStrategyBuilder';
import PaperTrading from '../components/strategy/PaperTrading';
import OIAnalysisComponent from '../components/fno/OIAnalysis';
import OptionsChainBuilder from '../components/fno/OptionsChainBuilder';

interface OIAnalysisData {
  signal: string;
  sentiment: string;
  strength: number;
  price_change: number;
  oi_change: number;
  current_price: number;
  current_oi: number;
}

interface PCRAnalysis {
  pcr: number;
  sentiment: string;
  signal: string;
  interpretation: string;
}

interface MaxPain {
  max_pain: number;
  current_price: number;
  distance: number;
  signal: string;
}

interface OptionsStrategy {
  name: string;
  outlook: string;
  risk: string;
  max_profit?: string;
  max_loss: string;
}

const FNOTrading: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [selectedSymbol, setSelectedSymbol] = useState(searchParams.get('symbol') || 'NIFTY');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'analysis' | 'oi' | 'strategy' | 'options-chain' | 'paper'>('analysis');
  const [selectedStrategy, setSelectedStrategy] = useState<any>(null);
  
  // F&O Data
  const [oiAnalysis, setOiAnalysis] = useState<OIAnalysisData | null>(null);
  const [pcrAnalysis, setPcrAnalysis] = useState<PCRAnalysis | null>(null);
  const [maxPain, setMaxPain] = useState<MaxPain | null>(null);
  const [optionsStrategies, setOptionsStrategies] = useState<OptionsStrategy[]>([]);
  
  // Chart Analysis Data
  const [chartAnalysis, setChartAnalysis] = useState<any>(null);
  const [loadingChartAnalysis, setLoadingChartAnalysis] = useState(false);
  
  // Inputs for OI Analysis
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [previousPrice, setPreviousPrice] = useState<number>(0);
  const [currentOI, setCurrentOI] = useState<number>(0);
  const [previousOI, setPreviousOI] = useState<number>(0);
  
  // Inputs for PCR
  const [putOI, setPutOI] = useState<number>(0);
  const [callOI, setCallOI] = useState<number>(0);
  
  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        if (oiAnalysis) fetchOIAnalysis();
        if (pcrAnalysis) fetchPCRAnalysis();
        if (selectedSymbol) fetchChartAnalysis();
      }, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, oiAnalysis, pcrAnalysis, selectedSymbol]);

  // Fetch chart analysis when symbol changes
  useEffect(() => {
    if (selectedSymbol) {
      fetchChartAnalysis();
    }
  }, [selectedSymbol]);

  const fetchOIAnalysis = async () => {
    if (!currentPrice || !previousPrice || !currentOI || !previousOI) {
      toast.error('Please fill all OI Analysis fields');
      return;
    }
    
    setLoading(true);
    try {
      const response = await httpClient.post('/api/comprehensive-trading/fno/oi-analysis', {
        current_price: currentPrice,
        previous_price: previousPrice,
        current_oi: currentOI,
        previous_oi: previousOI
      }) as any;
      
      if (response.data?.success) {
        setOiAnalysis(response.data.data);
        toast.success('OI Analysis updated');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to fetch OI Analysis');
    } finally {
      setLoading(false);
    }
  };

  const fetchPCRAnalysis = async () => {
    if (!putOI || !callOI) {
      toast.error('Please fill Put OI and Call OI');
      return;
    }
    
    setLoading(true);
    try {
      const response = await httpClient.post('/api/comprehensive-trading/fno/pcr-analysis', {
        put_oi: putOI,
        call_oi: callOI
      }) as any;
      
      if (response.data?.success) {
        setPcrAnalysis(response.data.data);
        toast.success('PCR Analysis updated');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to fetch PCR Analysis');
    } finally {
      setLoading(false);
    }
  };

  const fetchMaxPain = async () => {
    // Simplified - in production, fetch from option chain
    const strikes = [2400, 2450, 2500, 2550, 2600];
    const callOI = [100, 200, 300, 200, 100];
    const putOI = [100, 200, 300, 200, 100];
    
    setLoading(true);
    try {
      const response = await httpClient.post('/api/comprehensive-trading/fno/max-pain', {
        strikes,
        call_oi: callOI,
        put_oi: putOI,
        current_price: currentPrice || 2500
      }) as any;
      
      if (response.data?.success) {
        setMaxPain(response.data.data);
        toast.success('Max Pain calculated');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to calculate Max Pain');
    } finally {
      setLoading(false);
    }
  };

  const fetchChartAnalysis = async () => {
    if (!selectedSymbol) return;
    
    setLoadingChartAnalysis(true);
    try {
      const response = await httpClient.get(`/api/comprehensive-trading/fno/chart-analysis/${selectedSymbol}`, {
        timeframe: '1D'
      }) as any;
      
      if (response.success && response.data) {
        setChartAnalysis(response.data);
        // Auto-update current price if available
        if (response.data.facts?.current_price) {
          setCurrentPrice(response.data.facts.current_price);
        }
      }
    } catch (error: any) {
      console.error('Failed to fetch chart analysis:', error);
      // Don't show error toast, just log it
    } finally {
      setLoadingChartAnalysis(false);
    }
  };

  const fetchOptionsStrategies = async (outlook: string = 'bullish') => {
    setLoading(true);
    try {
      const response = await httpClient.post('/api/comprehensive-trading/fno/options-strategy', {
        market_outlook: outlook,
        volatility_outlook: 'stable',
        time_to_expiry_days: 30,
        risk_tolerance: 'medium'
      }) as any;
      
      if (response.data?.success) {
        setOptionsStrategies(response.data.data || []);
        toast.success('Options strategies loaded');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to fetch strategies');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signal: string) => {
    if (signal?.includes('BUY') || signal?.includes('BULLISH')) return 'text-green-600';
    if (signal?.includes('SELL') || signal?.includes('BEARISH')) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSignalBg = (signal: string) => {
    if (signal?.includes('BUY') || signal?.includes('BULLISH')) return 'bg-green-50 border-green-500';
    if (signal?.includes('SELL') || signal?.includes('BEARISH')) return 'bg-red-50 border-red-500';
    return 'bg-yellow-50 border-yellow-500';
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('analysis')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'analysis'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Analysis
          </button>
          <button
            onClick={() => setActiveTab('oi')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'oi'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Open Interest
          </button>
          <button
            onClick={() => setActiveTab('strategy')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'strategy'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Strategy Builder
          </button>
          <button
            onClick={() => setActiveTab('options-chain')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'options-chain'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Options Chain
          </button>
          <button
            onClick={() => setActiveTab('paper')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'paper'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Activity className="w-4 h-4" />
            Paper Trading
          </button>
        </div>

        {activeTab === 'oi' ? (
          <div className="h-[calc(100vh-200px)] overflow-auto">
            <OIAnalysisComponent 
              symbol={selectedSymbol}
              onExpiryChange={(expiry: string) => {
                // Handle expiry change if needed
                console.log('Expiry changed to:', expiry);
              }}
              onSymbolChange={(symbol: string) => {
                setSelectedSymbol(symbol);
              }}
            />
          </div>
        ) : activeTab === 'strategy' ? (
          <div className="h-[calc(100vh-200px)]">
            <EnhancedStrategyBuilder 
              symbol={selectedSymbol} 
              showPaperTrading={true}
              onStrategySelect={(strategy) => {
                setSelectedStrategy(strategy);
                // Optionally switch to paper trading tab when strategy is selected
                // setActiveTab('paper');
              }}
            />
          </div>
        ) : activeTab === 'options-chain' ? (
          <div className="h-[calc(100vh-200px)]">
            <OptionsChainBuilder
              symbol={selectedSymbol}
              onSymbolChange={(symbol) => {
                setSelectedSymbol(symbol);
              }}
            />
          </div>
        ) : activeTab === 'paper' ? (
          <div className="h-[calc(100vh-200px)]">
            <PaperTrading
              strategy={selectedStrategy || {
                id: undefined,
                name: 'FNO Paper Trading',
                legs: [],
                metrics: null
              }}
              symbol={selectedSymbol}
              currentPrice={currentPrice || 26042.30}
            />
          </div>
        ) : (
          <>
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <BarChart3 className="w-8 h-8 text-blue-600" />
                F&O Trading Dashboard
              </h1>
              <p className="text-gray-600 mt-2">Futures & Options analysis and signals</p>
            </div>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Auto Refresh</span>
              </label>
              {autoRefresh && (
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  className="bg-white border border-gray-300 rounded px-3 py-1 text-sm text-gray-900"
                >
                  <option value={10}>10s</option>
                  <option value={30}>30s</option>
                  <option value={60}>60s</option>
                </select>
              )}
            </div>
          </div>
          
          {/* Symbol Selector */}
          <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <StockSelector
              value={selectedSymbol}
              onChange={(symbol) => setSelectedSymbol(symbol)}
              className="w-full"
            />
          </div>
        </div>

        {/* Chart Analysis Based Suggestions */}
        {chartAnalysis && (
          <div className="mb-6">
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-900">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                  Chart Analysis Based Suggestions
                </h2>
                <button
                  onClick={fetchChartAnalysis}
                  disabled={loadingChartAnalysis}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium text-white disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${loadingChartAnalysis ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
              
              {/* Key Facts */}
              {chartAnalysis.facts && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-sm text-gray-600 mb-1">Current Price</div>
                    <div className="text-xl font-bold text-gray-900">₹{chartAnalysis.facts.current_price?.toFixed(2) || 'N/A'}</div>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-sm text-gray-600 mb-1">RSI</div>
                    <div className={`text-xl font-bold ${chartAnalysis.facts.rsi > 70 ? 'text-red-600' : chartAnalysis.facts.rsi < 30 ? 'text-green-600' : 'text-gray-900'}`}>
                      {chartAnalysis.facts.rsi?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-sm text-gray-600 mb-1">Trend</div>
                    <div className={`text-xl font-bold ${
                      chartAnalysis.facts.trend === 'BULLISH' ? 'text-green-600' : 
                      chartAnalysis.facts.trend === 'BEARISH' ? 'text-red-600' : 
                      'text-gray-600'
                    }`}>
                      {chartAnalysis.facts.trend || 'NEUTRAL'}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-sm text-gray-600 mb-1">Patterns</div>
                    <div className="text-xl font-bold text-gray-900">{chartAnalysis.facts.patterns_detected || 0}</div>
                  </div>
                </div>
              )}
              
              {/* Suggestions */}
              {chartAnalysis.suggestions && chartAnalysis.suggestions.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Trading Suggestions</h3>
                  {chartAnalysis.suggestions.map((suggestion: any, idx: number) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-lg border ${
                        suggestion.type === 'BULLISH'
                          ? 'bg-green-50 border-green-200'
                          : suggestion.type === 'BEARISH'
                          ? 'bg-red-50 border-red-200'
                          : 'bg-yellow-50 border-yellow-200'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`font-bold text-lg ${
                              suggestion.type === 'BULLISH' ? 'text-green-700' : 
                              suggestion.type === 'BEARISH' ? 'text-red-700' : 
                              'text-yellow-700'
                            }`}>
                              {typeof suggestion.title === 'string' ? suggestion.title : suggestion.title?.title || suggestion.title?.name || 'Trading Signal'}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded ${
                              (typeof suggestion.confidence === 'string' && suggestion.confidence === 'HIGH') ? 'bg-green-200 text-green-800' :
                              (typeof suggestion.confidence === 'string' && suggestion.confidence === 'MEDIUM') ? 'bg-yellow-200 text-yellow-800' :
                              'bg-gray-200 text-gray-800'
                            }`}>
                              {typeof suggestion.confidence === 'string' 
                                ? suggestion.confidence 
                                : typeof suggestion.confidence === 'number'
                                ? `${Math.round(suggestion.confidence)}%`
                                : suggestion.confidence?.level || suggestion.confidence?.value || 'MEDIUM'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 mb-2">
                            {typeof suggestion.description === 'string' 
                              ? suggestion.description 
                              : suggestion.description?.text || suggestion.description?.message || 'No description available'}
                          </p>
                          <div className="text-xs text-gray-500">
                            Based on: {typeof suggestion.indicator === 'string' 
                              ? suggestion.indicator 
                              : suggestion.indicator?.name || suggestion.indicator?.title || 'Technical Analysis'}
                          </div>
                        </div>
                        <div className={`ml-4 px-3 py-1 rounded font-semibold text-sm ${
                          suggestion.type === 'BULLISH' ? 'bg-green-600 text-white' :
                          suggestion.type === 'BEARISH' ? 'bg-red-600 text-white' :
                          'bg-yellow-600 text-white'
                        }`}>
                          {suggestion.type}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Additional Metrics */}
              {chartAnalysis.facts && (
                <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-lg p-3 border border-gray-200">
                    <div className="text-xs text-gray-600 mb-1">Price vs SMA 20</div>
                    <div className={`text-sm font-semibold ${
                      chartAnalysis.facts.price_vs_sma20 > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {chartAnalysis.facts.price_vs_sma20 > 0 ? '+' : ''}{chartAnalysis.facts.price_vs_sma20}%
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-gray-200">
                    <div className="text-xs text-gray-600 mb-1">Price vs SMA 50</div>
                    <div className={`text-sm font-semibold ${
                      chartAnalysis.facts.price_vs_sma50 > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {chartAnalysis.facts.price_vs_sma50 > 0 ? '+' : ''}{chartAnalysis.facts.price_vs_sma50}%
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-gray-200">
                    <div className="text-xs text-gray-600 mb-1">Volume Trend</div>
                    <div className={`text-sm font-semibold ${
                      chartAnalysis.facts.volume_trend === 'BULLISH' ? 'text-green-600' :
                      chartAnalysis.facts.volume_trend === 'BEARISH' ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {chartAnalysis.facts.volume_trend || 'NEUTRAL'}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Open Interest Analysis */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-600" />
                Open Interest Analysis
              </h2>
              <button
                onClick={fetchOIAnalysis}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Analyze
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm text-gray-700 mb-2 font-medium">Current Price</label>
                <input
                  type="number"
                  value={currentPrice || ''}
                  onChange={(e) => setCurrentPrice(Number(e.target.value))}
                  className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="2500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-2 font-medium">Previous Price</label>
                <input
                  type="number"
                  value={previousPrice || ''}
                  onChange={(e) => setPreviousPrice(Number(e.target.value))}
                  className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="2480"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-2 font-medium">Current OI</label>
                <input
                  type="number"
                  value={currentOI || ''}
                  onChange={(e) => setCurrentOI(Number(e.target.value))}
                  className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="1000000"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-2 font-medium">Previous OI</label>
                <input
                  type="number"
                  value={previousOI || ''}
                  onChange={(e) => setPreviousOI(Number(e.target.value))}
                  className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="950000"
                />
              </div>
            </div>

            {oiAnalysis && (
              <div className={`mt-4 p-4 rounded-lg border ${getSignalBg(oiAnalysis.signal)}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-lg">Signal: {oiAnalysis.signal}</span>
                  <span className={`text-sm font-semibold ${getSignalColor(oiAnalysis.signal)}`}>
                    {oiAnalysis.sentiment}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Price Change:</span>
                    <span className={`ml-2 font-semibold ${oiAnalysis.price_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {oiAnalysis.price_change >= 0 ? '+' : ''}{oiAnalysis.price_change.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">OI Change:</span>
                    <span className={`ml-2 font-semibold ${oiAnalysis.oi_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {oiAnalysis.oi_change >= 0 ? '+' : ''}{oiAnalysis.oi_change.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Strength:</span>
                    <span className="ml-2 font-semibold text-gray-900">{oiAnalysis.strength.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Current OI:</span>
                    <span className="ml-2 font-semibold text-gray-900">{oiAnalysis.current_oi.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Put-Call Ratio Analysis */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Calculator className="w-5 h-5 text-purple-600" />
                Put-Call Ratio (PCR)
              </h2>
              <button
                onClick={fetchPCRAnalysis}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Calculate
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm text-gray-700 mb-2 font-medium">Put OI</label>
                <input
                  type="number"
                  value={putOI || ''}
                  onChange={(e) => setPutOI(Number(e.target.value))}
                  className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="1500000"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-2 font-medium">Call OI</label>
                <input
                  type="number"
                  value={callOI || ''}
                  onChange={(e) => setCallOI(Number(e.target.value))}
                  className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="1000000"
                />
              </div>
            </div>

            {pcrAnalysis && (
              <div className={`mt-4 p-4 rounded-lg border ${getSignalBg(pcrAnalysis.signal)}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-lg">PCR: {pcrAnalysis.pcr.toFixed(2)}</span>
                  <span className={`text-sm font-semibold ${getSignalColor(pcrAnalysis.signal)}`}>
                    {pcrAnalysis.signal}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mt-2">{pcrAnalysis.interpretation}</p>
                <div className="mt-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Put OI:</span>
                    <span className="font-semibold text-gray-900">{putOI.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-gray-600">Call OI:</span>
                    <span className="font-semibold text-gray-900">{callOI.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Max Pain */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Target className="w-5 h-5 text-orange-600" />
                Maximum Pain
              </h2>
              <button
                onClick={fetchMaxPain}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                <Calculator className="w-4 h-4" />
                Calculate
              </button>
            </div>

            {maxPain && (
              <div className="mt-4 p-4 rounded-lg border border-orange-500 bg-orange-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-lg text-gray-900">Max Pain: ₹{maxPain.max_pain.toFixed(2)}</span>
                  <span className={`text-sm font-semibold ${getSignalColor(maxPain.signal)}`}>
                    {maxPain.signal}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm mt-3">
                  <div>
                    <span className="text-gray-600">Current Price:</span>
                    <span className="ml-2 font-semibold text-gray-900">₹{maxPain.current_price.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Distance:</span>
                    <span className={`ml-2 font-semibold ${Math.abs(maxPain.distance) < 10 ? 'text-green-600' : 'text-yellow-600'}`}>
                      ₹{Math.abs(maxPain.distance).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Options Strategies */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                Options Strategies
              </h2>
              <div className="flex gap-2">
                {['bullish', 'bearish', 'volatile', 'range_bound'].map(outlook => (
                  <button
                    key={outlook}
                    onClick={() => fetchOptionsStrategies(outlook)}
                    disabled={loading}
                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-xs font-medium disabled:opacity-50 capitalize text-gray-700"
                  >
                    {outlook.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            {optionsStrategies.length > 0 && (
              <div className="space-y-3 mt-4">
                {optionsStrategies.map((strategy, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-gray-900">{strategy.name}</span>
                      <span className={`text-xs px-2 py-1 rounded ${getSignalBg(strategy.outlook)}`}>
                        {strategy.outlook}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 space-y-1">
                      <div>Risk: {strategy.risk}</div>
                      <div>Max Loss: {strategy.max_loss}</div>
                      {strategy.max_profit && <div>Max Profit: {strategy.max_profit}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </>
        )}
      </div>
    </div>
  );
};

export default FNOTrading;

