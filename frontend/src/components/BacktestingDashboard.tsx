/**
 * Backtesting Dashboard Component
 * Run backtests and view historical strategy performance
 */

import React, { useState, useEffect } from 'react';
import { backtestingApi, BacktestRequest, BacktestResponse, BacktestMetrics, Trade } from '../services/backtestingApi';
import { TrendingUp, TrendingDown, Activity, DollarSign, Target, BarChart3, Play, Loader2 } from 'lucide-react';

interface BacktestingDashboardProps {
  symbol: string;
  className?: string;
}

export const BacktestingDashboard: React.FC<BacktestingDashboardProps> = ({
  symbol,
  className = '',
}) => {
  const [strategyType, setStrategyType] = useState<'sd_zones' | 'sr_levels' | 'structure_breaks'>('sd_zones');
  const [entryThreshold, setEntryThreshold] = useState(0.5);
  const [stopLoss, setStopLoss] = useState(2.0);
  const [takeProfit, setTakeProfit] = useState(4.0);
  
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<BacktestResponse | null>(null);
  const [zoneSuccess, setZoneSuccess] = useState<any>(null);

  const handleRunBacktest = async () => {
    setRunning(true);
    setResults(null);

    try {
      const request: BacktestRequest = {
        symbol,
        strategy_type: strategyType,
        entry_threshold: entryThreshold,
        stop_loss: stopLoss,
        take_profit: takeProfit,
      };

      const response = await backtestingApi.runBacktest(request);
      console.log('Backtest Response:', response);
      setResults(response);

      // Also fetch zone success rate
      if (strategyType === 'sd_zones') {
        const zoneResponse = await backtestingApi.calculateZoneSuccessRate(symbol);
        console.log('Zone Success Response:', zoneResponse);
        if (zoneResponse.success) {
          setZoneSuccess(zoneResponse.results);
        }
      }
    } catch (error) {
      console.error('Backtest failed:', error);
      window.alert('Failed to run backtest. Please try again.');
    } finally {
      setRunning(false);
    }
  };

  const renderMetricCard = (
    title: string,
    value: string | number,
    subtitle?: string,
    icon?: React.ReactNode,
    colorClass: string = 'text-white'
  ) => (
    <div className="bg-[#131722] rounded-lg p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">{title}</span>
        {icon}
      </div>
      <div className={`text-2xl font-bold ${colorClass}`}>{value}</div>
      {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
  );

  const getWinRateColor = (winRate: number): string => {
    if (winRate >= 60) return 'text-green-400';
    if (winRate >= 45) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getProfitFactorColor = (pf: number): string => {
    if (pf >= 2) return 'text-green-400';
    if (pf >= 1) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className={`bg-[#1E222D] rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <BarChart3 className="w-6 h-6 text-purple-400" />
        <h2 className="text-xl font-bold text-white">Backtesting Dashboard</h2>
      </div>

      {/* Configuration Panel */}
      <div className="bg-[#131722] rounded-lg p-4 mb-6 border border-gray-700">
        <h3 className="text-white font-medium mb-4">Configuration</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Strategy Type */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Strategy</label>
            <select
              value={strategyType}
              onChange={(e) => setStrategyType(e.target.value as any)}
              className="w-full px-3 py-2 bg-[#1E222D] text-white rounded border border-gray-700 focus:border-blue-500 focus:outline-none"
            >
              <option value="sd_zones">Supply & Demand Zones</option>
              <option value="sr_levels">Support & Resistance</option>
              <option value="structure_breaks">Structure Breaks (BOS/CHoCH)</option>
            </select>
          </div>

          {/* Entry Threshold */}
          {strategyType !== 'structure_breaks' && (
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Entry Threshold: {entryThreshold}%
              </label>
              <input
                type="range"
                min="0.1"
                max="2"
                step="0.1"
                value={entryThreshold}
                onChange={(e) => setEntryThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          )}

          {/* Stop Loss */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Stop Loss: {stopLoss}%
            </label>
            <input
              type="range"
              min="0.5"
              max="5"
              step="0.5"
              value={stopLoss}
              onChange={(e) => setStopLoss(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Take Profit */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Take Profit: {takeProfit}%
            </label>
            <input
              type="range"
              min="1"
              max="10"
              step="0.5"
              value={takeProfit}
              onChange={(e) => setTakeProfit(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        {/* Run Button */}
        <button
          onClick={handleRunBacktest}
          disabled={running}
          className={`mt-4 w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
            running
              ? 'bg-gray-600 cursor-not-allowed'
              : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white'
          }`}
        >
          {running ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Running Backtest...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Run Backtest on {symbol}
            </>
          )}
        </button>
      </div>

      {/* Results Section */}
      {results && results.success && results.metrics && (
        <div className="space-y-6">
          {/* Key Metrics Grid */}
          <div>
            <h3 className="text-white font-medium mb-3">Performance Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {renderMetricCard(
                'Total Trades',
                results.metrics.total_trades,
                `${results.metrics.winning_trades}W / ${results.metrics.losing_trades}L`,
                <Activity className="w-5 h-5 text-blue-400" />,
                'text-white'
              )}

              {renderMetricCard(
                'Win Rate',
                `${results.metrics.win_rate}%`,
                results.metrics.win_rate >= 50 ? 'Profitable' : 'Needs improvement',
                <Target className="w-5 h-5 text-green-400" />,
                getWinRateColor(results.metrics.win_rate)
              )}

              {renderMetricCard(
                'Profit Factor',
                results.metrics.profit_factor.toFixed(2),
                results.metrics.profit_factor >= 1 ? 'Positive' : 'Negative',
                <TrendingUp className="w-5 h-5 text-purple-400" />,
                getProfitFactorColor(results.metrics.profit_factor)
              )}

              {renderMetricCard(
                'Total Return',
                `${results.metrics.total_return_percent >= 0 ? '+' : ''}${results.metrics.total_return_percent}%`,
                `₹${results.metrics.final_capital.toLocaleString()}`,
                <DollarSign className="w-5 h-5 text-yellow-400" />,
                results.metrics.total_return_percent >= 0 ? 'text-green-400' : 'text-red-400'
              )}

              {renderMetricCard(
                'Avg Win',
                `+${results.metrics.avg_win}%`,
                'Per winning trade',
                undefined,
                'text-green-400'
              )}

              {renderMetricCard(
                'Avg Loss',
                `-${results.metrics.avg_loss}%`,
                'Per losing trade',
                undefined,
                'text-red-400'
              )}
            </div>
          </div>

          {/* Advanced Risk Metrics */}
          <div>
            <h3 className="text-white font-medium mb-3">📉 Risk & Drawdown Analysis</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {renderMetricCard(
                'Max Drawdown',
                `${results.metrics.max_drawdown}%`,
                'Largest decline',
                <TrendingDown className="w-5 h-5 text-red-400" />,
                results.metrics.max_drawdown > 20 ? 'text-red-400' : results.metrics.max_drawdown > 10 ? 'text-yellow-400' : 'text-green-400'
              )}

              {renderMetricCard(
                'Avg Drawdown',
                `${results.metrics.avg_drawdown}%`,
                'Average decline',
                undefined,
                'text-orange-400'
              )}

              {renderMetricCard(
                'Sharpe Ratio',
                results.metrics.sharpe_ratio.toFixed(2),
                results.metrics.sharpe_ratio >= 1 ? 'Excellent' : results.metrics.sharpe_ratio >= 0.5 ? 'Good' : 'Poor',
                <Activity className="w-5 h-5 text-blue-400" />,
                results.metrics.sharpe_ratio >= 1 ? 'text-green-400' : results.metrics.sharpe_ratio >= 0.5 ? 'text-yellow-400' : 'text-red-400'
              )}

              {renderMetricCard(
                'Sortino Ratio',
                results.metrics.sortino_ratio.toFixed(2),
                'Downside risk-adjusted',
                undefined,
                results.metrics.sortino_ratio >= 1 ? 'text-green-400' : results.metrics.sortino_ratio >= 0.5 ? 'text-yellow-400' : 'text-red-400'
              )}
            </div>
          </div>

          {/* Additional Advanced Metrics */}
          <div>
            <h3 className="text-white font-medium mb-3">🎯 Advanced Performance Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {renderMetricCard(
                'Calmar Ratio',
                results.metrics.calmar_ratio.toFixed(2),
                'Return / Max DD',
                undefined,
                results.metrics.calmar_ratio >= 3 ? 'text-green-400' : results.metrics.calmar_ratio >= 1 ? 'text-yellow-400' : 'text-red-400'
              )}

              {renderMetricCard(
                'Expectancy',
                `${results.metrics.expectancy >= 0 ? '+' : ''}${results.metrics.expectancy.toFixed(2)}%`,
                'Expected $ per trade',
                <Target className="w-5 h-5 text-purple-400" />,
                results.metrics.expectancy >= 0 ? 'text-green-400' : 'text-red-400'
              )}

              {renderMetricCard(
                'Recovery Factor',
                results.metrics.recovery_factor.toFixed(2),
                'Profit / Max DD',
                undefined,
                results.metrics.recovery_factor >= 2 ? 'text-green-400' : results.metrics.recovery_factor >= 1 ? 'text-yellow-400' : 'text-red-400'
              )}
            </div>
          </div>

          {/* Risk Interpretation Guide */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <h4 className="text-blue-400 font-medium mb-2">📊 Metric Interpretation Guide</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-300">
              <div>
                <p className="font-medium text-white mb-1">Sharpe Ratio:</p>
                <p className="text-xs text-gray-400">
                  &gt;1.0: Excellent | 0.5-1.0: Good | &lt;0.5: Poor
                </p>
              </div>
              <div>
                <p className="font-medium text-white mb-1">Calmar Ratio:</p>
                <p className="text-xs text-gray-400">
                  &gt;3.0: Excellent | 1.0-3.0: Good | &lt;1.0: Risky
                </p>
              </div>
              <div>
                <p className="font-medium text-white mb-1">Max Drawdown:</p>
                <p className="text-xs text-gray-400">
                  &lt;10%: Low Risk | 10-20%: Medium | &gt;20%: High Risk
                </p>
              </div>
              <div>
                <p className="font-medium text-white mb-1">Recovery Factor:</p>
                <p className="text-xs text-gray-400">
                  &gt;2.0: Strong | 1.0-2.0: Fair | &lt;1.0: Weak
                </p>
              </div>
            </div>
          </div>

          {/* Zone Success Rate (if available) */}
          {zoneSuccess && (
            <div>
              <h3 className="text-white font-medium mb-3">Zone Success Rate Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {renderMetricCard(
                  'Demand Zone Bounce Rate',
                  `${zoneSuccess.demand_zones.success_rate}%`,
                  `${zoneSuccess.demand_zones.successful_bounces}/${zoneSuccess.demand_zones.total_touches} touches`,
                  <TrendingUp className="w-5 h-5 text-green-400" />,
                  getWinRateColor(zoneSuccess.demand_zones.success_rate)
                )}

                {renderMetricCard(
                  'Supply Zone Rejection Rate',
                  `${zoneSuccess.supply_zones.success_rate}%`,
                  `${zoneSuccess.supply_zones.successful_rejections}/${zoneSuccess.supply_zones.total_touches} touches`,
                  <TrendingDown className="w-5 h-5 text-red-400" />,
                  getWinRateColor(zoneSuccess.supply_zones.success_rate)
                )}

                {renderMetricCard(
                  'Overall Success Rate',
                  `${zoneSuccess.overall_success_rate}%`,
                  'Combined performance',
                  <Activity className="w-5 h-5 text-purple-400" />,
                  getWinRateColor(zoneSuccess.overall_success_rate)
                )}
              </div>
            </div>
          )}

          {/* Recent Trades Table */}
          {results.trades && results.trades.length > 0 && (
            <div>
              <h3 className="text-white font-medium mb-3">Recent Trades (Last 10)</h3>
              <div className="bg-[#131722] rounded-lg border border-gray-700 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-[#1E222D]">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Direction</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Entry</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Exit</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">P&L</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                      {results.trades.slice(0, 10).map((trade, idx) => (
                        <tr key={idx} className="hover:bg-[#1E222D]/50">
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              trade.direction === 'long' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                            }`}>
                              {trade.direction === 'long' ? '↑ LONG' : '↓ SHORT'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-300">₹{trade.entry_price.toFixed(2)}</td>
                          <td className="px-4 py-3 text-sm text-gray-300">₹{trade.exit_price.toFixed(2)}</td>
                          <td className="px-4 py-3">
                            <span className={`text-sm font-medium ${trade.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              trade.result === 'win' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                            }`}>
                              {trade.result.toUpperCase()}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Equity Curve (Simple) */}
          {results.equity_curve && results.equity_curve.length > 0 && (
            <div>
              <h3 className="text-white font-medium mb-3">Equity Curve</h3>
              <div className="bg-[#131722] rounded-lg p-4 border border-gray-700">
                <div className="h-48 flex items-end justify-between gap-1">
                  {results.equity_curve.map((point, idx) => {
                    const maxEquity = Math.max(...results.equity_curve!.map((p) => p.equity));
                    const minEquity = Math.min(...results.equity_curve!.map((p) => p.equity));
                    const range = maxEquity - minEquity;
                    const heightPercent = range > 0 ? ((point.equity - minEquity) / range) * 100 : 50;

                    return (
                      <div
                        key={idx}
                        className="flex-1 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t"
                        style={{ height: `${Math.max(heightPercent, 2)}%` }}
                        title={`₹${point.equity.toLocaleString()}`}
                      />
                    );
                  })}
                </div>
                <div className="flex justify-between mt-2 text-xs text-gray-400">
                  <span>Start</span>
                  <span>End: ₹{results.equity_curve[results.equity_curve.length - 1].equity.toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Trades Warning */}
      {results && results.success && results.metrics && results.metrics.total_trades === 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-6 text-center">
          <div className="text-yellow-400 text-5xl mb-4">⚠️</div>
          <h3 className="text-xl font-bold text-yellow-400 mb-2">No Trades Found</h3>
          <p className="text-gray-300 mb-4">
            The backtest completed successfully but found 0 trades for {symbol}.
          </p>
          <div className="text-left bg-[#131722] rounded-lg p-4 mb-4">
            <p className="text-sm text-gray-400 mb-2">Possible reasons:</p>
            <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
              <li>No {strategyType === 'sd_zones' ? 'Supply/Demand zones' : strategyType === 'sr_levels' ? 'Support/Resistance levels' : 'structure breaks'} detected in historical data</li>
              <li>Entry threshold ({entryThreshold}%) might be too strict</li>
              <li>Price never approached the detected zones/levels</li>
              <li>Try adjusting parameters or selecting a different stock</li>
            </ul>
          </div>
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => {
                setEntryThreshold(1.0);
                setStopLoss(3.0);
                setTakeProfit(6.0);
              }}
              className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm transition-colors"
            >
              Try Relaxed Parameters (1% / 3% / 6%)
            </button>
            <button
              onClick={() => setResults(null)}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm transition-colors"
            >
              Clear Results
            </button>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!results && !running && (
        <div className="text-center py-12 text-gray-400">
          <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg">Configure your backtest parameters and click "Run Backtest"</p>
          <p className="text-sm mt-2">Test historical performance of trading strategies</p>
        </div>
      )}
    </div>
  );
};

