/**
 * Stock Screener Page
 * Simple, clean screener focused on NIFTY 50 with basic filters
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Download, RefreshCw, Filter, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import { httpClient } from '../config/api';
import { nifty50Stocks } from '../data/indexStocks';
import candleDataApi from '../services/candleDataApi';
import BuySellButton from '../components/BuySellButton';

interface StockResult {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  avg_volume?: number;
  market_cap?: number;
  pe_ratio?: number;
  rsi?: number;
  roe?: number;
  debt_to_equity?: number;
  profit_growth?: number;
  revenue_growth?: number;
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  year_high?: number;
  year_low?: number;
  signal?: 'BUY' | 'SELL' | 'HOLD';
}

const StockScreener: React.FC = () => {
  const navigate = useNavigate();
  const [results, setResults] = useState<StockResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  // Price Filters
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [minVolume, setMinVolume] = useState<string>('');
  const [minChange, setMinChange] = useState<string>('');
  
  // Technical Filters
  const [minRsi, setMinRsi] = useState<string>('');
  const [maxRsi, setMaxRsi] = useState<string>('');
  const [priceAboveSma, setPriceAboveSma] = useState<string>('');
  const [macdBullish, setMacdBullish] = useState<boolean>(false);
  const [near52wHigh, setNear52wHigh] = useState<boolean>(false);
  
  // Financial Ratio Filters
  const [minPeRatio, setMinPeRatio] = useState<string>('');
  const [maxPeRatio, setMaxPeRatio] = useState<string>('');
  const [minRoe, setMinRoe] = useState<string>('');
  const [maxDebtToEquity, setMaxDebtToEquity] = useState<string>('');
  const [minProfitGrowth, setMinProfitGrowth] = useState<string>('');
  const [minRevenueGrowth, setMinRevenueGrowth] = useState<string>('');
  
  // Market Cap & Sector Filters
  const [minMarketCap, setMinMarketCap] = useState<string>('');
  const [maxMarketCap, setMaxMarketCap] = useState<string>('');
  const [selectedSectors, setSelectedSectors] = useState<string[]>([]);
  
  const [sortBy, setSortBy] = useState<string>('volume');

  const presets = [
    { id: 'high_volume', name: '🔥 High Volume', desc: 'Most actively traded' },
    { id: 'breakouts', name: '📈 Breakouts', desc: 'Price up >5%' },
    { id: 'oversold', name: '💚 Oversold', desc: 'RSI < 30 (Buy)' },
    { id: 'overbought', name: '🔴 Overbought', desc: 'RSI > 70 (Sell)' },
    { id: 'gainers', name: '⬆️ Top Gainers', desc: 'Biggest movers up' },
    { id: 'losers', name: '⬇️ Top Losers', desc: 'Biggest movers down' },
    { id: 'value_stocks', name: '💰 Value Stocks', desc: 'PE < 20, ROE > 15%' },
    { id: 'growth_stocks', name: '📊 Growth Stocks', desc: 'Profit Growth > 15%' },
    { id: 'low_debt', name: '🛡️ Low Debt', desc: 'Debt-to-Equity < 0.5' },
    { id: 'above_sma200', name: '📈 Above SMA 200', desc: 'Price above 200 SMA' },
  ];

  // Helper: fallback to local NIFTY 50 list when backend screener has no data
  const loadNifty50Fallback = async (limit: number = 30): Promise<StockResult[]> => {
    const fallbackResults: StockResult[] = [];
    const stocksToUse = nifty50Stocks.slice(0, limit);

    for (const stock of stocksToUse) {
      try {
        const response = await candleDataApi.getLatestCandle(stock.symbol);
        if (response.success && response.data) {
          const candle = response.data;
          const change = candle.close - candle.open;
          const changePercent = (change / candle.open) * 100;
          fallbackResults.push({
            symbol: stock.symbol,
            name: stock.name,
            price: candle.close,
            change,
            change_percent: changePercent,
            volume: candle.volume ?? 0,
            market_cap: undefined,
            pe_ratio: undefined,
            rsi: undefined,
            signal: 'HOLD',
          });
        } else {
          fallbackResults.push({
            symbol: stock.symbol,
            name: stock.name,
            price: 0,
            change: 0,
            change_percent: 0,
            volume: 0,
            signal: 'HOLD',
          });
        }
      } catch {
        fallbackResults.push({
          symbol: stock.symbol,
          name: stock.name,
          price: 0,
          change: 0,
          change_percent: 0,
          volume: 0,
          signal: 'HOLD',
        });
      }
    }
    return fallbackResults;
  };

  // Initial load: show first 30 NIFTY 50 stocks so the list is never empty
  React.useEffect(() => {
    (async () => {
      try {
        const initial = await loadNifty50Fallback(30);
        setResults(initial);
      } catch (e) {
        console.error('Failed to load initial NIFTY 50 fallback:', e);
      }
    })();
  }, []);

  const runScan = async () => {
    setLoading(true);
    try {
      const criteria: any = {
        sort_by: sortBy,
        limit: 50,
      };

      // Price filters
      if (minPrice) criteria.min_price = parseFloat(minPrice);
      if (maxPrice) criteria.max_price = parseFloat(maxPrice);
      if (minVolume) criteria.min_volume = parseInt(minVolume);
      if (minChange) criteria.min_change_percent = parseFloat(minChange);
      
      // Technical filters
      if (minRsi) criteria.min_rsi = parseFloat(minRsi);
      if (maxRsi) criteria.max_rsi = parseFloat(maxRsi);
      if (priceAboveSma) criteria.price_above_sma = parseInt(priceAboveSma);
      if (macdBullish) criteria.macd_bullish = true;
      if (near52wHigh) criteria.near_52w_high = true;
      
      // Financial ratio filters
      if (minPeRatio) criteria.min_pe_ratio = parseFloat(minPeRatio);
      if (maxPeRatio) criteria.max_pe_ratio = parseFloat(maxPeRatio);
      if (minRoe) criteria.min_roe = parseFloat(minRoe);
      if (maxDebtToEquity) criteria.max_debt_to_equity = parseFloat(maxDebtToEquity);
      if (minProfitGrowth) criteria.min_profit_growth = parseFloat(minProfitGrowth);
      if (minRevenueGrowth) criteria.min_revenue_growth = parseFloat(minRevenueGrowth);
      
      // Market cap filters
      if (minMarketCap) criteria.min_market_cap = parseFloat(minMarketCap) * 1000000000; // Convert to actual value
      if (maxMarketCap) criteria.max_market_cap = parseFloat(maxMarketCap) * 1000000000;
      if (selectedSectors.length > 0) criteria.sectors = selectedSectors;

      const response = await httpClient.post<any>('/api/screener/scan', criteria);

      if (response.data?.success && Array.isArray(response.data.results) && response.data.results.length > 0) {
        setResults(response.data.results || []);
      } else {
        console.warn('Screener returned no data. Falling back to NIFTY 50 list.');
        const fallback = await loadNifty50Fallback();
        setResults(fallback);
      }
    } catch (error) {
      console.error('Scan error:', error);
      // If backend fails, still try to show NIFTY 50
      const fallback = await loadNifty50Fallback();
      setResults(fallback);
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = async (presetId: string) => {
    setSelectedPreset(presetId);
    setLoading(true);
    try {
      const response = await httpClient.get<any>(`/api/screener/presets/${presetId}`);
      
      if (response.data.success) {
        setResults(response.data.results || []);
      }
    } catch (error) {
      console.error('Preset error:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = () => {
    if (results.length === 0) return;

    const csvContent = [
      ['Symbol', 'Name', 'Price', 'Change%', 'Volume', 'RSI', 'Signal'],
      ...results.map(r => [
        r.symbol,
        r.name,
        r.price,
        r.change_percent,
        r.volume,
        r.rsi || 'N/A',
        r.signal || 'HOLD'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `screener_results_${Date.now()}.csv`;
    a.click();
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-sm">
          <div className="flex items-center gap-3">
            <Search className="w-6 h-6 text-gray-700" />
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Stock Screener (NIFTY 50 Focus)</h1>
              <p className="text-sm text-gray-500 mt-1">
                Simple white/black view with NIFTY 50 stocks. Click any symbol to open Comprehensive Trading Pro.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Presets */}
        <div className="bg-white rounded-xl p-6 mb-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
            Quick Presets
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {presets.map(preset => (
              <button
                key={preset.id}
                onClick={() => loadPreset(preset.id)}
                className={`p-3 rounded-lg text-left text-sm border transition-all ${
                  selectedPreset === preset.id
                    ? 'bg-black text-white border-black'
                    : 'bg-white text-gray-800 hover:bg-gray-50 border-gray-200'
                }`}
              >
                <div className="font-semibold mb-1">{preset.name}</div>
                <div className="text-xs text-gray-500">{preset.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl p-6 mb-6 border border-gray-200">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-700" />
            Custom Filters
          </h3>
          
          {/* Price & Volume Filters */}
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Price & Volume</h4>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Min Price (₹)</label>
              <input
                type="number"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                placeholder="0"
                className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Price (₹)</label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="10000"
                className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Min Volume</label>
              <input
                type="number"
                value={minVolume}
                onChange={(e) => setMinVolume(e.target.value)}
                placeholder="1000000"
                className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Min Change %</label>
              <input
                type="number"
                step="0.1"
                value={minChange}
                onChange={(e) => setMinChange(e.target.value)}
                placeholder="2.0"
                className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
              />
            </div>
            </div>
          </div>
          
          {/* Technical Filters */}
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Technical Indicators</h4>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min RSI</label>
                <input
                  type="number"
                  value={minRsi}
                  onChange={(e) => setMinRsi(e.target.value)}
                  placeholder="30"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max RSI</label>
                <input
                  type="number"
                  value={maxRsi}
                  onChange={(e) => setMaxRsi(e.target.value)}
                  placeholder="70"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price Above SMA</label>
                <select
                  value={priceAboveSma}
                  onChange={(e) => setPriceAboveSma(e.target.value)}
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                >
                  <option value="">None</option>
                  <option value="20">SMA 20</option>
                  <option value="50">SMA 50</option>
                  <option value="200">SMA 200</option>
                </select>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={macdBullish}
                    onChange={(e) => setMacdBullish(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm font-medium text-gray-700">MACD Bullish</span>
                </label>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={near52wHigh}
                    onChange={(e) => setNear52wHigh(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm font-medium text-gray-700">Near 52W High</span>
                </label>
              </div>
            </div>
          </div>
          
          {/* Financial Ratio Filters */}
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Financial Ratios</h4>
            <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min PE Ratio</label>
                <input
                  type="number"
                  value={minPeRatio}
                  onChange={(e) => setMinPeRatio(e.target.value)}
                  placeholder="5"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max PE Ratio</label>
                <input
                  type="number"
                  value={maxPeRatio}
                  onChange={(e) => setMaxPeRatio(e.target.value)}
                  placeholder="20"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min ROE (%)</label>
                <input
                  type="number"
                  value={minRoe}
                  onChange={(e) => setMinRoe(e.target.value)}
                  placeholder="15"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Debt/Equity</label>
                <input
                  type="number"
                  step="0.1"
                  value={maxDebtToEquity}
                  onChange={(e) => setMaxDebtToEquity(e.target.value)}
                  placeholder="0.5"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Profit Growth (%)</label>
                <input
                  type="number"
                  value={minProfitGrowth}
                  onChange={(e) => setMinProfitGrowth(e.target.value)}
                  placeholder="15"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Revenue Growth (%)</label>
                <input
                  type="number"
                  value={minRevenueGrowth}
                  onChange={(e) => setMinRevenueGrowth(e.target.value)}
                  placeholder="10"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
            </div>
          </div>
          
          {/* Market Cap & Sector Filters */}
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Market Cap & Sector</h4>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Market Cap (₹ Cr)</label>
                <input
                  type="number"
                  value={minMarketCap}
                  onChange={(e) => setMinMarketCap(e.target.value)}
                  placeholder="1000"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Market Cap (₹ Cr)</label>
                <input
                  type="number"
                  value={maxMarketCap}
                  onChange={(e) => setMaxMarketCap(e.target.value)}
                  placeholder="100000"
                  className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Sectors</label>
                <div className="flex flex-wrap gap-2">
                  {['Technology', 'Banking', 'Pharmaceuticals', 'Automobile', 'Energy', 'FMCG', 'Finance', 'Telecommunications'].map(sector => (
                    <button
                      key={sector}
                      onClick={() => {
                        setSelectedSectors(prev =>
                          prev.includes(sector) 
                            ? prev.filter(s => s !== sector)
                            : [...prev, sector]
                        );
                      }}
                      className={`px-3 py-1 rounded-full text-xs transition-all border ${
                        selectedSectors.includes(sector)
                          ? 'bg-black text-white border-black'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {sector}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          {/* Sort By */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full bg-white px-3 py-2 rounded-md border border-gray-300 focus:border-black focus:outline-none text-sm max-w-xs"
            >
              <option value="volume">Volume</option>
              <option value="change">Change %</option>
              <option value="price">Price</option>
              <option value="rsi">RSI</option>
              <option value="pe_ratio">PE Ratio</option>
              <option value="roe">ROE</option>
            </select>
          </div>
          <div className="flex gap-3 mt-2">
            <button
              onClick={runScan}
              disabled={loading}
              className="flex items-center gap-2 bg-black hover:bg-gray-900 disabled:bg-gray-400 text-white px-5 py-2 rounded-md text-sm font-medium transition-colors"
            >
              <Search className="w-5 h-5" />
              {loading ? 'Scanning...' : 'Run Custom Scan'}
            </button>
            <button
              onClick={() => {
                setMinPrice('');
                setMaxPrice('');
                setMinVolume('');
                setMinChange('');
                setMinRsi('');
                setMaxRsi('');
                setPriceAboveSma('');
                setMacdBullish(false);
                setNear52wHigh(false);
                setMinPeRatio('');
                setMaxPeRatio('');
                setMinRoe('');
                setMaxDebtToEquity('');
                setMinProfitGrowth('');
                setMinRevenueGrowth('');
                setMinMarketCap('');
                setMaxMarketCap('');
                setSelectedSectors([]);
                setSortBy('volume');
                setResults([]);
                setSelectedPreset('');
              }}
              className="flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 px-5 py-2 rounded-md text-sm font-medium text-gray-700 transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
              Reset
            </button>
          </div>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-gray-700" />
                Results ({results.length} stocks){' '}
                <span className="text-xs font-normal text-gray-500">(NIFTY 50 fallback if screener is empty)</span>
              </h3>
              <button
                onClick={exportCSV}
                className="flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 px-4 py-2 rounded-md text-sm font-medium text-gray-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 text-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Symbol</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Name</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide">Price (₹)</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide">Change</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide">Volume</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide">RSI</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide">PE</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide">ROE (%)</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide">Growth</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide">Signal</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {results.map((stock, idx) => (
                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                      <td
                        className="px-4 py-3 font-semibold text-sm text-blue-700 cursor-pointer"
                        onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                      >
                        {stock.symbol}
                      </td>
                      <td
                        className="px-4 py-3 text-gray-700 text-xs cursor-pointer"
                        onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                      >
                        {stock.name}
                      </td>
                      <td
                        className="px-4 py-3 text-right font-semibold text-gray-900 cursor-pointer"
                        onClick={() => navigate(`/comprehensive-trading-pro?symbol=${stock.symbol}`)}
                      >
                        ₹{stock.price.toFixed(2)}
                      </td>
                      <td
                        className={`px-4 py-3 text-right font-semibold ${
                          stock.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {stock.change_percent >= 0 ? '+' : ''}{stock.change_percent.toFixed(2)}%
                      </td>
                      <td className="px-4 py-3 text-right text-gray-500">
                        {(stock.volume / 1000000).toFixed(2)}M
                      </td>
                      <td className="px-4 py-3 text-right">
                        {stock.rsi ? (
                          <span className={`font-semibold ${
                            stock.rsi < 30 ? 'text-green-600' :
                            stock.rsi > 70 ? 'text-red-600' :
                            'text-yellow-600'
                          }`}>
                            {stock.rsi.toFixed(1)}
                          </span>
                        ) : (
                          <span className="text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {stock.pe_ratio ? stock.pe_ratio.toFixed(2) : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {stock.roe ? `${stock.roe.toFixed(1)}%` : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {stock.profit_growth ? (
                          <span className={`font-semibold ${
                            stock.profit_growth > 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {stock.profit_growth >= 0 ? '+' : ''}{stock.profit_growth.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                          stock.signal === 'BUY' ? 'bg-green-50 text-green-700 border border-green-200' :
                          stock.signal === 'SELL' ? 'bg-red-50 text-red-700 border border-red-200' :
                          'bg-gray-50 text-gray-600 border border-gray-200'
                        }`}>
                          {stock.signal || 'HOLD'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <BuySellButton
                          symbol={stock.symbol}
                          currentPrice={stock.price}
                          size="sm"
                          onOrderPlaced={() => {
                            // Portfolio will be updated automatically
                          }}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Empty State */}
        {results.length === 0 && !loading && (
          <div className="bg-[#1a1d28] rounded-xl p-12 text-center border border-gray-700/50">
            <Search className="w-16 h-16 mx-auto mb-4 text-gray-600" />
            <h3 className="text-xl font-semibold mb-2">No Results Yet</h3>
            <p className="text-gray-400 mb-6">Choose a preset or set custom filters to scan stocks</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockScreener;

