/**
 * Portfolio Dashboard Component - Complete portfolio visibility
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, PieChart, BarChart3, Activity, Shield,
  DollarSign, Percent, Clock, Eye, RefreshCw, Download, Plus, X,
  Award, AlertTriangle, Info, Target, Zap, Briefcase, Star,
  TrendingUp as TrendingUpIcon, TrendingDown as TrendingDownIcon
} from 'lucide-react';
import { httpClient, APIResponse } from '../config/api';
import { toast } from 'react-hot-toast';

interface Holding {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  current_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  status: string;
  days_held: number;
  performance: {
    total_trades: number;
    win_rate: number;
    avg_return: number;
  };
}

interface PortfolioData {
  holdings: Record<string, Holding>;
  total_value: number;
  holding_count: number;
  portfolio_composition: Record<string, any>;
  sector_allocation: Record<string, any>;
  risk_metrics: {
    concentration_risk: number;
    diversification_score: number;
    risk_level: string;
  };
  performance_metrics: {
    total_trades: number;
    win_rate: number;
    total_return: number;
  };
  overall_performance: {
    total_invested: number;
    current_value: number;
    total_pnl: number;
    total_pnl_percent: number;
    best_performer: any;
    worst_performer: any;
  };
}

interface DashboardData {
  portfolio_summary: PortfolioData;
  performance_metrics: any;
  recent_transactions: any[];
  watchlist: any[];
  top_performers: any[];
  market_overview: any;
  recommendations: string[];
}

export const PortfolioDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'holdings' | 'performance' | 'allocation' | 'risk' | 'dashboard'>('dashboard');
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedHolding, setSelectedHolding] = useState<string | null>(null);

  const fetchPortfolioData = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/v1/direct-portfolio');

      if (response.success) {
        setPortfolioData(response.data as PortfolioData);
      }
    } catch (err) {
      toast.error('Failed to fetch portfolio data');
      setError('Error fetching portfolio data');
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/v1/direct-portfolio');

      if (response.success) {
        setDashboardData(response.data as DashboardData);
      }
    } catch (err) {
      toast.error('Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchDashboardData();
    } else {
      fetchPortfolioData();
    }
  }, [activeTab]);

  const formatCurrency = (value: number) => {
    return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PROFITABLE': return 'text-green-600 bg-green-50';
      case 'POSITIVE': return 'text-blue-600 bg-blue-50';
      case 'BREAKEVEN': return 'text-yellow-600 bg-yellow-50';
      case 'LOSING': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'LOW': return 'text-green-600 bg-green-50';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50';
      case 'HIGH': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
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

  if (error && !portfolioData) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-red-600">
          <AlertTriangle className="w-12 h-12 mx-auto mb-2" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Portfolio Dashboard</h2>
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              if (activeTab === 'dashboard') fetchDashboardData();
              else fetchPortfolioData();
            }}
            className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => {
              httpClient.get('/api/v1/direct-portfolio')
                .then(() => toast.success('Portfolio exported successfully'))
                .catch(() => toast.error('Export failed'));
            }}
            className="text-green-600 hover:text-green-800 flex items-center gap-1"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'dashboard'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('holdings')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'holdings'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Holdings
        </button>
        <button
          onClick={() => setActiveTab('performance')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'performance'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Performance
        </button>
        <button
          onClick={() => setActiveTab('allocation')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'allocation'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Allocation
        </button>
        <button
          onClick={() => setActiveTab('risk')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'risk'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Risk Analysis
        </button>
      </div>

      {activeTab === 'dashboard' && dashboardData && (
        <div className="space-y-6">
          {/* Portfolio Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-blue-600">Total Value</div>
                  <div className="text-2xl font-bold text-blue-800">
                    {formatCurrency(dashboardData.portfolio_summary.total_value)}
                  </div>
                </div>
                <DollarSign className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-green-600">Total P&L</div>
                  <div className={`text-2xl font-bold ${
                    dashboardData.portfolio_summary.overall_performance.total_pnl >= 0 
                      ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {formatCurrency(dashboardData.portfolio_summary.overall_performance.total_pnl)}
                  </div>
                </div>
                {dashboardData.portfolio_summary.overall_performance.total_pnl >= 0 ? (
                  <TrendingUp className="w-8 h-8 text-green-500" />
                ) : (
                  <TrendingDown className="w-8 h-8 text-red-500" />
                )}
              </div>
            </div>
            
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-purple-600">Holdings</div>
                  <div className="text-2xl font-bold text-purple-800">
                    {dashboardData.portfolio_summary.holding_count}
                  </div>
                </div>
                <Briefcase className="w-8 h-8 text-purple-500" />
              </div>
            </div>
            
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-orange-600">Win Rate</div>
                  <div className="text-2xl font-bold text-orange-800">
                    {(dashboardData.portfolio_summary.performance_metrics.win_rate * 100).toFixed(1)}%
                  </div>
                </div>
                <Target className="w-8 h-8 text-orange-500" />
              </div>
            </div>
          </div>

          {/* Top Performers */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Top Performers</h3>
            <div className="space-y-2">
              {dashboardData.top_performers.slice(0, 5).map((performer, index) => (
                <div key={performer.symbol} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="text-lg font-bold text-gray-600">#{index + 1}</div>
                    <div>
                      <div className="font-medium">{performer.symbol}</div>
                      <div className="text-sm text-gray-600">{formatCurrency(performer.current_value)}</div>
                    </div>
                  </div>
                  <div className={`font-bold ${performer.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(performer.pnl_percent)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          {dashboardData.recommendations.length > 0 && (
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-yellow-800 mb-3">Portfolio Recommendations</h3>
              <ul className="space-y-2">
                {dashboardData.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2 text-yellow-700">
                    <Info className="w-4 h-4 mt-0.5" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {activeTab === 'holdings' && portfolioData && (
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Current Holdings</h3>
            <div className="text-sm text-gray-600">
              {portfolioData.holding_count} holdings • {formatCurrency(portfolioData.total_value)} total value
            </div>
          </div>
          
          {Object.entries(portfolioData.holdings).map(([symbol, holding]) => (
            <div key={symbol} className="bg-gray-50 p-4 rounded-lg">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="text-lg font-semibold">{symbol}</h4>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(holding.status)}`}>
                      {holding.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Quantity</div>
                      <div className="font-medium">{holding.quantity}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Avg Price</div>
                      <div className="font-medium">{formatCurrency(holding.avg_price)}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Current Price</div>
                      <div className="font-medium">{formatCurrency(holding.current_price)}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Days Held</div>
                      <div className="font-medium">{holding.days_held}</div>
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-800">
                    {formatCurrency(holding.current_value)}
                  </div>
                  <div className={`font-medium ${holding.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(holding.unrealized_pnl)} ({formatPercentage(holding.unrealized_pnl_percent)})
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    WR: {(holding.performance.win_rate * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'performance' && portfolioData && (
        <div className="space-y-6">
          {/* Overall Performance */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-800 mb-3">Overall Performance</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-blue-600">Total Invested</div>
                <div className="text-lg font-bold text-blue-800">
                  {formatCurrency(portfolioData.overall_performance.total_invested)}
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-600">Current Value</div>
                <div className="text-lg font-bold text-blue-800">
                  {formatCurrency(portfolioData.overall_performance.current_value)}
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-600">Total P&L</div>
                <div className={`text-lg font-bold ${
                  portfolioData.overall_performance.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(portfolioData.overall_performance.total_pnl)}
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-600">P&L %</div>
                <div className={`text-lg font-bold ${
                  portfolioData.overall_performance.total_pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatPercentage(portfolioData.overall_performance.total_pnl_percent)}
                </div>
              </div>
            </div>
          </div>

          {/* Trading Performance */}
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-green-800 mb-3">Trading Performance</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-green-600">Total Trades</div>
                <div className="text-lg font-bold text-green-800">
                  {portfolioData.performance_metrics.total_trades}
                </div>
              </div>
              <div>
                <div className="text-sm text-green-600">Win Rate</div>
                <div className="text-lg font-bold text-green-800">
                  {(portfolioData.performance_metrics.win_rate * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-green-600">Total Return</div>
                <div className="text-lg font-bold text-green-800">
                  {formatPercentage(portfolioData.performance_metrics.total_return)}
                </div>
              </div>
            </div>
          </div>

          {/* Best/Worst Performers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-semibold text-green-800 mb-2">Best Performer</h4>
              {portfolioData.overall_performance.best_performer ? (
                <div>
                  <div className="text-lg font-bold">{portfolioData.overall_performance.best_performer.symbol}</div>
                  <div className="text-green-600">
                    {formatPercentage(portfolioData.overall_performance.best_performer.pnl_percent)}
                  </div>
                </div>
              ) : (
                <div className="text-gray-600">No data available</div>
              )}
            </div>
            
            <div className="bg-red-50 p-4 rounded-lg">
              <h4 className="font-semibold text-red-800 mb-2">Worst Performer</h4>
              {portfolioData.overall_performance.worst_performer ? (
                <div>
                  <div className="text-lg font-bold">{portfolioData.overall_performance.worst_performer.symbol}</div>
                  <div className="text-red-600">
                    {formatPercentage(portfolioData.overall_performance.worst_performer.pnl_percent)}
                  </div>
                </div>
              ) : (
                <div className="text-gray-600">No data available</div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'allocation' && portfolioData && (
        <div className="space-y-6">
          {/* Portfolio Composition */}
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-purple-800 mb-3">Portfolio Composition</h3>
            <div className="space-y-2">
              {Object.entries(portfolioData.portfolio_composition).map(([symbol, data]: [string, any]) => (
                <div key={symbol} className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">{symbol}</div>
                    <div className="text-sm text-gray-600">{data.quantity} shares</div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{formatCurrency(data.value)}</div>
                    <div className="text-sm text-gray-600">{data.percentage.toFixed(1)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sector Allocation */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-800 mb-3">Sector Allocation</h3>
            <div className="space-y-2">
              {Object.entries(portfolioData.sector_allocation).map(([sector, data]: [string, any]) => (
                <div key={sector} className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">{sector}</div>
                    <div className="text-sm text-gray-600">{data.symbols.length} stocks</div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{formatCurrency(data.value)}</div>
                    <div className="text-sm text-gray-600">{data.percentage.toFixed(1)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'risk' && portfolioData && (
        <div className="space-y-6">
          {/* Risk Metrics */}
          <div className="bg-red-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-red-800 mb-3">Risk Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-red-600">Risk Level</div>
                <div className={`text-lg font-bold ${getRiskColor(portfolioData.risk_metrics.risk_level).split(' ')[0]}`}>
                  {portfolioData.risk_metrics.risk_level}
                </div>
              </div>
              <div>
                <div className="text-sm text-red-600">Concentration Risk</div>
                <div className="text-lg font-bold text-red-800">
                  {portfolioData.risk_metrics.concentration_risk.toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-red-600">Diversification Score</div>
                <div className="text-lg font-bold text-red-800">
                  {portfolioData.risk_metrics.diversification_score.toFixed(1)}
                </div>
              </div>
            </div>
          </div>

          {/* Risk Assessment */}
          <div className="bg-orange-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-orange-800 mb-3">Risk Assessment</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-orange-700">Portfolio is well-diversified</span>
                <span className="text-orange-600">
                  {portfolioData.risk_metrics.diversification_score > 70 ? '✅ Yes' : '⚠️ No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-orange-700">Concentration risk is acceptable</span>
                <span className="text-orange-600">
                  {portfolioData.risk_metrics.concentration_risk < 30 ? '✅ Yes' : '⚠️ No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-orange-700">Overall risk level</span>
                <span className={`font-medium ${getRiskColor(portfolioData.risk_metrics.risk_level).split(' ')[0]}`}>
                  {portfolioData.risk_metrics.risk_level}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
