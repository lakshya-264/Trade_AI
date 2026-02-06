/**
 * Multi-Timeframe Tab Component
 * Complete multi-timeframe analysis with timeframe selector
 */

import React, { useState } from 'react';
import { MultiTimeframeView } from './MultiTimeframeView';

interface MultiTimeframeTabProps {
  symbol: string;
  className?: string;
}

export const MultiTimeframeTab: React.FC<MultiTimeframeTabProps> = ({
  symbol,
  className = '',
}) => {
  const [timeframes, setTimeframes] = useState(['1D', '4H', '1H', '15m']);

  const intradayTimeframes = [
    { value: '1m', label: '1m', fullLabel: '1 Minute', category: 'Scalping' },
    { value: '5m', label: '5m', fullLabel: '5 Minutes', category: 'Day Trading' },
    { value: '15m', label: '15m', fullLabel: '15 Minutes', category: 'Intraday' },
    { value: '30m', label: '30m', fullLabel: '30 Minutes', category: 'Intraday' },
    { value: '1H', label: '1H', fullLabel: '1 Hour', category: 'Swing' },
    { value: '4H', label: '4H', fullLabel: '4 Hours', category: 'Swing' },
  ];

  const dailyTimeframes = [
    { value: '1D', label: '1D', fullLabel: '1 Day', category: 'Daily' },
    { value: '1W', label: '1W', fullLabel: '1 Week', category: 'Weekly' },
    { value: '1M', label: '1M', fullLabel: '1 Month', category: 'Monthly' },
  ];

  const toggleTimeframe = (tf: string) => {
    setTimeframes((prev) => {
      if (prev.includes(tf)) {
        // Don't allow removing if only one left
        if (prev.length <= 1) return prev;
        return prev.filter((t) => t !== tf);
      } else {
        // Don't allow more than 4
        if (prev.length >= 4) return prev;
        return [...prev, tf];
      }
    });
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Timeframe Selector */}
      <div className="bg-gradient-to-br from-[#1e222d] to-[#1a1e28] rounded-2xl p-6 border border-[#2a2e39] shadow-xl">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              Select Timeframes
            </h3>
            <p className="text-xs text-gray-400 mt-1">
              Choose up to 4 timeframes • HTF levels show on LTF charts
            </p>
          </div>
          {timeframes.length >= 4 && (
            <div className="px-3 py-1 bg-yellow-500/20 border border-yellow-500/30 rounded-lg">
              <span className="text-xs font-medium text-yellow-400">Maximum reached</span>
            </div>
          )}
        </div>

        {/* Selection Info Bar */}
        <div className="mb-5 px-4 py-3 bg-[#131722] rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Selected:</span>
              <span className="font-mono font-bold text-blue-400">{timeframes.length}/4</span>
            </div>
            <div className="h-4 w-px bg-gray-600"></div>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Active:</span>
              <span className="font-mono font-bold text-white">{timeframes.join(' • ')}</span>
            </div>
          </div>
        </div>

        {/* Intraday Timeframes */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-1 h-4 bg-blue-500 rounded-full"></div>
            <h4 className="text-sm font-semibold text-gray-300">Intraday Timeframes</h4>
            <div className="flex-1 h-px bg-gradient-to-r from-[#2a2e39] to-transparent"></div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {intradayTimeframes.map((tf) => {
              const isSelected = timeframes.includes(tf.value);
              const position = timeframes.indexOf(tf.value) + 1;
              return (
                <button
                  key={tf.value}
                  onClick={() => toggleTimeframe(tf.value)}
                  disabled={!isSelected && timeframes.length >= 4}
                  className={`
                    relative group px-4 py-3 rounded-xl font-medium transition-all duration-200
                    ${
                      isSelected
                        ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/30 scale-105'
                        : 'bg-[#2a2e39] text-gray-400 hover:bg-[#363a45] hover:text-white hover:shadow-md'
                    }
                    ${!isSelected && timeframes.length >= 4 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-lg font-bold">{tf.label}</span>
                    <span className="text-[10px] opacity-75">{tf.category}</span>
                  </div>
                  {isSelected && (
                    <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-xs font-bold shadow-lg">
                      {position}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Daily+ Timeframes */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-1 h-4 bg-purple-500 rounded-full"></div>
            <h4 className="text-sm font-semibold text-gray-300">Daily & Higher Timeframes</h4>
            <div className="flex-1 h-px bg-gradient-to-r from-[#2a2e39] to-transparent"></div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {dailyTimeframes.map((tf) => {
              const isSelected = timeframes.includes(tf.value);
              const position = timeframes.indexOf(tf.value) + 1;
              return (
                <button
                  key={tf.value}
                  onClick={() => toggleTimeframe(tf.value)}
                  disabled={!isSelected && timeframes.length >= 4}
                  className={`
                    relative group px-4 py-3 rounded-xl font-medium transition-all duration-200
                    ${
                      isSelected
                        ? 'bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-lg shadow-purple-500/30 scale-105'
                        : 'bg-[#2a2e39] text-gray-400 hover:bg-[#363a45] hover:text-white hover:shadow-md'
                    }
                    ${!isSelected && timeframes.length >= 4 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-lg font-bold">{tf.label}</span>
                    <span className="text-[10px] opacity-75">{tf.category}</span>
                  </div>
                  {isSelected && (
                    <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-xs font-bold shadow-lg">
                      {position}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Quick Presets */}
        <div className="mt-5 pt-5 border-t border-[#2a2e39]">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-gray-400">Quick Presets:</span>
            <button
              onClick={() => setTimeframes(['1H', '15m', '5m', '1m'])}
              className="px-3 py-1 bg-[#2a2e39] hover:bg-blue-600 text-xs text-gray-300 hover:text-white rounded-lg transition-all"
            >
              Day Trading
            </button>
            <button
              onClick={() => setTimeframes(['1D', '4H', '1H', '15m'])}
              className="px-3 py-1 bg-[#2a2e39] hover:bg-purple-600 text-xs text-gray-300 hover:text-white rounded-lg transition-all"
            >
              Swing Trading
            </button>
            <button
              onClick={() => setTimeframes(['1D', '1W', '1M'])}
              className="px-3 py-1 bg-[#2a2e39] hover:bg-green-600 text-xs text-gray-300 hover:text-white rounded-lg transition-all"
            >
              Long Term
            </button>
          </div>
        </div>
      </div>

      {/* Multi-Timeframe View */}
      <MultiTimeframeView
        key={timeframes.join(',')} // Force re-render when timeframes change
        symbol={symbol}
        defaultTimeframes={timeframes}
        defaultLayout={(timeframes.length === 1 ? 1 : timeframes.length === 2 ? 2 : 4) as 1 | 2 | 4}
        enableSync={true}
        showHTFLevels={true}
        showAlignment={true}
      />
    </div>
  );
};

export default MultiTimeframeTab;

