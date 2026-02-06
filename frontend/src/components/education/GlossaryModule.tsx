/**
 * Glossary Education Module
 * Comprehensive stock market terms dictionary
 */

import React, { useState } from 'react';
import { httpClient } from '../../config/api';
import { MagnifyingGlassIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const GlossaryModule: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      toast.error('Please enter a search term');
      return;
    }

    try {
      setLoading(true);
      const response = await httpClient.get(
        `/api/market-education/glossary/search?term=${encodeURIComponent(searchTerm)}`
      );

      if (response.success) {
        const data: any = response.data;
        const results = data?.terms || data?.results || [];
        setSearchResults(Array.isArray(results) ? results : results ? [results] : []);
        if (!results || (Array.isArray(results) && results.length === 0)) {
          toast('No results found', { icon: 'ℹ️' });
        }
      }
    } catch (error: any) {
      toast.error('Failed to search glossary');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
            <MagnifyingGlassIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Glossary</h2>
            <p className="text-gray-600 dark:text-gray-400">Comprehensive stock market terms dictionary</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Search Bar */}
        <div className="mb-6">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search for terms (e.g., IPO, PE Ratio, Dividend)..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="space-y-4">
            {searchResults.map((term, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="flex items-start gap-3 mb-3">
                  <BookOpenIcon className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                      {term.term || term.name || 'Term'}
                    </h3>
                    {term.full_form && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        Full Form: {term.full_form}
                      </p>
                    )}
                    <p className="text-gray-700 dark:text-gray-300 mb-3">
                      {term.definition || term.description || 'No definition available'}
                    </p>
                    {term.example && (
                      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 mt-3">
                        <p className="text-sm font-semibold text-gray-900 dark:text-white mb-1">Example:</p>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{term.example}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {searchResults.length === 0 && !loading && searchTerm && (
          <div className="text-center py-12 text-gray-500">
            No results found for "{searchTerm}"
          </div>
        )}

        {!searchTerm && (
          <div className="text-center py-12">
            <BookOpenIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              Enter a term above to search the glossary
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GlossaryModule;
