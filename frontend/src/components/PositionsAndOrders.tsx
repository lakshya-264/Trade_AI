import React, { useState, useEffect } from 'react';
import { 
  ArrowUpIcon, 
  ArrowDownIcon, 
  ClockIcon, 
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import { httpClient, APIResponse } from '../config/api';

interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  value: number;
}

interface Order {
  id: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  timestamp: string;
  filledQuantity?: number;
  remainingQuantity?: number;
}

interface PositionsAndOrdersProps {
  className?: string;
}

const PositionsAndOrders: React.FC<PositionsAndOrdersProps> = ({ className }) => {
  const [activeTab, setActiveTab] = useState<'positions' | 'orders'>('positions');
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load real data from API
    const loadData = async () => {
      setLoading(true);
      
      try {
        // Fetch orders from API
        const ordersResponse = await httpClient.get('/api/order-book/executed-orders') as any;
        
        console.log('🔍 PositionsAndOrders API Response:', ordersResponse);
        console.log('🔍 Response data:', ordersResponse.data);
        
        if (ordersResponse?.data?.orders) {
          console.log('🔍 Using ordersResponse.data.orders:', ordersResponse.data.orders.length);
          // Transform API orders to component format
          const transformedOrders = ordersResponse.data.orders.map((order: any) => ({
            id: order.id.toString(),
            symbol: order.symbol,
            type: order.order_type || order.signal_type,
            quantity: order.quantity,
            price: order.price || order.entry_price,
            status: mapStatusToComponent(order.order_status || order.status),
            timestamp: order.created_at || order.timestamp,
            filledQuantity: order.status === 'EXECUTED' ? order.quantity : 0,
            remainingQuantity: order.status === 'PENDING' ? order.quantity : 0
          }));
          
          setOrders(transformedOrders);
        }
        
        // TODO: Fetch positions from portfolio API
        // For now, positions will be empty until we implement the positions endpoint
        setPositions([]);
        
      } catch (error) {
        console.error('Error loading orders:', error);
        setOrders([]);
        setPositions([]);
      } finally {
        setLoading(false);
      }
    };

    // Helper function to map API status to component status
    const mapStatusToComponent = (apiStatus: string): 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED' => {
      switch (apiStatus) {
        case 'PENDING':
        case 'OPEN':
          return 'PENDING';
        case 'EXECUTED':
        case 'CLOSED':
        case 'ACTIVE':
          return 'FILLED';
        case 'CANCELLED':
          return 'CANCELLED';
        case 'REJECTED':
          return 'REJECTED';
        default:
          return 'PENDING';
      }
    };

    loadData();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'FILLED':
        return <CheckCircleIcon className="h-4 w-4 text-success-600" />;
      case 'PENDING':
        return <ClockIcon className="h-4 w-4 text-warning-600" />;
      case 'CANCELLED':
        return <XCircleIcon className="h-4 w-4 text-muted-foreground" />;
      case 'REJECTED':
        return <ExclamationTriangleIcon className="h-4 w-4 text-danger-600" />;
      default:
        return <ClockIcon className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'FILLED':
        return 'text-success-600 bg-success/10';
      case 'PENDING':
        return 'text-warning-600 bg-warning/10';
      case 'CANCELLED':
        return 'text-muted-foreground bg-muted/10';
      case 'REJECTED':
        return 'text-danger-600 bg-danger/10';
      default:
        return 'text-muted-foreground bg-muted/10';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
        <div className="flex space-x-4 mb-4">
          <div className="h-8 bg-muted rounded w-20 animate-pulse" />
          <div className="h-8 bg-muted rounded w-20 animate-pulse" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("bg-card border border-border rounded-lg p-4", className)}>
      {/* Tabs */}
      <div className="flex space-x-4 mb-4 border-b border-border">
        <button
          onClick={() => setActiveTab('positions')}
          className={cn(
            "pb-2 text-sm font-medium transition-colors",
            activeTab === 'positions'
              ? 'text-primary border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          Positions ({positions.length})
        </button>
        <button
          onClick={() => setActiveTab('orders')}
          className={cn(
            "pb-2 text-sm font-medium transition-colors",
            activeTab === 'orders'
              ? 'text-primary border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          Orders ({orders.length})
        </button>
      </div>

      {/* Positions Tab */}
      {activeTab === 'positions' && (
        <div className="space-y-3">
          {positions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No positions found</p>
            </div>
          ) : (
            positions.map((position, index) => (
              <div
                key={index}
                className="p-3 border border-border rounded-lg hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-foreground">{position.symbol}</span>
                    <span className="text-sm text-muted-foreground">
                      {position.quantity} shares
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-foreground">
                      {formatCurrency(position.currentPrice)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Avg: {formatCurrency(position.avgPrice)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Value: {formatCurrency(position.value)}
                  </div>
                  <div className="text-right">
                    <div className={cn(
                      "font-medium",
                      position.pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                    )}>
                      {formatCurrency(position.pnl)}
                    </div>
                    <div className={cn(
                      "text-sm",
                      position.pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                    )}>
                      {formatPercentage(position.pnlPercent)}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div className="space-y-3">
          {orders.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No orders found</p>
            </div>
          ) : (
            orders.map((order) => (
              <div
                key={order.id}
                className="p-3 border border-border rounded-lg hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-foreground">{order.symbol}</span>
                    <div className={cn(
                      "flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium",
                      getStatusColor(order.status)
                    )}>
                      {getStatusIcon(order.status)}
                      <span>{order.status}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-foreground">
                      {formatCurrency(order.price)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {formatTime(order.timestamp)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {order.type === 'BUY' ? (
                      <ArrowUpIcon className="h-4 w-4 text-success-600" />
                    ) : (
                      <ArrowDownIcon className="h-4 w-4 text-danger-600" />
                    )}
                    <span className={cn(
                      "text-sm font-medium",
                      order.type === 'BUY' ? 'text-success-600' : 'text-danger-600'
                    )}>
                      {order.type}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {order.quantity} shares
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {order.filledQuantity && order.remainingQuantity ? (
                      <span>
                        Filled: {order.filledQuantity} | Remaining: {order.remainingQuantity}
                      </span>
                    ) : (
                      <span>Total: {order.quantity}</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default PositionsAndOrders;
