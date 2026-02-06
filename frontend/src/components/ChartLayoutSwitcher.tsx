/**
 * Chart Layout Switcher Component
 * Allows users to switch between 1, 2, or 4 chart layouts
 */

import React from 'react';

export type ChartLayout = 1 | 2 | 4;

interface ChartLayoutSwitcherProps {
  layout: ChartLayout;
  onLayoutChange: (layout: ChartLayout) => void;
  className?: string;
}

export const ChartLayoutSwitcher: React.FC<ChartLayoutSwitcherProps> = ({
  layout,
  onLayoutChange,
  className = '',
}) => {
  const layouts: ChartLayout[] = [1, 2, 4];

  const getLayoutIcon = (layoutValue: ChartLayout): JSX.Element => {
    switch (layoutValue) {
      case 1:
        return (
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <rect x="2" y="2" width="20" height="20" rx="2" />
          </svg>
        );
      case 2:
        return (
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <rect x="2" y="2" width="9" height="20" rx="2" />
            <rect x="13" y="2" width="9" height="20" rx="2" />
          </svg>
        );
      case 4:
        return (
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <rect x="2" y="2" width="9" height="9" rx="2" />
            <rect x="13" y="2" width="9" height="9" rx="2" />
            <rect x="2" y="13" width="9" height="9" rx="2" />
            <rect x="13" y="13" width="9" height="9" rx="2" />
          </svg>
        );
    }
  };

  const getLayoutLabel = (layoutValue: ChartLayout): string => {
    switch (layoutValue) {
      case 1:
        return 'Single Chart';
      case 2:
        return '2 Charts';
      case 4:
        return '2x2 Grid';
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-sm text-gray-400 mr-2">Layout:</span>
      <div className="flex gap-1 bg-[#1e222d] rounded-lg p-1">
        {layouts.map((layoutValue) => (
          <button
            key={layoutValue}
            onClick={() => onLayoutChange(layoutValue)}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-md transition-all
              ${
                layout === layoutValue
                  ? 'bg-[#2962FF] text-white'
                  : 'text-gray-400 hover:text-white hover:bg-[#2a2e39]'
              }
            `}
            title={getLayoutLabel(layoutValue)}
          >
            {getLayoutIcon(layoutValue)}
            <span className="text-sm font-medium">{layoutValue}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ChartLayoutSwitcher;

