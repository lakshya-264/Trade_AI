import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  CalculatorIcon, 
  ShieldCheckIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { api } from '../../services/api';

interface IntrinsicValueAnalysis {
  symbol: string;
  current_price: number;
  intrinsic_value: number;
  margin_of_safety: {
    percentage: number;
    safety_level: string;
    recommendation: string;
  };
  models: {
    graham: any;
    dcf_lite: any;
    earnings_yield: any;
    pe_mean_reversion?: any;
    pb_roe?: any;
  };
  risk_assessment: {
    risk_level: string;
    reason: string;
  };
  recommendation: {
    action: string;
    confidence: string;
    reasoning: string;
  };
}

interface DefensiveScreening {
  symbol: string;
  defensive_score: number;
  criteria_results: any;
  recommendation: {
    action: string;
    strengths: string[];
    weaknesses: string[];
  };
}

interface ComprehensiveAnalysisProps {
  symbol: string;
  onClose?: () => void;
}

const EnhancedAnalysis: React.FC<ComprehensiveAnalysisProps> = ({ symbol, onClose }) => {
  const [analysis, setAnalysis] = useState<IntrinsicValueAnalysis | null>(null);
  const [defensiveScreening, setDefensiveScreening] = useState<DefensiveScreening | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'intrinsic' | 'defensive' | 'models'>('intrinsic');

  useEffect(() => {
    if (symbol) {
      fetchComprehensiveAnalysis();
    }
  }, [symbol]);

  const fetchComprehensiveAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.getComprehensiveAnalysis(symbol);
      
      if (response.success) {
        const data = response.data;
        setAnalysis(data.intrinsic_value_analysis);
        setDefensiveScreening(data.defensive_screening);
      } else {
        setError('Failed to fetch analysis');
      }
    } catch (err) {
      setError('Error fetching analysis');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSafetyLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'very high':
        return 'text-green-600 bg-green-100';
      case 'high':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-orange-600 bg-orange-100';
      case 'negative':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getRecommendationColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'strong buy':
        return 'text-green-600 bg-green-100';
      case 'buy':
        return 'text-green-600 bg-green-100';
      case 'consider':
        return 'text-yellow-600 bg-yellow-100';
      case 'hold':
        return 'text-blue-600 bg-blue-100';
      case 'avoid':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Analysis Error</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchComprehensiveAnalysis}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry Analysis
          </button>
        </div>
      </div>
    );
  }

  if (!analysis || !defensiveScreening) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center">
          <InformationCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analysis Available</h3>
          <p className="text-gray-600">Unable to load analysis for {symbol}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Enhanced Analysis: {symbol}</h2>
            <p className="text-sm text-gray-600">Intrinsic Value & Defensive Screening</p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="px-6 py-3 border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'intrinsic', label: 'Intrinsic Value', icon: CalculatorIcon },
            { id: 'defensive', label: 'Defensive Screen', icon: ShieldCheckIcon },
            { id: 'models', label: 'Models', icon: ChartBarIcon }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'intrinsic' && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <ArrowTrendingUpIcon className="h-5 w-5 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">Current Price</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">₹{analysis.current_price}</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <CalculatorIcon className="h-5 w-5 text-green-600" />
                  <span className="text-sm font-medium text-gray-700">Intrinsic Value</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">₹{analysis.intrinsic_value}</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <ShieldCheckIcon className="h-5 w-5 text-purple-600" />
                  <span className="text-sm font-medium text-gray-700">Margin of Safety</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{analysis.margin_of_safety.percentage}%</p>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getSafetyLevelColor(analysis.margin_of_safety.safety_level)}`}>
                  {analysis.margin_of_safety.safety_level}
                </span>
              </div>
            </div>

            {/* Recommendation */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">Investment Recommendation</span>
              </div>
              <div className="flex items-center space-x-3">
                <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getRecommendationColor(analysis.recommendation.action)}`}>
                  {analysis.recommendation.action}
                </span>
                <span className="text-sm text-blue-700">Confidence: {analysis.recommendation.confidence}</span>
              </div>
              <p className="text-sm text-blue-800 mt-2">{analysis.recommendation.reasoning}</p>
            </div>

            {/* Risk Assessment */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Risk Assessment</h3>
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-sm font-medium text-gray-700">Risk Level:</span>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                  analysis.risk_assessment.risk_level === 'Low' ? 'bg-green-100 text-green-800' :
                  analysis.risk_assessment.risk_level === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {analysis.risk_assessment.risk_level}
                </span>
              </div>
              <p className="text-sm text-gray-600">{analysis.risk_assessment.reason}</p>
            </div>
          </div>
        )}

        {activeTab === 'defensive' && (
          <div className="space-y-6">
            {/* Defensive Score */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <ShieldCheckIcon className="h-5 w-5 text-green-600" />
                <span className="text-sm font-medium text-gray-700">Defensive Score</span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-3xl font-bold text-gray-900">{defensiveScreening.defensive_score}%</div>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${defensiveScreening.defensive_score}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
                <span className="text-sm font-medium text-green-900">Defensive Recommendation</span>
              </div>
              <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getRecommendationColor(defensiveScreening.recommendation.action)}`}>
                {defensiveScreening.recommendation.action}
              </span>
            </div>

            {/* Strengths and Weaknesses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-900 mb-3">Strengths</h3>
                <ul className="space-y-2">
                  {defensiveScreening.recommendation.strengths.map((strength, index) => (
                    <li key={index} className="flex items-center space-x-2 text-sm text-green-800">
                      <CheckCircleIcon className="h-4 w-4 text-green-600" />
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="bg-red-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-red-900 mb-3">Weaknesses</h3>
                <ul className="space-y-2">
                  {defensiveScreening.recommendation.weaknesses.map((weakness, index) => (
                    <li key={index} className="flex items-center space-x-2 text-sm text-red-800">
                      <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
                      <span>{weakness}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'models' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Intrinsic Value Models</h3>
            
            {/* Graham Formula */}
            {analysis.models.graham && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-md font-semibold text-gray-900 mb-2">Graham Formula</h4>
                <p className="text-sm text-gray-600 mb-2">{analysis.models.graham.formula}</p>
                <div className="text-lg font-bold text-gray-900">₹{analysis.models.graham.intrinsic_value}</div>
              </div>
            )}

            {/* DCF Lite */}
            {analysis.models.dcf_lite && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-md font-semibold text-gray-900 mb-2">DCF Lite</h4>
                <p className="text-sm text-gray-600 mb-2">{analysis.models.dcf_lite.formula}</p>
                <div className="text-lg font-bold text-gray-900">₹{analysis.models.dcf_lite.intrinsic_value}</div>
              </div>
            )}

            {/* Earnings Yield */}
            {analysis.models.earnings_yield && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-md font-semibold text-gray-900 mb-2">Earnings Yield Model</h4>
                <p className="text-sm text-gray-600 mb-2">{analysis.models.earnings_yield.formula}</p>
                <div className="text-lg font-bold text-gray-900">₹{analysis.models.earnings_yield.intrinsic_value}</div>
              </div>
            )}

            {/* P/E Mean Reversion */}
            {analysis.models.pe_mean_reversion && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-md font-semibold text-gray-900 mb-2">P/E Mean Reversion</h4>
                <p className="text-sm text-gray-600 mb-2">{analysis.models.pe_mean_reversion.formula}</p>
                <div className="text-lg font-bold text-gray-900">₹{analysis.models.pe_mean_reversion.intrinsic_value}</div>
              </div>
            )}

            {/* P/B vs ROE */}
            {analysis.models.pb_roe && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-md font-semibold text-gray-900 mb-2">P/B vs ROE Model</h4>
                <p className="text-sm text-gray-600 mb-2">{analysis.models.pb_roe.formula}</p>
                <div className="text-lg font-bold text-gray-900">₹{analysis.models.pb_roe.intrinsic_value}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedAnalysis;
