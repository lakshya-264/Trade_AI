import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  CpuChipIcon, ChartBarIcon, ClockIcon, CircleStackIcon,
  ArrowPathIcon, ExclamationTriangleIcon, CheckCircleIcon,
  LightBulbIcon, CogIcon, EyeIcon, ServerIcon,
  BoltIcon, ShieldCheckIcon, GlobeAltIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../LoadingSpinner';

// Performance Metrics Types
interface PerformanceMetrics {
  apiResponseTime: number;
  renderTime: number;
  memoryUsage: number;
  bundleSize: number;
  cacheHitRate: number;
  errorRate: number;
  uptime: number;
  lastUpdated: string;
}

interface OptimizationSuggestion {
  id: string;
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  category: 'api' | 'ui' | 'memory' | 'network' | 'cache';
  effort: 'low' | 'medium' | 'high';
  estimatedImprovement: string;
  action: string;
  isApplied: boolean;
}

interface PerformanceConfig {
  enableCaching: boolean;
  enableCompression: boolean;
  enableLazyLoading: boolean;
  enablePrefetching: boolean;
  maxCacheSize: number;
  cacheExpiry: number;
  apiTimeout: number;
  retryAttempts: number;
  enableMonitoring: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
}

// Performance API Service
class PerformanceApiService {
  private baseUrl = '/api/performance';

  async getMetrics(): Promise<PerformanceMetrics> {
    const response = await fetch(`${this.baseUrl}/metrics`);
    if (!response.ok) throw new Error('Failed to fetch performance metrics');
    return response.json();
  }

  async getOptimizationSuggestions(): Promise<OptimizationSuggestion[]> {
    const response = await fetch(`${this.baseUrl}/suggestions`);
    if (!response.ok) throw new Error('Failed to fetch optimization suggestions');
    return response.json();
  }

  async applyOptimization(suggestionId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/apply-optimization/${suggestionId}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to apply optimization');
  }

  async getConfig(): Promise<PerformanceConfig> {
    const response = await fetch(`${this.baseUrl}/config`);
    if (!response.ok) throw new Error('Failed to fetch performance config');
    return response.json();
  }

