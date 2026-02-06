import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { ThemeProvider } from './context/ThemeContext';
import { EnhancedThemeProvider } from './components/theme/ThemeCustomizationFeatures';
import ErrorBoundary from './components/ErrorBoundary';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import MobileNavigation from './components/MobileNavigation';
import LazyWrapper, {
  LazyDashboard,
  LazyTrading,
  LazyPortfolio,
  LazySettings
} from './components/LazyWrapper';
import { lazy, Suspense } from 'react';
import LoadingSpinner from './components/LoadingSpinner';

// Keep lighter components as regular imports
import Education from './pages/Education';
import MarketEducation from './pages/MarketEducation';
import Monitoring from './pages/Monitoring';
import Notifications from './pages/Notifications';
import ChartExport from './pages/ChartExport';
import ThemeCustomization from './pages/ThemeCustomization';
import PerformanceOptimization from './pages/PerformanceOptimization';
import UnifiedTradingDashboard from './pages/UnifiedTradingDashboard';
import ResearchReport from './pages/ResearchReport';
import Stocks from './pages/Stocks';
import ForgotPassword from './pages/ForgotPassword';
import VerifyReset from './pages/VerifyReset';
import ResetPassword from './pages/ResetPassword';
import WatchlistPage from './pages/WatchlistPage';
import AlertsPage from './pages/AlertsPage';
import AIAssistant from './components/chat/AIAssistant';
import { logBundleAnalysis } from './utils/bundleAnalyzer';
import './App.css';

