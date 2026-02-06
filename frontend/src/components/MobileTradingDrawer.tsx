/**
 * Mobile Trading Drawer Component
 * Slide-out drawer for mobile devices containing all trading toolbar buttons
 */

import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface MobileTradingDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

const MobileTradingDrawer: React.FC<MobileTradingDrawerProps> = ({ isOpen, onClose, children }) => {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-50 lg:hidden"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-80 bg-[#1e222d] shadow-xl z-50 lg:hidden transform transition-transform duration-300 ease-in-out">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-[#2a2e39]">
            <h2 className="text-lg font-semibold text-white">Trading Tools</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-md text-gray-400 hover:text-white hover:bg-[#2a2e39] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Close drawer"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-2">
              {children}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default MobileTradingDrawer;

