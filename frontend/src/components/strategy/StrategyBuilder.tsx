/**
 * Strategy Builder Component
 * Complete options strategy builder with legs management, cockpit view, and payoff chart
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Plus, Trash2, Edit2, Save, Download, Upload, 
  TrendingUp, TrendingDown, BarChart3, Calculator,
  Target, AlertCircle, CheckCircle, XCircle,
  Play, Pause, RefreshCw, FileText, BookOpen
} from 'lucide-react';
import { httpClient } from '../../config/api';
import { toast } from 'react-hot-toast';
import { handleApiErrorWithLog } from '../../utils/errorHandler';
import PayoffChart from './PayoffChart';
import StrategyCockpit from './StrategyCockpit';
import SuggestedStrategies from './SuggestedStrategies';
import SavedStrategies from './SavedStrategies';
import PaperTrading from './PaperTrading';

export interface StrategyLeg {
  id: string;
  action: 'BUY' | 'SELL';
  instrument: 'CE' | 'PE' | 'FUT';
  expiry: string;
  strike: number;
  quantity: number;
  price: number;
  premium?: number;
  lotSize?: number;
}

export interface StrategyMetrics {
  maxProfit: number;
  maxLoss: number;
  breakevenPoints: number[];
  probabilityOfProfit: number;
  rewardRiskRatio: number;
  totalPremium: number;
  marginRequired: number;
  greeks?: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
  };
}

export interface Strategy {
  id?: string;
  name: string;
  description?: string;
  symbol?: string;
  legs: StrategyLeg[];
  metrics?: StrategyMetrics;
  createdAt?: string;
  updatedAt?: string;
}

const StrategyBuilder: React.FC<{
  symbol?: string;
  onStrategySelect?: (strategy: Strategy) => void;
  showPaperTrading?: boolean;
}> = ({ symbol = 'NIFTY', onStrategySelect, showPaperTrading = true }) => {
  const [activeTab, setActiveTab] = useState<'builder' | 'saved' | 'suggested' | 'paper'>('builder');
  const [refreshSavedStrategies, setRefreshSavedStrategies] = useState(0);
  const [strategy, setStrategy] = useState<Strategy>({
    name: 'New Strategy',
    legs: []
  });
  const [metrics, setMetrics] = useState<StrategyMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [editingLeg, setEditingLeg] = useState<StrategyLeg | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(26042.30);
  const [expiryDate, setExpiryDate] = useState<string>('30 Dec');
  const [showLegForm, setShowLegForm] = useState(false);

  // Use ref to track if we're already calculating to prevent infinite loops
  const isCalculatingRef = useRef(false);
  
  useEffect(() => {
    // Prevent infinite loop by checking if already calculating
    if (isCalculatingRef.current) return;
    
    if (strategy.legs.length > 0) {
      isCalculatingRef.current = true;
      calculateStrategyMetrics().finally(() => {
        isCalculatingRef.current = false;
      });
    } else {
      setMetrics(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strategy.legs.length, currentPrice, expiryDate]);

  const calculateStrategyMetrics = async () => {
    if (strategy.legs.length === 0) return;

    setLoading(true);
    try {
      const response = await httpClient.post('/api/comprehensive-trading/strategy/calculate', {
        symbol,
        legs: strategy.legs,
        current_price: currentPrice,
        expiry_date: expiryDate
      }) as any;

      if (response.success && response.data) {
        setMetrics(response.data);
        // Don't update strategy here to avoid triggering useEffect loop
        // Metrics are stored separately and can be accessed via metrics state
      }
    } catch (error: any) {
      handleApiErrorWithLog(error, 'Failed to calculate strategy metrics', 'calculateStrategyMetrics');
    } finally {
      setLoading(false);
    }
  };

  const addLeg = (leg: Omit<StrategyLeg, 'id'>) => {
    try {
      const newLeg: StrategyLeg = {
        ...leg,
        id: Date.now().toString()
      };
      setStrategy(prev => ({
        ...prev,
        legs: [...prev.legs, newLeg]
      }));
      setShowLegForm(false);
      toast.success('Leg added successfully');
    } catch (error) {
      console.error('Error adding leg:', error);
      toast.error('Failed to add leg. Please try again.');
    }
  };

  const updateLeg = (id: string, updates: Partial<StrategyLeg>) => {
    setStrategy(prev => ({
      ...prev,
      legs: prev.legs.map(leg => leg.id === id ? { ...leg, ...updates } : leg)
    }));
    setEditingLeg(null);
    toast.success('Leg updated successfully');
  };

  const removeLeg = (id: string) => {
    setStrategy(prev => ({
      ...prev,
      legs: prev.legs.filter(leg => leg.id !== id)
    }));
    toast.success('Leg removed');
  };

  const loadStrategy = (loadedStrategy: Strategy) => {
    setStrategy(loadedStrategy);
    setActiveTab('builder');
    if (onStrategySelect) {
      onStrategySelect(loadedStrategy);
    }
    toast.success('Strategy loaded successfully');
  };

  const saveStrategy = async () => {
    if (!strategy.name || strategy.legs.length === 0) {
      toast.error('Please add a name and at least one leg to save the strategy');
      return;
    }

    setLoading(true);
    try {
      // Format legs for backend (remove id, ensure all required fields)
      const formattedLegs = strategy.legs.map(leg => ({
        action: leg.action,
        instrument: leg.instrument,
        expiry: leg.expiry,
        strike: leg.strike,
        quantity: leg.quantity,
        price: leg.price,
        premium: leg.premium,
        lotSize: leg.lotSize || 50
      }));

      const response = await httpClient.post('/api/comprehensive-trading/strategy/save', {
        id: strategy.id,
        name: strategy.name,
        description: strategy.description || '',
        symbol: symbol,
        legs: formattedLegs,
        metrics: strategy.metrics || null
      }) as any;

      if (response.success && response.data) {
        setStrategy(prev => ({ ...prev, id: response.data.id }));
        toast.success('Strategy saved successfully');
        // Trigger refresh of saved strategies list
        setRefreshSavedStrategies(prev => prev + 1);
      } else {
        toast.error(response.error || response.message || 'Failed to save strategy');
      }
    } catch (error: any) {
      handleApiErrorWithLog(error, 'Failed to save strategy', 'saveStrategy');
    } finally {
      setLoading(false);
    }
  };

  const clearStrategy = () => {
    setStrategy({ name: 'New Strategy', legs: [] });
    setMetrics(null);
    toast.success('Strategy cleared');
  };

  return (
    <div className="flex flex-col h-full bg-[#0f1117] text-white">
      {/* Header Tabs */}
      <div className="flex border-b border-gray-700 bg-[#1a1d28]">
        <button
          onClick={() => setActiveTab('builder')}
          className={`px-6 py-3 font-medium transition-colors ${
            activeTab === 'builder'
              ? 'bg-[#2a2e39] text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4" />
            Strategy Builder
          </div>
        </button>
        <button
          onClick={() => setActiveTab('suggested')}
          className={`px-6 py-3 font-medium transition-colors ${
            activeTab === 'suggested'
              ? 'bg-[#2a2e39] text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            Suggested Strategies
          </div>
        </button>
        <button
          onClick={() => {
            setActiveTab('saved');
            // Refresh saved strategies when tab is clicked
            setRefreshSavedStrategies(prev => prev + 1);
          }}
          className={`px-6 py-3 font-medium transition-colors ${
            activeTab === 'saved'
              ? 'bg-[#2a2e39] text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Saved Strategies
          </div>
        </button>
        {showPaperTrading && (
          <button
            onClick={() => setActiveTab('paper')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'paper'
                ? 'bg-[#2a2e39] text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-2">
              <Play className="w-4 h-4" />
              Paper Trading
            </div>
          </button>
        )}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'builder' && (
          <div className="flex flex-col gap-4 p-4">
            {/* Top Section - Strategy Legs and Cockpit */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Left Panel - Strategy Legs */}
              <div className="space-y-4">
                <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Strategy Legs</h3>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setShowLegForm(true)}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm flex items-center gap-1"
                      >
                        <Plus className="w-4 h-4" />
                        Add Leg
                      </button>
                      <button
                        onClick={saveStrategy}
                        disabled={loading || strategy.legs.length === 0}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm flex items-center gap-1 disabled:opacity-50"
                      >
                        <Save className="w-4 h-4" />
                        Save
                      </button>
                      <button
                        onClick={clearStrategy}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                      >
                        Clear
                      </button>
                    </div>
                  </div>

                  {/* Strategy Name */}
                  <input
                    type="text"
                    value={strategy.name}
                    onChange={(e) => setStrategy(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Strategy Name"
                    className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded mb-4 text-white placeholder-gray-400"
                  />

                  {/* Legs List */}
                  {strategy.legs.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      <Calculator className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>No legs added yet</p>
                      <p className="text-sm mt-1">Click "Add Leg" to start building your strategy</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {strategy.legs.map((leg) => (
                        <div
                          key={leg.id}
                          className="bg-[#2a2e39] rounded p-3 border border-gray-600"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                leg.action === 'BUY' ? 'bg-green-600' : 'bg-red-600'
                              }`}>
                                {leg.action}
                              </span>
                              <span className="px-2 py-1 bg-blue-600 rounded text-xs">
                                {leg.instrument}
                              </span>
                              <span className="text-sm font-medium">{leg.strike}</span>
                            </div>
                            <div className="flex gap-1">
                              <button
                                onClick={() => setEditingLeg(leg)}
                                className="p-1 hover:bg-gray-600 rounded"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => removeLeg(leg.id)}
                                className="p-1 hover:bg-red-600 rounded"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          <div className="text-xs text-gray-400 space-y-1">
                            <div>Expiry: {leg.expiry}</div>
                            <div>Qty: {leg.quantity} × {leg.price.toFixed(2)}</div>
                            <div>Total: ₹{(leg.quantity * leg.price).toFixed(2)}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Add/Edit Leg Form */}
                {(showLegForm || editingLeg) && (
                  <LegForm
                    leg={editingLeg}
                    onSave={(leg) => {
                      if (editingLeg) {
                        updateLeg(editingLeg.id, leg);
                      } else {
                        addLeg(leg);
                      }
                      setShowLegForm(false);
                      setEditingLeg(null);
                    }}
                    onCancel={() => {
                      setShowLegForm(false);
                      setEditingLeg(null);
                    }}
                    symbol={symbol}
                    expiryDate={expiryDate}
                  />
                )}
              </div>

              {/* Right Panel - Cockpit */}
              <div>
                <StrategyCockpit
                  strategy={strategy}
                  metrics={metrics}
                  currentPrice={currentPrice}
                  loading={loading}
                  onPriceChange={setCurrentPrice}
                />
              </div>
            </div>

            {/* Bottom Section - Payoff Chart (Full Width, Centered, Draggable) */}
            <div className="w-full">
              {strategy.legs.length > 0 ? (
                <PayoffChart
                  legs={strategy.legs}
                  currentPrice={currentPrice}
                  metrics={metrics}
                  symbol={symbol}
                />
              ) : (
                <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-center h-64 text-gray-400">
                    <div className="text-center">
                      <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Add legs to see payoff chart</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'suggested' && (
          <SuggestedStrategies
            symbol={symbol}
            onStrategySelect={loadStrategy}
          />
        )}

        {activeTab === 'saved' && (
          <SavedStrategies
            key={refreshSavedStrategies}
            symbol={symbol}
            onStrategySelect={loadStrategy}
            onStrategyDelete={() => {
              if (strategy.id) {
                setStrategy({ name: 'New Strategy', legs: [] });
                setMetrics(null);
              }
            }}
          />
        )}

        {activeTab === 'paper' && showPaperTrading && (
          <PaperTrading
            strategy={strategy}
            symbol={symbol}
            currentPrice={currentPrice}
          />
        )}
      </div>
    </div>
  );
};

