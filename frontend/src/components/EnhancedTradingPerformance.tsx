/**
 * Enhanced Trading Performance Component
 * Integrates portfolio and trading performance with unified metrics
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, BarChart3, Target, AlertTriangle,
  ArrowUpRight, ArrowDownRight, Minus, Calculator, Activity,
  Shield, Award, Info, Eye, Plus, X, CheckCircle, AlertCircle
} from 'lucide-react';
import { httpClient, APIResponse } from '../config/api';
import { toast } from 'react-hot-toast';

interface UnifiedMetrics {
  overall_score: number;
  trading_score: number;
  portfolio_score: number;
  risk_score: number;
  grade: string;
  recommendations: string[];
}

interface TradingMetrics {
  total_trades: number;
  closed_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_return: number;
  max_profit: number;
  max_loss: number;
}

interface PortfolioMetrics {
  total_value: number;
  holdings_count: number;
  diversification_score: number;
  concentration_risk: number;
  holdings: Record<string, number>;
}

interface UnifiedPerformance {
  trading_performance: TradingMetrics;
  portfolio_performance: PortfolioMetrics;
  unified_metrics: UnifiedMetrics;
}

export const EnhancedTradingPerformance: React.FC = () => {
  const [performance, setPerformance] = useState<UnifiedPerformance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [days, setDays] = useState(30);

  const fetchUnifiedPerformance = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/v1/enhanced-trading/unified-performance', {
        params: { days }
      });

      if (response.success) {
        setPerformance(response.data as UnifiedPerformance);
      } else {
        setError('Failed to fetch unified performance');
      }
    } catch (err) {
      setError('Error fetching performance data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnifiedPerformance();
  }, [days]);

  const getGradeColor = (grade: string) => {
    switch (grade[0]) {
      case 'A': return 'text-green-600 bg-green-50';
      case 'B': return 'text-blue-600 bg-blue-50';
      case 'C': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-red-600 bg-red-50';
    }
  };

  const getGradeIcon = (grade: string) => {
    switch (grade[0]) {
      case 'A': return <Award className="w-8 h-8 text-green-500" />;
      case 'B': return <TrendingUp className="w-8 h-8 text-blue-500" />;
      case 'C': return <Shield className="w-8 h-8 text-yellow-500" />;
      default: return <AlertTriangle className="w-8 h-8 text-red-500" />;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-3 bg-gray-200 rounded"></div>
          <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          <div className="h-3 bg-gray-200 rounded w-4/6"></div>
        </div>
      </div>
    );
  }

  if (error || !performance) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-red-600">
          <AlertCircle className="w-12 h-12 mx-auto mb-2" />
          <p>{error || 'No performance data available'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Enhanced Trading Performance</h2>
        <div className="flex items-center gap-4">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-2 border rounded-md"
          >
            <option value={7}>7 Days</option>
            <option value={30}>30 Days</option>
            <option value={90}>90 Days</option>
          </select>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <Eye className="w-4 h-4" />
            {showDetails ? 'Hide' : 'Show'} Details
          </button>
        </div>
      </div>

      {/* Overall Grade */}
      <div className={`mb-6 p-4 rounded-lg ${getGradeColor(performance.unified_metrics.grade)}`}>
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold mb-1">Overall Performance Grade</h3>
            <div className="text-3xl font-bold">{performance.unified_metrics.grade}</div>
            <div className="text-sm mt-1">Score: {performance.unified_metrics.overall_score.toFixed(1)}/100</div>
          </div>
          <div className="text-4xl">
            {getGradeIcon(performance.unified_metrics.grade)}
          </div>
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="font-semibold text-blue-800 mb-2">Trading Score</h4>
          <div className="text-2xl font-bold text-blue-600">
            {performance.unified_metrics.trading_score.toFixed(1)}
          </div>
          <div className="text-sm text-blue-600">Win Rate: {(performance.trading_performance.win_rate * 100).toFixed(1)}%</div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <h4 className="font-semibold text-green-800 mb-2">Portfolio Score</h4>
          <div className="text-2xl font-bold text-green-600">
            {performance.unified_metrics.portfolio_score.toFixed(1)}
          </div>
          <div className="text-sm text-green-600">Diversification: {performance.portfolio_performance.diversification_score.toFixed(1)}%</div>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg">
          <h4 className="font-semibold text-purple-800 mb-2">Risk Score</h4>
          <div className="text-2xl font-bold text-purple-600">
            {performance.unified_metrics.risk_score.toFixed(1)}
          </div>
          <div className="text-sm text-purple-600">Concentration: {performance.portfolio_performance.concentration_risk.toFixed(1)}%</div>
        </div>
      </div>

      {/* Trading Performance */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Trading Performance</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-800">{performance.trading_performance.total_trades}</div>
            <div className="text-sm text-gray-600">Total Trades</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{(performance.trading_performance.win_rate * 100).toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Win Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">₹{performance.trading_performance.total_pnl.toFixed(0)}</div>
            <div className="text-sm text-gray-600">Total P&L</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{performance.trading_performance.avg_return.toFixed(2)}%</div>
            <div className="text-sm text-gray-600">Avg Return</div>
          </div>
        </div>
      </div>

      {/* Portfolio Performance */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Portfolio Performance</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-800">₹{performance.portfolio_performance.total_value.toFixed(0)}</div>
            <div className="text-sm text-gray-600">Total Value</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{performance.portfolio_performance.holdings_count}</div>
            <div className="text-sm text-gray-600">Holdings</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{performance.portfolio_performance.diversification_score.toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Diversification</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{performance.portfolio_performance.concentration_risk.toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Concentration</div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {showDetails && (
        <div className="border-t pt-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Info className="w-5 h-5" />
            AI Recommendations
          </h3>
          <div className="space-y-2">
            {performance.unified_metrics.recommendations.map((rec, index) => (
              <div key={index} className="flex items-start gap-2 p-3 bg-yellow-50 rounded">
                <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5" />
                <span className="text-sm text-yellow-800">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
