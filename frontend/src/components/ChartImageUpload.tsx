/**
 * Chart Image Upload Component
 * Allows users to upload multiple chart images for analysis
 */

import React, { useState, useRef } from 'react';
import { PhotoIcon, XMarkIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { httpClient } from '../config/api';

interface ChartImageUploadProps {
  symbol: string;
  onAnalysisComplete?: (analysis: any) => void;
  className?: string;
}

const ChartImageUpload: React.FC<ChartImageUploadProps> = ({
  symbol,
  onAnalysisComplete,
  className = ''
}) => {
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
      toast.error('Please select valid image files (PNG, JPG, JPEG)');
      return;
    }
    
    // Limit to 10 images
    const filesToAdd = imageFiles.slice(0, 10 - selectedImages.length);
    
    if (filesToAdd.length < imageFiles.length) {
      toast.error('Maximum 10 images allowed. Only first 10 will be added.');
    }
    
    setSelectedImages(prev => [...prev, ...filesToAdd]);
    
    // Create previews
    filesToAdd.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviews(prev => [...prev, e.target?.result as string]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index: number) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedImages.length === 0) {
      toast.error('Please select at least one image');
      return;
    }
    
    setUploading(true);
    try {
      const formData = new FormData();
      selectedImages.forEach((file, index) => {
        formData.append('files', file);
      });
      
      // Use native fetch for file uploads (multipart/form-data)
      const apiUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('token');
      
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(
        `${apiUrl}/api/financial/research-report/${symbol}/analyze-chart-images`,
        {
          method: 'POST',
          headers,
          body: formData,
          // Don't set Content-Type header - browser will set it with boundary
        }
      );
      
      const responseData = await response.json();
      
      if (!response.ok) {
        throw new Error(responseData.detail || 'Failed to analyze images');
      }
      
      if (responseData.success && responseData.data) {
        setAnalysis(responseData.data);
        toast.success(`Successfully analyzed ${selectedImages.length} chart image(s)`);
        if (onAnalysisComplete) {
          onAnalysisComplete(responseData.data);
        }
      } else {
        toast.error(responseData.message || 'Failed to analyze images');
      }
      
    } catch (error: any) {
      console.error('Error uploading images:', error);
      toast.error(error.message || 'Failed to upload and analyze images');
    } finally {
      setUploading(false);
    }
  };

  const clearAll = () => {
    setSelectedImages([]);
    setPreviews([]);
    setAnalysis(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <PhotoIcon className="h-6 w-6 text-blue-600" />
          Upload Chart Images for Analysis
        </h3>
        {selectedImages.length > 0 && (
          <button
            onClick={clearAll}
            className="text-sm text-red-600 hover:text-red-700 dark:text-red-400"
          >
            Clear All
          </button>
        )}
      </div>
      
      <div className="mb-4">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="chart-image-upload"
        />
        <label
          htmlFor="chart-image-upload"
          className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
        >
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <ArrowUpTrayIcon className="w-10 h-10 mb-3 text-gray-400" />
            <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              PNG, JPG, JPEG, GIF, WEBP (MAX. 10 images)
            </p>
          </div>
        </label>
      </div>

      {selectedImages.length > 0 && (
        <div className="mb-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {previews.map((preview, index) => (
              <div key={index} className="relative group">
                <img
                  src={preview}
                  alt={`Chart ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg border border-gray-300 dark:border-gray-600"
                />
                <button
                  onClick={() => removeImage(index)}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
                <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
                  {selectedImages[index].name}
                </div>
              </div>
            ))}
          </div>
          
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Analyzing Images...
              </>
            ) : (
              <>
                <PhotoIcon className="h-5 w-5" />
                Analyze {selectedImages.length} Image(s)
              </>
            )}
          </button>
        </div>
      )}

      {analysis && (
        <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">
            Analysis Complete
          </h4>
          <p className="text-sm text-green-800 dark:text-green-200 mb-3">
            {analysis.summary?.summary_text || 'Chart images analyzed successfully'}
          </p>
          
          {analysis.detected_patterns && analysis.detected_patterns.length > 0 && (
            <div className="mb-3">
              <p className="text-xs font-semibold text-green-900 dark:text-green-100 mb-1">
                Detected Patterns:
              </p>
              <div className="flex flex-wrap gap-2">
                {analysis.detected_patterns.slice(0, 5).map((pattern: any, idx: number) => (
                  <span
                    key={idx}
                    className="text-xs px-2 py-1 bg-green-200 dark:bg-green-800 text-green-900 dark:text-green-100 rounded"
                  >
                    {pattern.pattern_name}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {analysis.overall_trend && analysis.overall_trend !== 'unknown' && (
            <p className="text-xs text-green-800 dark:text-green-200">
              Overall Trend: <span className="font-semibold">{analysis.overall_trend.toUpperCase()}</span>
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default ChartImageUpload;

