/**
 * Corporate Actions Education Module
 * Dividends, splits, bonus, rights with impact calculators
 */

import React, { useState, useEffect } from 'react';
import { httpClient } from '../../config/api';
import { CalculatorIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const CorporateActionsModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'education' | 'calculators'>('education');
  const [activeCalculator, setActiveCalculator] = useState<'dividend' | 'split' | 'bonus' | 'rights'>('dividend');
  const [corporateActionsInfo, setCorporateActionsInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Calculator states
  const [currentPrice, setCurrentPrice] = useState('');
  const [sharesHeld, setSharesHeld] = useState('');
  const [dividendPerShare, setDividendPerShare] = useState('');
  const [splitRatio, setSplitRatio] = useState('');
  const [bonusRatio, setBonusRatio] = useState('');
  const [rightsRatio, setRightsRatio] = useState('');
  const [rightsPrice, setRightsPrice] = useState('');
  const [calculationResult, setCalculationResult] = useState<any>(null);

  useEffect(() => {
    if (activeTab === 'education') {
      loadCorporateActionsInfo();
    }
  }, [activeTab]);

  const loadCorporateActionsInfo = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/market-education/corporate-actions/info');
      if (response.success) {
        const data: any = response.data;
        setCorporateActionsInfo(data?.actions ?? data ?? null);
      }
    } catch (error: any) {
      toast.error('Failed to load corporate actions information');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateImpact = async () => {
    try {
      if (!currentPrice || !sharesHeld) {
        toast.error('Please enter current price and shares held');
        return;
      }

      setLoading(true);
      let response;

      if (activeCalculator === 'dividend') {
        if (!dividendPerShare) {
          toast.error('Please enter dividend per share');
          return;
        }
        response = await httpClient.post(
          `/api/market-education/corporate-actions/calculate-dividend-impact?current_price=${currentPrice}&dividend_per_share=${dividendPerShare}&shares_held=${sharesHeld}`
        );
      } else if (activeCalculator === 'split') {
        if (!splitRatio) {
          toast.error('Please enter split ratio (e.g., 2:1)');
          return;
        }
        response = await httpClient.post(
          `/api/market-education/corporate-actions/calculate-split-impact?current_price=${currentPrice}&split_ratio=${splitRatio}&shares_held=${sharesHeld}`
        );
      } else if (activeCalculator === 'bonus') {
        if (!bonusRatio) {
          toast.error('Please enter bonus ratio (e.g., 1:2)');
          return;
        }
        response = await httpClient.post(
          `/api/market-education/corporate-actions/calculate-bonus-impact?current_price=${currentPrice}&bonus_ratio=${bonusRatio}&shares_held=${sharesHeld}`
        );
      } else if (activeCalculator === 'rights') {
        if (!rightsRatio || !rightsPrice) {
          toast.error('Please enter rights ratio and rights price');
          return;
        }
        response = await httpClient.post(
          `/api/market-education/corporate-actions/calculate-rights-impact?current_price=${currentPrice}&rights_ratio=${rightsRatio}&rights_price=${rightsPrice}&shares_held=${sharesHeld}`
        );
      }

      if (response?.success) {
        const data: any = response.data;
        setCalculationResult(data?.impact ?? data ?? null);
        toast.success('Impact calculated successfully');
      }
    } catch (error: any) {
      toast.error('Failed to calculate impact');
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
            <CalculatorIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Corporate Actions</h2>
            <p className="text-gray-600 dark:text-gray-400">Dividends, splits, bonus, rights with impact calculators</p>
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
            onClick={() => setActiveTab('calculators')}
            className={`px-4 py-3 font-medium text-sm border-b-2 ${
              activeTab === 'calculators'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400'
            }`}
          >
            Calculators
          </button>
        </div>
      </div>

      <div className="p-6">
        {activeTab === 'education' && (
          <div className="space-y-6">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
              </div>
            ) : corporateActionsInfo ? (
              Object.entries(corporateActionsInfo).map(([key, action]: [string, any]) => (
                <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                    {action.name || key}
                  </h3>
                  {action.description && (
                    <p className="text-gray-700 dark:text-gray-300 mb-4">{action.description}</p>
                  )}
                  {action.impact && (
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Impact:</h4>
                      <p className="text-gray-700 dark:text-gray-300">{action.impact}</p>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-gray-500">No information available</div>
            )}
          </div>
        )}

        {activeTab === 'calculators' && (
          <div className="max-w-2xl mx-auto">
            {/* Calculator Type Selector */}
            <div className="grid grid-cols-4 gap-2 mb-6">
              {[
                { id: 'dividend', label: 'Dividend' },
                { id: 'split', label: 'Split' },
                { id: 'bonus', label: 'Bonus' },
                { id: 'rights', label: 'Rights' }
              ].map((calc) => (
                <button
                  key={calc.id}
                  onClick={() => {
                    setActiveCalculator(calc.id as any);
                    setCalculationResult(null);
                  }}
                  className={`px-4 py-2 rounded-lg font-medium ${
                    activeCalculator === calc.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  {calc.label}
                </button>
              ))}
            </div>

            {/* Calculator Form */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                {activeCalculator.charAt(0).toUpperCase() + activeCalculator.slice(1)} Impact Calculator
              </h3>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Current Price (₹)
                  </label>
                  <input
                    type="number"
                    value={currentPrice}
                    onChange={(e) => setCurrentPrice(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="1000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Shares Held
                  </label>
                  <input
                    type="number"
                    value={sharesHeld}
                    onChange={(e) => setSharesHeld(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="100"
                  />
                </div>

                {activeCalculator === 'dividend' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Dividend per Share (₹)
                    </label>
                    <input
                      type="number"
                      value={dividendPerShare}
                      onChange={(e) => setDividendPerShare(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="10"
                    />
                  </div>
                )}

                {activeCalculator === 'split' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Split Ratio (e.g., 2:1)
                    </label>
                    <input
                      type="text"
                      value={splitRatio}
                      onChange={(e) => setSplitRatio(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="2:1"
                    />
                  </div>
                )}

                {activeCalculator === 'bonus' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Bonus Ratio (e.g., 1:2)
                    </label>
                    <input
                      type="text"
                      value={bonusRatio}
                      onChange={(e) => setBonusRatio(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="1:2"
                    />
                  </div>
                )}

                {activeCalculator === 'rights' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Rights Ratio (e.g., 1:5)
                      </label>
                      <input
                        type="text"
                        value={rightsRatio}
                        onChange={(e) => setRightsRatio(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="1:5"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Rights Price (₹)
                      </label>
                      <input
                        type="number"
                        value={rightsPrice}
                        onChange={(e) => setRightsPrice(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="800"
                      />
                    </div>
                  </>
                )}
              </div>

              <button
                onClick={calculateImpact}
                disabled={loading}
                className="w-full px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
              >
                Calculate Impact
              </button>

              {calculationResult && (
                <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Results:</h4>
                  <div className="space-y-2">
                    {Object.entries(calculationResult).map(([key, value]: [string, any]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400 capitalize">
                          {key.replace(/_/g, ' ')}:
                        </span>
                        <span className="font-semibold text-gray-900 dark:text-white">
                          {typeof value === 'number' ? value.toFixed(2) : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CorporateActionsModule;
