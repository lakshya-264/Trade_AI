import React, { useState, useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi, LineData } from 'lightweight-charts';
import { Play, Download, TrendingUp, TrendingDown, Target, BarChart3, Save } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { httpClient } from '../config/api';

interface BacktestStrategy {
  id: string;
  name: string;
  description: string;
  parameters: Record<string, any>;
}

interface BacktestResult {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  profitFactor: number;
  averageWin: number;
  averageLoss: number;
  totalPnL: number;
  trades: Array<{
    entryTime: number;
    exitTime: number;
    entryPrice: number;
    exitPrice: number;
    pnl: number;
    pnlPercent: number;
    type: 'long' | 'short';
  }>;
  equityCurve: Array<{ time: number; value: number }>;
}

interface EnhancedBacktestingProps {
  symbol?: string;
  onClose?: () => void;
}

const EnhancedBacktesting: React.FC<EnhancedBacktestingProps> = ({ 
  symbol = 'RELIANCE',
  onClose 
}) => {
  const [selectedStrategy, setSelectedStrategy] = useState<string>('moving_average_crossover');
  const [parameters, setParameters] = useState({
    fastPeriod: 10,
    slowPeriod: 20,
    stopLoss: 2.0,
    takeProfit: 4.0,
    rsiPeriod: 14,
    oversold: 30,
    overbought: 70,
  });
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2024-01-01');
  
  const chartRef = useRef<HTMLDivElement>(null);
  const equityChartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<IChartApi | null>(null);
  const equityChartInstance = useRef<IChartApi | null>(null);
  const equitySeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  const strategies: BacktestStrategy[] = [
    {
      id: 'moving_average_crossover',
      name: 'Moving Average Crossover',
      description: 'Buy when fast MA crosses above slow MA, sell when it crosses below',
      parameters: { fastPeriod: 10, slowPeriod: 20 }
    },
    {
      id: 'rsi_oversold',
      name: 'RSI Oversold/Overbought',
      description: 'Buy when RSI < 30, sell when RSI > 70',
      parameters: { rsiPeriod: 14, oversold: 30, overbought: 70 }
    },
    {
      id: 'macd_crossover',
      name: 'MACD Crossover',
      description: 'Buy on MACD bullish crossover, sell on bearish crossover',
      parameters: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 }
    },
    {
      id: 'bollinger_bands',
      name: 'Bollinger Bands',
      description: 'Buy when price touches lower band, sell when it touches upper band',
      parameters: { period: 20, stdDev: 2 }
    }
  ];

  // Initialize equity curve chart
  useEffect(() => {
    if (equityChartRef.current && !equityChartInstance.current) {
      equityChartInstance.current = createChart(equityChartRef.current, {
        width: equityChartRef.current.clientWidth,
        height: 300,
        layout: {
          background: { color: '#1a1d28' },
          textColor: '#d1d4dc',
        },
        grid: {
          vertLines: { color: '#2B2B43' },
          horzLines: { color: '#2B2B43' },
        },
        timeScale: {
          borderColor: '#2B2B43',
          timeVisible: true,
        },
      });
    }

    return () => {
      if (equityChartInstance.current) {
        equityChartInstance.current.remove();
        equityChartInstance.current = null;
        equitySeriesRef.current = null;
      }
    };
  }, []);

  const runBacktest = async () => {
    setLoading(true);
    try {
      const response = await httpClient.post('/api/backtesting/run', {
        strategy: selectedStrategy,
        parameters,
        symbol,
        startDate,
        endDate,
      }) as any;

      if (response.success && response.data) {
        setResults(response.data);
        updateEquityChart(response.data.equityCurve);
        toast.success('Backtest completed successfully');
      } else {
        toast.error(response.message || 'Backtest failed');
      }
    } catch (error: any) {
      console.error('Backtest failed:', error);
      toast.error(error?.response?.data?.detail || 'Failed to run backtest');
    } finally {
      setLoading(false);
    }
  };

  const updateEquityChart = (equityCurve: Array<{ time: number; value: number }>) => {
    if (!equityChartInstance.current || !equityCurve.length) return;

    // Remove existing series
    if (equitySeriesRef.current) {
      try {
        equityChartInstance.current.removeSeries(equitySeriesRef.current);
      } catch (e) {
        console.warn('Error removing series:', e);
      }
    }

    // Add new series
    const series = equityChartInstance.current.addLineSeries({
      color: '#3B82F6',
      lineWidth: 2,
      title: 'Equity Curve'
    });
    
    series.setData(equityCurve.map(point => ({
      time: point.time as any,
      value: point.value
    })));
    
    equitySeriesRef.current = series;
    equityChartInstance.current.timeScale().fitContent();
  };

  const exportResults = () => {
    if (!results) return;
    
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `backtest_${symbol}_${selectedStrategy}_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Results exported');
  };

  const currentStrategy = strategies.find(s => s.id === selectedStrategy);

  return (
    <div className="p-6 space-y-6 bg-[#131722] min-h-screen">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Enhanced Backtesting</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#2a2e39] hover:bg-[#3a3e49] rounded-lg text-white"
          >
            Close
          </button>
        )}
      </div>

      {/* Strategy Selection */}
      <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 text-white">Strategy Selection</h3>
        <select
          value={selectedStrategy}
          onChange={(e) => setSelectedStrategy(e.target.value)}
          className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
        >
          {strategies.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        {currentStrategy && (
          <p className="mt-2 text-sm text-gray-400">{currentStrategy.description}</p>
        )}
      </div>

      {/* Parameters */}
      <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 text-white">Parameters</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {selectedStrategy === 'moving_average_crossover' && (
            <>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Fast Period</label>
                <input
                  type="number"
                  value={parameters.fastPeriod}
                  onChange={(e) => setParameters({ ...parameters, fastPeriod: parseInt(e.target.value) })}
                  className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Slow Period</label>
                <input
                  type="number"
                  value={parameters.slowPeriod}
                  onChange={(e) => setParameters({ ...parameters, slowPeriod: parseInt(e.target.value) })}
                  className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
                />
              </div>
            </>
          )}
          {selectedStrategy === 'rsi_oversold' && (
            <>
              <div>
                <label className="block text-sm text-gray-400 mb-1">RSI Period</label>
                <input
                  type="number"
                  value={parameters.rsiPeriod}
                  onChange={(e) => setParameters({ ...parameters, rsiPeriod: parseInt(e.target.value) })}
                  className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Oversold Level</label>
                <input
                  type="number"
                  value={parameters.oversold}
                  onChange={(e) => setParameters({ ...parameters, oversold: parseInt(e.target.value) })}
                  className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Overbought Level</label>
                <input
                  type="number"
                  value={parameters.overbought}
                  onChange={(e) => setParameters({ ...parameters, overbought: parseInt(e.target.value) })}
                  className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
                />
              </div>
            </>
          )}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Stop Loss (%)</label>
            <input
              type="number"
              step="0.1"
              value={parameters.stopLoss}
              onChange={(e) => setParameters({ ...parameters, stopLoss: parseFloat(e.target.value) })}
              className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Take Profit (%)</label>
            <input
              type="number"
              step="0.1"
              value={parameters.takeProfit}
              onChange={(e) => setParameters({ ...parameters, takeProfit: parseFloat(e.target.value) })}
              className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
            />
          </div>
        </div>
      </div>

      {/* Date Range */}
      <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 text-white">Date Range</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full p-2 bg-[#2a2e39] rounded text-white border border-gray-600"
            />
          </div>
        </div>
      </div>

      {/* Run Button */}
      <div className="flex gap-4">
        <button
          onClick={runBacktest}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Play className="w-5 h-5" />
          {loading ? 'Running...' : 'Run Backtest'}
        </button>
        {results && (
          <button
            onClick={exportResults}
            className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg text-white font-medium"
          >
            <Download className="w-5 h-5" />
            Export Results
          </button>
        )}
      </div>

      {/* Results */}
      {results && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Win Rate</div>
              <div className="text-2xl font-bold text-green-400">{results.winRate.toFixed(2)}%</div>
            </div>
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Total Return</div>
              <div className={`text-2xl font-bold ${results.totalReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {results.totalReturn >= 0 ? '+' : ''}{results.totalReturn.toFixed(2)}%
              </div>
            </div>
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Sharpe Ratio</div>
              <div className="text-2xl font-bold text-white">{results.sharpeRatio.toFixed(2)}</div>
            </div>
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Max Drawdown</div>
              <div className="text-2xl font-bold text-red-400">{results.maxDrawdown.toFixed(2)}%</div>
            </div>
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Total Trades</div>
              <div className="text-2xl font-bold text-white">{results.totalTrades}</div>
            </div>
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Winning Trades</div>
              <div className="text-2xl font-bold text-green-400">{results.winningTrades}</div>
            </div>
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Profit Factor</div>
              <div className="text-2xl font-bold text-white">{results.profitFactor.toFixed(2)}</div>
            </div>
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Total P&L</div>
              <div className={`text-2xl font-bold ${results.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ₹{results.totalPnL.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Equity Curve Chart */}
          <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4 text-white">Equity Curve</h3>
            <div ref={equityChartRef} className="h-96 w-full" />
          </div>

          {/* Trades Table */}
          {results.trades && results.trades.length > 0 && (
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold mb-4 text-white">Trade History</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left p-2 text-gray-400">Entry</th>
                      <th className="text-left p-2 text-gray-400">Exit</th>
                      <th className="text-left p-2 text-gray-400">Entry Price</th>
                      <th className="text-left p-2 text-gray-400">Exit Price</th>
                      <th className="text-left p-2 text-gray-400">P&L</th>
                      <th className="text-left p-2 text-gray-400">P&L %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.trades.slice(0, 20).map((trade, idx) => (
                      <tr key={idx} className="border-b border-gray-800">
                        <td className="p-2 text-white">{new Date(trade.entryTime * 1000).toLocaleDateString()}</td>
                        <td className="p-2 text-white">{new Date(trade.exitTime * 1000).toLocaleDateString()}</td>
                        <td className="p-2 text-white">₹{trade.entryPrice.toFixed(2)}</td>
                        <td className="p-2 text-white">₹{trade.exitPrice.toFixed(2)}</td>
                        <td className={`p-2 ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          ₹{trade.pnl.toFixed(2)}
                        </td>
                        <td className={`p-2 ${trade.pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {trade.pnlPercent >= 0 ? '+' : ''}{trade.pnlPercent.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default EnhancedBacktesting;
