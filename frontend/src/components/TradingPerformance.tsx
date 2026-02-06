/**
 * Enhanced Trading Performance Component
 * Integrates with the new trading performance API for P&L analysis
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, BarChart3, Target, AlertTriangle,
  ArrowUpRight, ArrowDownRight, Minus, Calculator, Activity,
  Clock, DollarSign, TrendingUpIcon, Shield, Zap, Award,
  Info, Calendar, Filter, Download, RefreshCw, Eye
} from 'lucide-react';
import { httpClient, API_CONFIG, APIResponse } from '../config/api';
import { toast } from 'react-hot-toast';

interface PerformanceMetrics {
  total_trades: number;
  win_rate: number;
  total_pnl_percent: number;
  profitable_trades: number;
  losing_trades: number;
  avg_profit_percent: number;
  avg_loss_percent: number;
  max_profit_percent: number;
  max_loss_percent: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  volatility?: number;
  avg_holding_period?: number;
}

interface EntryExitAnalysis {
  total_closed_trades: number;
  exits_higher_than_entry: number;
  exits_lower_than_entry: number;
  exits_equal_to_entry: number;
  profitable_exit_rate: number;
  loss_exit_rate: number;
  breakeven_rate: number;
  price_statistics: {
    avg_price_change_percent: number;
    max_profit_percent: number;
    max_loss_percent: number;
  };
  time_analysis?: {
    avg_holding_period_hours: number;
    shortest_trade_hours: number;
    longest_trade_hours: number;
  };
  pattern_analysis?: {
    consecutive_wins: number;
    consecutive_losses: number;
    best_day_performance: number;
    worst_day_performance: number;
  };
}

interface TradingPerformanceProps {
  symbol: string;
  className?: string;
  showAdvanced?: boolean;
  timeRange?: number;
}

export const TradingPerformance: React.FC<TradingPerformanceProps> = ({ 
  symbol, 
  className = "",
  showAdvanced = false,
  timeRange = 30
}) => {
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [entryExitAnalysis, setEntryExitAnalysis] = useState<EntryExitAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [showDetails, setShowDetails] = useState(false);
  const [debugError, setDebugError] = useState<string | null>(null);

  useEffect(() => {
    fetchPerformanceData();
  }, [symbol]);

  const fetchPerformanceData = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log('Fetching performance data for symbol:', symbol);
      
      // First test if backend is reachable at all
      console.log('Testing backend connectivity...');
      try {
        const healthResponse = await fetch('http://127.0.0.1:8000/', {
          method: 'GET',
          mode: 'cors'
        });
        console.log('Backend health check status:', healthResponse.status);
      } catch (healthErr: any) {
        console.error('Backend not reachable:', healthErr);
        setDebugError(`Backend not reachable: ${healthErr?.message || healthErr}`);
        setError('Backend server not accessible');
        setLoading(false);
        return;
      }

      // Test direct fetch first to bypass any httpClient issues
      console.log('Testing direct fetch...');
      const directUrl = `http://127.0.0.1:8000/api/v1/trading/performance/symbol/${symbol}/summary`;
      
      try {
        console.log('Attempting direct fetch to:', directUrl);
        const directResponse = await fetch(directUrl, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          mode: 'cors' // Explicitly set CORS mode
        });
        
        console.log('Direct fetch status:', directResponse.status);
        console.log('Direct fetch headers:', directResponse.headers);
        
        if (!directResponse.ok) {
          throw new Error(`HTTP ${directResponse.status}: ${directResponse.statusText}`);
        }
        
        const directData = await directResponse.json();
        console.log('Direct fetch data:', directData);
        
        if (directData.success) {
          const metrics = directData.data?.performance_metrics || {};
          console.log('Setting performance from direct fetch:', metrics);
          setPerformance(metrics);
          setError(null); // Clear any existing error
          setDebugError(null); // Clear debug error
          
          // Also fetch analysis data
          const analysisUrl = `http://127.0.0.1:8000/api/v1/trading/performance/analysis/entry-exit/${symbol}`;
          const analysisResponse = await fetch(analysisUrl, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            mode: 'cors'
          });
          
          if (analysisResponse.ok) {
            const analysisData = await analysisResponse.json();
            console.log('Analysis data:', analysisData);
            if (analysisData.success) {
              setEntryExitAnalysis(analysisData.data);
            }
          }
        }
      } catch (directErr: any) {
        console.error('Direct fetch failed:', directErr);
        console.error('Error details:', directErr?.message || directErr);
        setDebugError(`Direct fetch failed: ${directErr?.message || directErr}`);
        
        // Fallback to httpClient
        console.log('Falling back to httpClient...');
        
        // Fetch performance summary (try Nifty50 performance first)
        let performanceResponse: APIResponse<any>;
        try {
          performanceResponse = await httpClient.get(
            `${API_CONFIG.NIFTY50_PERFORMANCE}/symbol/${symbol}/summary`
          );
        } catch (error) {
          console.log('Nifty50 performance failed, trying general performance...');
          performanceResponse = await httpClient.get(
            `${API_CONFIG.TRADING_PERFORMANCE}/symbol/${symbol}/summary`
          );
        }
        
        console.log('Performance response:', performanceResponse);

        // Fetch entry/exit analysis (try Nifty50 performance first)
        let analysisResponse: APIResponse<any>;
        try {
          analysisResponse = await httpClient.get(
            `${API_CONFIG.NIFTY50_PERFORMANCE}/symbol/${symbol}/entry-exit`
          );
        } catch (error) {
          console.log('Nifty50 entry-exit failed, trying general performance...');
          analysisResponse = await httpClient.get(
            `${API_CONFIG.TRADING_PERFORMANCE}/analysis/entry-exit/${symbol}`
          );
        }
        
        console.log('Analysis response:', analysisResponse);

        if (performanceResponse.success) {
          console.log('Setting performance data:', performanceResponse.data?.performance_metrics);
          const metrics = performanceResponse.data?.performance_metrics || {};
          console.log('Metrics object:', metrics);
          console.log('Metrics keys:', Object.keys(metrics));
          setPerformance(metrics);
          setError(null); // Clear any existing error
          setDebugError(null); // Clear debug error
        } else {
          console.error('Performance API failed:', performanceResponse);
          setError('Performance data unavailable');
        }

        if (analysisResponse.success) {
          console.log('Setting analysis data:', analysisResponse.data);
          setEntryExitAnalysis(analysisResponse.data);
        } else {
          console.error('Analysis API failed:', analysisResponse);
          setError('Analysis data unavailable');
        }
      }

    } catch (err) {
      console.error('Failed to fetch performance data:', err);
      setError('Failed to load performance data');
      toast.error('Could not load trading performance data');
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '0.00%';
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getPerformanceColor = (value: number | null | undefined): string => {
    if (!value) return 'text-gray-600';
    return value >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getPerformanceIcon = (value: number | null | undefined) => {
    if (!value) return <Minus className="w-4 h-4" />;
    if (value > 0) return <ArrowUpRight className="w-4 h-4 text-green-600" />;
    if (value < 0) return <ArrowDownRight className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-600" />;
  };

  // Performance grading functions
  const getPerformanceGrade = (performance: PerformanceMetrics): string => {
    const score = calculatePerformanceScore(performance);
    if (score >= 90) return 'A+';
    if (score >= 85) return 'A';
    if (score >= 80) return 'A-';
    if (score >= 75) return 'B+';
    if (score >= 70) return 'B';
    if (score >= 65) return 'B-';
    if (score >= 60) return 'C+';
    if (score >= 55) return 'C';
    if (score >= 50) return 'C-';
    return 'D';
  };

  const calculatePerformanceScore = (performance: PerformanceMetrics): number => {
    let score = 0;
    
    // Win rate (40% weight)
    score += performance.win_rate * 0.4;
    
    // Total P&L (30% weight)
    score += Math.max(0, Math.min(100, 50 + performance.total_pnl_percent)) * 0.3;
    
    // Risk-adjusted returns (20% weight)
    if (performance.sharpe_ratio) {
      score += Math.max(0, Math.min(100, 50 + performance.sharpe_ratio * 10)) * 0.2;
    } else {
      score += 50 * 0.2; // Default if no Sharpe ratio
    }
    
    // Trade frequency (10% weight)
    const tradeFrequency = Math.min(100, performance.total_trades / 30 * 100); // Normalize to 30 days
    score += tradeFrequency * 0.1;
    
    return Math.round(score);
  };

  const getPerformanceDescription = (performance: PerformanceMetrics): string => {
    const score = calculatePerformanceScore(performance);
    if (score >= 85) return 'Exceptional performance with excellent risk management';
    if (score >= 75) return 'Strong performance with good risk-adjusted returns';
    if (score >= 65) return 'Above average performance with room for improvement';
    if (score >= 55) return 'Average performance, consider strategy review';
    return 'Below average performance, strategy adjustment needed';
  };

  const getGradeIcon = (performance: PerformanceMetrics) => {
    const score = calculatePerformanceScore(performance);
    if (score >= 85) return <Award className="w-8 h-8 text-yellow-500" />;
    if (score >= 70) return <TrendingUp className="w-8 h-8 text-green-500" />;
    if (score >= 55) return <Shield className="w-8 h-8 text-blue-500" />;
    return <AlertTriangle className="w-8 h-8 text-orange-500" />;
  };

  const getRiskAssessment = (performance: PerformanceMetrics): string => {
    if (!performance.max_drawdown) return 'Insufficient data for risk assessment';
    
    const drawdown = Math.abs(performance.max_drawdown);
    if (drawdown < 5) return 'Low risk - Conservative approach with minimal drawdowns';
    if (drawdown < 10) return 'Moderate risk - Balanced risk-reward profile';
    if (drawdown < 20) return 'High risk - Aggressive approach with significant drawdowns';
    return 'Very high risk - Consider reducing position sizes';
  };

  const getRecommendation = (performance: PerformanceMetrics): string => {
    const winRate = performance.win_rate;
    const pnl = performance.total_pnl_percent;
    
    if (winRate >= 60 && pnl >= 10) return 'Continue current strategy with slight position size increase';
    if (winRate >= 50 && pnl >= 5) return 'Maintain current strategy, focus on consistency';
    if (winRate >= 40 && pnl >= 0) return 'Review entry/exit criteria, consider risk management improvements';
    if (winRate < 40 || pnl < -5) return 'Significant strategy revision required, consider reducing position sizes';
    return 'Monitor closely, prepare to adjust strategy based on market conditions';
  };

  const getNextSteps = (performance: PerformanceMetrics): string => {
    const steps = [];
    
    if (performance.win_rate < 50) {
      steps.push('Improve signal accuracy through backtesting');
    }
    
    if (performance.total_pnl_percent < 0) {
      steps.push('Review stop-loss and take-profit levels');
    }
    
    if (!performance.sharpe_ratio || performance.sharpe_ratio < 1) {
      steps.push('Focus on risk-adjusted returns');
    }
    
    if (performance.total_trades < 10) {
      steps.push('Increase trade frequency for better statistical significance');
    }
    
    if (steps.length === 0) {
      steps.push('Continue monitoring and maintaining current performance');
    }
    
    return steps.join(', ');
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !performance) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="flex items-center space-x-2 text-red-600">
          <AlertTriangle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  console.log('TradingPerformance render - performance:', performance);
  console.log('TradingPerformance render - entryExitAnalysis:', entryExitAnalysis);
  console.log('TradingPerformance render - error:', error);

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          Trading Performance - {symbol}
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              console.log('Reset debug state');
              setError(null);
              setDebugError(null);
              setPerformance(null);
              setEntryExitAnalysis(null);
            }}
            className="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Reset
          </button>
          <button
            onClick={() => {
              console.log('Manual test button clicked');
              fetchPerformanceData();
            }}
            className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
          >
            Test API
          </button>
          <button
            onClick={fetchPerformanceData}
            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="Refresh performance data"
          >
            <Activity className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Debug Info */}
      <div className="mb-4 p-3 bg-gray-100 rounded text-xs">
        <div><strong>Debug Info:</strong></div>
        <div>Loading: {loading.toString()}</div>
        <div>Error: {error || 'None'}</div>
        <div>Debug Error: {debugError || 'None'}</div>
        <div>Performance Keys: {performance ? Object.keys(performance).join(', ') : 'None'}</div>
        <div>Performance Win Rate: {performance?.win_rate || 'N/A'}</div>
        <div>EntryExitAnalysis Keys: {entryExitAnalysis ? Object.keys(entryExitAnalysis).join(', ') : 'None'}</div>
      </div>

      {/* Performance Metrics */}
      {performance && Object.keys(performance).length > 0 ? (
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-700 mb-4 flex items-center gap-2">
            <Calculator className="w-4 h-4" />
            Performance Metrics
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-blue-600">
                {performance.total_trades}
              </div>
              <div className="text-xs text-gray-600">Total Trades</div>
            </div>
            
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-600">
                {formatPercentage(performance.win_rate)}
              </div>
              <div className="text-xs text-gray-600">Win Rate</div>
            </div>
            
            <div className={`rounded-lg p-3 ${
              performance.total_pnl_percent >= 0 ? 'bg-green-50' : 'bg-red-50'
            }`}>
              <div className={`text-2xl font-bold flex items-center gap-1 ${
                getPerformanceColor(performance.total_pnl_percent)
              }`}>
                {getPerformanceIcon(performance.total_pnl_percent)}
                {formatPercentage(performance.total_pnl_percent)}
              </div>
              <div className="text-xs text-gray-600">Total P&L</div>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-purple-600">
                {performance.profitable_trades}/{performance.losing_trades}
              </div>
              <div className="text-xs text-gray-600">Profit/Loss Trades</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="mb-6 text-center py-8">
          <div className="text-gray-500">
            <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No performance data available</p>
            <p className="text-sm">Start trading to see performance metrics</p>
          </div>
        </div>
      )}

      {/* Entry/Exit Analysis */}
      {entryExitAnalysis && (
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-700 mb-4 flex items-center gap-2">
            <Target className="w-4 h-4" />
            Entry/Exit Analysis
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-green-800">Profitable Exits</span>
                <TrendingUp className="w-4 h-4 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-green-600">
                {entryExitAnalysis.exits_higher_than_entry}
              </div>
              <div className="text-xs text-gray-700">
                {formatPercentage(entryExitAnalysis.profitable_exit_rate * 100)} of trades
              </div>
            </div>
            
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-red-800">Loss Exits</span>
                <TrendingDown className="w-4 h-4 text-red-600" />
              </div>
              <div className="text-2xl font-bold text-red-600">
                {entryExitAnalysis.exits_lower_than_entry}
              </div>
              <div className="text-xs text-red-700">
                {formatPercentage(entryExitAnalysis.loss_exit_rate)} of trades
              </div>
            </div>
            
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-800">Breakeven</span>
                <Minus className="w-4 h-4 text-gray-600" />
              </div>
              <div className="text-2xl font-bold text-gray-600">
                {entryExitAnalysis.exits_equal_to_entry}
              </div>
              <div className="text-xs text-gray-700">
                {formatPercentage(entryExitAnalysis.breakeven_rate)} of trades
              </div>
            </div>
          </div>

          {/* Price Statistics */}
          {entryExitAnalysis.price_statistics && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="text-sm font-medium text-gray-700 mb-3">Price Statistics</h5>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Avg Change:</span>
                  <span className={`ml-2 font-medium ${getPerformanceColor(entryExitAnalysis.price_statistics.avg_price_change_percent)}`}>
                    {formatPercentage(entryExitAnalysis.price_statistics.avg_price_change_percent)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Max Profit:</span>
                  <span className="ml-2 font-medium text-green-600">
                    {formatPercentage(entryExitAnalysis.price_statistics.max_profit_percent)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Max Loss:</span>
                  <span className="ml-2 font-medium text-red-600">
                    {formatPercentage(entryExitAnalysis.price_statistics.max_loss_percent)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Advanced Metrics */}
      {showAdvanced && performance && (
        <div className="mb-6 border-t pt-6">
          <h4 className="text-md font-medium text-gray-700 mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Advanced Risk Metrics
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-indigo-50 rounded-lg p-3">
              <div className="text-lg font-bold text-indigo-600">
                {performance.sharpe_ratio ? performance.sharpe_ratio.toFixed(2) : 'N/A'}
              </div>
              <div className="text-xs text-gray-600">Sharpe Ratio</div>
            </div>
            
            <div className="bg-orange-50 rounded-lg p-3">
              <div className="text-lg font-bold text-orange-600">
                {performance.max_drawdown ? formatPercentage(performance.max_drawdown) : 'N/A'}
              </div>
              <div className="text-xs text-gray-600">Max Drawdown</div>
            </div>
            
            <div className="bg-teal-50 rounded-lg p-3">
              <div className="text-lg font-bold text-teal-600">
                {performance.volatility ? performance.volatility.toFixed(2) : 'N/A'}
              </div>
              <div className="text-xs text-gray-600">Volatility</div>
            </div>
            
            <div className="bg-pink-50 rounded-lg p-3">
              <div className="text-lg font-bold text-pink-600">
                {performance.avg_holding_period ? `${performance.avg_holding_period.toFixed(1)}h` : 'N/A'}
              </div>
              <div className="text-xs text-gray-600">Avg Holding Period</div>
            </div>
          </div>
        </div>
      )}

      {/* Time Analysis */}
      {entryExitAnalysis?.time_analysis && (
        <div className="mb-6 border-t pt-6">
          <h4 className="text-md font-medium text-gray-700 mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Time Analysis
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-lg font-bold text-blue-600">
                {entryExitAnalysis.time_analysis.avg_holding_period_hours.toFixed(1)}h
              </div>
              <div className="text-xs text-gray-600">Average Holding Time</div>
            </div>
            
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-lg font-bold text-green-600">
                {entryExitAnalysis.time_analysis.shortest_trade_hours.toFixed(1)}h
              </div>
              <div className="text-xs text-gray-600">Shortest Trade</div>
            </div>
            
            <div className="bg-red-50 rounded-lg p-3">
              <div className="text-lg font-bold text-red-600">
                {entryExitAnalysis.time_analysis.longest_trade_hours.toFixed(1)}h
              </div>
              <div className="text-xs text-gray-600">Longest Trade</div>
            </div>
          </div>
        </div>
      )}

      {/* Pattern Analysis */}
      {entryExitAnalysis?.pattern_analysis && (
        <div className="mb-6 border-t pt-6">
          <h4 className="text-md font-medium text-gray-700 mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Pattern Analysis
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-lg font-bold text-green-600">
                {entryExitAnalysis.pattern_analysis.consecutive_wins}
              </div>
              <div className="text-xs text-gray-600">Best Win Streak</div>
            </div>
            
            <div className="bg-red-50 rounded-lg p-3">
              <div className="text-lg font-bold text-red-600">
                {entryExitAnalysis.pattern_analysis.consecutive_losses}
              </div>
              <div className="text-xs text-gray-600">Worst Loss Streak</div>
            </div>
            
            <div className="bg-emerald-50 rounded-lg p-3">
              <div className="text-lg font-bold text-emerald-600">
                {formatPercentage(entryExitAnalysis.pattern_analysis.best_day_performance)}
              </div>
              <div className="text-xs text-gray-600">Best Day</div>
            </div>
            
            <div className="bg-rose-50 rounded-lg p-3">
              <div className="text-lg font-bold text-rose-600">
                {formatPercentage(entryExitAnalysis.pattern_analysis.worst_day_performance)}
              </div>
              <div className="text-xs text-gray-600">Worst Day</div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Grade */}
      {performance && (
        <div className="mb-6 border-t pt-6">
          <h4 className="text-md font-medium text-gray-700 mb-4 flex items-center gap-2">
            <Award className="w-4 h-4" />
            Performance Grade
          </h4>
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600 mb-1">
                  {getPerformanceGrade(performance)}
                </div>
                <div className="text-sm text-gray-600">
                  {getPerformanceDescription(performance)}
                </div>
              </div>
              <div className="text-4xl">
                {getGradeIcon(performance)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Key Insights */}
      <div className="border-t pt-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
            <Info className="w-4 h-4" />
            Key Insights
          </h4>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <Eye className="w-3 h-3" />
            {showDetails ? 'Hide' : 'Show'} Details
          </button>
        </div>
        
        <div className="text-sm text-gray-600 space-y-1">
          <div>• Exit prices {'>'} Entry prices = PROFIT (positive % change)</div>
          <div>• Exit prices {'<'} Entry prices = LOSS (negative % change)</div>
          <div>• Current win rate: {performance ? formatPercentage(performance.win_rate * 100) : 'N/A'}</div>
          <div>• Total P&L: {performance ? formatPercentage(performance.total_pnl_percent) : 'N/A'}</div>
          
          {showDetails && (
            <div className="mt-3 pt-3 border-t space-y-2">
              <div className="bg-blue-50 p-2 rounded">
                <strong>Risk Assessment:</strong> {performance ? getRiskAssessment(performance) : 'Insufficient data'}
              </div>
              <div className="bg-green-50 p-2 rounded">
                <strong>Recommendation:</strong> {performance ? getRecommendation(performance) : 'Analyze performance data first'}
              </div>
              <div className="bg-purple-50 p-2 rounded">
                <strong>Next Steps:</strong> {performance ? getNextSteps(performance) : 'Start trading to generate insights'}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
