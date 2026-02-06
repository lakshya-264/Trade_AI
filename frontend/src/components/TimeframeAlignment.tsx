/**
 * Timeframe Alignment Indicator Component
 * Shows trend alignment across multiple timeframes with confidence scores
 */

import React from 'react';
import { AlignmentData } from '../services/multiTimeframeApi';

interface TimeframeAlignmentProps {
  alignment: AlignmentData | null;
  loading?: boolean;
  compact?: boolean;
  showDetails?: boolean;
  className?: string;
}

export const TimeframeAlignment: React.FC<TimeframeAlignmentProps> = ({
  alignment,
  loading = false,
  compact = false,
  showDetails = true,
  className = '',
}) => {
  if (loading) {
    return (
      <div className={`bg-[#1e222d] rounded-lg p-4 ${className}`}>
        <div className="flex items-center gap-2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          <span className="text-gray-400">Calculating alignment...</span>
        </div>
      </div>
    );
  }

  if (!alignment) {
    return (
      <div className={`bg-[#1e222d] rounded-lg p-4 ${className}`}>
        <span className="text-gray-400">No alignment data available</span>
      </div>
    );
  }

  const getTrendIcon = (trend: string): string => {
    switch (trend.toLowerCase()) {
      case 'bullish':
        return '🟢';
      case 'bearish':
        return '🔴';
      case 'neutral':
        return '⚪';
      default:
        return '⚫';
    }
  };

  const getTrendColor = (trend: string): string => {
    switch (trend.toLowerCase()) {
      case 'bullish':
        return 'text-green-400';
      case 'bearish':
        return 'text-red-400';
      case 'neutral':
        return 'text-gray-400';
      default:
        return 'text-gray-400';
    }
  };

  const getVerdictColor = (verdict: string): string => {
    if (verdict.includes('BULLISH')) return 'text-green-400';
    if (verdict.includes('BEARISH')) return 'text-red-400';
    return 'text-gray-400';
  };

  const getVerdictBg = (verdict: string): string => {
    if (verdict.includes('BULLISH')) return 'bg-green-500/20';
    if (verdict.includes('BEARISH')) return 'bg-red-500/20';
    return 'bg-gray-500/20';
  };

  const renderStars = (confidence: number): JSX.Element[] => {
    const stars = Math.round(confidence * 5);
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < stars ? 'text-yellow-400' : 'text-gray-600'}>
        ⭐
      </span>
    ));
  };

  if (compact) {
    return (
      <div className={`bg-[#1e222d] rounded-lg p-3 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Alignment:</span>
            <span className={`text-sm font-bold ${getVerdictColor(alignment.overall.verdict)}`}>
              {alignment.overall.verdict}
            </span>
          </div>
          <div className="flex items-center gap-1">
            {renderStars(alignment.overall.confidence)}
            <span className="text-xs text-gray-400 ml-2">
              {Math.round(alignment.overall.alignment_pct)}%
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-[#1e222d] rounded-lg border border-[#2a2e39] ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#2a2e39]">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          📊 Timeframe Alignment
        </h3>
      </div>

      {/* Timeframe Details */}
      {showDetails && (
        <div className="px-4 py-3 space-y-2 border-b border-[#2a2e39]">
          {Object.entries(alignment.timeframes).map(([tf, data]) => (
            <div key={tf} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm font-bold text-gray-300 w-12">{tf}:</span>
                <span className="text-lg">{getTrendIcon(data.trend)}</span>
                <span className={`text-sm font-medium ${getTrendColor(data.trend)}`}>
                  {data.trend.charAt(0).toUpperCase() + data.trend.slice(1)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      data.trend === 'bullish'
                        ? 'bg-green-500'
                        : data.trend === 'bearish'
                        ? 'bg-red-500'
                        : 'bg-gray-500'
                    }`}
                    style={{ width: `${data.confidence * 100}%` }}
                  ></div>
                </div>
                <span className="text-xs text-gray-400 w-10 text-right">
                  {Math.round(data.confidence * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Overall Verdict */}
      <div className="px-4 py-3 space-y-3">
        <div className={`px-4 py-3 rounded-lg ${getVerdictBg(alignment.overall.verdict)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold text-gray-300">Overall:</span>
            <span className={`text-lg font-bold ${getVerdictColor(alignment.overall.verdict)}`}>
              {alignment.overall.verdict}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              {renderStars(alignment.overall.confidence)}
              <span className="text-xs text-gray-400 ml-2">
                ({Math.round(alignment.overall.confidence * 100)}%)
              </span>
            </div>
            <span className="text-xs text-gray-400">{alignment.overall.agreement}</span>
          </div>
        </div>

        {/* Confidence Bar */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-400">Alignment</span>
            <span className="text-xs text-gray-400">
              {Math.round(alignment.overall.alignment_pct)}%
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                alignment.overall.alignment_pct >= 75
                  ? alignment.overall.verdict.includes('BULLISH')
                    ? 'bg-green-500'
                    : 'bg-red-500'
                  : 'bg-yellow-500'
              }`}
              style={{ width: `${alignment.overall.alignment_pct}%` }}
            ></div>
          </div>
        </div>

        {/* Recommendation */}
        {alignment.overall.recommendation && (
          <div className="bg-[#2a2e39] rounded-lg p-3">
            <p className="text-xs text-gray-300 leading-relaxed">
              💡 <span className="font-semibold">Recommendation:</span>{' '}
              {alignment.overall.recommendation}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TimeframeAlignment;

