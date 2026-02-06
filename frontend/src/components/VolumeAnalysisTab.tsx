/**
 * Volume Analysis Tab Component
 * Dedicated tab for volume analysis, volume profile, and volume-based insights
 */

import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon,
  FireIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import comprehensiveTradingApi from '../services/comprehensiveTradingApi';
import { toast } from 'react-hot-toast';

interface VolumeAnalysisTabProps {
  symbol: string;
  chartData: any[];
  className?: string;
}

const VolumeAnalysisTab: React.FC<VolumeAnalysisTabProps> = ({
  symbol,
  chartData,
  className = ''
}) => {
  const [volumeProfile, setVolumeProfile] = useState<any>(null);
  const [volumeAnalysis, setVolumeAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1D');

  useEffect(() => {
    if (symbol && chartData && chartData.length > 0) {
      fetchVolumeAnalysis();
    }
  }, [symbol, selectedTimeframe]);

  const fetchVolumeAnalysis = async () => {
    setLoading(true);
    try {
      // Fetch volume profile
      const profileResponse = await comprehensiveTradingApi.getVolumeProfile({
        symbol,
        timeframe: selectedTimeframe,
        price_bins: 50
      });

      if (profileResponse.success) {
        setVolumeProfile(profileResponse.volume_profile);
      }

      // Fetch volume analysis
      const analysisResponse = await comprehensiveTradingApi.getOrderFlow({
        symbol,
        timeframe: selectedTimeframe
      });

      if (analysisResponse.success) {
        setVolumeAnalysis(analysisResponse.order_flow);
      }
    } catch (error: any) {
      console.error('Error fetching volume analysis:', error);
      toast.error('Failed to load volume analysis');
    } finally {
      setLoading(false);
    }
  };

  const calculateVolumeMetrics = () => {
    if (!chartData || chartData.length === 0) return null;

    const volumes = chartData.map((c: any) => c.volume || 0);
    const avgVolume = volumes.reduce((a: number, b: number) => a + b, 0) / volumes.length;
    const maxVolume = Math.max(...volumes);
    const currentVolume = volumes[volumes.length - 1] || 0;
    const volumeRatio = currentVolume / avgVolume;

    return {
      avgVolume,
      maxVolume,
      currentVolume,
      volumeRatio,
      isHighVolume: volumeRatio > 1.5,
      isLowVolume: volumeRatio < 0.5
    };
  };

  const volumeMetrics = calculateVolumeMetrics();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ChartBarIcon className="w-6 h-6 text-blue-400" />
          <h3 className="text-xl font-bold text-white">Volume Analysis</h3>
        </div>
        <select
          value={selectedTimeframe}
          onChange={(e) => setSelectedTimeframe(e.target.value)}
          className="px-3 py-2 bg-[#2a2e39] border border-[#363a45] rounded-lg text-white text-sm"
        >
          <option value="1D">Daily</option>
          <option value="1W">Weekly</option>
          <option value="1M">Monthly</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <>
          {/* Volume Metrics Cards */}
          {volumeMetrics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Average Volume</div>
                <div className="text-2xl font-bold text-white">
                  {volumeMetrics.avgVolume.toLocaleString()}
                </div>
              </div>
              <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Current Volume</div>
                <div className="text-2xl font-bold text-white">
                  {volumeMetrics.currentVolume.toLocaleString()}
                </div>
                <div className={`text-xs mt-1 ${
                  volumeMetrics.isHighVolume ? 'text-green-400' :
                  volumeMetrics.isLowVolume ? 'text-red-400' : 'text-gray-400'
                }`}>
                  {volumeMetrics.isHighVolume ? 'High Volume' :
                   volumeMetrics.isLowVolume ? 'Low Volume' : 'Normal'}
                </div>
              </div>
              <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Volume Ratio</div>
                <div className="text-2xl font-bold text-white">
                  {volumeMetrics.volumeRatio.toFixed(2)}x
                </div>
              </div>
              <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Max Volume</div>
                <div className="text-2xl font-bold text-white">
                  {volumeMetrics.maxVolume.toLocaleString()}
                </div>
              </div>
            </div>
          )}

          {/* Volume Profile */}
          {volumeProfile && (
            <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6">
              <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <FireIcon className="w-5 h-5 text-orange-400" />
                Volume Profile
              </h4>
              
              {volumeProfile.poc && (
                <div className="mb-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-gray-400">Point of Control (POC)</div>
                      <div className="text-xl font-bold text-blue-400">
                        ₹{volumeProfile.poc.price.toFixed(2)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">Volume</div>
                      <div className="text-lg font-semibold text-white">
                        {volumeProfile.poc.volume.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {volumeProfile.value_area && (
                <div className="mb-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="text-sm text-gray-400 mb-2">Value Area (70% Volume)</div>
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="text-xs text-gray-500">Low</div>
                      <div className="text-lg font-semibold text-green-400">
                        ₹{volumeProfile.value_area.low.toFixed(2)}
                      </div>
                    </div>
                    <div className="flex-1 h-1 bg-green-500/30 rounded"></div>
                    <div>
                      <div className="text-xs text-gray-500">High</div>
                      <div className="text-lg font-semibold text-green-400">
                        ₹{volumeProfile.value_area.high.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Volume Profile Visualization */}
              {volumeProfile.volume_profile && volumeProfile.volume_profile.length > 0 && (
                <div className="mt-4">
                  <div className="text-sm text-gray-400 mb-2">Volume Distribution</div>
                  <div className="space-y-1">
                    {volumeProfile.volume_profile
                      .sort((a: any, b: any) => b.volume - a.volume)
                      .slice(0, 10)
                      .map((vp: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-2">
                          <div className="w-20 text-xs text-gray-400 text-right">
                            ₹{vp.price.toFixed(2)}
                          </div>
                          <div className="flex-1 bg-[#131722] rounded h-6 relative overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                              style={{
                                width: `${(vp.volume / volumeProfile.poc.volume) * 100}%`
                              }}
                            />
                          </div>
                          <div className="w-24 text-xs text-gray-500 text-right">
                            {vp.volume.toLocaleString()}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Order Flow Analysis */}
          {volumeAnalysis && (
            <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6">
              <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <InformationCircleIcon className="w-5 h-5 text-purple-400" />
                Order Flow Analysis
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[#131722] rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">Average Imbalance</div>
                  <div className={`text-2xl font-bold ${
                    volumeAnalysis.average_imbalance > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {volumeAnalysis.average_imbalance > 0 ? '+' : ''}
                    {(volumeAnalysis.average_imbalance * 100).toFixed(2)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {volumeAnalysis.average_imbalance > 0 ? 'Buying Pressure' : 'Selling Pressure'}
                  </div>
                </div>

                <div className="bg-[#131722] rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">Total Imbalance</div>
                  <div className={`text-2xl font-bold ${
                    volumeAnalysis.total_imbalance > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {volumeAnalysis.total_imbalance > 0 ? '+' : ''}
                    {volumeAnalysis.total_imbalance.toFixed(2)}
                  </div>
                </div>

                <div className="bg-[#131722] rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-2">Order Flow Points</div>
                  <div className="text-2xl font-bold text-white">
                    {volumeAnalysis.order_flow?.length || 0}
                  </div>
                </div>
              </div>

              {/* Order Flow Chart */}
              {volumeAnalysis.order_flow && volumeAnalysis.order_flow.length > 0 && (
                <div className="mt-6">
                  <div className="text-sm text-gray-400 mb-2">Recent Order Flow</div>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {volumeAnalysis.order_flow.slice(-20).map((flow: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 bg-[#131722] rounded"
                      >
                        <div className="flex items-center gap-3">
                          {flow.imbalance > 0 ? (
                            <ArrowTrendingUpIcon className="w-4 h-4 text-green-400" />
                          ) : (
                            <ArrowTrendingDownIcon className="w-4 h-4 text-red-400" />
                          )}
                          <div>
                            <div className="text-sm text-white">
                              ₹{flow.price.toFixed(2)}
                            </div>
                            <div className="text-xs text-gray-500">
                              {new Date(flow.timestamp).toLocaleTimeString()}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`text-sm font-semibold ${
                            flow.imbalance > 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {flow.imbalance > 0 ? '+' : ''}{(flow.imbalance * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-500">
                            Vol: {flow.volume.toLocaleString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Volume Heat Map (Placeholder) */}
          <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6">
            <h4 className="text-lg font-semibold text-white mb-4">Volume Heat Map</h4>
            <div className="text-center py-12 text-gray-400">
              <ChartBarIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>Volume Heat Map visualization coming soon</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default VolumeAnalysisTab;

