import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon,
  ChartBarIcon,
  BriefcaseIcon,
  ChartPieIcon,
  CogIcon,
  XMarkIcon,
  AcademicCapIcon,
  SignalIcon,
  BuildingOffice2Icon,
  CpuChipIcon,
  PresentationChartLineIcon,
  BeakerIcon,
  DocumentTextIcon,
  ServerIcon,
  BellIcon,
  ArrowDownTrayIcon,
  SwatchIcon,
  BoltIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../context/AuthContext';

interface MobileNavigationProps {
  isOpen: boolean;
  onClose: () => void;
}

const MobileNavigation: React.FC<MobileNavigationProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();

  const navigation = [
    // Keep this in sync with Sidebar routes for a consistent experience on mobile.
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Trading', href: '/trading', icon: ChartBarIcon },
    { name: 'Stocks', href: '/stocks', icon: BuildingOffice2Icon },
    { name: 'Unified AI', href: '/unified-ai', icon: CpuChipIcon },
    { name: 'Intelligent Trading', href: '/intelligent-trading', icon: SignalIcon },
    { name: 'Risk Management', href: '/risk-management', icon: ChartPieIcon },
    { name: 'Portfolio Allocation', href: '/portfolio-allocation', icon: BriefcaseIcon },
    { name: 'Education', href: '/education', icon: AcademicCapIcon },
    { name: 'Comprehensive Trading', href: '/comprehensive-trading-pro', icon: PresentationChartLineIcon },
    { name: 'Backtesting', href: '/backtesting', icon: BeakerIcon },
    { name: 'Research Reports', href: '/research-report', icon: DocumentTextIcon },
    { name: 'Monitoring', href: '/monitoring', icon: ServerIcon },
    { name: 'Notifications', href: '/notifications', icon: BellIcon },
    { name: 'Chart Export', href: '/chart-export', icon: ArrowDownTrayIcon },
    { name: 'Theme Customization', href: '/theme-customization', icon: SwatchIcon },
    { name: 'Performance Optimization', href: '/performance-optimization', icon: BoltIcon },
    { name: 'Settings', href: '/settings', icon: CogIcon },
  ];

  const isCurrentPath = (path: string) => {
    return location.pathname === path;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      
      {/* Navigation Panel */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Trader AI</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* User Info */}
          {isAuthenticated && user && (
            <div className="p-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {user.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{user.username}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Links */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={onClose}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isCurrentPath(item.href)
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            {isAuthenticated ? (
              <button
                onClick={() => {
                  logout();
                  onClose();
                }}
                className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Sign Out
              </button>
            ) : (
              <p className="text-sm text-gray-500 text-center">
                Please sign in to access all features
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileNavigation;
