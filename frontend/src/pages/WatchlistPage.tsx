import React from 'react';
import { useNavigate } from 'react-router-dom';
import Watchlist from '../components/Watchlist';

const WatchlistPage: React.FC = () => {
  const navigate = useNavigate();

  const handleSymbolSelect = (symbol: string) => {
    navigate(`/comprehensive-trading-pro?symbol=${symbol}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900/20 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">My Watchlist</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage and monitor your favorite stocks</p>
        </div>
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl shadow-2xl p-6">
          <Watchlist onSymbolSelect={handleSymbolSelect} />
        </div>
      </div>
    </div>
  );
};

export default WatchlistPage;

