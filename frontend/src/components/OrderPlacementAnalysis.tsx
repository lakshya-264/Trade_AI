/**
 * Order Placement and Duration Analysis Component
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, Clock, Target, Shield, AlertTriangle,
  Calculator, BarChart3, Activity, Zap, Info, Eye, RefreshCw,
  CheckCircle, XCircle, Timer, DollarSign, Percent, Award,
  TrendingUp as TrendingUpIcon, TrendingDown as TrendingDownIcon
} from 'lucide-react';
import { httpClient, APIResponse } from '../config/api';
import { toast } from 'react-hot-toast';

interface OrderMetrics {
  total_value: number;
  potential_profit: number;
  potential_loss: number;
  risk_reward_ratio: number;
  order_quality_score: number;
  risk_per_share: number;
  profit_per_share: number;
  position_size_score: number;
  liquidity_score: number;
}

interface PlacementAnalysis {
  timing_analysis: {
    timing_score: number;
    session: string;
    session_score: number;
    day_score: number;
  };
  size_analysis: {
    size_score: number;
    size_percentile: number;
    current_value: number;
    avg_value: number;
  };
  risk_analysis: {
    rr_score: number;
    risk_reward_ratio: number;
    risk_percentage: number;
    rr_grade: string;
  };
  recommendations: string[];
  overall_score: number;
}

interface DurationPerformance {
  trade_count: number;
  win_rate: number;
  avg_return: number;
  total_return: number;
  avg_holding_period: number;
  performance_score: number;
  benchmark_comparison: {
    meets_win_rate_target: boolean;
    meets_return_target: boolean;
  };
}

interface DurationAnalysis {
  total_trades: number;
  duration_metrics: {
    avg_holding_period: number;
    median_holding_period: number;
    distribution: Record<string, number>;
  };
  performance_by_duration: Record<string, DurationPerformance>;
  optimal_duration: {
    duration: string;
    score: number;
    recommendation: string;
  };
  holding_patterns: {
    holding_return_correlation: number;
    correlation_interpretation: string;
  };
}

export const OrderPlacementAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'placement' | 'duration' | 'simulation'>('placement');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Order placement state
  const [orderData, setOrderData] = useState({
    symbol: '',
    order_type: 'MARKET',
    action: 'BUY',
    quantity: 1,
    price: 0,
    target_price: 0,
    stop_loss: 0,
    signal_strength: 'MODERATE',
    confidence_score: 0.5,
    duration: 'INTRADAY'
  });
  
  const [orderMetrics, setOrderMetrics] = useState<OrderMetrics | null>(null);
  const [placementAnalysis, setPlacementAnalysis] = useState<PlacementAnalysis | null>(null);
  
  // Duration analysis state
  const [durationAnalysis, setDurationAnalysis] = useState<DurationAnalysis | null>(null);
  const [analysisDays, setAnalysisDays] = useState(30);
  
  // Simulation state
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [showSimulation, setShowSimulation] = useState(false);

  // Fetch order types and signal strengths on mount
  useEffect(() => {
    fetchOrderTypes();
    fetchSignalStrengths();
    fetchDurations();
  }, []);

  const fetchOrderTypes = async () => {
    try {
      const response = await httpClient.get('/api/v1/order-placement/order-types');
      console.log('Order types:', response.data);
    } catch (err) {
      console.error('Failed to fetch order types');
    }
  };

  const fetchSignalStrengths = async () => {
    try {
      const response = await httpClient.get('/api/v1/order-placement/signal-strengths');
      console.log('Signal strengths:', response.data);
    } catch (err) {
      console.error('Failed to fetch signal strengths');
    }
  };

  const fetchDurations = async () => {
    try {
      const response = await httpClient.get('/api/v1/order-placement/durations');
      console.log('Durations:', response.data);
    } catch (err) {
      console.error('Failed to fetch durations');
    }
  };

  const calculateOrderMetrics = async () => {
    if (!orderData.symbol || !orderData.price || !orderData.quantity) {
      toast.error('Please fill in basic order details');
      return;
    }

    try {
      setLoading(true);
      const response = await httpClient.get('/api/v1/order-placement/calculate-metrics', {
        params: {
          symbol: orderData.symbol,
          order_type: orderData.order_type,
          action: orderData.action,
          quantity: orderData.quantity,
          price: orderData.price,
          target_price: orderData.target_price || undefined,
          stop_loss: orderData.stop_loss || undefined,
          signal_strength: orderData.signal_strength,
          confidence_score: orderData.confidence_score
        }
      });

      if (response.success) {
        setOrderMetrics(response.data as OrderMetrics);
        toast.success('Order metrics calculated');
      }
    } catch (err) {
      toast.error('Failed to calculate order metrics');
    } finally {
      setLoading(false);
    }
  };

  const validateOrder = async () => {
    try {
      const response = await httpClient.get('/api/v1/order-placement/validate', {
        params: {
          symbol: orderData.symbol,
          order_type: orderData.order_type,
          action: orderData.action,
          quantity: orderData.quantity,
          price: orderData.price,
          target_price: orderData.target_price || undefined,
          stop_loss: orderData.stop_loss || undefined
        }
      });

      if (response.success && (response.data as any).is_valid) {
        toast.success('Order parameters are valid');
      } else {
        toast.error(`Invalid: ${(response.data as any).reason}`);
      }
    } catch (err) {
      toast.error('Validation failed');
    }
  };

  const simulateOrder = async () => {
    try {
      setLoading(true);
      const response = await httpClient.post('/api/v1/order-placement/simulate-order', orderData);

      if (response.success) {
        setSimulationResult(response.data);
        setShowSimulation(true);
        toast.success('Order simulation completed');
      }
    } catch (err) {
      toast.error('Order simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const fetchDurationAnalysis = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/v1/order-placement/duration-analysis', {
        params: { days: analysisDays }
      });

      if (response.success) {
        setDurationAnalysis(response.data as DurationAnalysis);
      }
    } catch (err) {
      toast.error('Failed to fetch duration analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'duration') {
      fetchDurationAnalysis();
    }
  }, [activeTab, analysisDays]);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-blue-600 bg-blue-50';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatCurrency = (value: number) => {
    return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Order Placement & Duration Analysis</h2>
        <div className="flex items-center gap-4">
          {activeTab === 'duration' && (
            <select
              value={analysisDays}
              onChange={(e) => setAnalysisDays(Number(e.target.value))}
              className="px-3 py-2 border rounded-md"
            >
              <option value={7}>7 Days</option>
              <option value={30}>30 Days</option>
              <option value={90}>90 Days</option>
            </select>
          )}
          <button
            onClick={() => {
              if (activeTab === 'placement') calculateOrderMetrics();
              else if (activeTab === 'duration') fetchDurationAnalysis();
            }}
            className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        <button
          onClick={() => setActiveTab('placement')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'placement'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Order Placement
        </button>
        <button
          onClick={() => setActiveTab('duration')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'duration'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Duration Analysis
        </button>
        <button
          onClick={() => setActiveTab('simulation')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'simulation'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Order Simulation
        </button>
      </div>

      {activeTab === 'placement' && (
        <div className="space-y-6">
          {/* Order Form */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Order Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
                <input
                  type="text"
                  value={orderData.symbol}
                  onChange={(e) => setOrderData({...orderData, symbol: e.target.value.toUpperCase()})}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="e.g., RELIANCE"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Order Type</label>
                <select
                  value={orderData.order_type}
                  onChange={(e) => setOrderData({...orderData, order_type: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="MARKET">Market</option>
                  <option value="LIMIT">Limit</option>
                  <option value="STOP_LOSS">Stop Loss</option>
                  <option value="STOP_LIMIT">Stop Limit</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
                <select
                  value={orderData.action}
                  onChange={(e) => setOrderData({...orderData, action: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                <input
                  type="number"
                  value={orderData.quantity}
                  onChange={(e) => setOrderData({...orderData, quantity: Number(e.target.value)})}
                  className="w-full px-3 py-2 border rounded-md"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
                <input
                  type="number"
                  value={orderData.price}
                  onChange={(e) => setOrderData({...orderData, price: Number(e.target.value)})}
                  className="w-full px-3 py-2 border rounded-md"
                  step="0.01"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Signal Strength</label>
                <select
                  value={orderData.signal_strength}
                  onChange={(e) => setOrderData({...orderData, signal_strength: e.target.value})}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="WEAK">Weak</option>
                  <option value="MODERATE">Moderate</option>
                  <option value="STRONG">Strong</option>
                  <option value="VERY_STRONG">Very Strong</option>
                </select>
              </div>
              {(orderData.order_type === 'LIMIT' || orderData.order_type === 'STOP_LIMIT') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Target Price</label>
                  <input
                    type="number"
                    value={orderData.target_price}
                    onChange={(e) => setOrderData({...orderData, target_price: Number(e.target.value)})}
                    className="w-full px-3 py-2 border rounded-md"
                    step="0.01"
                    min="0"
                  />
                </div>
              )}
              {(orderData.order_type === 'STOP_LOSS' || orderData.order_type === 'STOP_LIMIT') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Stop Loss</label>
                  <input
                    type="number"
                    value={orderData.stop_loss}
                    onChange={(e) => setOrderData({...orderData, stop_loss: Number(e.target.value)})}
                    className="w-full px-3 py-2 border rounded-md"
                    step="0.01"
                    min="0"
                  />
                </div>
              )}
            </div>
            <div className="flex gap-4 mt-4">
              <button
                onClick={calculateOrderMetrics}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <Calculator className="w-4 h-4 inline mr-2" />
                Calculate Metrics
              </button>
              <button
                onClick={validateOrder}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <CheckCircle className="w-4 h-4 inline mr-2" />
                Validate Order
              </button>
            </div>
          </div>

          {/* Order Metrics */}
          {orderMetrics && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-blue-800 mb-3">Order Metrics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-blue-600">Total Value</div>
                  <div className="text-lg font-bold text-blue-800">
                    {formatCurrency(orderMetrics.total_value)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-blue-600">Risk/Reward Ratio</div>
                  <div className="text-lg font-bold text-blue-800">
                    {orderMetrics.risk_reward_ratio.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-blue-600">Order Quality Score</div>
                  <div className="text-lg font-bold text-blue-800">
                    {orderMetrics.order_quality_score.toFixed(1)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-blue-600">Liquidity Score</div>
                  <div className="text-lg font-bold text-blue-800">
                    {orderMetrics.liquidity_score.toFixed(1)}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                <div>
                  <div className="text-sm text-blue-600">Potential Profit</div>
                  <div className="text-lg font-bold text-green-600">
                    {formatCurrency(orderMetrics.potential_profit)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-blue-600">Potential Loss</div>
                  <div className="text-lg font-bold text-red-600">
                    {formatCurrency(orderMetrics.potential_loss)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-blue-600">Risk per Share</div>
                  <div className="text-lg font-bold text-orange-600">
                    {formatCurrency(orderMetrics.risk_per_share)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'duration' && (
        <div className="space-y-6">
          {durationAnalysis && (
            <>
              {/* Duration Metrics */}
              <div className="bg-purple-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-purple-800 mb-3">Holding Period Analysis</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-purple-600">Total Trades</div>
                    <div className="text-lg font-bold text-purple-800">
                      {durationAnalysis.total_trades}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-purple-600">Avg Holding Period</div>
                    <div className="text-lg font-bold text-purple-800">
                      {durationAnalysis.duration_metrics.avg_holding_period.toFixed(1)} hrs
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-purple-600">Median Holding Period</div>
                    <div className="text-lg font-bold text-purple-800">
                      {durationAnalysis.duration_metrics.median_holding_period.toFixed(1)} hrs
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-purple-600">Return Correlation</div>
                    <div className="text-lg font-bold text-purple-800">
                      {durationAnalysis.holding_patterns.holding_return_correlation.toFixed(3)}
                    </div>
                  </div>
                </div>
                <div className="mt-3 text-sm text-purple-700">
                  {durationAnalysis.holding_patterns.correlation_interpretation}
                </div>
              </div>

              {/* Performance by Duration */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Performance by Duration</h3>
                <div className="space-y-3">
                  {Object.entries(durationAnalysis.performance_by_duration).map(([duration, perf]) => (
                    <div key={duration} className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-semibold text-gray-800">{duration}</h4>
                          <div className="text-sm text-gray-600 mt-1">
                            {perf.trade_count} trades • {perf.avg_holding_period.toFixed(1)} hrs avg
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`text-lg font-bold ${getScoreColor(perf.performance_score).split(' ')[0]}`}>
                            {perf.performance_score.toFixed(1)}
                          </div>
                          <div className="text-sm text-gray-600">
                            Win Rate: {(perf.win_rate * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-4 mt-3">
                        <div>
                          <div className="text-sm text-gray-600">Avg Return</div>
                          <div className={`font-medium ${perf.avg_return > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatPercentage(perf.avg_return)}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Total Return</div>
                          <div className={`font-medium ${perf.total_return > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatPercentage(perf.total_return)}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Targets Met</div>
                          <div className="font-medium">
                            {perf.benchmark_comparison.meets_win_rate_target ? '✅' : '❌'} WR / 
                            {perf.benchmark_comparison.meets_return_target ? '✅' : '❌'} RT
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Optimal Duration */}
              {durationAnalysis.optimal_duration && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-green-800 mb-2">Optimal Duration Recommendation</h3>
                  <div className="flex items-center gap-3">
                    <Award className="w-6 h-6 text-green-600" />
                    <div>
                      <div className="text-lg font-bold text-green-800">
                        {durationAnalysis.optimal_duration.duration}
                      </div>
                      <div className="text-sm text-green-700">
                        Score: {durationAnalysis.optimal_duration.score.toFixed(1)}/100
                      </div>
                      <div className="text-sm text-green-600 mt-1">
                        {durationAnalysis.optimal_duration.recommendation}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'simulation' && (
        <div className="space-y-6">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Order Simulation</h3>
            <p className="text-sm text-gray-600 mb-4">
              Test your order parameters before placing the actual order
            </p>
            <button
              onClick={simulateOrder}
              disabled={loading || !orderData.symbol || !orderData.price}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
            >
              <Activity className="w-4 h-4 inline mr-2" />
              Simulate Order
            </button>
          </div>

          {showSimulation && simulationResult && (
            <div className="space-y-4">
              {/* Validation Result */}
              <div className={`p-4 rounded-lg ${
                simulationResult.validation.is_valid ? 'bg-green-50' : 'bg-red-50'
              }`}>
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  {simulationResult.validation.is_valid ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600" />
                  )}
                  Order Validation
                </h4>
                <p className={`text-sm ${
                  simulationResult.validation.is_valid ? 'text-green-700' : 'text-red-700'
                }`}>
                  {simulationResult.validation.reason}
                </p>
              </div>

              {/* Simulation Metrics */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-blue-800 mb-3">Simulation Results</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-blue-600">Timing Score</div>
                    <div className="text-lg font-bold text-blue-800">
                      {simulationResult.timing_analysis.timing_score.toFixed(1)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-blue-600">Size Score</div>
                    <div className="text-lg font-bold text-blue-800">
                      {simulationResult.size_analysis.size_score.toFixed(1)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-blue-600">Risk Score</div>
                    <div className="text-lg font-bold text-blue-800">
                      {simulationResult.risk_analysis.rr_score.toFixed(1)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-blue-600">Overall Score</div>
                    <div className="text-lg font-bold text-blue-800">
                      {simulationResult.overall_score.toFixed(1)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              {simulationResult.recommendations.length > 0 && (
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-yellow-800 mb-2">Recommendations</h4>
                  <ul className="space-y-1">
                    {simulationResult.recommendations.map((rec: string, index: number) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-yellow-700">
                        <Info className="w-4 h-4 mt-0.5" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
