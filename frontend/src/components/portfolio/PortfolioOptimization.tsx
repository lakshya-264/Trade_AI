/**
 * Portfolio Optimization Component
 * Modern Portfolio Theory (MPT) based optimization
 */

import React, { useState, useEffect } from 'react';
import { httpClient } from '../../config/api';
import { toast } from 'react-hot-toast';
import { 
  TrendingUp, TrendingDown, BarChart3, Target, 
  RefreshCw, Calculator, PieChart, ArrowRight,
  CheckCircle, XCircle, AlertCircle
} from 'lucide-react';

interface OptimizationResult {
  weights: number[];
  symbols: string[];
  metrics: {
    return: number;
    volatility: number;
    sharpe_ratio: number;
  };
  optimization_type: string;
  success: boolean;
}

interface EfficientFrontierPoint {
  return: number;
  volatility: number;
  sharpe_ratio: number;
}

interface RebalancingAction {
  symbol: string;
  current_weight: number;
  target_weight: number;
  current_value: number;
  target_value: number;
  action: 'BUY' | 'SELL';
  action_value: number;
  action_percent: number;
}

const PortfolioOptimization: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [newSymbol, setNewSymbol] = useState('');
  const [optimizationType, setOptimizationType] = useState('max_sharpe');
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [efficientFrontier, setEfficientFrontier] = useState<EfficientFrontierPoint[]>([]);
  const [rebalancingActions, setRebalancingActions] = useState<RebalancingAction[]>([]);
  const [currentHoldings, setCurrentHoldings] = useState<any[]>([]);
  const [maxWeight, setMaxWeight] = useState(0.4); // 40% max per stock

  useEffect(() => {
    loadCurrentHoldings();
  }, []);

  const loadCurrentHoldings = async () => {
    try {
      const response = await httpClient.get('/api/portfolio-allocation/holdings') as any;
      if (response.data?.success) {
        const holdings = response.data.data?.holdings || [];
        setCurrentHoldings(holdings);
        // Pre-populate symbols from holdings
        if (holdings.length > 0) {
          setSymbols(holdings.map((h: any) => h.symbol));
        }
      }
    } catch (error) {
      console.error('Failed to load holdings:', error);
    }
  };

  const addSymbol = () => {
    if (newSymbol.trim() && !symbols.includes(newSymbol.trim().toUpperCase())) {
      setSymbols([...symbols, newSymbol.trim().toUpperCase()]);
      setNewSymbol('');
    }
  };

  const removeSymbol = (symbol: string) => {
    setSymbols(symbols.filter(s => s !== symbol));
  };

  const optimizePortfolio = async () => {
    if (symbols.length < 2) {
      toast.error('Please add at least 2 symbols for optimization');
      return;
    }

    setOptimizing(true);
    try {
      const response = await httpClient.post('/api/portfolio-allocation/optimize-portfolio', {
        symbols,
        optimization_type: optimizationType,
        constraints: {
          max_weight: maxWeight
        },
        days: 252
      }) as any;

      if (response.data?.success) {
        setOptimizationResult(response.data.optimization);
        setEfficientFrontier(response.data.efficient_frontier || []);
        toast.success('Portfolio optimized successfully!');
      } else {
        toast.error('Optimization failed');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to optimize portfolio');
    } finally {
      setOptimizing(false);
    }
  };

  const calculateRebalancing = async () => {
    if (currentHoldings.length === 0) {
      toast.error('No holdings found. Please add holdings first.');
      return;
    }

    setLoading(true);
    try {
      const response = await httpClient.post('/api/portfolio-allocation/rebalance-portfolio', {
        optimization_type: optimizationType
      }) as any;

      if (response.data?.success) {
        setRebalancingActions(response.data.rebalancing_actions || []);
        setOptimizationResult({
          weights: Object.values(response.data.target_allocation),
          symbols: Object.keys(response.data.target_allocation),
          metrics: response.data.optimization_metrics,
          optimization_type: optimizationType,
          success: true
        });
        toast.success('Rebalancing calculated!');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to calculate rebalancing');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-semibold flex items-center gap-2">
              <Target className="w-6 h-6 text-blue-500" />
              Portfolio Optimization
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Optimize your portfolio using Modern Portfolio Theory (MPT)
            </p>
          </div>
        </div>

        {/* Symbol Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Select Symbols</label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
              placeholder="Enter symbol (e.g., RELIANCE)"
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
            />
            <button
              onClick={addSymbol}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {symbols.map((symbol) => (
              <span
                key={symbol}
                className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full flex items-center gap-2"
              >
                {symbol}
                <button
                  onClick={() => removeSymbol(symbol)}
                  className="hover:text-red-600"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Optimization Settings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium mb-2">Optimization Strategy</label>
            <select
              value={optimizationType}
              onChange={(e) => setOptimizationType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
            >
              <option value="max_sharpe">Maximize Sharpe Ratio</option>
              <option value="min_volatility">Minimize Volatility</option>
              <option value="max_return">Maximize Return</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">
              Max Weight per Stock: {(maxWeight * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.05"
              value={maxWeight}
              onChange={(e) => setMaxWeight(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={optimizePortfolio}
            disabled={optimizing || symbols.length < 2}
            className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {optimizing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Optimizing...
              </>
            ) : (
              <>
                <Calculator className="w-4 h-4" />
                Optimize Portfolio
              </>
            )}
          </button>
          <button
            onClick={calculateRebalancing}
            disabled={loading || currentHoldings.length === 0}
            className="flex-1 px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Calculating...
              </>
            ) : (
              <>
                <BarChart3 className="w-4 h-4" />
                Rebalance Portfolio
              </>
            )}
          </button>
        </div>
      </div>

      {/* Optimization Results */}
      {optimizationResult && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Optimization Results
          </h4>

          {/* Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <div className="text-sm text-gray-600 dark:text-gray-400">Expected Return</div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {(optimizationResult.metrics.return * 100).toFixed(2)}%
              </div>
            </div>
            <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
              <div className="text-sm text-gray-600 dark:text-gray-400">Volatility</div>
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {(optimizationResult.metrics.volatility * 100).toFixed(2)}%
              </div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
              <div className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {optimizationResult.metrics.sharpe_ratio.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Optimal Allocation */}
          <div className="mb-6">
            <h5 className="font-semibold mb-3">Optimal Allocation</h5>
            <div className="space-y-2">
              {optimizationResult.symbols.map((symbol, index) => {
                const weight = optimizationResult.weights[index];
                return (
                  <div key={symbol} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex justify-between mb-1">
                        <span className="font-medium">{symbol}</span>
                        <span className="text-gray-600 dark:text-gray-400">
                          {(weight * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${weight * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Rebalancing Actions */}
      {rebalancingActions.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-500" />
            Rebalancing Actions Required
          </h4>
          <div className="space-y-3">
            {rebalancingActions.map((action, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex-1">
                  <div className="font-medium">{action.symbol}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Current: {(action.current_weight * 100).toFixed(2)}% → Target: {(action.target_weight * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-semibold ${action.action === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                    {action.action} ₹{action.action_value.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {action.action_percent.toFixed(2)}% change
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Efficient Frontier Chart Placeholder */}
      {efficientFrontier.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h4 className="text-lg font-semibold mb-4">Efficient Frontier</h4>
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400">
              Efficient Frontier visualization (Chart integration coming soon)
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioOptimization;

