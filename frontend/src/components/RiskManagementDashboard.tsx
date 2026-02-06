/**
 * Risk Management Dashboard - Portfolio Risk Tools
 * Comprehensive risk management interface with portfolio analysis
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  ExclamationTriangleIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  AdjustmentsHorizontalIcon,
  DocumentTextIcon,
  BellIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  PlayIcon,
  PauseIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  ShareIcon,
  DocumentArrowDownIcon,
  CpuChipIcon,
  ArrowTrendingDownIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import { toast } from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';
import ErrorDisplay from './ErrorDisplay';
import BuySellButton from './BuySellButton';

// Import Risk Management API service
import riskManagementApi, {
  RiskMetricsResponse,
  PortfolioAllocationResponse,
  StressTestRequest,
  StressTestResponse,
  RiskLimitsRequest,
  RiskLimitsResponse
} from '../services/riskManagementApi';

interface RiskManagementDashboardProps {
  className?: string;
}

type TabType = 'metrics' | 'allocation' | 'stress-test' | 'limits' | 'alerts' | 'reports';

const RiskManagementDashboard: React.FC<RiskManagementDashboardProps> = ({
  className = ''
}) => {
  // State management
  const [activeTab, setActiveTab] = useState<TabType>('metrics');
  const [isLive, setIsLive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [riskMetrics, setRiskMetrics] = useState<RiskMetricsResponse | null>(null);
  const [portfolioAllocation, setPortfolioAllocation] = useState<PortfolioAllocationResponse | null>(null);
  const [stressTestResults, setStressTestResults] = useState<StressTestResponse | null>(null);
  const [riskLimits, setRiskLimits] = useState<RiskLimitsResponse | null>(null);
  const [riskAlerts, setRiskAlerts] = useState<any[]>([]);
  const [riskReports, setRiskReports] = useState<any[]>([]);

  // Stress test configuration
  const [stressTestConfig, setStressTestConfig] = useState<StressTestRequest>({
    scenarios: [
      {
        name: 'Market Crash',
        type: 'market_crash',
        parameters: { market_decline: -20 },
        duration: '1_month'
      },
      {
        name: 'Sector Rotation',
        type: 'sector_rotation',
        parameters: { tech_decline: -15, finance_growth: 10 },
        duration: '3_months'
      },
      {
        name: 'Volatility Spike',
        type: 'volatility_spike',
        parameters: { volatility_increase: 50 },
        duration: '1_week'
      }
    ],
    portfolio_data: [
      { symbol: 'RELIANCE', quantity: 100, current_price: 2500, sector: 'Energy', market_cap: 'large' },
      { symbol: 'TCS', quantity: 50, current_price: 3500, sector: 'Technology', market_cap: 'large' },
      { symbol: 'INFY', quantity: 75, current_price: 1500, sector: 'Technology', market_cap: 'large' }
    ]
  });

  const refreshIntervalRef = React.useRef<NodeJS.Timeout | null>(null);

  // Fetch data functions
  const fetchRiskMetrics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await riskManagementApi.getRiskMetrics();
      setRiskMetrics(result);
      toast.success('Risk metrics updated');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get risk metrics';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPortfolioAllocation = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await riskManagementApi.getPortfolioAllocation();
      setPortfolioAllocation(result);
      toast.success('Portfolio allocation updated');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get portfolio allocation';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const runStressTest = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await riskManagementApi.runStressTest(stressTestConfig);
      setStressTestResults(result);
      toast.success(`Stress test completed: ${(result.test_results ?? []).length} scenarios`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to run stress test';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [stressTestConfig]);

  const fetchRiskLimits = useCallback(async () => {
    try {
      const result = await riskManagementApi.getRiskLimits();
      setRiskLimits(result);
    } catch (err) {
      console.error('Failed to fetch risk limits:', err);
    }
  }, []);

  const fetchRiskAlerts = useCallback(async () => {
    try {
      const result = await riskManagementApi.getRiskAlerts();
      setRiskAlerts(result.data || []);
    } catch (err) {
      console.error('Failed to fetch risk alerts:', err);
    }
  }, []);

  const fetchRiskReports = useCallback(async () => {
    try {
      const result = await riskManagementApi.getRiskReports();
      setRiskReports(result.data || []);
    } catch (err) {
      console.error('Failed to fetch risk reports:', err);
    }
  }, []);

  // Auto-refresh for live data
  useEffect(() => {
    if (isLive) {
      refreshIntervalRef.current = setInterval(() => {
        fetchRiskMetrics();
        fetchPortfolioAllocation();
        fetchRiskAlerts();
        if (activeTab === 'metrics' && riskMetrics) {
          fetchRiskMetrics();
        }
      }, 300000); // Refresh every 5 minutes
    } else {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [isLive, activeTab, riskMetrics, fetchRiskMetrics, fetchPortfolioAllocation, fetchRiskAlerts]);

  // Initial data load
  useEffect(() => {
    fetchRiskMetrics();
    fetchPortfolioAllocation();
    fetchRiskLimits();
    fetchRiskAlerts();
    fetchRiskReports();
  }, [fetchRiskMetrics, fetchPortfolioAllocation, fetchRiskLimits, fetchRiskAlerts, fetchRiskReports]);

  // Tab configuration
  const tabs = [
    { id: 'metrics', label: 'Risk Metrics', icon: ChartBarIcon },
    { id: 'allocation', label: 'Allocation', icon: AdjustmentsHorizontalIcon },
    { id: 'stress-test', label: 'Stress Test', icon: CpuChipIcon },
    { id: 'limits', label: 'Risk Limits', icon: ShieldCheckIcon },
    { id: 'alerts', label: 'Alerts', icon: BellIcon },
    { id: 'reports', label: 'Reports', icon: DocumentTextIcon }
  ] as const;

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <ErrorDisplay 
          message={error} 
          onRetry={() => {
            setError(null);
            if (activeTab === 'metrics') fetchRiskMetrics();
            else if (activeTab === 'allocation') fetchPortfolioAllocation();
            else if (activeTab === 'stress-test') runStressTest();
            else if (activeTab === 'limits') fetchRiskLimits();
            else if (activeTab === 'alerts') fetchRiskAlerts();
            else if (activeTab === 'reports') fetchRiskReports();
          }}
          title="Risk Management Error"
        />
      </div>
    );
  }

  return (
    <div className={cn("h-full flex flex-col bg-gray-50 dark:bg-gray-900", className)}>
      {/* Header */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Risk Management Dashboard</h1>
            </div>

            {/* Live Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsLive(!isLive)}
                className={cn(
                  "flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors",
                  isLive
                    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                    : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                )}
              >
                {isLive ? <PlayIcon className="h-4 w-4" /> : <PauseIcon className="h-4 w-4" />}
                <span>{isLive ? 'Live' : 'Paused'}</span>
              </button>

              <button
                onClick={() => {
                  if (activeTab === 'metrics') fetchRiskMetrics();
                  else if (activeTab === 'allocation') fetchPortfolioAllocation();
                  else if (activeTab === 'stress-test') runStressTest();
                  else if (activeTab === 'limits') fetchRiskLimits();
                  else if (activeTab === 'alerts') fetchRiskAlerts();
                  else if (activeTab === 'reports') fetchRiskReports();
                }}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-4">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors",
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600 dark:text-blue-400"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4">
        {loading && (
          <div className="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-50">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Risk Metrics Tab */}
        {activeTab === 'metrics' && (
          <div className="space-y-6">
            {riskMetrics ? (
              <>
                {/* Portfolio Risk Overview */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Portfolio Risk Overview</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Total Value</div>
                      <div className="font-semibold text-gray-900 dark:text-white">₹{(riskMetrics.portfolio_risk?.total_value ?? 0).toLocaleString()}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Total Risk</div>
                      <div className="font-semibold text-gray-900 dark:text-white">₹{(riskMetrics.portfolio_risk?.total_risk ?? 0).toLocaleString()}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Risk %</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{riskMetrics.portfolio_risk?.risk_percentage ?? 0}%</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">VaR 95%</div>
                      <div className="font-semibold text-gray-900 dark:text-white">₹{(riskMetrics.portfolio_risk?.var_95 ?? 0).toLocaleString()}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{riskMetrics.portfolio_risk?.max_drawdown ?? 0}%</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{riskMetrics.portfolio_risk?.sharpe_ratio ?? 0}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Sortino Ratio</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{riskMetrics.portfolio_risk?.sortino_ratio ?? 0}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Calmar Ratio</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{riskMetrics.portfolio_risk?.calmar_ratio ?? 0}</div>
                    </div>
                  </div>
                </div>

                {/* Position Risks */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Position Risks</h3>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                      <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Symbol</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Position Value</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Risk Contribution</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Beta</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Volatility</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Concentration Risk</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider text-center">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                        {(riskMetrics.position_risks ?? []).map((position, index) => (
                          <tr key={index}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{position.symbol}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">₹{position.position_value.toLocaleString()}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{position.risk_contribution}%</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{position.beta}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{position.volatility}%</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={cn(
                                "px-2 py-1 rounded-full text-xs font-medium",
                                position.concentration_risk === 'low' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                                position.concentration_risk === 'medium' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                                "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                              )}>
                                {position.concentration_risk}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <BuySellButton
                                symbol={position.symbol}
                                currentPrice={0} // Will fetch current price in modal
                                size="sm"
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Compliance Status */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Compliance Status</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Compliance Overview</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Overall Status:</span>
                          <span className={cn(
                            "px-2 py-1 rounded-full text-xs font-medium",
                            (riskMetrics.compliance_status?.overall_compliance ?? 'compliant') === 'compliant' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                            (riskMetrics.compliance_status?.overall_compliance ?? 'compliant') === 'warning' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                            "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                          )}>
                            {riskMetrics.compliance_status?.overall_compliance ?? 'compliant'}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Position Limits Breached: {(riskMetrics.compliance_status?.position_limits_breached ?? []).length}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Sector Limits Breached: {(riskMetrics.compliance_status?.sector_limits_breached ?? []).length}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Risk Limits Breached: {(riskMetrics.compliance_status?.risk_limits_breached ?? []).length}
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Recommendations</h4>
                      <div className="space-y-2">
                        {(riskMetrics.recommendations ?? []).map((rec, index) => (
                          <div key={index} className="p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-gray-900 dark:text-white">{rec.type}</span>
                              <span className={cn(
                                "px-2 py-1 rounded-full text-xs font-medium",
                                rec.priority === 'high' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                                rec.priority === 'medium' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                                "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                              )}>
                                {rec.priority}
                              </span>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">{rec.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Risk Metrics Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Get comprehensive portfolio risk analysis</p>
                <button
                  onClick={fetchRiskMetrics}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Load Risk Metrics
                </button>
              </div>
            )}
          </div>
        )}

        {/* Portfolio Allocation Tab */}
        {activeTab === 'allocation' && (
          <div className="space-y-6">
            {portfolioAllocation ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Portfolio Allocation Analysis</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Current vs Target Allocation</h4>
                      <div className="space-y-2">
                        {(portfolioAllocation.current_allocation ?? []).map((item, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div>
                              <span className="font-medium text-gray-900 dark:text-white">{item.symbol}</span>
                              <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">({item.sector})</span>
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              {item.current_weight}% → {item.target_weight}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Sector Allocation</h4>
                      <div className="space-y-2">
                        {(portfolioAllocation.sector_allocation ?? []).map((sector, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div>
                              <span className="font-medium text-gray-900 dark:text-white">{sector.sector}</span>
                              <span className={cn(
                                "ml-2 px-2 py-1 rounded-full text-xs font-medium",
                                sector.risk_level === 'low' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                                sector.risk_level === 'medium' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                                "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                              )}>
                                {sector.risk_level}
                              </span>
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              {sector.current_weight}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Rebalancing Recommendations */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Rebalancing Recommendations</h3>
                  
                  <div className="space-y-3">
                    {(portfolioAllocation.rebalancing_priority ?? []).map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                        <div className="flex items-center space-x-3">
                          <span className="font-medium text-gray-900 dark:text-white">{item.symbol}</span>
                          <span className={cn(
                            "px-2 py-1 rounded-full text-xs font-medium",
                            item.action === 'BUY' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                            item.action === 'SELL' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                            "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
                          )}>
                            {item.action}
                          </span>
                          <span className={cn(
                            "px-2 py-1 rounded-full text-xs font-medium",
                            item.priority === 'high' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                            item.priority === 'medium' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                            "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                          )}>
                            {item.priority}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {item.quantity} shares
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <AdjustmentsHorizontalIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Allocation Data Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Analyze portfolio allocation and rebalancing needs</p>
                <button
                  onClick={fetchPortfolioAllocation}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Load Allocation Data
                </button>
              </div>
            )}
          </div>
        )}

        {/* Stress Test Tab */}
        {activeTab === 'stress-test' && (
          <div className="space-y-6">
            {/* Stress Test Configuration */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Stress Test Configuration</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                {stressTestConfig.scenarios.map((scenario, index) => (
                  <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2">{scenario.name}</h4>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <div>Type: {scenario.type}</div>
                      <div>Duration: {scenario.duration}</div>
                      <div>Parameters: {Object.entries(scenario.parameters).map(([key, value]) => `${key}: ${value}`).join(', ')}</div>
                    </div>
                  </div>
                ))}
              </div>
              
              <button
                onClick={runStressTest}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Run Stress Test
              </button>
            </div>

            {/* Stress Test Results */}
            {stressTestResults ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Stress Test Results</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Worst Case Scenario</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{stressTestResults.summary.worst_case_scenario}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Maximum Loss</div>
                      <div className="font-semibold text-gray-900 dark:text-white">₹{stressTestResults.summary.maximum_loss.toLocaleString()}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Portfolio Resilience</div>
                      <div className="font-semibold text-gray-900 dark:text-white capitalize">{stressTestResults.summary.overall_portfolio_resilience}</div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {(stressTestResults.test_results ?? []).map((result, index) => (
                      <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 dark:text-white mb-3">{result.scenario_name}</h4>
                        
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div className="text-xs text-gray-600 dark:text-gray-400">Total Loss</div>
                            <div className="font-semibold text-gray-900 dark:text-white">₹{result.portfolio_impact.total_loss.toLocaleString()}</div>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div className="text-xs text-gray-600 dark:text-gray-400">Loss %</div>
                            <div className="font-semibold text-gray-900 dark:text-white">{result.portfolio_impact.loss_percentage}%</div>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div className="text-xs text-gray-600 dark:text-gray-400">Worst Day</div>
                            <div className="font-semibold text-gray-900 dark:text-white">{result.portfolio_impact.worst_day_loss}%</div>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div className="text-xs text-gray-600 dark:text-gray-400">Recovery Time</div>
                            <div className="font-semibold text-gray-900 dark:text-white">{result.portfolio_impact.recovery_time}</div>
                          </div>
                        </div>
                        
                        <div>
                          <h5 className="font-medium text-gray-900 dark:text-white mb-2">Recommendations</h5>
                          <div className="space-y-1">
                            {(result.recommendations ?? []).map((rec, recIndex) => (
                              <div key={recIndex} className="text-sm text-gray-600 dark:text-gray-400">
                                • {rec.description} ({rec.priority} priority)
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <CpuChipIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Stress Test Results Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Run stress tests to analyze portfolio resilience</p>
                <button
                  onClick={runStressTest}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Run Stress Test
                </button>
              </div>
            )}
          </div>
        )}

        {/* Risk Limits Tab */}
        {activeTab === 'limits' && (
          <div className="space-y-6">
            {riskLimits ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Risk Limits & Compliance</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Current Limits</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Max Position Size:</span>
                          <span className="font-medium text-gray-900 dark:text-white">₹{(riskLimits.current_limits?.position_limits?.max_single_position ?? 0).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Max Position %:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{riskLimits.current_limits?.position_limits?.max_position_percentage ?? 0}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Max Sector Allocation:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{riskLimits.current_limits?.sector_limits?.max_sector_allocation ?? 0}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Max Portfolio VaR:</span>
                          <span className="font-medium text-gray-900 dark:text-white">₹{(riskLimits.current_limits?.risk_limits?.max_portfolio_var ?? 0).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Compliance Status</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Overall Status:</span>
                          <span className={cn(
                            "px-2 py-1 rounded-full text-xs font-medium",
                            (riskLimits.compliance_status?.overall_status ?? 'compliant') === 'compliant' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                            (riskLimits.compliance_status?.overall_status ?? 'compliant') === 'warning' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                            "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                          )}>
                            {riskLimits.compliance_status?.overall_status ?? 'compliant'}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Breaches: {(riskLimits.breaches ?? []).length}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Breaches */}
                {(riskLimits.breaches ?? []).length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Limit Breaches</h3>
                    
                    <div className="space-y-3">
                      {(riskLimits.breaches ?? []).map((breach, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                          <div className="flex items-center space-x-3">
                            <span className="font-medium text-gray-900 dark:text-white">{breach.type}</span>
                            {breach.symbol && <span className="text-sm text-gray-600 dark:text-gray-400">({breach.symbol})</span>}
                            {breach.sector && <span className="text-sm text-gray-600 dark:text-gray-400">({breach.sector})</span>}
                            <span className={cn(
                              "px-2 py-1 rounded-full text-xs font-medium",
                              breach.severity === 'severe' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                              breach.severity === 'moderate' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                              "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                            )}>
                              {breach.severity}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            {breach.current_value} / {breach.limit_value} ({breach.breach_percentage}%)
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12">
                <ShieldCheckIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Risk Limits Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Configure and monitor risk limits</p>
                <button
                  onClick={fetchRiskLimits}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Load Risk Limits
                </button>
              </div>
            )}
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Risk Alerts</h3>
              
              {riskAlerts.length > 0 ? (
                <div className="space-y-3">
                  {(riskAlerts ?? []).map((alert, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="flex items-center space-x-3">
                        <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{alert.title}</div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">{alert.message}</div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(alert.timestamp).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BellIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500 dark:text-gray-400">No active risk alerts</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Risk Reports</h3>
              
              {riskReports.length > 0 ? (
                <div className="space-y-3">
                  {(riskReports ?? []).map((report, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="flex items-center space-x-3">
                        <DocumentTextIcon className="h-5 w-5 text-blue-500" />
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{report.name}</div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">{report.description}</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {new Date(report.created_at).toLocaleDateString()}
                        </span>
                        <button className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                          <DocumentArrowDownIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <DocumentTextIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500 dark:text-gray-400">No risk reports available</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskManagementDashboard;
