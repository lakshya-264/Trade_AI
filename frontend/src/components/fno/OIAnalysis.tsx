/**
 * Open Interest Analysis Component
 * Comprehensive OI analysis with charts similar to OPSTRA
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, ChevronLeft, ChevronRight, Calendar, Clock, BarChart3 } from 'lucide-react';
import { httpClient } from '../../config/api';
import { toast } from 'react-hot-toast';
import { handleApiError } from '../../utils/errorHandler';
import { createChart, IChartApi, ISeriesApi, ColorType, LineData, HistogramData } from 'lightweight-charts';
import StockSelector from '../StockSelector';

interface OIAnalysisProps {
  symbol: string;
  onExpiryChange?: (expiry: string) => void;
  onSymbolChange?: (symbol: string) => void;
}

interface OIMetrics {
  spot_price: number;
  futures_price: number;
  lot_size: number;
  pcr: number;
  max_pain_strike: number;
  modified_max_pain: number;
  atm_strike: number;
  total_call_oi: number;
  total_put_oi: number;
}

interface OIDataPoint {
  strike: number;
  oi?: number;
  change_oi?: number;
  volume?: number;
  ltp?: number;
  buildup?: number;
  call_oi?: number;
  put_oi?: number;
}

const OIAnalysis: React.FC<OIAnalysisProps> = ({ symbol, onExpiryChange, onSymbolChange }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [timeframe, setTimeframe] = useState<'3MIN' | '15MIN' | '30MIN' | 'DAILY'>('DAILY');
  
  // Generate default expiry date (last Thursday of current month)
  const getDefaultExpiry = (): string => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    
    // Get last day of month
    const lastDay = new Date(year, month + 1, 0).getDate();
    let lastThursday = lastDay;
    const dayOfWeek = new Date(year, month, lastDay).getDay();
    const daysToSubtract = (dayOfWeek + 3) % 7;
    lastThursday = lastDay - daysToSubtract;
    
    return `${lastThursday.toString().padStart(2, '0')}${months[month]}${year}`;
  };
  
  const [expiryDate, setExpiryDate] = useState(getDefaultExpiry());
  const [oiData, setOiData] = useState<any>(null);
  const [metrics, setMetrics] = useState<OIMetrics | null>(null);
  const [activeTab, setActiveTab] = useState<'openInterest' | 'oiBuildup'>('openInterest');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [currentSymbol, setCurrentSymbol] = useState(symbol);
  
  // Generate common expiry dates (next 4-6 months)
  const generateExpiryDates = (): string[] => {
    const dates: string[] = [];
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth();
    
    // Helper function to get last Thursday of a month
    const getLastThursday = (year: number, month: number): number => {
      const lastDay = new Date(year, month + 1, 0).getDate();
      let lastThursday = lastDay;
      const dayOfWeek = new Date(year, month, lastDay).getDay();
      // Thursday is day 4 (0 = Sunday, 4 = Thursday)
      const daysToSubtract = (dayOfWeek + 3) % 7;
      lastThursday = lastDay - daysToSubtract;
      return lastThursday;
    };
    
    // Generate next 6 months of expiry dates (last Thursday of each month)
    for (let i = 0; i < 6; i++) {
      const monthIndex = (currentMonth + i) % 12;
      const year = currentYear + Math.floor((currentMonth + i) / 12);
      const monthName = months[monthIndex];
      
      // Get last Thursday of the month
      const lastThursday = getLastThursday(year, monthIndex);
      
      // Format: DDMMMYYYY (e.g., 30DEC2025)
      const dayStr = lastThursday.toString().padStart(2, '0');
      dates.push(`${dayStr}${monthName}${year}`);
    }
    
    // Also add weekly expiry dates for current month (if applicable)
    // For now, we'll keep it simple with monthly expiries
    
    return dates;
  };
  
  const expiryDates = generateExpiryDates();
  
  // Chart refs
  const oiChartContainerRef = useRef<HTMLDivElement>(null);
  const oiBuildupChartContainerRef = useRef<HTMLDivElement>(null);
  const changeOiChartContainerRef = useRef<HTMLDivElement>(null);
  const oiChartRef = useRef<IChartApi | null>(null);
  const oiBuildupChartRef = useRef<IChartApi | null>(null);
  const changeOiChartRef = useRef<IChartApi | null>(null);
  const oiLineSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const pcrLineSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const oiBuildupSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const changeOiSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const resizeObserversRef = useRef<ResizeObserver[]>([]);

  useEffect(() => {
    setCurrentSymbol(symbol);
  }, [symbol]);
  
  useEffect(() => {
    fetchOIData();
  }, [currentSymbol, expiryDate, timeframe]);
  
  const handleSymbolChange = (newSymbol: string) => {
    setCurrentSymbol(newSymbol);
    if (onSymbolChange) {
      onSymbolChange(newSymbol);
    }
  };
  
  const handleChartingClick = () => {
    navigate(`/comprehensive-trading-pro?symbol=${currentSymbol}&tab=patterns&period=1y`);
  };

  useEffect(() => {
    if (oiData) {
      renderCharts();
    }
    return () => {
      // Cleanup charts - check if they exist and are not disposed
      try {
        if (oiChartRef.current) {
          oiChartRef.current.remove();
          oiChartRef.current = null;
        }
      } catch (e) {
        // Chart already disposed, ignore
      }
      try {
        if (oiBuildupChartRef.current) {
          oiBuildupChartRef.current.remove();
          oiBuildupChartRef.current = null;
        }
      } catch (e) {
        // Chart already disposed, ignore
      }
      try {
        if (changeOiChartRef.current) {
          changeOiChartRef.current.remove();
          changeOiChartRef.current = null;
        }
      } catch (e) {
        // Chart already disposed, ignore
      }
      // Clear series refs
      oiLineSeriesRef.current = null;
      pcrLineSeriesRef.current = null;
      oiBuildupSeriesRef.current = null;
      changeOiSeriesRef.current = null;
      // Disconnect resize observers
      resizeObserversRef.current.forEach(observer => {
        try {
          observer.disconnect();
        } catch (e) {
          // Ignore disconnect errors
        }
      });
      resizeObserversRef.current = [];
    };
  }, [oiData]);

  const fetchOIData = async () => {
    setLoading(true);
    try {
      const response = await httpClient.get(`/api/comprehensive-trading/fno/oi-analysis/${currentSymbol}`, {
        params: {
          expiry_date: expiryDate,
          timeframe: timeframe
        }
      }) as any;

      if (response.success && response.data) {
        setOiData(response.data);
        setMetrics(response.data.metrics);
      }
    } catch (error: any) {
      handleApiError(error, 'Failed to fetch OI analysis');
    } finally {
      setLoading(false);
    }
  };

  const renderCharts = () => {
    if (!oiData || !metrics) return;

    // Clean up existing charts before creating new ones
    try {
      if (oiChartRef.current) {
        oiChartRef.current.remove();
        oiChartRef.current = null;
      }
    } catch (e) {
      // Ignore disposal errors
    }
    try {
      if (oiBuildupChartRef.current) {
        oiBuildupChartRef.current.remove();
        oiBuildupChartRef.current = null;
      }
    } catch (e) {
      // Ignore disposal errors
    }
    try {
      if (changeOiChartRef.current) {
        changeOiChartRef.current.remove();
        changeOiChartRef.current = null;
      }
    } catch (e) {
      // Ignore disposal errors
    }

    // Chart 1: Open Interest Line Chart
    if (oiChartContainerRef.current) {
      const chart = createChart(oiChartContainerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: 'white' },
          textColor: '#333',
        },
        width: oiChartContainerRef.current.clientWidth,
        height: 300,
        grid: {
          vertLines: { color: '#e0e0e0' },
          horzLines: { color: '#e0e0e0' },
        },
        rightPriceScale: {
          borderColor: '#ccc',
        },
        leftPriceScale: {
          borderColor: '#ccc',
        },
      });

      // OI Line Series (left axis)
      const oiLineSeries = chart.addLineSeries({
        color: '#ef4444',
        lineWidth: 2,
        priceScaleId: 'left',
        title: 'Open Interest',
      });

      // PCR Line Series (right axis)
      const pcrLineSeries = chart.addLineSeries({
        color: '#3b82f6',
        lineWidth: 2,
        priceScaleId: 'right',
        title: 'PCR',
      });

      // Prepare data with actual dates based on timeframe
      // Since OI data is organized by strike (not time), we'll use today's date
      // and create a time series that represents the data points
      const now = new Date();
      const getTimeForIndex = (idx: number): number => {
        // For strike-based OI data, we need unique ascending timestamps
        // Use Unix timestamp (seconds since epoch) with index offset to ensure uniqueness
        const baseTimestamp = Math.floor(now.getTime() / 1000); // Convert to seconds
        // Add index to ensure unique, ascending timestamps
        // For DAILY: use same day but with seconds offset
        // For intraday: distribute over trading hours
        if (timeframe === 'DAILY') {
          // Use base timestamp + index seconds to ensure uniqueness
          return baseTimestamp + idx;
        } else {
          // For intraday timeframes, create time progression throughout today
          // Distribute strikes over trading hours (9:15 AM to 3:30 PM IST = 375 minutes)
          const tradingMinutes = 375;
          const minutesPerStrike = tradingMinutes / Math.max(oiData.strikes.length, 1);
          const minutesFromStart = idx * minutesPerStrike;
          
          // Set to market open time (9:15 AM local time)
          const date = new Date(now);
          date.setHours(9, 15, 0, 0);
          date.setMinutes(date.getMinutes() + Math.floor(minutesFromStart));
          
          // Return as Unix timestamp (seconds)
          return Math.floor(date.getTime() / 1000);
        }
      };

      const oiLineData: LineData[] = oiData.strikes.map((strike: number, idx: number) => ({
        time: getTimeForIndex(idx),
        value: oiData.call_oi[idx]?.oi || 0,
      })).sort((a: LineData, b: LineData) => (a.time as number) - (b.time as number)); // Ensure ascending order

      const pcrData: LineData[] = oiData.strikes.map((strike: number, idx: number) => {
        const callOi = oiData.call_oi[idx]?.oi || 0;
        const putOi = oiData.put_oi[idx]?.oi || 0;
        const pcr = callOi > 0 ? (putOi / callOi) : 0;
        return {
          time: getTimeForIndex(idx),
          value: pcr * 10, // Scale PCR for visibility (multiply by 10 to match OI scale)
        };
      }).sort((a: LineData, b: LineData) => (a.time as number) - (b.time as number)); // Ensure ascending order

      oiLineSeries.setData(oiLineData);
      pcrLineSeries.setData(pcrData);

      // Note: ATM strike line would be added here if createPriceLine was available
      // For now, we'll show it in the chart title

      chart.timeScale().fitContent();
      oiChartRef.current = chart;
      oiLineSeriesRef.current = oiLineSeries;
      pcrLineSeriesRef.current = pcrLineSeries;

      // Handle resize
      const resizeObserver1 = new ResizeObserver(() => {
        if (oiChartRef.current && oiChartContainerRef.current) {
          try {
            oiChartRef.current.applyOptions({
              width: oiChartContainerRef.current.clientWidth,
            });
          } catch (e) {
            // Ignore resize errors if chart is disposed
          }
        }
      });
      if (oiChartContainerRef.current) {
        resizeObserver1.observe(oiChartContainerRef.current);
        resizeObserversRef.current.push(resizeObserver1);
      }
    }

    // Chart 2: OI Buildup Histogram
    if (oiBuildupChartContainerRef.current) {
      const chart = createChart(oiBuildupChartContainerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: 'white' },
          textColor: '#333',
        },
        width: oiBuildupChartContainerRef.current.clientWidth,
        height: 200,
        grid: {
          vertLines: { color: '#e0e0e0' },
          horzLines: { color: '#e0e0e0' },
        },
      });

      // Add separate series for calls and puts
      const callSeries = chart.addHistogramSeries({
        color: '#ef4444',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'left',
        title: 'Call OI',
      });

      const putSeries = chart.addHistogramSeries({
        color: '#10b981',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'left',
        title: 'Put OI',
      });

      // Prepare data for calls and puts with actual dates
      const getTimeForIndex = (idx: number): number => {
        const now = new Date();
        const baseTimestamp = Math.floor(now.getTime() / 1000);
        
        if (timeframe === 'DAILY') {
          // Use base timestamp + index seconds to ensure uniqueness
          return baseTimestamp + idx;
        } else {
          // Distribute over today's trading hours
          const tradingMinutes = 375;
          const minutesPerStrike = tradingMinutes / Math.max(oiData.strikes.length, 1);
          const minutesFromStart = idx * minutesPerStrike;
          const date = new Date(now);
          date.setHours(9, 15, 0, 0);
          date.setMinutes(date.getMinutes() + Math.floor(minutesFromStart));
          return Math.floor(date.getTime() / 1000);
        }
      };

      const callBuildupData: HistogramData[] = oiData.strikes.map((strike: number, idx: number) => ({
        time: getTimeForIndex(idx),
        value: oiData.call_oi[idx]?.oi || 0,
        color: '#ef4444',
      })).sort((a: LineData, b: LineData) => (a.time as number) - (b.time as number)); // Ensure ascending order

      const putBuildupData: HistogramData[] = oiData.strikes.map((strike: number, idx: number) => ({
        time: getTimeForIndex(idx),
        value: oiData.put_oi[idx]?.oi || 0,
        color: '#10b981',
      })).sort((a: LineData, b: LineData) => (a.time as number) - (b.time as number)); // Ensure ascending order

      callSeries.setData(callBuildupData);
      putSeries.setData(putBuildupData);

      // Note: ATM strike indicator would be added here

      chart.timeScale().fitContent();
      oiBuildupChartRef.current = chart;
      oiBuildupSeriesRef.current = callSeries; // Store reference
    }

    // Chart 3: Change in OI Histogram
    if (changeOiChartContainerRef.current) {
      const chart = createChart(changeOiChartContainerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: 'white' },
          textColor: '#333',
        },
        width: changeOiChartContainerRef.current.clientWidth,
        height: 200,
        grid: {
          vertLines: { color: '#e0e0e0' },
          horzLines: { color: '#e0e0e0' },
        },
      });

      const histogramSeries = chart.addHistogramSeries({
        color: '#10b981',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'left',
      });

      // Prepare Change in OI data with actual dates
      const getTimeForIndex = (idx: number): number => {
        const now = new Date();
        const baseTimestamp = Math.floor(now.getTime() / 1000);
        
        if (timeframe === 'DAILY') {
          // Use base timestamp + index seconds to ensure uniqueness
          return baseTimestamp + idx;
        } else {
          // Distribute over today's trading hours
          const tradingMinutes = 375;
          const minutesPerStrike = tradingMinutes / Math.max(oiData.change_in_oi.length, 1);
          const minutesFromStart = idx * minutesPerStrike;
          const date = new Date(now);
          date.setHours(9, 15, 0, 0);
          date.setMinutes(date.getMinutes() + Math.floor(minutesFromStart));
          return Math.floor(date.getTime() / 1000);
        }
      };

      const histogramData: HistogramData[] = oiData.strikes.map((strike: number, idx: number) => ({
        time: getTimeForIndex(idx),
        value: oiData.change_in_oi[idx]?.change_oi || 0,
        color: (oiData.change_in_oi[idx]?.change_oi || 0) >= 0 ? '#10b981' : '#ef4444',
      })).sort((a: HistogramData, b: HistogramData) => (a.time as number) - (b.time as number)); // Ensure ascending order

      histogramSeries.setData(histogramData);

      // Note: Zero line would be added here

      chart.timeScale().fitContent();
      changeOiChartRef.current = chart;
      changeOiSeriesRef.current = histogramSeries;

      // Handle resize
      const resizeObserver3 = new ResizeObserver(() => {
        if (changeOiChartRef.current && changeOiChartContainerRef.current) {
          try {
            changeOiChartRef.current.applyOptions({
              width: changeOiChartContainerRef.current.clientWidth,
            });
          } catch (e) {
            // Ignore resize errors if chart is disposed
          }
        }
      });
      if (changeOiChartContainerRef.current) {
        resizeObserver3.observe(changeOiChartContainerRef.current);
        resizeObserversRef.current.push(resizeObserver3);
      }
    }
  };

  const handleTimeframeChange = (tf: '3MIN' | '15MIN' | '30MIN' | 'DAILY') => {
    setTimeframe(tf);
  };

  const handleExpiryChange = (newExpiry: string) => {
    setExpiryDate(newExpiry);
    if (onExpiryChange) {
      onExpiryChange(newExpiry);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="w-48">
            <label className="block text-sm text-gray-600 mb-1 font-medium">Symbol</label>
            <StockSelector
              value={currentSymbol}
              onChange={handleSymbolChange}
              className="w-full"
              showNavigateButton={false}
            />
          </div>
          <div className="w-48">
            <label className="block text-sm text-gray-600 mb-1 font-medium">Expiry</label>
            <select
              value={expiryDate}
              onChange={(e) => handleExpiryChange(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {expiryDates.map((expiry) => (
                <option key={expiry} value={expiry}>
                  {expiry}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleChartingClick}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white font-medium"
            title="View charts in Comprehensive Trading Pro"
          >
            <BarChart3 className="w-4 h-4" />
            Charting
          </button>
          <button
            onClick={fetchOIData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="text-xs text-gray-600 mb-1">Spot Price</div>
            <div className="text-lg font-bold text-gray-900">₹{metrics.spot_price.toFixed(2)}</div>
          </div>
          <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
            <div className="text-xs text-gray-600 mb-1">Futures Price</div>
            <div className="text-lg font-bold text-gray-900">₹{metrics.futures_price.toFixed(2)}</div>
          </div>
          <div className="bg-green-50 rounded-lg p-3 border border-green-200">
            <div className="text-xs text-gray-600 mb-1">Lot Size</div>
            <div className="text-lg font-bold text-gray-900">{metrics.lot_size}</div>
          </div>
          <div className="bg-pink-50 rounded-lg p-3 border border-pink-200">
            <div className="text-xs text-gray-600 mb-1">PCR</div>
            <div className="text-lg font-bold text-gray-900">{metrics.pcr.toFixed(2)}</div>
          </div>
          <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
            <div className="text-xs text-gray-600 mb-1">MaxPain Strike</div>
            <div className="text-lg font-bold text-gray-900">{metrics.max_pain_strike}</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="text-xs text-gray-600 mb-1">Modified MaxPain</div>
            <div className="text-lg font-bold text-gray-900">{metrics.modified_max_pain.toFixed(0)}</div>
          </div>
        </div>
      )}

      {/* Tabs: OPEN INTEREST and OI BUILDUP */}
      <div className="flex items-center gap-2 mb-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('openInterest')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'openInterest'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          OPEN INTEREST
        </button>
        <button
          onClick={() => setActiveTab('oiBuildup')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'oiBuildup'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          OI BUILDUP
        </button>
      </div>

      {/* MAXPAIN Section */}
      <div className="bg-purple-50 rounded-lg p-4 border border-purple-200 mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-900">MAXPAIN</span>
            <RefreshCw className="w-4 h-4 text-gray-600 cursor-pointer hover:text-gray-900" onClick={fetchOIData} />
          </div>
        </div>
        <div className="flex items-center gap-4 mb-3">
          <div className="flex items-center gap-2">
            <ChevronLeft 
              className="w-4 h-4 text-gray-600 cursor-pointer hover:text-gray-900" 
              onClick={() => {
                const newDate = new Date(selectedDate);
                newDate.setDate(newDate.getDate() - 1);
                setSelectedDate(newDate);
              }}
            />
            <input
              type="datetime-local"
              value={(() => {
                // Format date for datetime-local input (YYYY-MM-DDTHH:mm)
                const d = new Date(selectedDate);
                const year = d.getFullYear();
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                const hours = String(d.getHours()).padStart(2, '0');
                const minutes = String(d.getMinutes()).padStart(2, '0');
                return `${year}-${month}-${day}T${hours}:${minutes}`;
              })()}
              onChange={(e) => setSelectedDate(new Date(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded text-sm text-gray-900"
            />
            <ChevronRight 
              className="w-4 h-4 text-gray-600 cursor-pointer hover:text-gray-900"
              onClick={() => {
                const newDate = new Date(selectedDate);
                newDate.setDate(newDate.getDate() + 1);
                setSelectedDate(newDate);
              }}
            />
          </div>
          <div className="flex items-center gap-2">
            {(['3MIN', '15MIN', '30MIN', 'DAILY'] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => handleTimeframeChange(tf)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  timeframe === tf
                    ? 'bg-purple-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
        {metrics && (
          <div className="text-sm text-gray-700">
            <span className="font-semibold">MaxPain Strike: </span>
            <span className="text-purple-700 font-bold">{metrics.max_pain_strike}</span>
            {' | '}
            <span className="font-semibold">Modified MaxPain: </span>
            <span className="text-purple-700 font-bold">{metrics.modified_max_pain.toFixed(0)}</span>
          </div>
        )}
      </div>

      {/* Charts based on active tab */}
      {oiData && metrics && (
        <div className="space-y-6">
          {activeTab === 'openInterest' ? (
            <>
              {/* Open Interest Chart */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {symbol} {expiryDate} - current
                  </h3>
                  <div className="text-sm text-gray-600">
                    ATM Strike: <span className="font-semibold text-purple-600">{metrics.atm_strike}</span>
                  </div>
                </div>
                <div ref={oiChartContainerRef} className="w-full border border-gray-200 rounded bg-white" style={{ height: '300px' }} />
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-0.5 bg-red-500"></div>
                    <span>Open Interest</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-0.5 bg-blue-500"></div>
                    <span>PCR (scaled ×10)</span>
                  </div>
                </div>
              </div>

              {/* Change in OI Chart */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Change in OI</h3>
                <div ref={changeOiChartContainerRef} className="w-full border border-gray-200 rounded bg-white" style={{ height: '200px' }} />
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 bg-green-500"></div>
                    <span>Increase</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 bg-red-500"></div>
                    <span>Decrease</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* OI Buildup Chart */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {symbol} {expiryDate} - OI Buildup
                </h3>
                <div ref={oiBuildupChartContainerRef} className="w-full border border-gray-200 rounded bg-white" style={{ height: '300px' }} />
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 bg-red-500"></div>
                    <span>Call OI Buildup</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 bg-green-500"></div>
                    <span>Put OI Buildup</span>
                  </div>
                  <div className="text-gray-500">
                    ATM Strike: <span className="font-semibold">{metrics.atm_strike}</span>
                  </div>
                </div>
              </div>

              {/* Volume Analysis */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Volume Analysis</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Total Call OI</div>
                    <div className="text-lg font-bold text-red-600">{metrics.total_call_oi.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Total Put OI</div>
                    <div className="text-lg font-bold text-green-600">{metrics.total_put_oi.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 mb-1">PCR Ratio</div>
                    <div className={`text-lg font-bold ${metrics.pcr > 1 ? 'text-green-600' : 'text-red-600'}`}>
                      {metrics.pcr.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 mb-1">OI Trend</div>
                    <div className={`text-lg font-bold ${metrics.pcr > 0.8 && metrics.pcr < 1.2 ? 'text-yellow-600' : metrics.pcr > 1 ? 'text-green-600' : 'text-red-600'}`}>
                      {metrics.pcr > 1.2 ? 'Bullish' : metrics.pcr < 0.8 ? 'Bearish' : 'Neutral'}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      )}
    </div>
  );
};

export default OIAnalysis;

