/**
 * Enhanced WebSocket Context with Type Safety
 * Provides real-time data updates with proper typing
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { 
  WebSocketMessage, 
  PriceUpdateMessage, 
  TradingSignalMessage, 
  MarketStatusMessage, 
  OrderUpdateMessage, 
  ErrorMessage,
  WebSocketConfig,
  WebSocketState,
  TradingSignal,
  ChartData
} from '../types/api';
import { errorHandler, handleNetworkError } from '../services/errorHandler';

interface WebSocketContextType {
  state: WebSocketState;
  connect: () => void;
  disconnect: () => void;
  subscribe: (symbol: string) => void;
  unsubscribe: (symbol: string) => void;
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  priceUpdates: Map<string, PriceUpdateMessage['data']>;
  tradingSignals: TradingSignal[];
  marketStatus: MarketStatusMessage['data'] | null;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: React.ReactNode;
  config?: Partial<WebSocketConfig>;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ 
  children, 
  config: userConfig 
}) => {
  const defaultConfig: WebSocketConfig = {
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
    protocols: [],
    reconnect_interval: 5000,
    max_reconnect_attempts: 10,
    heartbeat_interval: 30000,
    ...userConfig
  };

  const [state, setState] = useState<WebSocketState>({
    connected: false,
    connecting: false,
    error: null,
    last_message: null,
    reconnect_attempts: 0,
    subscriptions: []
  });

  const [priceUpdates, setPriceUpdates] = useState<Map<string, PriceUpdateMessage['data']>>(new Map());
  const [tradingSignals, setTradingSignals] = useState<TradingSignal[]>([]);
  const [marketStatus, setMarketStatus] = useState<MarketStatusMessage['data'] | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastMessageRef = useRef<WebSocketMessage | null>(null);

  // Message handlers with type safety
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      lastMessageRef.current = message;

      setState(prev => ({
        ...prev,
        last_message: message,
        error: null
      }));

      // Type-safe message handling
      switch (message.type) {
        case 'price_update':
          const priceData = message as PriceUpdateMessage;
          setPriceUpdates(prev => {
            const newMap = new Map(prev);
            newMap.set(priceData.data.symbol, priceData.data);
            return newMap;
          });
          break;

        case 'trading_signal':
          const signalData = message as TradingSignalMessage;
          setTradingSignals(prev => {
            const newSignals = [signalData.data, ...prev.slice(0, 49)]; // Keep last 50 signals
            return newSignals;
          });
          break;

        case 'market_status':
          const statusData = message as MarketStatusMessage;
          setMarketStatus(statusData.data);
          break;

        case 'order_update':
          const orderData = message as OrderUpdateMessage;
          // Handle order updates (could trigger notifications, update UI, etc.)
          console.log('Order update received:', orderData.data);
          break;

        case 'error':
          const errorData = message as ErrorMessage;
          errorHandler.handleApiError(new Error(errorData.data.message), {
            component: 'WebSocket',
            action: 'handleMessage',
            requestId: `ws_${Date.now()}`
          });
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    } catch (error) {
      errorHandler.handleApiError(error, {
        component: 'WebSocket',
        action: 'parseMessage'
      });
    }
  }, []);

  const handleOpen = useCallback(() => {
    setState(prev => ({
      ...prev,
      connected: true,
      connecting: false,
      error: null,
      reconnect_attempts: 0
    }));

    // Resubscribe to previous subscriptions
    state.subscriptions.forEach(symbol => {
      sendMessage({ type: 'subscribe', symbol });
    });

    // Start heartbeat
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'ping' });
      }
    }, defaultConfig.heartbeat_interval);
  }, [state.subscriptions]);

  const handleClose = useCallback((event: CloseEvent) => {
    setState(prev => ({
      ...prev,
      connected: false,
      connecting: false,
      error: event.reason || 'Connection closed'
    }));

    // Clear heartbeat
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    // Attempt reconnection if not manually closed
    if (event.code !== 1000 && state.reconnect_attempts < (defaultConfig.max_reconnect_attempts || 10)) {
      const delay = defaultConfig.reconnect_interval! * Math.pow(2, state.reconnect_attempts);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        setState(prev => ({
          ...prev,
          reconnect_attempts: prev.reconnect_attempts + 1
        }));
        connect();
      }, delay);
    }
  }, [state.reconnect_attempts]);

  const handleError = useCallback((error: Event) => {
    errorHandler.handleNetworkError(new Error('WebSocket error'), {
      component: 'WebSocket',
      action: 'connection'
    });

    setState(prev => ({
      ...prev,
      error: 'WebSocket connection error',
      connecting: false
    }));
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || state.connecting) {
      return;
    }

    setState(prev => ({ ...prev, connecting: true, error: null }));

    try {
      wsRef.current = new WebSocket(defaultConfig.url, defaultConfig.protocols);
      
      wsRef.current.onopen = handleOpen;
      wsRef.current.onmessage = handleMessage;
      wsRef.current.onclose = handleClose;
      wsRef.current.onerror = handleError;
    } catch (error) {
      errorHandler.handleNetworkError(error, {
        component: 'WebSocket',
        action: 'connect'
      });
      
      setState(prev => ({
        ...prev,
        connecting: false,
        error: 'Failed to create WebSocket connection'
      }));
    }
  }, [defaultConfig.url, defaultConfig.protocols, handleOpen, handleMessage, handleClose, handleError, state.connecting]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    setState(prev => ({
      ...prev,
      connected: false,
      connecting: false,
      reconnect_attempts: 0
    }));
  }, []);

  const subscribe = useCallback((symbol: string) => {
    if (!state.subscriptions.includes(symbol)) {
      setState(prev => ({
        ...prev,
        subscriptions: [...prev.subscriptions, symbol]
      }));

      if (state.connected) {
        sendMessage({ type: 'subscribe', symbol });
      }
    }
  }, [state.subscriptions, state.connected]);

  const unsubscribe = useCallback((symbol: string) => {
    setState(prev => ({
      ...prev,
      subscriptions: prev.subscriptions.filter(s => s !== symbol)
    }));

    if (state.connected) {
      sendMessage({ type: 'unsubscribe', symbol });
    }
  }, [state.connected]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (error) {
        errorHandler.handleApiError(error, {
          component: 'WebSocket',
          action: 'sendMessage'
        });
      }
    } else {
      console.warn('WebSocket not connected, cannot send message:', message);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
  }, [connect]);

  const contextValue: WebSocketContextType = {
    state,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendMessage,
    lastMessage: lastMessageRef.current,
    priceUpdates,
    tradingSignals,
    marketStatus
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

// Hook for real-time price updates
export const usePriceUpdates = (symbol: string) => {
  const { priceUpdates, subscribe, unsubscribe } = useWebSocket();
  
  useEffect(() => {
    subscribe(symbol);
    return () => unsubscribe(symbol);
  }, [symbol, subscribe, unsubscribe]);

  return priceUpdates.get(symbol) || null;
};

// Hook for trading signals
export const useTradingSignals = (symbol?: string) => {
  const { tradingSignals } = useWebSocket();
  
  if (symbol) {
    return tradingSignals.filter(signal => signal.symbol === symbol);
  }
  
  return tradingSignals;
};

// Hook for market status
export const useMarketStatus = () => {
  const { marketStatus } = useWebSocket();
  return marketStatus;
};

export default WebSocketContext;
