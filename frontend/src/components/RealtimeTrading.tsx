/**
 * Real-time Trading Execution Component
 * Executes Nifty 50 signals and manages portfolio
 */

import React, { useState, useEffect } from 'react';
import { 
  Play, Pause, BarChart3, TrendingUp, TrendingDown, 
  Settings, RefreshCw, AlertCircle, CheckCircle, Clock,
  Target, DollarSign, Activity, Eye
} from 'lucide-react';
import { httpClient } from '../config/api';
import { toast } from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';

interface ExecutionResult {
  symbol: string;
  signal_type: string;
  confidence: number;
  execution_result: {
    success: boolean;
    order_id?: number;
    message?: string;
    error?: string;
  };
}

interface PortfolioHolding {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  total_value: number;
  pnl: number;
  pnl_percent: number;
  last_updated: string;
}

interface SignalAccuracy {
  total_trades: number;
  win_rate: number;
  total_pnl_percent: number;
  profitable_trades: number;
  losing_trades: number;
  accuracy_score: number;
}

const RealtimeTrading: React.FC = () => {
  const { user } = useAuth();
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastExecution, setLastExecution] = useState<string>('');
  const [executionResults, setExecutionResults] = useState<ExecutionResult[]>([]);
  const [portfolioHoldings, setPortfolioHoldings] = useState<PortfolioHolding[]>([]);
  const [signalAccuracy, setSignalAccuracy] = useState<SignalAccuracy | null>(null);
  const [settings, setSettings] = useState({
    timeframe: '5m',
    maxTrades: 5,
    minConfidence: 0.7,
    paperTrading: true
  });

  useEffect(() => {
    fetchPortfolioHoldings();
    fetchSignalAccuracy();
  }, []);

  const executeSignals = async () => {
    setIsExecuting(true);
    try {
      const response = await httpClient.post('/api/realtime-trading/execute-nifty50-signals', {
        params: {
          timeframe: settings.timeframe,
          max_trades: settings.maxTrades,
          min_confidence: settings.minConfidence,
          paper_trading: settings.paperTrading
        }
      });

      if (response.success) {
        const data = response.data as any;
        setExecutionResults(data.trades || []);
        setLastExecution(data.execution_time);
        
        toast.success(`Executed ${data.executed_trades} trades successfully!`);
        
        // Refresh portfolio and accuracy
        await fetchPortfolioHoldings();
        await fetchSignalAccuracy();
      } else {
        toast.error(response.error || 'Failed to execute signals');
      }
    } catch (error: any) {
      console.error('Error executing signals:', error);
      toast.error(error?.response?.data?.detail || 'Failed to execute signals');
    } finally {
      setIsExecuting(false);
    }
  };

  const fetchPortfolioHoldings = async () => {
    try {
      const response = await httpClient.get('/api/realtime-trading/portfolio-holdings');
      if (response.success) {
        setPortfolioHoldings((response.data as any).holdings || []);
      }
    } catch (error) {
      console.error('Error fetching portfolio holdings:', error);
    }
  };

  const fetchSignalAccuracy = async () => {
    try {
      const response = await httpClient.get('/api/realtime-trading/signal-accuracy');
      if (response.success) {
        setSignalAccuracy(response.data as SignalAccuracy);
      }
    } catch (error) {
      console.error('Error fetching signal accuracy:', error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Real-time Trading Execution
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  Auto-execute Nifty 50 signals and manage portfolio
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                settings.paperTrading 
                  ? 'bg-yellow-100 text-yellow-800' 
                  : 'bg-green-100 text-green-800'
              }`}>
                {settings.paperTrading ? 'Paper Trading' : 'Live Trading'}
              </span>
            </div>
          </div>
        </div>

        {/* Control Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Execution Settings
              </h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Timeframe
                </label>
                <select
                  value={settings.timeframe}
                  onChange={(e) => setSettings({...settings, timeframe: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="1m">1 Minute</option>
                  <option value="5m">5 Minutes</option>
                  <option value="15m">15 Minutes</option>
                  <option value="1h">1 Hour</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Max Trades
                </label>
                <input
                  type="number"
                  value={settings.maxTrades}
                  onChange={(e) => setSettings({...settings, maxTrades: parseInt(e.target.value)})}
                  min="1"
                  max="20"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Min Confidence
                </label>
                <input
                  type="number"
                  value={settings.minConfidence}
                  onChange={(e) => setSettings({...settings, minConfidence: parseFloat(e.target.value)})}
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="paperTrading"
                  checked={settings.paperTrading}
                  onChange={(e) => setSettings({...settings, paperTrading: e.target.checked})}
                  className="mr-2"
                />
                <label htmlFor="paperTrading" className="text-sm text-gray-700 dark:text-gray-300">
                  Paper Trading Mode
                </label>
              </div>
            </div>
            
            <button
              onClick={executeSignals}
              disabled={isExecuting}
              className="w-full mt-6 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isExecuting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Execute Signals
                </>
              )}
            </button>
          </div>

          {/* Signal Accuracy */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Signal Accuracy
              </h2>
            </div>
            
            {signalAccuracy ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total Trades</span>
                  <span className="font-medium">{signalAccuracy.total_trades}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Win Rate</span>
                  <span className={`font-medium ${signalAccuracy.win_rate >= 60 ? 'text-green-600' : 'text-red-600'}`}>
                    {signalAccuracy.win_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total P&L</span>
                  <span className={`font-medium ${signalAccuracy.total_pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(signalAccuracy.total_pnl_percent)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Accuracy Score</span>
                  <span className="font-medium text-blue-600">
                    {signalAccuracy.accuracy_score.toFixed(2)}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <AlertCircle className="w-8 h-8 mx-auto mb-2" />
                <p>No accuracy data available</p>
              </div>
            )}
          </div>

          {/* Portfolio Summary */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <DollarSign className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Portfolio Summary
              </h2>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Holdings</span>
                <span className="font-medium">{portfolioHoldings.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total Value</span>
                <span className="font-medium">
                  {formatCurrency(portfolioHoldings.reduce((sum, h) => sum + h.total_value, 0))}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total P&L</span>
                <span className={`font-medium ${
                  portfolioHoldings.reduce((sum, h) => sum + h.pnl, 0) >= 0 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {formatCurrency(portfolioHoldings.reduce((sum, h) => sum + h.pnl, 0))}
                </span>
              </div>
            </div>
            
            <button
              onClick={fetchPortfolioHoldings}
              className="w-full mt-4 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Execution Results */}
        {executionResults.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Last Execution Results
              </h2>
              <span className="text-sm text-gray-500">
                {lastExecution ? new Date(lastExecution).toLocaleString() : ''}
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {executionResults.map((result, index) => (
                <div
                  key={index}
                  className={`border rounded-lg p-4 ${
                    result.execution_result.success
                      ? 'border-green-200 bg-green-50'
                      : 'border-red-200 bg-red-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{result.symbol}</span>
                    {result.execution_result.success ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-600" />
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    <div>Signal: {result.signal_type}</div>
                    <div>Confidence: {(result.confidence * 100).toFixed(1)}%</div>
                    {result.execution_result.order_id && (
                      <div>Order ID: {result.execution_result.order_id}</div>
                    )}
                    {result.execution_result.error && (
                      <div className="text-red-600 text-xs mt-1">
                        {result.execution_result.error}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Portfolio Holdings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Portfolio Holdings
            </h2>
            <button
              onClick={fetchPortfolioHoldings}
              className="text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <Eye className="w-4 h-4" />
              View in Portfolio
            </button>
          </div>
          
          {portfolioHoldings.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b dark:border-gray-700">
                    <th className="text-left py-2 px-4">Symbol</th>
                    <th className="text-right py-2 px-4">Quantity</th>
                    <th className="text-right py-2 px-4">Avg Price</th>
                    <th className="text-right py-2 px-4">Current Price</th>
                    <th className="text-right py-2 px-4">Total Value</th>
                    <th className="text-right py-2 px-4">P&L</th>
                    <th className="text-right py-2 px-4">P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolioHoldings.map((holding, index) => (
                    <tr key={index} className="border-b dark:border-gray-700">
                      <td className="py-2 px-4 font-medium">{holding.symbol}</td>
                      <td className="text-right py-2 px-4">{holding.quantity}</td>
                      <td className="text-right py-2 px-4">{formatCurrency(holding.avg_price)}</td>
                      <td className="text-right py-2 px-4">{formatCurrency(holding.current_price)}</td>
                      <td className="text-right py-2 px-4">{formatCurrency(holding.total_value)}</td>
                      <td className={`text-right py-2 px-4 ${holding.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(holding.pnl)}
                      </td>
                      <td className={`text-right py-2 px-4 ${holding.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(holding.pnl_percent)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <Clock className="w-8 h-8 mx-auto mb-2" />
              <p>No holdings available</p>
              <p className="text-sm">Execute signals to build your portfolio</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RealtimeTrading;