// Leg Form Component
interface LegFormProps {
  leg: StrategyLeg | null;
  onSave: (leg: Omit<StrategyLeg, 'id'>) => void;
  onCancel: () => void;
  symbol: string;
  expiryDate: string;
}

const LegForm: React.FC<LegFormProps> = ({ leg, onSave, onCancel, symbol, expiryDate }) => {
  const [formData, setFormData] = useState({
    action: (leg?.action || 'BUY') as 'BUY' | 'SELL',
    instrument: (leg?.instrument || 'CE') as 'CE' | 'PE' | 'FUT',
    expiry: leg?.expiry || expiryDate,
    strike: leg?.strike || (symbol === 'NIFTY' ? 26000 : 0),
    quantity: leg?.quantity || 1,
    price: leg?.price || 0,
    premium: leg?.premium || 0,
    lotSize: leg?.lotSize || 50
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Validate required fields
    if (!formData.expiry || formData.expiry.trim() === '') {
      toast.error('Please enter an expiry date');
      return;
    }
    
    // Validate strike price for CE and PE (not required for FUT)
    if ((formData.instrument === 'CE' || formData.instrument === 'PE') && (!formData.strike || formData.strike <= 0)) {
      toast.error('Please enter a valid strike price for ' + formData.instrument);
      return;
    }
    
    if (formData.quantity <= 0) {
      toast.error('Please enter a valid quantity');
      return;
    }
    
    if (formData.lotSize <= 0) {
      toast.error('Please enter a valid lot size');
      return;
    }
    
    // Call onSave with the form data
    try {
      onSave(formData);
    } catch (error) {
      console.error('Error saving leg:', error);
      toast.error('Failed to save leg. Please try again.');
    }
  };

  return (
    <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
      <h4 className="text-lg font-semibold mb-4">{leg ? 'Edit Leg' : 'Add Leg'}</h4>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Action</label>
            <select
              value={formData.action}
              onChange={(e) => setFormData(prev => ({ ...prev, action: e.target.value as 'BUY' | 'SELL' }))}
              className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded text-white"
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Instrument</label>
            <select
              value={formData.instrument}
              onChange={(e) => setFormData(prev => ({ ...prev, instrument: e.target.value as 'CE' | 'PE' | 'FUT' }))}
              className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded text-white"
            >
              <option value="CE">Call (CE)</option>
              <option value="PE">Put (PE)</option>
              <option value="FUT">Future</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Expiry <span className="text-red-400">*</span></label>
          <input
            type="text"
            value={formData.expiry}
            onChange={(e) => setFormData(prev => ({ ...prev, expiry: e.target.value }))}
            className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="30 Dec"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Strike {formData.instrument !== 'FUT' && <span className="text-red-400">*</span>}
            </label>
            <input
              type="number"
              value={formData.strike != null ? formData.strike : ''}
              onChange={(e) => setFormData(prev => ({ ...prev, strike: parseFloat(e.target.value) || 0 }))}
              className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={symbol === 'NIFTY' ? '26000' : 'Enter strike'}
              required={formData.instrument !== 'FUT'}
              min="0"
              step="50"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Quantity <span className="text-red-400">*</span></label>
            <input
              type="number"
              value={formData.quantity}
              onChange={(e) => setFormData(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
              className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="1"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Price</label>
            <input
              type="number"
              step="0.01"
              value={formData.price}
              onChange={(e) => setFormData(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
              className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Lot Size <span className="text-red-400">*</span></label>
            <input
              type="number"
              value={formData.lotSize}
              onChange={(e) => setFormData(prev => ({ ...prev, lotSize: parseInt(e.target.value) || 50 }))}
              className="w-full px-3 py-2 bg-[#2a2e39] border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="1"
              required
            />
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
          >
            {leg ? 'Update' : 'Add'} Leg
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-white"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default StrategyBuilder;

