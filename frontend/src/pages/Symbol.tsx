import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import ResponsiveCard from '../components/ResponsiveCard';
import ResponsiveChart from '../components/ResponsiveChart';
import LoadingSpinner from '../components/LoadingSpinner';
import BuySellButton from '../components/BuySellButton';
import { formatINR, formatINRCompact } from '../utils/currency';

const presets = {
  minimal: ['sma20'],
  swing: ['sma20', 'sma50', 'rsi', 'macd'],
  full: ['sma20', 'sma50', 'ema12', 'rsi', 'macd', 'vwap', 'pivot']
};

const Symbol: React.FC = () => {
  const { symbol = 'RELIANCE' } = useParams();
  const [searchParams] = useSearchParams();
  const exchange = searchParams.get('exchange') || 'NSE';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quote, setQuote] = useState<any>(null);
  const [fastInfo, setFastInfo] = useState<any>(null);
  const [candles, setCandles] = useState<any[]>([]);
  const [indicators, setIndicators] = useState<any | null>(null);
  const [signals, setSignals] = useState<any | null>(null);
  const [preset, setPreset] = useState<string>(() => localStorage.getItem('analysis_preset') || 'swing');

  // List of screener categories that should not be treated as stock symbols
  const screenerCategories = ['top-gainers', 'top-losers', 'only-buyers', 'only-sellers', 'volume-shockers', 'most-active'];
  const isScreenerCategory = screenerCategories.includes(symbol?.toLowerCase() || '');

  useEffect(() => {
    if (symbol && !isScreenerCategory) {
      localStorage.setItem('last_symbol', symbol);
    }
  }, [symbol, isScreenerCategory]);

  useEffect(() => {
    // Redirect screener categories to stocks page
    if (isScreenerCategory) {
      window.location.href = `/stocks/${symbol}`;
      return;
    }

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [q, f, h, ind, sig] = await Promise.all([
          api.getQuote(symbol, exchange),
          api.getFastInfo(symbol),
          api.getHistoricalData(symbol, exchange, undefined, undefined, undefined), // Remove extra parameter
          api.getIndicator(symbol, 'all'),
          api.get('/trading/signals').catch(() => ({ data: null })) // Handle 404 gracefully
        ]);
        setQuote(q);
        setFastInfo(f);
        setCandles(
          (h || []).map((d: any) => ({
            date: d.date || d.timestamp || new Date().toISOString(),
            open: d.open, high: d.high, low: d.low, close: d.close, volume: d.volume, timestamp: d.timestamp
          }))
        );
        setIndicators(ind?.data || ind);
        setSignals(sig?.data || sig);
      } catch (e: any) {
        // Don't show error for 404s on trading/signals
        if (e?.message?.includes('signals')) {
          setSignals(null);
        } else {
          setError(e?.message || 'Failed to load symbol data');
        }
      } finally {
        setLoading(false);
      }
    }
    
    if (!isScreenerCategory) {
      load();
    }
  }, [symbol, exchange, isScreenerCategory]);

  const activeOverlays = useMemo(() => presets[preset as keyof typeof presets] || presets.swing, [preset]);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 text-sm">{error}</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{symbol} · {exchange}</h1>
        <div className="flex items-center space-x-2">
          {quote && (
            <BuySellButton
              symbol={symbol}
              currentPrice={quote.last_price}
              onOrderPlaced={() => {
                // Portfolio will be updated automatically
              }}
            />
          )}
          <select
            className="border rounded px-2 py-1 text-sm"
            value={preset}
            onChange={(e) => {
              setPreset(e.target.value);
              localStorage.setItem('analysis_preset', e.target.value);
            }}
          >
            <option value="minimal">Minimal</option>
            <option value="swing">Swing</option>
            <option value="full">Full Pack</option>
          </select>
        </div>
      </div>

      <ResponsiveCard padding="lg">
        <ResponsiveChart
          data={candles}
          dataKey="close"
          title={`${symbol} Price`}
          height={420}
          loading={false}
          symbol={symbol}
          advanced={true}
        />
      </ResponsiveCard>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ResponsiveCard padding="md">
          <h3 className="font-semibold mb-2">Fast Info</h3>
          {fastInfo ? (
            <div className="space-y-1 text-sm">
              <div className="text-gray-700">Last: {formatINR(fastInfo.last_price)}</div>
              <div className="text-gray-700">Open: {formatINR(fastInfo.open)}</div>
              <div className="text-gray-700">High: {formatINR(fastInfo.day_high)}</div>
              <div className="text-gray-700">Low: {formatINR(fastInfo.day_low)}</div>
              <div className="text-gray-700">Volume: {formatINRCompact(fastInfo.last_volume)}</div>
              <div className="text-gray-700">52W High: {formatINR(fastInfo.year_high)}</div>
              <div className="text-gray-700">52W Low: {formatINR(fastInfo.year_low)}</div>
              <div className="text-gray-700">50D MA: {formatINR(fastInfo.fifty_day_average)}</div>
              <div className="text-gray-700">200D MA: {formatINR(fastInfo.two_hundred_day_average)}</div>
            </div>
          ) : (
            <div className="text-sm text-gray-500">Loading fast info...</div>
          )}
        </ResponsiveCard>

        <ResponsiveCard padding="md">
          <h3 className="font-semibold mb-2">Technical Indicators</h3>
          {indicators ? (
            <div className="space-y-1 text-sm">
              <div className="text-gray-700">RSI: {indicators.rsi?.toFixed(2)}</div>
              <div className="text-gray-700">MACD: {indicators.macd?.toFixed(4)}</div>
              <div className="text-gray-700">SMA20: {formatINR(indicators.sma_20)}</div>
              <div className="text-gray-700">SMA50: {formatINR(indicators.sma_50)}</div>
              <div className="text-gray-700">EMA12: {formatINR(indicators.ema_12)}</div>
              <div className="text-gray-700">EMA26: {formatINR(indicators.ema_26)}</div>
            </div>
          ) : (
            <div className="text-sm text-gray-500">Loading indicators...</div>
          )}
        </ResponsiveCard>

        <ResponsiveCard padding="md">
          <h3 className="font-semibold mb-2">Signals</h3>
          <div className="text-sm text-gray-700">Buys: {signals?.buy_signals?.length || 0}</div>
          <div className="text-sm text-gray-700">Sells: {signals?.sell_signals?.length || 0}</div>
        </ResponsiveCard>
      </div>
    </div>
  );
};

export default Symbol;


