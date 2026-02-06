import React, { useState, useEffect, useCallback } from 'react';
import { ISeriesApi, CandlestickData, Time } from 'lightweight-charts';

// Technical Indicator Types
export interface IndicatorResult {
  time: Time;
  value: number;
}

export interface IndicatorConfig {
  id: string;
  type: string;
  name: string;
  parameters: Record<string, any>;
  visible: boolean;
  color?: string;
  lineWidth?: number;
  lineStyle?: 'solid' | 'dashed' | 'dotted';
}

// Base Indicator Class
export abstract class TechnicalIndicator {
  abstract name: string;
  abstract calculate(data: CandlestickData[], parameters: Record<string, any>): IndicatorResult[];
  abstract getDefaultParameters(): Record<string, any>;
}

// Moving Average Indicators
export class SMAIndicator extends TechnicalIndicator {
  name = 'Simple Moving Average';
  
  calculate(data: CandlestickData[], parameters: Record<string, any>): IndicatorResult[] {
    const period = parameters.period || 20;
    const results: IndicatorResult[] = [];
    
    for (let i = period - 1; i < data.length; i++) {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      results.push({
        time: data[i].time,
        value: sum / period
      });
    }
    
    return results;
  }
  
  getDefaultParameters() {
    return { period: 20 };
  }
}

export class EMAIndicator extends TechnicalIndicator {
  name = 'Exponential Moving Average';
  
  calculate(data: CandlestickData[], parameters: Record<string, any>): IndicatorResult[] {
    const period = parameters.period || 20;
    const multiplier = 2 / (period + 1);
    const results: IndicatorResult[] = [];
    
    if (data.length === 0) return results;
    
    // First EMA value is the first close price
    let ema = data[0].close;
    results.push({ time: data[0].time, value: ema });
    
    for (let i = 1; i < data.length; i++) {
      ema = (data[i].close - ema) * multiplier + ema;
      results.push({ time: data[i].time, value: ema });
    }
    
    return results;
  }
  
  getDefaultParameters() {
    return { period: 20 };
  }
}

// Momentum Indicators
export class RSIIndicator extends TechnicalIndicator {
  name = 'Relative Strength Index';
  
  calculate(data: CandlestickData[], parameters: Record<string, any>): IndicatorResult[] {
    const period = parameters.period || 14;
    const results: IndicatorResult[] = [];
    
    if (data.length < period + 1) return results;
    
    const gains: number[] = [];
    const losses: number[] = [];
    
    // Calculate price changes
    for (let i = 1; i < data.length; i++) {
      const change = data[i].close - data[i - 1].close;
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }
    
    // Calculate initial averages
    let avgGain = gains.slice(0, period).reduce((sum, gain) => sum + gain, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((sum, loss) => sum + loss, 0) / period;
    
    // Calculate RSI
    for (let i = period; i < data.length; i++) {
      if (avgLoss === 0) {
        results.push({ time: data[i].time, value: 100 });
      } else {
        const rs = avgGain / avgLoss;
        const rsi = 100 - (100 / (1 + rs));
        results.push({ time: data[i].time, value: rsi });
      }
      
      // Update averages for next iteration
      if (i < data.length - 1) {
        avgGain = ((avgGain * (period - 1)) + gains[i]) / period;
        avgLoss = ((avgLoss * (period - 1)) + losses[i]) / period;
      }
    }
    
    return results;
  }
  
  getDefaultParameters() {
    return { period: 14 };
  }
}

export class MACDIndicator extends TechnicalIndicator {
  name = 'MACD';
  
  calculate(data: CandlestickData[], parameters: Record<string, any>): IndicatorResult[] {
    const fastPeriod = parameters.fastPeriod || 12;
    const slowPeriod = parameters.slowPeriod || 26;
    const signalPeriod = parameters.signalPeriod || 9;
    
    const emaFast = new EMAIndicator();
    const emaSlow = new EMAIndicator();
    
    const fastEMA = emaFast.calculate(data, { period: fastPeriod });
    const slowEMA = emaSlow.calculate(data, { period: slowPeriod });
    
    const results: IndicatorResult[] = [];
    
    // Calculate MACD line
    for (let i = 0; i < Math.min(fastEMA.length, slowEMA.length); i++) {
      const macd = fastEMA[i].value - slowEMA[i].value;
      results.push({
        time: fastEMA[i].time,
        value: macd
      });
    }
    
    return results;
  }
  
  getDefaultParameters() {
    return { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 };
  }
}

// Volatility Indicators
export class BollingerBandsIndicator extends TechnicalIndicator {
  name = 'Bollinger Bands';
  
