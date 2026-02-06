/**
 * Sentiment Overlay Component
 * Displays news sentiment indicators on charts
 */

import React, { useEffect, useState } from 'react';
import { unifiedAiApi } from '../services/unifiedAiApi';
import {
  FaceSmileIcon,
  FaceFrownIcon,
  MinusIcon,
  NewspaperIcon
} from '@heroicons/react/24/outline';

interface SentimentOverlayProps {
  symbol: string;
  chartApi: any; // Lightweight Charts API
  candlestickSeries: any;
  visible: boolean;
}

interface SentimentMarker {
  time: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  score: number;
  newsCount: number;
}

const SentimentOverlay: React.FC<SentimentOverlayProps> = ({
  symbol,
  chartApi,
  candlestickSeries,
  visible
}) => {
  const [sentimentData, setSentimentData] = useState<SentimentMarker[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible || !chartApi || !candlestickSeries) return;

    fetchSentimentData();
    
    // Refresh sentiment data every 5 minutes
    const interval = setInterval(fetchSentimentData, 300000);
    return () => clearInterval(interval);
  }, [symbol, visible, chartApi, candlestickSeries]);

  const fetchSentimentData = async () => {
    if (!symbol) return;
    
    setLoading(true);
    try {
      const response = await unifiedAiApi.analyzeStock({
        symbol,
        user_query: `Get sentiment analysis for ${symbol}`,
        analysis_depth: 'QUICK',
        include_charts: false,
        include_news: true
      });

      // analyzeStock returns UnifiedAnalysisResponse directly
      if (response?.analysis_result?.sentiment_analysis) {
        const sentiment = response.analysis_result.sentiment_analysis;
        
        // Create sentiment markers for recent candles
        const markers: SentimentMarker[] = [];
        const now = Math.floor(Date.now() / 1000);
        
        // Add current sentiment marker
        markers.push({
          time: now,
          sentiment: sentiment.overall_sentiment === 'positive' ? 'positive' :
                    sentiment.overall_sentiment === 'negative' ? 'negative' : 'neutral',
          score: sentiment.sentiment_score || 0,
          newsCount: 0 // news_count not in current response structure
        });

        setSentimentData(markers);
        drawSentimentMarkers(markers);
      }
    } catch (error) {
      console.error('Error fetching sentiment data:', error);
    } finally {
      setLoading(false);
    }
  };

  const drawSentimentMarkers = (markers: SentimentMarker[]) => {
    if (!chartApi || !candlestickSeries) return;

    // Remove existing markers
    candlestickSeries.setMarkers([]);

    const chartMarkers = markers.map((marker) => {
      let shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown' = 'circle';
      let color = '#888888';
      let text = '';
      let position: 'aboveBar' | 'belowBar' | 'inBar' = 'aboveBar';

      if (marker.sentiment === 'positive') {
        shape = 'arrowUp';
        color = '#26a69a';
        text = '📈';
        position = 'aboveBar';
      } else if (marker.sentiment === 'negative') {
        shape = 'arrowDown';
        color = '#ef5350';
        text = '📉';
        position = 'belowBar';
      } else {
        shape = 'circle';
        color = '#888888';
        text = '➡️';
        position = 'inBar';
      }

      return {
        time: marker.time,
        position: position,
        color: color,
        shape: shape,
        text: text,
        size: 1
      };
    });

    candlestickSeries.setMarkers(chartMarkers);
  };

  if (!visible) return null;

  return (
    <div className="absolute top-2 right-2 bg-[#1e222d]/90 backdrop-blur-sm border border-[#2a2e39] rounded-lg p-2 z-20">
      <div className="flex items-center gap-2 text-xs">
        <NewspaperIcon className="w-4 h-4 text-blue-400" />
        <span className="text-gray-300">Sentiment:</span>
        {loading ? (
          <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
        ) : sentimentData.length > 0 ? (
          <>
            {sentimentData[0].sentiment === 'positive' && (
              <FaceSmileIcon className="w-4 h-4 text-green-400" />
            )}
            {sentimentData[0].sentiment === 'negative' && (
              <FaceFrownIcon className="w-4 h-4 text-red-400" />
            )}
            {sentimentData[0].sentiment === 'neutral' && (
              <MinusIcon className="w-4 h-4 text-gray-400" />
            )}
            <span className={`${
              sentimentData[0].sentiment === 'positive' ? 'text-green-400' :
              sentimentData[0].sentiment === 'negative' ? 'text-red-400' :
              'text-gray-400'
            }`}>
              {sentimentData[0].sentiment.toUpperCase()}
            </span>
            {sentimentData[0].newsCount > 0 && (
              <span className="text-gray-500">
                ({sentimentData[0].newsCount} news)
              </span>
            )}
          </>
        ) : (
          <span className="text-gray-500">No data</span>
        )}
      </div>
    </div>
  );
};

export default SentimentOverlay;

