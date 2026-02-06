import React from 'react';

interface ArpitToolsProps {
  onClose: () => void;
}

const ArpitTools: React.FC<ArpitToolsProps> = ({ onClose }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Trading Tools</h2>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 transition-colors"
        >
          ✕
        </button>
      </div>
      <div className="space-y-4">
        <div className="p-4 bg-purple-50 rounded-lg">
          <h3 className="font-medium text-purple-900">Analysis Tools</h3>
          <p className="text-sm text-purple-700 mt-1">Trading tools and calculators will be available here.</p>
        </div>
      </div>
    </div>
  );
};

export default ArpitTools;
