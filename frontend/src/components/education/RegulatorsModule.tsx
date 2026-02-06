/**
 * Regulators Education Module
 * SEBI, RBI, and market structure education
 */

import React, { useState, useEffect } from 'react';
import { httpClient } from '../../config/api';
import { AcademicCapIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const RegulatorsModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'education' | 'analysis'>('education');
  const [regulatorsInfo, setRegulatorsInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeTab === 'education') {
      loadRegulatorsInfo();
    }
  }, [activeTab]);

  const loadRegulatorsInfo = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/market-education/regulators/info');
      if (response.success) {
        const data: any = response.data;
        setRegulatorsInfo(data?.regulators ?? data ?? null);
      }
    } catch (error: any) {
      toast.error('Failed to load regulators information');
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
            <AcademicCapIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Regulators & Market Structure</h2>
            <p className="text-gray-600 dark:text-gray-400">Understanding SEBI, RBI, and market participants</p>
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
            onClick={() => setActiveTab('analysis')}
            className={`px-4 py-3 font-medium text-sm border-b-2 ${
              activeTab === 'analysis'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400'
            }`}
          >
            Market Structure Analysis
          </button>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          </div>
        ) : activeTab === 'education' && regulatorsInfo ? (
          <div className="space-y-6">
            {Object.entries(regulatorsInfo).map(([key, regulator]: [string, any]) => (
              <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="flex items-start gap-4 mb-4">
                  <BuildingOfficeIcon className="w-8 h-8 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                      {regulator.name || key}
                    </h3>
                    {regulator.full_form && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        {regulator.full_form}
                      </p>
                    )}
                  </div>
                </div>
                
                {regulator.role && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Role:</h4>
                    <p className="text-gray-700 dark:text-gray-300">{regulator.role}</p>
                  </div>
                )}

                {regulator.functions && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Key Functions:</h4>
                    <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                      {Array.isArray(regulator.functions) ? (
                        regulator.functions.map((func: string, idx: number) => (
                          <li key={idx}>{func}</li>
                        ))
                      ) : (
                        <li>{regulator.functions}</li>
                      )}
                    </ul>
                  </div>
                )}

                {regulator.importance && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Importance:</h4>
                    <p className="text-gray-700 dark:text-gray-300">{regulator.importance}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : activeTab === 'analysis' ? (
          <div className="space-y-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Market Structure Analysis
              </h3>
              <p className="text-blue-800 dark:text-blue-200 text-sm">
                This feature analyzes how regulatory structure impacts market dynamics. 
                Use this to understand market participants, trading mechanisms, and regulatory oversight.
              </p>
            </div>
            <div className="text-center py-12 text-gray-500">
              Market structure analysis tool coming soon
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">No information available</div>
        )}
      </div>
    </div>
  );
};

export default RegulatorsModule;
