import React, { useState, useRef, useCallback } from 'react';
import {
  ArrowDownTrayIcon, DocumentArrowDownIcon, PhotoIcon,
  DocumentTextIcon, CogIcon, EyeIcon, PrinterIcon,
  ShareIcon, CloudArrowUpIcon, CheckCircleIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../LoadingSpinner';

// Types for Chart Export
interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mimeType: string;
  description: string;
  icon: React.ComponentType<any>;
  maxSize?: string;
}

interface ExportOptions {
  format: string;
  quality: 'low' | 'medium' | 'high' | 'ultra';
  resolution: 'standard' | 'hd' | '4k';
  includeIndicators: boolean;
  includeVolume: boolean;
  includePatterns: boolean;
  watermark: boolean;
  customTitle?: string;
  timeframe: string;
  period: number;
}

interface ExportHistory {
  id: string;
  symbol: string;
  format: string;
  timestamp: string;
  fileSize: string;
  downloadUrl: string;
  status: 'completed' | 'processing' | 'failed';
}

// Chart Export API Service
class ChartExportApiService {
  private baseUrl = '/api/charting';

  async exportChart(symbol: string, options: ExportOptions): Promise<any> {
    const params = new URLSearchParams({
      format: options.format,
      timeframe: options.timeframe,
      period: options.period.toString(),
      quality: options.quality,
      resolution: options.resolution,
      include_indicators: options.includeIndicators.toString(),
      include_volume: options.includeVolume.toString(),
      include_patterns: options.includePatterns.toString(),
      watermark: options.watermark.toString(),
      ...(options.customTitle && { custom_title: options.customTitle })
    });

    const response = await fetch(`${this.baseUrl}/export-chart/${symbol}?${params}`);
    if (!response.ok) throw new Error('Failed to export chart');
    return response.json();
  }

  async getExportHistory(): Promise<ExportHistory[]> {
    const response = await fetch(`${this.baseUrl}/export-history`);
    if (!response.ok) throw new Error('Failed to fetch export history');
    return response.json();
  }

  async downloadExport(exportId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/download-export/${exportId}`);
    if (!response.ok) throw new Error('Failed to download export');
    return response.blob();
  }

  async shareExport(exportId: string, shareOptions: { email?: string; message?: string }): Promise<void> {
    const response = await fetch(`${this.baseUrl}/share-export/${exportId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(shareOptions)
    });
    if (!response.ok) throw new Error('Failed to share export');
  }
}

const chartExportApi = new ChartExportApiService();

// Export Format Options
const exportFormats: ExportFormat[] = [
  {
    id: 'png',
    name: 'PNG Image',
    extension: 'png',
    mimeType: 'image/png',
    description: 'High-quality raster image, perfect for presentations',
    icon: PhotoIcon,
    maxSize: '50MB'
  },
  {
    id: 'jpg',
    name: 'JPEG Image',
    extension: 'jpg',
    mimeType: 'image/jpeg',
    description: 'Compressed image format, smaller file size',
    icon: PhotoIcon,
    maxSize: '25MB'
  },
  {
    id: 'svg',
    name: 'SVG Vector',
    extension: 'svg',
    mimeType: 'image/svg+xml',
    description: 'Scalable vector graphics, perfect for web use',
    icon: DocumentTextIcon,
    maxSize: '10MB'
  },
  {
    id: 'pdf',
    name: 'PDF Document',
    extension: 'pdf',
    mimeType: 'application/pdf',
    description: 'Portable document format, great for reports',
    icon: DocumentArrowDownIcon,
    maxSize: '100MB'
  },
  {
    id: 'csv',
    name: 'CSV Data',
    extension: 'csv',
    mimeType: 'text/csv',
    description: 'Raw chart data in spreadsheet format',
    icon: DocumentTextIcon,
    maxSize: '5MB'
  }
];

