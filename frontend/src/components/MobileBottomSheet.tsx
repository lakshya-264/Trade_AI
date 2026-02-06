/**
 * Mobile Bottom Sheet Component
 * Bottom sheet panel for mobile devices (similar to mobile app modals)
 */

import React, { useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface MobileBottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  maxHeight?: string;
}

const MobileBottomSheet: React.FC<MobileBottomSheetProps> = ({
  isOpen,
  onClose,
  title,
  children,
  maxHeight = '90vh'
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-50 lg:hidden"
        onClick={onClose}
      />
      
      {/* Bottom Sheet */}
      <div
        className={`fixed bottom-0 left-0 right-0 bg-[#1e222d] rounded-t-2xl shadow-2xl z-50 lg:hidden transform transition-transform duration-300 ease-out`}
        style={{ maxHeight }}
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-2">
          <div className="w-12 h-1 bg-gray-600 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-4 pb-4 border-b border-[#2a2e39]">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-md text-gray-400 hover:text-white hover:bg-[#2a2e39] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Close"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto" style={{ maxHeight: `calc(${maxHeight} - 80px)` }}>
          <div className="p-4">
            {children}
          </div>
        </div>
      </div>
    </>
  );
};

export default MobileBottomSheet;

