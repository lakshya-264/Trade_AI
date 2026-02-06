import React, { useState } from 'react';
import { 
  AcademicCapIcon,
  BookOpenIcon,
  ChartBarIcon,
  LightBulbIcon,
  TrophyIcon,
  PlayIcon,
  UserGroupIcon,
  CalculatorIcon
} from '@heroicons/react/24/outline';
import LearningDashboard from '../components/education/LearningDashboard';
import TradingStrategies from '../components/education/TradingStrategies';
import TradingExplanation from '../components/education/TradingExplanation';
import ArpitEducation from '../components/education/ArpitEducation';
import ArpitLessonViewer from '../components/education/ArpitLessonViewer';
import ArpitTools from '../components/education/ArpitTools';
import TechnicalIndicatorsGuide from '../components/education/TechnicalIndicatorsGuide';
import ComprehensiveEducation from '../components/education/ComprehensiveEducation';
import ComprehensiveLessonViewer from '../components/education/ComprehensiveLessonViewer';
import MarketEducation from './MarketEducation';

const Education: React.FC = () => {
  const [activeTab, setActiveTab] = useState('market-education');
  const [selectedLesson, setSelectedLesson] = useState<string | null>(null);
  const [showTools, setShowTools] = useState(false);
  const [showIndicatorsGuide, setShowIndicatorsGuide] = useState(false);

  const tabs = [
    { 
      id: 'market-education', 
      label: 'Market Education', 
      icon: BookOpenIcon,
      description: 'IPO, CPR, Regulators, Corporate Actions & more'
    },
    { 
      id: 'comprehensive', 
      label: 'Comprehensive Education', 
      icon: BookOpenIcon,
      description: 'Professional-grade stock market education'
    },
    { 
      id: 'learning', 
      label: 'Learning Path', 
      icon: AcademicCapIcon,
      description: 'Structured learning modules'
    },
    { 
      id: 'arpit', 
      label: 'Arpit Principles', 
      icon: UserGroupIcon,
      description: 'Value Investing Education'
    },
    { 
      id: 'strategies', 
      label: 'Trading Strategies', 
      icon: ChartBarIcon,
      description: 'Different trading approaches'
    },
    { 
      id: 'explanation', 
      label: 'Signal Explanation', 
      icon: LightBulbIcon,
      description: 'Understand trading signals'
    },
    { 
      id: 'quiz', 
      label: 'Quiz & Tests', 
      icon: TrophyIcon,
      description: 'Test your knowledge'
    }
  ];

  // Sample data for demonstration
  const sampleExplanationData = {
    symbol: 'RELIANCE',
    signal: 'BUY',
    confidence: 0.75,
    technicalAnalysis: {
      rsi: {
        value: 45.2,
        signal: 'Neutral',
        explanation: 'RSI at 45.2 indicates the stock is in neutral zone, not overbought or oversold.',
        action: 'Look for other signals',
        confidence: 0.6
      },
      macd: {
        macd: 2.5,
        signal_line: 1.8,
        signal: 'Bullish',
        explanation: 'MACD line is above signal line, indicating bullish momentum.',
        action: 'Consider buying',
        confidence: 0.7
      },
      moving_averages: {
        sma_20: 2450,
        sma_50: 2400,
        current_price: 2475,
        signal: 'Strong Uptrend',
        explanation: 'Price is above both moving averages in ascending order, indicating strong uptrend.',
        action: 'Consider buying on pullbacks',
        confidence: 0.8
      }
    },
    riskAssessment: {
      risk_level: 'Medium',
      risk_score: 0.4,
      risk_color: 'yellow',
      risk_factors: [
        'Medium volatility - moderate price movements expected',
        'Strong trend - momentum may continue'
      ],
      recommendations: [
        'Use standard position sizing',
        'Set stop-loss at 2% below entry',
        'Monitor closely for trend changes'
      ]
    },
    timeHorizon: {
      time_horizon: 'Medium-term (1-4 weeks)',
      reasoning: [
        'Strong trend suggests longer holding period',
        'Technical indicators support medium-term view'
      ],
      recommended_strategies: ['Swing Trading']
    },
    entryExitStrategy: {
      action: 'BUY',
      entry_price: 2475,
      stop_loss: 2400,
      target: 2625,
      risk_reward_ratio: '1:2',
      position_sizing: {
        quantity: 20,
        position_value: 49500,
        risk_amount: 1500,
        risk_percentage: 1.5
      },
      entry_reasoning: 'Technical indicators suggest bullish momentum with strong trend',
      exit_reasoning: 'Take profit at target or stop-loss if trend reverses'
    },
    educationalContent: {
      key_concepts: [
        {
          concept: 'RSI (Relative Strength Index)',
          explanation: 'RSI measures momentum and identifies overbought/oversold conditions',
          learning_url: '/learn/technical-analysis/rsi'
        },
        {
          concept: 'MACD (Moving Average Convergence Divergence)',
          explanation: 'MACD shows relationship between two moving averages and momentum',
          learning_url: '/learn/technical-analysis/macd'
        }
      ],
      learning_resources: [
        {
          title: 'Technical Analysis Basics',
          type: 'Video Tutorial',
          duration: '15 minutes',
          url: '/learn/technical-analysis/basics'
        },
        {
          title: 'Risk Management Strategies',
          type: 'Interactive Guide',
          duration: '20 minutes',
          url: '/learn/risk-management/strategies'
        }
      ],
      practical_tips: [
        'Always use stop-loss orders to limit risk',
        'Never risk more than 1-2% of your capital per trade',
        'Keep a trading journal to track your decisions'
      ],
      common_mistakes: [
        'Not using stop-loss orders',
        'Risking too much capital on single trade',
        'Trading based on emotions rather than analysis'
      ]
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center">
              <AcademicCapIcon className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Education Center</h1>
                <p className="text-gray-600 mt-1">Master stock market trading with AI-powered learning</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
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
                  <Icon className="h-5 w-5 mr-2" />
                  <div className="text-left">
                    <div>{tab.label}</div>
                    <div className="text-xs text-gray-400">{tab.description}</div>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Market Education Tab */}
        {activeTab === 'market-education' && (
          <MarketEducation />
        )}

        {/* Comprehensive Education Tab */}
        {activeTab === 'comprehensive' && (
          <div className="space-y-6">
            <div className="flex justify-end">
              <button
                onClick={() => setShowIndicatorsGuide(true)}
                className="px-3 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-black/80"
              >
                Open Technical Indicators Guide
              </button>
            </div>
            {selectedLesson ? (
              <ComprehensiveLessonViewer 
                lessonId={selectedLesson} 
                onClose={() => setSelectedLesson(null)} 
              />
            ) : showTools ? (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="text-center py-12">
                  <CalculatorIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Interactive Tools</h3>
                  <p className="text-gray-600 mb-6">
                    Professional-grade calculators and analysis tools coming soon.
                  </p>
                  <button
                    onClick={() => setShowTools(false)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                  >
                    Back to Education
                  </button>
                </div>
              </div>
            ) : (
              <ComprehensiveEducation 
                onLessonSelect={setSelectedLesson}
                onShowTools={() => setShowTools(true)}
              />
            )}
          </div>
        )}
        <TechnicalIndicatorsGuide isOpen={showIndicatorsGuide} onClose={() => setShowIndicatorsGuide(false)} />

        {/* Learning Path Tab */}
        {activeTab === 'learning' && (
          <LearningDashboard />
        )}

        {/* Arpit Education Tab */}
        {activeTab === 'arpit' && (
          <div className="space-y-6">
            {selectedLesson ? (
              <ArpitLessonViewer 
                lessonId={selectedLesson} 
                onClose={() => setSelectedLesson(null)} 
              />
            ) : showTools ? (
              <ArpitTools onClose={() => setShowTools(false)} />
            ) : (
              <ArpitEducation 
                onLessonSelect={setSelectedLesson}
                onShowTools={() => setShowTools(true)}
              />
            )}
          </div>
        )}

        {/* Trading Strategies Tab */}
        {activeTab === 'strategies' && (
          <TradingStrategies />
        )}

        {/* Signal Explanation Tab */}
        {activeTab === 'explanation' && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <LightBulbIcon className="h-5 w-5 text-blue-600 mr-2" />
                <h3 className="font-medium text-blue-900">Interactive Signal Explanation</h3>
              </div>
              <p className="text-blue-800 text-sm mt-1">
                This section shows detailed explanations of trading signals. In the actual application, 
                this would be populated with real signal data from your AI analysis.
              </p>
            </div>
            
            <TradingExplanation {...sampleExplanationData} />
          </div>
        )}

        {/* Quiz Tab */}
        {activeTab === 'quiz' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-center py-12">
              <TrophyIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Quiz & Assessment Center</h3>
              <p className="text-gray-600 mb-6">
                Test your knowledge with interactive quizzes and assessments.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
                <div className="bg-gray-50 rounded-lg p-6">
                  <BookOpenIcon className="h-8 w-8 text-blue-600 mx-auto mb-3" />
                  <h4 className="font-medium text-gray-900 mb-2">Technical Analysis Quiz</h4>
                  <p className="text-sm text-gray-600 mb-4">Test your knowledge of technical indicators and chart patterns.</p>
                  <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Start Quiz
                  </button>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-6">
                  <ChartBarIcon className="h-8 w-8 text-green-600 mx-auto mb-3" />
                  <h4 className="font-medium text-gray-900 mb-2">Trading Strategies Quiz</h4>
                  <p className="text-sm text-gray-600 mb-4">Test your understanding of different trading approaches.</p>
                  <button className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                    Start Quiz
                  </button>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-6">
                  <LightBulbIcon className="h-8 w-8 text-purple-600 mx-auto mb-3" />
                  <h4 className="font-medium text-gray-900 mb-2">Risk Management Quiz</h4>
                  <p className="text-sm text-gray-600 mb-4">Test your knowledge of risk management principles.</p>
                  <button className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                    Start Quiz
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Education;
