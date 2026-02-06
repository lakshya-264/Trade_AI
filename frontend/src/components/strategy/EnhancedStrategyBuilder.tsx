/**
 * Enhanced Strategy Builder Component
 * Sensibull-style interface with Payoff Graph, P&L Table, Greeks, and Strategy Chart tabs
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Plus, Trash2, Edit2, Save, Download, Upload, 
  TrendingUp, TrendingDown, BarChart3, Calculator,
  Target, AlertCircle, CheckCircle, XCircle,
  Play, Pause, RefreshCw, FileText, BookOpen,
  ChevronLeft, ChevronRight, HelpCircle,
  MoreVertical
} from 'lucide-react';
import { httpClient } from '../../config/api';
import { api } from '../../services/api';
import { toast } from 'react-hot-toast';
import { handleApiErrorWithLog } from '../../utils/errorHandler';
import PayoffChart from './PayoffChart';
import StrategyCockpit from './StrategyCockpit';
import SuggestedStrategies from './SuggestedStrategies';
import SavedStrategies from './SavedStrategies';
import PaperTrading from './PaperTrading';
import PnLTable from './PnLTable';
import GreeksView from './GreeksView';
import StrategyChart from './StrategyChart';
import StockSelector from '../StockSelector';
import { StrategyLeg, StrategyMetrics, Strategy } from './StrategyBuilder';

interface EnhancedStrategyBuilderProps {
  symbol?: string;
  onStrategySelect?: (strategy: Strategy) => void;
  showPaperTrading?: boolean;
  initialStrategy?: Strategy; // Strategy to load initially (e.g., from Options Chain)
}

const EnhancedStrategyBuilder: React.FC<EnhancedStrategyBuilderProps> = ({ 
  symbol = 'NIFTY', 
  onStrategySelect, 
  showPaperTrading = true,
  initialStrategy
}) => {
  const [activeMainTab, setActiveMainTab] = useState<'builder' | 'saved' | 'suggested' | 'paper'>('builder');
  const [activeViewTab, setActiveViewTab] = useState<'payoff' | 'pnl' | 'greeks' | 'chart'>('payoff');
  const [refreshSavedStrategies, setRefreshSavedStrategies] = useState(0);
  const [strategy, setStrategy] = useState<Strategy>(
    initialStrategy || {
      name: 'New Strategy',
      legs: []
    }
  );
  
  // Load initial strategy when it changes (from Options Chain Builder)
  useEffect(() => {
    if (initialStrategy && initialStrategy.legs && initialStrategy.legs.length > 0) {
      // Deep clone to ensure React detects the change and ensure all properties are primitives
      const strategyToLoad: Strategy = {
        ...initialStrategy,
        legs: [...initialStrategy.legs].map((leg, idx) => {
          // Ensure all leg properties are primitives, not objects (fixes React rendering error)
          const actionStr = typeof leg.action === 'string' ? leg.action : String(leg.action || 'BUY');
          const action: 'BUY' | 'SELL' = (actionStr === 'BUY' || actionStr === 'SELL') ? actionStr : 'BUY';
          const instrumentStr = typeof leg.instrument === 'string' ? leg.instrument : String(leg.instrument || 'CE');
          const instrument: 'CE' | 'PE' | 'FUT' = (instrumentStr === 'CE' || instrumentStr === 'PE' || instrumentStr === 'FUT') ? instrumentStr : 'CE';
          
          return {
            ...leg,
            id: typeof leg.id === 'string' ? leg.id : `leg-${Date.now()}-${idx}`,
            action: action,
            instrument: instrument,
            expiry: typeof leg.expiry === 'string' ? leg.expiry : String(leg.expiry || '30 Dec'),
            strike: typeof leg.strike === 'number' ? leg.strike : parseFloat(String(leg.strike)) || 0,
            quantity: typeof leg.quantity === 'number' ? leg.quantity : parseInt(String(leg.quantity)) || 1,
            price: typeof leg.price === 'number' ? leg.price : parseFloat(String(leg.price)) || 0,
            premium: typeof leg.premium === 'number' ? leg.premium : parseFloat(String(leg.premium)) || 0,
            lotSize: typeof leg.lotSize === 'number' ? leg.lotSize : parseInt(String(leg.lotSize)) || 50
          };
        })
      };
      setStrategy(strategyToLoad);
      setActiveMainTab('builder'); // Switch to builder tab to show the strategy
      
      // Set expiry date from first leg if available
      if (strategyToLoad.legs.length > 0 && strategyToLoad.legs[0].expiry) {
        setExpiryDate(strategyToLoad.legs[0].expiry);
      }
      
      // Set symbol if available
      if (initialStrategy.symbol) {
        setSelectedSymbol(initialStrategy.symbol);
      }
      
      toast.success(`✅ Strategy loaded: ${initialStrategy.name} with ${initialStrategy.legs.length} leg(s)`);
    }
  }, [initialStrategy?.name, initialStrategy?.legs?.length]); // Use specific properties for dependency
  const [metrics, setMetrics] = useState<StrategyMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [editingLeg, setEditingLeg] = useState<StrategyLeg | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(26042.30); // Default fallback
  const [expiryDate, setExpiryDate] = useState<string>('30 Dec');
  const [showLegForm, setShowLegForm] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string>(symbol);
  const [priceLoading, setPriceLoading] = useState(false);
  
  // Sensibull-style controls
  const [niftyTarget, setNiftyTarget] = useState<number>(0); // Percentage change
  const [niftyTargetPrice, setNiftyTargetPrice] = useState<number>(currentPrice);
  const [daysToExpiry, setDaysToExpiry] = useState<number>(0);
  const [targetDate, setTargetDate] = useState<Date>(new Date());
  const [addBookedPnL, setAddBookedPnL] = useState<boolean>(false);
  const [invertPrice, setInvertPrice] = useState<boolean>(false);
  const [multiplyByLotSize, setMultiplyByLotSize] = useState<boolean>(false);
  const [multiplyByLots, setMultiplyByLots] = useState<boolean>(false);
  
  // IVs and Standard Deviation
  const [strikewiseIVs, setStrikewiseIVs] = useState<Array<{strike: number, iv: number, expiry: string}>>([]);
  const [standardDeviation, setStandardDeviation] = useState<{sd1: number, sd2: number, price1: number, price2: number} | null>(null);
  
  // Strategy adjustment controls (Sensibull-style)
  const [strategyShift, setStrategyShift] = useState<number>(0);
  const [strategyWidth, setStrategyWidth] = useState<number>(0);
  const [strategyHedge, setStrategyHedge] = useState<number>(0);
  const [multiplier, setMultiplier] = useState<number>(1);
  const [selectedLegs, setSelectedLegs] = useState<Set<string>>(new Set());
  
  const isCalculatingRef = useRef(false);
  const calculationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Memoize calculateStrategyMetrics to prevent unnecessary recreations
  // Use strategy.legs.length and a ref to track legs to avoid dependency issues
  const strategyLegsRef = useRef(strategy.legs);
  strategyLegsRef.current = strategy.legs;

  // Fetch current price when symbol changes
  useEffect(() => {
    const fetchCurrentPrice = async () => {
      if (!selectedSymbol) return;
      
      setPriceLoading(true);
      try {
        const quote = await api.getQuote(selectedSymbol, 'NSE');
        if (quote && quote.last_price) {
          setCurrentPrice(quote.last_price);
          // Update nifty target price to match new current price
          setNiftyTargetPrice(quote.last_price);
          toast.success(`Current price updated: ₹${quote.last_price.toFixed(2)}`);
        }
      } catch (error: any) {
        console.error('Failed to fetch current price:', error);
        // Keep existing price or use default
        toast.error('Failed to fetch current price. Using default value.');
      } finally {
        setPriceLoading(false);
      }
    };

    fetchCurrentPrice();
    
    // Set up interval to refresh price every 30 seconds during market hours
    const priceInterval = setInterval(fetchCurrentPrice, 30000);
    
    return () => clearInterval(priceInterval);
  }, [selectedSymbol]);
  
  const calculateStrategyMetrics = useCallback(async () => {
    const legs = strategyLegsRef.current;
    if (legs.length === 0) return;

    setLoading(true);
    try {
      const targetPrice = niftyTargetPrice || currentPrice;
      const response = await httpClient.post('/api/comprehensive-trading/strategy/calculate', {
        symbol: selectedSymbol,
        legs: legs.map(leg => ({
          action: leg.action,
          instrument: leg.instrument,
          expiry: expiryDate,
          strike: leg.strike,
          quantity: leg.quantity,
          price: leg.price,
          lotSize: leg.lotSize || 50
        })),
        current_price: targetPrice,
        days_to_expiry: daysToExpiry || 30
      }) as any;

      if (response.success && response.data) {
        setMetrics(response.data);
      }
    } catch (error: any) {
      handleApiErrorWithLog(error, 'Failed to calculate strategy metrics', 'calculateStrategyMetrics');
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, expiryDate, currentPrice, niftyTargetPrice, daysToExpiry]);
  
  // Debounced calculation to prevent too many API calls
  useEffect(() => {
    if (isCalculatingRef.current) return;
    
    // Clear any pending calculation
    if (calculationTimeoutRef.current) {
      clearTimeout(calculationTimeoutRef.current);
    }
    
    if (strategy.legs.length > 0) {
      // Debounce the calculation by 300ms to avoid rapid-fire API calls
      calculationTimeoutRef.current = setTimeout(() => {
        if (isCalculatingRef.current) return;
        isCalculatingRef.current = true;
        calculateStrategyMetrics().finally(() => {
          isCalculatingRef.current = false;
        });
      }, 300);
    } else {
      setMetrics(null);
    }
    
    return () => {
      if (calculationTimeoutRef.current) {
        clearTimeout(calculationTimeoutRef.current);
      }
    };
  }, [strategy.legs.length, currentPrice, expiryDate, niftyTargetPrice, daysToExpiry, selectedSymbol, calculateStrategyMetrics]);
  
  useEffect(() => {
    // Update nifty target price when percentage changes
    const newPrice = currentPrice * (1 + niftyTarget / 100);
    setNiftyTargetPrice(newPrice);
  }, [niftyTarget, currentPrice]);
  
  useEffect(() => {
    // Calculate standard deviation
    if (currentPrice > 0) {
      // Simplified SD calculation (typically based on historical volatility)
      const volatility = 0.20; // 20% annual volatility
      const timeToExpiry = Math.max(daysToExpiry, 1) / 365;
      const sd1Points = currentPrice * volatility * Math.sqrt(timeToExpiry);
      const sd2Points = currentPrice * volatility * Math.sqrt(timeToExpiry) * 2;
      
      setStandardDeviation({
        sd1: sd1Points,
        sd2: sd2Points,
        price1: currentPrice - sd1Points,
        price2: currentPrice + sd1Points,
      });
    }
  }, [currentPrice, daysToExpiry]);

  const saveStrategy = async () => {
    if (strategy.legs.length === 0) {
      toast.error('Please add at least one leg to save');
      return;
    }

    setLoading(true);
    try {
      const response = await httpClient.post('/api/comprehensive-trading/strategy/save', {
        id: strategy.id,
        name: strategy.name,
        description: strategy.description || '',
        symbol: selectedSymbol,
        legs: strategy.legs.map(leg => ({
          action: leg.action,
          instrument: leg.instrument,
          expiry: expiryDate,
          strike: leg.strike,
          quantity: leg.quantity,
          price: leg.price,
          lotSize: leg.lotSize || 50
        })),
        metrics: metrics
      }) as any;

      if (response.success && response.data) {
        setStrategy(prev => ({ ...prev, id: response.data.id }));
        toast.success('Strategy saved successfully');
        setRefreshSavedStrategies(prev => prev + 1);
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

  const addLeg = (leg: Omit<StrategyLeg, 'id'>) => {
    try {
      if (editingLeg) {
        // Update existing leg
        setStrategy(prev => ({
          ...prev,
          legs: prev.legs.map(l => l.id === editingLeg.id ? { ...leg, id: editingLeg.id } : l)
        }));
        setEditingLeg(null);
        setShowLegForm(false);
        toast.success('Leg updated successfully');
      } else {
        // Add new leg
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
      }
    } catch (error) {
      console.error('Error adding/updating leg:', error);
      toast.error('Failed to add/update leg. Please try again.');
    }
  };

  const removeLeg = (legId: string) => {
    setStrategy(prev => ({
      ...prev,
      legs: prev.legs.filter(leg => leg.id !== legId)
    }));
    toast.success('Leg removed');
  };

  const loadStrategy = (loadedStrategy: Strategy) => {
    // Ensure legs have IDs
    const strategyWithIds: Strategy = {
      ...loadedStrategy,
      legs: loadedStrategy.legs.map((leg, idx) => ({
        ...leg,
        id: leg.id || `${Date.now()}_${idx}`
      }))
    };
    setStrategy(strategyWithIds);
    
    // Set expiry date from first leg if available
    if (strategyWithIds.legs.length > 0 && strategyWithIds.legs[0].expiry) {
      setExpiryDate(strategyWithIds.legs[0].expiry);
    }
    
    // Set symbol if available
    if (loadedStrategy.symbol) {
      setSelectedSymbol(loadedStrategy.symbol);
    }
    
    if (onStrategySelect) {
      onStrategySelect(strategyWithIds);
    }
    setActiveMainTab('builder');
    toast.success(strategyWithIds.id ? 'Strategy loaded for editing' : 'Strategy loaded');
  };

  const formatDate = (date: Date): string => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${days[date.getDay()]}, ${date.getDate()} ${months[date.getMonth()]} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')} ${date.getHours() >= 12 ? 'PM' : 'AM'}`;
  };

  const adjustDate = (days: number) => {
    const newDate = new Date(targetDate);
    newDate.setDate(newDate.getDate() + days);
    setTargetDate(newDate);
    const diffDays = Math.ceil((newDate.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
    setDaysToExpiry(Math.max(0, diffDays));
  };

  return (
    <div className="flex flex-col h-full bg-white text-gray-900">
      {/* Top Navigation - Main Tabs */}
      <div className="flex border-b border-gray-300 bg-white">
        <button
          onClick={() => setActiveMainTab('builder')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${
            activeMainTab === 'builder'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Strategy Builder
        </button>
        <button
          onClick={() => setActiveMainTab('suggested')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${
            activeMainTab === 'suggested'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Ready-made
        </button>
        <button
          onClick={() => {
            setActiveMainTab('saved');
            setRefreshSavedStrategies(prev => prev + 1);
          }}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${
            activeMainTab === 'saved'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Saved Strategies
        </button>
        {showPaperTrading && (
          <button
            onClick={() => setActiveMainTab('paper')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeMainTab === 'paper'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Positions
          </button>
        )}
        <div className="flex-1"></div>
        <div className="flex items-center px-4 border-l border-gray-300">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={addBookedPnL}
              onChange={(e) => setAddBookedPnL(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-700">Add Booked P&L</span>
          </label>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto">
        {activeMainTab === 'builder' && (
          <div className="flex flex-col h-full">
            {/* Symbol and Expiry Selection */}
            <div className="bg-gray-50 border-b border-gray-200 p-4">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
                  <StockSelector
                    value={selectedSymbol}
                    onChange={setSelectedSymbol}
                    className="w-full"
                  />
                </div>
                <div className="w-48">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Expiry</label>
                  <input
                    type="text"
                    value={expiryDate}
                    onChange={(e) => setExpiryDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900"
                    placeholder="30 Dec"
                  />
                </div>
              </div>
            </div>

            {/* Strategy Legs Section - Sensibull Style */}
            <div className="p-4 border-b border-gray-200 bg-white">
              {/* Header with Tabs and Selection */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <h3 className={`text-lg font-semibold ${strategy.name === 'New Strategy' ? 'font-bold' : ''}`}>
                    {strategy.name}
                  </h3>
                  <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                    Insights
                  </button>
                </div>
                <div className="flex items-center gap-4">
                  {strategy.legs.length > 0 && (
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedLegs.size === strategy.legs.length && strategy.legs.length > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedLegs(new Set(strategy.legs.map(l => l.id)));
                          } else {
                            setSelectedLegs(new Set());
                          }
                        }}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                      <span className="text-sm text-gray-600">
                        {selectedLegs.size || strategy.legs.length} selected
                      </span>
                    </div>
                  )}
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        if (selectedLegs.size > 0) {
                          setStrategy(prev => ({
                            ...prev,
                            legs: prev.legs.filter(l => !selectedLegs.has(l.id))
                          }));
                          setSelectedLegs(new Set());
                          toast.success('Selected legs cleared');
                        } else {
                          clearStrategy();
                        }
                      }}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Clear New Trades
                    </button>
                    <button
                      onClick={() => {
                        // Reset all prices to current market prices
                        toast.success('Prices reset');
                      }}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                    >
                      <RefreshCw className="w-3 h-3" />
                      Reset Prices
                    </button>
                  </div>
                </div>
              </div>

              {/* Strategy Name Input */}
              <div className="mb-4">
                <input
                  type="text"
                  value={strategy.name}
                  onChange={(e) => setStrategy(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="New Strategy"
                  className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Legs Table - Sensibull Style */}
              {strategy.legs.length === 0 ? (
                <div className="text-center py-12 text-gray-400 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                  <Calculator className="w-16 h-16 mx-auto mb-3 opacity-50" />
                  <p className="text-lg font-medium">No legs added yet</p>
                  <p className="text-sm mt-1">Click 'Add Leg' to start building your strategy</p>
                  <button
                    onClick={() => setShowLegForm(true)}
                    className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white flex items-center gap-2 mx-auto"
                  >
                    <Plus className="w-4 h-4" />
                    Add Leg
                  </button>
                </div>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-700">B/S</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-700">Expiry</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-700">Strike</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-700">Type</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-700">Lots</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-700">Price</th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-700">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {strategy.legs.map((leg, idx) => (
                        <tr key={typeof leg.id === 'string' ? leg.id : `leg-${idx}-${Date.now()}`} className="hover:bg-gray-50">
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={selectedLegs.has(typeof leg.id === 'string' ? leg.id : String(leg.id || ''))}
                                onChange={(e) => {
                                  const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                  const newSelected = new Set(selectedLegs);
                                  if (e.target.checked) {
                                    newSelected.add(legId);
                                  } else {
                                    newSelected.delete(legId);
                                  }
                                  setSelectedLegs(newSelected);
                                }}
                                className="w-4 h-4 text-blue-600 rounded"
                              />
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                (typeof leg.action === 'string' ? leg.action : String(leg.action || 'BUY')) === 'BUY' 
                                  ? 'bg-blue-600 text-white' 
                                  : 'bg-red-600 text-white'
                              }`}>
                                {(typeof leg.action === 'string' ? leg.action : String(leg.action || 'BUY')) === 'BUY' ? 'B' : 'S'}
                              </span>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <select
                              value={typeof leg.expiry === 'string' ? leg.expiry : String(leg.expiry || expiryDate)}
                              onChange={(e) => {
                                const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                setStrategy(prev => ({
                                  ...prev,
                                  legs: prev.legs.map(l => {
                                    const lId = typeof l.id === 'string' ? l.id : String(l.id || '');
                                    return lId === legId ? { ...l, expiry: e.target.value } : l;
                                  })
                                }));
                              }}
                              className="text-sm border border-gray-300 rounded px-2 py-1 text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                              <option value="06 Jan">06 Jan</option>
                              <option value="13 Jan">13 Jan</option>
                              <option value="20 Jan">20 Jan</option>
                              <option value="27 Jan">27 Jan</option>
                              <option value="30 Dec">30 Dec</option>
                            </select>
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => {
                                  const strikeStep = 50; // NIFTY strike step
                                  const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                  const currentStrike = typeof leg.strike === 'number' ? leg.strike : parseFloat(String(leg.strike)) || 0;
                                  setStrategy(prev => ({
                                    ...prev,
                                    legs: prev.legs.map(l => {
                                      const lId = typeof l.id === 'string' ? l.id : String(l.id || '');
                                      return lId === legId ? { ...l, strike: Math.max(0, currentStrike - strikeStep) } : l;
                                    })
                                  }));
                                }}
                                className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
                              >
                                -
                              </button>
                              <input
                                type="number"
                                value={typeof leg.strike === 'number' ? leg.strike : (parseFloat(String(leg.strike)) || 0)}
                                onChange={(e) => {
                                  const strike = parseInt(e.target.value) || 0;
                                  const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                  setStrategy(prev => ({
                                    ...prev,
                                    legs: prev.legs.map(l => {
                                      const lId = typeof l.id === 'string' ? l.id : String(l.id || '');
                                      return lId === legId ? { ...l, strike } : l;
                                    })
                                  }));
                                }}
                                className="w-20 px-2 py-1 border border-gray-300 rounded text-center text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                              <button
                                onClick={() => {
                                  const strikeStep = 50;
                                  const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                  const currentStrike = typeof leg.strike === 'number' ? leg.strike : parseFloat(String(leg.strike)) || 0;
                                  setStrategy(prev => ({
                                    ...prev,
                                    legs: prev.legs.map(l => {
                                      const lId = typeof l.id === 'string' ? l.id : String(l.id || '');
                                      return lId === legId ? { ...l, strike: currentStrike + strikeStep } : l;
                                    })
                                  }));
                                }}
                                className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
                              >
                                +
                              </button>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <select
                              value={typeof leg.instrument === 'string' ? leg.instrument : String(leg.instrument || 'CE')}
                              onChange={(e) => {
                                const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                setStrategy(prev => ({
                                  ...prev,
                                  legs: prev.legs.map(l => {
                                    const lId = typeof l.id === 'string' ? l.id : String(l.id || '');
                                    return lId === legId ? { ...l, instrument: e.target.value as 'CE' | 'PE' | 'FUT' } : l;
                                  })
                                }));
                              }}
                              className="text-sm border border-gray-300 rounded px-2 py-1 text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                              <option value="CE">CE</option>
                              <option value="PE">PE</option>
                              <option value="FUT">FUT</option>
                            </select>
                          </td>
                          <td className="px-3 py-3">
                            <select
                              value={typeof leg.quantity === 'number' ? leg.quantity : (parseInt(String(leg.quantity)) || 1)}
                              onChange={(e) => {
                                const qty = parseInt(e.target.value) || 1;
                                const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                setStrategy(prev => ({
                                  ...prev,
                                  legs: prev.legs.map(l => {
                                    const lId = typeof l.id === 'string' ? l.id : String(l.id || '');
                                    return lId === legId ? { ...l, quantity: qty } : l;
                                  })
                                }));
                              }}
                              className="text-sm border border-gray-300 rounded px-2 py-1 text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                              {[1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 75, 100].map(qty => (
                                <option key={qty} value={qty}>{qty}</option>
                              ))}
                            </select>
                          </td>
                          <td className="px-3 py-3 text-right">
                            <input
                              type="number"
                              value={typeof leg.price === 'number' ? leg.price : (parseFloat(String(leg.price)) || 0)}
                              onChange={(e) => {
                                const price = parseFloat(e.target.value) || 0;
                                const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                setStrategy(prev => ({
                                  ...prev,
                                  legs: prev.legs.map(l => {
                                    const lId = typeof l.id === 'string' ? l.id : String(l.id || '');
                                    return lId === legId ? { ...l, price } : l;
                                  })
                                }));
                              }}
                              className="w-20 px-2 py-1 border border-gray-300 rounded text-right text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                              step="0.01"
                            />
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => {
                                  setEditingLeg(leg);
                                  setShowLegForm(true);
                                }}
                                className="p-1 hover:bg-gray-100 rounded text-gray-600"
                                title="Edit leg"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => {
                                  const legId = typeof leg.id === 'string' ? leg.id : String(leg.id || '');
                                  removeLeg(legId);
                                }}
                                className="p-1 hover:bg-red-100 rounded text-red-600"
                                title="Delete leg"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  
                  {/* Add Leg Button */}
                  <div className="p-3 border-t border-gray-200 bg-gray-50">
                    <button
                      onClick={() => setShowLegForm(true)}
                      className="w-full px-4 py-2 bg-white border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50 flex items-center justify-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Leg
                    </button>
                  </div>
                </div>
              )}

              {/* Strategy Adjustment Controls - Sensibull Style */}
              {strategy.legs.length > 0 && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Shift</label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setStrategyShift(prev => prev - 50)}
                          className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
                        >
                          -
                        </button>
                        <input
                          type="number"
                          value={strategyShift}
                          onChange={(e) => setStrategyShift(parseInt(e.target.value) || 0)}
                          className="w-20 px-2 py-1 border border-gray-300 rounded text-center text-sm text-gray-900 focus:outline-none"
                        />
                        <button
                          onClick={() => setStrategyShift(prev => prev + 50)}
                          className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
                        >
                          +
                        </button>
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Width</label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setStrategyWidth(prev => Math.max(0, prev - 50))}
                          className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
                        >
                          -
                        </button>
                        <input
                          type="number"
                          value={strategyWidth}
                          onChange={(e) => setStrategyWidth(parseInt(e.target.value) || 0)}
                          className="w-20 px-2 py-1 border border-gray-300 rounded text-center text-sm text-gray-900 focus:outline-none"
                        />
                        <button
                          onClick={() => setStrategyWidth(prev => prev + 50)}
                          className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
                        >
                          +
                        </button>
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Hedge</label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setStrategyHedge(prev => prev - 50)}
                          className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
                        >
                          -
                        </button>
                        <input
                          type="number"
                          value={strategyHedge}
                          onChange={(e) => setStrategyHedge(parseInt(e.target.value) || 0)}
                          className="w-20 px-2 py-1 border border-gray-300 rounded text-center text-sm text-gray-900 focus:outline-none"
                        />
                        <button
                          onClick={() => setStrategyHedge(prev => prev + 50)}
                          className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Summary and Action Buttons - Sensibull Style */}
              {strategy.legs.length > 0 && (
                <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">Multiplier</label>
                        <select
                          value={multiplier}
                          onChange={(e) => setMultiplier(parseInt(e.target.value) || 1)}
                          className="px-3 py-1 border border-gray-300 rounded text-sm text-gray-900 focus:outline-none"
                        >
                          {[1, 2, 3, 4, 5, 10].map(m => (
                            <option key={m} value={m}>{m}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Price Pay</div>
                        <div className="text-lg font-semibold text-gray-900">
                          ₹{strategy.legs.reduce((sum, leg) => {
                            const price = typeof leg.price === 'number' ? leg.price : parseFloat(String(leg.price)) || 0;
                            const quantity = typeof leg.quantity === 'number' ? leg.quantity : parseInt(String(leg.quantity)) || 1;
                            return sum + (price * quantity * multiplier);
                          }, 0).toFixed(2)}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Premium Pay</div>
                        <div className="text-lg font-semibold text-gray-900">
                          ₹{(strategy.legs.reduce((sum, leg) => {
                            const price = typeof leg.price === 'number' ? leg.price : parseFloat(String(leg.price)) || 0;
                            const quantity = typeof leg.quantity === 'number' ? leg.quantity : parseInt(String(leg.quantity)) || 1;
                            const lotSize = typeof leg.lotSize === 'number' ? leg.lotSize : parseInt(String(leg.lotSize)) || 50;
                            return sum + (price * quantity * multiplier * lotSize);
                          }, 0)).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          if (editingLeg) {
                            setShowLegForm(true);
                          } else {
                            setShowLegForm(true);
                          }
                        }}
                        className="px-4 py-2 border border-blue-600 text-blue-600 rounded text-sm font-medium hover:bg-blue-50"
                      >
                        Add/Edit
                      </button>
                      <button
                        onClick={saveStrategy}
                        disabled={loading}
                        className="px-4 py-2 border border-blue-600 text-blue-600 rounded text-sm font-medium hover:bg-blue-50 disabled:opacity-50"
                      >
                        Add to Drafts
                      </button>
                      <button
                        onClick={async () => {
                          if (!strategy.legs || strategy.legs.length === 0) {
                            toast.error('Please add at least one leg to the strategy');
                            return;
                          }
                          
                          setLoading(true);
                          try {
                            // Save strategy first (don't execute yet)
                            const saveResponse = await httpClient.post('/api/comprehensive-trading/strategy/save', {
                              id: strategy.id,
                              name: strategy.name || `${strategy.legs.length} Leg Strategy`,
                              description: strategy.description || '',
                              symbol: selectedSymbol,
                              legs: strategy.legs.map(leg => ({
                                action: leg.action,
                                instrument: leg.instrument,
                                expiry: leg.expiry || expiryDate,
                                strike: leg.strike,
                                quantity: leg.quantity,
                                price: leg.price,
                                lotSize: leg.lotSize || 50
                              })),
                              metrics: metrics
                            }) as any;

                            if (saveResponse.success && saveResponse.data) {
                              // Update strategy with saved ID
                              const savedStrategy = { ...strategy, id: saveResponse.data.id };
                              setStrategy(savedStrategy);
                              
                              // Navigate to positions page
                              toast.success('Strategy saved! Navigate to Positions to start trading.');
                              
                              // Switch to Positions tab
                              setActiveMainTab('paper');
                              setRefreshSavedStrategies(prev => prev + 1);
                              
                              if (onStrategySelect) {
                                onStrategySelect(savedStrategy);
                              }
                            } else {
                              toast.error('Failed to save strategy');
                            }
                          } catch (error: any) {
                            console.error('Error saving strategy:', error);
                            toast.error(error?.response?.data?.detail || 'Failed to save strategy');
                          } finally {
                            setLoading(false);
                          }
                        }}
                        disabled={loading || !strategy.legs || strategy.legs.length === 0}
                        className="px-6 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {loading ? 'Saving...' : 'Trade All'}
                      </button>
                      <button className="px-2 py-2 text-gray-600 hover:bg-gray-100 rounded">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* View Tabs (Payoff Graph, P&L Table, Greeks, Strategy Chart) */}
            <div className="flex-1 flex flex-col">
              <div className="flex border-b border-gray-300 bg-white">
                <button
                  onClick={() => setActiveViewTab('payoff')}
                  className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                    activeViewTab === 'payoff'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Payoff Graph
                </button>
                <button
                  onClick={() => setActiveViewTab('pnl')}
                  className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                    activeViewTab === 'pnl'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  P&L Table
                </button>
                <button
                  onClick={() => setActiveViewTab('greeks')}
                  className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                    activeViewTab === 'greeks'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Greeks
                </button>
                <button
                  onClick={() => setActiveViewTab('chart')}
                  className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                    activeViewTab === 'chart'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Strategy Chart
                </button>
              </div>

              {/* Controls Section */}
              <div className="bg-gray-50 border-b border-gray-200 p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* NIFTY Target */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">NIFTY Target</label>
                      <button
                        onClick={() => {
                          setNiftyTarget(0);
                          setNiftyTargetPrice(currentPrice);
                        }}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Reset
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setNiftyTarget(prev => Math.max(-50, prev - 1))}
                        className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100"
                      >
                        -
                      </button>
                      <input
                        type="number"
                        value={niftyTarget.toFixed(1)}
                        onChange={(e) => setNiftyTarget(parseFloat(e.target.value) || 0)}
                        className="w-20 px-2 py-1 border border-gray-300 rounded text-center text-gray-900"
                        step="0.1"
                      />
                      <span className="text-sm text-gray-600">%</span>
                      <input
                        type="number"
                        value={niftyTargetPrice.toFixed(2)}
                        onChange={(e) => {
                          const price = parseFloat(e.target.value) || currentPrice;
                          setNiftyTargetPrice(price);
                          setNiftyTarget(((price / currentPrice - 1) * 100));
                        }}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-gray-900"
                        step="0.01"
                      />
                      <button
                        onClick={() => setNiftyTarget(prev => Math.min(50, prev + 1))}
                        className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100"
                      >
                        +
                      </button>
                    </div>
                    <input
                      type="range"
                      min="-50"
                      max="50"
                      value={niftyTarget}
                      onChange={(e) => setNiftyTarget(parseFloat(e.target.value))}
                      className="w-full mt-2"
                    />
                  </div>

                  {/* Date Control */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700 flex items-center gap-1">
                        Date: {daysToExpiry}D to expiry
                        <HelpCircle className="w-3 h-3 text-gray-400" />
                      </label>
                      <button
                        onClick={() => {
                          setTargetDate(new Date());
                          setDaysToExpiry(0);
                        }}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Reset
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => adjustDate(-1)}
                        className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <div className="flex-1 px-3 py-1 border border-gray-300 rounded text-center text-gray-900">
                        {formatDate(targetDate)}
                      </div>
                      <button
                        onClick={() => adjustDate(1)}
                        className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="365"
                      value={daysToExpiry}
                      onChange={(e) => {
                        const days = parseInt(e.target.value);
                        setDaysToExpiry(days);
                        const newDate = new Date();
                        newDate.setDate(newDate.getDate() + days);
                        setTargetDate(newDate);
                      }}
                      className="w-full mt-2"
                    />
                  </div>
                </div>
              </div>

              {/* View Content */}
              <div className="flex-1 overflow-auto">
                {activeViewTab === 'payoff' && (
                  <div className="p-4">
                    {strategy.legs.length > 0 ? (
                      <PayoffChart
                        legs={strategy.legs}
                        currentPrice={niftyTargetPrice || currentPrice}
                        metrics={metrics}
                        symbol={selectedSymbol}
                      />
                    ) : (
                      <div className="text-center py-12 text-gray-400">
                        <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p>Add strategy legs to see payoff graph</p>
                      </div>
                    )}
                    
                    {/* Strikewise IVs and Standard Deviation Section */}
                    <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* Strikewise IVs */}
                      <div className="bg-white rounded-lg border border-gray-200 p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-sm font-semibold text-gray-900">Strikewise IVs</h4>
                          <button
                            onClick={() => setStrikewiseIVs([])}
                            className="text-xs text-blue-600 hover:underline"
                          >
                            Reset IVs
                          </button>
                        </div>
                        <div className="mb-3">
                          <label className="block text-xs text-gray-600 mb-1">Offset</label>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => {}}
                              className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100"
                            >
                              -
                            </button>
                            <input
                              type="number"
                              value="0"
                              readOnly
                              className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-gray-900"
                            />
                            <button
                              onClick={() => {}}
                              className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-100"
                            >
                              +
                            </button>
                          </div>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="border-b border-gray-200">
                                <th className="text-left py-2 text-gray-700">Strike</th>
                                <th className="text-left py-2 text-gray-700">Expiry</th>
                                <th className="text-right py-2 text-gray-700">IV</th>
                                <th className="text-right py-2 text-gray-700">Chg</th>
                              </tr>
                            </thead>
                            <tbody>
                              {strategy.legs.filter(l => l.instrument !== 'FUT').map((leg, idx) => (
                                <tr key={leg.id} className="border-b border-gray-100">
                                  <td className="py-2 text-gray-900">{leg.strike}</td>
                                  <td className="py-2 text-gray-600">{leg.expiry}</td>
                                  <td className="py-2 text-right">
                                    <div className="flex items-center justify-end gap-1">
                                      <input
                                        type="number"
                                        value="0"
                                        readOnly
                                        className="w-16 px-1 py-0.5 border border-gray-300 rounded text-gray-900"
                                      />
                                      <button className="px-1 py-0.5 border border-gray-300 rounded hover:bg-gray-100">-</button>
                                      <button className="px-1 py-0.5 border border-gray-300 rounded hover:bg-gray-100">+</button>
                                    </div>
                                  </td>
                                  <td className="py-2 text-right text-gray-600">(-9.3)</td>
                                </tr>
                              ))}
                              {strategy.legs.filter(l => l.instrument !== 'FUT').length === 0 && (
                                <tr>
                                  <td colSpan={4} className="py-4 text-center text-gray-400 text-xs">
                                    No options legs to show IVs
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Standard Deviation */}
                      <div className="bg-white rounded-lg border border-gray-200 p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-1">
                            Standard Deviation
                            <HelpCircle className="w-3 h-3 text-gray-400" />
                          </h4>
                        </div>
                        {standardDeviation ? (
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="border-b border-gray-200">
                                  <th className="text-left py-2 text-gray-700">SD</th>
                                  <th className="text-right py-2 text-gray-700">Points</th>
                                  <th className="text-right py-2 text-gray-700">Price</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr className="border-b border-gray-100">
                                  <td className="py-2 text-gray-900">-2SD</td>
                                  <td className="py-2 text-right text-gray-600">
                                    {standardDeviation.sd2.toFixed(1)} ({((standardDeviation.sd2 / currentPrice) * 100).toFixed(1)}%)
                                  </td>
                                  <td className="py-2 text-right text-gray-900">
                                    {(currentPrice - standardDeviation.sd2).toFixed(2)}
                                  </td>
                                </tr>
                                <tr className="border-b border-gray-100">
                                  <td className="py-2 text-gray-900">-1SD</td>
                                  <td className="py-2 text-right text-gray-600">
                                    {standardDeviation.sd1.toFixed(1)} ({((standardDeviation.sd1 / currentPrice) * 100).toFixed(1)}%)
                                  </td>
                                  <td className="py-2 text-right text-gray-900">
                                    {(currentPrice - standardDeviation.sd1).toFixed(2)}
                                  </td>
                                </tr>
                                <tr className="border-b border-gray-100">
                                  <td className="py-2 text-gray-900">1SD</td>
                                  <td className="py-2 text-right text-gray-600">
                                    {standardDeviation.sd1.toFixed(1)} ({((standardDeviation.sd1 / currentPrice) * 100).toFixed(1)}%)
                                  </td>
                                  <td className="py-2 text-right text-gray-900">
                                    {(currentPrice + standardDeviation.sd1).toFixed(2)}
                                  </td>
                                </tr>
                                <tr>
                                  <td className="py-2 text-gray-900">2SD</td>
                                  <td className="py-2 text-right text-gray-600">
                                    {standardDeviation.sd2.toFixed(1)} ({((standardDeviation.sd2 / currentPrice) * 100).toFixed(1)}%)
                                  </td>
                                  <td className="py-2 text-right text-gray-900">
                                    {(currentPrice + standardDeviation.sd2).toFixed(2)}
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className="text-center py-4 text-gray-400 text-xs">
                            Calculate strategy to see standard deviation
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                {activeViewTab === 'pnl' && (
                  <PnLTable
                    legs={strategy.legs}
                    currentPrice={niftyTargetPrice || currentPrice}
                    metrics={metrics}
                  />
                )}
                {activeViewTab === 'greeks' && (
                  <GreeksView
                    legs={strategy.legs}
                    metrics={metrics}
                    multiplyByLotSize={multiplyByLotSize}
                    multiplyByLots={multiplyByLots}
                    onToggleLotSize={() => setMultiplyByLotSize(!multiplyByLotSize)}
                    onToggleLots={() => setMultiplyByLots(!multiplyByLots)}
                  />
                )}
                {activeViewTab === 'chart' && (
                  <StrategyChart
                    legs={strategy.legs}
                    currentPrice={currentPrice}
                    symbol={selectedSymbol}
                    invertPrice={invertPrice}
                    onToggleInvert={() => setInvertPrice(!invertPrice)}
                  />
                )}
              </div>
            </div>
          </div>
        )}

        {activeMainTab === 'suggested' && (
          <SuggestedStrategies
            symbol={selectedSymbol}
            onStrategySelect={loadStrategy}
          />
        )}

        {activeMainTab === 'saved' && (
          <SavedStrategies
            key={refreshSavedStrategies}
            symbol={selectedSymbol}
            onStrategySelect={loadStrategy}
            onStrategyDelete={() => {
              if (strategy.id) {
                setStrategy({ name: 'New Strategy', legs: [] });
                setMetrics(null);
              }
            }}
          />
        )}

        {activeMainTab === 'paper' && showPaperTrading && (
          <PaperTrading
            strategy={strategy.legs && strategy.legs.length > 0 ? strategy : undefined}
            symbol={selectedSymbol}
            currentPrice={currentPrice}
          />
        )}
      </div>

      {/* Leg Form Modal */}
      {showLegForm && (
        <LegForm
          onAdd={addLeg}
          onClose={() => {
            setShowLegForm(false);
            setEditingLeg(null);
          }}
          expiryDate={expiryDate}
          editingLeg={editingLeg}
        />
      )}
    </div>
  );
};

// Leg Form Component
interface LegFormProps {
  onAdd: (leg: Omit<StrategyLeg, 'id'>) => void;
  onClose: () => void;
  expiryDate: string;
  editingLeg?: StrategyLeg | null;
}

const LegForm: React.FC<LegFormProps> = ({ onAdd, onClose, expiryDate, editingLeg }) => {
  const [formData, setFormData] = useState({
    action: (editingLeg?.action || 'BUY') as 'BUY' | 'SELL',
    instrument: (editingLeg?.instrument || 'CE') as 'CE' | 'PE' | 'FUT',
    expiry: editingLeg?.expiry || expiryDate,
    strike: editingLeg?.strike || 0,
    quantity: editingLeg?.quantity || 1,
    price: editingLeg?.price || 0,
    lotSize: editingLeg?.lotSize || 50
  });

  // Update form data when editingLeg changes
  useEffect(() => {
    if (editingLeg) {
      setFormData({
        action: editingLeg.action,
        instrument: editingLeg.instrument,
        expiry: editingLeg.expiry || expiryDate,
        strike: editingLeg.strike || 0,
        quantity: editingLeg.quantity || 1,
        price: editingLeg.price || 0,
        lotSize: editingLeg.lotSize || 50
      });
    } else {
      setFormData({
        action: 'BUY',
        instrument: 'CE',
        expiry: expiryDate,
        strike: 0,
        quantity: 1,
        price: 0,
        lotSize: 50
      });
    }
  }, [editingLeg, expiryDate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if ((formData.instrument === 'CE' || formData.instrument === 'PE') && (!formData.strike || formData.strike <= 0)) {
      toast.error('Please enter a valid strike price for ' + formData.instrument);
      return;
    }
    
    onAdd(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">
          {editingLeg ? 'Edit Strategy Leg' : 'Add Strategy Leg'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
            <select
              value={formData.action}
              onChange={(e) => setFormData(prev => ({ ...prev, action: e.target.value as 'BUY' | 'SELL' }))}
              className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900"
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Instrument</label>
            <select
              value={formData.instrument}
              onChange={(e) => setFormData(prev => ({ ...prev, instrument: e.target.value as 'CE' | 'PE' | 'FUT' }))}
              className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900"
            >
              <option value="CE">Call (CE)</option>
              <option value="PE">Put (PE)</option>
              <option value="FUT">Future (FUT)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Expiry</label>
            <input
              type="text"
              value={formData.expiry}
              onChange={(e) => setFormData(prev => ({ ...prev, expiry: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900"
              placeholder="30 Dec"
            />
          </div>
          {(formData.instrument === 'CE' || formData.instrument === 'PE') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Strike Price</label>
              <input
                type="number"
                value={formData.strike != null ? formData.strike : ''}
                onChange={(e) => setFormData(prev => ({ ...prev, strike: parseFloat(e.target.value) || 0 }))}
                className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900"
                required
                step="0.01"
              />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
            <input
              type="number"
              value={formData.quantity}
              onChange={(e) => setFormData(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
              className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900"
              min="1"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Entry Price</label>
            <input
              type="number"
              value={formData.price}
              onChange={(e) => setFormData(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
              className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900"
              step="0.01"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lot Size</label>
            <input
              type="number"
              value={formData.lotSize}
              onChange={(e) => setFormData(prev => ({ ...prev, lotSize: parseInt(e.target.value) || 50 }))}
              className="w-full px-3 py-2 border border-gray-300 rounded text-gray-900"
              min="1"
            />
          </div>
          <div className="flex gap-2 pt-4">
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
            >
              {editingLeg ? 'Update Leg' : 'Add Leg'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-gray-700"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EnhancedStrategyBuilder;

