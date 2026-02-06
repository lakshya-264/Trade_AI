/**
 * Unified AI Watchlist Component
 * Track analyzed stocks in Unified AI
 */

import React, { useState, useEffect } from 'react';
import { watchlistService } from '../services/watchlistService';
import { unifiedAiApi } from '../services/unifiedAiApi';
import { toast } from 'react-hot-toast';
import {
  StarIcon,
  XMarkIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import {
  StarIcon as StarIconSolid
} from '@heroicons/react/24/solid';

interface UnifiedAIWatchlistProps {
  onSymbolSelect?: (symbol: string) => void;
  selectedSymbol?: string;
  compact?: boolean;
}

const UnifiedAIWatchlist: React.FC<UnifiedAIWatchlistProps> = ({
  onSymbolSelect,
  selectedSymbol,
  compact = false
}) => {
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [newSymbol, setNewSymbol] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = () => {
    const symbols = watchlistService.getWatchlist();
    setWatchlist(symbols);
  };

  const handleAddSymbol = () => {
    if (!newSymbol.trim()) return;

    const symbol = newSymbol.trim().toUpperCase();
    if (watchlistService.isInWatchlist(symbol)) {
      toast.error(`${symbol} is already in watchlist`);
      return;
    }

    watchlistService.addSymbol(symbol);
    loadWatchlist();
    setNewSymbol('');
    setShowAddForm(false);
    toast.success(`${symbol} added to watchlist`);
  };

  const handleRemoveSymbol = (symbol: string) => {
    watchlistService.removeSymbol(symbol);
    loadWatchlist();
    toast.success(`${symbol} removed from watchlist`);
  };

  const handleSymbolClick = (symbol: string) => {
    onSymbolSelect?.(symbol);
  };

  if (compact) {
    return (
      <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <StarIcon className="w-4 h-4 text-yellow-400" />
            <span className="text-xs font-semibold text-gray-300">Watchlist</span>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="text-gray-400 hover:text-white"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>
        
        {showAddForm && (
          <div className="mb-2 flex gap-2">
            <input
              type="text"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
              placeholder="Add symbol..."
              className="flex-1 px-2 py-1 bg-[#131722] border border-[#2a2e39] rounded text-xs text-white placeholder-gray-500"
            />
            <button
              onClick={handleAddSymbol}
              className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs"
            >
              Add
            </button>
          </div>
        )}

        <div className="space-y-1 max-h-32 overflow-y-auto">
          {watchlist.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-2">No symbols</p>
          ) : (
            watchlist.map((symbol) => (
              <div
                key={symbol}
                className={`flex items-center justify-between p-1.5 rounded text-xs cursor-pointer hover:bg-[#2a2e39] ${
                  selectedSymbol === symbol ? 'bg-blue-500/20' : ''
                }`}
                onClick={() => handleSymbolClick(symbol)}
              >
                <span className="text-gray-300">{symbol}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveSymbol(symbol);
                  }}
                  className="text-gray-500 hover:text-red-400"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 h-full flex flex-col shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <StarIconSolid className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Watchlist</h3>
          <span className="text-xs text-gray-400">({watchlist.length})</span>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="text-gray-400 hover:text-white"
        >
          <PlusIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Add Symbol Form */}
      {showAddForm && (
        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
                placeholder="Enter symbol (e.g., RELIANCE)"
                className="w-full pl-8 pr-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleAddSymbol}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium"
            >
              Add
            </button>
          </div>
        </div>
      )}

      {/* Watchlist Items */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {watchlist.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <StarIcon className="w-12 h-12 text-gray-600 mb-2" />
            <p className="text-sm text-gray-400">No symbols in watchlist</p>
            <p className="text-xs text-gray-500 mt-1">Add symbols to track them</p>
          </div>
        ) : (
          watchlist.map((symbol) => (
            <div
              key={symbol}
              className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedSymbol === symbol
                  ? 'bg-blue-50 dark:bg-blue-500/20 border-blue-500 dark:border-blue-500/50'
                  : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'
              }`}
              onClick={() => handleSymbolClick(symbol)}
            >
              <div className="flex items-center gap-3">
                <ChartBarIcon className="w-5 h-5 text-blue-400" />
                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">{symbol}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Click to analyze</p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveSymbol(symbol);
                }}
                className="text-gray-400 hover:text-red-400 transition-colors"
                title="Remove from watchlist"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default UnifiedAIWatchlist;

