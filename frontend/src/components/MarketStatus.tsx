import React, { useState, useEffect } from 'react';
import { MarketStatus } from '../types/api';
import api from '../services/api';

interface MarketStatusProps {
  className?: string;
}

const MarketStatusComponent: React.FC<MarketStatusProps> = ({ className = '' }) => {
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarketStatus = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get('/api/realtime/market-status');
        
        if (response && response.data && typeof response.data === 'object' && 'nse' in response.data && 'bse' in response.data) {
          setMarketStatus(response.data as MarketStatus);
        }
      } catch (err) {
        console.error('Error fetching market status:', err);
        setError('Failed to fetch market status');
      } finally {
        setLoading(false);
      }
    };

    fetchMarketStatus();
  }, []);

  if (loading) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-4 text-red-600 ${className}`}>
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!marketStatus) {
    return (
      <div className={`p-4 text-gray-500 ${className}`}>
        <p>No market status available</p>
      </div>
    );
  }

  return (
    <div className={`p-4 ${className}`}>
      <h3 className="text-lg font-semibold mb-2">Market Status</h3>
      <div className="space-y-2">
        <div className="flex justify-between">
          <span>NSE:</span>
          <span className={marketStatus.nse?.status === 'open' ? 'text-green-600' : 'text-red-600'}>
            {marketStatus.nse?.status || 'Unknown'}
          </span>
        </div>
        <div className="flex justify-between">
          <span>BSE:</span>
          <span className={marketStatus.bse?.status === 'open' ? 'text-green-600' : 'text-red-600'}>
            {marketStatus.bse?.status || 'Unknown'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MarketStatusComponent;
