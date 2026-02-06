/**
 * Suggested Strategies Component
 * Displays predefined options strategies based on market outlook
 */

import React, { useState, useEffect } from 'react';
import { BookOpen, TrendingUp, TrendingDown, ArrowLeftRight, Zap } from 'lucide-react';
import { Strategy } from './StrategyBuilder';
import { httpClient } from '../../config/api';
import { toast } from 'react-hot-toast';

interface SuggestedStrategiesProps {
  symbol: string;
  onStrategySelect: (strategy: Strategy) => void;
}

interface SuggestedStrategy {
  id: string;
  name: string;
  description: string;
  outlook: 'bullish' | 'bearish' | 'neutral' | 'volatile';
  risk: 'low' | 'medium' | 'high';
  maxProfit: string;
  maxLoss: string;
  legs: Strategy['legs'];
  payoffGraph?: string; // Base64 encoded image or SVG path
}

const SuggestedStrategies: React.FC<SuggestedStrategiesProps> = ({ symbol, onStrategySelect }) => {
  const [selectedOutlook, setSelectedOutlook] = useState<'bullish' | 'bearish' | 'neutral' | 'volatile'>('bullish');
  const [strategies, setStrategies] = useState<SuggestedStrategy[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSuggestedStrategies();
  }, [selectedOutlook, symbol]);

  const fetchSuggestedStrategies = async () => {
    if (!symbol) {
      // If no symbol, use default strategies
      setStrategies(getDefaultStrategies(selectedOutlook));
      return;
    }
    
    setLoading(true);
    try {
      const response = await httpClient.get(`/api/comprehensive-trading/strategy/suggested`, {
        params: { symbol, outlook: selectedOutlook }
      }) as any;

      if (response.data?.success) {
        setStrategies(response.data.data || getDefaultStrategies(selectedOutlook));
      } else {
        setStrategies(getDefaultStrategies(selectedOutlook));
      }
    } catch (error) {
      console.error('Error fetching suggested strategies:', error);
      setStrategies(getDefaultStrategies(selectedOutlook));
    } finally {
      setLoading(false);
    }
  };

  const getDefaultStrategies = (outlook: string): SuggestedStrategy[] => {
    const baseStrategies: Record<string, SuggestedStrategy[]> = {
      bullish: [
        {
          id: 'bull-call-spread',
          name: 'Bull Call Spread',
          description: 'Buy lower strike call, sell higher strike call. Limited risk, limited reward.',
          outlook: 'bullish',
          risk: 'low',
          maxProfit: 'Limited',
          maxLoss: 'Limited',
          legs: [
            { id: '1', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 },
            { id: '2', action: 'SELL', instrument: 'CE', expiry: '30 Dec', strike: 26500, quantity: 1, price: 50, lotSize: 50 }
          ]
        },
        {
          id: 'bull-put-spread',
          name: 'Bull Put Spread',
          description: 'Sell higher strike put, buy lower strike put. Collect premium with limited risk.',
          outlook: 'bullish',
          risk: 'medium',
          maxProfit: 'Premium Collected',
          maxLoss: 'Limited',
          legs: [
            { id: '1', action: 'SELL', instrument: 'PE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 100, lotSize: 50 },
            { id: '2', action: 'BUY', instrument: 'PE', expiry: '30 Dec', strike: 25500, quantity: 1, price: 30, lotSize: 50 }
          ]
        },
        {
          id: 'long-call',
          name: 'Long Call',
          description: 'Buy call option. Unlimited profit potential, limited risk.',
          outlook: 'bullish',
          risk: 'low',
          maxProfit: 'Unlimited',
          maxLoss: 'Premium Paid',
          legs: [
            { id: '1', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 }
          ]
        },
        {
          id: 'bull-condor',
          name: 'Bull Condor',
          description: 'Four-leg strategy with limited risk and profit. Profitable in moderate upward move.',
          outlook: 'bullish',
          risk: 'low',
          maxProfit: 'Limited',
          maxLoss: 'Limited',
          legs: [
            { id: '1', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 },
            { id: '2', action: 'SELL', instrument: 'CE', expiry: '30 Dec', strike: 26200, quantity: 1, price: 100, lotSize: 50 },
            { id: '3', action: 'SELL', instrument: 'CE', expiry: '30 Dec', strike: 26500, quantity: 1, price: 50, lotSize: 50 },
            { id: '4', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26700, quantity: 1, price: 20, lotSize: 50 }
          ]
        }
      ],
      bearish: [
        {
          id: 'bear-put-spread',
          name: 'Bear Put Spread',
          description: 'Buy higher strike put, sell lower strike put. Limited risk, limited reward.',
          outlook: 'bearish',
          risk: 'low',
          maxProfit: 'Limited',
          maxLoss: 'Limited',
          legs: [
            { id: '1', action: 'BUY', instrument: 'PE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 },
            { id: '2', action: 'SELL', instrument: 'PE', expiry: '30 Dec', strike: 25500, quantity: 1, price: 50, lotSize: 50 }
          ]
        },
        {
          id: 'long-put',
          name: 'Long Put',
          description: 'Buy put option. Unlimited profit potential, limited risk.',
          outlook: 'bearish',
          risk: 'low',
          maxProfit: 'Unlimited',
          maxLoss: 'Premium Paid',
          legs: [
            { id: '1', action: 'BUY', instrument: 'PE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 }
          ]
        },
        {
          id: 'bear-call-spread',
          name: 'Bear Call Spread',
          description: 'Sell lower strike call, buy higher strike call. Collect premium with limited risk.',
          outlook: 'bearish',
          risk: 'medium',
          maxProfit: 'Premium Collected',
          maxLoss: 'Limited',
          legs: [
            { id: '1', action: 'SELL', instrument: 'CE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 },
            { id: '2', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26500, quantity: 1, price: 50, lotSize: 50 }
          ]
        }
      ],
      neutral: [
        {
          id: 'iron-condor',
          name: 'Iron Condor',
          description: 'Four-leg strategy profitable in range-bound market. Limited risk and profit.',
          outlook: 'neutral',
          risk: 'low',
          maxProfit: 'Limited',
          maxLoss: 'Limited',
          legs: [
            { id: '1', action: 'SELL', instrument: 'CE', expiry: '30 Dec', strike: 26200, quantity: 1, price: 100, lotSize: 50 },
            { id: '2', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26500, quantity: 1, price: 50, lotSize: 50 },
            { id: '3', action: 'SELL', instrument: 'PE', expiry: '30 Dec', strike: 25800, quantity: 1, price: 100, lotSize: 50 },
            { id: '4', action: 'BUY', instrument: 'PE', expiry: '30 Dec', strike: 25500, quantity: 1, price: 50, lotSize: 50 }
          ]
        },
        {
          id: 'straddle',
          name: 'Long Straddle',
          description: 'Buy call and put at same strike. Profitable on large moves in either direction.',
          outlook: 'neutral',
          risk: 'medium',
          maxProfit: 'Unlimited',
          maxLoss: 'Total Premium',
          legs: [
            { id: '1', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 },
            { id: '2', action: 'BUY', instrument: 'PE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 }
          ]
        },
        {
          id: 'strangle',
          name: 'Long Strangle',
          description: 'Buy OTM call and put. Lower cost than straddle, needs larger move.',
          outlook: 'neutral',
          risk: 'medium',
          maxProfit: 'Unlimited',
          maxLoss: 'Total Premium',
          legs: [
            { id: '1', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26500, quantity: 1, price: 50, lotSize: 50 },
            { id: '2', action: 'BUY', instrument: 'PE', expiry: '30 Dec', strike: 25500, quantity: 1, price: 50, lotSize: 50 }
          ]
        }
      ],
      volatile: [
        {
          id: 'straddle',
          name: 'Long Straddle',
          description: 'Buy call and put at same strike. Profitable on large volatility.',
          outlook: 'volatile',
          risk: 'medium',
          maxProfit: 'Unlimited',
          maxLoss: 'Total Premium',
          legs: [
            { id: '1', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 },
            { id: '2', action: 'BUY', instrument: 'PE', expiry: '30 Dec', strike: 26000, quantity: 1, price: 150, lotSize: 50 }
          ]
        },
        {
          id: 'butterfly',
          name: 'Long Butterfly',
          description: 'Three-leg strategy with limited risk. Profitable in narrow range.',
          outlook: 'volatile',
          risk: 'low',
          maxProfit: 'Limited',
          maxLoss: 'Limited',
          legs: [
            { id: '1', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 25800, quantity: 1, price: 200, lotSize: 50 },
            { id: '2', action: 'SELL', instrument: 'CE', expiry: '30 Dec', strike: 26000, quantity: 2, price: 150, lotSize: 50 },
            { id: '3', action: 'BUY', instrument: 'CE', expiry: '30 Dec', strike: 26200, quantity: 1, price: 100, lotSize: 50 }
          ]
        }
      ]
    };

    return baseStrategies[outlook] || [];
  };

  const handleStrategySelect = (strategy: SuggestedStrategy) => {
    const fullStrategy: Strategy = {
      name: strategy.name,
      description: strategy.description,
      legs: strategy.legs.map(leg => ({ ...leg, id: leg.id }))
    };
    onStrategySelect(fullStrategy);
  };

  const getOutlookIcon = (outlook: string) => {
    switch (outlook) {
      case 'bullish': return <TrendingUp className="w-4 h-4" />;
      case 'bearish': return <TrendingDown className="w-4 h-4" />;
      case 'neutral': return <ArrowLeftRight className="w-4 h-4" />;
      case 'volatile': return <Zap className="w-4 h-4" />;
      default: return <BookOpen className="w-4 h-4" />;
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-400 bg-green-400/20';
      case 'medium': return 'text-yellow-400 bg-yellow-400/20';
      case 'high': return 'text-red-400 bg-red-400/20';
      default: return 'text-gray-400 bg-gray-400/20';
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* Outlook Filter */}
      <div className="flex gap-2">
        {(['bullish', 'bearish', 'neutral', 'volatile'] as const).map((outlook) => (
          <button
            key={outlook}
            onClick={() => setSelectedOutlook(outlook)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
              selectedOutlook === outlook
                ? 'bg-blue-600 text-white'
                : 'bg-[#2a2e39] text-gray-400 hover:text-white'
            }`}
          >
            {getOutlookIcon(outlook)}
            {outlook.charAt(0).toUpperCase() + outlook.slice(1)}
          </button>
        ))}
      </div>

      {/* Strategies Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
          <p className="mt-2 text-gray-400">Loading strategies...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {strategies.map((strategy) => (
            <div
              key={strategy.id}
              onClick={() => handleStrategySelect(strategy)}
              className="bg-[#1a1d28] rounded-lg p-4 border border-gray-700 hover:border-blue-500 cursor-pointer transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-semibold text-lg">{strategy.name}</h4>
                <span className={`px-2 py-1 rounded text-xs ${getRiskColor(strategy.risk)}`}>
                  {strategy.risk}
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-4">{strategy.description}</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Max Profit:</span>
                  <span className="text-green-400 font-medium">{strategy.maxProfit}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Max Loss:</span>
                  <span className="text-red-400 font-medium">{strategy.maxLoss}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Legs:</span>
                  <span className="font-medium">{strategy.legs.length}</span>
                </div>
              </div>
              <button className="w-full mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium">
                Load Strategy
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SuggestedStrategies;

