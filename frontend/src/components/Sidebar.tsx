import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  ChartBarIcon, 
  BriefcaseIcon, 
  CogIcon,
  XMarkIcon,
  UserIcon,
  AcademicCapIcon,
  LightBulbIcon,
  PresentationChartLineIcon,
  CpuChipIcon,
  SignalIcon,
  ShieldCheckIcon,
  BookOpenIcon,
  UsersIcon,
  ChartPieIcon,
  ServerIcon,
  BellIcon,
  ArrowDownTrayIcon,
  SwatchIcon,
  BoltIcon,
  PlayIcon,
  BuildingOffice2Icon,
  ChevronDownIcon,
  ChevronRightIcon,
  MapIcon,
  AdjustmentsVerticalIcon,
  CubeIcon,
  Squares2X2Icon,
  BeakerIcon,
  DocumentTextIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  const [expandedItems, setExpandedItems] = useState<string[]>(['Comprehensive Trading']);

  // Sub-navigation items for Comprehensive Trading
  const comprehensiveTradingSubItems = [
    { 
      name: 'Overview', 
      href: '/comprehensive-trading-pro', 
      icon: Squares2X2Icon,
      description: 'Main dashboard'
    },
    { 
      name: 'Trendlines', 
      href: '/comprehensive-trading-pro?tab=0', 
      icon: ChartBarIcon,
      description: 'Auto-detect trendlines'
    },
    { 
      name: 'Swing Points', 
      href: '/comprehensive-trading-pro?tab=1', 
      icon: MapIcon,
      description: 'HH/HL/LH/LL detection'
    },
    { 
      name: 'Market Structure', 
      href: '/comprehensive-trading-pro?tab=2', 
      icon: SignalIcon,
      description: 'BOS & CHoCH'
    },
    { 
      name: 'Support & Resistance', 
      href: '/comprehensive-trading-pro?tab=3', 
      icon: AdjustmentsVerticalIcon,
      description: 'Key price levels'
    },
    { 
      name: 'Supply & Demand', 
      href: '/comprehensive-trading-pro?tab=4', 
      icon: CubeIcon,
      description: 'Trading zones'
    },
    { 
      name: 'Multi-Timeframe', 
      href: '/comprehensive-trading-pro?tab=5', 
      icon: Squares2X2Icon,
      description: 'Synchronized charts'
    },
  ];

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Trading', href: '/trading', icon: ChartBarIcon },
    { name: 'Stocks', href: '/stocks', icon: BuildingOffice2Icon },
    { 
      name: 'Unified AI', 
      href: '/unified-ai', 
      icon: CpuChipIcon,
      badge: 'ENHANCED',
      badgeColor: 'bg-gradient-to-r from-blue-500 to-purple-600'
    },
    { name: 'Intelligent Trading', href: '/intelligent-trading', icon: SignalIcon },
    { name: 'Risk Management', href: '/risk-management', icon: ShieldCheckIcon },
    { name: 'Portfolio Allocation', href: '/portfolio-allocation', icon: ChartPieIcon },
    { name: 'ML Dashboard', href: '/ml-dashboard', icon: CpuChipIcon },
    { name: 'Education', href: '/education', icon: AcademicCapIcon },
    { 
      name: 'Comprehensive Trading', 
      href: '/comprehensive-trading-pro', 
      icon: PresentationChartLineIcon,
      hasSubItems: true,
      subItems: comprehensiveTradingSubItems
    },
    { 
      name: 'Consolidated Analysis', 
      href: '/consolidated-analysis/RELIANCE', 
      icon: ChartBarIcon,
      badge: 'ALL-IN-ONE',
      badgeColor: 'bg-gradient-to-r from-purple-500 to-pink-600'
    },
    { 
      name: 'Backtesting', 
      href: '/backtesting', 
      icon: BeakerIcon,
      badge: 'NEW',
      badgeColor: 'bg-gradient-to-r from-green-500 to-emerald-600'
    },
    { 
      name: 'Stock Screener', 
      href: '/screener', 
      icon: BuildingOffice2Icon,
      badge: 'ENHANCED',
      badgeColor: 'bg-gradient-to-r from-indigo-500 to-purple-600'
    },
    { 
      name: 'Research Reports', 
      href: '/research-report', 
      icon: DocumentTextIcon,
      badge: 'NEW',
      badgeColor: 'bg-gradient-to-r from-green-500 to-emerald-600'
    },
    { 
      name: 'FNO Trading', 
      href: '/fno-trading', 
      icon: ChartBarIcon,
      badge: 'F&O',
      badgeColor: 'bg-gradient-to-r from-purple-500 to-pink-600'
    },
    { 
      name: 'Intraday Trading', 
      href: '/intraday-trading', 
      icon: SignalIcon,
      badge: 'DAY',
      badgeColor: 'bg-gradient-to-r from-blue-500 to-cyan-600'
    },
    { 
      name: "Tomorrow's NIFTY Opening", 
      href: '/tomorrow-nifty-opening', 
      icon: ClockIcon,
      badge: 'NEW',
      badgeColor: 'bg-gradient-to-r from-indigo-500 to-purple-600'
    },
    { 
      name: 'Commodity Trading', 
      href: '/commodity-trading', 
      icon: ChartBarIcon,
      badge: 'GOLD',
      badgeColor: 'bg-gradient-to-r from-yellow-500 to-orange-600'
    },
    { 
      name: 'Nifty50 Signals', 
      href: '/nifty50-signals', 
      icon: ChartBarIcon,
      badge: '50',
      badgeColor: 'bg-gradient-to-r from-indigo-500 to-blue-600'
    },
    { 
      name: 'Real-time Trading', 
      href: '/realtime-trading', 
      icon: PlayIcon,
      badge: 'LIVE',
      badgeColor: 'bg-gradient-to-r from-green-500 to-emerald-600'
    },
    { 
      name: 'NSE Results', 
      href: '/nse-results', 
      icon: DocumentTextIcon,
      badge: 'NEW',
      badgeColor: 'bg-gradient-to-r from-emerald-500 to-green-600'
    },
    { name: 'Monitoring', href: '/monitoring', icon: ServerIcon },
    { name: 'Notifications', href: '/notifications', icon: BellIcon },
    { name: 'Chart Export', href: '/chart-export', icon: ArrowDownTrayIcon },
    { name: 'Theme Customization', href: '/theme-customization', icon: SwatchIcon },
    { name: 'Performance Optimization', href: '/performance-optimization', icon: BoltIcon },
    { name: 'Settings', href: '/settings', icon: CogIcon },
  ];

  const isActive = (href: string) => {
    return location.pathname === href || location.pathname + location.search === href;
  };

  const toggleExpanded = (itemName: string) => {
    setExpandedItems(prev => 
      prev.includes(itemName) 
        ? prev.filter(name => name !== itemName)
        : [...prev, itemName]
    );
  };

  return (
    <>
      {/* Mobile sidebar overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-gray-600 opacity-75"></div>
        </div>
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:inset-0
      `}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">T</span>
              </div>
            </div>
            <div className="ml-3">
              <h1 className="text-xl font-bold text-gray-900">Trader AI</h1>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-8 px-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
          <div className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isExpanded = expandedItems.includes(item.name);
              const isItemActive = isActive(item.href);

              return (
                <div key={item.name}>
                  {/* Main navigation item */}
                  <div className="flex items-center">
                    <Link
                      to={item.href}
                      onClick={(e) => {
                        if (item.hasSubItems) {
                          e.preventDefault();
                          toggleExpanded(item.name);
                        } else {
                          onClose();
                        }
                      }}
                      className={`
                        group flex items-center flex-1 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200
                        ${isItemActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                        }
                      `}
                    >
                      <Icon
                        className={`
                          mr-3 h-5 w-5 flex-shrink-0
                          ${isItemActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'}
                        `}
                      />
                      <span className="flex-1">{item.name}</span>
                      {(item as any).badge && (
                        <span className={`ml-2 px-2 py-0.5 text-xs font-bold text-white rounded-full ${(item as any).badgeColor || 'bg-green-500'}`}>
                          {(item as any).badge}
                        </span>
                      )}
                      {item.hasSubItems && (
                        <span className="ml-auto">
                          {isExpanded ? (
                            <ChevronDownIcon className="h-4 w-4 text-gray-400" />
                          ) : (
                            <ChevronRightIcon className="h-4 w-4 text-gray-400" />
                          )}
                        </span>
                      )}
                    </Link>
                  </div>

                  {/* Sub-items (expandable) */}
                  {item.hasSubItems && isExpanded && item.subItems && (
                    <div className="mt-1 ml-4 space-y-1 animate-in slide-in-from-top-2 duration-200">
                      {item.subItems.map((subItem: any) => {
                        const SubIcon = subItem.icon;
                        const isSubActive = isActive(subItem.href);
                        
                        return (
                          <Link
                            key={subItem.name}
                            to={subItem.href}
                            onClick={onClose}
                            className={`
                              group flex items-center px-3 py-2 text-sm rounded-lg transition-all duration-200
                              ${isSubActive
                                ? 'bg-blue-50 text-blue-600 border-l-2 border-blue-500'
                                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 border-l-2 border-transparent'
                              }
                            `}
                            title={subItem.description}
                          >
                            <SubIcon
                              className={`
                                mr-3 h-4 w-4 flex-shrink-0
                                ${isSubActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'}
                              `}
                            />
                            <span className="text-xs font-medium">{subItem.name}</span>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </nav>

        {/* User section */}
        <div className="absolute bottom-0 w-full p-4 border-t border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UserIcon className="h-8 w-8 text-gray-400" />
            </div>
            <div className="ml-3">
              {isAuthenticated && user ? (
                <>
                  <p className="text-sm font-medium text-gray-900">{user.username}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </>
              ) : (
                <>
                  <p className="text-sm font-medium text-gray-900">Not signed in</p>
                  <p className="text-xs text-gray-500">Please log in</p>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
