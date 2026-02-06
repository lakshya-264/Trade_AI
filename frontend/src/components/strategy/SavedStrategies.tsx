/**
 * Saved Strategies Component
 * Manages saved user strategies
 */

import React, { useState, useEffect } from 'react';
import { FileText, Trash2, Download, Upload, Calendar, Edit2, FileDown, HelpCircle } from 'lucide-react';
import { Strategy } from './StrategyBuilder';
import { httpClient } from '../../config/api';
import { toast } from 'react-hot-toast';

interface SavedStrategiesProps {
  symbol: string;
  onStrategySelect: (strategy: Strategy) => void;
  onStrategyDelete: () => void;
}

const SavedStrategies: React.FC<SavedStrategiesProps> = ({ symbol, onStrategySelect, onStrategyDelete }) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    fetchSavedStrategies();
  }, [symbol]);

  const fetchSavedStrategies = async () => {
    setLoading(true);
    try {
      const response = await httpClient.get('/api/comprehensive-trading/strategy/saved', {
        params: { symbol }
      }) as any;

      if (response.data?.success) {
        setStrategies(response.data.data || []);
      }
    } catch (error: any) {
      console.error('Error fetching saved strategies:', error);
      // Use mock data for development
      setStrategies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this strategy?')) return;

    setDeletingId(id);
    try {
      const response = await httpClient.delete(`/api/comprehensive-trading/strategy/${id}`) as any;

      if (response.data?.success) {
        setStrategies(prev => prev.filter(s => s.id !== id));
        toast.success('Strategy deleted successfully');
        onStrategyDelete();
      }
    } catch (error: any) {
      console.error('Error deleting strategy:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete strategy');
    } finally {
      setDeletingId(null);
    }
  };

  const handleExport = (strategy: Strategy) => {
    // Clean strategy object for export (remove id, timestamps if needed)
    const exportStrategy = {
      name: strategy.name,
      description: strategy.description || '',
      legs: strategy.legs.map(leg => ({
        action: leg.action,
        instrument: leg.instrument,
        strike: leg.strike,
        quantity: leg.quantity,
        expiry: leg.expiry,
        lotSize: leg.lotSize
      })),
      // Include metrics if available
      ...(strategy.metrics && { metrics: strategy.metrics })
    };

    const dataStr = JSON.stringify(exportStrategy, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${strategy.name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Strategy exported successfully');
  };

  const handleExportAll = () => {
    if (strategies.length === 0) {
      toast.error('No strategies to export');
      return;
    }

    // Export all strategies as an array
    const exportData = {
      version: '1.0',
      exportDate: new Date().toISOString(),
      strategies: strategies.map(strategy => ({
        name: strategy.name,
        description: strategy.description || '',
        legs: strategy.legs.map(leg => ({
          action: leg.action,
          instrument: leg.instrument,
          strike: leg.strike,
          quantity: leg.quantity,
          expiry: leg.expiry,
          lotSize: leg.lotSize
        })),
        ...(strategy.metrics && { metrics: strategy.metrics })
      }))
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `strategies_export_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success(`Exported ${strategies.length} strategy(ies) successfully`);
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        const data = JSON.parse(text);
        
        // Handle both single strategy and bulk import (array format)
        let strategiesToImport: Strategy[] = [];
        
        if (Array.isArray(data)) {
          // Array of strategies
          strategiesToImport = data;
        } else if (data.strategies && Array.isArray(data.strategies)) {
          // Bulk export format with version info
          strategiesToImport = data.strategies;
        } else if (data.name && data.legs) {
          // Single strategy
          strategiesToImport = [data];
        } else {
          throw new Error('Invalid strategy format');
        }

        // Validate each strategy
        for (const strategy of strategiesToImport) {
          if (!strategy.name || !strategy.legs || !Array.isArray(strategy.legs)) {
            throw new Error(`Invalid strategy: ${strategy.name || 'Unknown'}`);
          }

          // Validate legs
          for (const leg of strategy.legs) {
            if (!leg.action || !leg.instrument || leg.quantity === undefined) {
              throw new Error(`Invalid leg in strategy: ${strategy.name}`);
            }
            if ((leg.instrument === 'CE' || leg.instrument === 'PE') && !leg.strike) {
              throw new Error(`Missing strike price for ${leg.instrument} in strategy: ${strategy.name}`);
            }
          }
        }

        // Import first strategy (or all if bulk import is supported)
        if (strategiesToImport.length > 0) {
          const strategyToLoad = strategiesToImport[0];
          // Add IDs to legs if missing
          const strategyWithIds: Strategy = {
            ...strategyToLoad,
            legs: strategyToLoad.legs.map((leg, idx) => ({
              ...leg,
              id: leg.id || `${Date.now()}_${idx}`
            }))
          };
          onStrategySelect(strategyWithIds);
          toast.success(
            strategiesToImport.length > 1 
              ? `Imported ${strategiesToImport.length} strategies. First strategy loaded.`
              : 'Strategy imported successfully'
          );
        }
      } catch (error: any) {
        console.error('Import error:', error);
        toast.error(error.message || 'Invalid strategy file format');
      }
    };
    input.click();
  };

  const showFormatExample = () => {
    const example = {
      name: "Bull Call Spread",
      description: "Example strategy description",
      legs: [
        {
          action: "BUY",
          instrument: "CE",
          strike: 26000,
          quantity: 1,
          expiry: "30 Dec",
          lotSize: 50
        },
        {
          action: "SELL",
          instrument: "CE",
          strike: 26500,
          quantity: 1,
          expiry: "30 Dec",
          lotSize: 50
        }
      ]
    };

    const exampleStr = JSON.stringify(example, null, 2);
    const blob = new Blob([exampleStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'strategy_format_example.json';
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Format example downloaded');
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', { 
      day: 'numeric', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold">Saved Strategies</h3>
        <div className="flex gap-2">
          <button
            onClick={showFormatExample}
            className="px-4 py-2 bg-[#2a2e39] hover:bg-[#3a3e49] rounded-lg flex items-center gap-2 text-sm"
            title="Download format example"
          >
            <HelpCircle className="w-4 h-4" />
            Format
          </button>
          {strategies.length > 0 && (
            <button
              onClick={handleExportAll}
              className="px-4 py-2 bg-[#2a2e39] hover:bg-[#3a3e49] rounded-lg flex items-center gap-2 text-sm"
              title="Export all strategies"
            >
              <FileDown className="w-4 h-4" />
              Export All
            </button>
          )}
          <button
            onClick={handleImport}
            className="px-4 py-2 bg-[#2a2e39] hover:bg-[#3a3e49] rounded-lg flex items-center gap-2 text-sm"
            title="Import strategy from JSON file"
          >
            <Upload className="w-4 h-4" />
            Import
          </button>
          <button
            onClick={fetchSavedStrategies}
            className="px-4 py-2 bg-[#2a2e39] hover:bg-[#3a3e49] rounded-lg text-sm"
            title="Refresh strategies list"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Format Info */}
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-sm">
        <div className="flex items-start gap-2">
          <HelpCircle className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-blue-300 font-semibold mb-1">Import Format:</p>
            <p className="text-gray-300 text-xs">
              Import single strategy or bulk export file. Required fields: <code className="bg-[#1a1d28] px-1 rounded">name</code>, <code className="bg-[#1a1d28] px-1 rounded">legs</code> (array). Each leg requires: <code className="bg-[#1a1d28] px-1 rounded">action</code> (BUY/SELL), <code className="bg-[#1a1d28] px-1 rounded">instrument</code> (CE/PE/FUT), <code className="bg-[#1a1d28] px-1 rounded">strike</code> (for CE/PE), <code className="bg-[#1a1d28] px-1 rounded">quantity</code>, <code className="bg-[#1a1d28] px-1 rounded">expiry</code>, <code className="bg-[#1a1d28] px-1 rounded">lotSize</code>. Click "Format" to download an example.
            </p>
          </div>
        </div>
      </div>

      {/* Strategies List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
          <p className="mt-2 text-gray-400">Loading strategies...</p>
        </div>
      ) : strategies.length === 0 ? (
        <div className="text-center py-12 bg-[#1a1d28] rounded-lg border border-gray-700">
          <FileText className="w-12 h-12 mx-auto mb-2 text-gray-500" />
          <p className="text-gray-400">No saved strategies found</p>
          <p className="text-sm text-gray-500 mt-1">Create and save strategies in the Strategy Builder</p>
        </div>
      ) : (
        <div className="space-y-3">
          {strategies.map((strategy) => (
            <div
              key={strategy.id}
              className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700 hover:border-blue-500 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="font-semibold text-lg mb-1">{strategy.name}</h4>
                  {strategy.description && (
                    <p className="text-sm text-gray-400 mb-2">{strategy.description}</p>
                  )}
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(strategy.createdAt)}
                    </div>
                    <div>Legs: {strategy.legs.length}</div>
                    {strategy.metrics && (
                      <>
                        <div className="text-green-400">
                          Max Profit: ₹{(strategy.metrics.maxProfit / 100000).toFixed(2)}L
                        </div>
                        <div className="text-red-400">
                          Max Loss: ₹{(Math.abs(strategy.metrics.maxLoss) / 100000).toFixed(2)}L
                        </div>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onStrategySelect(strategy)}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                  >
                    Load
                  </button>
                  <button
                    onClick={() => onStrategySelect(strategy)}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm flex items-center gap-1"
                    title="Edit strategy"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => handleExport(strategy)}
                    className="px-3 py-1 bg-[#2a2e39] hover:bg-[#3a3e49] rounded text-sm"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(strategy.id!)}
                    disabled={deletingId === strategy.id}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm disabled:opacity-50"
                  >
                    {deletingId === strategy.id ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Legs Preview */}
              <div className="mt-3 pt-3 border-t border-gray-700">
                <div className="flex flex-wrap gap-2">
                  {strategy.legs.map((leg, idx) => (
                    <div
                      key={idx}
                      className="px-2 py-1 bg-[#2a2e39] rounded text-xs"
                    >
                      <span className={leg.action === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                        {leg.action}
                      </span>
                      {' '}
                      <span className="text-blue-400">{leg.instrument}</span>
                      {' '}
                      <span>{leg.strike}</span>
                      {' '}
                      <span className="text-gray-400">×{leg.quantity}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SavedStrategies;

