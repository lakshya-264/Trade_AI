/**
 * Chart Export Component - Export charts to various formats
 */

import React, { useState } from 'react';
import { 
  ArrowDownTrayIcon,
  DocumentArrowDownIcon,
  PrinterIcon,
  ShareIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';

interface ChartExportProps {
  isOpen: boolean;
  onClose: () => void;
  chartData?: any;
  chartTitle?: string;
  className?: string;
}

const ChartExport: React.FC<ChartExportProps> = ({
  isOpen,
  onClose,
  chartData,
  chartTitle = "Chart",
  className = ""
}) => {
  const [exportFormat, setExportFormat] = useState<'png' | 'jpg' | 'pdf' | 'svg'>('png');
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In a real implementation, this would trigger the actual export
      console.log(`Exporting chart as ${exportFormat}`);
      
      // Close modal after export
      onClose();
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={cn(
        "bg-white rounded-lg shadow-xl max-w-md w-full mx-4",
        className
      )}>
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Export Chart</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as any)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="png">PNG Image</option>
              <option value="jpg">JPG Image</option>
              <option value="pdf">PDF Document</option>
              <option value="svg">SVG Vector</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Chart Title
            </label>
            <input
              type="text"
              value={chartTitle}
              readOnly
              className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
            >
              {isExporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  Export
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartExport;
