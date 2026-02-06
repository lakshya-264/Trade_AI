/**
 * Chart Library Adapter
 * 
 * Provides compatibility with multiple charting libraries:
 * - Recharts: React-native charting library
 * - Chart.js: Canvas-based charting library  
 * - TradingView: Professional trading charts
 * - D3.js: Data visualization library
 * - Highcharts: Commercial charting library
 * 
 * Usage:
 * ```typescript
 * // Convert data for specific library
 * const rechartsData = RechartsAdapter.convertToRechartsData(chartData);
 * 
 * // Create chart configuration
 * const config = ChartFactory.createChart('recharts', chartConfig);
 * 
 * // Convert data using factory
 * const data = ChartFactory.convertData('recharts', chartData);
 * ```
 */

import { 
  ChartData, 
  ChartConfig, 
  ChartSeries, 
  ChartAxis, 
  ChartOverlay,
  ChartLibraryConfig 
} from '../types/api';

/**
 * Recharts Chart Adapter
 * 
 * Converts data and creates configurations for Recharts library.
 * Recharts is a composable charting library built on React and D3.
 */
export class RechartsAdapter {
  /**
   * Converts ChartData array to Recharts-compatible format
   * @param data - Array of chart data points
   * @returns Array of data points formatted for Recharts
   */
  static convertToRechartsData(data: ChartData[]): any[] {
    if (!Array.isArray(data)) {
      throw new Error('Data must be an array of ChartData objects');
    }
    
    if (data.length === 0) {
      return [];
    }
    
    return data.map(point => ({
      date: point.date,
      timestamp: point.timestamp,
      open: point.open,
      high: point.high,
      low: point.low,
      close: point.close,
      volume: point.volume,
      // Technical indicators
      sma20: point.sma20,
      sma50: point.sma50,
      ema12: point.ema12,
      ema26: point.ema26,
      rsi: point.rsi,
      macd: point.macd,
      macdSignal: point.macd_signal,
      macdHistogram: point.macd_histogram,
      bbandsUpper: point.bbands_upper,
      bbandsMiddle: point.bbands_middle,
      bbandsLower: point.bbands_lower,
      // Volume indicators
      volumeSma: point.volume_sma,
      obv: point.obv,
      // Price patterns
      isDoji: point.doji,
      isHammer: point.hammer,
      isMorningStar: point.morning_star,
      // Support/Resistance
      supportLevel: point.support_level,
      resistanceLevel: point.resistance_level,
      pivotPoint: point.pivot_point
    }));
  }

  /**
   * Creates Recharts configuration object
   * @param config - Chart configuration
   * @returns Recharts-compatible configuration object
   */
  static createRechartsConfig(config: ChartConfig): any {
    if (!config) {
      throw new Error('Chart configuration is required');
    }
    
    return {
      width: config.width || 800,
      height: config.height || 400,
      margin: config.margin || { top: 20, right: 30, left: 20, bottom: 5 },
      data: RechartsAdapter.convertToRechartsData(config.series[0]?.data || []),
      // Additional Recharts-specific configuration
      syncId: 'chart-sync',
      syncMethod: 'value'
    };
  }
}

// Chart.js adapter
export class ChartJSAdapter {
  static convertToChartJSData(data: ChartData[]): any {
    return {
      labels: data.map(point => point.date),
      datasets: [
        {
          label: 'Price',
          data: data.map(point => ({
            x: point.timestamp,
            y: point.close,
            o: point.open,
            h: point.high,
            l: point.low,
            v: point.volume
          })),
          type: 'candlestick',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }
      ]
    };
  }

  static createChartJSConfig(config: ChartConfig): any {
    return {
      type: 'candlestick',
      data: ChartJSAdapter.convertToChartJSData(config.series[0]?.data || []),
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day'
            }
          },
          y: {
            beginAtZero: false,
            position: 'right'
          }
        },
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          tooltip: {
            enabled: config.tooltip.enabled,
            mode: config.tooltip.shared ? 'index' : 'point',
            intersect: false
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      }
    };
  }
}

// TradingView adapter
export class TradingViewAdapter {
  static convertToTradingViewData(data: ChartData[]): any[] {
    return data.map(point => [
      point.timestamp,
      point.open,
      point.high,
      point.low,
      point.close,
      point.volume
    ]);
  }

