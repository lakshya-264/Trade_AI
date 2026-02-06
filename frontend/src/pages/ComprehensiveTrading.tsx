import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import comprehensiveTradingApi, { ChartDataRequest, PatternAnalyzeRequest } from '../services/comprehensiveTradingApi';

const ComprehensiveTrading: React.FC = () => {
  const navigate = useNavigate();
  // Temporary mock switch to guarantee render even if APIs return unexpected shapes
  const USE_MOCK = true;
  const MOCK: {
    patterns: string[];
    symbols: string[];
    chartData: { candles: { o: number; h: number; l: number; c: number }[] };
    patternResult: { patterns: any[] };
    smv: any;
    optionsIdea: any;
  } = {
    patterns: ['doji', 'hammer', 'engulfing'],
    symbols: ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK'],
    chartData: {
      candles: Array.from({ length: 50 }).map((_, i) => ({
        o: 100 + i * 0.3,
        h: 102 + i * 0.3,
        l: 98 + i * 0.3,
        c: 101 + i * 0.3,
      })),
    },
    patternResult: {
      patterns: [
        { name: 'doji', count: 3, significance: 'medium' },
        { name: 'hammer', count: 2, significance: 'high' },
      ],
    },
    smv: {
      levels: Array.from({ length: 10 }).map((_, i) => ({
        price: 100 + i,
        type: i % 2 === 0 ? 'bullish' : 'bearish',
        class: i % 3 === 0 ? 'Smart Money' : 'Retail',
        z_score: 2.1 + (i % 3) * 0.4,
        volume: 100000 + i * 5000,
      })),
      bubble: { max_abs_z: 3.2, dir: 1, price: 123.45, class: 'Smart Money', color: '#00ffbb' },
      pl_table: { retail_profit_vol: 100000, retail_loss_vol: 50000, smart_profit_vol: 150000, smart_loss_vol: 40000 },
    },
    optionsIdea: {
      strategy: 'Covered Call',
      strikes: [100, 105, 110],
      payoff: { maxProfit: 1500, maxLoss: 500, breakeven: 99.5 },
    },
  };
  const [status, setStatus] = useState<any>(null);
  const [performance, setPerformance] = useState<any>(null);
  const [patterns, setPatterns] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [symbols, setSymbols] = useState<any[]>([]);
  const [activeSymbol, setActiveSymbol] = useState('RELIANCE');
  const [timeframe, setTimeframe] = useState('1D');
  const [chartData, setChartData] = useState<any>(null);
  const [patternResult, setPatternResult] = useState<any>(null);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [optionsIdea, setOptionsIdea] = useState<any>(null);
  const [smv, setSmv] = useState<any>(null);
  const [smvAlerts, setSmvAlerts] = useState<any[]>([]);
  const [smvWsConnection, setSmvWsConnection] = useState<WebSocket | null>(null);
  const [userId, setUserId] = useState<string>(() => {
    const stored = typeof window !== 'undefined' ? window.localStorage.getItem('userId') : null;
    return stored || '1';
  });
  const [alerts, setAlerts] = useState<any[]>([]);
  const [watchlists, setWatchlists] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        if (USE_MOCK) {
          setStatus({ ok: true });
          setPerformance({ latency_ms: 42, uptime: '99.9%' });
          setPatterns([...(MOCK.patterns as string[])]);
        } else {
          const [st, pf, pt] = await Promise.all([
            comprehensiveTradingApi.getSystemStatus(),
            comprehensiveTradingApi.getSystemPerformance(),
            comprehensiveTradingApi.getAvailablePatterns(),
          ]);
          setStatus(st);
          setPerformance(pf);
          setPatterns(Array.isArray(pt) ? pt : []);
        }
      } catch (e: any) {
        setError(e?.message || 'Failed to load comprehensive trading info');
        if (USE_MOCK) {
          setStatus({ ok: true });
          setPerformance({ latency_ms: 42, uptime: '99.9%' });
          setPatterns([...(MOCK.patterns as string[])]);
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const onSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      if (USE_MOCK) {
        const list = MOCK.symbols.filter((s) => s.includes((query || '').toUpperCase()));
        setSymbols(list);
      } else {
        const res = await comprehensiveTradingApi.searchSymbols(query);
        setSymbols(Array.isArray(res) ? res : []);
      }
    } catch (e: any) {
      const msg = e?.message || 'Search failed';
      setError(msg);
      showToast(msg);
      if (USE_MOCK) {
        setSymbols([...(MOCK.symbols as string[])]);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadChart = async () => {
    try {
      setLoading(true);
      setError(null);
      const payload: ChartDataRequest = { symbol: activeSymbol, timeframe };
      if (USE_MOCK) {
        setChartData(MOCK.chartData);
      } else {
        const res = await comprehensiveTradingApi.getChartData(payload);
        const valid = Array.isArray(res?.candles) || Array.isArray(res?.data);
        setChartData(valid ? res : MOCK.chartData);
      }
    } catch (e: any) {
      const msg = e?.message || 'Failed to load chart data';
      setError(msg);
      showToast(msg);
      if (USE_MOCK) setChartData(MOCK.chartData);
    } finally {
      setLoading(false);
    }
  };

  const analyzePatterns = async () => {
    try {
      setLoading(true);
      setError(null);
      const payload: PatternAnalyzeRequest = { symbol: activeSymbol, timeframe, patterns } as any;
      if (USE_MOCK) {
        setPatternResult(MOCK.patternResult);
      } else {
        const res = await comprehensiveTradingApi.analyzePatterns(payload);
        const pr = (res && Array.isArray(res?.patterns)) ? res : MOCK.patternResult;
        setPatternResult(pr);
      }
    } catch (e: any) {
      const msg = e?.message || 'Failed to analyze patterns';
      setError(msg);
      showToast(msg);
      if (USE_MOCK) setPatternResult(MOCK.patternResult);
    } finally {
      setLoading(false);
    }
  };

  const generateRecommendation = async () => {
    try {
      setLoading(true);
      setError(null);
      if (USE_MOCK) {
        setRecommendation({ action: 'BUY', confidence: 0.72, reasoning: 'Uptrend with positive momentum and bullish SMV.' });
      } else {
        const res = await comprehensiveTradingApi.generateRecommendation({ symbol: activeSymbol, timeframe, analysis_data: {}, user_preferences: {} });
        setRecommendation(res);
      }
    } catch (e: any) {
      const msg = e?.message || 'Failed to generate recommendation';
      setError(msg);
      showToast(msg);
      if (USE_MOCK) setRecommendation({ action: 'HOLD', confidence: 0.5, reasoning: 'Mock fallback' });
    } finally {
      setLoading(false);
    }
  };

  const suggestOptions = async () => {
    try {
      setLoading(true);
      setError(null);
      if (USE_MOCK) {
        setOptionsIdea(MOCK.optionsIdea);
      } else {
        const res = await comprehensiveTradingApi.optionsSuggestion({ symbol: activeSymbol, timeframe, underlying_price: 100, days_to_expiry: 30, option_type: 'call', risk_tolerance: 'medium' });
        setOptionsIdea(res);
      }
    } catch (e: any) {
      const msg = e?.message || 'Failed to get options suggestion';
      setError(msg);
      showToast(msg);
      if (USE_MOCK) setOptionsIdea(MOCK.optionsIdea);
    } finally {
      setLoading(false);
    }
  };

  const loadAlerts = async () => {
    try {
      const res = await comprehensiveTradingApi.getAlerts();
      setAlerts(Array.isArray(res) ? res : []);
    } catch {
      setAlerts([]);
    }
  };

  const createSampleAlert = async () => {
    try {
      await comprehensiveTradingApi.createAlert({ symbol: activeSymbol, rule: 'price_cross', operator: 'gt', value: 100, notifications: { in_app: true } });
      await loadAlerts();
      showToast('Alert created');
    } catch (e: any) {
      showToast(e?.message || 'Failed to create alert');
    }
  };

  const loadWatchlists = async () => {
    try {
      const res = await comprehensiveTradingApi.getWatchlists();
      setWatchlists(Array.isArray(res) ? res : []);
    } catch {
      setWatchlists([]);
    }
  };

  const createSampleWatchlist = async () => {
    try {
      await comprehensiveTradingApi.createWatchlist({ name: 'My Watchlist', symbols: [activeSymbol] });
      await loadWatchlists();
      showToast('Watchlist created');
    } catch (e: any) {
      showToast(e?.message || 'Failed to create watchlist');
    }
  };

  // SMV Alert functions
  const loadSMV = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await comprehensiveTradingApi.getSmartMoneyVolumeActivity({
        symbol: activeSymbol,
        timeframe,
        lower_timeframe: '5m',
        z_len: 50,
        threshold_abs: 2.0,
        who: 'Both'
      });
      setSmv(res);
      showToast('SMV data loaded successfully!');
    } catch (e: any) {
      setError(e?.message || 'Failed to load SMV data');
      showToast(e?.message || 'Failed to load SMV data');
    } finally {
      setLoading(false);
    }
  };

  const createSMVAlert = async (activityType: string) => {
    try {
      setLoading(true);
      setError(null);
      await comprehensiveTradingApi.createSmartMoneyAlert(
        activeSymbol,
        activityType,
        { in_app: true, email: false },
        30
      );
      showToast(`SMV ${activityType} alert created for ${activeSymbol}`);
    } catch (e: any) {
      setError(e?.message || 'Failed to create SMV alert');
      showToast(e?.message || 'Failed to create SMV alert');
    } finally {
      setLoading(false);
    }
  };

  const testSMVAlert = async () => {
    try {
      setLoading(true);
      setError(null);
      await comprehensiveTradingApi.testSmartMoneyAlert(activeSymbol);
      showToast(`Test SMV alert sent for ${activeSymbol}`);
    } catch (e: any) {
      setError(e?.message || 'Failed to test SMV alert');
      showToast(e?.message || 'Failed to test SMV alert');
    } finally {
      setLoading(false);
    }
  };

  const connectSMVAlerts = () => {
    if (smvWsConnection) {
      smvWsConnection.close();
    }
    const effectiveUserId = String(userId || '1');
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('userId', effectiveUserId);
      }
    } catch {}
    const ws = comprehensiveTradingApi.connectSmartMoneyAlerts(effectiveUserId, (alert) => {
      // Add the alert to the state
      setSmvAlerts(prev => [alert, ...prev].slice(0, 10)); // Keep only last 10 alerts
    });
    setSmvWsConnection(ws);
    showToast('SMV Alerts WebSocket connected');
  };

  const disconnectSMVAlerts = () => {
    if (smvWsConnection) {
      smvWsConnection.close();
      setSmvWsConnection(null);
      showToast('SMV Alerts WebSocket disconnected');
    }
  };

  useEffect(() => {
    loadAlerts();
    loadWatchlists();
  }, []);

  // Build OHLC candlesticks with zoom/tooltip
  const candlestickChart = useMemo(() => {
    const candles = Array.isArray(chartData?.candles) ? chartData.candles : 
                   Array.isArray(chartData?.data) ? chartData.data : [];
    if (!candles.length || !Array.isArray(candles)) return null;
    
    try {
      const w = 600, h = 300, pad = 20;
      const min = Math.min(...candles.map((c: any) => Number(c.low ?? c.l ?? 0))), 
            max = Math.max(...candles.map((c: any) => Number(c.high ?? c.h ?? 0)));
      const range = max - min || 1;
      const stepX = (w - pad * 2) / Math.max(1, candles.length - 1);
      const candleWidth = Math.max(2, stepX * 0.8);
      return { candles, w, h, pad, min, max, range, stepX, candleWidth };
    } catch (error) {
      console.error('Error creating candlestick chart:', error);
      return null;
    }
  }, [chartData]);

  type MiniCandleProps = { o: number; high: number; low: number; c: number; width: number; height: number; x: number; y: number; min: number; max: number };
  const MiniCandlestick: React.FC<MiniCandleProps> = ({ o, high, low, c, width, height, x, y, min, max }) => {
    const range = max - min || 1;
    const scaleY = (v: number) => y + (height - ((v - min) / range) * height);
    const isGreen = c >= o;
    const topY = scaleY(Math.max(o, c));
    const bottomY = scaleY(Math.min(o, c));
    const bodyTop = Math.min(topY, bottomY);
    const bodyBottom = Math.max(topY, bottomY);
    const bodyHeight = Math.max(1, bodyBottom - bodyTop);
    const wickTop = scaleY(high), wickBottom = scaleY(low);
    return (
      <g>
        <line x1={x + width/2} y1={wickTop} x2={x + width/2} y2={wickBottom} stroke={isGreen ? '#10B981' : '#EF4444'} strokeWidth="1"/>
        <rect x={x} y={bodyTop} width={width} height={bodyHeight} fill={isGreen ? '#10B981' : '#EF4444'} stroke={isGreen ? '#059669' : '#DC2626'}/>
      </g>
    );
  };

  return (
    <div className="space-y-4 relative">
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-3 py-2 rounded shadow">
          {toast}
        </div>
      )}
      {loading && (
        <div className="absolute inset-0 bg-black/10 dark:bg-white/5 flex items-center justify-center z-40">
          <div className="animate-spin h-6 w-6 border-2 border-gray-400 border-t-transparent rounded-full"/>
        </div>
      )}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Comprehensive Trading</h1>
        <button
          onClick={() => navigate('/comprehensive-trading-pro')}
          className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Professional View
        </button>
      </div>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      {loading && <div className="text-sm text-gray-500">Loading…</div>}

      <section className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">System Status</h2>
        <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(status ?? {}, null, 2)}</pre>
      </section>

      <section className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">Performance</h2>
        <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(performance ?? {}, null, 2)}</pre>
      </section>

      <section className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">Available Patterns</h2>
        <div className="flex flex-wrap gap-2">
          {(() => {
            try {
              return Array.isArray(patterns) ? patterns.map((p, i) => (
                <span key={i} className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">{p}</span>
              )) : null;
            } catch (error) {
              console.error('Error mapping patterns:', error, 'patterns:', patterns);
              return <span className="text-red-500">Error loading patterns</span>;
            }
          })()}
        </div>
        <div className="mt-3 flex gap-2">
          <input className="border dark:border-gray-700 rounded px-3 py-2 dark:bg-gray-700 dark:text-white" value={activeSymbol} onChange={e => setActiveSymbol(e.target.value.toUpperCase())} />
          <select className="border dark:border-gray-700 rounded px-3 py-2 dark:bg-gray-700 dark:text-white" value={timeframe} onChange={e => setTimeframe(e.target.value)}>
            <option value="1D">1D</option>
            <option value="1H">1H</option>
            <option value="5m">5m</option>
          </select>
          <button onClick={loadChart} className="px-3 py-2 bg-blue-600 text-white rounded">Load Chart</button>
          <button onClick={analyzePatterns} className="px-3 py-2 bg-purple-600 text-white rounded">Analyze Patterns</button>
          <button onClick={generateRecommendation} className="px-3 py-2 bg-green-600 text-white rounded">AI Recommendation</button>
          <button onClick={suggestOptions} className="px-3 py-2 bg-amber-600 text-white rounded">Options Suggestion</button>
        </div>
        {/* OHLC Candlestick Chart */}
        {candlestickChart && (
          <div className="mt-4">
            <svg width={candlestickChart.w} height={candlestickChart.h} className="w-full max-w-2xl border dark:border-gray-600 rounded">
              <rect width={candlestickChart.w} height={candlestickChart.h} fill="transparent"/>
              {Array.isArray(candlestickChart.candles) ? candlestickChart.candles.map((candle, i) => {
                const x = candlestickChart.pad + i * candlestickChart.stepX;
                const o = Number(candle.open ?? candle.o ?? 0);
                const high = Number(candle.high ?? candle.h ?? 0);
                const low = Number(candle.low ?? candle.l ?? 0);
                const c = Number(candle.close ?? candle.c ?? 0);
                return (
                  <MiniCandlestick
                    key={i}
                    o={o} high={high} low={low} c={c}
                    width={candlestickChart.candleWidth}
                    height={candlestickChart.h - candlestickChart.pad * 2}
                    x={x - candlestickChart.candleWidth/2}
                    y={candlestickChart.pad}
                    min={candlestickChart.min}
                    max={candlestickChart.max}
                  />
                );
              }) : null}
            </svg>
            {/* Smart Money Volume overlay: bubble marker */}
            {smv?.bubble && (
              <div className="mt-2 text-xs text-gray-600 dark:text-gray-300">
                Bubble: class {smv.bubble.class} | {smv.bubble.dir === 1 ? 'Bull' : 'Bear'} | |Z|={Number(smv.bubble.max_abs_z).toFixed(2)} at price ~{Number(smv.bubble.price).toFixed(2)}
              </div>
            )}
          </div>
        )}

        {/* Pattern table */}
        {patternResult?.patterns && Array.isArray(patternResult.patterns) && patternResult.patterns.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left border-b dark:border-gray-700">
                  <th className="py-2 pr-4">Pattern</th>
                  <th className="py-2 pr-4">Count</th>
                  <th className="py-2 pr-4">Significance</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(patternResult?.patterns) ? patternResult.patterns.map((p: any, i: number) => (
                  <tr key={i} className="border-b dark:border-gray-700">
                    <td className="py-2 pr-4 font-medium">{p.name ?? p.pattern ?? '-'}</td>
                    <td className="py-2 pr-4">{p.count ?? '-'}</td>
                    <td className="py-2 pr-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        (p.significance ?? 'low') === 'high' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                        (p.significance ?? 'low') === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                        'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      }`}>
                        {p.significance ?? 'low'}
                      </span>
                    </td>
                  </tr>
                )) : null}
              </tbody>
            </table>
          </div>
        )}

        {/* Recommendation & Options */}
        {(recommendation || optionsIdea) && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border dark:border-gray-700 rounded p-3">
              <h3 className="font-semibold mb-2">Recommendation</h3>
              <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(recommendation ?? {}, null, 2)}</pre>
            </div>
            <div className="border dark:border-gray-700 rounded p-3">
              <h3 className="font-semibold mb-2">Options Suggestion</h3>
              <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(optionsIdea ?? {}, null, 2)}</pre>
            </div>
          </div>
        )}
      </section>

      {/* Smart Money Volume Activity */}
      <section className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">Smart Money Volume Activity</h2>
        <div className="flex gap-2">
          <button
            onClick={async () => {
              try {
                setLoading(true);
                const res = await comprehensiveTradingApi.getSmartMoneyVolumeActivity({ symbol: activeSymbol, timeframe, lower_timeframe: '5m', z_len: 50, threshold_abs: 2.0, who: 'Both' });
                setSmv(res);
                showToast('Smart Money Volume loaded');
              } catch (e: any) {
                setError(e?.message || 'Failed to load Smart Money Volume');
                showToast(e?.message || 'Failed to load Smart Money Volume');
              } finally {
                setLoading(false);
              }
            }}
            className="px-3 py-2 bg-indigo-600 text-white rounded"
          >
            Load SMV
          </button>
        </div>
        {smv && (
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="border dark:border-gray-700 rounded p-3">
              <h3 className="font-semibold mb-2">P/L Volume</h3>
              <div className="grid grid-cols-3 gap-2">
                <div className="font-medium">Class</div>
                <div className="font-medium text-center">Profit</div>
                <div className="font-medium text-center">Loss</div>
                <div>Retail</div>
                <div className="text-center">{Number(smv?.pl?.retail_profit ?? 0).toLocaleString()}</div>
                <div className="text-center">{Number(smv?.pl?.retail_loss ?? 0).toLocaleString()}</div>
                <div>Smart</div>
                <div className="text-center">{Number(smv?.pl?.smart_profit ?? 0).toLocaleString()}</div>
                <div className="text-center">{Number(smv?.pl?.smart_loss ?? 0).toLocaleString()}</div>
              </div>
            </div>
            <div className="border dark:border-gray-700 rounded p-3 overflow-x-auto">
              <h3 className="font-semibold mb-2">Levels ({smv?.count ?? 0})</h3>
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="text-left border-b dark:border-gray-700">
                    <th className="py-1 pr-3">Price</th>
                    <th className="py-1 pr-3">Type</th>
                    <th className="py-1 pr-3">Class</th>
                    <th className="py-1 pr-3">Vol</th>
                    <th className="py-1 pr-3">|Z|</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(smv?.levels) ? smv.levels.slice(0, 50).map((lv: any, i: number) => (
                    <tr key={i} className="border-b dark:border-gray-700">
                      <td className="py-1 pr-3">{Number(lv.price).toFixed(2)}</td>
                      <td className="py-1 pr-3">{lv.type === 1 ? 'Bull' : 'Bear'}</td>
                      <td className="py-1 pr-3">{lv.class === 1 ? 'Retail' : 'Smart'}</td>
                      <td className="py-1 pr-3">{Number(lv.volume ?? 0).toLocaleString()}</td>
                      <td className="py-1 pr-3">{Math.abs(Number(lv.z ?? 0)).toFixed(2)}</td>
                    </tr>
                  )) : null}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* Alerts & Watchlists */}
      <section className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">Alerts & Watchlists</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
          <div className="border dark:border-gray-700 rounded p-3">
            <h3 className="font-semibold mb-2">Create Alert</h3>
            <div className="flex flex-wrap gap-2 items-center">
              <input className="border dark:border-gray-700 rounded px-3 py-2 dark:bg-gray-700 dark:text-white" value={activeSymbol} onChange={e => setActiveSymbol(e.target.value.toUpperCase())} />
              <select className="border dark:border-gray-700 rounded px-3 py-2 dark:bg-gray-700 dark:text-white" defaultValue="price_cross">
                <option value="price_cross">Price Cross</option>
                <option value="pct_change">% Change</option>
              </select>
              <select className="border dark:border-gray-700 rounded px-3 py-2 dark:bg-gray-700 dark:text-white" defaultValue="gt">
                <option value="gt">&gt;</option>
                <option value="lt">&lt;</option>
                <option value="eq">=</option>
              </select>
              <input type="number" className="border dark:border-gray-700 rounded px-3 py-2 w-28 dark:bg-gray-700 dark:text-white" placeholder="Value" />
              <button onClick={createSampleAlert} className="px-3 py-2 bg-pink-600 text-white rounded">Add Alert</button>
            </div>
          </div>
          <div className="border dark:border-gray-700 rounded p-3">
            <h3 className="font-semibold mb-2">Create Watchlist</h3>
            <div className="flex flex-wrap gap-2 items-center">
              <input className="border dark:border-gray-700 rounded px-3 py-2 dark:bg-gray-700 dark:text-white" defaultValue="My Watchlist" />
              <input className="border dark:border-gray-700 rounded px-3 py-2 dark:bg-gray-700 dark:text-white" defaultValue={activeSymbol} />
              <button onClick={createSampleWatchlist} className="px-3 py-2 bg-teal-600 text-white rounded">Add Watchlist</button>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-semibold mb-2">Alerts</h3>
            <ul className="space-y-1 text-sm">
              {Array.isArray(alerts) ? alerts.map((a, i) => (
                <li key={a.id || i} className="border-b dark:border-gray-700 py-1 flex items-center justify-between">
                  <span className="truncate">{a.name || a.title || a.type || a.symbol || JSON.stringify(a)}</span>
                  <div className="flex gap-2">
                    <button onClick={async () => { await comprehensiveTradingApi.updateAlert(a.id, { status: a.status === 'paused' ? 'active' : 'paused' }); await loadAlerts(); }} className="px-2 py-1 text-xs bg-gray-600 text-white rounded">{a.status === 'paused' ? 'Resume' : 'Pause'}</button>
                    <button onClick={async () => { await comprehensiveTradingApi.deleteAlert(a.id); await loadAlerts(); }} className="px-2 py-1 text-xs bg-red-600 text-white rounded">Delete</button>
                  </div>
                </li>
              )) : null}
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Watchlists</h3>
            <ul className="space-y-1 text-sm">
              {Array.isArray(watchlists) ? watchlists.map((w, i) => (
                <li key={w.id || i} className="border-b dark:border-gray-700 py-1 flex items-center justify-between">
                  <span className="truncate">{w.name || JSON.stringify(w)}</span>
                  <div className="flex gap-2">
                    <button onClick={async () => { await comprehensiveTradingApi.updateWatchlist(w.id, { name: w.name }); await loadWatchlists(); }} className="px-2 py-1 text-xs bg-gray-600 text-white rounded">Save</button>
                    <button onClick={async () => { await comprehensiveTradingApi.deleteWatchlist(w.id); await loadWatchlists(); }} className="px-2 py-1 text-xs bg-red-600 text-white rounded">Delete</button>
                  </div>
                </li>
              )) : null}
            </ul>
          </div>
        </div>
      </section>

      {/* Smart Money Volume Alerts */}
      <section className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">Smart Money Volume Alerts</h2>
        <div className="space-y-3">
          <div className="flex gap-2">
            <button onClick={loadSMV} className="px-3 py-2 bg-purple-600 text-white rounded">Load SMV</button>
            <button onClick={testSMVAlert} className="px-3 py-2 bg-orange-600 text-white rounded">Test Alert</button>
            <button onClick={connectSMVAlerts} className="px-3 py-2 bg-green-600 text-white rounded">Connect WS</button>
            <button onClick={disconnectSMVAlerts} className="px-3 py-2 bg-red-600 text-white rounded">Disconnect WS</button>
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            <button onClick={() => createSMVAlert('smart_money_bullish')} className="px-3 py-2 bg-green-500 text-white rounded text-sm">SM Bullish Alert</button>
            <button onClick={() => createSMVAlert('smart_money_bearish')} className="px-3 py-2 bg-red-500 text-white rounded text-sm">SM Bearish Alert</button>
            <button onClick={() => createSMVAlert('retail_bullish')} className="px-3 py-2 bg-blue-500 text-white rounded text-sm">Retail Bullish Alert</button>
            <button onClick={() => createSMVAlert('retail_bearish')} className="px-3 py-2 bg-yellow-500 text-white rounded text-sm">Retail Bearish Alert</button>
          </div>

          {smvWsConnection && (
            <div className="text-sm text-green-600 dark:text-green-400">
              ✅ SMV Alerts WebSocket Connected
            </div>
          )}

          {Array.isArray(smvAlerts) && smvAlerts.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">Recent SMV Alerts</h3>
              <ul className="space-y-1 text-sm">
                {smvAlerts.map((alert, i) => (
                  <li key={i} className="border-b dark:border-gray-700 py-1">
                    <span className="font-medium">{alert.symbol}</span> - {alert.class} {alert.direction} (Z: {alert.z_score?.toFixed(2)})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>

      <section className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">Symbol Search</h2>
        <div className="flex gap-2 mb-3">
          <input className="border dark:border-gray-700 rounded px-3 py-2 flex-1 dark:bg-gray-700 dark:text-white" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search symbols" />
          <button onClick={onSearch} className="px-4 py-2 bg-blue-600 text-white rounded">Search</button>
        </div>
        <ul className="space-y-1 text-sm">
          {(() => {
            try {
              return Array.isArray(symbols) ? symbols.map((s, i) => (
                <li key={i} className="border-b dark:border-gray-700 py-1">{typeof s === 'string' ? s : (s.symbol || JSON.stringify(s))}</li>
              )) : null;
            } catch (error) {
              console.error('Error mapping symbols:', error, 'symbols:', symbols);
              return <li className="text-red-500">Error loading symbols</li>;
            }
          })()}
        </ul>
      </section>
    </div>
  );
};

export default ComprehensiveTrading;


