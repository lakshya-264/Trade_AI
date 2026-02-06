/**
 * Level 3 Data Education Module
 * Order book depth and market depth analysis
 */

import React, { useState, useEffect } from 'react';
import { httpClient } from '../../config/api';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const Level3DataModule: React.FC = () => {
  const [educationContent, setEducationContent] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadEducationContent();
  }, []);

  const loadEducationContent = async () => {
    try {
      setLoading(true);
      const response = await httpClient.get('/api/market-education/level3/education');
      if (response.success) {
        const data: any = response.data;
        setEducationContent(data?.education ?? data ?? null);
      }
    } catch (error: any) {
      toast.error('Failed to load Level 3 data education');
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
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Level 3 Data</h2>
            <p className="text-gray-600 dark:text-gray-400">Order book depth and market depth analysis</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          </div>
        ) : educationContent ? (
          <div className="space-y-6 prose dark:prose-invert max-w-none">
            {Object.entries(educationContent).map(([key, section]: [string, any]) => (
              <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  {section.title || key}
                </h3>
                {section.description && (
                  <p className="text-gray-700 dark:text-gray-300 mb-4">{section.description}</p>
                )}
                {section.content && (
                  <p className="text-gray-600 dark:text-gray-400">{section.content}</p>
                )}
                {section.key_points && (
                  <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300 mt-4">
                    {Array.isArray(section.key_points) ? (
                      section.key_points.map((point: string, idx: number) => (
                        <li key={idx}>{point}</li>
                      ))
                    ) : (
                      <li>{section.key_points}</li>
                    )}
                  </ul>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <p>Level 3 data education content coming soon</p>
            <p className="text-sm mt-2">This module covers order book depth, market depth, and Level 3 data analysis.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Level3DataModule;
