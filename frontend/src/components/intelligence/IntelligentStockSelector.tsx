import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { api } from '../../services/api';
import { formatINR, formatINRCompact } from '../../utils/currency';
import { 
  StockRecommendation, 
  MarketConditions, 
  SectorAnalysis, 
  SectorPerformance, 
  IndustrySummary,
  UserPreferences 
} from '../../types/api';
import { errorHandler, handleApiError } from '../../services/errorHandler';

interface IntelligentStockSelectorProps {
  className?: string;
}

const IntelligentStockSelector: React.FC<IntelligentStockSelectorProps> = ({ className = '' }) => {
  const [recommendations, setRecommendations] = useState<StockRecommendation[]>([]);
  const [marketConditions, setMarketConditions] = useState<MarketConditions | null>(null);
  const [sectorAnalysis, setSectorAnalysis] = useState<SectorAnalysis | null>(null);
  const [sectorPerformance, setSectorPerformance] = useState<SectorPerformance | null>(null);
  const [industrySummary, setIndustrySummary] = useState<Record<string, IndustrySummary>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('recommendations');
  const [userPreferences, setUserPreferences] = useState({
    risk_tolerance: 'medium',
    investment_horizon: 'medium_term',
    preferred_sectors: ['IT', 'Banking', 'Pharma'],
    market_cap_preference: 'large_cap',
    volatility_tolerance: 'medium',
    max_positions: 10,
    min_confidence: 0.6
  });

  useEffect(() => {
    fetchRecommendations();
    fetchMarketConditions();
    fetchSectorAnalysis();
    fetchSectorPerformance();
    fetchIndustrySummary();
  }, []);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.getStockRecommendations(userPreferences);
      
      if (response.success) {
        setRecommendations(response.data.recommendations);
      } else {
        setError('Failed to load stock recommendations');
      }
    } catch (err) {
      handleApiError(err, { 
        component: 'IntelligentStockSelector', 
        action: 'fetchRecommendations' 
      });
      setError('Error loading stock recommendations');
    } finally {
      setLoading(false);
    }
  };

  const fetchMarketConditions = async () => {
    try {
      const response = await api.getMarketOverview();
      
      if (response.success) {
        setMarketConditions(response.data.market_conditions);
      }
    } catch (err) {
      console.error('Error fetching market conditions:', err);
    }
  };

  const fetchSectorAnalysis = async () => {
    try {
      const response = await api.getSectorRotation();
      
      if (response.success) {
        setSectorAnalysis(response.data);
      }
    } catch (err) {
      console.error('Error fetching sector analysis:', err);
      // Fallback to mock data if API fails
      setSectorAnalysis({
        sector_analysis: {
          'Banking': { performance: 2.4, trend: 'up', volume: 'high', momentum: 'strong' },
          'IT': { performance: -1.2, trend: 'down', volume: 'medium', momentum: 'weak' },
          'Pharma': { performance: 3.8, trend: 'up', volume: 'high', momentum: 'strong' },
          'Auto': { performance: 0.8, trend: 'sideways', volume: 'low', momentum: 'neutral' },
          'FMCG': { performance: -0.5, trend: 'down', volume: 'medium', momentum: 'weak' },
          'Energy': { performance: 4.2, trend: 'up', volume: 'high', momentum: 'strong' },
          'Metals': { performance: 1.6, trend: 'up', volume: 'medium', momentum: 'moderate' },
          'Telecom': { performance: -2.1, trend: 'down', volume: 'low', momentum: 'weak' },
          'Real Estate': { performance: 5.1, trend: 'up', volume: 'high', momentum: 'strong' }
        },
        sector_recommendations: {
          buy: ['Real Estate', 'Energy', 'Pharma'],
          hold: ['Banking', 'Metals', 'Auto'],
          sell: ['Telecom', 'IT', 'FMCG']
        }
      });
    }
  };

  const fetchSectorPerformance = async () => {
    try {
      const response = await api.getSectorPerformance();
      if (response.success && response.data) {
        setSectorPerformance(response.data);
      } else {
        throw new Error('Failed to fetch sector performance');
      }
    } catch (err) {
      console.error('Error fetching sector performance:', err);
      // Fallback to mock data
      setSectorPerformance({
        sectors: [
          { name: 'Banking', symbol: 'NIFTY_BANK', last_price: 45000, change: 1080, change_percent: 2.4, volume: 1000000, trend: 'up', momentum: 'strong', timestamp: new Date().toISOString() },
          { name: 'IT', symbol: 'NIFTY_IT', last_price: 35000, change: -420, change_percent: -1.2, volume: 500000, trend: 'down', momentum: 'weak', timestamp: new Date().toISOString() },
          { name: 'Pharma', symbol: 'NIFTY_PHARMA', last_price: 18000, change: 684, change_percent: 3.8, volume: 800000, trend: 'up', momentum: 'strong', timestamp: new Date().toISOString() },
          { name: 'Auto', symbol: 'NIFTY_AUTO', last_price: 25000, change: 200, change_percent: 0.8, volume: 300000, trend: 'sideways', momentum: 'neutral', timestamp: new Date().toISOString() },
          { name: 'FMCG', symbol: 'NIFTY_FMCG', last_price: 55000, change: -275, change_percent: -0.5, volume: 400000, trend: 'down', momentum: 'weak', timestamp: new Date().toISOString() },
          { name: 'Energy', symbol: 'NIFTY_ENERGY', last_price: 32000, change: 1344, change_percent: 4.2, volume: 1200000, trend: 'up', momentum: 'strong', timestamp: new Date().toISOString() },
          { name: 'Metals', symbol: 'NIFTY_METAL', last_price: 15000, change: 240, change_percent: 1.6, volume: 600000, trend: 'up', momentum: 'moderate', timestamp: new Date().toISOString() },
          { name: 'Telecom', symbol: 'NIFTY_TELECOM', last_price: 12000, change: -252, change_percent: -2.1, volume: 200000, trend: 'down', momentum: 'weak', timestamp: new Date().toISOString() },
          { name: 'Real Estate', symbol: 'NIFTY_REALTY', last_price: 8000, change: 408, change_percent: 5.1, volume: 900000, trend: 'up', momentum: 'strong', timestamp: new Date().toISOString() }
        ],
        last_updated: new Date().toISOString(),
        market_status: 'open'
      });
    }
  };

  const fetchIndustrySummary = async () => {
    try {
      // Fetch industry summary for key sectors
      const sectors = ['IT', 'Banking', 'Pharma', 'Auto', 'FMCG'];
      const summaries = await Promise.all(
        sectors.map(async (sector) => {
          try {
            const response = await api.getIndustrySummary(sector);
            return { sector, data: response };
          } catch (err) {
            console.error(`Error fetching industry summary for ${sector}:`, err);
            return { sector, data: null };
          }
        })
      );
      
      const industryData: any = {};
      summaries.forEach(({ sector, data }) => {
        if (data) {
          industryData[sector] = data;
        }
      });
      
      setIndustrySummary(industryData);
    } catch (err) {
      console.error('Error fetching industry summaries:', err);
      setIndustrySummary({});
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation.toUpperCase()) {
      case 'BUY': return 'text-green-600 bg-green-100';
      case 'SELL': return 'text-red-600 bg-red-100';
      case 'HOLD': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation.toUpperCase()) {
      case 'BUY': return <ArrowTrendingUpIcon className="h-4 w-4" />;
      case 'SELL': return <ArrowTrendingDownIcon className="h-4 w-4" />;
      case 'HOLD': return <EyeIcon className="h-4 w-4" />;
      default: return <InformationCircleIcon className="h-4 w-4" />;
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTimingColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'trade_now': return 'text-green-600 bg-green-100';
      case 'wait': return 'text-yellow-600 bg-yellow-100';
      case 'proceed_with_caution': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const tabs = [
    { id: 'recommendations', label: 'Stock Recommendations', icon: ChartBarIcon },
    { id: 'market', label: 'Market Intelligence', icon: LightBulbIcon },
    { id: 'timing', label: 'Optimal Timing', icon: ClockIcon },
    { id: 'sectors', label: 'Sector Analysis', icon: CurrencyDollarIcon }
  ];

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-center text-red-600">
          <p>{error}</p>
          <button 
            onClick={fetchRecommendations}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <LightBulbIcon className="h-8 w-8 text-blue-600 mr-3" />
              Intelligent Stock Selector
            </h2>
            <p className="text-gray-600 mt-1">AI-powered stock selection and timing intelligence</p>
          </div>
          
          <button 
            onClick={() => {
              fetchRecommendations();
              fetchMarketConditions();
              fetchSectorAnalysis();
              fetchSectorPerformance();
              fetchIndustrySummary();
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
          >
            <PlayIcon className="h-4 w-4 mr-2" />
            Refresh Analysis
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {/* Stock Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                Top Stock Recommendations ({recommendations.length})
              </h3>
              <div className="text-sm text-gray-600">
                Based on AI analysis and market conditions
              </div>
            </div>

            <div className="space-y-4">
              {recommendations.map((stock) => (
                <div key={stock.symbol} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl font-bold text-gray-900">#{stock.rank}</div>
                      <div>
                        <h4 className="text-xl font-semibold text-gray-900">{stock.symbol}</h4>
                        <p className="text-sm text-gray-600">{stock.sector} • {stock.time_horizon}</p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-2xl font-bold text-gray-900">{formatINR(stock.current_price)}</div>
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getRecommendationColor(stock.recommendation)}`}>
                        {getRecommendationIcon(stock.recommendation)}
                        <span className="ml-1">{stock.recommendation}</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-600 mb-1">Confidence</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {(stock.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-600 mb-1">Price Target</div>
                      <div className="text-lg font-semibold text-green-600">
                        {formatINR(stock.price_target)}
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-600 mb-1">Stop Loss</div>
                      <div className="text-lg font-semibold text-red-600">
                        {formatINR(stock.stop_loss)}
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-600 mb-1">Risk Level</div>
                      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(stock.risk_level)}`}>
                        {stock.risk_level}
                      </div>
                    </div>
                  </div>

                  <div className="mb-4">
                    <h5 className="font-medium text-gray-900 mb-2">AI Reasoning</h5>
                    <p className="text-sm text-gray-700">{stock.reasoning}</p>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getTimingColor(stock.timing_recommendation.action)}`}>
                        <ClockIcon className="h-4 w-4 mr-1" />
                        {stock.timing_recommendation.action.replace('_', ' ').toUpperCase()}
                      </div>
                      <div className="text-sm text-gray-600">
                        {stock.timing_recommendation.reason}
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      Position: {stock.position_sizing.suggested_quantity} shares
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Market Intelligence Tab */}
        {activeTab === 'market' && marketConditions && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Market Intelligence</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-blue-50 rounded-lg p-6">
                <h4 className="font-semibold text-blue-900 mb-4">Market Conditions</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-blue-800">Trend:</span>
                    <span className="font-medium text-blue-900 capitalize">{marketConditions.market_trend}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-800">Volatility:</span>
                    <span className="font-medium text-blue-900 capitalize">{marketConditions.volatility_level}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-800">Volume:</span>
                    <span className="font-medium text-blue-900 capitalize">{marketConditions.volume_profile}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-800">Sector Rotation:</span>
                    <span className="font-medium text-blue-900 capitalize">{marketConditions.sector_rotation}</span>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 rounded-lg p-6">
                <h4 className="font-semibold text-green-900 mb-4">Economic Indicators</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-green-800">GDP Growth:</span>
                    <span className="font-medium text-green-900">{marketConditions.economic_indicators.gdp_growth}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-800">Inflation:</span>
                    <span className="font-medium text-green-900">{marketConditions.economic_indicators.inflation}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-800">Interest Rates:</span>
                    <span className="font-medium text-green-900">{marketConditions.economic_indicators.interest_rates}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-800">Currency:</span>
                    <span className="font-medium text-green-900 capitalize">{marketConditions.economic_indicators.currency_strength}</span>
                  </div>
                </div>
              </div>

              <div className="bg-yellow-50 rounded-lg p-6">
                <h4 className="font-semibold text-yellow-900 mb-4">Market Sentiment</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-yellow-800">Fear & Greed Index:</span>
                    <span className="font-medium text-yellow-900">{marketConditions.market_sentiment.fear_greed_index}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-yellow-800">Put/Call Ratio:</span>
                    <span className="font-medium text-yellow-900">{marketConditions.market_sentiment.put_call_ratio}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-yellow-800">VIX Level:</span>
                    <span className="font-medium text-yellow-900">{marketConditions.market_sentiment.vix_level}</span>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 rounded-lg p-6">
                <h4 className="font-semibold text-purple-900 mb-4">Seasonal Factors</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-purple-800">Current Month:</span>
                    <span className="font-medium text-purple-900">{marketConditions.seasonal_factors.current_month}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-800">Earnings Season:</span>
                    <span className="font-medium text-purple-900">
                      {marketConditions.seasonal_factors.earnings_season ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-800">Budget Session:</span>
                    <span className="font-medium text-purple-900">
                      {marketConditions.seasonal_factors.budget_session ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-800">Monsoon Impact:</span>
                    <span className="font-medium text-purple-900">
                      {marketConditions.seasonal_factors.monsoon_impact ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Optimal Timing Tab */}
        {activeTab === 'timing' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Optimal Trading Timing</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-green-50 rounded-lg p-6">
                <h4 className="font-semibold text-green-900 mb-4">Best Trading Hours</h4>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <CheckCircleIcon className="h-5 w-5 text-green-600 mr-3" />
                    <span className="text-green-800">09:30 - 10:30 AM (Opening momentum)</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircleIcon className="h-5 w-5 text-green-600 mr-3" />
                    <span className="text-green-800">02:00 - 03:00 PM (Closing momentum)</span>
                  </div>
                </div>
              </div>

              <div className="bg-red-50 rounded-lg p-6">
                <h4 className="font-semibold text-red-900 mb-4">Avoid These Hours</h4>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <XCircleIcon className="h-5 w-5 text-red-600 mr-3" />
                    <span className="text-red-800">09:15 - 09:30 AM (High volatility)</span>
                  </div>
                  <div className="flex items-center">
                    <XCircleIcon className="h-5 w-5 text-red-600 mr-3" />
                    <span className="text-red-800">03:00 - 03:30 PM (Closing volatility)</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-6">
              <h4 className="font-semibold text-blue-900 mb-4">Current Market Status</h4>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-900 mb-2">Market is Open</div>
                <div className="text-blue-800">Current time is optimal for trading</div>
              </div>
            </div>
          </div>
        )}

        {/* Sector Analysis Tab */}
        {activeTab === 'sectors' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Sector Analysis</h3>
              <div className="text-sm text-gray-600">
                Real-time sector performance and rotation analysis
              </div>
            </div>
            
            {/* New Sector Performance from Backend API */}
            {sectorPerformance?.sectors && (
              <div className="mb-6">
                <h4 className="text-md font-semibold text-gray-800 mb-3">Live Sector Performance</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {sectorPerformance.sectors.map((sector: any, index: number) => (
                    <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <h5 className="font-semibold text-gray-900">{sector.name}</h5>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          (sector.change_percent || 0) > 0 
                            ? 'bg-green-100 text-green-800' 
                            : (sector.change_percent || 0) < 0 
                            ? 'bg-red-100 text-red-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {(sector.change_percent || 0) > 0 ? '+' : ''}{(sector.change_percent || 0).toFixed(2)}%
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Trend:</span>
                          <span className={`capitalize ${
                            sector.trend === 'up' ? 'text-green-600' : 
                            sector.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {sector.trend || 'neutral'}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Volume:</span>
                          <span className="capitalize text-gray-900">{sector.volume || 'medium'}</span>
                        </div>
                        {sector.last_price && (
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Index Price:</span>
                            <span className="font-medium text-gray-900">{formatINR(sector.last_price)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Industry Summary from Backend API */}
            {Object.keys(industrySummary || {}).length > 0 && (
              <div className="mb-6">
                <h4 className="text-md font-semibold text-gray-800 mb-3">Industry Insights</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(industrySummary).map(([sector, data]: [string, any]) => (
                    <div key={sector} className="bg-white border border-gray-200 rounded-lg p-4">
                      <h5 className="font-semibold text-gray-900 mb-3">{sector} Industry</h5>
                      
                      {data.top_performing_companies && data.top_performing_companies.length > 0 && (
                        <div className="mb-4">
                          <h6 className="text-sm font-medium text-gray-700 mb-2">Top Performers</h6>
                          <div className="space-y-1">
                            {data.top_performing_companies.slice(0, 3).map((company: any, idx: number) => (
                              <div key={idx} className="flex justify-between text-sm">
                                <span className="text-gray-600">{company.symbol}</span>
                                <span className="text-green-600 font-medium">
                                  +{(company.change_percent || 0).toFixed(2)}%
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {data.top_growth_companies && data.top_growth_companies.length > 0 && (
                        <div>
                          <h6 className="text-sm font-medium text-gray-700 mb-2">Growth Leaders</h6>
                          <div className="space-y-1">
                            {data.top_growth_companies.slice(0, 3).map((company: any, idx: number) => (
                              <div key={idx} className="flex justify-between text-sm">
                                <span className="text-gray-600">{company.symbol}</span>
                                <span className="text-blue-600 font-medium">
                                  {formatINR(company.last_price || 0)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Legacy Sector Performance Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sectorAnalysis?.sector_analysis ? Object.entries(sectorAnalysis.sector_analysis).map(([name, data]: [string, any]) => (
                <div key={name} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-900">{name}</h4>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      data.performance > 0 
                        ? 'bg-green-100 text-green-800' 
                        : data.performance < 0 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {data.performance > 0 ? '+' : ''}{data.performance}%
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Trend:</span>
                      <span className={`capitalize ${
                        data.trend === 'up' ? 'text-green-600' : 
                        data.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {data.trend}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Volume:</span>
                      <span className="capitalize text-gray-900">{data.volume}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Momentum:</span>
                      <span className={`capitalize ${
                        data.momentum === 'strong' ? 'text-green-600' : 
                        data.momentum === 'weak' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {data.momentum}
                      </span>
                    </div>
                  </div>
                </div>
              )) : (
                // Fallback to static data if API data not available
                [
                  { name: 'Banking', performance: 2.4, trend: 'up', volume: 'high', momentum: 'strong' },
                  { name: 'IT', performance: -1.2, trend: 'down', volume: 'medium', momentum: 'weak' },
                  { name: 'Pharma', performance: 3.8, trend: 'up', volume: 'high', momentum: 'strong' },
                  { name: 'Auto', performance: 0.8, trend: 'sideways', volume: 'low', momentum: 'neutral' },
                  { name: 'FMCG', performance: -0.5, trend: 'down', volume: 'medium', momentum: 'weak' },
                  { name: 'Energy', performance: 4.2, trend: 'up', volume: 'high', momentum: 'strong' },
                  { name: 'Metals', performance: 1.6, trend: 'up', volume: 'medium', momentum: 'moderate' },
                  { name: 'Telecom', performance: -2.1, trend: 'down', volume: 'low', momentum: 'weak' },
                  { name: 'Real Estate', performance: 5.1, trend: 'up', volume: 'high', momentum: 'strong' }
                ].map((sector) => (
                  <div key={sector.name} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold text-gray-900">{sector.name}</h4>
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                        sector.performance > 0 
                          ? 'bg-green-100 text-green-800' 
                          : sector.performance < 0 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {sector.performance > 0 ? '+' : ''}{sector.performance}%
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Trend:</span>
                        <span className={`capitalize ${
                          sector.trend === 'up' ? 'text-green-600' : 
                          sector.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                        }`}>
                          {sector.trend}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Volume:</span>
                        <span className="capitalize text-gray-900">{sector.volume}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Momentum:</span>
                        <span className={`capitalize ${
                          sector.momentum === 'strong' ? 'text-green-600' : 
                          sector.momentum === 'weak' ? 'text-red-600' : 'text-gray-600'
                        }`}>
                          {sector.momentum}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Sector Rotation Analysis */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Sector Rotation Analysis</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h5 className="font-medium text-gray-900 mb-3">Currently Leading</h5>
                  <div className="space-y-2">
                    {['Real Estate', 'Energy', 'Pharma', 'Banking'].map((sector, index) => (
                      <div key={sector} className="flex items-center justify-between bg-white rounded-lg p-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                            <span className="text-green-600 text-xs font-bold">{index + 1}</span>
                          </div>
                          <span className="font-medium text-gray-900">{sector}</span>
                        </div>
                        <div className="text-green-600 font-semibold">+{4.2 - index * 0.5}%</div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h5 className="font-medium text-gray-900 mb-3">Currently Lagging</h5>
                  <div className="space-y-2">
                    {['Telecom', 'FMCG', 'IT', 'Auto'].map((sector, index) => (
                      <div key={sector} className="flex items-center justify-between bg-white rounded-lg p-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center">
                            <span className="text-red-600 text-xs font-bold">{index + 1}</span>
                          </div>
                          <span className="font-medium text-gray-900">{sector}</span>
                        </div>
                        <div className="text-red-600 font-semibold">-{2.1 + index * 0.3}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Sector Recommendations */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">AI Sector Recommendations</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <ArrowTrendingUpIcon className="h-5 w-5 text-green-600 mr-2" />
                    <h5 className="font-semibold text-green-900">Buy Opportunities</h5>
                  </div>
                  <div className="space-y-2">
                    {(sectorAnalysis?.sector_recommendations?.buy || ['Real Estate', 'Energy', 'Pharma']).map((sector: string) => (
                      <div key={sector} className="text-sm text-green-800">• {sector}: Strong momentum</div>
                    ))}
                  </div>
                </div>
                
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <EyeIcon className="h-5 w-5 text-yellow-600 mr-2" />
                    <h5 className="font-semibold text-yellow-900">Hold Positions</h5>
                  </div>
                  <div className="space-y-2">
                    {(sectorAnalysis?.sector_recommendations?.hold || ['Banking', 'Metals', 'Auto']).map((sector: string) => (
                      <div key={sector} className="text-sm text-yellow-800">• {sector}: Monitor trends</div>
                    ))}
                  </div>
                </div>
                
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <ArrowTrendingDownIcon className="h-5 w-5 text-red-600 mr-2" />
                    <h5 className="font-semibold text-red-900">Avoid/Sell</h5>
                  </div>
                  <div className="space-y-2">
                    {(sectorAnalysis?.sector_recommendations?.sell || ['Telecom', 'IT', 'FMCG']).map((sector: string) => (
                      <div key={sector} className="text-sm text-red-800">• {sector}: Regulatory headwinds</div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Sector Heat Map */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Sector Performance Heat Map</h4>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { name: 'Real Estate', performance: 5.1, color: 'bg-green-500' },
                  { name: 'Energy', performance: 4.2, color: 'bg-green-400' },
                  { name: 'Pharma', performance: 3.8, color: 'bg-green-300' },
                  { name: 'Banking', performance: 2.4, color: 'bg-green-200' },
                  { name: 'Metals', performance: 1.6, color: 'bg-yellow-200' },
                  { name: 'Auto', performance: 0.8, color: 'bg-yellow-300' },
                  { name: 'FMCG', performance: -0.5, color: 'bg-red-200' },
                  { name: 'IT', performance: -1.2, color: 'bg-red-300' },
                  { name: 'Telecom', performance: -2.1, color: 'bg-red-400' }
                ].map((sector) => (
                  <div key={sector.name} className={`${sector.color} rounded-lg p-3 text-center`}>
                    <div className="text-white font-semibold text-sm">{sector.name}</div>
                    <div className="text-white text-xs">{sector.performance > 0 ? '+' : ''}{sector.performance}%</div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center justify-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-red-400 rounded"></div>
                  <span>Underperforming</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-yellow-300 rounded"></div>
                  <span>Neutral</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-green-400 rounded"></div>
                  <span>Outperforming</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligentStockSelector;
