/**
 * Strategy Cockpit Component
 * Dashboard view showing key strategy metrics and Greeks
 */

import React from 'react';
import { 
  TrendingUp, TrendingDown, Target, AlertCircle, 
  DollarSign, Shield, BarChart3, Calculator
} from 'lucide-react';
import { Strategy, StrategyMetrics } from './StrategyBuilder';

interface StrategyCockpitProps {
  strategy: Strategy;
  metrics: StrategyMetrics | null;
  currentPrice: number;
  loading: boolean;
  onPriceChange: (price: number) => void;
}

const StrategyCockpit: React.FC<StrategyCockpitProps> = ({
  strategy,
  metrics,
  currentPrice,
  loading,
  onPriceChange
}) => {
  const calculateCurrentPnl = () => {
    if (!metrics || strategy.legs.length === 0) return 0;

    // Simplified current P&L calculation
    let pnl = 0;
    strategy.legs.forEach(leg => {
      const multiplier = leg.lotSize || 50;
      const totalQuantity = leg.quantity * multiplier;

      if (leg.instrument === 'CE') {
        const intrinsicValue = Math.max(0, currentPrice - leg.strike);
        if (leg.action === 'BUY') {
          pnl += (intrinsicValue - leg.price) * totalQuantity;
        } else {
          pnl += (leg.price - intrinsicValue) * totalQuantity;
        }
      } else if (leg.instrument === 'PE') {
        const intrinsicValue = Math.max(0, leg.strike - currentPrice);
        if (leg.action === 'BUY') {
          pnl += (intrinsicValue - leg.price) * totalQuantity;
        } else {
          pnl += (leg.price - intrinsicValue) * totalQuantity;
        }
      } else if (leg.instrument === 'FUT') {
        const pnlPerUnit = currentPrice - leg.price;
        if (leg.action === 'BUY') {
          pnl += pnlPerUnit * totalQuantity;
        } else {
          pnl -= pnlPerUnit * totalQuantity;
        }
      }
    });

    return pnl;
  };

  const currentPnl = calculateCurrentPnl();
  const pnlPercentage = metrics ? (currentPnl / Math.abs(metrics.totalPremium || 1)) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Current Price Input */}
      <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
        <label className="block text-sm text-gray-400 mb-2">Current Underlying Price</label>
        <input
          type="number"
          value={currentPrice}
          onChange={(e) => onPriceChange(parseFloat(e.target.value) || 0)}
          className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded text-white text-lg font-semibold"
          step="0.01"
        />
      </div>

      {/* Current P&L */}
      <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Current P&L</span>
          <span className={`text-2xl font-bold ${currentPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {currentPnl >= 0 ? '+' : ''}₹{(currentPnl / 100000).toFixed(2)}L
          </span>
        </div>
        <div className={`text-sm ${pnlPercentage >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {pnlPercentage >= 0 ? '+' : ''}{pnlPercentage.toFixed(2)}%
        </div>
      </div>

      {loading ? (
        <div className="bg-[#1a1d28] rounded-lg p-8 border border-gray-700 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
          <p className="mt-2 text-gray-400">Calculating metrics...</p>
        </div>
      ) : metrics ? (
        <>
          {/* Max Profit & Loss */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-green-400" />
                <span className="text-sm text-gray-400">Max Profit</span>
              </div>
              <div className="text-xl font-bold text-green-400">
                ₹{(metrics.maxProfit / 100000).toFixed(2)}L
              </div>
            </div>
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown className="w-4 h-4 text-red-400" />
                <span className="text-sm text-gray-400">Max Loss</span>
              </div>
              <div className="text-xl font-bold text-red-400">
                ₹{(Math.abs(metrics.maxLoss) / 100000).toFixed(2)}L
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Key Metrics
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-400">Reward/Risk Ratio</span>
                <span className="text-sm font-medium">
                  {metrics.rewardRiskRatio > 0 ? '1:' : ''}{metrics.rewardRiskRatio.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-400">Probability of Profit</span>
                <span className="text-sm font-medium text-green-400">
                  {metrics.probabilityOfProfit.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-400">Total Premium</span>
                <span className="text-sm font-medium">
                  ₹{(metrics.totalPremium / 100000).toFixed(2)}L
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-400">Margin Required</span>
                <span className="text-sm font-medium">
                  ₹{(metrics.marginRequired / 100000).toFixed(2)}L
                </span>
              </div>
            </div>
          </div>

          {/* Breakeven Points */}
          {metrics.breakevenPoints.length > 0 && (
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Target className="w-4 h-4" />
                Breakeven Points
              </h4>
              <div className="space-y-1">
                {metrics.breakevenPoints.map((be, idx) => (
                  <div key={idx} className="flex justify-between">
                    <span className="text-sm text-gray-400">BE {idx + 1}</span>
                    <span className="text-sm font-medium">₹{be.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Greeks */}
          {metrics.greeks && (
            <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
              <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Calculator className="w-4 h-4" />
                Greeks
              </h4>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-xs text-gray-400">Delta</span>
                  <div className="text-sm font-medium">{metrics.greeks.delta.toFixed(4)}</div>
                </div>
                <div>
                  <span className="text-xs text-gray-400">Gamma</span>
                  <div className="text-sm font-medium">{metrics.greeks.gamma.toFixed(4)}</div>
                </div>
                <div>
                  <span className="text-xs text-gray-400">Theta</span>
                  <div className="text-sm font-medium text-red-400">{metrics.greeks.theta.toFixed(2)}</div>
                </div>
                <div>
                  <span className="text-xs text-gray-400">Vega</span>
                  <div className="text-sm font-medium">{metrics.greeks.vega.toFixed(2)}</div>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-[#1a1d28] rounded-lg p-8 border border-gray-700 text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-2 text-gray-500" />
          <p className="text-gray-400">Add legs to see strategy metrics</p>
        </div>
      )}
    </div>
  );
};

export default StrategyCockpit;

