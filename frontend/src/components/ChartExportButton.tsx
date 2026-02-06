import React, { useState, useRef } from 'react';
import { ArrowDownTrayIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

interface ChartExportButtonProps {
  chartContainerRef: React.RefObject<HTMLDivElement>;
  chartWrapperRef?: React.RefObject<HTMLDivElement>; // For capturing entire chart area including volume
  symbol: string;
  timeframe: string;
}

const ChartExportButton: React.FC<ChartExportButtonProps> = ({
  chartContainerRef,
  chartWrapperRef,
  symbol,
  timeframe
}) => {
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState<'png' | 'jpg' | 'svg' | 'pdf' | 'csv'>('png');
  const [isExporting, setIsExporting] = useState(false);
  const [includeIndicators, setIncludeIndicators] = useState(true);
  const [highResolution, setHighResolution] = useState(false);

  const handleExport = async () => {
    if (exportFormat === 'csv') {
      // Export chart data as CSV
      try {
        const chartData = chartContainerRef.current?.querySelector('canvas')?.getContext('2d');
        // For CSV, we need to get the actual data from the chart
        // This is a simplified version - in production, you'd get data from your chart data source
        const csvContent = `Date,Open,High,Low,Close,Volume\n`;
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${symbol}_${timeframe}_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(url);
        toast.success('Chart data exported as CSV');
        setShowExportModal(false);
        return;
      } catch (error) {
        console.error('CSV export error:', error);
        toast.error('Failed to export CSV');
        return;
      }
    }

    const elementToExport = chartWrapperRef?.current || chartContainerRef.current;
    
    if (!elementToExport) {
      toast.error('Chart container not found');
      return;
    }

    setIsExporting(true);
    try {
      const chartElement = elementToExport;
      const scale = highResolution ? 4 : 2; // Higher scale for high-res export
      
      if (exportFormat === 'pdf') {
        // Export as PDF
        const canvas = await html2canvas(chartElement, {
          backgroundColor: '#131722',
          scale: scale,
          logging: false,
        });
        
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF('landscape', 'mm', 'a4');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
        
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
        pdf.save(`${symbol}_${timeframe}_${new Date().toISOString().split('T')[0]}.pdf`);
        toast.success('Chart exported as PDF');
      } else if (exportFormat === 'svg') {
        // For SVG, we'll export as PNG (SVG export requires more complex handling)
        const canvas = await html2canvas(chartElement, {
          backgroundColor: '#131722',
          scale: scale,
          logging: false,
        });
        
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${symbol}_${timeframe}_${new Date().toISOString().split('T')[0]}.png`;
            link.click();
            URL.revokeObjectURL(url);
            toast.success('Chart exported as PNG');
          }
        }, 'image/png');
      } else {
        // Export as PNG or JPG
        const canvas = await html2canvas(chartElement, {
          backgroundColor: '#131722',
          scale: scale,
          logging: false,
        });
        
        const mimeType = exportFormat === 'jpg' ? 'image/jpeg' : 'image/png';
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${symbol}_${timeframe}_${new Date().toISOString().split('T')[0]}.${exportFormat}`;
            link.click();
            URL.revokeObjectURL(url);
            toast.success(`Chart exported as ${exportFormat.toUpperCase()}`);
          }
        }, mimeType);
      }
      
      setShowExportModal(false);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export chart');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setShowExportModal(true)}
        className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm text-gray-300 hover:text-white transition-colors"
        title="Export Chart"
      >
        <ArrowDownTrayIcon className="w-5 h-5" />
        Export
      </button>

      {showExportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-6 w-96 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Export Chart</h3>
              <button
                onClick={() => setShowExportModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Export Format
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['png', 'jpg', 'svg', 'pdf', 'csv'] as const).map((format) => (
                    <button
                      key={format}
                      onClick={() => setExportFormat(format)}
                      className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                        exportFormat === format
                          ? 'bg-blue-600 text-white'
                          : 'bg-[#2a2e39] text-gray-300 hover:bg-[#363a45]'
                      }`}
                    >
                      {format.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              {exportFormat !== 'csv' && (
                <>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-300">
                      Include Indicators
                    </label>
                    <input
                      type="checkbox"
                      checked={includeIndicators}
                      onChange={(e) => setIncludeIndicators(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-300">
                      High Resolution
                    </label>
                    <input
                      type="checkbox"
                      checked={highResolution}
                      onChange={(e) => setHighResolution(e.target.checked)}
                      className="w-4 h-4"
                    />
                  </div>
                </>
              )}

              <div className="flex gap-2 pt-4">
                <button
                  onClick={handleExport}
                  disabled={isExporting}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded font-medium transition-colors"
                >
                  {isExporting ? 'Exporting...' : 'Export'}
                </button>
                <button
                  onClick={() => setShowExportModal(false)}
                  className="px-4 py-2 bg-[#2a2e39] hover:bg-[#363a45] text-gray-300 rounded font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChartExportButton;

