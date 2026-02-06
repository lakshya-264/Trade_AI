/**
 * Multi-Timeframe View Component
 * Main container for multi-timeframe analysis with synchronized charts
 */

import React, { useState, useEffect } from 'react';
import { IChartApi, ISeriesApi } from 'lightweight-charts';
import { ChartLayoutSwitcher, ChartLayout } from './ChartLayoutSwitcher';
import { TimeframeChartGrid } from './TimeframeChartGrid';
import { TimeframeAlignment } from './TimeframeAlignment';
import {
  multiTimeframeApi,
  CandleData,
  MultiTimeframeDataResponse,
  MultiTimeframeAnalysisResponse,
  AlignmentData,
} from '../services/multiTimeframeApi';
import { chartSyncService } from '../services/chartSyncService';
import { htfLevelService, HTFLevel } from '../services/htfLevelService';

interface MultiTimeframeViewProps {
  symbol: string;
  defaultTimeframes?: string[];
  defaultLayout?: ChartLayout;
  enableSync?: boolean;
  showHTFLevels?: boolean;
  showAlignment?: boolean;
  className?: string;
}

export const MultiTimeframeView: React.FC<MultiTimeframeViewProps> = ({
  symbol,
  defaultTimeframes = ['1D', '4H', '1H', '15m'],
  defaultLayout = 4,
  enableSync = true,
  showHTFLevels = true,
  showAlignment = true,
  className = '',
}) => {
  // State
  const [layout, setLayout] = useState<ChartLayout>(defaultLayout);
  const [timeframes, setTimeframes] = useState<string[]>(defaultTimeframes);
  const [chartData, setChartData] = useState<Record<string, CandleData[]>>({});
  const [analyses, setAnalyses] = useState<Record<string, any>>({});
  const [alignment, setAlignment] = useState<AlignmentData | null>(null);
  const [htfLevels, setHtfLevels] = useState<Record<string, HTFLevel[]>>({});
  const [syncEnabled, setSyncEnabled] = useState(enableSync);
  const [htfEnabled, setHtfEnabled] = useState(showHTFLevels);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Charts registry
  const [charts, setCharts] = useState<Record<string, IChartApi>>({});
  const [series, setSeries] = useState<Record<string, ISeriesApi<'Candlestick'>>>({});

  // Fetch data on mount or symbol change
  useEffect(() => {
    fetchMultiTimeframeData();
  }, [symbol, timeframes]);

  // Update sync service when syncEnabled changes
  useEffect(() => {
    chartSyncService.setSyncEnabled(syncEnabled);
  }, [syncEnabled]);

  // Calculate HTF levels when analyses change
  useEffect(() => {
    if (Object.keys(analyses).length === 0) return;

    const newHtfLevels: Record<string, HTFLevel[]> = {};

    timeframes.forEach((currentTf) => {
      // Get HTF levels for this timeframe (from higher timeframes)
      const higherTimeframes = timeframes.filter((tf) => {
        const currentWeight = getTimeframeWeight(currentTf);
        const tfWeight = getTimeframeWeight(tf);
        return tfWeight > currentWeight;
      });

      if (higherTimeframes.length > 0) {
        const levels = htfLevelService.extractHTFLevels(
          analyses,
          currentTf,
          higherTimeframes
        );
        newHtfLevels[currentTf] = levels;
      } else {
        newHtfLevels[currentTf] = [];
      }
    });

    setHtfLevels(newHtfLevels);
  }, [analyses, timeframes]);

  const getTimeframeWeight = (tf: string): number => {
    const weights: Record<string, number> = {
      '1m': 1,
      '5m': 2,
      '15m': 3,
      '30m': 4,
      '1H': 5,
      '4H': 6,
      '1D': 7,
      '1W': 8,
      '1M': 9,
    };
    return weights[tf] || 5;
  };

  const fetchMultiTimeframeData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch candlestick data
      const dataResponse = await multiTimeframeApi.getMultiTimeframeData(
        symbol,
        timeframes,
        500
      );

      if (!dataResponse.success) {
        throw new Error('Failed to fetch multi-timeframe data');
      }

      setChartData(dataResponse.data);

      // Fetch analysis
      const analysisResponse = await multiTimeframeApi.analyzeMultiTimeframe(
        symbol,
        timeframes,
        ['structure', 'sr', 'sd']
      );

      if (analysisResponse.success) {
        setAnalyses(analysisResponse.analyses);
      }

      // Fetch alignment
      if (showAlignment) {
        const alignmentResponse = await multiTimeframeApi.getTimeframeAlignment(
          symbol,
          timeframes
        );

        if (alignmentResponse.success) {
          setAlignment(alignmentResponse.alignment);
        }
      }
    } catch (err: any) {
      console.error('[MultiTimeframe] Error fetching data:', err);
      setError(err.message || 'Failed to load multi-timeframe data');
    } finally {
      setLoading(false);
    }
  };

  const handleChartReady = (
    timeframe: string,
    chart: IChartApi,
    chartSeries: ISeriesApi<'Candlestick'>
  ) => {
    setCharts((prev) => ({ ...prev, [timeframe]: chart }));
    setSeries((prev) => ({ ...prev, [timeframe]: chartSeries }));
  };

  const handleLayoutChange = (newLayout: ChartLayout) => {
    setLayout(newLayout);
  };

  const handleRefresh = () => {
    fetchMultiTimeframeData();
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-12 bg-[#131722] rounded-lg ${className}`}>
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="text-gray-400">Loading multi-timeframe analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center p-12 bg-[#131722] rounded-lg ${className}`}>
        <div className="text-center">
          <p className="text-red-400 mb-4">❌ {error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Controls */}
      <div className="bg-[#1e222d] rounded-lg p-4 border border-[#2a2e39]">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Left: Layout Switcher */}
          <ChartLayoutSwitcher layout={layout} onLayoutChange={handleLayoutChange} />

          {/* Right: Options */}
          <div className="flex items-center gap-4">
            {/* Sync Toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={syncEnabled}
                onChange={(e) => setSyncEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-300">Sync Crosshair</span>
            </label>

            {/* HTF Levels Toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={htfEnabled}
                onChange={(e) => setHtfEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-300">HTF Levels</span>
            </label>

            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              className="px-3 py-2 bg-[#2a2e39] text-gray-300 rounded-lg hover:bg-[#363a45] transition flex items-center gap-2"
              title="Refresh data"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-sm">Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Alignment Indicator */}
      {showAlignment && alignment && (
        <TimeframeAlignment
          alignment={alignment}
          showDetails={layout === 1}
          compact={layout > 1}
        />
      )}

      {/* Chart Grid */}
      <TimeframeChartGrid
        layout={layout}
        symbol={symbol}
        timeframes={timeframes}
        chartData={chartData}
        htfLevels={htfEnabled ? htfLevels : {}}
        showHTFLevels={htfEnabled}
        syncEnabled={syncEnabled}
        onChartReady={handleChartReady}
      />

      {/* Info Footer */}
      <div className="bg-[#1e222d] rounded-lg p-3 border border-[#2a2e39] text-xs text-gray-400 text-center">
        💡 <strong>Tip:</strong> Hover over any chart to see synchronized crosshair across all
        timeframes. Toggle HTF Levels to see higher timeframe support/resistance on lower timeframe
        charts.
      </div>
    </div>
  );
};

export default MultiTimeframeView;

