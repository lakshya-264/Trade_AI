import React, { useState, useEffect, useCallback } from 'react';
import {
  ChartBarIcon, CpuChipIcon, ServerIcon, CircleStackIcon,
  ExclamationTriangleIcon, CheckCircleIcon, ClockIcon,
  ArrowTrendingUpIcon, ArrowTrendingDownIcon, EyeIcon,
  ArrowPathIcon, PauseIcon, PlayIcon, BellIcon, WifiIcon,
  SignalIcon, FireIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../LoadingSpinner';
import ErrorDisplay from '../ErrorDisplay';

// Types for Real-time Monitoring
interface SystemMetrics {
  timestamp: string;
  cpu: {
    usage: number;
    cores: number;
    temperature: number;
    load_average: number[];
  };
  memory: {
    total: number;
    used: number;
    free: number;
    cached: number;
    swap_total: number;
    swap_used: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    read_ops: number;
    write_ops: number;
    read_speed: number;
    write_speed: number;
  };
  network: {
    bytes_sent: number;
    bytes_received: number;
    packets_sent: number;
    packets_received: number;
    connections: number;
    latency: number;
  };
  processes: Array<{
    pid: number;
    name: string;
    cpu_percent: number;
    memory_percent: number;
    status: string;
  }>;
}

interface ServiceStatus {
  service_name: string;
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  uptime: number;
  last_check: string;
  response_time: number;
  error_rate: number;
  dependencies: string[];
  health_checks: Array<{
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message: string;
    last_check: string;
  }>;
  metrics: {
    requests_per_second: number;
    average_response_time: number;
    error_count: number;
    success_rate: number;
  };
}

interface DatabaseMetrics {
  connection_pool: {
    active_connections: number;
    idle_connections: number;
    max_connections: number;
    waiting_connections: number;
  };
  query_performance: {
    slow_queries: number;
    average_query_time: number;
    total_queries: number;
    cache_hit_rate: number;
  };
  storage: {
    database_size: number;
    table_sizes: Array<{
      table_name: string;
      size: number;
      row_count: number;
    }>;
    index_usage: Array<{
      index_name: string;
      usage_count: number;
      efficiency: number;
    }>;
  };
  replication: {
    lag: number;
    status: 'synced' | 'lagging' | 'error';
    last_sync: string;
  };
}

interface APIMetrics {
  endpoint: string;
  method: string;
  requests_count: number;
  average_response_time: number;
  error_rate: number;
  status_codes: Record<string, number>;
  last_request: string;
  peak_requests_per_minute: number;
}

interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  source: string;
  timestamp: string;
  status: 'active' | 'acknowledged' | 'resolved';
  acknowledged_by?: string;
  resolved_at?: string;
  tags: string[];
}

interface MonitoringDashboard {
  system_metrics: SystemMetrics;
  services: ServiceStatus[];
  database: DatabaseMetrics;
  api_metrics: APIMetrics[];
  alerts: Alert[];
  overall_health: 'healthy' | 'degraded' | 'critical';
  last_updated: string;
}

// Real-time Monitoring API Service
class RealTimeMonitoringApiService {
  private baseUrl = '/api/monitoring';
  private wsUrl = 'ws://localhost:8000/ws/monitoring';

  async getDashboardData(): Promise<MonitoringDashboard> {
    const response = await fetch(`${this.baseUrl}/dashboard`);
    if (!response.ok) throw new Error('Failed to fetch monitoring dashboard');
    return response.json();
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await fetch(`${this.baseUrl}/system-metrics`);
    if (!response.ok) throw new Error('Failed to fetch system metrics');
    return response.json();
  }

  async getServiceStatus(): Promise<ServiceStatus[]> {
    const response = await fetch(`${this.baseUrl}/services`);
    if (!response.ok) throw new Error('Failed to fetch service status');
    return response.json();
  }

  async getDatabaseMetrics(): Promise<DatabaseMetrics> {
    const response = await fetch(`${this.baseUrl}/database`);
    if (!response.ok) throw new Error('Failed to fetch database metrics');
    return response.json();
  }

  async getAPIMetrics(): Promise<APIMetrics[]> {
    const response = await fetch(`${this.baseUrl}/api-metrics`);
    if (!response.ok) throw new Error('Failed to fetch API metrics');
    return response.json();
  }

  async getAlerts(): Promise<Alert[]> {
    const response = await fetch(`${this.baseUrl}/alerts`);
    if (!response.ok) throw new Error('Failed to fetch alerts');
    return response.json();
  }

