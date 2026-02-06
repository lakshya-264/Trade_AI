/**
 * Market Factors Panel Component
 * Displays news, orderbook, block deals, FII/DII flows for a stock
 */

import React, { useState, useEffect } from 'react';
import { 
  NewspaperIcon, 
  ChartBarIcon, 
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  InformationCircleIcon,
  PencilIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { httpClient } from '../config/api';

interface MarketFactorsPanelProps {
  symbol: string;
  className?: string;
}

interface ResearchReportApiResponse {
  sections?: {
    market_factors?: MarketFactors;
  };
}

interface MarketFactors {
  news?: {
    total_news: number;
    positive_count: number;
    negative_count: number;
    sentiment: string;
    recent_news: Array<{
      title: string;
      date: string;
      sentiment?: string;
    }>;
  };
  orderbook?: {
    buy_pressure: string;
    sell_pressure: string;
    volume: number;
    interpretation: string;
  };
  block_deals?: Array<{
    date: string;
    buyer: string;
    seller: string;
    quantity: number;
    price: number;
    value: number;
    exchange: string;
  }>;
  fii_dii_flows?: {
    fii_net_investment: number;
    dii_net_investment: number;
    trend: string;
    data_source: string;
  };
  impact_analysis?: {
    overall_impact: string;
    impact_score: number;
    impact_factors: string[];
    summary: string;
  };
}

const MarketFactorsPanel: React.FC<MarketFactorsPanelProps> = ({
  symbol,
  className = ''
}) => {
  const [factors, setFactors] = useState<MarketFactors | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showManualInput, setShowManualInput] = useState(false);
  const [manualFII, setManualFII] = useState<string>('');
  const [manualDII, setManualDII] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (symbol) {
      fetchMarketFactors();
    }
  }, [symbol]);

  const fetchMarketFactors = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch from research report endpoint (which includes market factors)
      const response = await httpClient.get<ResearchReportApiResponse>(`/api/financial/research-report/${symbol}`);
      
      if (response.data?.sections?.market_factors) {
        setFactors(response.data.sections.market_factors);
      } else {
        setError('Market factors data not available');
      }
    } catch (err: any) {
      console.error('Error fetching market factors:', err);
      setError(err.message || 'Failed to load market factors');
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = async () => {
    const fiiValue = parseFloat(manualFII);
    const diiValue = parseFloat(manualDII);
    
    if (isNaN(fiiValue) || isNaN(diiValue)) {
      alert('Please enter valid numbers for FII and DII values');
      return;
    }
    
    setSubmitting(true);
    try {
      const response = await httpClient.post<{ success: boolean; message?: string; data?: any }>('/api/market-factors/fii-dii/manual', {
        fii_net_investment: fiiValue,
        dii_net_investment: diiValue
      });
      
      if (response.data?.success) {
        alert('FII/DII data set successfully! Refreshing...');
        setShowManualInput(false);
        setManualFII('');
        setManualDII('');
        // Refresh market factors
        await fetchMarketFactors();
      } else {
        alert('Failed to set FII/DII data');
      }
    } catch (err: any) {
      console.error('Error setting manual FII/DII:', err);
      alert(err.response?.data?.detail || 'Failed to set FII/DII data');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className={`bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-[#2a2e39] rounded w-1/3"></div>
          <div className="h-4 bg-[#2a2e39] rounded"></div>
          <div className="h-4 bg-[#2a2e39] rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (error || !factors) {
    return (
      <div className={`bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6 ${className}`}>
        <p className="text-red-400 text-sm">{error || 'No market factors data available'}</p>
      </div>
    );
  }

  const formatNumber = (value?: number, decimals = 2, prefix = '', suffix = '') => {
    return typeof value === 'number' ? `${prefix}${value.toFixed(decimals)}${suffix}` : 'N/A';
  };

  const formatDivided = (value?: number, divisor = 1, decimals = 2, suffix = '') => {
    return typeof value === 'number' ? `${(value / divisor).toFixed(decimals)}${suffix}` : 'N/A';
  };

  const fiiTrend = factors.fii_dii_flows?.trend || 'neutral';
  const fiiTrendLabel = fiiTrend ? fiiTrend.toUpperCase() : 'N/A';
  const impactLabel = factors.impact_analysis?.overall_impact || 'Neutral';

  return (
    <div className={`bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6 ${className}`}>
      <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <ChartBarIcon className="h-6 w-6 text-blue-400" />
        Market Factors
      </h3>

      <div className="space-y-6">
        {/* News Section */}
        {factors.news && factors.news.total_news > 0 && (
          <div className="bg-[#2a2e39] rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-lg font-semibold text-white flex items-center gap-2">
                <NewspaperIcon className="h-5 w-5 text-blue-400" />
                Recent News ({factors.news.total_news})
              </h4>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                factors.news.sentiment === 'positive' ? 'bg-green-900/50 text-green-400' :
                factors.news.sentiment === 'negative' ? 'bg-red-900/50 text-red-400' :
                'bg-gray-700 text-gray-400'
              }`}>
                {factors.news.sentiment.toUpperCase()}
              </span>
            </div>
            
            <div className="space-y-2">
              {factors.news.recent_news?.slice(0, 3).map((news, idx) => (
                <div key={idx} className="bg-[#1e222d] p-3 rounded">
                  <p className="text-white text-sm">{news.title}</p>
                  <p className="text-gray-400 text-xs mt-1">{news.date}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Orderbook & FII/DII Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Orderbook */}
          {factors.orderbook && (
            <div className="bg-[#2a2e39] rounded-lg p-4">
              <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <ChartBarIcon className="h-5 w-5 text-green-400" />
                Orderbook
              </h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Buy Pressure</span>
                  <span className={`font-bold text-sm ${
                    factors.orderbook.buy_pressure === 'high' ? 'text-green-400' :
                    factors.orderbook.buy_pressure === 'medium' ? 'text-yellow-400' :
                    'text-gray-400'
                  }`}>
                    {factors.orderbook.buy_pressure.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Sell Pressure</span>
                  <span className={`font-bold text-sm ${
                    factors.orderbook.sell_pressure === 'high' ? 'text-red-400' :
                    factors.orderbook.sell_pressure === 'medium' ? 'text-yellow-400' :
                    'text-gray-400'
                  }`}>
                    {factors.orderbook.sell_pressure.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Volume</span>
                  <span className="text-white font-semibold">
                    {formatDivided(factors.orderbook.volume, 1_000_000, 2, 'M')}
                  </span>
                </div>
                <p className="text-gray-400 text-xs mt-2">{factors.orderbook.interpretation}</p>
              </div>
            </div>
          )}

          {/* FII/DII Flows */}
          {factors.fii_dii_flows && (
            <div className="bg-[#2a2e39] rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-lg font-semibold text-white flex items-center gap-2">
                  <CurrencyDollarIcon className="h-5 w-5 text-purple-400" />
                  Institutional Flows
                </h4>
                {(factors.fii_dii_flows.data_source === 'NONE' || factors.fii_dii_flows.data_source === 'ERROR') && (
                  <button
                    onClick={() => setShowManualInput(true)}
                    className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors"
                    title="Set manual FII/DII data"
                  >
                    <PencilIcon className="h-3 w-3" />
                    Set Manual
                  </button>
                )}
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">FII Net Investment</span>
                  <span
                    className={`font-bold text-sm ${
                      typeof factors.fii_dii_flows.fii_net_investment === 'number'
                        ? factors.fii_dii_flows.fii_net_investment > 0
                          ? 'text-green-400'
                          : factors.fii_dii_flows.fii_net_investment < 0
                            ? 'text-red-400'
                            : 'text-gray-400'
                        : 'text-gray-400'
                    }`}
                  >
                    {formatNumber(factors.fii_dii_flows.fii_net_investment, 2, '₹', ' Cr')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">DII Net Investment</span>
                  <span
                    className={`font-bold text-sm ${
                      typeof factors.fii_dii_flows.dii_net_investment === 'number'
                        ? factors.fii_dii_flows.dii_net_investment > 0
                          ? 'text-green-400'
                          : factors.fii_dii_flows.dii_net_investment < 0
                            ? 'text-red-400'
                            : 'text-gray-400'
                        : 'text-gray-400'
                    }`}
                  >
                    {formatNumber(factors.fii_dii_flows.dii_net_investment, 2, '₹', ' Cr')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Trend</span>
                  <span className={`font-bold text-sm ${
                    fiiTrend === 'positive' ? 'text-green-400' :
                    fiiTrend === 'negative' ? 'text-red-400' :
                    'text-gray-400'
                  }`}>
                    {fiiTrendLabel}
                  </span>
                </div>
                <p className="text-gray-400 text-xs mt-2 flex items-center gap-1">
                  <InformationCircleIcon className="h-3 w-3" />
                  Source: {factors.fii_dii_flows.data_source}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Block Deals */}
        {factors.block_deals && factors.block_deals.length > 0 && (
          <div className="bg-[#2a2e39] rounded-lg p-4">
            <h4 className="text-lg font-semibold text-white mb-3">
              Recent Block Deals ({factors.block_deals.length})
            </h4>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e222d]">
                    <th className="text-left text-gray-400 py-2">Date</th>
                    <th className="text-left text-gray-400 py-2">Buyer</th>
                    <th className="text-left text-gray-400 py-2">Seller</th>
                    <th className="text-right text-gray-400 py-2">Qty</th>
                    <th className="text-right text-gray-400 py-2">Price</th>
                    <th className="text-right text-gray-400 py-2">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {factors.block_deals.slice(0, 5).map((deal, idx) => (
                    <tr key={idx} className="border-b border-[#1e222d]">
                      <td className="text-white py-2">{deal.date || 'N/A'}</td>
                      <td className="text-green-400 py-2">{deal.buyer || 'N/A'}</td>
                      <td className="text-red-400 py-2">{deal.seller || 'N/A'}</td>
                      <td className="text-white text-right py-2">
                        {formatDivided(deal.quantity, 1_000, 1, 'K')}
                      </td>
                      <td className="text-white text-right py-2">
                        {formatNumber(deal.price, 2, '₹')}
                      </td>
                      <td className="text-white text-right py-2">
                        {typeof deal.value === 'number'
                          ? `₹${(deal.value / 10_000_000).toFixed(2)} Cr`
                          : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Impact Analysis */}
        {factors.impact_analysis && (
          <div className="bg-[#2a2e39] rounded-lg p-4">
            <h4 className="text-lg font-semibold text-white mb-3">Overall Impact</h4>
            <div className="flex items-center gap-3 mb-2">
              <span className={`text-2xl font-bold ${
                impactLabel.toLowerCase().includes('positive') ? 'text-green-400' :
                impactLabel.toLowerCase().includes('negative') ? 'text-red-400' :
                'text-gray-400'
              }`}>
                {impactLabel}
              </span>
              <span className="text-gray-400 text-sm">
                {typeof factors.impact_analysis.impact_score === 'number'
                  ? `(Score: ${factors.impact_analysis.impact_score > 0 ? '+' : ''}${factors.impact_analysis.impact_score.toFixed(1)})`
                  : '(Score: N/A)'}
              </span>
            </div>
            <p className="text-gray-300 text-sm mb-2">{factors.impact_analysis.summary}</p>
            {factors.impact_analysis.impact_factors.length > 0 && (
              <div className="mt-3">
                <p className="text-gray-400 text-xs mb-1">Key Factors:</p>
                <ul className="list-disc list-inside text-gray-400 text-xs space-y-1">
                  {factors.impact_analysis.impact_factors.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Manual FII/DII Input Modal */}
      {showManualInput && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Set Manual FII/DII Data</h3>
              <button
                onClick={() => {
                  setShowManualInput(false);
                  setManualFII('');
                  setManualDII('');
                }}
                className="text-gray-400 hover:text-white"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <p className="text-gray-400 text-sm mb-4">
              Enter FII and DII net investment values in Crores (₹ Cr). 
              You can find this data at{' '}
              <a 
                href="https://www.nseindia.com/market-data/fii-dii-data" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              >
                NSE FII/DII Data
              </a>
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  FII Net Investment (₹ Cr)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={manualFII}
                  onChange={(e) => setManualFII(e.target.value)}
                  placeholder="e.g., 1234.56"
                  className="w-full px-3 py-2 bg-[#2a2e39] border border-[#3a3e49] rounded text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  DII Net Investment (₹ Cr)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={manualDII}
                  onChange={(e) => setManualDII(e.target.value)}
                  placeholder="e.g., -567.89"
                  className="w-full px-3 py-2 bg-[#2a2e39] border border-[#3a3e49] rounded text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>
              
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleManualSubmit}
                  disabled={submitting}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded transition-colors"
                >
                  {submitting ? 'Submitting...' : 'Submit'}
                </button>
                <button
                  onClick={() => {
                    setShowManualInput(false);
                    setManualFII('');
                    setManualDII('');
                  }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketFactorsPanel;

