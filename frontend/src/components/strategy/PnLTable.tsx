/**
 * P&L Table Component
 * Shows profit/loss at different price points
 */

import React, { useMemo } from 'react';
import { StrategyLeg, StrategyMetrics } from './StrategyBuilder';

interface PnLTableProps {
  legs: StrategyLeg[];
  currentPrice: number;
  metrics: StrategyMetrics | null;
}

const PnLTable: React.FC<PnLTableProps> = ({ legs, currentPrice, metrics }) => {
  const tableData = useMemo(() => {
    if (legs.length === 0) return [];

    const minStrike = Math.min(...legs.map(l => l.strike));
    const maxStrike = Math.max(...legs.map(l => l.strike));
    const priceRange = maxStrike - minStrike;
    const startPrice = Math.max(0, minStrike - priceRange * 0.3);
    const endPrice = maxStrike + priceRange * 0.3;
    const step = (endPrice - startPrice) / 20; // 20 data points

    const data = [];
    for (let price = startPrice; price <= endPrice; price += step) {
      let totalPayoff = 0;

      legs.forEach(leg => {
        let legPayoff = 0;
        const multiplier = leg.lotSize || 50;
        const totalQuantity = leg.quantity * multiplier;

        if (leg.instrument === 'CE') {
          const intrinsicValue = Math.max(0, price - leg.strike);
          if (leg.action === 'BUY') {
            legPayoff = (intrinsicValue - leg.price) * totalQuantity;
          } else {
            legPayoff = (leg.price - intrinsicValue) * totalQuantity;
          }
        } else if (leg.instrument === 'PE') {
          const intrinsicValue = Math.max(0, leg.strike - price);
          if (leg.action === 'BUY') {
            legPayoff = (intrinsicValue - leg.price) * totalQuantity;
          } else {
            legPayoff = (leg.price - intrinsicValue) * totalQuantity;
          }
        } else if (leg.instrument === 'FUT') {
          const pnl = price - leg.price;
          if (leg.action === 'BUY') {
            legPayoff = pnl * totalQuantity;
          } else {
            legPayoff = -pnl * totalQuantity;
          }
        }

        totalPayoff += legPayoff;
      });

      data.push({
        price: Math.round(price),
        pnl: totalPayoff,
        pnlPercentage: metrics?.totalPremium ? (totalPayoff / Math.abs(metrics.totalPremium)) * 100 : 0
      });
    }

    return data;
  }, [legs, metrics]);

  if (legs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <div className="text-center">
          <p className="text-lg mb-2">No strategy legs added</p>
          <p className="text-sm">Add legs to see P&L table</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                  P&L %
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tableData.map((row, idx) => (
                <tr
                  key={idx}
                  className={`hover:bg-gray-50 ${
                    Math.abs(row.price - currentPrice) < 10 ? 'bg-blue-50' : ''
                  }`}
                >
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                    ₹{row.price.toLocaleString()}
                    {Math.abs(row.price - currentPrice) < 10 && (
                      <span className="ml-2 text-xs text-blue-600">(Current)</span>
                    )}
                  </td>
                  <td className={`px-4 py-3 whitespace-nowrap text-sm text-right font-medium ${
                    row.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {row.pnl >= 0 ? '+' : ''}₹{row.pnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </td>
                  <td className={`px-4 py-3 whitespace-nowrap text-sm text-right ${
                    row.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {row.pnlPercentage >= 0 ? '+' : ''}{row.pnlPercentage.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PnLTable;

