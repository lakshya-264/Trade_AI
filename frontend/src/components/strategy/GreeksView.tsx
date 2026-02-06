/**
 * Greeks View Component
 * Displays Delta, Theta, Gamma, Vega for each leg and total
 */

import React from 'react';
import { StrategyLeg, StrategyMetrics } from './StrategyBuilder';
import { HelpCircle } from 'lucide-react';

interface GreeksViewProps {
  legs: StrategyLeg[];
  metrics: StrategyMetrics | null;
  multiplyByLotSize: boolean;
  multiplyByLots: boolean;
  onToggleLotSize: () => void;
  onToggleLots: () => void;
}

const GreeksView: React.FC<GreeksViewProps> = ({
  legs,
  metrics,
  multiplyByLotSize,
  multiplyByLots,
  onToggleLotSize,
  onToggleLots
}) => {
  const getMultiplier = (leg: StrategyLeg): number => {
    let multiplier = 1;
    if (multiplyByLotSize) {
      multiplier *= (leg.lotSize || 50);
    }
    if (multiplyByLots) {
      multiplier *= leg.quantity;
    }
    return multiplier;
  };

  const formatGreek = (value: number, leg: StrategyLeg): string => {
    const mult = getMultiplier(leg);
    const result = value * mult;
    if (Math.abs(result) < 0.01) return '0.00';
    return result.toFixed(2);
  };

  const formatTotalGreek = (value: number): string => {
    if (Math.abs(value) < 0.01) return '0.00';
    return value.toFixed(2);
  };

  if (legs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <div className="text-center">
          <p className="text-lg mb-2">No strategy legs added</p>
          <p className="text-sm">Add legs to see Greeks</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Toggle Controls */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={multiplyByLotSize}
              onChange={onToggleLotSize}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-700">Multiply by Lot Size</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={multiplyByLots}
              onChange={onToggleLots}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-700">Multiply by Number of Lots</span>
          </label>
        </div>
      </div>

      {/* Greeks Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Instrument
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Delta
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Theta
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Decay
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Gamma
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Vega
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {legs.map((leg, idx) => {
                const legGreeks = metrics?.greeks ? {
                  delta: (metrics.greeks.delta / legs.length) * (leg.action === 'BUY' ? 1 : -1),
                  theta: (metrics.greeks.theta / legs.length) * (leg.action === 'BUY' ? 1 : -1),
                  gamma: (metrics.greeks.gamma / legs.length),
                  vega: (metrics.greeks.vega / legs.length)
                } : {
                  delta: 0,
                  theta: 0,
                  gamma: 0,
                  vega: 0
                };

                return (
                  <tr key={leg.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                      <span className={`px-2 py-1 rounded text-xs mr-2 ${
                        leg.action === 'BUY' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {leg.action}
                      </span>
                      {leg.quantity} x {leg.expiry} {leg.strike} {leg.instrument}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatGreek(legGreeks.delta, leg)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatGreek(legGreeks.theta, leg)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatGreek(legGreeks.theta, leg)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                      {legGreeks.gamma === 0 ? '--' : formatGreek(legGreeks.gamma, leg)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatGreek(legGreeks.vega, leg)}
                    </td>
                  </tr>
                );
              })}
              {metrics?.greeks && (
                <tr className="bg-gray-50 font-semibold">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                    Total
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                    {formatTotalGreek(metrics.greeks.delta)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                    {formatTotalGreek(metrics.greeks.theta)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                    {formatTotalGreek(metrics.greeks.theta)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                    {formatTotalGreek(metrics.greeks.gamma)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                    {formatTotalGreek(metrics.greeks.vega)}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Additional Info */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <div className="flex items-start gap-2">
          <HelpCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">About Greeks:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li><strong>Delta:</strong> Price sensitivity to underlying price change</li>
              <li><strong>Theta:</strong> Time decay per day</li>
              <li><strong>Gamma:</strong> Rate of change of delta</li>
              <li><strong>Vega:</strong> Sensitivity to volatility changes</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GreeksView;

