/**
 * Options Chain Builder Component
 * Sensibull-style interface with Options Chain, Strategy Editor, and Orders
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Search, ChevronDown, TrendingUp, TrendingDown,
  FileText, BookOpen, X, Plus, Trash2, CheckCircle
} from 'lucide-react';
import StockSelector from '../StockSelector';
import EnhancedStrategyBuilder from '../strategy/EnhancedStrategyBuilder';
import { httpClient } from '../../config/api';
import { toast } from 'react-hot-toast';

interface OptionsChainBuilderProps {
  symbol?: string;
  onSymbolChange?: (symbol: string) => void;
}

interface StrikeData {
  strike: number;
  callDelta: number;
  callLTP: number;
  callOI: number;
  callIV: number;
  putDelta: number;
  putLTP: number;
  putOI: number;
  putIV: number;
}

interface SelectedLeg {
  strike: number;
  optionType: 'CALL' | 'PUT';
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
}

interface StrategyTemplate {
  name: string;
  outlook: 'Bullish' | 'Bearish' | 'Neutral' | 'Others';
  icon: string;
}

const OptionsChainBuilder: React.FC<OptionsChainBuilderProps> = ({ 
  symbol = 'NIFTY',
  onSymbolChange 
}) => {
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);
  const [expiryDate, setExpiryDate] = useState('30 Dec');
  const [chainView, setChainView] = useState<'LTP' | 'OI' | 'Greeks'>('LTP');
  const [chainTab, setChainTab] = useState<'Straddles' | 'Strangles' | 'Strikes' | 'Futures'>('Strikes');
  const [strikesData, setStrikesData] = useState<StrikeData[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPrice, setCurrentPrice] = useState(26042.30);
  const [selectedStrategy, setSelectedStrategy] = useState<any>(null);
  const [strategyOutlook, setStrategyOutlook] = useState<'Bullish' | 'Bearish' | 'Neutral' | 'Others'>('Bullish');
  const [selectedLegs, setSelectedLegs] = useState<SelectedLeg[]>([]);
  const [highlightedStrikes, setHighlightedStrikes] = useState<Set<number>>(new Set());

  // Generate expiry dates (last Thursday of each month for next 6 months)
  const generateExpiryDates = (): string[] => {
    const dates: string[] = [];
    const today = new Date();
    for (let i = 0; i < 6; i++) {
      const date = new Date(today.getFullYear(), today.getMonth() + i, 1);
      // Find last Thursday
      const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
      let thursday = new Date(lastDay);
      thursday.setDate(lastDay.getDate() - ((lastDay.getDay() + 3) % 7));
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      dates.push(`${thursday.getDate()} ${monthNames[thursday.getMonth()]}`);
    }
    return dates;
  };

  const expiryDates = generateExpiryDates();

  // Strategy templates matching Sensibull
  const strategyTemplates: StrategyTemplate[] = [
    { name: 'Buy Call', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Sell Put', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Bull Call Spread', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Bull Put Spread', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Call Ratio Back Spread', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Long Calendar with Calls', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Bull Condor', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Bull Butterfly', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Range Forward', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Buy Future', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Long Synthetic Future', outlook: 'Bullish', icon: 'TrendingUp' },
    { name: 'Sell Call', outlook: 'Bearish', icon: 'TrendingDown' },
    { name: 'Buy Put', outlook: 'Bearish', icon: 'TrendingDown' },
    { name: 'Bear Call Spread', outlook: 'Bearish', icon: 'TrendingDown' },
    { name: 'Bear Put Spread', outlook: 'Bearish', icon: 'TrendingDown' },
    { name: 'Iron Condor', outlook: 'Neutral', icon: 'FileText' },
    { name: 'Short Straddle', outlook: 'Neutral', icon: 'FileText' },
    { name: 'Short Strangle', outlook: 'Neutral', icon: 'FileText' },
  ];

  const filteredStrategies = strategyTemplates.filter(s => s.outlook === strategyOutlook);

  const fetchCurrentPrice = useCallback(async () => {
    try {
      const response = await httpClient.get(`/api/realtime/quote/${selectedSymbol}`) as any;
      if (response.success && response.data?.last_price) {
        setCurrentPrice(response.data.last_price);
      }
    } catch (error) {
      console.error('Failed to fetch current price:', error);
    }
  }, [selectedSymbol]);

  const fetchOptionsChain = useCallback(async () => {
    setLoading(true);
    try {
      // Mock data for now - replace with actual API call
      const mockStrikes: StrikeData[] = [];
      const baseStrike = Math.round(currentPrice / 50) * 50; // Round to nearest 50
      
      for (let i = -10; i <= 10; i++) {
        const strike = baseStrike + (i * 50);
        mockStrikes.push({
          strike,
          callDelta: Math.max(0, Math.min(1, 0.5 + (i * 0.05))),
          callLTP: Math.max(5, 500 - (Math.abs(i) * 30)),
          callOI: Math.floor(Math.random() * 2000) + 500,
          callIV: 15 + Math.random() * 10,
          putDelta: Math.max(-1, Math.min(0, -0.5 - (i * 0.05))),
          putLTP: Math.max(5, 500 - (Math.abs(i) * 30)),
          putOI: Math.floor(Math.random() * 2000) + 500,
          putIV: 15 + Math.random() * 10,
        });
      }
      
      setStrikesData(mockStrikes);
    } catch (error) {
      toast.error('Failed to fetch options chain');
    } finally {
      setLoading(false);
    }
  }, [currentPrice]);

  useEffect(() => {
    fetchCurrentPrice();
  }, [fetchCurrentPrice]);

  useEffect(() => {
    if (currentPrice > 0) {
      fetchOptionsChain();
    }
  }, [selectedSymbol, expiryDate, currentPrice, fetchOptionsChain]);

  const handleStrategySelect = (template: StrategyTemplate) => {
    setSelectedStrategy({
      name: template.name,
      outlook: template.outlook,
      legs: []
    });
    toast.success(`Selected ${template.name} strategy`);
  };

  const handleSymbolChange = (newSymbol: string) => {
    setSelectedSymbol(newSymbol);
    if (onSymbolChange) {
      onSymbolChange(newSymbol);
    }
  };

  const handleOptionAction = (strike: number, optionType: 'CALL' | 'PUT', action: 'BUY' | 'SELL') => {
    const strikeData = strikesData.find(s => s.strike === strike);
    if (!strikeData) return;

    const price = optionType === 'CALL' ? strikeData.callLTP : strikeData.putLTP;
    
    // Check if this leg already exists
    const existingLegIndex = selectedLegs.findIndex(
      leg => leg.strike === strike && leg.optionType === optionType
    );

    if (existingLegIndex >= 0) {
      // Update existing leg
      const updatedLegs = [...selectedLegs];
      if (updatedLegs[existingLegIndex].action === action) {
        // Same action - remove the leg
        updatedLegs.splice(existingLegIndex, 1);
        setHighlightedStrikes(prev => {
          const newSet = new Set(prev);
          newSet.delete(strike);
          return newSet;
        });
      } else {
        // Different action - update it
        updatedLegs[existingLegIndex] = {
          ...updatedLegs[existingLegIndex],
          action,
          price
        };
      }
      setSelectedLegs(updatedLegs);
    } else {
      // Add new leg
      const newLeg: SelectedLeg = {
        strike,
        optionType,
        action,
        quantity: 50, // Default quantity
        price
      };
      setSelectedLegs([...selectedLegs, newLeg]);
      setHighlightedStrikes(prev => new Set(prev).add(strike));
    }
  };

  const handleQuantityChange = (strike: number, optionType: 'CALL' | 'PUT', quantity: number) => {
    setSelectedLegs(prevLegs =>
      prevLegs.map(leg =>
        leg.strike === strike && leg.optionType === optionType
          ? { ...leg, quantity }
          : leg
      )
    );
  };

  const handleClearAll = () => {
    setSelectedLegs([]);
    setHighlightedStrikes(new Set());
    toast.success('All legs cleared');
  };

  const handleDone = () => {
    if (selectedLegs.length === 0) {
      toast.error('Please select at least one leg');
      return;
    }
    
    // Convert selected legs to StrategyLeg format expected by Strategy Builder
    const convertedLegs = selectedLegs.map((leg, index) => {
      // Ensure all values are primitives, not objects
      const strike = typeof leg.strike === 'number' ? leg.strike : parseFloat(String(leg.strike)) || 0;
      const quantity = typeof leg.quantity === 'number' ? leg.quantity : parseInt(String(leg.quantity)) || 50;
      const price = typeof leg.price === 'number' ? leg.price : parseFloat(String(leg.price)) || 0;
      const actionStr = typeof leg.action === 'string' ? leg.action : String(leg.action || 'BUY');
      const action: 'BUY' | 'SELL' = (actionStr === 'BUY' || actionStr === 'SELL') ? actionStr : 'BUY';
      const optionType = typeof leg.optionType === 'string' ? leg.optionType : String(leg.optionType || 'CALL');
      const instrumentStr = optionType === 'CALL' ? 'CE' : 'PE';
      const instrument: 'CE' | 'PE' | 'FUT' = (instrumentStr === 'CE' || instrumentStr === 'PE' || instrumentStr === 'FUT') ? instrumentStr : 'CE';
      
      return {
        id: `leg-${index + 1}-${strike}-${optionType}`,
        action: action,
        instrument: instrument,
        expiry: typeof expiryDate === 'string' ? expiryDate : String(expiryDate || '30 Dec'),
        strike: strike,
        quantity: quantity,
        price: price,
        premium: price * quantity, // Calculate total premium
        lotSize: 50 // Default lot size for NIFTY
      };
    });
    
    // Create strategy from selected legs in the format expected by EnhancedStrategyBuilder
    const strategy = {
      id: undefined, // New strategy, no ID yet
      name: `${selectedLegs.length} Leg Strategy`,
      description: `Strategy with ${selectedLegs.length} leg(s) selected from options chain`,
      symbol: selectedSymbol,
      legs: convertedLegs,
      metrics: null // Will be calculated by Strategy Builder
    };
    
    setSelectedStrategy(strategy);
    toast.success(`Strategy created with ${selectedLegs.length} leg(s). Ready to trade!`);
  };

  return (
    <div className="h-full flex gap-4 bg-white">
      {/* Left Panel - Options Chain */}
      <div className="w-1/3 border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Options Chain</h3>
            <button className="text-gray-500 hover:text-gray-700">
              <X className="w-4 h-4" />
            </button>
          </div>
          
          {/* Symbol Selector */}
          <div className="mb-3">
            <StockSelector
              value={selectedSymbol}
              onChange={handleSymbolChange}
            />
          </div>

          {/* Main Tabs */}
          <div className="flex gap-1 mb-2">
            {['Straddles', 'Strangles', 'Strikes', 'Futures'].map((tab) => (
              <button
                key={tab}
                onClick={() => setChainTab(tab as any)}
                className={`px-3 py-1.5 text-sm rounded ${
                  chainTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Expiry and View Selector */}
          <div className="flex gap-2">
            <select
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
              className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {expiryDates.map((date) => (
                <option key={date} value={date}>{date}</option>
              ))}
            </select>
            <div className="flex gap-1">
              {['LTP', 'OI', 'Greeks'].map((view) => (
                <button
                  key={view}
                  onClick={() => setChainView(view as any)}
                  className={`px-3 py-1.5 text-sm rounded ${
                    chainView === view
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {view}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Options Chain Table */}
        <div className="flex-1 overflow-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-2 py-2 text-left font-medium text-gray-700">Delta</th>
                <th className="px-2 py-2 text-right font-medium text-gray-700">Call LTP</th>
                <th className="px-2 py-2 text-right font-medium text-gray-700">Call OI</th>
                <th className="px-2 py-2 text-center font-medium text-gray-700">Strike</th>
                <th className="px-2 py-2 text-right font-medium text-gray-700">IV</th>
                <th className="px-2 py-2 text-right font-medium text-gray-700">Put OI</th>
                <th className="px-2 py-2 text-right font-medium text-gray-700">Put LTP</th>
                <th className="px-2 py-2 text-right font-medium text-gray-700">Delta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {strikesData.map((row, idx) => {
                const isITM = row.strike < currentPrice;
                const isOTM = row.strike > currentPrice;
                const isHighlighted = highlightedStrikes.has(row.strike);
                const rowBg = isHighlighted 
                  ? 'bg-blue-100' 
                  : isITM 
                    ? 'bg-yellow-50' 
                    : isOTM 
                      ? 'bg-red-50' 
                      : 'bg-white';
                
                const callLeg = selectedLegs.find(leg => leg.strike === row.strike && leg.optionType === 'CALL');
                const putLeg = selectedLegs.find(leg => leg.strike === row.strike && leg.optionType === 'PUT');
                
                return (
                  <tr key={idx} className={`${rowBg} hover:bg-gray-100`}>
                    <td className="px-2 py-2 text-left text-gray-900">{row.callDelta.toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-gray-900">{row.callLTP.toFixed(2)}</td>
                    <td className="px-2 py-2 text-right">
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center justify-end gap-1">
                          <div className="w-16 h-4 bg-gray-200 rounded relative">
                            <div 
                              className="h-full bg-blue-500 rounded"
                              style={{ width: `${(row.callOI / 2000) * 100}%` }}
                            />
                          </div>
                          <span className="text-gray-900 min-w-[50px] text-right text-xs">
                            {row.callOI.toLocaleString()}
                          </span>
                        </div>
                        {/* Buy/Sell Buttons for Call */}
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleOptionAction(row.strike, 'CALL', 'BUY')}
                            className={`px-2 py-0.5 text-xs rounded font-medium transition-colors ${
                              callLeg?.action === 'BUY'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                          >
                            B
                          </button>
                          <button
                            onClick={() => handleOptionAction(row.strike, 'CALL', 'SELL')}
                            className={`px-2 py-0.5 text-xs rounded font-medium transition-colors ${
                              callLeg?.action === 'SELL'
                                ? 'bg-red-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                          >
                            S
                          </button>
                        </div>
                        {/* Quantity Selector for Call */}
                        {callLeg && (
                          <select
                            value={callLeg.quantity}
                            onChange={(e) => handleQuantityChange(row.strike, 'CALL', parseInt(e.target.value))}
                            onClick={(e) => e.stopPropagation()}
                            className="w-16 px-1 py-0.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          >
                            {[25, 50, 75, 100, 125, 150, 200, 250].map(qty => (
                              <option key={qty} value={qty}>{qty}</option>
                            ))}
                          </select>
                        )}
                      </div>
                    </td>
                    <td className="px-2 py-2 text-center font-semibold text-gray-900">{row.strike}</td>
                    <td className="px-2 py-2 text-right text-gray-600">{row.callIV.toFixed(2)}%</td>
                    <td className="px-2 py-2 text-right">
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center justify-end gap-1">
                          <div className="w-16 h-4 bg-gray-200 rounded relative">
                            <div 
                              className="h-full bg-green-500 rounded"
                              style={{ width: `${(row.putOI / 2000) * 100}%` }}
                            />
                          </div>
                          <span className="text-gray-900 min-w-[50px] text-right text-xs">
                            {row.putOI.toLocaleString()}
                          </span>
                        </div>
                        {/* Buy/Sell Buttons for Put */}
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleOptionAction(row.strike, 'PUT', 'BUY')}
                            className={`px-2 py-0.5 text-xs rounded font-medium transition-colors ${
                              putLeg?.action === 'BUY'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                          >
                            B
                          </button>
                          <button
                            onClick={() => handleOptionAction(row.strike, 'PUT', 'SELL')}
                            className={`px-2 py-0.5 text-xs rounded font-medium transition-colors ${
                              putLeg?.action === 'SELL'
                                ? 'bg-red-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                          >
                            S
                          </button>
                        </div>
                        {/* Quantity Selector for Put */}
                        {putLeg && (
                          <select
                            value={putLeg.quantity}
                            onChange={(e) => handleQuantityChange(row.strike, 'PUT', parseInt(e.target.value))}
                            onClick={(e) => e.stopPropagation()}
                            className="w-16 px-1 py-0.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          >
                            {[25, 50, 75, 100, 125, 150, 200, 250].map(qty => (
                              <option key={qty} value={qty}>{qty}</option>
                            ))}
                          </select>
                        )}
                      </div>
                    </td>
                    <td className="px-2 py-2 text-right text-gray-900">{row.putLTP.toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-gray-900">{row.putDelta.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Bottom Bar - Selected Legs Summary */}
        <div className="p-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
          <span className="text-sm text-gray-700 font-medium">
            {selectedLegs.length} leg{selectedLegs.length !== 1 ? 's' : ''} selected
          </span>
          <div className="flex gap-2">
            <button
              onClick={handleClearAll}
              className="px-3 py-1.5 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-200 rounded transition-colors"
            >
              Clear All
            </button>
            <button
              onClick={handleDone}
              className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 font-medium transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>

      {/* Middle Panel - Strategy Editor */}
      <div className="flex-1 flex flex-col border-r border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Editor</h3>
            <button className="text-sm text-blue-600 hover:text-blue-700">Collapse</button>
          </div>
        </div>

        {selectedStrategy ? (
          <div className="flex-1 overflow-auto">
            <EnhancedStrategyBuilder
              key={selectedStrategy.name + selectedStrategy.legs.length} // Force re-render when strategy changes
              symbol={selectedSymbol}
              initialStrategy={selectedStrategy}
              onStrategySelect={(strategy) => {
                setSelectedStrategy(strategy);
              }}
            />
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => {
                  setSelectedStrategy(null);
                  toast.success('Strategy editor cleared');
                }}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm text-gray-700"
              >
                Clear Editor
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <FileText className="w-16 h-16 text-gray-300 mb-4" />
            <p className="text-gray-500 text-lg mb-2">No Trades Added</p>
            <p className="text-gray-400 text-sm mb-6">
              Please click on a ready-made strategy to load it
            </p>
            <a href="#" className="text-blue-600 hover:text-blue-700 text-sm">
              Learn Options Strategies
            </a>

            {/* Strategy Filters */}
            <div className="mt-8 w-full max-w-4xl">
              <div className="flex gap-2 mb-4">
                {['Bullish', 'Bearish', 'Neutral', 'Others'].map((outlook) => (
                  <button
                    key={outlook}
                    onClick={() => setStrategyOutlook(outlook as any)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium ${
                      strategyOutlook === outlook
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {outlook}
                  </button>
                ))}
              </div>

              {/* Expiry Selector */}
              <div className="mb-4">
                <select
                  value={expiryDate}
                  onChange={(e) => setExpiryDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Expiry</option>
                  {expiryDates.map((date) => (
                    <option key={date} value={date}>Expiry {date}</option>
                  ))}
                </select>
              </div>

              {/* Strategy Templates Grid */}
              <div className="grid grid-cols-3 gap-3">
                {filteredStrategies.map((template, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleStrategySelect(template)}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gray-100 rounded flex items-center justify-center">
                        <TrendingUp className="w-4 h-4 text-gray-600" />
                      </div>
                      <span className="text-sm font-medium text-gray-900">{template.name}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex gap-3">
              <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                Clear All
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Done
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Right Panel - Orders/Positions */}
      <div className="w-80 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex gap-2">
            <button className="px-3 py-1.5 text-sm font-medium text-gray-700 hover:text-gray-900">
              Positions
            </button>
            <button className="px-3 py-1.5 text-sm font-medium bg-blue-600 text-white rounded">
              Orders
            </button>
          </div>
        </div>

        <div className="flex-1 p-4">
          <div className="space-y-3">
            <div className="p-3 border border-gray-200 rounded-lg">
              <p className="text-sm text-gray-500 mb-2">Order Type</p>
              <select className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none">
                <option>Market</option>
                <option>Limit</option>
                <option>SL</option>
                <option>SL-M</option>
              </select>
            </div>

            <div className="p-3 border border-gray-200 rounded-lg">
              <p className="text-sm text-gray-500 mb-2">Quantity</p>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none"
                placeholder="Enter quantity"
              />
            </div>

            <div className="p-3 border border-gray-200 rounded-lg">
              <p className="text-sm text-gray-500 mb-2">Price</p>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none"
                placeholder="Enter price"
              />
            </div>

            <button className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              Place Order
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptionsChainBuilder;

