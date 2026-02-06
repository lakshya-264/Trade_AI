/**
 * Clickable Symbol Component
 * Reusable component for making stock symbols clickable and redirectable
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';

interface ClickableSymbolProps {
  symbol: string;
  className?: string;
  showArrow?: boolean;
  variant?: 'default' | 'bold' | 'link';
  onClick?: (symbol: string) => void;
}

const ClickableSymbol: React.FC<ClickableSymbolProps> = ({
  symbol,
  className = '',
  showArrow = false,
  variant = 'default',
  onClick
}) => {
  const navigate = useNavigate();

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onClick) {
      onClick(symbol);
    } else {
      navigate(`/comprehensive-trading-pro?symbol=${symbol}`);
    }
  };

  const baseClasses = 'cursor-pointer transition-colors hover:underline';
  
  const variantClasses = {
    default: 'text-blue-400 hover:text-blue-300',
    bold: 'text-blue-400 hover:text-blue-300 font-bold',
    link: 'text-blue-500 hover:text-blue-400 font-semibold underline'
  };

  return (
    <span
      onClick={handleClick}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      title={`Click to view ${symbol} chart`}
    >
      {symbol}
      {showArrow && (
        <svg 
          className="inline-block w-3 h-3 ml-1" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      )}
    </span>
  );
};

export default ClickableSymbol;

