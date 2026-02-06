/**
 * Auto Trading Status Component
 * Displays real-time status of automated trading execution
 */

import React, { useState, useEffect } from 'react';
import { 
  Bot, Activity, Clock, CheckCircle, XCircle, AlertCircle, 
  TrendingUp, Pause, Play, RefreshCw, Info
} from 'lucide-react';
import { httpClient, API_CONFIG } from '../config/api';
import { toast } from 'react-hot-toast';

interface AutoTradingStatus {
  enabled: boolean;
  last_execution: string | null;
  next_execution: string | null;
  execution_count: number;
  last_result: {
    success: boolean;
    executed_trades: any[];
    portfolio_update: any;
    error?: string;
  } | null;
  time_until_next: {
    minutes: number;
    seconds: number;
  } | null;
  status_message: string;
  server_time: string;
  execution_interval: string;
  paper_trading: boolean;
  max_trades_per_execution: number;
  min_confidence_threshold: number;
  target_symbols: string;
}

export const AutoTradingStatus: React.FC = () => {
  const [status, setStatus] = useState<AutoTradingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStatus = async () => {
    try {
      const response = await httpClient.get('/api/auto-trading/public/status');
      if (response.success) {
        setStatus(response.data as AutoTradingStatus);
      }
    } catch (error) {
      console.error('Error fetching auto-trading status:', error);
      toast.error('Failed to fetch auto-trading status');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const toggleAutoTrading = async (enable: boolean) => {
    setToggling(true);
    try {
      const response = await httpClient.post(`/api/auto-trading/toggle?enable=${enable}`);
      if (response.success) {
        toast.success(`Auto-trading ${enable ? 'enabled' : 'disabled'}`);
        await fetchStatus();
      } else {
        toast.error(response.error || 'Failed to toggle auto-trading');
      }
    } catch (error) {
      console.error('Error toggling auto-trading:', error);
      toast.error('Failed to toggle auto-trading');
    } finally {
      setToggling(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Update countdown every second
    const countdownInterval = setInterval(() => {
      if (status?.time_until_next) {
        fetchStatus();
      }
    }, 1000);
    return () => clearInterval(countdownInterval);
  }, [status?.time_until_next]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
        <div className="flex items-center gap-3">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
          <span className="text-gray-600">Loading auto-trading status...</span>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
        <div className="flex items-center gap-3 text-red-600">
          <XCircle className="w-5 h-5" />
          <span>Unable to load auto-trading status</span>
        </div>
      </div>
    );
  }

  const getStatusColor = () => {
    if (!status.enabled) return 'bg-gray-100 border-gray-300 text-gray-600';
    if (status.last_result?.success) return 'bg-green-100 border-green-300 text-green-700';
    if (status.last_result && !status.last_result.success) return 'bg-red-100 border-red-300 text-red-700';
    return 'bg-blue-100 border-blue-300 text-blue-700';
  };

  const getStatusIcon = () => {
    if (!status.enabled) return <Pause className="w-4 h-4" />;
    if (status.last_result?.success) return <CheckCircle className="w-4 h-4" />;
    if (status.last_result && !status.last_result.success) return <XCircle className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Bot className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">Auto Trading Status</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchStatus()}
            disabled={refreshing}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            title="Refresh status"
          >
            <RefreshCw className={`w-4 h-4 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => toggleAutoTrading(!status.enabled)}
            disabled={toggling}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              status.enabled
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {toggling ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : status.enabled ? (
              <>
                <Pause className="w-4 h-4 inline mr-1" />
                Disable
              </>
            ) : (
              <>
                <Play className="w-4 h-4 inline mr-1" />
                Enable
              </>
            )}
          </button>
        </div>
      </div>

      {/* Status Indicator */}
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getStatusColor()} mb-4`}>
        {getStatusIcon()}
        <span className="font-medium">{status.status_message}</span>
      </div>

      {/* Status Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Status:</span>
            <span className={`font-medium ${status.enabled ? 'text-green-600' : 'text-gray-600'}`}>
              {status.enabled ? 'Active' : 'Disabled'}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Total Executions:</span>
            <span className="font-medium">{status.execution_count}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Execution Interval:</span>
            <span className="font-medium">{status.execution_interval}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Target Symbols:</span>
            <span className="font-medium">{status.target_symbols}</span>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Mode:</span>
            <span className={`font-medium ${status.paper_trading ? 'text-blue-600' : 'text-orange-600'}`}>
              {status.paper_trading ? 'Paper Trading' : 'Live Trading'}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Max Trades:</span>
            <span className="font-medium">{status.max_trades_per_execution}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Min Confidence:</span>
            <span className="font-medium">{(status.min_confidence_threshold * 100).toFixed(0)}%</span>
          </div>
          {status.time_until_next && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Next Execution:</span>
              <span className="font-medium text-blue-600">
                {status.time_until_next.minutes}m {status.time_until_next.seconds}s
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Last Execution Result */}
      {status.last_result && (
        <div className="border-t pt-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Last Execution</span>
            {status.last_execution && (
              <span className="text-xs text-gray-500">
                {new Date(status.last_execution).toLocaleString()}
              </span>
            )}
          </div>
          
          <div className={`p-3 rounded-lg ${
            status.last_result.success 
              ? 'bg-green-50 border border-green-200' 
              : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              {status.last_result.success ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <XCircle className="w-4 h-4 text-red-600" />
              )}
              <span className={`font-medium ${
                status.last_result.success ? 'text-green-700' : 'text-red-700'
              }`}>
                {status.last_result.success ? 'Success' : 'Failed'}
              </span>
            </div>
            
            {status.last_result.success && status.last_result.executed_trades.length > 0 && (
              <div className="text-sm text-gray-700">
                <span className="font-medium">Executed Trades:</span> {status.last_result.executed_trades.length}
                <div className="mt-1">
                  {status.last_result.executed_trades.map((trade, index) => (
                    <span key={index} className="inline-block bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs mr-1 mb-1">
                      {trade.symbol}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {status.last_result.error && (
              <div className="text-sm text-red-700">
                <span className="font-medium">Error:</span> {status.last_result.error}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">Auto Trading Information</p>
            <ul className="text-xs space-y-1">
              <li>• Executes Nifty 50 trades automatically every 30 minutes</li>
              <li>• Currently in {status.paper_trading ? 'paper trading' : 'live trading'} mode for safety</li>
              <li>• Only executes trades with {status.min_confidence_threshold * 100}%+ confidence</li>
              <li>• Maximum {status.max_trades_per_execution} trades per execution</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