  async acknowledgeAlert(alertId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/alerts/${alertId}/acknowledge`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to acknowledge alert');
  }

  async resolveAlert(alertId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/alerts/${alertId}/resolve`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to resolve alert');
  }

  // WebSocket connection for real-time updates
  connectWebSocket(onMessage: (data: any) => void): WebSocket {
    const ws = new WebSocket(this.wsUrl);
    
    ws.onopen = () => {
      console.log('Monitoring WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    ws.onclose = () => {
      console.log('Monitoring WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('Monitoring WebSocket error:', error);
    };
    
    return ws;
  }
}

const monitoringApi = new RealTimeMonitoringApiService();

// System Metrics Component
const SystemMetricsCard: React.FC<{
  metrics: SystemMetrics;
  isLive: boolean;
}> = ({ metrics, isLive }) => {
  const getStatusColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return 'text-red-500';
    if (value >= thresholds.warning) return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <div className="space-y-6">
      {/* CPU Metrics */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <CpuChipIcon className="h-6 w-6 text-blue-500 mr-2" />
            <h3 className="text-lg font-semibold">CPU Usage</h3>
          </div>
          <div className="flex items-center">
            <div className={cn(
              "w-2 h-2 rounded-full mr-2",
              isLive ? "bg-green-500 animate-pulse" : "bg-gray-400"
            )} />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {isLive ? 'Live' : 'Paused'}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className={cn(
              "text-2xl font-bold",
              getStatusColor(metrics.cpu.usage, { warning: 70, critical: 90 })
            )}>
              {metrics.cpu.usage.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Usage</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {metrics.cpu.cores}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Cores</div>
          </div>
          <div className="text-center">
            <div className={cn(
              "text-2xl font-bold",
              getStatusColor(metrics.cpu.temperature, { warning: 70, critical: 85 })
            )}>
              {metrics.cpu.temperature}°C
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Temperature</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {metrics.cpu.load_average[0].toFixed(2)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Load (1m)</div>
          </div>
        </div>

        <div className="mt-4">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={cn(
                "h-2 rounded-full transition-all duration-300",
                metrics.cpu.usage >= 90 ? "bg-red-500" :
                metrics.cpu.usage >= 70 ? "bg-yellow-500" : "bg-green-500"
              )}
              style={{ width: `${metrics.cpu.usage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Memory Metrics */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <ServerIcon className="h-6 w-6 text-green-500 mr-2" />
          <h3 className="text-lg font-semibold">Memory Usage</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(metrics.memory.used / 1024 / 1024 / 1024).toFixed(1)} GB
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Used</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(metrics.memory.free / 1024 / 1024 / 1024).toFixed(1)} GB
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Free</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(metrics.memory.total / 1024 / 1024 / 1024).toFixed(1)} GB
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total</div>
          </div>
        </div>

        <div className="mt-4">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={cn(
                "h-2 rounded-full transition-all duration-300",
                (metrics.memory.used / metrics.memory.total) >= 0.9 ? "bg-red-500" :
                (metrics.memory.used / metrics.memory.total) >= 0.7 ? "bg-yellow-500" : "bg-green-500"
              )}
              style={{ width: `${(metrics.memory.used / metrics.memory.total) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Network Metrics */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <WifiIcon className="h-6 w-6 text-purple-500 mr-2" />
          <h3 className="text-lg font-semibold">Network Activity</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(metrics.network.bytes_sent / 1024 / 1024).toFixed(1)} MB
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Sent</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {(metrics.network.bytes_received / 1024 / 1024).toFixed(1)} MB
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Received</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {metrics.network.connections}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Connections</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {metrics.network.latency}ms
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Latency</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Service Status Component
const ServiceStatusCard: React.FC<{
  services: ServiceStatus[];
}> = ({ services }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'down':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'down':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center mb-4">
        <ServerIcon className="h-6 w-6 text-blue-500 mr-2" />
        <h3 className="text-lg font-semibold">Service Status</h3>
      </div>

      <div className="space-y-3">
        {services.map((service) => (
          <div key={service.service_name} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center">
              {getStatusIcon(service.status)}
              <div className="ml-3">
                <div className="font-medium text-gray-900 dark:text-white">{service.service_name}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Uptime: {Math.floor(service.uptime / 3600)}h {Math.floor((service.uptime % 3600) / 60)}m
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm font-medium">{service.response_time}ms</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Response Time</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium">{service.metrics.success_rate.toFixed(1)}%</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Success Rate</div>
              </div>
              <span className={cn("px-2 py-1 text-xs rounded-full", getStatusColor(service.status))}>
                {service.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Database Metrics Component
const DatabaseMetricsCard: React.FC<{
  database: DatabaseMetrics;
}> = ({ database }) => {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center mb-4">
        <CircleStackIcon className="h-6 w-6 text-green-500 mr-2" />
        <h3 className="text-lg font-semibold">Database Metrics</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-medium mb-3">Connection Pool</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Active</span>
              <span className="font-medium">{database.connection_pool.active_connections}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Idle</span>
              <span className="font-medium">{database.connection_pool.idle_connections}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Max</span>
              <span className="font-medium">{database.connection_pool.max_connections}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Waiting</span>
              <span className="font-medium">{database.connection_pool.waiting_connections}</span>
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-medium mb-3">Query Performance</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Slow Queries</span>
              <span className="font-medium">{database.query_performance.slow_queries}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Avg Query Time</span>
              <span className="font-medium">{database.query_performance.average_query_time.toFixed(2)}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Total Queries</span>
              <span className="font-medium">{database.query_performance.total_queries}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Cache Hit Rate</span>
              <span className="font-medium">{database.query_performance.cache_hit_rate.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <h4 className="font-medium mb-3">Replication Status</h4>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={cn(
              "w-2 h-2 rounded-full mr-2",
              database.replication.status === 'synced' ? "bg-green-500" :
              database.replication.status === 'lagging' ? "bg-yellow-500" : "bg-red-500"
            )} />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {database.replication.status === 'synced' ? 'Synced' :
               database.replication.status === 'lagging' ? 'Lagging' : 'Error'}
            </span>
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Lag: {database.replication.lag}ms
          </div>
        </div>
      </div>
    </div>
  );
};

// Alerts Component
const AlertsCard: React.FC<{
  alerts: Alert[];
  onAcknowledge: (alertId: string) => void;
  onResolve: (alertId: string) => void;
}> = ({ alerts, onAcknowledge, onResolve }) => {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <FireIcon className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <BellIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <BellIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'info':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <BellIcon className="h-6 w-6 text-red-500 mr-2" />
          <h3 className="text-lg font-semibold">Active Alerts</h3>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {alerts.filter(alert => alert.status === 'active').length} active
        </div>
      </div>

      <div className="space-y-3">
        {alerts.slice(0, 10).map((alert) => (
          <div key={alert.id} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex items-start">
                {getSeverityIcon(alert.severity)}
                <div className="ml-3">
                  <div className="font-medium text-gray-900 dark:text-white">{alert.title}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">{alert.description}</div>
                  <div className="flex items-center mt-2 space-x-4">
                    <span className={cn("px-2 py-1 text-xs rounded-full", getSeverityColor(alert.severity))}>
                      {alert.severity}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(alert.timestamp).toLocaleString()}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {alert.source}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex space-x-2">
                {alert.status === 'active' && (
                  <>
                    <button
                      onClick={() => onAcknowledge(alert.id)}
                      className="px-2 py-1 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600"
                    >
                      Ack
                    </button>
                    <button
                      onClick={() => onResolve(alert.id)}
                      className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
                    >
                      Resolve
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main Real-time Monitoring Dashboard Component
const RealTimeMonitoringDashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'system' | 'services' | 'database' | 'alerts'>('overview');
  const [dashboardData, setDashboardData] = useState<MonitoringDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await monitoringApi.getDashboardData();
      setDashboardData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (isLive) {
      const ws = monitoringApi.connectWebSocket((data) => {
        if (data.type === 'metrics_update') {
          setDashboardData(prev => prev ? { ...prev, ...data.payload } : null);
        } else if (data.type === 'alert') {
          setDashboardData(prev => prev ? {
            ...prev,
            alerts: [data.payload, ...prev.alerts]
          } : null);
        }
      });
      setWsConnection(ws);

      return () => {
        ws.close();
      };
    } else {
      if (wsConnection) {
        wsConnection.close();
        setWsConnection(null);
      }
    }
  }, [isLive]);

  // Auto-refresh when not using WebSocket
  useEffect(() => {
    if (!isLive) {
      const interval = setInterval(() => {
        fetchData();
      }, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);

      return () => {
        if (interval) clearInterval(interval);
      };
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }
  }, [isLive, fetchData]);

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await monitoringApi.acknowledgeAlert(alertId);
      toast.success('Alert acknowledged');
      fetchData(); // Refresh data
    } catch (error) {
      toast.error('Failed to acknowledge alert');
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      await monitoringApi.resolveAlert(alertId);
      toast.success('Alert resolved');
      fetchData(); // Refresh data
    } catch (error) {
      toast.error('Failed to resolve alert');
    }
  };

  const renderTabContent = () => {
    if (!dashboardData) return null;

    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* Overall Health Status */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Overall System Health</h3>
                <div className="flex items-center">
                  <div className={cn(
                    "w-3 h-3 rounded-full mr-2",
                    dashboardData.overall_health === 'healthy' ? "bg-green-500" :
                    dashboardData.overall_health === 'degraded' ? "bg-yellow-500" : "bg-red-500"
                  )} />
                  <span className={cn(
                    "font-medium",
                    dashboardData.overall_health === 'healthy' ? "text-green-600" :
                    dashboardData.overall_health === 'degraded' ? "text-yellow-600" : "text-red-600"
                  )}>
                    {dashboardData.overall_health.toUpperCase()}
                  </span>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {dashboardData.services.filter(s => s.status === 'healthy').length}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Healthy Services</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {dashboardData.alerts.filter(a => a.status === 'active').length}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Active Alerts</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {dashboardData.system_metrics.cpu.usage.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">CPU Usage</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {((dashboardData.system_metrics.memory.used / dashboardData.system_metrics.memory.total) * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Memory Usage</div>
                </div>
              </div>
            </div>

            {/* Quick Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SystemMetricsCard metrics={dashboardData.system_metrics} isLive={isLive} />
              <ServiceStatusCard services={dashboardData.services} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <DatabaseMetricsCard database={dashboardData.database} />
              <AlertsCard
                alerts={dashboardData.alerts}
                onAcknowledge={handleAcknowledgeAlert}
                onResolve={handleResolveAlert}
              />
            </div>
          </div>
        );

      case 'system':
        return <SystemMetricsCard metrics={dashboardData.system_metrics} isLive={isLive} />;

      case 'services':
        return <ServiceStatusCard services={dashboardData.services} />;

      case 'database':
        return <DatabaseMetricsCard database={dashboardData.database} />;

      case 'alerts':
        return (
          <AlertsCard
            alerts={dashboardData.alerts}
            onAcknowledge={handleAcknowledgeAlert}
            onResolve={handleResolveAlert}
          />
        );

      default:
        return null;
    }
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} />;
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Real-time Monitoring Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">Monitor system performance and health in real-time</p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsLive(!isLive)}
            className={cn(
              "flex items-center px-4 py-2 rounded-md transition-colors",
              isLive ? "bg-red-500 hover:bg-red-600 text-white" : "bg-green-500 hover:bg-green-600 text-white"
            )}
          >
            {isLive ? <PauseIcon className="h-4 w-4 mr-2" /> : <PlayIcon className="h-4 w-4 mr-2" />}
            {isLive ? 'Pause Live' : 'Go Live'}
          </button>
          <button
            onClick={fetchData}
            className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b dark:border-gray-700">
        {[
          { id: 'overview', name: 'Overview', icon: ChartBarIcon },
          { id: 'system', name: 'System', icon: CpuChipIcon },
          { id: 'services', name: 'Services', icon: ServerIcon },
          { id: 'database', name: 'Database', icon: CircleStackIcon },
          { id: 'alerts', name: 'Alerts', icon: BellIcon }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              "flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors",
              activeTab === tab.id
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
            )}
          >
            <tab.icon className="h-5 w-5 mr-2" />
            {tab.name}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {renderTabContent()}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between px-6 py-3 bg-gray-50 dark:bg-gray-800 border-t dark:border-gray-700">
        <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center">
            <div className={cn(
              "w-2 h-2 rounded-full mr-2",
              isLive ? "bg-green-500 animate-pulse" : "bg-gray-400"
            )} />
            {isLive ? 'Live Updates' : 'Paused'}
          </div>
          <div>
            Last Updated: {dashboardData ? new Date(dashboardData.last_updated).toLocaleTimeString() : 'Never'}
          </div>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {dashboardData && (
            <>
              {dashboardData.services.length} Services • {dashboardData.alerts.length} Alerts
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default RealTimeMonitoringDashboard;
