import React from 'react';
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

interface PredictionData {
  signal: string;
  confidence: number;
  price_target?: number;
  current_price?: number;
  direction?: string;
  technical_analysis?: string;
  reasoning?: string;
  risk_level?: string;
  support_levels?: number[];
  resistance_levels?: number[];
  nearest_support?: number;
  nearest_resistance?: number;
  volatility?: number;
  volatility_trend?: string;
}

interface PredictionDisplayProps {
  symbol: string;
  predictionType: string;
  data: PredictionData;
  className?: string;
}

const PredictionDisplay: React.FC<PredictionDisplayProps> = ({
  symbol,
  predictionType,
  data,
  className = ''
}) => {
  const getSignalColor = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BUY':
      case 'STRONG_BUY':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'SELL':
      case 'STRONG_SELL':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'HOLD':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BUY':
      case 'STRONG_BUY':
        return <ArrowTrendingUpIcon className="w-5 h-5 text-green-600" />;
      case 'SELL':
      case 'STRONG_SELL':
        return <ArrowTrendingDownIcon className="w-5 h-5 text-red-600" />;
      case 'HOLD':
        return <CheckCircleIcon className="w-5 h-5 text-yellow-600" />;
      default:
        return <ChartBarIcon className="w-5 h-5 text-gray-600" />;
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <ChartBarIcon className="w-6 h-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            {symbol} Prediction
          </h3>
        </div>
        <div className="text-sm text-gray-500 capitalize">
          {predictionType.replace('_', ' ')}
        </div>
      </div>

      {/* Signal Display */}
      <div className="mb-4">
        <div className={`inline-flex items-center space-x-2 px-3 py-2 rounded-lg border ${getSignalColor(data.signal)}`}>
          {getSignalIcon(data.signal)}
          <span className="font-semibold">{data.signal}</span>
          <span className="text-sm opacity-75">
            {Math.round(data.confidence * 100)}% confidence
          </span>
        </div>
      </div>

      {/* Trading Signal Analysis */}
      {predictionType === 'trading_signal' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center space-x-3">
            {getSignalIcon(data.signal || '')}
            <div>
              <p className="text-sm text-muted-foreground">Trading Signal</p>
              <p className={`text-lg font-bold ${data.signal === 'BUY' ? 'text-green-600' : data.signal === 'SELL' ? 'text-red-600' : 'text-yellow-600'}`}>
                {data.signal}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 font-bold text-sm">{(data.confidence * 100).toFixed(0)}%</span>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Confidence</p>
              <p className={`text-lg font-bold ${data.confidence > 0.7 ? 'text-green-600' : data.confidence > 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                {(data.confidence * 100).toFixed(1)}%
              </p>
            </div>
          </div>
          <div className="md:col-span-2">
            <h4 className="font-semibold text-foreground mt-4 mb-2 flex items-center space-x-2">
              <LightBulbIcon className="h-5 w-5 text-yellow-500" />
              <span>Analysis</span>
            </h4>
            <p className="text-sm text-muted-foreground">{data.reasoning || data.technical_analysis}</p>
          </div>
        </div>
      )}

      {/* Price Information */}
      {data.price_target && data.current_price && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Current Price</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(data.current_price)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Target Price</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(data.price_target)}
              </p>
            </div>
          </div>
          {data.direction && (
            <div className="mt-2 text-center">
              <span className={`text-sm font-medium ${
                data.direction === 'UP' ? 'text-green-600' : 'text-red-600'
              }`}>
                {data.direction} {formatPercentage((data.price_target - data.current_price) / data.current_price * 100)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Technical Analysis */}
      {data.technical_analysis && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Technical Analysis</h4>
          <p className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
            {data.technical_analysis}
          </p>
        </div>
      )}

      {/* Risk Level */}
      {data.risk_level && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Risk Assessment</h4>
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="w-4 h-4 text-gray-500" />
            <span className={`text-sm font-medium ${getRiskColor(data.risk_level)}`}>
              {data.risk_level} Risk
            </span>
          </div>
        </div>
      )}

      {/* Support and Resistance Levels */}
      {(data.support_levels || data.resistance_levels) && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Key Levels</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.support_levels && data.support_levels.length > 0 && (
              <div>
                <p className="text-xs text-gray-600 mb-2">Support Levels</p>
                <div className="space-y-1">
                  {data.support_levels.map((level, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <span className="text-green-600">S{index + 1}</span>
                      <span className="font-medium">{formatCurrency(level)}</span>
                    </div>
                  ))}
                </div>
                {data.nearest_support && (
                  <div className="mt-2 p-2 bg-green-50 rounded text-xs">
                    <span className="text-green-700 font-medium">
                      Nearest: {formatCurrency(data.nearest_support)}
                    </span>
                  </div>
                )}
              </div>
            )}
            
            {data.resistance_levels && data.resistance_levels.length > 0 && (
              <div>
                <p className="text-xs text-gray-600 mb-2">Resistance Levels</p>
                <div className="space-y-1">
                  {data.resistance_levels.map((level, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <span className="text-red-600">R{index + 1}</span>
                      <span className="font-medium">{formatCurrency(level)}</span>
                    </div>
                  ))}
                </div>
                {data.nearest_resistance && (
                  <div className="mt-2 p-2 bg-red-50 rounded text-xs">
                    <span className="text-red-700 font-medium">
                      Nearest: {formatCurrency(data.nearest_resistance)}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Volatility Information */}
      {data.volatility && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Volatility Analysis</h4>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Predicted Volatility</span>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">
                {formatPercentage(data.volatility * 100)}
              </span>
              {data.volatility_trend && (
                <span className={`text-xs ${
                  data.volatility_trend === 'increasing' ? 'text-red-600' : 'text-green-600'
                }`}>
                  {data.volatility_trend}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start space-x-2">
          <ExclamationTriangleIcon className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-yellow-800">
            <strong>Disclaimer:</strong> This prediction is for educational purposes only. 
            Past performance does not guarantee future results. Please do your own research 
            and consider your risk tolerance before making investment decisions.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PredictionDisplay;
