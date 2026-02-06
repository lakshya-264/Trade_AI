/**
 * Clearing & Settlement Education Module
 * T+1 settlement, pay-in/pay-out process
 */

import React, { useState } from 'react';
import { httpClient } from '../../config/api';
import { DocumentTextIcon, CalculatorIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const ClearingSettlementModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'education' | 'calculator'>('education');
  const [tradeDate, setTradeDate] = useState('');
  const [settlementDays, setSettlementDays] = useState('1');
  const [settlementResult, setSettlementResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const calculateSettlementDate = async () => {
    try {
      if (!tradeDate) {
        toast.error('Please enter trade date');
        return;
      }

      setLoading(true);
      const response = await httpClient.post(
        `/api/market-education/settlement/calculate-date?trade_date=${tradeDate}&settlement_days=${settlementDays}`
      );

      if (response.success) {
        setSettlementResult(response.data);
        toast.success('Settlement date calculated');
      }
    } catch (error: any) {
      toast.error('Failed to calculate settlement date');
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
            <DocumentTextIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Clearing & Settlement</h2>
            <p className="text-gray-600 dark:text-gray-400">T+1 settlement, pay-in/pay-out process</p>
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
            Settlement Calculator
          </button>
        </div>
      </div>

      <div className="p-6">
        {activeTab === 'education' && (
          <div className="space-y-6 prose dark:prose-invert max-w-none">
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                T+1 Settlement System
              </h3>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                India follows a T+1 settlement cycle, meaning trades are settled one business day after the trade date.
              </p>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Process:</h4>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                    <li>T Day: Trade executed</li>
                    <li>T+1 Day: Settlement (funds and securities exchange hands)</li>
                    <li>Pay-in: Funds/securities must be available by T+1</li>
                    <li>Pay-out: Funds/securities credited to your account on T+1</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Important Points:</h4>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                    <li>Ensure sufficient funds/securities before T+1</li>
                    <li>Failure to deliver results in penalties</li>
                    <li>Holidays are excluded from settlement days</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'calculator' && (
          <div className="max-w-md mx-auto">
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Trade Date
                </label>
                <input
                  type="date"
                  value={tradeDate}
                  onChange={(e) => setTradeDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Settlement Days (default: 1 for T+1)
                </label>
                <input
                  type="number"
                  value={settlementDays}
                  onChange={(e) => setSettlementDays(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  min="1"
                />
              </div>
            </div>
            <button
              onClick={calculateSettlementDate}
              disabled={loading}
              className="w-full px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
            >
              Calculate Settlement Date
            </button>

            {settlementResult && (
              <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Settlement Date:</h4>
                <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                  {settlementResult.settlement_date || settlementResult.date || 'N/A'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClearingSettlementModule;
