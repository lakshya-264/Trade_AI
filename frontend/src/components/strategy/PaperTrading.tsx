/**
 * Paper Trading Component
 * Simulated trading for strategies without real money
 */

import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, RefreshCw, TrendingUp, TrendingDown, DollarSign, Clock } from 'lucide-react';
import { Strategy } from './StrategyBuilder';
import { httpClient } from '../../config/api';
import { toast } from 'react-hot-toast';
import { handleApiErrorWithLog } from '../../utils/errorHandler';
import api from '../../services/api';

interface PaperTradingProps {
  strategy?: Strategy;  // Optional - if not provided, show all saved strategies
  symbol: string;
  currentPrice: number;
}

interface PaperTrade {
  id: string;
  strategyId: string;
  entryPrice: number;
  currentPrice: number;
  quantity: number;
  entryTime: string;
  pnl: number;
  pnlPercentage: number;
  status: 'open' | 'closed';
  exitPrice?: number;
  exitTime?: string;
}

const PaperTrading: React.FC<PaperTradingProps> = ({ strategy, symbol, currentPrice: initialCurrentPrice }) => {
  const [isTrading, setIsTrading] = useState(false);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalPnl, setTotalPnl] = useState(0);
  const [winRate, setWinRate] = useState(0);
  const [currentPrice, setCurrentPrice] = useState<number>(initialCurrentPrice || 0);
  const [savedStrategies, setSavedStrategies] = useState<Strategy[]>([]);
  const [activePositions, setActivePositions] = useState<any[]>([]);
  const [loadingPositions, setLoadingPositions] = useState(false);

  // Fetch current price automatically
  useEffect(() => {
    if (!symbol) return;
    
    const fetchCurrentPrice = async () => {
      try {
        const quote = await api.getQuote(symbol, 'NSE');
        if (quote && quote.last_price && quote.last_price > 0) {
          setCurrentPrice(quote.last_price);
        }
      } catch (error) {
        console.error('Error fetching current price:', error);
        // Fallback to prop if available
        if (initialCurrentPrice) {
          setCurrentPrice(initialCurrentPrice);
        }
      }
    };

    fetchCurrentPrice();
    
    // Update price every 5 seconds
    const priceInterval = setInterval(fetchCurrentPrice, 5000);
    return () => clearInterval(priceInterval);
  }, [symbol, initialCurrentPrice]);

  // Fetch saved strategies and active positions
  useEffect(() => {
    fetchSavedStrategies();
    fetchActivePositions();
    // Refresh positions every 5 seconds for real-time P&L
    const positionsInterval = setInterval(fetchActivePositions, 5000);
    return () => clearInterval(positionsInterval);
  }, [symbol]);

  useEffect(() => {
    if (strategy?.id) {
      fetchPaperTrades();
    }
  }, [strategy?.id]); // Fetch trades when strategy changes or on mount

  // Update trade prices for all open trades, not just when isTrading is true
  useEffect(() => {
    const openTrades = trades.filter(t => t.status === 'open');
    if (openTrades.length > 0 && currentPrice > 0 && strategy?.id) {
      // Update immediately
      updateTradePrices();
      
      // Then set up interval for regular updates
      const interval = setInterval(() => {
        updateTradePrices();
      }, 5000); // Update every 5 seconds
      return () => clearInterval(interval);
    }
  }, [trades.length, currentPrice, strategy?.id]); // Use trades.length to avoid infinite loop

  useEffect(() => {
    calculateStats();
  }, [trades]);

  const fetchPaperTrades = async () => {
    // Allow fetching even without strategy.id to show all trades
    setLoading(true);
    try {
      const response = await httpClient.get('/api/comprehensive-trading/paper-trading/trades', {
        params: strategy?.id ? { strategy_id: strategy?.id } : {}
      }) as any;

      if (response.data?.success && response.data?.data) {
        setTrades(response.data.data || []);
      } else if (response.success && response.data) {
        setTrades(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching paper trades:', error);
      toast.error('Failed to fetch paper trades');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = () => {
    const closedTrades = trades.filter(t => t.status === 'closed');
    const openTrades = trades.filter(t => t.status === 'open');

    const closedPnl = closedTrades.reduce((sum, t) => sum + t.pnl, 0);
    const openPnl = openTrades.reduce((sum, t) => sum + t.pnl, 0);
    setTotalPnl(closedPnl + openPnl);

    const wins = closedTrades.filter(t => t.pnl > 0).length;
    setWinRate(closedTrades.length > 0 ? (wins / closedTrades.length) * 100 : 0);
  };

  const updateTradePrices = async () => {
    if (!strategy?.id) return;

    try {
      const response = await httpClient.post('/api/comprehensive-trading/paper-trading/update-prices', {
        strategy_id: strategy.id,
        current_price: currentPrice
      }) as any;

      if (response.data?.success && response.data?.data) {
        setTrades(response.data.data || []);
      } else if (response.success && response.data) {
        setTrades(response.data || []);
      }
    } catch (error) {
      console.error('Error updating trade prices:', error);
    }
  };

  const fetchSavedStrategies = async () => {
    try {
      const response = await httpClient.get('/api/comprehensive-trading/strategy/saved', {
        params: { symbol }
      }) as any;

      if (response.data?.success) {
        setSavedStrategies(response.data.data || []);
      }
    } catch (error) {
      console.error('Error fetching saved strategies:', error);
    }
  };

  const fetchActivePositions = async () => {
    setLoadingPositions(true);
    try {
      const response = await httpClient.get('/api/trading/positions', {
        params: { is_demo: true }
      }) as any;

      const responseData = response.data || response;
      if (responseData?.success && responseData?.data?.positions) {
        setActivePositions(responseData.data.positions || []);
        // Calculate total P&L from positions
        const totalPnlFromPositions = responseData.data.totalPnl || 0;
        setTotalPnl(totalPnlFromPositions);
      }
    } catch (error) {
      console.error('Error fetching positions:', error);
    } finally {
      setLoadingPositions(false);
    }
  };

  const startVirtualTrading = async (strategyToTrade: Strategy) => {
    if (!strategyToTrade.legs || strategyToTrade.legs.length === 0) {
      toast.error('Strategy has no legs');
      return;
    }

    setLoading(true);
    try {
      // Execute strategy trade - creates positions automatically
      const response = await httpClient.post('/api/trading/execute-strategy', {
        strategy_name: strategyToTrade.name || `${strategyToTrade.legs.length} Leg Strategy`,
        symbol: symbol,
        legs: strategyToTrade.legs.map(leg => ({
          id: leg.id,
          action: leg.action,
          instrument: leg.instrument,
          expiry: leg.expiry,
          strike: leg.strike,
          quantity: leg.quantity,
          price: leg.price || 0, // Use current market price if not set
          lotSize: leg.lotSize || 50
        })),
        is_demo: true
      }) as any;

      const executeResponse = (response as any).data || response;
      
      if (response?.success || executeResponse?.success) {
        toast.success(`Virtual trading started! ${executeResponse?.legsCount || strategyToTrade.legs.length} position(s) created.`);
        await fetchActivePositions(); // Refresh positions
        setIsTrading(true);
      } else {
        toast.error(executeResponse?.message || response?.message || 'Failed to start virtual trading');
      }
    } catch (error: any) {
      console.error('Error starting virtual trading:', error);
      toast.error(error?.response?.data?.detail || 'Failed to start virtual trading');
    } finally {
      setLoading(false);
    }
  };

  const startPaperTrade = async () => {
    if (!strategy || strategy.legs.length === 0) {
      toast.error('Please add legs to the strategy first');
      return;
    }

    // Use the new startVirtualTrading function
    await startVirtualTrading(strategy);
  };

  const exitPaperTrade = async (tradeId: string) => {
    setLoading(true);
    try {
      const response = await httpClient.post('/api/comprehensive-trading/paper-trading/exit', {
        trade_id: tradeId,
        exit_price: currentPrice,
        exit_time: new Date().toISOString()
      }) as any;

      if (response.data?.success || response.success) {
        await fetchPaperTrades();
        setIsTrading(false);
        toast.success('Paper trade closed successfully');
      } else {
        toast.error(response.data?.error || response.error || response.data?.message || response.message || 'Failed to exit paper trade');
      }
    } catch (error: any) {
      handleApiErrorWithLog(error, 'Failed to exit paper trade', 'exitPaperTrade');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    
    // Parse the date string - handle both UTC and timezone-aware strings
    let date: Date;
    if (dateString.includes('Z') || dateString.endsWith('+00:00')) {
      // UTC time - convert to IST
      date = new Date(dateString);
    } else if (dateString.includes('+') || dateString.includes('-') && dateString.length > 19) {
      // Timezone-aware string
      date = new Date(dateString);
    } else {
      // Assume UTC if no timezone info
      date = new Date(dateString + 'Z');
    }
    
    // Convert to IST (Asia/Kolkata) and format
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const openTrades = trades.filter(t => t.status === 'open');
  const closedTrades = trades.filter(t => t.status === 'closed');

  return (
    <div className="p-4 space-y-4">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-400">Total P&L</span>
          </div>
          <div className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {totalPnl >= 0 ? '+' : ''}₹{(totalPnl / 100000).toFixed(2)}L
          </div>
        </div>

        <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-400">Win Rate</span>
          </div>
          <div className="text-2xl font-bold text-green-400">
            {winRate.toFixed(1)}%
          </div>
        </div>

        <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <Play className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-400">Open Trades</span>
          </div>
          <div className="text-2xl font-bold">
            {openTrades.length}
          </div>
        </div>

        <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <Square className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-400">Closed Trades</span>
          </div>
          <div className="text-2xl font-bold">
            {closedTrades.length}
          </div>
        </div>
      </div>

      {/* Control Panel */}
      <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold mb-1">Paper Trading</h3>
            <p className="text-sm text-gray-400">
              Simulate trading without real money. Track your strategy performance.
            </p>
          </div>
          <div className="flex gap-2">
            {!isTrading ? (
              <button
                onClick={startPaperTrade}
                disabled={loading || !strategy || strategy.legs.length === 0}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg flex items-center gap-2 disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                Start Trade
              </button>
            ) : (
              <button
                onClick={() => setIsTrading(false)}
                className="px-6 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg flex items-center gap-2"
              >
                <Pause className="w-4 h-4" />
                Pause
              </button>
            )}
            <button
              onClick={fetchPaperTrades}
              className="px-4 py-2 bg-[#2a2e39] hover:bg-[#3a3e49] rounded-lg"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Open Trades */}
      {openTrades.length > 0 && (
        <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
          <h4 className="font-semibold mb-3">Open Trades</h4>
          <div className="space-y-2">
            {openTrades.map((trade) => (
              <div
                key={trade.id}
                className="bg-[#2a2e39] rounded p-3 border border-gray-600"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div>
                        <span className="text-xs text-gray-400">Entry Price</span>
                        <div className="font-medium">₹{trade.entryPrice.toFixed(2)}</div>
                      </div>
                      <div>
                        <span className="text-xs text-gray-400">Current Price</span>
                        <div className="font-medium">₹{trade.currentPrice.toFixed(2)}</div>
                      </div>
                      <div>
                        <span className="text-xs text-gray-400">Quantity</span>
                        <div className="font-medium">{trade.quantity}</div>
                      </div>
                      <div>
                        <span className="text-xs text-gray-400">Entry Time</span>
                        <div className="text-xs">{formatDate(trade.entryTime)}</div>
                      </div>
                    </div>
                    <div className={`text-lg font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      P&L: {trade.pnl >= 0 ? '+' : ''}₹{(trade.pnl / 100000).toFixed(2)}L
                      {' '}
                      ({trade.pnlPercentage >= 0 ? '+' : ''}{trade.pnlPercentage.toFixed(2)}%)
                    </div>
                  </div>
                  <button
                    onClick={() => exitPaperTrade(trade.id)}
                    className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm"
                  >
                    Exit Trade
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Closed Trades */}
      {closedTrades.length > 0 && (
        <div className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
          <h4 className="font-semibold mb-3">Closed Trades</h4>
          <div className="space-y-2">
            {closedTrades.map((trade) => (
              <div
                key={trade.id}
                className="bg-[#2a2e39] rounded p-3 border border-gray-600"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div>
                        <span className="text-xs text-gray-400">Entry</span>
                        <div className="font-medium">₹{trade.entryPrice.toFixed(2)}</div>
                      </div>
                      <div>
                        <span className="text-xs text-gray-400">Exit</span>
                        <div className="font-medium">₹{trade.exitPrice?.toFixed(2) || 'N/A'}</div>
                      </div>
                      <div>
                        <span className="text-xs text-gray-400">Quantity</span>
                        <div className="font-medium">{trade.quantity}</div>
                      </div>
                      <div>
                        <span className="text-xs text-gray-400">Duration</span>
                        <div className="text-xs">
                          {trade.exitTime && trade.entryTime
                            ? `${Math.round((new Date(trade.exitTime).getTime() - new Date(trade.entryTime).getTime()) / 60000)} min`
                            : 'N/A'}
                        </div>
                      </div>
                    </div>
                    <div className={`text-lg font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      P&L: {trade.pnl >= 0 ? '+' : ''}₹{(trade.pnl / 100000).toFixed(2)}L
                      {' '}
                      ({trade.pnlPercentage >= 0 ? '+' : ''}{trade.pnlPercentage.toFixed(2)}%)
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activePositions.length === 0 && savedStrategies.length === 0 && (!strategy || strategy.legs.length === 0) && (
        <div className="text-center py-12 bg-[#1a1d28] rounded-lg border border-gray-700">
          <Play className="w-12 h-12 mx-auto mb-2 text-gray-500" />
          <p className="text-gray-400">No positions or strategies yet</p>
          <p className="text-sm text-gray-500 mt-1">Save a strategy and start virtual trading to track P&L</p>
        </div>
      )}
    </div>
  );
};

export default PaperTrading;

