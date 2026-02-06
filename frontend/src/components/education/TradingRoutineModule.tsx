/**
 * Trading Routine Module
 * Daily, weekly, monthly trading checklists
 */

import React, { useState, useEffect } from 'react';
import { httpClient } from '../../config/api';
import { ClipboardDocumentListIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const TradingRoutineModule: React.FC = () => {
  const [activePeriod, setActivePeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [routines, setRoutines] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [completedItems, setCompletedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadRoutines();
  }, []);

  const loadRoutines = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/market-education/trading-routine');
      if (response.success) {
        const data: any = response.data;
        setRoutines(data?.routines ?? data ?? null);
      }
    } catch (error: any) {
      toast.error('Failed to load trading routines');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const toggleItem = (itemId: string) => {
    setCompletedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  const getRoutineForPeriod = () => {
    if (!routines) return null;
    return routines[activePeriod] || routines[`${activePeriod}_routine`] || null;
  };

  const currentRoutine = getRoutineForPeriod();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <ClipboardDocumentListIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Trading Routine</h2>
            <p className="text-gray-600 dark:text-gray-400">Daily, weekly, monthly trading checklists</p>
          </div>
        </div>
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-1 px-6">
          {['daily', 'weekly', 'monthly'].map((period) => (
            <button
              key={period}
              onClick={() => setActivePeriod(period as any)}
              className={`px-4 py-3 font-medium text-sm border-b-2 capitalize ${
                activePeriod === period
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400'
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          </div>
        ) : currentRoutine ? (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 capitalize">
              {activePeriod} Trading Routine
            </h3>
            {Array.isArray(currentRoutine) ? (
              currentRoutine.map((item: string | any, idx: number) => {
                const itemId = `${activePeriod}-${idx}`;
                const itemText = typeof item === 'string' ? item : item.task || item.title || item;
                const isCompleted = completedItems.has(itemId);

                return (
                  <div
                    key={idx}
                    onClick={() => toggleItem(itemId)}
                    className={`flex items-start gap-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                      isCompleted
                        ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <CheckCircleIcon
                      className={`w-6 h-6 flex-shrink-0 mt-0.5 ${
                        isCompleted
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}
                    />
                    <span
                      className={`flex-1 ${
                        isCompleted
                          ? 'line-through text-gray-500 dark:text-gray-400'
                          : 'text-gray-900 dark:text-white'
                      }`}
                    >
                      {itemText}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className="text-gray-700 dark:text-gray-300">
                {typeof currentRoutine === 'string' ? currentRoutine : JSON.stringify(currentRoutine)}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 capitalize">
              {activePeriod} Trading Routine
            </h3>
            <div className="text-center py-12 text-gray-500">
              <p>Sample {activePeriod} routine:</p>
              <ul className="list-disc list-inside space-y-2 mt-4 text-left max-w-md mx-auto">
                {activePeriod === 'daily' && (
                  <>
                    <li>Review market news and economic calendar</li>
                    <li>Check overnight global market movements</li>
                    <li>Review your watchlist and positions</li>
                    <li>Set alerts for key levels</li>
                    <li>Review trading journal</li>
                  </>
                )}
                {activePeriod === 'weekly' && (
                  <>
                    <li>Review weekly performance</li>
                    <li>Analyze winning and losing trades</li>
                    <li>Update trading plan if needed</li>
                    <li>Review risk management</li>
                    <li>Plan for next week</li>
                  </>
                )}
                {activePeriod === 'monthly' && (
                  <>
                    <li>Review monthly P&L</li>
                    <li>Analyze trading statistics</li>
                    <li>Review and update trading strategy</li>
                    <li>Set goals for next month</li>
                    <li>Review risk parameters</li>
                  </>
                )}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingRoutineModule;