  static createTradingViewConfig(config: ChartConfig): any {
    return {
      symbol: 'RELIANCE',
      interval: '1D',
      container_id: 'tradingview_chart',
      datafeed: {
        onReady: (callback: any) => {
          callback({
            exchanges: [
              { value: 'NSE', name: 'National Stock Exchange', desc: 'NSE' }
            ],
            symbols_types: [
              { name: 'Stock', value: 'stock' }
            ],
            supported_resolutions: ['1', '5', '15', '30', '60', '1D', '1W', '1M'],
            supports_marks: true,
            supports_timescale_marks: true
          });
        },
        searchSymbols: (userInput: string, exchange: string, symbolType: string, onResultReadyCallback: any) => {
          // Implement symbol search
          onResultReadyCallback([]);
        },
        resolveSymbol: (symbolName: string, onSymbolResolvedCallback: any, onResolveErrorCallback: any) => {
          onSymbolResolvedCallback({
            name: symbolName,
            ticker: symbolName,
            description: symbolName,
            type: 'stock',
            session: '0930-1530',
            timezone: 'Asia/Kolkata',
            exchange: 'NSE',
            minmov: 1,
            pricescale: 100,
            has_intraday: true,
            has_weekly_and_monthly: true,
            supported_resolutions: ['1', '5', '15', '30', '60', '1D', '1W', '1M'],
            volume_precision: 0,
            data_status: 'streaming'
          });
        },
        getBars: (symbolInfo: any, resolution: string, from: number, to: number, onHistoryCallback: any, onErrorCallback: any, firstDataRequest: boolean) => {
          const bars = TradingViewAdapter.convertToTradingViewData(config.series[0]?.data || []);
          onHistoryCallback(bars, { noData: false });
        },
        subscribeBars: (symbolInfo: any, resolution: string, onRealtimeCallback: any, subscribeUID: string, onResetCacheNeededCallback: any) => {
          // Implement real-time data subscription
        },
        unsubscribeBars: (subscribeUID: string) => {
          // Implement unsubscribe
        }
      },
      library_path: '/static/charting_library/',
      locale: 'en',
      disabled_features: ['use_localstorage_for_settings'],
      enabled_features: ['study_templates'],
      charts_storage_url: 'https://saveload.tradingview.com',
      charts_storage_api_version: '1.1',
      client_id: 'tradingview.com',
      user_id: 'public_user_id',
      fullscreen: false,
      autosize: true,
      studies_overrides: {},
      overrides: {
        'paneProperties.background': '#131722',
        'paneProperties.vertGridProperties.color': '#363c4e',
        'paneProperties.horzGridProperties.color': '#363c4e',
        'symbolWatermarkProperties.transparency': 90,
        'scalesProperties.textColor': '#AAA',
        'mainSeriesProperties.candleStyle.upColor': '#26a69a',
        'mainSeriesProperties.candleStyle.downColor': '#ef5350',
        'mainSeriesProperties.candleStyle.borderUpColor': '#26a69a',
        'mainSeriesProperties.candleStyle.borderDownColor': '#ef5350',
        'mainSeriesProperties.candleStyle.wickUpColor': '#26a69a',
        'mainSeriesProperties.candleStyle.wickDownColor': '#ef5350'
      }
    };
  }
}

// D3.js adapter
export class D3Adapter {
  static convertToD3Data(data: ChartData[]): any[] {
    return data.map(point => ({
      date: new Date(point.timestamp),
      open: point.open,
      high: point.high,
      low: point.low,
      close: point.close,
      volume: point.volume,
      // Technical indicators
      sma20: point.sma20,
      sma50: point.sma50,
      ema12: point.ema12,
      ema26: point.ema26,
      rsi: point.rsi,
      macd: point.macd,
      macdSignal: point.macd_signal,
      macdHistogram: point.macd_histogram,
      bbandsUpper: point.bbands_upper,
      bbandsMiddle: point.bbands_middle,
      bbandsLower: point.bbands_lower
    }));
  }

  static createD3Config(config: ChartConfig): any {
    return {
      width: config.width || 800,
      height: config.height || 400,
      margin: config.margin || { top: 20, right: 30, left: 20, bottom: 5 },
      data: D3Adapter.convertToD3Data(config.series[0]?.data || []),
      // D3-specific configuration
      scales: {
        x: {
          type: 'time',
          domain: 'auto'
        },
        y: {
          type: 'linear',
          domain: 'auto'
        }
      },
      axes: {
        x: {
          show: true,
          format: '%Y-%m-%d'
        },
        y: {
          show: true,
          format: '.2f'
        }
      }
    };
  }
}

