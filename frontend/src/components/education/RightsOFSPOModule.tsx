/**
 * Rights/OFS/FPO Education Module
 * Understanding rights issues, OFS, and FPO
 */

import React, { useState, useEffect } from 'react';
import { httpClient } from '../../config/api';
import { BookOpenIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const RightsOFSPOModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'rights' | 'ofs' | 'fpo' | 'comparison'>('rights');
  const [content, setContent] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/market-education/rights-ofs-fpo');
      if (response.success) {
        const data: any = response.data;
        setContent(data?.content ?? data ?? null);
      }
    } catch (error: any) {
      toast.error('Failed to load content');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getContentForTab = () => {
    if (!content) return null;
    return content[activeTab] || content[`${activeTab}_content`] || null;
  };

  const tabContent = getContentForTab();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <BookOpenIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Rights, OFS & FPO</h2>
            <p className="text-gray-600 dark:text-gray-400">Understanding rights issues, OFS, and FPO</p>
          </div>
        </div>
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-1 px-6">
          {['rights', 'ofs', 'fpo', 'comparison'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-3 font-medium text-sm border-b-2 uppercase ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          </div>
        ) : tabContent ? (
          <div className="space-y-6 prose dark:prose-invert max-w-none">
            {typeof tabContent === 'string' ? (
              <p className="text-gray-700 dark:text-gray-300">{tabContent}</p>
            ) : (
              <>
                {tabContent.title && (
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {tabContent.title}
                  </h3>
                )}
                {tabContent.description && (
                  <p className="text-gray-700 dark:text-gray-300">{tabContent.description}</p>
                )}
                {tabContent.key_points && (
                  <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300">
                    {Array.isArray(tabContent.key_points) ? (
                      tabContent.key_points.map((point: string, idx: number) => (
                        <li key={idx}>{point}</li>
                      ))
                    ) : (
                      <li>{tabContent.key_points}</li>
                    )}
                  </ul>
                )}
              </>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {activeTab === 'rights' && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Rights Issue</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  A rights issue allows existing shareholders to buy additional shares at a discounted price, 
                  usually in proportion to their existing holdings.
                </p>
                <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Offered to existing shareholders only</li>
                  <li>Usually at a discount to market price</li>
                  <li>Maintains proportional ownership</li>
                  <li>Can be renounced and traded</li>
                </ul>
              </div>
            )}

            {activeTab === 'ofs' && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">OFS (Offer for Sale)</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  OFS is a mechanism for large shareholders (usually promoters) to sell their shares to the public.
                </p>
                <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Used by promoters to reduce stake</li>
                  <li>Meets minimum public shareholding requirements</li>
                  <li>Usually at a discount to market price</li>
                  <li>Open to all investors</li>
                </ul>
              </div>
            )}

            {activeTab === 'fpo' && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">FPO (Follow-on Public Offer)</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  FPO is when a listed company issues additional shares to raise capital after its IPO.
                </p>
                <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Company issues new shares</li>
                  <li>Raises additional capital</li>
                  <li>May dilute existing shareholders</li>
                  <li>Open to all investors</li>
                </ul>
              </div>
            )}

            {activeTab === 'comparison' && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Comparison</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Feature</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Rights</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">OFS</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">FPO</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      <tr>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">Who can participate</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">Existing shareholders</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">All investors</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">All investors</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">Purpose</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">Raise capital</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">Reduce promoter stake</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">Raise capital</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">New shares issued</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">Yes</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">No</td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">Yes</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default RightsOFSPOModule;
