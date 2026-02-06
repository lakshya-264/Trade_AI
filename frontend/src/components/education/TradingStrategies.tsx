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
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { api } from '../../services/api';

interface Strategy {
  name: string;
  description: string;
  time_horizon: string;
  risk_level: string;
  capital_required: string;
  strategy_details: {
    entry_criteria: string[];
    exit_criteria: string[];
    risk_management: string[];
    best_practices: string[];
  };
  example_scenario: {
    stock: string;
    entry_price: number;
    stop_loss: number;
    target: number;
    quantity: number;
    risk: string;
    potential_profit: string;
    reasoning: string;
  };
}

interface TradingStrategiesProps {
  className?: string;
}

const TradingStrategies: React.FC<TradingStrategiesProps> = ({ className = '' }) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.getTradingStrategies();
      
      if (response.success) {
        const strategiesData = response.data.strategies;
        setStrategies(Object.values(strategiesData));
      } else {
        setError('Failed to load trading strategies');
      }
    } catch (err) {
      console.error('Error fetching strategies:', err);
      setError('Error loading trading strategies');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low': return <CheckCircleIcon className="h-4 w-4" />;
      case 'medium': return <ExclamationTriangleIcon className="h-4 w-4" />;
      case 'high': return <XCircleIcon className="h-4 w-4" />;
      default: return <InformationCircleIcon className="h-4 w-4" />;
    }
  };

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
            onClick={fetchStrategies}
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
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <ChartBarIcon className="h-8 w-8 text-blue-600 mr-3" />
          Trading Strategies
        </h2>
        <p className="text-gray-600 mt-1">Learn different trading approaches and their applications</p>
      </div>

      {/* Strategy Selection */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {strategies.map((strategy) => (
            <button
              key={strategy.name}
              onClick={() => setSelectedStrategy(strategy.name)}
              className={`p-4 rounded-lg border-2 transition-all ${
                selectedStrategy === strategy.name
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-left">
                <h3 className="font-semibold text-gray-900 mb-2">{strategy.name}</h3>
                <div className="space-y-2">
                  <div className="flex items-center text-sm text-gray-600">
                    <ClockIcon className="h-4 w-4 mr-2" />
                    {strategy.time_horizon}
                  </div>
                  <div className="flex items-center text-sm">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(strategy.risk_level)}`}>
                      {getRiskIcon(strategy.risk_level)}
                      <span className="ml-1">{strategy.risk_level}</span>
                    </span>
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <CurrencyDollarIcon className="h-4 w-4 mr-2" />
                    {strategy.capital_required}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Strategy Details */}
        {selectedStrategy && (
          <div className="space-y-6">
            {strategies
              .filter(s => s.name === selectedStrategy)
              .map((strategy) => (
                <div key={strategy.name} className="space-y-6">
                  {/* Strategy Overview */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">{strategy.name}</h3>
                    <p className="text-gray-700 mb-4">{strategy.description}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-white rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <ClockIcon className="h-5 w-5 text-blue-600 mr-2" />
                          <h4 className="font-medium text-gray-900">Time Horizon</h4>
                        </div>
                        <p className="text-gray-700">{strategy.time_horizon}</p>
                      </div>
                      
                      <div className="bg-white rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mr-2" />
                          <h4 className="font-medium text-gray-900">Risk Level</h4>
                        </div>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${getRiskColor(strategy.risk_level)}`}>
                          {getRiskIcon(strategy.risk_level)}
                          <span className="ml-1">{strategy.risk_level}</span>
                        </span>
                      </div>
                      
                      <div className="bg-white rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <CurrencyDollarIcon className="h-5 w-5 text-green-600 mr-2" />
                          <h4 className="font-medium text-gray-900">Capital Required</h4>
                        </div>
                        <p className="text-gray-700">{strategy.capital_required}</p>
                      </div>
                    </div>
                  </div>

                  {/* Strategy Details */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Entry Criteria */}
                    <div className="bg-green-50 rounded-lg p-6">
                      <h4 className="font-semibold text-green-900 mb-4 flex items-center">
                        <CheckCircleIcon className="h-5 w-5 mr-2" />
                        Entry Criteria
                      </h4>
                      <ul className="space-y-2">
                        {strategy.strategy_details.entry_criteria.map((criteria, index) => (
                          <li key={index} className="flex items-start">
                            <CheckCircleIcon className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-green-800">{criteria}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Exit Criteria */}
                    <div className="bg-red-50 rounded-lg p-6">
                      <h4 className="font-semibold text-red-900 mb-4 flex items-center">
                        <XCircleIcon className="h-5 w-5 mr-2" />
                        Exit Criteria
                      </h4>
                      <ul className="space-y-2">
                        {strategy.strategy_details.exit_criteria.map((criteria, index) => (
                          <li key={index} className="flex items-start">
                            <XCircleIcon className="h-4 w-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-red-800">{criteria}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Risk Management */}
                    <div className="bg-yellow-50 rounded-lg p-6">
                      <h4 className="font-semibold text-yellow-900 mb-4 flex items-center">
                        <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
                        Risk Management
                      </h4>
                      <ul className="space-y-2">
                        {strategy.strategy_details.risk_management.map((risk, index) => (
                          <li key={index} className="flex items-start">
                            <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-yellow-800">{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Best Practices */}
                    <div className="bg-blue-50 rounded-lg p-6">
                      <h4 className="font-semibold text-blue-900 mb-4 flex items-center">
                        <LightBulbIcon className="h-5 w-5 mr-2" />
                        Best Practices
                      </h4>
                      <ul className="space-y-2">
                        {strategy.strategy_details.best_practices.map((practice, index) => (
                          <li key={index} className="flex items-start">
                            <LightBulbIcon className="h-4 w-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-blue-800">{practice}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Example Scenario */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Example Scenario</h4>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h5 className="font-medium text-gray-900 mb-3">Trade Details</h5>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Stock:</span>
                            <span className="font-medium">{strategy.example_scenario.stock}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Entry Price:</span>
                            <span className="font-mono">₹{strategy.example_scenario.entry_price}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Stop Loss:</span>
                            <span className="font-mono text-red-600">₹{strategy.example_scenario.stop_loss}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Target:</span>
                            <span className="font-mono text-green-600">₹{strategy.example_scenario.target}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Quantity:</span>
                            <span className="font-medium">{strategy.example_scenario.quantity}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-gray-900 mb-3">Risk & Reward</h5>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Risk Amount:</span>
                            <span className="font-medium text-red-600">{strategy.example_scenario.risk}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Potential Profit:</span>
                            <span className="font-medium text-green-600">{strategy.example_scenario.potential_profit}</span>
                          </div>
                        </div>
                        
                        <div className="mt-4">
                          <h5 className="font-medium text-gray-900 mb-2">Reasoning</h5>
                          <p className="text-sm text-gray-700">{strategy.example_scenario.reasoning}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-4">
                    <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center">
                      <PlayIcon className="h-5 w-5 mr-2" />
                      Practice This Strategy
                    </button>
                    <button className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center">
                      <InformationCircleIcon className="h-5 w-5 mr-2" />
                      Learn More
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}

        {/* No Strategy Selected */}
        {!selectedStrategy && (
          <div className="text-center py-12">
            <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Trading Strategy</h3>
            <p className="text-gray-600">Choose a strategy above to learn about its details, risks, and best practices.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingStrategies;
