/**
 * Order Book Component
 * Displays pending and executed orders
 */

import React, { useState, useEffect } from 'react';
import {
  ClipboardDocumentListIcon,
  XMarkIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { httpClient } from '../config/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-hot-toast';
import ClickableSymbol from './ClickableSymbol';

interface OrderBookProps {
  visible?: boolean;
  onClose?: () => void;
  symbol?: string;
  className?: string;
}

interface Order {
  id: number;
  symbol: string;
  order_type: 'BUY' | 'SELL';
  order_side: 'MARKET' | 'LIMIT' | 'STOP_LOSS' | 'STOP_LOSS_LIMIT';
  quantity: number;
  price: number;
  order_status: 'PENDING' | 'EXECUTED' | 'CANCELLED' | 'REJECTED';
  created_at: string;
  execution_time?: string;
  filled_price?: number;
}

const OrderBook: React.FC<OrderBookProps> = ({
  visible = true,
  onClose,
  symbol,
  className = ''
}) => {
  const { user, isAuthenticated } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'EXECUTED' | 'CANCELLED'>('ALL');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    if (visible && isAuthenticated && user) {
      fetchOrders();
    }
  }, [visible, isAuthenticated, user, symbol]);

  // Auto-refresh orders every 30 seconds
  useEffect(() => {
    if (visible && isAuthenticated && user) {
      const interval = setInterval(() => {
        fetchOrders();
        setLastUpdate(new Date());
      }, 30000); // 30 seconds
      
      return () => clearInterval(interval);
    }
  }, [visible, isAuthenticated, user, symbol]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (symbol) {
        params.symbol = symbol;
      }
      const response = await httpClient.get<any>('/api/trading/orders', { params });
      
      // Handle different response structures
      // httpClient returns APIResponse<T> where T is the actual data
      // Backend returns { orders: [...], total: ..., ... }
      let ordersData: Order[] = [];
      
      // The response from httpClient is APIResponse<T>, so response.data contains the backend response
      const backendResponse = response.data || response;
      
      if (backendResponse) {
        // Check if backendResponse.orders exists (most common case)
        if (backendResponse.orders && Array.isArray(backendResponse.orders)) {
          ordersData = backendResponse.orders;
        }
        // Check if backendResponse is the orders array directly
        else if (Array.isArray(backendResponse)) {
          ordersData = backendResponse;
        }
        // Check if response.data.orders exists (nested)
        else if (backendResponse.data && backendResponse.data.orders && Array.isArray(backendResponse.data.orders)) {
          ordersData = backendResponse.data.orders;
        }
      }
      
      // Transform orders to match the expected interface
      const transformedOrders: Order[] = ordersData.map((order: any) => ({
        id: order.id,
        symbol: order.symbol || '',
        order_type: order.order_type || 'BUY',
        order_side: order.order_side || 'MARKET',
        quantity: order.quantity || 0,
        price: order.price || 0,
        order_status: order.order_status || 'PENDING',
        created_at: order.created_at || order.order_time || new Date().toISOString(),
        execution_time: order.execution_time || order.filled_time || undefined,
        filled_price: order.filled_price || undefined
      }));
      
      setOrders(transformedOrders);
      setLastUpdate(new Date());
    } catch (error: any) {
      console.error('Error fetching orders:', error);
      console.error('Error details:', error?.response?.data || error?.message);
      setOrders([]);
      toast.error('Failed to load orders. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId: number) => {
    try {
      const response = await httpClient.delete(`/api/trading/cancel-order/${orderId}`);
      if (response.success) {
        toast.success('Order cancelled successfully');
        fetchOrders();
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Failed to cancel order');
    }
  };

  const filteredOrders = orders.filter(order => {
    if (filter === 'ALL') return true;
    return order.order_status === filter;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'EXECUTED':
        return <CheckCircleIcon className="w-4 h-4 text-green-400" />;
      case 'CANCELLED':
      case 'REJECTED':
        return <XCircleIcon className="w-4 h-4 text-red-400" />;
      case 'PENDING':
        return <ClockIcon className="w-4 h-4 text-yellow-400" />;
      default:
        return <ClockIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  if (!visible) return null;

  if (!isAuthenticated) {
    return (
      <div className={`bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4 ${className}`}>
        <div className="text-center text-gray-400 py-8">
          <ClipboardDocumentListIcon className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p>Please login to view orders</p>
        </div>
      </div>
    );
  }

  // Check if className contains transparent/border-0 to determine if it's embedded
  const isEmbedded = className?.includes('bg-transparent') || className?.includes('border-0');
  
  return (
    <div className={isEmbedded 
      ? `bg-white dark:bg-gray-800 rounded-lg ${className}` 
      : `bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-lg ${className}`
    }>
      {/* Header - only show if not embedded */}
      {!isEmbedded && (
        <div className="flex items-center justify-between p-4 border-b border-[#2a2e39]">
          <div className="flex items-center gap-2">
            <ClipboardDocumentListIcon className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">Order Book</h3>
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <ClockIcon className="w-3 h-3" />
              <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchOrders}
              disabled={loading}
              className="text-gray-400 hover:text-white transition-colors"
              title="Refresh"
            >
              <ArrowPathIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className={`flex gap-2 p-4 border-b ${isEmbedded ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700' : 'border-[#2a2e39] bg-[#131722]'}`}>
        {(['ALL', 'PENDING', 'EXECUTED', 'CANCELLED'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              filter === f
                ? 'bg-blue-600 text-white'
                : isEmbedded 
                  ? 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500'
                  : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Orders List */}
      <div className="p-4">
        {loading ? (
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-[#131722] rounded"></div>
            ))}
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className={`text-center py-8 text-sm ${isEmbedded ? 'text-gray-500 dark:text-gray-400' : 'text-gray-400'}`}>
            <ClipboardDocumentListIcon className={`w-8 h-8 mx-auto mb-2 ${isEmbedded ? 'text-gray-400 dark:text-gray-600' : 'text-gray-600'}`} />
            <p>No orders found</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredOrders.map((order) => (
              <div
                key={order.id}
                className={`rounded-lg p-3 transition-colors ${
                  isEmbedded
                    ? 'bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 hover:border-blue-500 dark:hover:border-blue-500'
                    : 'bg-[#131722] border border-[#2a2e39] hover:border-blue-500/50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(order.order_status)}
                    <ClickableSymbol symbol={order.symbol} variant="bold" />
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      order.order_type === 'BUY'
                        ? isEmbedded 
                          ? 'bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400'
                          : 'bg-green-500/20 text-green-400'
                        : isEmbedded
                          ? 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400'
                          : 'bg-red-500/20 text-red-400'
                    }`}>
                      {order.order_type}
                    </span>
                    <span className={`text-xs ${isEmbedded ? 'text-gray-600 dark:text-gray-400' : 'text-gray-400'}`}>{order.order_side}</span>
                  </div>
                  {order.order_status === 'PENDING' && (
                    <button
                      onClick={() => handleCancelOrder(order.id)}
                      className="text-red-400 hover:text-red-300 text-xs"
                    >
                      Cancel
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className={isEmbedded ? 'text-gray-600 dark:text-gray-400' : 'text-gray-400'}>Qty: </span>
                    <span className={isEmbedded ? 'text-gray-900 dark:text-white' : 'text-white'}>{order.quantity}</span>
                  </div>
                  <div>
                    <span className={isEmbedded ? 'text-gray-600 dark:text-gray-400' : 'text-gray-400'}>Price: </span>
                    <span className={isEmbedded ? 'text-gray-900 dark:text-white' : 'text-white'}>₹{order.price.toFixed(2)}</span>
                  </div>
                  {order.filled_price && (
                    <div>
                      <span className={isEmbedded ? 'text-gray-600 dark:text-gray-400' : 'text-gray-400'}>Filled: </span>
                      <span className={isEmbedded ? 'text-gray-900 dark:text-white' : 'text-white'}>₹{order.filled_price.toFixed(2)}</span>
                    </div>
                  )}
                  <div>
                    <span className={isEmbedded ? 'text-gray-600 dark:text-gray-400' : 'text-gray-400'}>Status: </span>
                    <span className={`${
                      order.order_status === 'EXECUTED' ? 'text-green-600 dark:text-green-400' :
                      order.order_status === 'CANCELLED' || order.order_status === 'REJECTED' ? 'text-red-600 dark:text-red-400' :
                      'text-yellow-600 dark:text-yellow-400'
                    }`}>
                      {order.order_status}
                    </span>
                  </div>
                </div>
                <div className={`text-xs mt-1 ${isEmbedded ? 'text-gray-500 dark:text-gray-400' : 'text-gray-500'}`}>
                  {new Date(order.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderBook;
