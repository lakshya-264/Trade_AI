import React, { useState } from 'react';
import { 
  InformationCircleIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ClockIcon,
  CurrencyDollarIcon,
  LightBulbIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

interface TechnicalAnalysis {
  [key: string]: {
    value?: number;
    signal: string;
    explanation: string;
    action: string;
    confidence: number;
  };
}

interface RiskAssessment {
  risk_level: string;
  risk_score: number;
  risk_color: string;
  risk_factors: string[];
  recommendations: string[];
}

interface EntryExitStrategy {
  action: string;
  entry_price: number;
  stop_loss: number;
  target: number;
  risk_reward_ratio: string;
  position_sizing?: {
    quantity: number;
    position_value: number;
    risk_amount: number;
    risk_percentage: number;
  };
  entry_reasoning: string;
  exit_reasoning: string;
}

interface EducationalContent {
  key_concepts: Array<{
    concept: string;
    explanation: string;
    learning_url: string;
  }>;
  learning_resources: Array<{
    title: string;
    type: string;
    duration: string;
    url: string;
  }>;
  practical_tips: string[];
  common_mistakes: string[];
}

interface TradingExplanationProps {
  symbol: string;
  signal: string;
  confidence: number;
  technicalAnalysis: TechnicalAnalysis;
  riskAssessment: RiskAssessment;
  timeHorizon: {
    time_horizon: string;
    reasoning: string[];
    recommended_strategies: string[];
  };
  entryExitStrategy: EntryExitStrategy;
  educationalContent: EducationalContent;
  className?: string;
}

const TradingExplanation: React.FC<TradingExplanationProps> = ({
  symbol,
  signal,
  confidence,
  technicalAnalysis,
  riskAssessment,
  timeHorizon,
  entryExitStrategy,
  educationalContent,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState('technical');

  const getSignalColor = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BUY': return 'text-green-600 bg-green-100';
      case 'SELL': return 'text-red-600 bg-red-100';
      case 'HOLD': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BUY': return <CheckCircleIcon className="h-5 w-5" />;
      case 'SELL': return <XCircleIcon className="h-5 w-5" />;
      case 'HOLD': return <ExclamationTriangleIcon className="h-5 w-5" />;
      default: return <InformationCircleIcon className="h-5 w-5" />;
    }
  };

  const tabs = [
    { id: 'technical', label: 'Technical Analysis', icon: ChartBarIcon },
    { id: 'risk', label: 'Risk Assessment', icon: ExclamationTriangleIcon },
    { id: 'strategy', label: 'Trading Strategy', icon: CurrencyDollarIcon },
    { id: 'education', label: 'Learn More', icon: LightBulbIcon }
  ];

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Trading Analysis: {symbol}
            </h2>
            <p className="text-gray-600 mt-1">Detailed explanation of the trading decision</p>
          </div>
          
          <div className="text-right">
            <div className={`inline-flex items-center px-4 py-2 rounded-lg font-semibold ${getSignalColor(signal)}`}>
              {getSignalIcon(signal)}
              <span className="ml-2">{signal}</span>
            </div>
            <div className="mt-2">
              <span className="text-sm text-gray-600">Confidence: </span>
              <span className="font-semibold text-gray-900">{(confidence * 100).toFixed(1)}%</span>
            </div>
          </div>
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
        {/* Technical Analysis Tab */}
        {activeTab === 'technical' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Why {signal} {symbol}?
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(technicalAnalysis).map(([indicator, data]) => (
                  <div key={indicator} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{indicator.toUpperCase()}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        data.confidence > 0.7 ? 'bg-green-100 text-green-800' :
                        data.confidence > 0.4 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {(data.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    
                    {data.value && (
                      <div className="text-sm text-gray-600 mb-2">
                        Value: <span className="font-mono">{data.value.toFixed(2)}</span>
                      </div>
                    )}
                    
                    <div className="text-sm text-gray-700 mb-2">
                      <span className="font-medium">Signal:</span> {data.signal}
                    </div>
                    
                    <div className="text-sm text-gray-700 mb-2">
                      {data.explanation}
                    </div>
                    
                    <div className="text-sm text-blue-600 font-medium">
                      {data.action}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Risk Assessment Tab */}
        {activeTab === 'risk' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment</h3>
              
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-medium text-gray-900">Overall Risk Level</h4>
                  <span className={`px-4 py-2 rounded-lg font-semibold ${
                    riskAssessment.risk_level === 'Low' ? 'bg-green-100 text-green-800' :
                    riskAssessment.risk_level === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {riskAssessment.risk_level} Risk
                  </span>
                </div>
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Risk Score</span>
                    <span>{(riskAssessment.risk_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        riskAssessment.risk_level === 'Low' ? 'bg-green-500' :
                        riskAssessment.risk_level === 'Medium' ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${riskAssessment.risk_score * 100}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="mb-4">
                  <h5 className="font-medium text-gray-900 mb-2">Risk Factors:</h5>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                    {riskAssessment.risk_factors.map((factor, index) => (
                      <li key={index}>{factor}</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Recommendations:</h5>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                    {riskAssessment.recommendations.map((recommendation, index) => (
                      <li key={index}>{recommendation}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Trading Strategy Tab */}
        {activeTab === 'strategy' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trading Strategy</h3>
              
              {/* Time Horizon */}
              <div className="bg-blue-50 rounded-lg p-4 mb-6">
                <div className="flex items-center mb-2">
                  <ClockIcon className="h-5 w-5 text-blue-600 mr-2" />
                  <h4 className="font-medium text-gray-900">Recommended Time Horizon</h4>
                </div>
                <p className="text-blue-800 font-medium">{timeHorizon.time_horizon}</p>
                <div className="mt-2">
                  <h5 className="text-sm font-medium text-gray-700 mb-1">Reasoning:</h5>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                    {timeHorizon.reasoning.map((reason, index) => (
                      <li key={index}>{reason}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Entry/Exit Strategy */}
              {entryExitStrategy.action !== 'HOLD' && (
                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-4">Entry & Exit Strategy</h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h5 className="font-medium text-gray-900 mb-3">Price Levels</h5>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Entry Price:</span>
                          <span className="font-mono font-medium">₹{entryExitStrategy.entry_price.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Stop Loss:</span>
                          <span className="font-mono font-medium text-red-600">₹{entryExitStrategy.stop_loss.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Target:</span>
                          <span className="font-mono font-medium text-green-600">₹{entryExitStrategy.target.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Risk-Reward:</span>
                          <span className="font-medium">{entryExitStrategy.risk_reward_ratio}</span>
                        </div>
                      </div>
                    </div>
                    
                    {entryExitStrategy.position_sizing && (
                      <div>
                        <h5 className="font-medium text-gray-900 mb-3">Position Sizing</h5>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Quantity:</span>
                            <span className="font-medium">{entryExitStrategy.position_sizing.quantity}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Position Value:</span>
                            <span className="font-mono">₹{entryExitStrategy.position_sizing.position_value.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Risk Amount:</span>
                            <span className="font-mono text-red-600">₹{entryExitStrategy.position_sizing.risk_amount.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Risk %:</span>
                            <span className="font-medium">{entryExitStrategy.position_sizing.risk_percentage}%</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <h5 className="font-medium text-gray-900 mb-2">Strategy Reasoning</h5>
                    <p className="text-sm text-gray-700 mb-2">{entryExitStrategy.entry_reasoning}</p>
                    <p className="text-sm text-gray-700">{entryExitStrategy.exit_reasoning}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Education Tab */}
        {activeTab === 'education' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Learn More</h3>
              
              {/* Key Concepts */}
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">Key Concepts to Learn</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {educationalContent.key_concepts.map((concept, index) => (
                    <div key={index} className="bg-blue-50 rounded-lg p-4">
                      <h5 className="font-medium text-blue-900 mb-1">{concept.concept}</h5>
                      <p className="text-sm text-blue-800 mb-2">{concept.explanation}</p>
                      <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                        Learn More →
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Learning Resources */}
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">Learning Resources</h4>
                <div className="space-y-3">
                  {educationalContent.learning_resources.map((resource, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h5 className="font-medium text-gray-900">{resource.title}</h5>
                          <p className="text-sm text-gray-600">{resource.type} • {resource.duration}</p>
                        </div>
                        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
                          Start Learning
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Practical Tips */}
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">Practical Trading Tips</h4>
                <div className="bg-green-50 rounded-lg p-4">
                  <ul className="space-y-2">
                    {educationalContent.practical_tips.map((tip, index) => (
                      <li key={index} className="flex items-start">
                        <CheckCircleIcon className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-green-800">{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Common Mistakes */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Common Mistakes to Avoid</h4>
                <div className="bg-red-50 rounded-lg p-4">
                  <ul className="space-y-2">
                    {educationalContent.common_mistakes.map((mistake, index) => (
                      <li key={index} className="flex items-start">
                        <XCircleIcon className="h-4 w-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-red-800">{mistake}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingExplanation;
