/**
 * Central Pivot Range (CPR) Module
 * CPR calculation, education, and chart overlay
 */

import React, { useState } from 'react';
import { httpClient } from '../../config/api';
import { CalculatorIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

interface CPRResult {
  pivot_point?: number;
  cpr_top?: number;
  cpr_bottom?: number;
  cpr_width?: number;
}

const CPRModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'education' | 'calculator'>('education');
  const [high, setHigh] = useState('');
  const [low, setLow] = useState('');
  const [close, setClose] = useState('');
  const [cpr, setCpr] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const calculateCPR = async () => {
    try {
      if (!high || !low || !close) {
        toast.error('Please enter High, Low, and Close prices');
        return;
      }

      setLoading(true);
      const response = await httpClient.post<{ cpr?: CPRResult }>(
        '/api/market-education/cpr/calculate',
        {
        high: parseFloat(high),
        low: parseFloat(low),
        close: parseFloat(close)
        }
      );

      if (response.success) {
        const cprResult = response.data?.cpr ?? response.data;
        if (cprResult) {
          setCpr(cprResult);
        }
        toast.success('CPR calculated');
      }
    } catch (error: any) {
      toast.error('Failed to calculate CPR');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <ChartBarIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Central Pivot Range (CPR)</h2>
            <p className="text-gray-600 dark:text-gray-400">Calculate and understand CPR for trading</p>
          </div>
        </div>
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-1 px-6">
          <button
            onClick={() => setActiveTab('education')}
            className={`px-4 py-3 font-medium text-sm border-b-2 ${
              activeTab === 'education'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400'
            }`}
          >
            Education
          </button>
          <button
            onClick={() => setActiveTab('calculator')}
            className={`px-4 py-3 font-medium text-sm border-b-2 ${
              activeTab === 'calculator'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400'
            }`}
          >
            Calculator
          </button>
        </div>
      </div>

      <div className="p-6">
        {activeTab === 'calculator' && (
          <div className="max-w-md mx-auto">
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  High Price (₹)
                </label>
                <input
                  type="number"
                  value={high}
                  onChange={(e) => setHigh(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Low Price (₹)
                </label>
                <input
                  type="number"
                  value={low}
                  onChange={(e) => setLow(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Close Price (₹)
                </label>
                <input
                  type="number"
                  value={close}
                  onChange={(e) => setClose(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
            <button
              onClick={calculateCPR}
              disabled={loading}
              className="w-full px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
            >
              Calculate CPR
            </button>

            {cpr && (
              <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">CPR Levels:</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Pivot Point (PP):</span>
                    <span className="font-semibold text-gray-900 dark:text-white">₹{cpr.pivot_point?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Central Pivot Range (CPR):</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      ₹{cpr.cpr_top?.toFixed(2)} - ₹{cpr.cpr_bottom?.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">CPR Width:</span>
                    <span className="font-semibold text-gray-900 dark:text-white">₹{cpr.cpr_width?.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'education' && (
          <div className="prose dark:prose-invert max-w-none">
            <p className="text-gray-700 dark:text-gray-300">
              Central Pivot Range (CPR) is a key technical indicator used by traders to identify potential support and resistance levels.
              It's calculated using the previous day's high, low, and close prices.
            </p>
            <p className="text-gray-700 dark:text-gray-300 mt-4">
              CPR helps traders understand where price might find support or resistance during the trading day.
              When price is above CPR, it's considered bullish. When below, it's bearish.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CPRModule;

