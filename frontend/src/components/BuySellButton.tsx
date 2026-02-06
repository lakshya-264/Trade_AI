import React, { useState, useEffect } from 'react';
import { ShoppingCartIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { httpClient } from '../config/api';
import { useAuth } from '../context/AuthContext';
import candleDataApi from '../services/candleDataApi';

interface BuySellButtonProps {
  symbol: string;
  currentPrice?: number;
  onOrderPlaced?: () => void;
  size?: 'sm' | 'md' | 'lg';
  showBoth?: boolean;
}

const BuySellButton: React.FC<BuySellButtonProps> = ({
  symbol,
  currentPrice,
  onOrderPlaced,
  size = 'md',
  showBoth = true
}) => {
  const { user } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [orderType, setOrderType] = useState<'BUY' | 'SELL'>('BUY');
  const [orderSide, setOrderSide] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number>(currentPrice || 0);
  const [marketPrice, setMarketPrice] = useState<number>(currentPrice || 0);
  const [loading, setLoading] = useState(false);
  const [fetchingPrice, setFetchingPrice] = useState(false);

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  // Fetch current market price when modal opens
  useEffect(() => {
    if (showModal && symbol) {
      fetchCurrentPrice();
    }
  }, [showModal, symbol]);

  const fetchCurrentPrice = async () => {
    // Use currentPrice prop if available and valid
    if (currentPrice && currentPrice > 0) {
      setMarketPrice(currentPrice);
      if (orderSide === 'MARKET') {
        setPrice(currentPrice);
      }
      setFetchingPrice(false);
      return;
    }

    setFetchingPrice(true);
    try {
      // Try to fetch latest candle data (most reliable)
      const response = await candleDataApi.getLatestCandle(symbol);
      
      if (response.success && response.data) {
        const price = response.data.close || 0;
        if (price > 0) {
          setMarketPrice(price);
          if (orderSide === 'MARKET') {
            setPrice(price);
          }
          setFetchingPrice(false);
          return;
        }
      }

      // Fallback 1: Try market quote API
      try {
        const quoteResponse = await httpClient.get(`/api/market/quote/${symbol}`) as any;
        if (quoteResponse?.data?.last_price || quoteResponse?.last_price) {
          const price = quoteResponse.data?.last_price || quoteResponse.last_price;
          if (price > 0) {
            setMarketPrice(price);
            if (orderSide === 'MARKET') {
              setPrice(price);
            }
            setFetchingPrice(false);
            return;
          }
        }
      } catch (quoteError) {
        console.log('Quote API failed, trying candles API');
      }

      // Fallback 2: Try comprehensive trading candles endpoint
      try {
        const candlesResponse = await httpClient.get(`/api/comprehensive-trading/candles?symbol=${symbol}&interval=1d&range=1d`) as any;
        if (candlesResponse?.data?.candles && candlesResponse.data.candles.length > 0) {
          const lastCandle = candlesResponse.data.candles[candlesResponse.data.candles.length - 1];
          const price = lastCandle.close || 0;
          if (price > 0) {
            setMarketPrice(price);
            if (orderSide === 'MARKET') {
              setPrice(price);
            }
            setFetchingPrice(false);
            return;
          }
        }
      } catch (candlesError) {
        console.log('Candles API failed');
      }

      // If all fail, show error but don't block
      console.warn('Could not fetch current price for', symbol);
      toast.error('Unable to fetch current market price. Please enter price manually for LIMIT orders.');
    } catch (error) {
      console.error('Error fetching current price:', error);
      toast.error('Unable to fetch current market price. Please enter price manually for LIMIT orders.');
    } finally {
      setFetchingPrice(false);
    }
  };

  const handleBuyClick = () => {
    if (!user) {
      toast.error('Please login to place orders');
      return;
    }
    setOrderType('BUY');
    setOrderSide('MARKET');
    setPrice(marketPrice || currentPrice || 0);
    setShowModal(true);
  };

  const handleSellClick = () => {
    if (!user) {
      toast.error('Please login to place orders');
      return;
    }
    setOrderType('SELL');
    setOrderSide('MARKET');
    setPrice(marketPrice || currentPrice || 0);
    setShowModal(true);
  };

  const handlePlaceOrder = async () => {
    if (quantity <= 0) {
      toast.error('Please enter valid quantity');
      return;
    }

    // For LIMIT orders, price is required
    if (orderSide === 'LIMIT' && (!price || price <= 0)) {
      toast.error('Please enter a valid limit price');
      return;
    }

    // For MARKET orders, validate we have a market price
    if (orderSide === 'MARKET' && (!marketPrice || marketPrice <= 0)) {
      toast.error('Unable to fetch current market price. Please try again or use LIMIT order.');
      return;
    }

    setLoading(true);
    try {
      const orderData: any = {
        symbol: symbol.toUpperCase(),
        order_type: orderType, // BUY or SELL
        order_side: orderSide, // MARKET or LIMIT
        quantity: quantity
      };

      // For LIMIT orders, include the limit price
      if (orderSide === 'LIMIT') {
        orderData.price = price;
      } else {
        // For MARKET orders, backend should fetch current price at execution time
        // We can send marketPrice as reference for validation
        orderData.price = marketPrice; // For reference/validation only
      }

      const response = await httpClient.post('/api/trading/place-order', orderData) as any;

      if (response?.success) {
        const orderTypeText = orderSide === 'MARKET' 
          ? 'MARKET' 
          : `LIMIT @ ₹${price.toFixed(2)}`;
        toast.success(`${orderType} ${orderTypeText} order placed successfully for ${quantity} shares of ${symbol}`);
        setShowModal(false);
        setQuantity(1);
        setOrderSide('MARKET');
        if (onOrderPlaced) {
          onOrderPlaced();
        }
      } else {
        toast.error(response?.message || response?.detail || 'Failed to place order');
      }
    } catch (error: any) {
      console.error('Error placing order:', error);
      toast.error(error?.response?.data?.detail || error?.message || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="flex items-center space-x-2">
        {showBoth ? (
          <>
            <button
              onClick={handleBuyClick}
              className={`${sizeClasses[size]} bg-green-500 hover:bg-green-600 text-white rounded-md font-medium flex items-center space-x-1 transition-colors`}
            >
              <ShoppingCartIcon className="h-4 w-4" />
              <span>Buy</span>
            </button>
            <button
              onClick={handleSellClick}
              className={`${sizeClasses[size]} bg-red-500 hover:bg-red-600 text-white rounded-md font-medium flex items-center space-x-1 transition-colors`}
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
            } text-white rounded-md font-medium flex items-center space-x-1 transition-colors`}
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

      {/* Order Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">
              {orderType} {symbol.toUpperCase()}
            </h3>
            
            <div className="space-y-4">
              {/* Order Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Order Type
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setOrderSide('MARKET');
                      setPrice(marketPrice);
                    }}
                    className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      orderSide === 'MARKET'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500'
                    }`}
                  >
                    MARKET
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setOrderSide('LIMIT');
                      setPrice(marketPrice || 0);
                    }}
                    className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      orderSide === 'LIMIT'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500'
                    }`}
                  >
                    LIMIT
                  </button>
                </div>
                {orderSide === 'MARKET' && (
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Order will be executed at current market price
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Quantity
                </label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  min="1"
                />
              </div>
              
              {/* Price field - only for LIMIT orders */}
              {orderSide === 'LIMIT' && (
                <>
                  {/* Current Market Price Display for LIMIT orders */}
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md border border-blue-200 dark:border-blue-800">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Current Market Price:</span>
                      {fetchingPrice ? (
                        <span className="text-gray-500 animate-pulse">Fetching...</span>
                      ) : marketPrice > 0 ? (
                        <span className="font-medium text-blue-600 dark:text-blue-400">
                          ₹{marketPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      ) : (
                        <span className="text-red-500 text-xs">Unable to fetch price</span>
                      )}
                    </div>
                    {!fetchingPrice && marketPrice > 0 && (
                      <button
                        type="button"
                        onClick={fetchCurrentPrice}
                        className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        Refresh Price
                      </button>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Limit Price (₹)
                    </label>
                    <input
                      type="number"
                      value={price}
                      onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                      className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      step="0.01"
                      min="0"
                      placeholder={marketPrice > 0 ? `Enter limit price (Current: ₹${marketPrice.toFixed(2)})` : "Enter limit price"}
                    />
                    {marketPrice > 0 && (
                      <div className="mt-1 flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setPrice(marketPrice)}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Use Current Price
                        </button>
                        {price > 0 && marketPrice > 0 && (
                          <span className={`text-xs ${
                            orderType === 'BUY' 
                              ? (price < marketPrice ? 'text-green-600' : price > marketPrice ? 'text-orange-600' : 'text-gray-500')
                              : (price > marketPrice ? 'text-green-600' : price < marketPrice ? 'text-orange-600' : 'text-gray-500')
                          }`}>
                            {orderType === 'BUY' 
                              ? (price < marketPrice ? `Below market by ₹${(marketPrice - price).toFixed(2)}` : price > marketPrice ? `Above market by ₹${(price - marketPrice).toFixed(2)}` : 'At market price')
                              : (price > marketPrice ? `Above market by ₹${(price - marketPrice).toFixed(2)}` : price < marketPrice ? `Below market by ₹${(marketPrice - price).toFixed(2)}` : 'At market price')
                            }
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* Market Price Display for MARKET orders */}
              {orderSide === 'MARKET' && (
                <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md border border-blue-200 dark:border-blue-800">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Current Market Price:</span>
                    {fetchingPrice ? (
                      <span className="text-gray-500 animate-pulse">Fetching...</span>
                    ) : marketPrice > 0 ? (
                      <span className="font-medium text-blue-600 dark:text-blue-400">
                        ₹{marketPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    ) : (
                      <span className="text-red-500 text-xs">Unable to fetch price</span>
                    )}
                  </div>
                  {!fetchingPrice && marketPrice > 0 && (
                    <button
                      type="button"
                      onClick={fetchCurrentPrice}
                      className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Refresh Price
                    </button>
                  )}
                </div>
              )}
              
              <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Total Value:</span>
                  <span className="font-medium">
                    ₹{((quantity * (orderSide === 'MARKET' ? marketPrice : price)) || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-500"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handlePlaceOrder}
                disabled={loading}
                className={`px-4 py-2 ${
                  orderType === 'BUY' 
                    ? 'bg-green-500 hover:bg-green-600' 
                    : 'bg-red-500 hover:bg-red-600'
                } text-white rounded-md font-medium`}
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

export default BuySellButton;

