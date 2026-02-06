import React from 'react';

interface DataIndicatorProps {
  dataType: string;
  dataStatus: string;
  frontendIndicator: string;
  frontendMessage: string;
  frontendColor: string;
  frontendBgColor: string;
  frontendBorder: string;
  reliabilityScore: number;
  dataFreshness: string;
  cacheAgeSeconds?: number;
  fallbackReason?: string;
  errorMessage?: string;
  className?: string;
}

const DataIndicator: React.FC<DataIndicatorProps> = ({
  dataType,
  dataStatus,
  frontendIndicator,
  frontendMessage,
  frontendColor,
  frontendBgColor,
  frontendBorder,
  reliabilityScore,
  dataFreshness,
  cacheAgeSeconds,
  fallbackReason,
  errorMessage,
  className = ""
}) => {
  const getIndicatorIcon = () => {
    switch (dataType) {
      case 'live_data':
        return '🟢';
      case 'cached_data':
        return '🟡';
      case 'estimated_data':
        return '🟠';
      case 'mock_data':
        return '🔴';
      case 'error_data':
        return '⚫';
      default:
        return '❓';
    }
  };

  const getStatusText = () => {
    switch (dataStatus) {
      case 'real_time':
        return 'LIVE';
      case 'near_real_time':
        return 'CACHED';
      case 'estimated':
        return 'ESTIMATED';
      case 'simulated':
        return 'MOCK';
      case 'error':
        return 'ERROR';
      default:
        return 'UNKNOWN';
    }
  };

  return (
    <div 
      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${className}`}
      style={{
        color: frontendColor,
        backgroundColor: frontendBgColor,
        border: frontendBorder
      }}
      title={frontendMessage}
    >
      <span className="mr-1">{getIndicatorIcon()}</span>
      <span className="font-semibold">{getStatusText()}</span>
      
      {/* Additional info based on data type */}
      {dataType === 'cached_data' && cacheAgeSeconds && (
        <span className="ml-1 text-xs opacity-75">
          ({Math.floor(cacheAgeSeconds / 60)}m ago)
        </span>
      )}
      
      {dataType === 'mock_data' && fallbackReason && (
        <span className="ml-1 text-xs opacity-75">
          (Fallback)
        </span>
      )}
      
      {dataType === 'error_data' && errorMessage && (
        <span className="ml-1 text-xs opacity-75">
          (Error)
        </span>
      )}
    </div>
  );
};

// Enhanced price display component with data indicators
interface PriceDisplayProps {
  symbol: string;
  lastPrice: number;
  change: number;
  changePercent: number;
  formattedPrice: string;
  formattedChange: string;
  formattedChangePercent: string;
  dataType: string;
  dataStatus: string;
  frontendIndicator: string;
  frontendMessage: string;
  frontendColor: string;
  frontendBgColor: string;
  frontendBorder: string;
  reliabilityScore: number;
  dataFreshness: string;
  cacheAgeSeconds?: number;
  fallbackReason?: string;
  errorMessage?: string;
  className?: string;
}

export const PriceDisplayWithIndicator: React.FC<PriceDisplayProps> = ({
  symbol,
  lastPrice,
  change,
  changePercent,
  formattedPrice,
  formattedChange,
  formattedChangePercent,
  dataType,
  dataStatus,
  frontendIndicator,
  frontendMessage,
  frontendColor,
  frontendBgColor,
  frontendBorder,
  reliabilityScore,
  dataFreshness,
  cacheAgeSeconds,
  fallbackReason,
  errorMessage,
  className = ""
}) => {
  const isPositive = change >= 0;
  const isNegative = change < 0;

  return (
    <div className={`p-4 rounded-lg border ${className}`}>
      {/* Header with symbol and data indicator */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
        <DataIndicator
          dataType={dataType}
          dataStatus={dataStatus}
          frontendIndicator={frontendIndicator}
          frontendMessage={frontendMessage}
          frontendColor={frontendColor}
          frontendBgColor={frontendBgColor}
          frontendBorder={frontendBorder}
          reliabilityScore={reliabilityScore}
          dataFreshness={dataFreshness}
          cacheAgeSeconds={cacheAgeSeconds}
          fallbackReason={fallbackReason}
          errorMessage={errorMessage}
        />
      </div>

      {/* Price display */}
      <div className="space-y-2">
        <div className="text-2xl font-bold text-gray-900">
          {formattedPrice}
        </div>
        
        <div className={`flex items-center space-x-2 ${
          isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'
        }`}>
          <span className="text-sm font-medium">
            {formattedChange}
          </span>
          <span className="text-sm font-medium">
            ({formattedChangePercent})
          </span>
        </div>

        {/* Data freshness indicator */}
        <div className="text-xs text-gray-500">
          {dataFreshness === 'Real-time' && '🟢 Live market data'}
          {dataFreshness === 'Estimated' && '🟠 Estimated from market patterns'}
          {dataFreshness === 'Simulated' && '🔴 Simulated data'}
          {dataFreshness === 'Error' && '⚫ Data unavailable'}
          {dataFreshness.includes('s old') && `🟡 Cached data (${dataFreshness})`}
        </div>

        {/* Reliability score */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">Reliability:</span>
          <div className="flex-1 bg-gray-200 rounded-full h-1.5">
            <div 
              className="h-1.5 rounded-full transition-all duration-300"
              style={{
                width: `${reliabilityScore}%`,
                backgroundColor: reliabilityScore >= 90 ? '#10B981' : 
                                reliabilityScore >= 70 ? '#F59E0B' : 
                                reliabilityScore >= 50 ? '#F97316' : '#EF4444'
              }}
            />
          </div>
          <span className="text-xs text-gray-500">{reliabilityScore}%</span>
        </div>
      </div>
    </div>
  );
};

// Portfolio item component with data indicators
interface PortfolioItemWithIndicatorProps {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  totalValue: number;
  formattedCurrentPrice: string;
  formattedPnL: string;
  formattedTotalValue: string;
  dataType: string;
  dataStatus: string;
  frontendIndicator: string;
  frontendMessage: string;
  frontendColor: string;
  frontendBgColor: string;
  frontendBorder: string;
  reliabilityScore: number;
  dataFreshness: string;
  cacheAgeSeconds?: number;
  fallbackReason?: string;
  errorMessage?: string;
}

export const PortfolioItemWithIndicator: React.FC<PortfolioItemWithIndicatorProps> = ({
  symbol,
  quantity,
  averagePrice,
  currentPrice,
  pnl,
  pnlPercent,
  totalValue,
  formattedCurrentPrice,
  formattedPnL,
  formattedTotalValue,
  dataType,
  dataStatus,
  frontendIndicator,
  frontendMessage,
  frontendColor,
  frontendBgColor,
  frontendBorder,
  reliabilityScore,
  dataFreshness,
  cacheAgeSeconds,
  fallbackReason,
  errorMessage
}) => {
  const isProfit = pnl >= 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header with symbol and data indicator */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-lg font-semibold text-gray-900">{symbol}</h4>
        <DataIndicator
          dataType={dataType}
          dataStatus={dataStatus}
          frontendIndicator={frontendIndicator}
          frontendMessage={frontendMessage}
          frontendColor={frontendColor}
          frontendBgColor={frontendBgColor}
          frontendBorder={frontendBorder}
          reliabilityScore={reliabilityScore}
          dataFreshness={dataFreshness}
          cacheAgeSeconds={cacheAgeSeconds}
          fallbackReason={fallbackReason}
          errorMessage={errorMessage}
        />
      </div>

      {/* Portfolio details */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Quantity:</span>
          <span className="text-sm font-medium">{quantity}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Avg Price:</span>
          <span className="text-sm font-medium">₹{averagePrice.toFixed(2)}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Current Price:</span>
          <span className="text-sm font-medium">{formattedCurrentPrice}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">P&L:</span>
          <span className={`text-sm font-medium ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
            {formattedPnL} ({pnlPercent.toFixed(2)}%)
          </span>
        </div>
        
        <div className="flex justify-between items-center border-t pt-2">
          <span className="text-sm font-semibold text-gray-900">Total Value:</span>
          <span className="text-sm font-semibold text-gray-900">{formattedTotalValue}</span>
        </div>

        {/* Data freshness indicator */}
        <div className="text-xs text-gray-500 mt-2">
          {dataFreshness === 'Real-time' && '🟢 Live market data'}
          {dataFreshness === 'Estimated' && '🟠 Estimated from market patterns'}
          {dataFreshness === 'Simulated' && '🔴 Simulated data'}
          {dataFreshness === 'Error' && '⚫ Data unavailable'}
          {dataFreshness.includes('s old') && `🟡 Cached data (${dataFreshness})`}
        </div>
      </div>
    </div>
  );
};

export default DataIndicator;