  calculate(data: CandlestickData[], parameters: Record<string, any>): IndicatorResult[] {
    const period = parameters.period || 20;
    const stdDev = parameters.stdDev || 2;
    const results: IndicatorResult[] = [];
    
    const sma = new SMAIndicator();
    const smaResults = sma.calculate(data, { period });
    
    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const mean = smaResults[i - period + 1]?.value || 0;
      
      let variance = 0;
      for (const candle of slice) {
        variance += Math.pow(candle.close - mean, 2);
      }
      const standardDeviation = Math.sqrt(variance / period);
      
      results.push({
        time: data[i].time,
        value: mean + (standardDeviation * stdDev) // Upper band
      });
    }
    
    return results;
  }
  
  getDefaultParameters() {
    return { period: 20, stdDev: 2 };
  }
}

// Volume Indicators
export class VolumeProfileIndicator extends TechnicalIndicator {
  name = 'Volume Profile';
  
  calculate(data: CandlestickData[], parameters: Record<string, any>): IndicatorResult[] {
    const bins = parameters.bins || 20;
    const results: IndicatorResult[] = [];
    
    if (data.length === 0) return results;
    
    // Find price range
    let minPrice = Math.min(...data.map(d => d.low));
    let maxPrice = Math.max(...data.map(d => d.high));
    
    const priceStep = (maxPrice - minPrice) / bins;
    
    // Create volume profile
    const volumeProfile: number[] = new Array(bins).fill(0);
    
    for (const candle of data) {
      const binIndex = Math.min(
        Math.floor((candle.close - minPrice) / priceStep),
        bins - 1
      );
      volumeProfile[binIndex] += (candle as any).volume || 0;
    }
    
    // Convert to indicator results
    for (let i = 0; i < bins; i++) {
      const price = minPrice + (i * priceStep);
      results.push({
        time: data[data.length - 1].time, // Use last time
        value: price
      });
    }
    
    return results;
  }
  
  getDefaultParameters() {
    return { bins: 20 };
  }
}

// Indicator Registry
export class IndicatorRegistry {
  private static indicators: Map<string, TechnicalIndicator> = new Map();
  
  static registerIndicator(type: string, indicator: TechnicalIndicator) {
    this.indicators.set(type, indicator);
  }
  
  static getIndicator(type: string): TechnicalIndicator | undefined {
    return this.indicators.get(type);
  }
  
  static getAllIndicators(): Array<{ type: string; indicator: TechnicalIndicator }> {
    return Array.from(this.indicators.entries()).map(([type, indicator]) => ({
      type,
      indicator
    }));
  }
}

// Register default indicators
IndicatorRegistry.registerIndicator('sma', new SMAIndicator());
IndicatorRegistry.registerIndicator('ema', new EMAIndicator());
IndicatorRegistry.registerIndicator('rsi', new RSIIndicator());
IndicatorRegistry.registerIndicator('macd', new MACDIndicator());
IndicatorRegistry.registerIndicator('bollinger', new BollingerBandsIndicator());
IndicatorRegistry.registerIndicator('volume_profile', new VolumeProfileIndicator());

// Indicator Manager Component
interface IndicatorManagerProps {
  chartId: string;
  data: CandlestickData[];
  onIndicatorsChange: (indicators: IndicatorConfig[]) => void;
  className?: string;
}

