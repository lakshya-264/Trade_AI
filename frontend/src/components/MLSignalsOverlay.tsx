/**
 * ML Signals Overlay Component
 * Displays machine learning predictions as chart overlays
 */

import React, { useEffect, useState } from 'react';
import { unifiedAiApi } from '../services/unifiedAiApi';
import {
  CpuChipIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline';

interface MLSignalsOverlayProps {
  symbol: string;
  chartApi: any; // Lightweight Charts API
  candlestickSeries: any;
  visible: boolean;
}

interface MLSignal {
  time: number;
  prediction: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  priceTarget?: number;
  stopLoss?: number;
}

const MLSignalsOverlay: React.FC<MLSignalsOverlayProps> = ({
  symbol,
  chartApi,
  candlestickSeries,
  visible
}) => {
  const [mlSignals, setMLSignals] = useState<MLSignal[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible || !chartApi || !candlestickSeries) return;

    fetchMLSignals();
    
    // Refresh ML signals every 10 minutes
    const interval = setInterval(fetchMLSignals, 600000);
    return () => clearInterval(interval);
  }, [symbol, visible, chartApi, candlestickSeries]);

  const fetchMLSignals = async () => {
    if (!symbol) return;
    
    setLoading(true);
    try {
      const response = await unifiedAiApi.analyzeStock({
        symbol,
        user_query: `Get ML predictions for ${symbol}`,
        analysis_depth: 'STANDARD',
        include_charts: false,
        include_news: false
      });

      // analyzeStock returns UnifiedAnalysisResponse directly
      if (response?.analysis_result?.ml_signals) {
        const mlData = response.analysis_result.ml_signals;
        const now = Math.floor(Date.now() / 1000);
        
        const signals: MLSignal[] = [{
          time: now,
          prediction: (mlData.prediction || 'HOLD') as 'BUY' | 'SELL' | 'HOLD',
          confidence: (mlData.confidence || 0) / 100, // Convert to decimal if needed
          priceTarget: response.price_target,
          stopLoss: response.stop_loss
        }];

        setMLSignals(signals);
        drawMLMarkers(signals);
      }
    } catch (error) {
      console.error('Error fetching ML signals:', error);
    } finally {
      setLoading(false);
    }
  };

  const drawMLMarkers = (signals: MLSignal[]) => {
    if (!chartApi || !candlestickSeries) return;

    // Get existing markers
    const existingMarkers = candlestickSeries.markers() || [];
    
    // Filter out old ML markers (those with ML prefix in text)
    const filteredMarkers = existingMarkers.filter((m: any) => 
      !m.text || !m.text.includes('ML:')
    );

    const mlMarkers = signals.map((signal) => {
      let shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown' = 'circle';
      let color = '#888888';
      let text = 'ML:';
      let position: 'aboveBar' | 'belowBar' | 'inBar' = 'aboveBar';

      if (signal.prediction === 'BUY') {
        shape = 'arrowUp';
        color = '#26a69a';
        text = `ML: BUY (${Math.round(signal.confidence * 100)}%)`;
        position = 'belowBar';
      } else if (signal.prediction === 'SELL') {
        shape = 'arrowDown';
        color = '#ef5350';
        text = `ML: SELL (${Math.round(signal.confidence * 100)}%)`;
        position = 'aboveBar';
      } else {
        shape = 'circle';
        color = '#888888';
        text = `ML: HOLD (${Math.round(signal.confidence * 100)}%)`;
        position = 'inBar';
      }

      return {
        time: signal.time,
        position: position,
        color: color,
        shape: shape,
        text: text,
        size: 1
      };
    });

    // Combine with existing markers
    candlestickSeries.setMarkers([...filteredMarkers, ...mlMarkers]);
  };

  if (!visible) return null;

  return (
    <div className="absolute top-2 right-2 bg-[#1e222d]/90 backdrop-blur-sm border border-[#2a2e39] rounded-lg p-2 z-20">
      <div className="flex items-center gap-2 text-xs">
        <CpuChipIcon className="w-4 h-4 text-purple-400" />
        <span className="text-gray-300">ML Signal:</span>
        {loading ? (
          <div className="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
        ) : mlSignals.length > 0 ? (
          <>
            {mlSignals[0].prediction === 'BUY' && (
              <ArrowTrendingUpIcon className="w-4 h-4 text-green-400" />
            )}
            {mlSignals[0].prediction === 'SELL' && (
              <ArrowTrendingDownIcon className="w-4 h-4 text-red-400" />
            )}
            {mlSignals[0].prediction === 'HOLD' && (
              <MinusIcon className="w-4 h-4 text-gray-400" />
            )}
            <span className={`${
              mlSignals[0].prediction === 'BUY' ? 'text-green-400' :
              mlSignals[0].prediction === 'SELL' ? 'text-red-400' :
              'text-gray-400'
            }`}>
              {mlSignals[0].prediction}
            </span>
            <span className="text-gray-500">
              ({Math.round(mlSignals[0].confidence * 100)}%)
            </span>
            {mlSignals[0].priceTarget && (
              <span className="text-gray-500">
                Target: ₹{mlSignals[0].priceTarget.toFixed(2)}
              </span>
            )}
          </>
        ) : (
          <span className="text-gray-500">No signal</span>
        )}
      </div>
    </div>
  );
};

export default MLSignalsOverlay;