// Highcharts adapter
export class HighchartsAdapter {
  static convertToHighchartsData(data: ChartData[]): any[] {
    return data.map(point => [
      point.timestamp,
      point.open,
      point.high,
      point.low,
      point.close,
      point.volume
    ]);
  }

  static createHighchartsConfig(config: ChartConfig): any {
    return {
      chart: {
        type: 'candlestick',
        backgroundColor: '#131722',
        style: {
          fontFamily: 'Arial, sans-serif'
        }
      },
      title: {
        text: 'Stock Price Chart',
        style: {
          color: '#AAA'
        }
      },
      xAxis: {
        type: 'datetime',
        gridLineColor: '#363c4e',
        lineColor: '#363c4e',
        tickColor: '#363c4e',
        labels: {
          style: {
            color: '#AAA'
          }
        }
      },
      yAxis: {
        title: {
          text: 'Price',
          style: {
            color: '#AAA'
          }
        },
        gridLineColor: '#363c4e',
        lineColor: '#363c4e',
        tickColor: '#363c4e',
        labels: {
          style: {
            color: '#AAA'
          }
        }
      },
      series: [
        {
          name: 'Price',
          data: HighchartsAdapter.convertToHighchartsData(config.series[0]?.data || []),
          color: '#26a69a',
          upColor: '#26a69a',
          downColor: '#ef5350'
        }
      ],
      tooltip: {
        enabled: config.tooltip.enabled,
        shared: config.tooltip.shared,
        crosshair: config.tooltip.crosshair,
        formatter: function(this: any): string {
          const point = this.point;
          return `
            <b>${new Date(point.x).toLocaleDateString()}</b><br/>
            Open: ${point.open}<br/>
            High: ${point.high}<br/>
            Low: ${point.low}<br/>
            Close: ${point.close}<br/>
            Volume: ${point.volume}
          `;
        }
      },
      plotOptions: {
        candlestick: {
          color: '#ef5350',
          upColor: '#26a69a',
          lineColor: '#363c4e'
        }
      },
      credits: {
        enabled: false
      }
    };
  }
}

/**
 * Universal Chart Factory
 * 
 * Provides a unified interface for creating charts across different libraries.
 * Use this factory to avoid direct library dependencies in your components.
 */
export class ChartFactory {
  /**
   * Creates chart configuration for specified library
   * @param library - Chart library name ('recharts', 'chartjs', etc.)
   * @param config - Chart configuration object
   * @returns Library-specific chart configuration
   * @throws Error if library is not supported
   */
  static createChart(
    library: ChartLibraryConfig['library'],
    config: ChartConfig
  ): any {
    if (!library) {
      throw new Error('Chart library is required');
    }
    
    if (!config) {
      throw new Error('Chart configuration is required');
    }
    
    switch (library) {
      case 'recharts':
        return RechartsAdapter.createRechartsConfig(config);
      
      case 'chartjs':
        return ChartJSAdapter.createChartJSConfig(config);
      
      case 'tradingview':
        return TradingViewAdapter.createTradingViewConfig(config);
      
      case 'd3':
        return D3Adapter.createD3Config(config);
      
      case 'highcharts':
        return HighchartsAdapter.createHighchartsConfig(config);
      
      default:
        throw new Error(`Unsupported chart library: ${library}`);
    }
  }

  /**
   * Converts data for specified chart library
   * @param library - Chart library name ('recharts', 'chartjs', etc.)
   * @param data - Array of chart data points
   * @returns Library-specific data format
   * @throws Error if library is not supported
   */
  static convertData(
    library: ChartLibraryConfig['library'],
    data: ChartData[]
  ): any {
    if (!library) {
      throw new Error('Chart library is required');
    }
    
    if (!Array.isArray(data)) {
      throw new Error('Data must be an array of ChartData objects');
    }
    
    switch (library) {
      case 'recharts':
        return RechartsAdapter.convertToRechartsData(data);
      
      case 'chartjs':
        return ChartJSAdapter.convertToChartJSData(data);
      
      case 'tradingview':
        return TradingViewAdapter.convertToTradingViewData(data);
      
      case 'd3':
        return D3Adapter.convertToD3Data(data);
      
      case 'highcharts':
        return HighchartsAdapter.convertToHighchartsData(data);
      
      default:
        throw new Error(`Unsupported chart library: ${library}`);
    }
  }
}

// All adapters are already exported inline above