const IndicatorManager: React.FC<IndicatorManagerProps> = ({
  chartId,
  data,
  onIndicatorsChange,
  className = ''
}) => {
  const [indicators, setIndicators] = useState<IndicatorConfig[]>([]);
  const [showAddIndicator, setShowAddIndicator] = useState(false);
  const [selectedIndicatorType, setSelectedIndicatorType] = useState<string>('');

  const availableIndicators = IndicatorRegistry.getAllIndicators();

  const addIndicator = useCallback((type: string) => {
    const indicator = IndicatorRegistry.getIndicator(type);
    if (!indicator) return;

    const newIndicator: IndicatorConfig = {
      id: `${type}-${Date.now()}`,
      type,
      name: indicator.name,
      parameters: indicator.getDefaultParameters(),
      visible: true,
      color: getRandomColor(),
      lineWidth: 2,
      lineStyle: 'solid'
    };

    const updatedIndicators = [...indicators, newIndicator];
    setIndicators(updatedIndicators);
    onIndicatorsChange(updatedIndicators);
    setShowAddIndicator(false);
  }, [indicators, onIndicatorsChange]);

  const removeIndicator = useCallback((id: string) => {
    const updatedIndicators = indicators.filter(ind => ind.id !== id);
    setIndicators(updatedIndicators);
    onIndicatorsChange(updatedIndicators);
  }, [indicators, onIndicatorsChange]);

  const updateIndicatorParameter = useCallback((id: string, parameter: string, value: any) => {
    const updatedIndicators = indicators.map(ind => {
      if (ind.id === id) {
        return {
          ...ind,
          parameters: {
            ...ind.parameters,
            [parameter]: value
          }
        };
      }
      return ind;
    });
    setIndicators(updatedIndicators);
    onIndicatorsChange(updatedIndicators);
  }, [indicators, onIndicatorsChange]);

  const toggleIndicatorVisibility = useCallback((id: string) => {
    const updatedIndicators = indicators.map(ind => {
      if (ind.id === id) {
        return { ...ind, visible: !ind.visible };
      }
      return ind;
    });
    setIndicators(updatedIndicators);
    onIndicatorsChange(updatedIndicators);
  }, [indicators, onIndicatorsChange]);

  const getRandomColor = () => {
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff'];
    return colors[Math.floor(Math.random() * colors.length)];
  };

  return (
    <div className={`indicator-manager ${className}`}>
      <div className="indicator-header flex items-center justify-between p-3 bg-gray-800 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">Technical Indicators</h3>
        <button
          onClick={() => setShowAddIndicator(!showAddIndicator)}
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
        >
          Add Indicator
        </button>
      </div>

      {/* Add Indicator Panel */}
      {showAddIndicator && (
        <div className="add-indicator-panel p-3 bg-gray-700 border-b border-gray-600">
          <div className="grid grid-cols-2 gap-2">
            {availableIndicators.map(({ type, indicator }) => (
              <button
                key={type}
                onClick={() => addIndicator(type)}
                className="p-2 text-left bg-gray-600 hover:bg-gray-500 text-white rounded text-sm"
              >
                {indicator.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Indicators List */}
      <div className="indicators-list max-h-96 overflow-y-auto">
        {indicators.map((indicator) => (
          <div key={indicator.id} className="indicator-item p-3 border-b border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={indicator.visible}
                  onChange={() => toggleIndicatorVisibility(indicator.id)}
                  className="rounded"
                />
                <span className="text-white font-medium">{indicator.name}</span>
              </div>
              <button
                onClick={() => removeIndicator(indicator.id)}
                className="text-red-400 hover:text-red-300"
              >
                Remove
              </button>
            </div>

            {/* Indicator Parameters */}
            <div className="indicator-parameters space-y-2">
              {Object.entries(indicator.parameters).map(([param, value]) => (
                <div key={param} className="flex items-center space-x-2">
                  <label className="text-sm text-gray-300 w-20 capitalize">
                    {param}:
                  </label>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => updateIndicatorParameter(indicator.id, param, Number(e.target.value))}
                    className="flex-1 px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white text-sm"
                  />
                </div>
              ))}
            </div>

            {/* Indicator Style */}
            <div className="indicator-style mt-2 flex items-center space-x-2">
              <label className="text-sm text-gray-300">Color:</label>
              <input
                type="color"
                value={indicator.color || '#ffffff'}
                onChange={(e) => {
                  const updatedIndicators = indicators.map(ind => {
                    if (ind.id === indicator.id) {
                      return { ...ind, color: e.target.value };
                    }
                    return ind;
                  });
                  setIndicators(updatedIndicators);
                  onIndicatorsChange(updatedIndicators);
                }}
                className="w-8 h-6 rounded border border-gray-500"
              />
              <label className="text-sm text-gray-300">Width:</label>
              <input
                type="range"
                min="1"
                max="5"
                value={indicator.lineWidth || 2}
                onChange={(e) => {
                  const updatedIndicators = indicators.map(ind => {
                    if (ind.id === indicator.id) {
                      return { ...ind, lineWidth: Number(e.target.value) };
                    }
                    return ind;
                  });
                  setIndicators(updatedIndicators);
                  onIndicatorsChange(updatedIndicators);
                }}
                className="w-16"
              />
            </div>
          </div>
        ))}
      </div>

      {indicators.length === 0 && (
        <div className="p-6 text-center text-gray-400">
          No indicators added. Click "Add Indicator" to get started.
        </div>
      )}
    </div>
  );
};

// Type alias for compatibility
export type TechnicalIndicatorsProps = IndicatorManagerProps;

export default IndicatorManager;
export { IndicatorManager };