// Chart Export Component
const ChartExportDialog: React.FC<{
  symbol: string;
  isOpen: boolean;
  onClose: () => void;
  chartRef?: React.RefObject<HTMLDivElement>;
}> = ({ symbol, isOpen, onClose, chartRef }) => {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'png',
    quality: 'high',
    resolution: 'hd',
    includeIndicators: true,
    includeVolume: true,
    includePatterns: true,
    watermark: false,
    timeframe: '1D',
    period: 100
  });

  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportResult, setExportResult] = useState<any>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setExportProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setExportProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const result = await chartExportApi.exportChart(symbol, exportOptions);
      
      clearInterval(progressInterval);
      setExportProgress(100);
      setExportResult(result);
      
      toast.success(`Chart exported successfully as ${exportOptions.format.toUpperCase()}`);
      
      // Auto-download if available
      if (result.data?.download_url) {
        const link = document.createElement('a');
        link.href = result.data.download_url;
        link.download = `${symbol}_chart_${new Date().toISOString().split('T')[0]}.${exportOptions.format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

    } catch (error) {
      toast.error(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsExporting(false);
    }
  };

  const updateExportOption = <K extends keyof ExportOptions>(key: K, value: ExportOptions[K]) => {
    setExportOptions(prev => ({ ...prev, [key]: value }));
  };

  const selectedFormat = exportFormats.find(f => f.id === exportOptions.format);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Export Chart</h2>
            <p className="text-gray-600 dark:text-gray-300">Export {symbol} chart in various formats</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-6">
            {/* Format Selection */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Export Format</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {exportFormats.map((format) => (
                  <div
                    key={format.id}
                    onClick={() => updateExportOption('format', format.id)}
                    className={cn(
                      "p-4 border rounded-lg cursor-pointer transition-colors",
                      exportOptions.format === format.id
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                        : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                    )}
                  >
                    <div className="flex items-center mb-2">
                      <format.icon className="h-5 w-5 text-blue-500 mr-2" />
                      <h4 className="font-semibold">{format.name}</h4>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{format.description}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Max size: {format.maxSize}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quality & Resolution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Quality
                </label>
                <select
                  value={exportOptions.quality}
                  onChange={(e) => updateExportOption('quality', e.target.value as any)}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                >
                  <option value="low">Low (Fast)</option>
                  <option value="medium">Medium</option>
                  <option value="high">High (Recommended)</option>
                  <option value="ultra">Ultra (Slow)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Resolution
                </label>
                <select
                  value={exportOptions.resolution}
                  onChange={(e) => updateExportOption('resolution', e.target.value as any)}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                >
                  <option value="standard">Standard (1920x1080)</option>
                  <option value="hd">HD (2560x1440)</option>
                  <option value="4k">4K (3840x2160)</option>
                </select>
              </div>
            </div>

            {/* Chart Settings */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Chart Settings</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Include Technical Indicators
                  </label>
                  <input
                    type="checkbox"
                    checked={exportOptions.includeIndicators}
                    onChange={(e) => updateExportOption('includeIndicators', e.target.checked)}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Include Volume
                  </label>
                  <input
                    type="checkbox"
                    checked={exportOptions.includeVolume}
                    onChange={(e) => updateExportOption('includeVolume', e.target.checked)}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Include Pattern Recognition
                  </label>
                  <input
                    type="checkbox"
                    checked={exportOptions.includePatterns}
                    onChange={(e) => updateExportOption('includePatterns', e.target.checked)}
                    className="rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Add Watermark
                  </label>
                  <input
                    type="checkbox"
                    checked={exportOptions.watermark}
                    onChange={(e) => updateExportOption('watermark', e.target.checked)}
                    className="rounded"
                  />
                </div>
              </div>
            </div>

            {/* Timeframe & Period */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Timeframe
                </label>
                <select
                  value={exportOptions.timeframe}
                  onChange={(e) => updateExportOption('timeframe', e.target.value)}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                >
                  <option value="1m">1 Minute</option>
                  <option value="5m">5 Minutes</option>
                  <option value="15m">15 Minutes</option>
                  <option value="1h">1 Hour</option>
                  <option value="4h">4 Hours</option>
                  <option value="1D">1 Day</option>
                  <option value="1W">1 Week</option>
                  <option value="1M">1 Month</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Data Points
                </label>
                <input
                  type="number"
                  value={exportOptions.period}
                  onChange={(e) => updateExportOption('period', parseInt(e.target.value))}
                  min="10"
                  max="1000"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>

            {/* Custom Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Custom Title (Optional)
              </label>
              <input
                type="text"
                value={exportOptions.customTitle || ''}
                onChange={(e) => updateExportOption('customTitle', e.target.value)}
                placeholder={`${symbol} Chart Analysis`}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Export Progress */}
            {isExporting && (
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="flex items-center mb-2">
                  <LoadingSpinner />
                  <span className="ml-2 text-sm font-medium text-blue-700 dark:text-blue-300">
                    Exporting chart...
                  </span>
                </div>
                <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${exportProgress}%` }}
                  />
                </div>
                <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                  {exportProgress}% complete
                </p>
              </div>
            )}

            {/* Export Result */}
            {exportResult && (
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="flex items-center mb-2">
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                  <span className="text-sm font-medium text-green-700 dark:text-green-300">
                    Export completed successfully!
                  </span>
                </div>
                <p className="text-xs text-green-600 dark:text-green-400">
                  File size: {exportResult.data?.file_size || 'Unknown'}
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end space-x-2 p-6 border-t dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
          >
            {isExporting ? (
              <>
                <LoadingSpinner />
                <span className="ml-2">Exporting...</span>
              </>
            ) : (
              <>
                <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                Export Chart
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// Export History Component
const ExportHistory: React.FC = () => {
  const [history, setHistory] = useState<ExportHistory[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await chartExportApi.getExportHistory();
      setHistory(data);
    } catch (error) {
      toast.error('Failed to fetch export history');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchHistory();
  }, []);

  const handleDownload = async (exportItem: ExportHistory) => {
    try {
      const blob = await chartExportApi.downloadExport(exportItem.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${exportItem.symbol}_chart_${exportItem.timestamp}.${exportItem.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download export');
    }
  };

  const handleShare = async (exportItem: ExportHistory) => {
    try {
      await chartExportApi.shareExport(exportItem.id, {});
      toast.success('Export shared successfully');
    } catch (error) {
      toast.error('Failed to share export');
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Export History</h3>
        <button
          onClick={fetchHistory}
          className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-500"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-3">
          {history.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">
              No exports found. Export a chart to see it here.
            </p>
          ) : (
            history.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center">
                  <DocumentArrowDownIcon className="h-5 w-5 text-blue-500 mr-3" />
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {item.symbol} Chart
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {item.format.toUpperCase()} • {item.fileSize} • {new Date(item.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={cn(
                    "px-2 py-1 text-xs rounded-full",
                    item.status === 'completed' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                    item.status === 'processing' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                    "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                  )}>
                    {item.status}
                  </span>
                  {item.status === 'completed' && (
                    <>
                      <button
                        onClick={() => handleDownload(item)}
                        className="p-1 text-blue-500 hover:text-blue-700"
                        title="Download"
                      >
                        <ArrowDownTrayIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleShare(item)}
                        className="p-1 text-green-500 hover:text-green-700"
                        title="Share"
                      >
                        <ShareIcon className="h-4 w-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// Main Chart Export Features Component
const ChartExportFeatures: React.FC = () => {
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('RELIANCE');
  const chartRef = useRef<HTMLDivElement>(null);

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Chart Export Features</h1>
          <p className="text-gray-600 dark:text-gray-400">Export charts in multiple formats with custom options</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Enter Symbol (e.g., RELIANCE)"
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value.toUpperCase())}
              className="p-2 pl-10 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <CogIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          </div>
          <button
            onClick={() => setShowExportDialog(true)}
            className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Export Chart
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Export Options Preview */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Export Options</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {exportFormats.map((format) => (
                  <div key={format.id} className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <format.icon className="h-6 w-6 text-blue-500 mr-3" />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{format.name}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">{format.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Export History */}
          <ExportHistory />
        </div>

        {/* Chart Preview Area */}
        <div className="mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Chart Preview</h3>
          <div ref={chartRef} className="h-64 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
            <div className="text-center text-gray-500 dark:text-gray-400">
              <PhotoIcon className="h-12 w-12 mx-auto mb-2" />
              <p>Chart preview for {selectedSymbol}</p>
              <p className="text-sm">This is where the actual chart would be rendered</p>
            </div>
          </div>
        </div>
      </div>

      {/* Export Dialog */}
      <ChartExportDialog
        symbol={selectedSymbol}
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        chartRef={chartRef}
      />
    </div>
  );
};

export default ChartExportFeatures;
