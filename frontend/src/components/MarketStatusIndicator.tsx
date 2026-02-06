import React, { useState, useEffect } from 'react';
import { 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import { api, ApiError } from '../services/api';

interface MarketStatus {
  nse: {
    status: string;
    next_open?: string;
    next_close?: string;
  };
  bse: {
    status: string;
    next_open?: string;
    next_close?: string;
  };
  timestamp: string;
}

const MarketStatusIndicator: React.FC = () => {
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarketStatus = async () => {
      try {
        setLoading(true);
        setError(null);
        const status = await api.getMarketStatus();
        setMarketStatus(status);
      } catch (err) {
        console.error('Error fetching market status:', err);
        // Fallback: Calculate market status based on current time
        const now = new Date();
        const isWeekday = now.getDay() >= 1 && now.getDay() <= 5; // Monday to Friday
        const currentHour = now.getHours();
        const currentMinute = now.getMinutes();
        const isMarketHours = isWeekday && 
          ((currentHour === 9 && currentMinute >= 15) || (currentHour > 9 && currentHour < 15) || 
           (currentHour === 15 && currentMinute < 30));
        
        // Calculate next open time (proper date format)
        const nextOpenDate = new Date();
        if (!isMarketHours || currentHour >= 15) {
          // Market is closed, calculate next open
          nextOpenDate.setHours(9, 15, 0, 0);
          if (currentHour >= 15 || !isWeekday) {
            // Move to next weekday
            nextOpenDate.setDate(nextOpenDate.getDate() + 1);
            while (nextOpenDate.getDay() === 0 || nextOpenDate.getDay() === 6) {
              nextOpenDate.setDate(nextOpenDate.getDate() + 1);
            }
          }
        }
        
        setMarketStatus({
          nse: { 
            status: isMarketHours ? 'open' : 'closed',
            next_open: isMarketHours ? undefined : nextOpenDate.toISOString(),
            next_close: isMarketHours ? '15:30' : undefined
          },
          bse: { 
            status: isMarketHours ? 'open' : 'closed',
            next_open: isMarketHours ? undefined : nextOpenDate.toISOString(),
            next_close: isMarketHours ? '15:30' : undefined
          },
          timestamp: now.toISOString()
        });
      } finally {
        setLoading(false);
      }
    };

    fetchMarketStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchMarketStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string | undefined) => {
    if (!status) return <ExclamationTriangleIcon className="h-4 w-4 text-gray-500" />;
    
    switch (status.toLowerCase()) {
      case 'open':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'closed':
        return <XCircleIcon className="h-4 w-4 text-red-500" />;
      case 'pre-market':
      case 'post-market':
        return <ClockIcon className="h-4 w-4 text-yellow-500" />;
      default:
        return <ExclamationTriangleIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string | undefined) => {
    if (!status) return 'text-gray-600 bg-gray-100';
    
    switch (status.toLowerCase()) {
      case 'open':
        return 'text-green-600 bg-green-100';
      case 'closed':
        return 'text-red-600 bg-red-100';
      case 'pre-market':
      case 'post-market':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTime = (timeString?: string) => {
    if (!timeString) return 'N/A';
    try {
      // Check if it's already a time string (HH:MM format)
      if (/^\d{1,2}:\d{2}$/.test(timeString)) {
        // It's already in HH:MM format, return as is
        return timeString;
      }
      // Otherwise, try to parse as date
      const date = new Date(timeString);
      if (isNaN(date.getTime())) {
        // Invalid date, return original string
        return timeString;
      }
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Kolkata'
      });
    } catch {
      return timeString;
    }
  };
  
  const formatNextOpenTime = (nextOpen?: string) => {
    if (!nextOpen) return null;
    
    // If it's already in HH:MM format, use it directly
    if (/^\d{1,2}:\d{2}$/.test(nextOpen)) {
      // Calculate next market open date
      const now = new Date();
      const [hours, minutes] = nextOpen.split(':').map(Number);
      
      // Create date for next market open (today if before 9 AM, tomorrow if after)
      const nextOpenDate = new Date();
      nextOpenDate.setHours(hours, minutes, 0, 0);
      
      // If market already closed today and it's past 9 AM, show tomorrow
      if (now.getHours() >= 15 || (now.getHours() >= 9 && now.getHours() < 15 && now.getHours() > hours)) {
        nextOpenDate.setDate(nextOpenDate.getDate() + 1);
      }
      
      // If it's a weekend, move to next Monday
      while (nextOpenDate.getDay() === 0 || nextOpenDate.getDay() === 6) {
        nextOpenDate.setDate(nextOpenDate.getDate() + 1);
      }
      
      return nextOpenDate.toLocaleDateString('en-IN', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    }
    
    // Otherwise, try to format as date
    return formatTime(nextOpen);
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

  if (!marketStatus) {
    return null;
  }

  return (
    <div className="flex items-center space-x-4">
      {/* NSE Status */}
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700">NSE:</span>
        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(marketStatus.nse.status)}`}>
          {getStatusIcon(marketStatus.nse.status)}
          <span>{marketStatus.nse.status}</span>
        </div>
        {marketStatus.nse.status && marketStatus.nse.status.toLowerCase() === 'closed' && marketStatus.nse.next_open && (
          <span className="text-xs text-gray-500">
            Opens at {formatNextOpenTime(marketStatus.nse.next_open) || formatTime(marketStatus.nse.next_open)}
          </span>
        )}
      </div>

      {/* BSE Status */}
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700">BSE:</span>
        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(marketStatus.bse.status)}`}>
          {getStatusIcon(marketStatus.bse.status)}
          <span>{marketStatus.bse.status}</span>
        </div>
        {marketStatus.bse.status && marketStatus.bse.status.toLowerCase() === 'closed' && marketStatus.bse.next_open && (
          <span className="text-xs text-gray-500">
            Opens at {formatNextOpenTime(marketStatus.bse.next_open) || formatTime(marketStatus.bse.next_open)}
          </span>
        )}
      </div>

      {/* Last Updated */}
      <div className="text-xs text-gray-500">
        Updated: {formatTime(marketStatus.timestamp)}
      </div>
    </div>
  );
};

export default MarketStatusIndicator;