// Lazy load heavy components for better initial load performance
const LazyMarketDashboard = lazy(() => import('./pages/MarketDashboard'));
const LazyComprehensiveTrading = lazy(() => import('./pages/ComprehensiveTrading'));
const LazyComprehensiveTradingPro = lazy(() => import('./pages/ComprehensiveTradingPro'));
const LazyUnifiedAI = lazy(() => import('./pages/UnifiedAI'));
const LazyIntelligentTrading = lazy(() => import('./pages/IntelligentTrading'));
const LazyRiskManagement = lazy(() => import('./pages/RiskManagement'));
const LazyPortfolioAllocation = lazy(() => import('./pages/PortfolioAllocation'));
const LazyMultiTimeframe = lazy(() => import('./pages/MultiTimeframe'));
const LazyBacktestingPage = lazy(() => import('./pages/BacktestingPage'));
const LazyStockScreener = lazy(() => import('./pages/StockScreener'));
const LazyFNOTrading = lazy(() => import('./pages/FNOTrading'));
const LazyIntradayTrading = lazy(() => import('./pages/IntradayTrading'));
const LazyCommodityTrading = lazy(() => import('./pages/CommodityTrading'));
const LazyNifty50TradingSignals = lazy(() => import('./pages/Nifty50TradingSignals'));
const LazyRealtimeTrading = lazy(() => import('./components/RealtimeTrading'));
const LazyTomorrowNiftyOpening = lazy(() => import('./pages/TomorrowNiftyOpening'));
const LazyNseResults = lazy(() => import('./pages/NseResults'));
const LazySymbol = lazy(() => import('./pages/Symbol'));
const LazyMLDashboard = lazy(() => import('./components/MLDashboard'));
const LazyConsolidatedAnalysis = lazy(() => import('./pages/ConsolidatedAnalysis'));
const LazyLogin = lazy(() => import('./pages/Login'));

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Log bundle analysis on mount
  React.useEffect(() => {
    logBundleAnalysis();
  }, []);

  const handleMenuClick = () => {
    setSidebarOpen(true);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  const handleMobileMenuClick = () => {
    setMobileMenuOpen(true);
  };

  const handleMobileMenuClose = () => {
    setMobileMenuOpen(false);
  };

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <EnhancedThemeProvider>
          <AuthProvider>
            <WebSocketProvider>
            <div className="min-h-screen bg-background text-foreground">
            <div className="flex">
              {/* Desktop Sidebar */}
              <Sidebar isOpen={sidebarOpen} onClose={handleSidebarClose} />
              
              {/* Main Content */}
              <div className="flex-1 flex flex-col lg:ml-64">
                <Header 
                  onMenuClick={handleMenuClick} 
                  onMobileMenuClick={handleMobileMenuClick}
                />
                
                <main className="flex-1 p-4 sm:p-6">
                  <LazyWrapper>
                    <Routes>
                      <Route path="/ml-dashboard" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading ML Dashboard..." />}>
                          <LazyMLDashboard />
                        </Suspense>
                      } />
                      <Route path="/test-ml" element={<div>ML Test Route Works!</div>} />
                      <Route path="/" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Market Dashboard..." />}>
                          <LazyMarketDashboard />
                        </Suspense>
                      } />
                      <Route path="/dashboard" element={<LazyDashboard />} />
                      <Route path="/market-dashboard" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Market Dashboard..." />}>
                          <LazyMarketDashboard />
                        </Suspense>
                      } />
                      <Route path="/trading" element={<LazyTrading />} />
                      <Route path="/unified-ai" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading AI Dashboard..." />}>
                          <LazyUnifiedAI />
                        </Suspense>
                      } />
                      <Route path="/intelligent-trading" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Intelligent Trading..." />}>
                          <LazyIntelligentTrading />
                        </Suspense>
                      } />
                      <Route path="/risk-management" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Risk Management..." />}>
                          <LazyRiskManagement />
                        </Suspense>
                      } />
                      <Route path="/portfolio-allocation" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Portfolio Allocation..." />}>
                          <LazyPortfolioAllocation />
                        </Suspense>
                      } />
                      <Route path="/portfolio" element={<Navigate to="/portfolio-allocation" replace />} />
                      <Route path="/monitoring" element={<Monitoring />} />
                      <Route path="/notifications" element={<Notifications />} />
                      <Route path="/chart-export" element={<ChartExport />} />
                      <Route path="/theme-customization" element={<ThemeCustomization />} />
                      <Route path="/performance-optimization" element={<PerformanceOptimization />} />
                      <Route path="/symbol/:symbol" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Symbol Data..." />}>
                          <LazySymbol />
                        </Suspense>
                      } />
                      <Route path="/consolidated-analysis/:symbol" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Consolidated Analysis..." />}>
                          <LazyConsolidatedAnalysis />
                        </Suspense>
                      } />
                      <Route path="/consolidated-analysis" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Consolidated Analysis..." />}>
                          <LazyConsolidatedAnalysis />
                        </Suspense>
                      } />
                      <Route path="/stocks" element={<Stocks />} />
                      <Route path="/stocks/top-gainers" element={<Stocks />} />
                      <Route path="/stocks/top-losers" element={<Stocks />} />
                      <Route path="/stocks/only-buyers" element={<Stocks />} />
                      <Route path="/stocks/only-sellers" element={<Stocks />} />
                      <Route path="/stocks/volume-shockers" element={<Stocks />} />
                      <Route path="/stocks/most-active" element={<Stocks />} />
                      <Route path="/stocks/sector/:sectorName" element={<Stocks />} />
                      <Route path="/stocks/:symbol" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Symbol Data..." />}>
                          <LazySymbol />
                        </Suspense>
                      } />
                      <Route path="/login" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Login..." />}>
                          <LazyLogin />
                        </Suspense>
                      } />
                      <Route path="/forgot-password" element={<ForgotPassword />} />
                      <Route path="/verify-reset" element={<VerifyReset />} />
                      <Route path="/reset-password" element={<ResetPassword />} />
                      <Route path="/portfolio" element={<LazyPortfolio />} />
                      <Route path="/comprehensive-trading" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Trading Interface..." />}>
                          <LazyComprehensiveTrading />
                        </Suspense>
                      } />
                      <Route path="/comprehensive-trading-pro" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Trading Pro..." />}>
                          <LazyComprehensiveTradingPro />
                        </Suspense>
                      } />
                      <Route path="/unified-dashboard" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Dashboard..." />}>
                          <LazyUnifiedAI />
                        </Suspense>
                      } />
                      <Route path="/multi-timeframe" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Multi-Timeframe..." />}>
                          <LazyMultiTimeframe />
                        </Suspense>
                      } />
                      <Route path="/backtesting" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Backtesting..." />}>
                          <LazyBacktestingPage />
                        </Suspense>
                      } />
                      <Route path="/screener" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Stock Screener..." />}>
                          <LazyStockScreener />
                        </Suspense>
                      } />
                      <Route path="/research-report" element={<ResearchReport />} />
                      <Route path="/watchlist" element={<WatchlistPage />} />
                      <Route path="/alerts" element={<AlertsPage />} />
                      <Route path="/education" element={<Education />} />
                      <Route path="/market-education" element={<MarketEducation />} />
                      <Route path="/intelligence" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Intelligence..." />}>
                          <LazyIntelligentTrading />
                        </Suspense>
                      } />
                      <Route path="/fno-trading" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading F&O Trading..." />}>
                          <LazyFNOTrading />
                        </Suspense>
                      } />
                      <Route path="/intraday-trading" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Intraday Trading..." />}>
                          <LazyIntradayTrading />
                        </Suspense>
                      } />
                      <Route path="/tomorrow-nifty-opening" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Tomorrow's NIFTY Opening Analysis..." />}>
                          <LazyTomorrowNiftyOpening />
                        </Suspense>
                      } />
                      <Route path="/commodity-trading" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Commodity Trading..." />}>
                          <LazyCommodityTrading />
                        </Suspense>
                      } />
                      <Route path="/nifty50-signals" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Nifty50 Signals..." />}>
                          <LazyNifty50TradingSignals />
                        </Suspense>
                      } />
                      <Route path="/realtime-trading" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading Real-time Trading..." />}>
                          <LazyRealtimeTrading />
                        </Suspense>
                      } />
                      <Route path="/nse-results" element={
                        <Suspense fallback={<LoadingSpinner size="md" text="Loading NSE Results..." />}>
                          <LazyNseResults />
                        </Suspense>
                      } />
                      <Route path="/settings" element={<LazySettings />} />
                    </Routes>
                  </LazyWrapper>
                </main>
              </div>
            </div>

            {/* Mobile Navigation */}
            <MobileNavigation 
              isOpen={mobileMenuOpen} 
              onClose={handleMobileMenuClose} 
            />
            
            {/* Toast Notifications */}
            <Toaster 
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
              }}
            />

            {/* Performance Dashboard (Development Only) - Component not implemented yet */}
            {/* {process.env.NODE_ENV === 'development' && <PerformanceDashboard />} */}
            
            {/* AI Assistant */}
            <AIAssistant />
          </div>
          </WebSocketProvider>
        </AuthProvider>
        </EnhancedThemeProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
