import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { toast } from 'react-hot-toast';

interface WebSocketContextType {
  isConnected: boolean;
  lastMessage: any;
  sendMessage: (message: any) => void;
  subscribeToSymbol: (symbol: string) => void;
  unsubscribeFromSymbol: (symbol: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  // const [subscribedSymbols, setSubscribedSymbols] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Check if WebSocket is enabled (can be disabled for development)
    const wsEnabled = process.env.REACT_APP_WS_ENABLED !== 'false';
    if (!wsEnabled) {
      console.log('WebSocket disabled by configuration');
      return;
    }
    
    // TEMPORARY FIX: Always disable WebSocket to stop errors
    console.log('WebSocket temporarily disabled to prevent errors');
    return;

    const connectWebSocket = () => {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
      
      // Check if WebSocket is supported
      if (!window.WebSocket) {
        console.warn('WebSocket not supported in this browser');
        return;
      }
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        toast.success('Connected to live data feed');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          
          // Handle different message types
          if (data.type === 'price_update') {
            // Update price data
            console.log('Price update:', data);
          } else if (data.type === 'trading_signal') {
            // Show trading signal notification
            toast.success(`Trading Signal: ${data.symbol} - ${data.signal}`);
          } else if (data.type === 'subscription_confirmed') {
            console.log(`Subscribed to ${data.symbol}`);
          } else if (data.type === 'unsubscription_confirmed') {
            console.log(`Unsubscribed from ${data.symbol}`);
          } else if (data.type === 'error') {
            toast.error(data.message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        
        // Only show error toast if it's not a clean close and not already showing
        if (event.code !== 1000 && !document.querySelector('.toast-error')) {
          toast.error('Disconnected from live data feed');
        }
        
        // Attempt to reconnect after 5 seconds (increased delay to reduce spam)
        setTimeout(() => {
          if (!isConnected) {
            connectWebSocket();
          }
        }, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Only show error toast if not already showing to avoid spam
        if (!document.querySelector('.toast-error')) {
          toast.error('WebSocket connection error');
        }
      };

      setSocket(ws);
    };

    connectWebSocket();

    return () => {
      // Cleanup will be handled by the component unmount
    };
  }, []); // Empty dependency array to prevent infinite re-renders

  const sendMessage = (message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  };

  const subscribeToSymbol = (symbol: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'subscribe',
        symbol: symbol
      };
      socket.send(JSON.stringify(message));
      // setSubscribedSymbols(prev => new Set([...prev, symbol]));
      console.log(`Subscribed to ${symbol}`);
    }
  };

  const unsubscribeFromSymbol = (symbol: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'unsubscribe',
        symbol: symbol
      };
      socket.send(JSON.stringify(message));
      // setSubscribedSymbols(prev => {
      //   const newSet = new Set(prev);
      //   newSet.delete(symbol);
      //   return newSet;
      // });
      console.log(`Unsubscribed from ${symbol}`);
    }
  };

  const value: WebSocketContextType = {
    isConnected,
    lastMessage,
    sendMessage,
    subscribeToSymbol,
    unsubscribeFromSymbol
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
