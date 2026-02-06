import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Users,
  Zap,
  Database,
  Settings,
  Play,
  Pause,
  Square,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface DashboardMetrics {
  training_jobs: {
    total: number;
    running: number;
    completed: number;
    failed: number;
  };
  models: {
    total_models: number;
    deployed_models: number;
    model_types: Record<string, number>;
    deployment_environments: Record<string, number>;
    storage_usage_mb: number;
  };
  drift_detection: {
    recent_alerts: number;
  };
  ab_testing: {
    running_experiments: number;
  };
  system_health: string;
}

interface TrainingJob {
  job_id: string;
  model_id: string;
  model_version: string;
  job_type: string;
  status: string;
  started_at: string;
  completed_at?: string;
  training_duration_seconds?: number;
  progress: number;
  error_message?: string;
}

interface PerformanceMetric {
  id: number;
  model_id: string;
  model_version: string;
  evaluated_at: string;
  evaluation_type: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  total_return?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
}

interface ErrorSummary {
  total_errors: number;
  error_categories: Record<string, number>;
  recent_errors: Array<{
    job_id: string;
    model_id: string;
    error_message: string;
    error_category: string;
    failed_at: string;
  }>;
  period_days: number;
}

interface ErrorDetails {
  job_id: string;
  model_id: string;
  error_message: string;
  error_traceback?: string;
  error_category: string;
  suggested_actions: string[];
  failed_at: string;
  hyperparameters?: Record<string, any>;
}

interface DriftAlert {
  id: number;
  model_id: string;
  model_version: string;
  drift_score: number;
  drift_type: string;
  detected_at: string;
  status: string;
  severity: 'high' | 'medium' | 'low';
}

interface ABTestExperiment {
  experiment_id: string;
  name: string;
  status: string;
  started_at: string;
  ended_at?: string;
  duration_days?: number;
  control_model_id: string;
  treatment_model_id: string;
  primary_metric: string;
  winner?: string;
  statistical_significance?: boolean;
}

const MLDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trainingJobs, setTrainingJobs] = useState<TrainingJob[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetric[]>([]);
  const [driftAlerts, setDriftAlerts] = useState<DriftAlert[]>([]);
  const [abTests, setABTests] = useState<ABTestExperiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [selectedTab, setSelectedTab] = useState('training');
  const [errorSummary, setErrorSummary] = useState<ErrorSummary | null>(null);
  const [selectedError, setSelectedError] = useState<ErrorDetails | null>(null);
  const ws = useRef<WebSocket | null>(null);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch overview metrics
      const overviewResponse = await fetch('/api/v1/ml/dashboard/overview');
      const overviewData = await overviewResponse.json();
      setMetrics(overviewData.metrics);
      
      // Fetch training status
      const trainingResponse = await fetch('/api/v1/ml/dashboard/training/status');
      const trainingData = await trainingResponse.json();
      setTrainingJobs([...trainingData.running_jobs, ...trainingData.recent_completed]);
      
      // Fetch performance metrics
      const perfResponse = await fetch(`/api/v1/ml/dashboard/models/performance?days=${selectedTimeRange}`);
      const perfData = await perfResponse.json();
      setPerformanceMetrics(perfData.metrics);
      
      // Fetch drift alerts
      const driftResponse = await fetch(`/api/v1/ml/dashboard/drift/alerts?days=${selectedTimeRange}`);
      const driftData = await driftResponse.json();
      setDriftAlerts([...driftData.alerts.high, ...driftData.alerts.medium, ...driftData.alerts.low]);
      
      // Fetch A/B tests
      const abResponse = await fetch(`/api/v1/ml/dashboard/ab-testing/experiments?days=${selectedTimeRange}`);
      const abData = await abResponse.json();
      setABTests(abData.experiments);

      // Fetch error summary
      await fetchErrorSummary();
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // WebSocket connection for real-time updates
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ml/dashboard/ws`;
    
    ws.current = new WebSocket(wsUrl);
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'metrics_update') {
        // Update metrics with real-time data
        setMetrics(prev => prev ? { ...prev, ...data.data } : null);
      }
    };
    
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    fetchDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    
    return () => clearInterval(interval);
  }, [selectedTimeRange]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-500';
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      case 'pending': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'resource': return 'bg-orange-100 text-orange-800';
      case 'data': return 'bg-yellow-100 text-yellow-800';
      case 'hyperparameter': return 'bg-purple-100 text-purple-800';
      case 'infrastructure': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const fetchErrorSummary = async () => {
    try {
      const response = await fetch('/api/v1/ml/dashboard/training/errors/summary');
      const data = await response.json();
      setErrorSummary(data);
    } catch (error) {
      console.error('Failed to fetch error summary:', error);
    }
  };

  const investigateError = async (jobId: string) => {
    try {
      const response = await fetch(`/api/v1/ml/dashboard/training/errors/${jobId}`);
      const data = await response.json();
      setSelectedError(data);
    } catch (error) {
      console.error('Failed to investigate error:', error);
    }
  };

  const retryJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/v1/ml/dashboard/training/${jobId}/retry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ learning_rate: 0.0005, batch_size: 16 })
      });
      const data = await response.json();
      console.log('Job retry initiated:', data);
      // Refresh data after retry
      fetchDashboardData();
      fetchErrorSummary();
    } catch (error) {
      console.error('Failed to retry job:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // Chart data preparation
  const trainingJobsChartData = metrics ? [
    { name: 'Running', value: metrics.training_jobs.running, color: '#3b82f6' },
    { name: 'Completed', value: metrics.training_jobs.completed, color: '#10b981' },
    { name: 'Failed', value: metrics.training_jobs.failed, color: '#ef4444' },
  ] : [];

  const modelTypesChartData = metrics?.models.model_types ? 
    Object.entries(metrics.models.model_types).map(([type, count]) => ({
      name: type,
      value: count,
    })) : [];

  const performanceChartData = performanceMetrics.slice(-10).map(metric => ({
    date: new Date(metric.evaluated_at).toLocaleDateString(),
    return: metric.total_return || 0,
    sharpe: metric.sharpe_ratio || 0,
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">ML Dashboard</h1>
          <p className="text-gray-600">Real-time monitoring of ML models and training</p>
        </div>
        <div className="flex items-center space-x-4">
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
            metrics?.system_health === 'healthy' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            <Activity className="w-4 h-4 mr-1" />
            {metrics?.system_health || 'Unknown'}
          </span>
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-3 py-1 border rounded"
          >
            <option value="1">Last 24 hours</option>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="text-sm font-medium">Training Jobs</h3>
            <Zap className="h-4 w-4 text-gray-500" />
          </div>
          <div>
            <div className="text-2xl font-bold">{metrics?.training_jobs.total || 0}</div>
            <p className="text-xs text-gray-600">
              {metrics?.training_jobs.running || 0} running
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="text-sm font-medium">Models</h3>
            <Database className="h-4 w-4 text-gray-500" />
          </div>
          <div>
            <div className="text-2xl font-bold">{metrics?.models.total_models || 0}</div>
            <p className="text-xs text-gray-600">
              {metrics?.models.deployed_models || 0} deployed
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="text-sm font-medium">Drift Alerts</h3>
            <AlertTriangle className="h-4 w-4 text-gray-500" />
          </div>
          <div>
            <div className="text-2xl font-bold">{metrics?.drift_detection.recent_alerts || 0}</div>
            <p className="text-xs text-gray-600">Last 7 days</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="text-sm font-medium">A/B Tests</h3>
            <Users className="h-4 w-4 text-gray-500" />
          </div>
          <div>
            <div className="text-2xl font-bold">{metrics?.ab_testing.running_experiments || 0}</div>
            <p className="text-xs text-gray-600">Running experiments</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-4">
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList>
            <TabsTrigger value="training">Training Jobs</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="drift">Drift Detection</TabsTrigger>
            <TabsTrigger value="abtesting">A/B Testing</TabsTrigger>
            <TabsTrigger value="errors">Error Investigation</TabsTrigger>
          </TabsList>

          {/* Training Jobs Tab */}
          <TabsContent value="training">
          <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Training Job Status</h3>
                </div>
                <div>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={trainingJobsChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {trainingJobsChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Recent Training Jobs</h3>
                </div>
                <div className="space-y-3">
                  {trainingJobs.slice(0, 5).map((job) => (
                    <div key={job.job_id} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex-1">
                        <div className="font-medium">{job.model_id}</div>
                        <div className="text-sm text-gray-600">{job.job_type}</div>
                        {job.status === 'running' && (
                          <div className="mt-2">
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${job.progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(job.status)}`}>
                          {job.status}
                        </span>
                        {job.status === 'running' && (
                          <button className="p-1 border rounded hover:bg-gray-100">
                            <Square className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance">
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="mb-4">
                <h3 className="text-lg font-medium">Model Performance Over Time</h3>
              </div>
              <div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="return" stroke="#3b82f6" name="Return" />
                  <Line type="monotone" dataKey="sharpe" stroke="#10b981" name="Sharpe Ratio" />
                </LineChart>
              </ResponsiveContainer>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Model Types Distribution</h3>
                </div>
                <div>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={modelTypesChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Latest Performance Metrics</h3>
                </div>
                <div className="space-y-3">
                  {performanceMetrics.slice(-5).reverse().map((metric) => (
                    <div key={metric.id} className="p-3 border rounded">
                      <div className="font-medium">{metric.model_id}</div>
                      <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                        <div>
                          <span className="text-gray-600">Return:</span>
                          <span className="ml-1">{(metric.total_return || 0).toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Sharpe:</span>
                          <span className="ml-1">{(metric.sharpe_ratio || 0).toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Drawdown:</span>
                          <span className="ml-1">{(metric.max_drawdown || 0).toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Win Rate:</span>
                          <span className="ml-1">{(metric.win_rate || 0).toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

          {/* Drift Detection Tab */}
          <TabsContent value="drift">
          <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Recent Drift Alerts</h3>
                </div>
                <div className="space-y-3">
                  {driftAlerts.slice(0, 10).map((alert) => (
                    <div key={alert.id} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex-1">
                        <div className="font-medium">{alert.model_id}</div>
                        <div className="text-sm text-gray-600">
                          {alert.drift_type} - Score: {alert.drift_score.toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(alert.detected_at).toLocaleString()}
                        </div>
                      </div>
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Drift Summary</h3>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>High Severity Alerts</span>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                      {driftAlerts.filter(a => a.severity === 'high').length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Medium Severity Alerts</span>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                      {driftAlerts.filter(a => a.severity === 'medium').length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Low Severity Alerts</span>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      {driftAlerts.filter(a => a.severity === 'low').length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Total Alerts</span>
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {driftAlerts.length}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

          {/* A/B Testing Tab */}
          <TabsContent value="abtesting">
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="mb-4">
                <h3 className="text-lg font-medium">A/B Testing Experiments</h3>
              </div>
              <div className="space-y-3">
                {abTests.map((experiment) => (
                  <div key={experiment.experiment_id} className="p-4 border rounded">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-medium">{experiment.name}</div>
                        <div className="text-sm text-gray-600">{experiment.experiment_id}</div>
                      </div>
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(experiment.status)}`}>
                        {experiment.status}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Control:</span>
                        <span className="ml-1">{experiment.control_model_id}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Treatment:</span>
                        <span className="ml-1">{experiment.treatment_model_id}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Primary Metric:</span>
                        <span className="ml-1">{experiment.primary_metric}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Duration:</span>
                        <span className="ml-1">{experiment.duration_days || 'N/A'} days</span>
                      </div>
                    </div>
                    
                    {experiment.winner && (
                      <div className="mt-3 p-2 bg-green-50 rounded">
                        <div className="text-sm font-medium text-green-800">
                          Winner: {experiment.winner}
                        </div>
                        {experiment.statistical_significance && (
                          <div className="text-xs text-green-600">
                            Statistically significant
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

          {/* Error Investigation Tab */}
          <TabsContent value="errors">
          <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Error Summary</h3>
                  <p className="text-sm text-gray-600">Recent training errors by category</p>
                </div>
                <div className="space-y-2">
                  {errorSummary?.error_categories ? Object.entries(errorSummary.error_categories).map(([category, count]) => (
                    <div key={category} className="flex justify-between items-center">
                      <span className="text-sm capitalize">{category}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        count > 0 ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {count}
                      </span>
                    </div>
                  )) : (
                    <div className="text-sm text-gray-500">Loading error summary...</div>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Recent Errors</h3>
                  <p className="text-sm text-gray-600">Latest training job failures</p>
                </div>
                <div className="space-y-2">
                  {errorSummary?.recent_errors?.slice(0, 5).map((error) => (
                    <div key={error.job_id} className="border-l-4 border-red-400 pl-3 py-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="text-sm font-medium">{error.job_id}</div>
                          <div className="text-xs text-gray-600">{error.error_category}</div>
                          <div className="text-xs text-gray-500 truncate max-w-xs">
                            {error.error_message}
                          </div>
                        </div>
                        <button 
                          className="text-xs text-blue-600 hover:text-blue-800"
                          onClick={() => investigateError(error.job_id)}
                        >
                          Investigate
                        </button>
                      </div>
                    </div>
                  )) || (
                    <div className="text-sm text-gray-500">No recent errors found</div>
                  )}
                </div>
              </div>
            </div>

            {/* Error Details Modal */}
            {selectedError && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="mb-4">
                  <h3 className="text-lg font-medium">Error Investigation: {selectedError.job_id}</h3>
                  <div className="flex space-x-2 mt-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(selectedError.error_category)}`}>
                      {selectedError.error_category}
                    </span>
                    <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      {selectedError.model_id}
                    </span>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Error Message</h4>
                    <div className="bg-red-50 border border-red-200 rounded p-3">
                      <p className="text-sm text-red-800">{selectedError.error_message}</p>
                    </div>
                  </div>

                  {selectedError.error_traceback && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Error Traceback</h4>
                      <div className="bg-gray-50 border border-gray-200 rounded p-3">
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-auto max-h-40">
                          {selectedError.error_traceback}
                        </pre>
                      </div>
                    </div>
                  )}

                  {selectedError.suggested_actions && selectedError.suggested_actions.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Suggested Actions</h4>
                      <div className="space-y-2">
                        {selectedError.suggested_actions.map((action, index) => (
                          <div key={index} className="flex items-start space-x-2">
                            <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                            <span className="text-sm text-gray-600">{action}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex space-x-3 pt-4">
                    <button 
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                      onClick={() => retryJob(selectedError.job_id)}
                    >
                      Retry Job
                    </button>
                    <button 
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 text-sm"
                      onClick={() => setSelectedError(null)}
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default MLDashboard;