  async updateConfig(config: Partial<PerformanceConfig>): Promise<void> {
    const response = await fetch(`${this.baseUrl}/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!response.ok) throw new Error('Failed to update performance config');
  }

  async clearCache(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/clear-cache`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to clear cache');
  }

  async runPerformanceTest(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/test`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to run performance test');
    return response.json();
  }
}

const performanceApi = new PerformanceApiService();

// Mock Data for Development
const mockMetrics: PerformanceMetrics = {
  apiResponseTime: 245,
  renderTime: 12,
  memoryUsage: 85.6,
  bundleSize: 2.4,
  cacheHitRate: 78.3,
  errorRate: 0.8,
  uptime: 99.7,
  lastUpdated: new Date().toISOString()
};

const mockSuggestions: OptimizationSuggestion[] = [
  {
    id: 'lazy-loading',
    title: 'Enable Lazy Loading',
    description: 'Load components only when needed to reduce initial bundle size',
    impact: 'high',
    category: 'ui',
    effort: 'low',
    estimatedImprovement: '30% faster initial load',
    action: 'Enable lazy loading for non-critical components',
    isApplied: false
  },
  {
    id: 'api-caching',
    title: 'Implement API Caching',
    description: 'Cache API responses to reduce server load and improve response times',
    impact: 'high',
    category: 'api',
    effort: 'medium',
    estimatedImprovement: '50% faster API responses',
    action: 'Implement Redis caching for frequently accessed data',
    isApplied: true
  },
  {
    id: 'image-optimization',
    title: 'Optimize Images',
    description: 'Compress and optimize images for faster loading',
    impact: 'medium',
    category: 'network',
    effort: 'low',
    estimatedImprovement: '25% faster image loading',
    action: 'Convert images to WebP format and implement responsive images',
    isApplied: false
  },
  {
    id: 'code-splitting',
    title: 'Implement Code Splitting',
    description: 'Split JavaScript bundles to load only necessary code',
    impact: 'high',
    category: 'ui',
    effort: 'medium',
    estimatedImprovement: '40% smaller initial bundle',
    action: 'Implement dynamic imports for route-based code splitting',
    isApplied: false
  },
  {
    id: 'database-indexing',
    title: 'Optimize Database Queries',
    description: 'Add indexes to frequently queried database columns',
    impact: 'high',
    category: 'api',
    effort: 'high',
    estimatedImprovement: '60% faster database queries',
    action: 'Add composite indexes on user_id and timestamp columns',
    isApplied: false
  }
];

// Performance Metrics Component
const PerformanceMetricsCard: React.FC<{ metrics: PerformanceMetrics }> = ({ metrics }) => {
  const getStatusColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return 'text-green-600';
    if (value <= thresholds.warning) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusIcon = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
    if (value <= thresholds.warning) return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />;
    return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />;
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Performance Metrics</h3>
        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
          <ClockIcon className="h-4 w-4 mr-1" />
          Last updated: {new Date(metrics.lastUpdated).toLocaleTimeString()}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            {getStatusIcon(metrics.apiResponseTime, { good: 200, warning: 500 })}
          </div>
          <div className={cn("text-2xl font-bold", getStatusColor(metrics.apiResponseTime, { good: 200, warning: 500 }))}>
            {metrics.apiResponseTime}ms
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">API Response</div>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            {getStatusIcon(metrics.renderTime, { good: 16, warning: 33 })}
          </div>
          <div className={cn("text-2xl font-bold", getStatusColor(metrics.renderTime, { good: 16, warning: 33 }))}>
            {metrics.renderTime}ms
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Render Time</div>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            {getStatusIcon(metrics.memoryUsage, { good: 70, warning: 85 })}
          </div>
          <div className={cn("text-2xl font-bold", getStatusColor(metrics.memoryUsage, { good: 70, warning: 85 }))}>
            {metrics.memoryUsage}%
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Memory Usage</div>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            {getStatusIcon(metrics.cacheHitRate, { good: 80, warning: 60 })}
          </div>
          <div className={cn("text-2xl font-bold", getStatusColor(metrics.cacheHitRate, { good: 80, warning: 60 }))}>
            {metrics.cacheHitRate}%
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Cache Hit Rate</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {metrics.bundleSize}MB
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Bundle Size</div>
        </div>

        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {metrics.errorRate}%
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Error Rate</div>
        </div>

        <div className="text-center">
          <div className="text-lg font-semibold text-green-600">
            {metrics.uptime}%
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Uptime</div>
        </div>

        <div className="text-center">
          <div className="text-lg font-semibold text-blue-600">
            {metrics.memoryUsage}MB
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Memory Used</div>
        </div>
      </div>
    </div>
  );
};

// Optimization Suggestions Component
const OptimizationSuggestions: React.FC<{ suggestions: OptimizationSuggestion[] }> = ({ suggestions }) => {
  const [applyingOptimization, setApplyingOptimization] = useState<string | null>(null);

  const handleApplyOptimization = async (suggestion: OptimizationSuggestion) => {
    setApplyingOptimization(suggestion.id);
    try {
      await performanceApi.applyOptimization(suggestion.id);
      toast.success(`Applied optimization: ${suggestion.title}`);
      // In a real app, you'd update the suggestions state here
    } catch (error) {
      toast.error(`Failed to apply optimization: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setApplyingOptimization(null);
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-200';
      case 'low': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-200';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'high': return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-200';
      case 'low': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-200';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Optimization Suggestions</h3>
        <LightBulbIcon className="h-5 w-5 text-yellow-500" />
      </div>

      <div className="space-y-4">
        {suggestions.map((suggestion) => (
          <div
            key={suggestion.id}
            className={cn(
              "p-4 border rounded-lg transition-all",
              suggestion.isApplied
                ? "border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-700"
                : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center mb-2">
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    {suggestion.title}
                  </h4>
                  {suggestion.isApplied && (
                    <CheckCircleIcon className="h-4 w-4 text-green-500 ml-2" />
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {suggestion.description}
                </p>
                <div className="flex items-center space-x-2 mb-3">
                  <span className={cn("px-2 py-1 text-xs rounded-full", getImpactColor(suggestion.impact))}>
                    {suggestion.impact} impact
                  </span>
                  <span className={cn("px-2 py-1 text-xs rounded-full", getEffortColor(suggestion.effort))}>
                    {suggestion.effort} effort
                  </span>
                  <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    {suggestion.category}
                  </span>
                </div>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">
                  Expected improvement: {suggestion.estimatedImprovement}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Action: {suggestion.action}
                </p>
              </div>
              {!suggestion.isApplied && (
                <button
                  onClick={() => handleApplyOptimization(suggestion)}
                  disabled={applyingOptimization === suggestion.id}
                  className="ml-4 px-3 py-1 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 disabled:opacity-50"
                >
                  {applyingOptimization === suggestion.id ? (
                    <LoadingSpinner />
                  ) : (
                    'Apply'
                  )}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Performance Configuration Component
const PerformanceConfig: React.FC = () => {
  const [config, setConfig] = useState<PerformanceConfig>({
    enableCaching: true,
    enableCompression: true,
    enableLazyLoading: false,
    enablePrefetching: true,
    maxCacheSize: 100,
    cacheExpiry: 3600,
    apiTimeout: 5000,
    retryAttempts: 3,
    enableMonitoring: true,
    logLevel: 'info'
  });

  const [saving, setSaving] = useState(false);

  const handleConfigChange = (key: keyof PerformanceConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      await performanceApi.updateConfig(config);
      toast.success('Performance configuration saved');
    } catch (error) {
      toast.error('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleClearCache = async () => {
    try {
      await performanceApi.clearCache();
      toast.success('Cache cleared successfully');
    } catch (error) {
      toast.error('Failed to clear cache');
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Performance Configuration</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleClearCache}
            className="px-3 py-1 bg-red-500 text-white rounded-md text-sm hover:bg-red-600"
          >
            Clear Cache
          </button>
          <button
            onClick={handleSaveConfig}
            disabled={saving}
            className="px-3 py-1 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 disabled:opacity-50"
          >
            {saving ? <LoadingSpinner /> : 'Save Config'}
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {/* Caching Options */}
        <div>
          <h4 className="font-medium mb-3">Caching</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enableCaching}
                onChange={(e) => handleConfigChange('enableCaching', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm">Enable caching</span>
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Max Cache Size (MB)</label>
                <input
                  type="number"
                  value={config.maxCacheSize}
                  onChange={(e) => handleConfigChange('maxCacheSize', parseInt(e.target.value))}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Cache Expiry (seconds)</label>
                <input
                  type="number"
                  value={config.cacheExpiry}
                  onChange={(e) => handleConfigChange('cacheExpiry', parseInt(e.target.value))}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Performance Options */}
        <div>
          <h4 className="font-medium mb-3">Performance</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enableCompression}
                onChange={(e) => handleConfigChange('enableCompression', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm">Enable compression</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enableLazyLoading}
                onChange={(e) => handleConfigChange('enableLazyLoading', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm">Enable lazy loading</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enablePrefetching}
                onChange={(e) => handleConfigChange('enablePrefetching', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm">Enable prefetching</span>
            </label>
          </div>
        </div>

        {/* API Options */}
        <div>
          <h4 className="font-medium mb-3">API Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">API Timeout (ms)</label>
              <input
                type="number"
                value={config.apiTimeout}
                onChange={(e) => handleConfigChange('apiTimeout', parseInt(e.target.value))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Retry Attempts</label>
              <input
                type="number"
                value={config.retryAttempts}
                onChange={(e) => handleConfigChange('retryAttempts', parseInt(e.target.value))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Monitoring Options */}
        <div>
          <h4 className="font-medium mb-3">Monitoring</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enableMonitoring}
                onChange={(e) => handleConfigChange('enableMonitoring', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm">Enable performance monitoring</span>
            </label>
            <div>
              <label className="block text-sm font-medium mb-1">Log Level</label>
              <select
                value={config.logLevel}
                onChange={(e) => handleConfigChange('logLevel', e.target.value)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              >
                <option value="error">Error</option>
                <option value="warn">Warning</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Performance Optimization Component
const PerformanceOptimizationFeatures: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>(mockMetrics);
  const [suggestions, setSuggestions] = useState<OptimizationSuggestion[]>(mockSuggestions);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // In a real app, you'd fetch from the API
      // const [metricsData, suggestionsData] = await Promise.all([
      //   performanceApi.getMetrics(),
      //   performanceApi.getOptimizationSuggestions()
      // ]);
      // setMetrics(metricsData);
      // setSuggestions(suggestionsData);
      
      // For now, using mock data
      await new Promise(resolve => setTimeout(resolve, 500));
      setMetrics(mockMetrics);
      setSuggestions(mockSuggestions);
    } catch (error) {
      toast.error('Failed to fetch performance data');
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshMetrics = useCallback(async () => {
    setRefreshing(true);
    try {
      // In a real app: const metricsData = await performanceApi.getMetrics();
      await new Promise(resolve => setTimeout(resolve, 1000));
      setMetrics(prev => ({
        ...prev,
        lastUpdated: new Date().toISOString(),
        apiResponseTime: Math.floor(Math.random() * 100) + 200,
        renderTime: Math.floor(Math.random() * 10) + 10,
        memoryUsage: Math.floor(Math.random() * 20) + 70
      }));
    } catch (error) {
      toast.error('Failed to refresh metrics');
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Performance Optimization</h1>
          <p className="text-gray-600 dark:text-gray-400">Monitor and optimize application performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={refreshMetrics}
            disabled={refreshing}
            className="flex items-center px-3 py-1 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 disabled:opacity-50"
          >
            <ArrowPathIcon className={cn("h-4 w-4 mr-1", refreshing && "animate-spin")} />
            Refresh
          </button>
          <CpuChipIcon className="h-6 w-6 text-blue-500" />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="space-y-6">
            <PerformanceMetricsCard metrics={metrics} />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <OptimizationSuggestions suggestions={suggestions} />
              <PerformanceConfig />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceOptimizationFeatures;
