/**
 * Tabbed Analysis Panel - User Friendly Interface
 * Groups all analysis features in a clean tabbed interface
 */

import React, { useState, useEffect, useMemo, useCallback, ErrorInfo, Component, Suspense } from 'react';
import { Tab } from '@headlessui/react';
import { cn } from '../lib/utils';
import {
  ChartBarIcon,
  SignalIcon,
  AdjustmentsVerticalIcon,
  CubeIcon,
  MapIcon,
  Squares2X2Icon,
  BellAlertIcon,
  SparklesIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';

// Import analysis components
import TrendlineAnalysis from './TrendlineAnalysis';
import SwingPointAnalysis from './SwingPointAnalysis';
import MarketStructureAnalysis from './MarketStructureAnalysis';
import SupportResistanceAnalysis from './SupportResistanceAnalysis';
import SupplyDemandAnalysis from './SupplyDemandAnalysis';
import { MultiTimeframeTab } from './MultiTimeframeTab';
import { AlertManager } from './AlertManager';
import PatternRecognitionTab from './PatternRecognitionTab';
import TradingSignalsTab from './TradingSignalsTab';
import MarketFactorsPanel from './MarketFactorsPanel';
import VolumeAnalysisTab from './VolumeAnalysisTab';

// Error Boundary Component to prevent one tab from crashing all tabs
class TabErrorBoundary extends Component<
  { children: React.ReactNode; tabName: string },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode; tabName: string }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`Error in ${this.props.tabName} tab:`, error, errorInfo);
  }

  // Reset error state when tab changes (when children prop changes)
  componentDidUpdate(prevProps: { children: React.ReactNode; tabName: string }) {
    if (prevProps.tabName !== this.props.tabName && this.state.hasError) {
      this.setState({ hasError: false, error: null });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-red-800 font-semibold mb-2">Error loading {this.props.tabName}</h3>
          <p className="text-red-600 text-sm mb-2">{this.state.error?.message || 'Unknown error'}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

interface TabbedAnalysisPanelProps {
  symbol: string;
  chartData: any[] | { candles: any[] } | any;
  currentPrice?: number;
  defaultTabIndex?: number;
  refreshTrigger?: number;
  activeTabIndex?: number;
  onTabChange?: (index: number) => void;
  lastAnalysisTime?: Date | null;
  onTrendlinesDetected?: (data: any) => void;
  onSwingPointsDetected?: (data: any) => void;
  onStructureDetected?: (data: any) => void;
  onLevelsDetected?: (data: any) => void;
  onZonesDetected?: (data: any) => void;
  onManualRefresh?: () => void;
}

const TabbedAnalysisPanel: React.FC<TabbedAnalysisPanelProps> = ({
  symbol,
  chartData,
  currentPrice,
  defaultTabIndex = 0,
  refreshTrigger = 0,
  activeTabIndex: externalActiveTabIndex,
  onTabChange,
  lastAnalysisTime,
  onTrendlinesDetected,
  onSwingPointsDetected,
  onStructureDetected,
  onLevelsDetected,
  onZonesDetected,
  onManualRefresh
}) => {
  const [internalActiveTabIndex, setInternalActiveTabIndex] = useState(defaultTabIndex);
  const activeTabIndex = externalActiveTabIndex !== undefined ? externalActiveTabIndex : internalActiveTabIndex;
  const [swingPointsLoading, setSwingPointsLoading] = useState(false);
  const [tabChangeInProgress, setTabChangeInProgress] = useState(false);

  // Handle tab change - wrap in try-catch to prevent errors from blocking tab switching
  // Use useCallback to ensure stable reference and prevent rapid clicks
  const handleTabChange = useCallback((index: number) => {
    try {
      // Prevent switching to same tab (can cause issues)
      if (index === activeTabIndex) {
        return;
      }
      
      // Prevent rapid tab switching that can cause hangs
      if (tabChangeInProgress) {
        console.log('Tab change already in progress, skipping...');
        return;
      }
      
      setTabChangeInProgress(true);
      
      // Use requestAnimationFrame to ensure UI updates smoothly
      requestAnimationFrame(() => {
        setInternalActiveTabIndex(index);
        onTabChange?.(index);
        
        // Reset flag after a short delay to allow component to mount
        setTimeout(() => {
          setTabChangeInProgress(false);
        }, 300);
      });
    } catch (error) {
      console.error('Error switching tabs:', error);
      // Still update internal state even if callback fails
      setInternalActiveTabIndex(index);
      setTabChangeInProgress(false);
    }
  }, [activeTabIndex, onTabChange, tabChangeInProgress]);

  // Trigger refresh for visible tab when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger > 0) {
      // Only log - components will refresh manually via their buttons
      console.log(`🔄 Analysis refresh available for tab ${activeTabIndex}`);
    }
  }, [refreshTrigger, activeTabIndex]);
  
  // Memoize tabs configuration to prevent unnecessary re-renders
  // Only depend on stable values, not callback functions
  const tabsConfig = useMemo(() => {
    interface TabConfig {
      name: string;
      icon: React.ComponentType<{ className?: string }>;
      activeClass: string;
      component: React.ComponentType<any>;
      props: any;
      isLoading?: boolean;
    }

    return [
      {
        name: 'Trendlines',
        icon: ChartBarIcon,
        activeClass: 'bg-blue-600 text-white shadow ring-blue-500',
        component: TrendlineAnalysis,
        props: { onTrendlinesDetected }
      },
      {
        name: 'Swing Points',
        icon: MapIcon,
        activeClass: 'bg-purple-600 text-white shadow ring-purple-500',
        component: SwingPointAnalysis,
        props: { 
          onSwingPointsDetected,
          onLoadingStateChange: setSwingPointsLoading
        },
        isLoading: swingPointsLoading
      },
      {
        name: 'Market Structure',
        icon: SignalIcon,
        activeClass: 'bg-indigo-600 text-white shadow ring-indigo-500',
        component: MarketStructureAnalysis,
        props: { onStructureDetected }
      },
      {
        name: 'Support & Resistance',
        icon: AdjustmentsVerticalIcon,
        activeClass: 'bg-green-600 text-white shadow ring-green-500',
        component: SupportResistanceAnalysis,
        props: { onLevelsDetected }
      },
      {
        name: 'Supply & Demand',
        icon: CubeIcon,
        activeClass: 'bg-orange-600 text-white shadow ring-orange-500',
        component: SupplyDemandAnalysis,
        props: { onZonesDetected }
      },
      {
        name: 'Multi-Timeframe',
        icon: Squares2X2Icon,
        activeClass: 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow ring-purple-500',
        component: MultiTimeframeTab,
        props: {}
      },
      {
        name: 'Pattern Recognition',
        icon: SparklesIcon,
        activeClass: 'bg-purple-600 text-white shadow ring-purple-500',
        component: PatternRecognitionTab,
        props: {}
      },
      {
        name: 'Trading Signals',
        icon: SignalIcon,
        activeClass: 'bg-blue-600 text-white shadow ring-blue-500',
        component: TradingSignalsTab,
        props: { currentPrice }
      },
      {
        name: 'Alerts',
        icon: BellAlertIcon,
        activeClass: 'bg-yellow-600 text-white shadow ring-yellow-500',
        component: AlertManager,
        props: { currentPrice }
      },
      {
        name: 'Market Factors',
        icon: CurrencyDollarIcon,
        activeClass: 'bg-teal-600 text-white shadow ring-teal-500',
        component: MarketFactorsPanel,
        props: {}
      },
      {
        name: 'Volume Analysis',
        icon: ChartBarIcon,
        activeClass: 'bg-cyan-600 text-white shadow ring-cyan-500',
        component: VolumeAnalysisTab,
        props: {}
      }
    ] as TabConfig[];
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // Note: Callback functions (onTrendlinesDetected, etc.) are stable references from parent
    // and don't need to be in dependencies. Including them would cause unnecessary re-renders.
    // Only include values that actually change (currentPrice, swingPointsLoading)
  }, [currentPrice, swingPointsLoading]);
  
  // Use memoized tabs config
  const tabs = tabsConfig;

  return (
    <div className="w-full bg-[#1e222d] rounded-lg shadow-lg">
      {/* Analysis Status Indicator */}
      <div className="px-4 pt-3 pb-2 flex items-center justify-between text-xs border-b border-gray-700/50">
        {lastAnalysisTime ? (
          <>
            <div className="flex items-center gap-2 text-gray-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Analysis updated: {lastAnalysisTime.toLocaleTimeString()}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Manual refresh only</span>
              {onManualRefresh && (
                <button
                  onClick={onManualRefresh}
                  className="px-2 py-1 bg-blue-600/20 text-blue-400 border border-blue-600/30 rounded hover:bg-blue-600/30 text-xs flex items-center gap-1"
                  title="Refresh all analysis tabs"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh All
                </button>
              )}
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 text-gray-400">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span>Analysis not yet run - Click refresh in each tab</span>
            </div>
            {onManualRefresh && (
              <button
                onClick={onManualRefresh}
                className="px-2 py-1 bg-blue-600/20 text-blue-400 border border-blue-600/30 rounded hover:bg-blue-600/30 text-xs flex items-center gap-1"
                title="Refresh all analysis tabs"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh All
              </button>
            )}
          </>
        )}
      </div>
      <Tab.Group 
        selectedIndex={activeTabIndex} 
        onChange={handleTabChange}
      >
        <Tab.List className="flex space-x-1 bg-[#131722] p-1 rounded-t-lg">
          {tabs.map((tab) => (
            <Tab
              key={tab.name}
              className={({ selected }) =>
                cn(
                  'w-full py-2.5 text-sm font-medium leading-5',
                  'rounded-lg transition-all duration-200',
                  'flex items-center justify-center gap-2',
                  'focus:outline-none focus:ring-2 ring-offset-2 ring-offset-[#131722]',
                  'relative',
                  selected
                    ? tab.activeClass
                    : 'text-gray-400 hover:bg-[#2a2e39] hover:text-white'
                )
              }
            >
              {({ selected }) => (
                <>
                  <tab.icon className={cn('w-5 h-5', selected && 'animate-pulse')} />
                  {tab.name}
                  {tab.isLoading && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse border-2 border-white dark:border-[#131722]"></div>
                  )}
                </>
              )}
            </Tab>
          ))}
        </Tab.List>
        
        <Tab.Panels className="p-4">
          {tabs.map((tab, index) => {
            // Prepare chart data once
            const processedChartData = Array.isArray(chartData) ? chartData : (chartData?.candles || []);
            
            return (
              <Tab.Panel
                key={`${tab.name}-panel`}
                className={cn(
                  'rounded-lg p-3',
                  'focus:outline-none focus:ring-2 ring-offset-2 ring-offset-[#131722] ring-white/60'
                )}
              >
                <TabErrorBoundary 
                  key={`${tab.name}-boundary-${activeTabIndex}`} 
                  tabName={tab.name}
                >
                  <Suspense
                    fallback={
                      <div className="flex items-center justify-center py-12">
                        <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
                      </div>
                    }
                  >
                    <tab.component
                      key={`${tab.name}-${activeTabIndex}-${refreshTrigger}`}
                      symbol={symbol}
                      chartData={processedChartData}
                      className="bg-transparent"
                      {...tab.props}
                    />
                  </Suspense>
                </TabErrorBoundary>
              </Tab.Panel>
            );
          })}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
};

export default TabbedAnalysisPanel;
