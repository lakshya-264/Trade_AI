/**
 * Dedicated Professional Backtesting Page
 * Complete backtesting platform with charts, metrics, and analysis
 */

import React, { useState, lazy, Suspense } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';

const EnhancedBacktesting = lazy(() => import('../components/EnhancedBacktesting'));

const BacktestingPage: React.FC = () => {
  const [selectedStock] = useState({ symbol: 'RELIANCE', name: 'Reliance Industries' });
  
  // Always use enhanced backtesting component
  return (
    <div className="min-h-screen bg-[#131722] text-white p-4 sm:p-6 lg:p-8">
      <h1 className="text-3xl font-bold mb-6 text-blue-400">Enhanced Backtesting Platform</h1>
      <Suspense fallback={<LoadingSpinner size="md" text="Loading Enhanced Backtesting..." />}>
        <EnhancedBacktesting symbol={selectedStock.symbol} />
      </Suspense>
    </div>
  );
};

export default BacktestingPage;
