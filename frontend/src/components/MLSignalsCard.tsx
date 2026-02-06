/**
 * ML Signals Card Component
 * Displays machine learning buy/sell signals with confidence scores
 */

import React from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  CpuChipIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface MLSignalsCardProps {
  mlSignals: {
    signal?: string;
    confidence?: number;
    buy_probability?: number;
    sell_probability?: number;
    hold_probability?: number;
    price_target?: number;
    stop_loss?: number;
    prediction?: string;
  } | null;
  loading?: boolean;
}

const MLSignalsCard: React.FC<MLSignalsCardProps> = ({ mlSignals, loading }) => {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (!mlSignals) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <p className="text-gray-500 dark:text-gray-400 text-sm">No ML signals available</p>
      </div>
    );
  }

  // Determine primary signal
  const signal = mlSignals.signal || mlSignals.prediction || 'HOLD';
  const confidence = mlSignals.confidence || 0;
  
  // Get probabilities
  const buyProb = mlSignals.buy_probability || 0;
  const sellProb = mlSignals.sell_probability || 0;
  const holdProb = mlSignals.hold_probability || 0;

  // Determine signal color and icon
  const getSignalStyle = (sig: string) => {
    const upperSig = sig.toUpperCase();
    if (upperSig.includes('BUY')) {
      return {
        color: 'text-green-600 dark:text-green-400',
        bgColor: 'bg-green-50 dark:bg-green-900/20',
        borderColor: 'border-green-200 dark:border-green-800',
        icon: ArrowTrendingUpIcon,
        label: 'BUY'
      };
    } else if (upperSig.includes('SELL')) {
      return {
        color: 'text-red-600 dark:text-red-400',
        bgColor: 'bg-red-50 dark:bg-red-900/20',
        borderColor: 'border-red-200 dark:border-red-800',
        icon: ArrowTrendingDownIcon,
        label: 'SELL'
      };
    } else {
      return {
        color: 'text-yellow-600 dark:text-yellow-400',
        bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
        borderColor: 'border-yellow-200 dark:border-yellow-800',
        icon: MinusIcon,
        label: 'HOLD'
      };
    }
  };

  const signalStyle = getSignalStyle(signal);
  const SignalIcon = signalStyle.icon;

  // Confidence level
  const getConfidenceLevel = (conf: number) => {
    if (conf >= 80) return { label: 'Very High', color: 'text-green-600 dark:text-green-400' };
    if (conf >= 60) return { label: 'High', color: 'text-blue-600 dark:text-blue-400' };
    if (conf >= 40) return { label: 'Medium', color: 'text-yellow-600 dark:text-yellow-400' };
    return { label: 'Low', color: 'text-gray-600 dark:text-gray-400' };
  };

  const confidenceLevel = getConfidenceLevel(confidence);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <CpuChipIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Machine Learning Signal
          </h3>
        </div>
        <span className={`text-xs font-medium px-2 py-1 rounded ${confidenceLevel.color} bg-opacity-10`}>
          {confidenceLevel.label} Confidence
        </span>
      </div>

      {/* Primary Signal */}
      <div className={`border-2 ${signalStyle.borderColor} ${signalStyle.bgColor} rounded-lg p-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <SignalIcon className={`h-8 w-8 ${signalStyle.color}`} />
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">ML Prediction</div>
              <div className={`text-2xl font-bold ${signalStyle.color}`}>
                {signalStyle.label}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600 dark:text-gray-400">Confidence</div>
            <div className={`text-2xl font-bold ${signalStyle.color}`}>
              {confidence.toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* Probability Breakdown */}
      <div className="space-y-2">
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300">Signal Probabilities</div>
        
        {/* Buy Probability */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
            <span className="flex items-center space-x-1">
              <ArrowTrendingUpIcon className="h-3 w-3 text-green-600" />
              <span>BUY</span>
            </span>
            <span className="font-medium">{(buyProb * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${buyProb * 100}%` }}
            />
          </div>
        </div>

        {/* Hold Probability */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
            <span className="flex items-center space-x-1">
              <MinusIcon className="h-3 w-3 text-yellow-600" />
              <span>HOLD</span>
            </span>
            <span className="font-medium">{(holdProb * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-yellow-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${holdProb * 100}%` }}
            />
          </div>
        </div>

        {/* Sell Probability */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
            <span className="flex items-center space-x-1">
              <ArrowTrendingDownIcon className="h-3 w-3 text-red-600" />
              <span>SELL</span>
            </span>
            <span className="font-medium">{(sellProb * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-red-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${sellProb * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Price Targets */}
      {(mlSignals.price_target || mlSignals.stop_loss) && (
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
          {mlSignals.price_target && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Price Target</span>
              <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                ₹{mlSignals.price_target.toFixed(2)}
              </span>
            </div>
          )}
          {mlSignals.stop_loss && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Stop Loss</span>
              <span className="text-sm font-semibold text-red-600 dark:text-red-400">
                ₹{mlSignals.stop_loss.toFixed(2)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MLSignalsCard;

