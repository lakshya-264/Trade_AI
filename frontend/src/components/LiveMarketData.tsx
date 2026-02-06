import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';
import { api } from '../services/api';
import { formatINR } from '../utils/currency';

interface MarketIndex {
  symbol: string;
  name: string;
  value: number;
  change: number;
  changePercent: number;
  volume?: number;
  source?: string;
  timestamp?: string;
}

interface LiveMarketDataProps {
  className?: string;
}

const LiveMarketData: React.FC<LiveMarketDataProps> = ({ className = '' }) => {
  const navigate = useNavigate();
  
  // Live Market Data Integration - Added by Critical Issues Fix v2.0
  const [marketData, setMarketData] = useState<any>(null);
  const [marketStatus, setMarketStatus] = useState<any>(null);
  const [topGainers, setTopGainers] = useState<any[]>([]);
  const [topLosers, setTopLosers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchMarketData = async (symbol = 'RELIANCE') => {
    try {
      const response = await api.get(`/api/realtime/quote/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching market data:', error);
      throw error;
    }
  };

  const fetchMarketStatus = async () => {
    try {
      const response = await api.get('/api/realtime/market-status');
      return response.data;
    } catch (error) {
      console.error('Error fetching market status:', error);
      throw error;
    }
  };

  const fetchTopGainers = async () => {
    try {
      const response = await api.get('/api/realtime/top-gainers');
      return response.data;
    } catch (error) {
      console.error('Error fetching top gainers:', error);
      throw error;
    }
  };

  const fetchTopLosers = async () => {
    try {
      const response = await api.get('/api/realtime/top-losers');
      return response.data;
    } catch (error) {
      console.error('Error fetching top losers:', error);
      throw error;
    }
  };

  // Real-time market data updates
  useEffect(() => {
    const loadMarketData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [market, status, gainers, losers] = await Promise.all([
          fetchMarketData(),
          fetchMarketStatus(),
          fetchTopGainers(),
          fetchTopLosers()
        ]);
        
        if (market) {
          setMarketData(market);
          localStorage.setItem('marketData', JSON.stringify(market));
        }
        
        if (status) {
          setMarketStatus(status);
          localStorage.setItem('marketStatus', JSON.stringify(status));
        }
        
        if (gainers && Array.isArray(gainers)) {
          setTopGainers(gainers);
          localStorage.setItem('topGainers', JSON.stringify(gainers));
        }
        
        if (losers && Array.isArray(losers)) {
          setTopLosers(losers);
          localStorage.setItem('topLosers', JSON.stringify(losers));
        }
        
        setLastUpdated(new Date().toISOString());
      } catch (error) {
        console.error('Error loading market data:', error);
        setError('Failed to load market data');
      } finally {
        setLoading(false);
      }
    };

    loadMarketData();
    
    // Refresh every 5 seconds for real-time data
    const interval = setInterval(loadMarketData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSymbolClick = (symbol: string) => {
    navigate(`/symbol/${symbol}`);
  };

  const renderMarketCard = (data: any, title: string, isPositive: boolean) => {
    if (!data) return null;

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>
        <div className="space-y-2">
          {Array.isArray(data) ? (
            data.slice(0, 5).map((item: any, index: number) => (
              <div
                key={index}
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => handleSymbolClick(item.symbol || item.name)}
              >
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">
                    {item.symbol || item.name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {item.name && item.name !== item.symbol ? item.name : ''}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {formatINR(item.price || item.value || 0)}
                  </div>
                  <div className={`text-xs flex items-center ${
                    isPositive ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {isPositive ? (
                      <ArrowTrendingUpIcon className="h-3 w-3 mr-1" />
                    ) : (
                      <ArrowTrendingDownIcon className="h-3 w-3 mr-1" />
                    )}
                    {item.changePercent ? `${item.changePercent.toFixed(2)}%` : '0.00%'}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-sm text-gray-500">No data available</div>
          )}
        </div>
      </div>
    );
  };

  if (loading && !marketData) {
    return (
      <div className={`${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-800 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Live Market Data</h2>
        {lastUpdated && (
          <p className="text-xs text-gray-500">
            Last updated: {new Date(lastUpdated).toLocaleTimeString()}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {renderMarketCard(topGainers, 'Top Gainers', true)}
        {renderMarketCard(topLosers, 'Top Losers', false)}
        
        {marketData && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Market Overview</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Current Price:</span>
                <span className="text-sm font-medium text-gray-900">
                  {formatINR(marketData.price || marketData.value || 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Change:</span>
                <span className={`text-sm font-medium ${
                  (marketData.change || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatINR(marketData.change || 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Change %:</span>
                <span className={`text-sm font-medium ${
                  (marketData.changePercent || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(marketData.changePercent || 0).toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {marketStatus && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Market Status</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Status:</span>
                <span className={`text-sm font-medium ${
                  marketStatus.isOpen ? 'text-green-600' : 'text-red-600'
                }`}>
                  {marketStatus.isOpen ? 'Open' : 'Closed'}
                </span>
              </div>
              {marketStatus.nextOpen && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Next Open:</span>
                  <span className="text-sm text-gray-900">
                    {new Date(marketStatus.nextOpen).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveMarketData;