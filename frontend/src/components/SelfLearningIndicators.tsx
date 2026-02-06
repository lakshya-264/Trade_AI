/**
 * Self-Learning Indicators Component
 * Shows how the system learns from user experience and market status
 */

import React, { useState, useEffect } from 'react';
import {
  AcademicCapIcon,
  ChartBarIcon,
  UserIcon,
  ArrowTrendingUpIcon,
  LightBulbIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { userLearningApi } from '../services/userLearningApi';

interface SelfLearningIndicatorsProps {
  symbol?: string;
  userId?: number;
}

interface LearningStats {
  totalFeedback: number;
  positiveFeedback: number;
  behaviorActions: number;
  modelImprovements: number;
  lastLearningUpdate?: string;
}

const SelfLearningIndicators: React.FC<SelfLearningIndicatorsProps> = ({ 
  symbol,
  userId 
}) => {
  const [stats, setStats] = useState<LearningStats>({
    totalFeedback: 0,
    positiveFeedback: 0,
    behaviorActions: 0,
    modelImprovements: 0
  });
  const [loading, setLoading] = useState(true);
  const [marketStatus, setMarketStatus] = useState<'BULL' | 'BEAR' | 'NEUTRAL'>('NEUTRAL');

  useEffect(() => {
    fetchLearningStats();
    fetchMarketStatus();
    
    // Refresh every 5 minutes
    const interval = setInterval(() => {
      fetchLearningStats();
      fetchMarketStatus();
    }, 300000);
    
    return () => clearInterval(interval);
  }, [symbol, userId]);

  const fetchLearningStats = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      // Fetch user feedback stats
      const feedbackStats = await userLearningApi.getFeedbackStats(30);
      
      // Fetch behavior tracking stats
      const behaviorInsights = await userLearningApi.getBehaviorInsights(30);
      
      setStats({
        totalFeedback: feedbackStats.total_feedback || 0,
        positiveFeedback: feedbackStats.positive_feedback || 0,
        behaviorActions: behaviorInsights.total_actions || 0,
        modelImprovements: Math.floor(feedbackStats.satisfaction_rate || 0),
        lastLearningUpdate: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error fetching learning stats:', error);
      // Set default values on error
      setStats({
        totalFeedback: 0,
        positiveFeedback: 0,
        behaviorActions: 0,
        modelImprovements: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchMarketStatus = async () => {
    try {
      // Fetch market status from API
      const response = await fetch('/api/realtime/market-status');
      if (response.ok) {
        const data = await response.json();
        if (data.market_trend) {
          const trend = data.market_trend.toUpperCase();
          if (trend.includes('BULL') || trend.includes('UP')) {
            setMarketStatus('BULL');
          } else if (trend.includes('BEAR') || trend.includes('DOWN')) {
            setMarketStatus('BEAR');
          } else {
            setMarketStatus('NEUTRAL');
          }
        }
      }
    } catch (error) {
      console.error('Error fetching market status:', error);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  const feedbackRate = stats.totalFeedback > 0 
    ? ((stats.positiveFeedback / stats.totalFeedback) * 100).toFixed(0)
    : '0';

  const getMarketStatusColor = () => {
    switch (marketStatus) {
      case 'BULL':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      case 'BEAR':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      default:
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AcademicCapIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Self-Learning System
          </h3>
        </div>
        <div className={`px-3 py-1 rounded-lg border text-xs font-medium ${getMarketStatusColor()}`}>
          {marketStatus} Market
        </div>
      </div>

      {/* Learning Metrics */}
      <div className="grid grid-cols-2 gap-4">
        {/* User Feedback */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
          <div className="flex items-center space-x-2 mb-2">
            <UserIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-blue-900 dark:text-blue-200">
              User Feedback
            </span>
          </div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {stats.totalFeedback}
          </div>
          <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
            {feedbackRate}% positive
          </div>
        </div>

        {/* Behavior Tracking */}
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
          <div className="flex items-center space-x-2 mb-2">
            <ChartBarIcon className="h-4 w-4 text-green-600 dark:text-green-400" />
            <span className="text-sm font-medium text-green-900 dark:text-green-200">
              Actions Tracked
            </span>
          </div>
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {stats.behaviorActions}
          </div>
          <div className="text-xs text-green-700 dark:text-green-300 mt-1">
            Learning from behavior
          </div>
        </div>

        {/* Model Improvements */}
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
          <div className="flex items-center space-x-2 mb-2">
            <LightBulbIcon className="h-4 w-4 text-purple-600 dark:text-purple-400" />
            <span className="text-sm font-medium text-purple-900 dark:text-purple-200">
              Model Updates
            </span>
          </div>
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {stats.modelImprovements}
          </div>
          <div className="text-xs text-purple-700 dark:text-purple-300 mt-1">
            Continuous improvement
          </div>
        </div>

        {/* Market Status Learning */}
        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
          <div className="flex items-center space-x-2 mb-2">
            <ArrowTrendingUpIcon className="h-4 w-4 text-orange-600 dark:text-orange-400" />
            <span className="text-sm font-medium text-orange-900 dark:text-orange-200">
              Market Learning
            </span>
          </div>
          <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
            Active
          </div>
          <div className="text-xs text-orange-700 dark:text-orange-300 mt-1">
            Adapting to {marketStatus.toLowerCase()} market
          </div>
        </div>
      </div>

      {/* Learning Status */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
            <ClockIcon className="h-4 w-4" />
            <span>Last Learning Update</span>
          </div>
          <span className="font-medium text-gray-900 dark:text-white">
            {stats.lastLearningUpdate 
              ? new Date(stats.lastLearningUpdate).toLocaleString()
              : 'Never'
            }
          </span>
        </div>
      </div>

      {/* Info Text */}
      <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/50 rounded p-3">
        <p className="font-medium mb-1">How it works:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Learns from your feedback on predictions</li>
          <li>Tracks your trading behavior and preferences</li>
          <li>Adapts to current market conditions</li>
          <li>Continuously improves model accuracy</li>
        </ul>
      </div>
    </div>
  );
};

export default SelfLearningIndicators;

