/**
 * Daily Comparison Component - Frontend Implementation
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, BarChart3, Target, AlertTriangle,
  Award, Calendar, Clock, Users, Trophy, Star, ChevronUp, ChevronDown,
  Eye, RefreshCw, Info, Activity, Zap, Shield
} from 'lucide-react';
import { httpClient, APIResponse } from '../config/api';
import { toast } from 'react-hot-toast';

interface MarketData {
  NIFTY: {
    open: number;
    close: number;
    high: number;
    low: number;
    volume: number;
    daily_return: number;
    volatility: number;
  };
  BANKNIFTY: {
    open: number;
    close: number;
    high: number;
    low: number;
    volume: number;
    daily_return: number;
    volatility: number;
  };
  sectors: {
    [key: string]: {
      return: number;
      volatility: number;
    };
  };
}

interface UserComparison {
  user_id: number;
  date: string;
  portfolio_return: number;
  trading_performance: {
    total_trades: number;
    win_rate: number;
    total_return: number;
    avg_return: number;
    max_profit: number;
    max_loss: number;
  };
  grade: string;
  score: number;
  insights: {
    market_comparison: string;
    strategy_effectiveness: string;
    risk_assessment: string;
    recommendations: string[];
  };
  rank_position?: number;
}

interface StrategyPerformance {
  [strategy: string]: {
    total_trades: number;
    closed_trades: number;
    win_rate: number;
    total_return: number;
    avg_return: number;
    rank_position: number;
  };
}

interface MarketSummary {
  market_return: number;
  avg_user_return: number;
  avg_user_score: number;
  total_users_analyzed: number;
  users_beating_market: number;
  percent_beating_market: number;
  best_performer_return: number;
  worst_performer_return: number;
}

interface DailyComparisonData {
  date: string;
  market_data: MarketData;
  user_comparison: UserComparison;
  strategy_performance: StrategyPerformance;
  market_summary: MarketSummary;
}

export const DailyComparison: React.FC = () => {
  const [comparison, setComparison] = useState<DailyComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [showDetails, setShowDetails] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'strategies' | 'insights'>('overview');

  const fetchDailyComparison = async (date: string) => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/v1/daily-comparison/summary', {
        params: { analysis_date: date }
      });

      if (response.success) {
        setComparison(response.data as DailyComparisonData);
      } else {
        setError('Failed to fetch daily comparison');
      }
    } catch (err) {
      setError('Error fetching daily comparison data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDailyComparison(selectedDate);
  }, [selectedDate]);

  const getGradeColor = (grade: string) => {
    switch (grade[0]) {
      case 'A': return 'text-green-600 bg-green-50 border-green-200';
      case 'B': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'C': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-red-600 bg-red-50 border-red-200';
    }
  };

  const getGradeIcon = (grade: string) => {
    switch (grade[0]) {
      case 'A': return <Trophy className="w-6 h-6 text-yellow-500" />;
      case 'B': return <Award className="w-6 h-6 text-blue-500" />;
      case 'C': return <Shield className="w-6 h-6 text-yellow-500" />;
      default: return <AlertTriangle className="w-6 h-6 text-red-500" />;
    }
  };

  const getReturnIcon = (value: number) => {
    if (value > 0) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (value < 0) return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Activity className="w-4 h-4 text-gray-600" />;
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
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

  if (error || !comparison) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-red-600">
          <AlertTriangle className="w-12 h-12 mx-auto mb-2" />
          <p>{error || 'No daily comparison data available'}</p>
        </div>
      </div>
    );
  }

  const { market_data, user_comparison, strategy_performance, market_summary } = comparison;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Daily Market Comparison</h2>
        <div className="flex items-center gap-4">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-2 border rounded-md"
            max={new Date().toISOString().split('T')[0]}
          />
          <button
            onClick={() => fetchDailyComparison(selectedDate)}
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
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'overview'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('strategies')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'strategies'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Strategies
        </button>
        <button
          onClick={() => setActiveTab('insights')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'insights'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Insights
        </button>
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Market Performance */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Market Performance
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-700 mb-2">NIFTY 50</h4>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-gray-800">
                    {market_data.NIFTY.close.toFixed(2)}
                  </span>
                  <div className="flex items-center gap-1">
                    {getReturnIcon(market_data.NIFTY.daily_return)}
                    <span className={`font-medium ${
                      market_data.NIFTY.daily_return > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatPercentage(market_data.NIFTY.daily_return)}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-700 mb-2">BANK NIFTY</h4>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-gray-800">
                    {market_data.BANKNIFTY.close.toFixed(2)}
                  </span>
                  <div className="flex items-center gap-1">
                    {getReturnIcon(market_data.BANKNIFTY.daily_return)}
                    <span className={`font-medium ${
                      market_data.BANKNIFTY.daily_return > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatPercentage(market_data.BANKNIFTY.daily_return)}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-700 mb-2">Market Summary</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Users Analyzed:</span>
                    <span className="font-medium">{market_summary.total_users_analyzed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Beating Market:</span>
                    <span className="font-medium text-green-600">
                      {market_summary.percent_beating_market.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Your Performance */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Trophy className="w-5 h-5" />
              Your Performance
            </h3>
            <div className={`p-4 rounded-lg border-2 ${getGradeColor(user_comparison.grade)}`}>
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="text-3xl font-bold">{user_comparison.grade}</div>
                    <div className="text-lg font-medium">Score: {user_comparison.score.toFixed(1)}/100</div>
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    {getReturnIcon(user_comparison.portfolio_return)}
                    <span className="text-xl font-bold">
                      {formatPercentage(user_comparison.portfolio_return)}
                    </span>
                    <span className="text-sm text-gray-600">Your Return</span>
                  </div>
                  <div className="text-sm text-gray-700">
                    {user_comparison.insights.market_comparison}
                  </div>
                </div>
                <div className="text-4xl">
                  {getGradeIcon(user_comparison.grade)}
                </div>
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Performance Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">
                  {user_comparison.trading_performance.total_trades}
                </div>
                <div className="text-sm text-gray-600">Total Trades</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {(user_comparison.trading_performance.win_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Win Rate</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {formatPercentage(user_comparison.trading_performance.avg_return)}
                </div>
                <div className="text-sm text-gray-600">Avg Return</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {formatPercentage(user_comparison.trading_performance.max_profit)}
                </div>
                <div className="text-sm text-gray-600">Max Profit</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'strategies' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Strategy Performance Ranking</h3>
          {Object.entries(strategy_performance)
            .sort(([,a], [,b]) => b.total_return - a.total_return)
            .map(([strategy, metrics], index) => (
              <div key={strategy} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="text-lg font-bold text-gray-600">#{index + 1}</div>
                  <div>
                    <div className="font-medium">{strategy}</div>
                    <div className="text-sm text-gray-600">
                      {metrics.total_trades} trades • {(metrics.win_rate * 100).toFixed(1)}% win rate
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${
                    metrics.total_return > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatPercentage(metrics.total_return)}
                  </div>
                  <div className="text-sm text-gray-600">
                    Avg: {formatPercentage(metrics.avg_return)}
                  </div>
                </div>
              </div>
            ))}
        </div>
      )}

      {activeTab === 'insights' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">AI Insights & Recommendations</h3>
          
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">Market Comparison</h4>
              <p className="text-blue-700">{user_comparison.insights.market_comparison}</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-semibold text-green-800 mb-2">Strategy Effectiveness</h4>
              <p className="text-green-700">{user_comparison.insights.strategy_effectiveness}</p>
            </div>
            
            <div className="bg-purple-50 p-4 rounded-lg">
              <h4 className="font-semibold text-purple-800 mb-2">Risk Assessment</h4>
              <p className="text-purple-700">{user_comparison.insights.risk_assessment}</p>
            </div>
            
            {user_comparison.insights.recommendations.length > 0 && (
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h4 className="font-semibold text-yellow-800 mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {user_comparison.insights.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start gap-2 text-yellow-700">
                      <Star className="w-4 h-4 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
