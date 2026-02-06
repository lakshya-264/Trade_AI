import React, { useState, useEffect, useMemo } from 'react';
import { 
  Bars3Icon, 
  BellIcon,
  WifiIcon,
  SignalSlashIcon,
  UserIcon
} from '@heroicons/react/24/outline';
import { useWebSocket } from '../context/WebSocketContext';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import LoginModal from './LoginModal';
import SearchBar from './SearchBar';
import MarketStatusIndicator from './MarketStatusIndicator';
import NetworkStatusIndicator from './NetworkStatusIndicator';
import MarketTicker from './MarketTicker';
import { MarketTickerLoadingState } from './LoadingStates';
import comprehensiveTradingApi from '../services/comprehensiveTradingApi';

interface HeaderProps {
  onMenuClick: () => void;
  onMobileMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, onMobileMenuClick }) => {
  const { isConnected } = useWebSocket();
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Debounced search
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchSuggestions([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      try {
        const response = await comprehensiveTradingApi.searchSymbols(searchQuery, 10);
        if (response.success && response.results) {
          setSearchSuggestions(response.results.map((r: any) => r.symbol));
        }
      } catch (error) {
        console.error('Search error:', error);
        setSearchSuggestions([]);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleSearch = (query: string) => {
    if (query.trim()) {
      // Navigate to Comprehensive Trading Pro with the symbol
      navigate(`/comprehensive-trading-pro?symbol=${query.toUpperCase()}`);
      setSearchQuery('');
      setSearchSuggestions([]);
    }
  };

  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
  };

  const handleSuggestionClick = (symbol: string) => {
    handleSearch(symbol);
  };

  const handleSearchClear = () => {
    setSearchQuery('');
    setSearchSuggestions([]);
  };

  return (
    <header className="bg-background shadow-sm border-b border-border">
      {/* Market Ticker */}
      <div className="bg-muted/30 border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <MarketTicker />
        </div>
      </div>
      
      {/* Main Header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left side */}
          <div className="flex items-center">
            {/* Mobile menu button */}
            <button
              onClick={onMobileMenuClick}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
            
            {/* Desktop menu button */}
            <button
              onClick={onMenuClick}
              className="hidden lg:block p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
            
            {/* Search bar */}
            <div className="hidden sm:block ml-4 w-60 sm:w-80">
              <SearchBar
                placeholder="Search stocks..."
                onSearch={handleSearch}
                onClear={handleSearchClear}
                suggestions={searchSuggestions}
                onSuggestionClick={handleSuggestionClick}
              />
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-2 sm:space-x-4">
            {/* Network Status - Hidden on mobile */}
            <div className="hidden lg:block">
              <NetworkStatusIndicator />
            </div>

            {/* Market Status - Hidden on mobile */}
            <div className="hidden xl:block">
              <MarketStatusIndicator />
            </div>

            {/* WebSocket Connection status - Compact on mobile */}
            <div className="flex items-center space-x-1 sm:space-x-2">
              {isConnected ? (
                <>
                  <WifiIcon className="h-4 w-4 sm:h-5 sm:w-5 text-green-500" />
                  <span className="hidden sm:inline text-sm text-green-600 font-medium">Live</span>
                </>
              ) : (
                <>
                  <SignalSlashIcon className="h-4 w-4 sm:h-5 sm:w-5 text-red-500" />
                  <span className="hidden sm:inline text-sm text-red-600 font-medium">Offline</span>
                </>
              )}
            </div>

            {/* Notifications - Hidden on mobile */}
            <button className="hidden sm:block p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
              <BellIcon className="h-6 w-6" />
            </button>

            {/* User menu */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              {isAuthenticated && user ? (
                <>
                  <div className="hidden sm:block text-right">
                    <p className="text-sm font-medium text-gray-900">{user.username}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                  <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {user.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    className="hidden sm:block px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsLoginModalOpen(true)}
                  className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                >
                  <UserIcon className="h-4 w-4" />
                  <span className="hidden sm:inline">Login</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Login Modal */}
      <LoginModal 
        isOpen={isLoginModalOpen} 
        onClose={() => setIsLoginModalOpen(false)} 
      />
    </header>
  );
};

export default Header;
