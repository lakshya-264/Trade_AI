import React, { useState, useEffect } from 'react';
import { 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  ExclamationTriangleIcon,
  WifiIcon,
  SignalSlashIcon
} from '@heroicons/react/24/outline';
import { api, ApiError } from '../services/api';

type ExchangeStatus = {
  status: string;
  next_open?: string;
  next_close?: string;
};

type MarketStatus = {
  nse: ExchangeStatus;
  bse: ExchangeStatus;
  timestamp: string;
  overall_status?: string;
};

const normalizeStatus = (raw: any): MarketStatus => {
  // Handle the actual API response format from NSE
  if (raw?.marketState && Array.isArray(raw.marketState)) {
    const capitalMarket = raw.marketState.find((market: any) => market.market === "Capital Market");
    const isOpen = capitalMarket?.marketStatus === "Open";
    
    return {
      nse: {
        status: isOpen ? 'open' : 'closed',
        next_open: isOpen ? undefined : '09:00',
        next_close: isOpen ? '15:30' : undefined
      },
      bse: {
        status: isOpen ? 'open' : 'closed',
        next_open: isOpen ? undefined : '09:00',
        next_close: isOpen ? '15:30' : undefined
      },
      timestamp: capitalMarket?.tradeDate || new Date().toISOString(),
      overall_status: isOpen ? 'open' : 'closed'
    };
  }

  // Fallback to old format
  const coerceStatus = (src: any): ExchangeStatus => ({
    status: (src?.status || raw?.market_status || raw?.status || 'closed') as string,
    next_open: src?.next_open || undefined,
    next_close: src?.next_close || undefined
  });

  const nse = coerceStatus(raw?.nse);
  const bse = coerceStatus(raw?.bse);

  return {
    nse,
    bse,
    timestamp: raw?.timestamp || new Date().toISOString(),
    overall_status: raw?.overall_status || raw?.market_status || raw?.status
  };
};

const EnhancedMarketStatusIndicator: React.FC = () => {
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    const fetchMarketStatus = async () => {
      try {
        setLoading(true);
        setError(null);

        try {
          const raw = await api.getMarketStatus();
          setMarketStatus(normalizeStatus(raw));
        } catch (apiError) {
          const now = new Date();
          const isWeekday = now.getDay() >= 1 && now.getDay() <= 5;
          const isMarketHours = isWeekday && now.getHours() >= 9 && now.getHours() < 16; // 09:00-15:59 IST

          setMarketStatus({
            nse: { 
              status: isMarketHours ? 'open' : 'closed', 
              next_open: isMarketHours ? '09:00' : '09:00',
              next_close: '15:30'
            },
            bse: { 
              status: isMarketHours ? 'open' : 'closed', 
              next_open: isMarketHours ? '09:00' : '09:00',
              next_close: '15:30'
            },
            timestamp: now.toISOString()
          });
        }
      } catch (err) {
        console.error('Error fetching market status:', err);
        if (err instanceof ApiError) setError(`API Error: ${err.message}`);
        else setError('Failed to fetch market status');
      } finally {
        setLoading(false);
      }
    };

    fetchMarketStatus();
    const interval = setInterval(fetchMarketStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status?: string) => {
    const s = (status || '').toLowerCase();
    switch (s) {
      case 'open': return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'closed': return <XCircleIcon className="h-4 w-4 text-red-500" />;
      case 'pre-market':
      case 'post-market': return <ClockIcon className="h-4 w-4 text-yellow-500" />;
      default: return <ExclamationTriangleIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status?: string) => {
    const s = (status || '').toLowerCase();
    switch (s) {
      case 'open': return 'text-green-600 bg-green-100';
      case 'closed': return 'text-red-600 bg-red-100';
      case 'pre-market':
      case 'post-market': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600"></div>
        <span className="text-sm text-gray-600">Loading market status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center space-x-2">
        <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
        <span className="text-sm text-red-600">Market status unavailable</span>
      </div>
    );
  }

  if (!marketStatus) return null;

  const nse = marketStatus?.nse ?? { status: 'unknown' };
  const bse = marketStatus?.bse ?? { status: 'unknown' };
  const overallStatus = marketStatus?.overall_status ||
    (nse.status === 'open' || bse.status === 'open' ? 'open' : 'closed');

  return (
    <div className="flex items-center space-x-4">
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700">Market:</span>
        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(overallStatus)}`}>
          {getStatusIcon(overallStatus)}
          <span className="capitalize">{overallStatus}</span>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700">NSE:</span>
        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(nse.status)}`}>
          {getStatusIcon(nse.status)}
          <span className="capitalize">{nse.status || 'unknown'}</span>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700">BSE:</span>
        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bse.status)}`}>
          {getStatusIcon(bse.status)}
          <span className="capitalize">{bse.status || 'unknown'}</span>
        </div>
      </div>

      <div className="flex items-center space-x-1">
        {isOnline ? (
          <>
            <WifiIcon className="h-4 w-4 text-green-500" />
            <span className="text-xs text-green-600 font-medium">Online</span>
          </>
        ) : (
          <>
            <SignalSlashIcon className="h-4 w-4 text-red-500" />
            <span className="text-xs text-red-600 font-medium">Offline</span>
          </>
        )}
      </div>

      <div className="text-xs text-gray-500">
        Updated: {new Date(marketStatus.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' })}
      </div>
    </div>
  );
};

export default EnhancedMarketStatusIndicator;


