/**
 * Enhanced Order Placement Component
 * Supports Market, Limit, and Stop Loss orders
 */

import React, { useState, useEffect } from 'react';
import {
  ShoppingCartIcon,
  ArrowTrendingDownIcon,
  XMarkIcon,
  InformationCircleIcon,
  ClockIcon,
  StopIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { httpClient } from '../config/api';
import { useAuth } from '../context/AuthContext';

interface EnhancedOrderPlacementProps {
  symbol: string;
  currentPrice?: number;
  onOrderPlaced?: () => void;
  size?: 'sm' | 'md' | 'lg';
  showBoth?: boolean;
  className?: string;
}

type OrderType = 'BUY' | 'SELL';
type OrderSide = 'MARKET' | 'LIMIT' | 'STOP_LOSS' | 'STOP_LOSS_LIMIT';

const EnhancedOrderPlacement: React.FC<EnhancedOrderPlacementProps> = ({
  symbol,
  currentPrice = 0,
  onOrderPlaced,
  size = 'md',
  showBoth = true,
  className = ''
}) => {
  const { user } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [orderType, setOrderType] = useState<OrderType>('BUY');
  const [orderSide, setOrderSide] = useState<OrderSide>('MARKET');
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number>(currentPrice);
  const [stopLoss, setStopLoss] = useState<number>(0);
  const [target, setTarget] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [availableBalance, setAvailableBalance] = useState<number>(0);

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  // Fetch available balance
  useEffect(() => {
    if (user && showModal) {
      fetchBalance();
    }
  }, [user, showModal]);

  const fetchBalance = async () => {
    try {
      const response = await httpClient.get<{ demo_cash_balance?: number; real_cash_balance?: number }>('/api/user/profile');
      if (response.data) {
        setAvailableBalance(response.data.demo_cash_balance || response.data.real_cash_balance || 1000000);
      }
    } catch (error) {
      console.error('Error fetching balance:', error);
      setAvailableBalance(1000000); // Default demo balance
    }
  };

  const handleBuyClick = () => {
    if (!user) {
      toast.error('Please login to place orders');
      return;
    }
    setOrderType('BUY');
    setPrice(currentPrice || 0);
    setShowModal(true);
  };

  const handleSellClick = () => {
    if (!user) {
      toast.error('Please login to place orders');
      return;
    }
    setOrderType('SELL');
    setPrice(currentPrice || 0);
    setShowModal(true);
  };

  const calculateTotal = () => {
    return quantity * price;
  };

  const calculateRequiredMargin = () => {
    if (orderType === 'BUY') {
      return calculateTotal();
    }
    return 0; // For SELL, check holdings instead
  };

  const canPlaceOrder = () => {
    if (quantity <= 0 || price <= 0) return false;
    if (orderSide === 'LIMIT' && price <= 0) return false;
    if (orderSide === 'STOP_LOSS' && stopLoss <= 0) return false;
    if (orderType === 'BUY' && calculateRequiredMargin() > availableBalance) return false;
    return true;
  };

  const handlePlaceOrder = async () => {
    if (!canPlaceOrder()) {
      toast.error('Please check order details');
      return;
    }

    setLoading(true);
    try {
      const orderData: any = {
        symbol: symbol.toUpperCase(),
        order_type: orderType,
        order_side: orderSide,
        quantity: quantity,
        price: price,
        is_demo: true // Demo trading mode
      };

      // Add stop loss if applicable
      if (orderSide === 'STOP_LOSS' || orderSide === 'STOP_LOSS_LIMIT') {
        orderData.stop_loss = stopLoss;
      }

      // Add target if provided
      if (target > 0) {
        orderData.target = target;
      }

      const response = await httpClient.post('/api/trading/place-order', orderData);

      if (response.success) {
        toast.success(`${orderType} ${orderSide} order placed successfully!`);
        setShowModal(false);
        setQuantity(1);
        setPrice(currentPrice || 0);
        setStopLoss(0);
        setTarget(0);
        if (onOrderPlaced) {
          onOrderPlaced();
        }
      } else {
        toast.error(response.message || 'Failed to place order');
      }
    } catch (error: any) {
      console.error('Error placing order:', error);
      toast.error(error?.response?.data?.detail || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className={`flex items-center space-x-2 ${className}`}>
        {showBoth ? (
          <>
            <button
              onClick={handleBuyClick}
              className={`${sizeClasses[size]} bg-green-500 hover:bg-green-600 text-white rounded-md font-medium flex items-center space-x-1 transition-colors shadow-md`}
            >
              <ShoppingCartIcon className="h-4 w-4" />
              <span>Buy</span>
            </button>
            <button
              onClick={handleSellClick}
              className={`${sizeClasses[size]} bg-red-500 hover:bg-red-600 text-white rounded-md font-medium flex items-center space-x-1 transition-colors shadow-md`}
            >
              <ArrowTrendingDownIcon className="h-4 w-4" />
              <span>Sell</span>
            </button>
          </>
        ) : (
          <button
            onClick={orderType === 'BUY' ? handleBuyClick : handleSellClick}
            className={`${sizeClasses[size]} ${
              orderType === 'BUY' 
                ? 'bg-green-500 hover:bg-green-600' 
                : 'bg-red-500 hover:bg-red-600'
            } text-white rounded-md font-medium flex items-center space-x-1 transition-colors shadow-md`}
          >
            {orderType === 'BUY' ? (
              <>
                <ShoppingCartIcon className="h-4 w-4" />
                <span>Buy</span>
              </>
            ) : (
              <>
                <ArrowTrendingDownIcon className="h-4 w-4" />
                <span>Sell</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Enhanced Order Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end lg:items-center justify-center z-50 p-0 lg:p-4">
          <div className="bg-[#1e222d] border border-[#2a2e39] rounded-t-2xl lg:rounded-lg w-full lg:max-w-md shadow-2xl max-h-[90vh] lg:max-h-[85vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-[#1e222d] z-10 flex items-center justify-between p-4 border-b border-[#2a2e39]">
              {/* Mobile Handle */}
              <div className="absolute top-2 left-1/2 transform -translate-x-1/2 lg:hidden w-12 h-1 bg-gray-600 rounded-full" />
              <h3 className="text-lg font-semibold text-white ml-0 lg:ml-0">
                {orderType} {symbol.toUpperCase()}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-white transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="Close"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-4 space-y-4">
              {/* Order Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Order Type
                </label>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                  <button
                    onClick={() => setOrderSide('MARKET')}
                    className={`px-3 py-3 lg:py-2 rounded text-sm font-medium transition-colors min-h-[44px] ${
                      orderSide === 'MARKET'
                        ? 'bg-blue-600 text-white'
                        : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
                    }`}
                  >
                    Market
                  </button>
                  <button
                    onClick={() => setOrderSide('LIMIT')}
                    className={`px-3 py-3 lg:py-2 rounded text-sm font-medium transition-colors min-h-[44px] ${
                      orderSide === 'LIMIT'
                        ? 'bg-blue-600 text-white'
                        : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
                    }`}
                  >
                    Limit
                  </button>
                  <button
                    onClick={() => setOrderSide('STOP_LOSS')}
                    className={`px-3 py-3 lg:py-2 rounded text-sm font-medium transition-colors min-h-[44px] ${
                      orderSide === 'STOP_LOSS'
                        ? 'bg-blue-600 text-white'
                        : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
                    }`}
                  >
                    Stop
                  </button>
                  <button
                    onClick={() => setOrderSide('STOP_LOSS_LIMIT')}
                    className={`px-3 py-3 lg:py-2 rounded text-sm font-medium transition-colors min-h-[44px] ${
                      orderSide === 'STOP_LOSS_LIMIT'
                        ? 'bg-blue-600 text-white'
                        : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
                    }`}
                  >
                    SL-Limit
                  </button>
                </div>
              </div>

              {/* Quantity */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Quantity
                </label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                  className="w-full p-3 lg:p-2 bg-[#131722] border border-[#2a2e39] rounded-md text-white focus:border-blue-500 focus:outline-none min-h-[44px] text-base lg:text-sm"
                  min="1"
                />
              </div>
              
              {/* Current Market Price Display for LIMIT orders */}
              {(orderSide === 'LIMIT' || orderSide === 'STOP_LOSS_LIMIT') && currentPrice > 0 && (
                <div className="bg-blue-900/20 border border-blue-700/50 p-3 rounded-md">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Current Market Price:</span>
                    <span className="font-medium text-blue-400">
                      ₹{currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPrice(currentPrice)}
                    className="mt-2 text-xs text-blue-400 hover:underline"
                  >
                    Use Current Price
                  </button>
                </div>
              )}

              {/* Price */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  {orderSide === 'MARKET' ? 'Expected Price' : orderSide === 'LIMIT' ? 'Limit Price' : 'Price'} (₹)
                </label>
                <input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                  className="w-full p-3 lg:p-2 bg-[#131722] border border-[#2a2e39] rounded-md text-white focus:border-blue-500 focus:outline-none min-h-[44px] text-base lg:text-sm"
                  step="0.01"
                  min="0"
                  disabled={orderSide === 'MARKET'}
                  placeholder={orderSide === 'LIMIT' && currentPrice > 0 ? `Enter limit price (Current: ₹${currentPrice.toFixed(2)})` : undefined}
                />
                {orderSide === 'MARKET' && (
                  <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                    <InformationCircleIcon className="w-3 h-3" />
                    Market orders execute at current market price
                  </p>
                )}
                {orderSide === 'LIMIT' && currentPrice > 0 && price > 0 && (
                  <p className={`text-xs mt-1 ${
                    orderType === 'BUY' 
                      ? (price < currentPrice ? 'text-green-400' : price > currentPrice ? 'text-orange-400' : 'text-gray-400')
                      : (price > currentPrice ? 'text-green-400' : price < currentPrice ? 'text-orange-400' : 'text-gray-400')
                  }`}>
                    {orderType === 'BUY' 
                      ? (price < currentPrice ? `Below market by ₹${(currentPrice - price).toFixed(2)}` : price > currentPrice ? `Above market by ₹${(price - currentPrice).toFixed(2)}` : 'At market price')
                      : (price > currentPrice ? `Above market by ₹${(price - currentPrice).toFixed(2)}` : price < currentPrice ? `Below market by ₹${(currentPrice - price).toFixed(2)}` : 'At market price')
                    }
                  </p>
                )}
              </div>

              {/* Stop Loss (for Stop Loss orders) */}
              {(orderSide === 'STOP_LOSS' || orderSide === 'STOP_LOSS_LIMIT') && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Stop Loss (₹)
                  </label>
                  <input
                    type="number"
                    value={stopLoss}
                    onChange={(e) => setStopLoss(parseFloat(e.target.value) || 0)}
                    className="w-full p-2 bg-[#131722] border border-[#2a2e39] rounded-md text-white focus:border-blue-500 focus:outline-none"
                    step="0.01"
                    min="0"
                  />
                </div>
              )}

              {/* Target (Optional) */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Target (₹) <span className="text-gray-500 text-xs">(Optional)</span>
                </label>
                <input
                  type="number"
                  value={target}
                  onChange={(e) => setTarget(parseFloat(e.target.value) || 0)}
                  className="w-full p-2 bg-[#131722] border border-[#2a2e39] rounded-md text-white focus:border-blue-500 focus:outline-none"
                  step="0.01"
                  min="0"
                />
              </div>
              
              {/* Order Summary */}
              <div className="bg-[#131722] border border-[#2a2e39] p-3 rounded-md space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Total Value:</span>
                  <span className="font-medium text-white">₹{calculateTotal().toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
                {orderType === 'BUY' && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Available Balance:</span>
                    <span className="font-medium text-white">₹{availableBalance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                )}
                {orderType === 'BUY' && calculateRequiredMargin() > availableBalance && (
                  <div className="text-xs text-red-400 flex items-center gap-1">
                    <InformationCircleIcon className="w-3 h-3" />
                    Insufficient balance
                  </div>
                )}
              </div>
            </div>
            
            {/* Footer */}
            <div className="sticky bottom-0 bg-[#1e222d] flex flex-col sm:flex-row justify-end gap-2 sm:gap-3 p-4 border-t border-[#2a2e39]">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-3 lg:py-2 bg-[#2a2e39] text-gray-300 rounded-md hover:bg-[#363a45] transition-colors min-h-[44px] font-medium"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handlePlaceOrder}
                disabled={loading || !canPlaceOrder()}
                className={`px-4 py-3 lg:py-2 ${
                  orderType === 'BUY' 
                    ? 'bg-green-500 hover:bg-green-600' 
                    : 'bg-red-500 hover:bg-red-600'
                } text-white rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]`}
              >
                {loading ? 'Placing...' : `Place ${orderType} Order`}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default EnhancedOrderPlacement;

