import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChartPieIcon, AdjustmentsHorizontalIcon, CalculatorIcon, 
  ArrowTrendingUpIcon, ArrowTrendingDownIcon, ExclamationTriangleIcon,
  CheckCircleIcon, ClockIcon, CurrencyDollarIcon, ChartBarIcon,
  PlusIcon, TrashIcon, PencilIcon, EyeIcon, EyeSlashIcon,
  BriefcaseIcon, SparklesIcon, WalletIcon, ClipboardDocumentListIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import FNOTrading from '../../pages/FNOTrading';
import IntradayTrading from '../../pages/IntradayTrading';
import PortfolioOptimization from './PortfolioOptimization';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';
import { httpClient, ApiError, isApiError, NetworkError } from '../../config/api';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../LoadingSpinner';
import refreshService from '../../services/RefreshService';
import ErrorDisplay from '../ErrorDisplay';
import BuySellButton from '../BuySellButton';
import StockSelector from '../StockSelector';
import OrderBook from '../OrderBook';

// Types for Portfolio Allocation
interface Asset {
  id: string;
  symbol: string;
  name: string;
  category: 'equity' | 'bond' | 'commodity' | 'crypto' | 'real_estate' | 'cash';
  current_price: number;
  quantity: number;
  market_value: number;
  target_allocation: number;
  current_allocation: number;
  weight: number;
  expected_return: number;
  volatility: number;
  beta: number;
  correlation_matrix: Record<string, number>;
}

interface PortfolioAllocation {
  id: string;
  name: string;
  description: string;
  total_value: number;
  assets: Asset[];
  target_allocation: Record<string, number>;
  current_allocation: Record<string, number>;
  allocation_drift: Record<string, number>;
  rebalancing_needed: boolean;
  rebalancing_priority: Array<{
    symbol: string;
    action: 'buy' | 'sell';
    quantity: number;
    value: number;
    priority: 'high' | 'medium' | 'low';
    reason: string;
  }>;
  risk_metrics: {
    portfolio_volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
    var_95: number;
    expected_return: number;
  };
  constraints: {
    max_single_position: number;
    max_sector_allocation: number;
    min_liquidity_requirement: number;
    rebalancing_threshold: number;
  };
  last_rebalanced: string;
  next_rebalance_date: string;
}

interface AllocationStrategy {
  id: string;
  name: string;
  description: string;
  type: 'equal_weight' | 'market_cap' | 'risk_parity' | 'momentum' | 'value' | 'custom';
  parameters: Record<string, any>;
  expected_performance: {
    return: number;
    volatility: number;
    sharpe_ratio: number;
  };
  suitability: {
    risk_tolerance: 'low' | 'medium' | 'high';
    investment_horizon: 'short' | 'medium' | 'long';
    market_conditions: 'bull' | 'bear' | 'sideways';
  };
}

interface RebalancingRecommendation {
  portfolio_id: string;
  rebalancing_needed: boolean;
  current_deviation: number;
  recommended_actions: Array<{
    symbol: string;
    current_weight: number;
    target_weight: number;
    deviation: number;
    action: 'buy' | 'sell' | 'hold';
    quantity: number;
    value: number;
    transaction_cost: number;
    priority: 'high' | 'medium' | 'low';
  }>;
  expected_benefits: {
    risk_reduction: number;
    return_improvement: number;
    transaction_costs: number;
    net_benefit: number;
  };
  implementation_plan: {
    phases: Array<{
      phase: number;
      description: string;
      actions: string[];
      timeline: string;
    }>;
    total_timeline: string;
    estimated_costs: number;
  };
}

// Portfolio Allocation API Service
class PortfolioAllocationApiService {
  private baseUrl = '/portfolio-allocation';

  // Use centralized httpClient so auth headers are included
  async getAllocationStrategies(): Promise<AllocationStrategy[]> {
    const res = await httpClient.get<any>(`/api${this.baseUrl}/strategies`);
    const payload = (res as any);
    const data = payload.data ?? payload;
    return (data?.strategies as AllocationStrategy[]) || [];
  }

  // Backend exposes GET /api/portfolio-allocation/allocation
  // Convert it into a single mock portfolio compatible with the UI
  async getPortfolioAllocations(): Promise<PortfolioAllocation[]> {
    // First try to get user's portfolios from database
    try {
      const userPortfolios = await this.getUserPortfolios();
      if (userPortfolios && userPortfolios.length > 0) {
        return userPortfolios;
      }
    } catch (error) {
      const err = error as any;
      // Don't log network errors as warnings - they're expected if backend is down
      if (!(err instanceof Error && (err.name === 'NetworkError' || err.message?.includes('Network error')))) {
        console.warn('Failed to fetch user portfolios, falling back to default:', error);
      }
    }
    
    // Fallback to allocation-based portfolio if no user portfolios exist
    const res = await httpClient.get<any>(`/api${this.baseUrl}/allocation`);
    const payload = (res as any);
    const data = payload.data ?? payload;
    const alloc = data.allocation || data;
    const equity = alloc?.equity ?? 60;
    const debt = alloc?.debt ?? 25;
    const cash = alloc?.cash ?? 10;
    const commodities = alloc?.commodities ?? 5;

    const portfolio: PortfolioAllocation = {
      id: 'default',
      name: 'My Portfolio',
      description: 'Auto-generated from allocation endpoint',
      total_value: 0,
      assets: [
        { id: 'equity', symbol: 'EQUITY', name: 'Equity', category: 'equity', current_price: 0, quantity: 0, market_value: 0, target_allocation: equity, current_allocation: equity, weight: equity, expected_return: 0, volatility: 0, beta: 1, correlation_matrix: {} },
        { id: 'debt', symbol: 'DEBT', name: 'Debt', category: 'bond', current_price: 0, quantity: 0, market_value: 0, target_allocation: debt, current_allocation: debt, weight: debt, expected_return: 0, volatility: 0, beta: 0, correlation_matrix: {} },
        { id: 'cash', symbol: 'CASH', name: 'Cash', category: 'cash', current_price: 0, quantity: 0, market_value: 0, target_allocation: cash, current_allocation: cash, weight: cash, expected_return: 0, volatility: 0, beta: 0, correlation_matrix: {} },
        { id: 'commodities', symbol: 'CMDTY', name: 'Commodities', category: 'commodity', current_price: 0, quantity: 0, market_value: 0, target_allocation: commodities, current_allocation: commodities, weight: commodities, expected_return: 0, volatility: 0, beta: 0, correlation_matrix: {} },
      ],
      target_allocation: { equity, debt, cash, commodities },
      current_allocation: { equity, debt, cash, commodities },
      allocation_drift: {},
      rebalancing_needed: false,
      rebalancing_priority: [],
      risk_metrics: { portfolio_volatility: 0, sharpe_ratio: 0, max_drawdown: 0, var_95: 0, expected_return: 0 },
      constraints: { max_single_position: 25, max_sector_allocation: 40, min_liquidity_requirement: 5, rebalancing_threshold: 5 },
      last_rebalanced: new Date().toISOString(),
      next_rebalance_date: new Date(Date.now() + 30*24*3600*1000).toISOString(),
    };
    return [portfolio];
  }

  // Until full backend CRUD exists, provide safe fallbacks to avoid UI errors
  async getPortfolioAllocation(portfolioId: string): Promise<PortfolioAllocation> {
    const list = await this.getPortfolioAllocations();
    return list.find(p => p.id === portfolioId) || list[0];
  }

  async createPortfolio(portfolio: Partial<PortfolioAllocation>): Promise<PortfolioAllocation> {
    try {
      console.log('Creating portfolio with:', portfolio);
      
      // Call the backend API to create portfolio
      const response = await httpClient.post<any>(`/api${this.baseUrl}/create-portfolio`, {
        name: portfolio.name || 'My Portfolio',
        description: portfolio.description || '',
        total_value: portfolio.total_value || 0
      });
      
      console.log('Portfolio creation response:', response);
      
      if (response && response.success && response.data) {
        const createdPortfolio = response.data;
        return {
          id: String(createdPortfolio.id),
          name: createdPortfolio.name,
          description: createdPortfolio.description || '',
          total_value: createdPortfolio.total_value,
          assets: [],
          target_allocation: {},
          current_allocation: {},
          allocation_drift: {},
          rebalancing_needed: false,
          rebalancing_priority: [],
          risk_metrics: {
            portfolio_volatility: 0,
            sharpe_ratio: 0,
            max_drawdown: 0,
            var_95: 0,
            expected_return: 0
          },
          constraints: {
            max_single_position: 20,
            max_sector_allocation: 30,
            min_liquidity_requirement: 5,
            rebalancing_threshold: 5
          },
          last_rebalanced: createdPortfolio.created_at || new Date().toISOString(),
          next_rebalance_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString()
        } as PortfolioAllocation;
      } else {
        throw new Error(response?.message || 'Failed to create portfolio');
      }
    } catch (error) {
      console.error('Failed to create portfolio:', error);
      throw error;
    }
  }
  
  async getUserPortfolios(): Promise<PortfolioAllocation[]> {
    try {
      const response = await httpClient.get<any>(`/api${this.baseUrl}/portfolios`);
      if (response && response.success && response.data) {
        return response.data.map((p: any) => ({
          id: String(p.id),
          name: p.name,
          description: p.description || '',
          total_value: p.total_value,
          assets: [],
          target_allocation: {},
          current_allocation: {},
          allocation_drift: {},
          rebalancing_needed: false,
          rebalancing_priority: [],
          risk_metrics: {
            portfolio_volatility: 0,
            sharpe_ratio: 0,
            max_drawdown: 0,
            var_95: 0,
            expected_return: 0
          },
          constraints: {
            max_single_position: 20,
            max_sector_allocation: 30,
            min_liquidity_requirement: 5,
            rebalancing_threshold: 5
          },
          last_rebalanced: p.created_at || new Date().toISOString(),
          next_rebalance_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString()
        })) as PortfolioAllocation[];
      }
      return [];
    } catch (error) {
      // Check if it's a network error (backend not running)
      const err = error as any;
      if (err instanceof Error && (err.name === 'NetworkError' || err.message?.includes('Network error'))) {
        console.error('[PortfolioAllocationApi] Backend connection failed:', err.message);
        // Return empty array instead of throwing - let fallback handle it
        return [];
      }
      console.error('Failed to fetch user portfolios:', error);
      return [];
    }
  }

  async updatePortfolio(portfolioId: string, updates: Partial<PortfolioAllocation>): Promise<PortfolioAllocation> {
    const p = await this.getPortfolioAllocation(portfolioId);
    return { ...p, ...updates, updated_at: new Date().toISOString() } as any;
  }

  async deletePortfolio(): Promise<void> {
    return;
  }

  async addAsset(_portfolioId: string, asset: Partial<Asset>): Promise<Asset> {
    return {
      id: `a_${Date.now()}`,
      symbol: asset.symbol || 'ASSET',
      name: asset.name || 'Asset',
      category: asset.category || 'equity',
      current_price: asset.current_price || 0,
      quantity: asset.quantity || 0,
      market_value: 0,
      target_allocation: asset.target_allocation || 0,
      current_allocation: asset.current_allocation || 0,
      weight: asset.weight || 0,
      expected_return: asset.expected_return || 0,
      volatility: asset.volatility || 0,
      beta: asset.beta || 0,
      correlation_matrix: asset.correlation_matrix || {}
    } as Asset;
  }

  async updateAsset(_portfolioId: string, _assetId: string, updates: Partial<Asset>): Promise<Asset> {
    return {
      id: _assetId,
      symbol: updates.symbol || 'ASSET',
      name: updates.name || 'Asset',
      category: updates.category || 'equity',
      current_price: updates.current_price || 0,
      quantity: updates.quantity || 0,
      market_value: 0,
      target_allocation: updates.target_allocation || 0,
      current_allocation: updates.current_allocation || 0,
      weight: updates.weight || 0,
      expected_return: updates.expected_return || 0,
      volatility: updates.volatility || 0,
      beta: updates.beta || 0,
      correlation_matrix: updates.correlation_matrix || {}
    } as Asset;
  }

  async removeAsset(): Promise<void> { return; }

  async applyStrategy(portfolioId: string, strategyId: string): Promise<PortfolioAllocation> {
    const p = await this.getPortfolioAllocation(portfolioId);
    return { ...p, optimized: true, description: `Applied strategy ${strategyId}` } as any;
  }

  async getRebalancingRecommendation(portfolioId: string): Promise<RebalancingRecommendation> {
    try {
      // Call the real backend API
      const res = await httpClient.post<any>(`${this.baseUrl}/rebalance`, {
        frequency: 'quarterly'
      });
      
      const payload = (res as any);
      const data = payload.data ?? payload;
      
      if (!data || data.error) {
        // Fallback to mock data if API fails
    const p = await this.getPortfolioAllocation(portfolioId);
    return {
      portfolio_id: p.id,
      rebalancing_needed: false,
      current_deviation: 0,
          recommended_actions: [],
          expected_benefits: { risk_reduction: 0, return_improvement: 0, transaction_costs: 0, net_benefit: 0 },
      implementation_plan: {
            phases: [],
            total_timeline: 'N/A',
        estimated_costs: 0,
      },
    };
  }

      // Transform backend response to frontend format
      const allocationAnalysis = data.allocation_analysis || {};
      const recommendations = data.rebalancing_recommendations || {};
      const needsRebalancing = allocationAnalysis.needs_rebalancing || false;
      
      // Build recommended actions from allocation drift
      const recommendedActions: RebalancingRecommendation['recommended_actions'] = [];
      
      if (needsRebalancing) {
        const currentAlloc = data.current_allocation || {};
        const targetAlloc = data.target_allocation || {};
        
        // Process equity
        const equityDrift = allocationAnalysis.equity_drift || 0;
        if (Math.abs(equityDrift) > 1) {
          recommendedActions.push({
            symbol: 'EQUITY',
            current_weight: currentAlloc.equity || 0,
            target_weight: targetAlloc.equity || 0,
            deviation: equityDrift,
            action: equityDrift > 0 ? 'sell' : 'buy',
            quantity: 0, // Will be calculated based on portfolio value
            value: Math.abs(equityDrift) * (data.portfolio?.total_value || 0) / 100,
            transaction_cost: 0,
            priority: Math.abs(equityDrift) > 10 ? 'high' : Math.abs(equityDrift) > 5 ? 'medium' : 'low'
          });
        }
        
        // Process bonds
        const bondDrift = allocationAnalysis.bond_drift || 0;
        if (Math.abs(bondDrift) > 1) {
          recommendedActions.push({
            symbol: 'BONDS',
            current_weight: currentAlloc.bonds || 0,
            target_weight: targetAlloc.bonds || 0,
            deviation: bondDrift,
            action: bondDrift > 0 ? 'sell' : 'buy',
            quantity: 0,
            value: Math.abs(bondDrift) * (data.portfolio?.total_value || 0) / 100,
            transaction_cost: 0,
            priority: Math.abs(bondDrift) > 10 ? 'high' : Math.abs(bondDrift) > 5 ? 'medium' : 'low'
          });
        }
        
        // Process cash
        const cashDrift = allocationAnalysis.cash_drift || 0;
        if (Math.abs(cashDrift) > 1) {
          recommendedActions.push({
            symbol: 'CASH',
            current_weight: currentAlloc.cash || 0,
            target_weight: targetAlloc.cash || 0,
            deviation: cashDrift,
            action: cashDrift > 0 ? 'sell' : 'buy',
            quantity: 0,
            value: Math.abs(cashDrift) * (data.portfolio?.total_value || 0) / 100,
            transaction_cost: 0,
            priority: Math.abs(cashDrift) > 10 ? 'high' : Math.abs(cashDrift) > 5 ? 'medium' : 'low'
          });
        }
      }
      
      // Calculate expected benefits (simplified)
      const maxDrift = allocationAnalysis.max_drift || 0;
      const riskReduction = needsRebalancing ? Math.min(maxDrift * 0.5, 10) : 0;
      const returnImprovement = needsRebalancing ? Math.min(maxDrift * 0.3, 5) : 0;
      const transactionCosts = recommendedActions.reduce((sum, action) => sum + (action.value * 0.001), 0); // 0.1% transaction cost
      
      return {
        portfolio_id: portfolioId,
        rebalancing_needed: needsRebalancing,
        current_deviation: maxDrift,
        recommended_actions: recommendedActions,
        expected_benefits: {
          risk_reduction: riskReduction,
          return_improvement: returnImprovement,
          transaction_costs: transactionCosts,
          net_benefit: returnImprovement - transactionCosts
        },
        implementation_plan: {
          phases: recommendations.recommendations ? [
            {
              phase: 1,
              description: recommendations.action || 'Rebalance Portfolio',
              actions: recommendations.recommendations || [],
              timeline: recommendations.timeline || 'Within 1 month'
            }
          ] : [],
          total_timeline: recommendations.timeline || 'Within 1 month',
          estimated_costs: transactionCosts,
        },
      };
    } catch (error) {
      console.error('Error fetching rebalancing recommendation:', error);
      // Return balanced portfolio if API fails
      const p = await this.getPortfolioAllocation(portfolioId);
      return {
        portfolio_id: p.id,
        rebalancing_needed: false,
        current_deviation: 0,
        recommended_actions: [],
        expected_benefits: { risk_reduction: 0, return_improvement: 0, transaction_costs: 0, net_benefit: 0 },
        implementation_plan: {
          phases: [],
          total_timeline: 'N/A',
          estimated_costs: 0,
        },
      };
    }
  }

  async executeRebalancing(portfolioId?: string): Promise<any> {
    try {
      // Call backend to execute rebalancing
      const res = await httpClient.post<any>(`${this.baseUrl}/rebalance`, {
        frequency: 'quarterly'
      });
      
      const payload = (res as any);
      return payload.data ?? payload;
    } catch (error) {
      console.error('Error executing rebalancing:', error);
      throw error;
    }
  }

  async optimizeAllocation(portfolioId: string, constraints: any): Promise<PortfolioAllocation> {
    const p = await this.getPortfolioAllocation(portfolioId);
    return { ...p, optimized: true, description: 'Optimized allocation', target_allocation: { ...(p as any).target_allocation, ...constraints } } as any;
  }
}

const portfolioAllocationApi = new PortfolioAllocationApiService();

// Asset Allocation Chart Component
const AssetAllocationChart: React.FC<{
  allocation: Record<string, number>;
  colors?: Record<string, string>;
  totalValue?: number; // Optional: actual portfolio total value in currency
}> = ({ allocation, colors = {}, totalValue }) => {
  // Note: allocation values are percentages (0-100), not currency amounts
  // Calculate total percentage for pie chart (should be 100 or close to it)
  const totalPercentage = Object.values(allocation).reduce((sum, value) => sum + value, 0);
  const defaultColors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
    '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6B7280'
  ];

  let cumulativePercentage = 0;
  const segments = Object.entries(allocation).map(([category, value], index) => {
    // Use value directly as percentage (allocation values are already percentages)
    const percentage = totalPercentage > 0 ? (value / totalPercentage) * 100 : value;
    const startAngle = (cumulativePercentage / 100) * 360;
    const endAngle = ((cumulativePercentage + percentage) / 100) * 360;
    cumulativePercentage += percentage;

    return {
      category,
      value,
      percentage,
      startAngle,
      endAngle,
      color: colors[category] || defaultColors[index % defaultColors.length]
    };
  });

  return (
    <div className="space-y-4">
      <div className="relative w-64 h-64 mx-auto">
        <svg width="256" height="256" viewBox="0 0 256 256" className="transform -rotate-90">
          {segments.map((segment, index) => (
            <path
              key={index}
              d={`M 128,128 L ${128 + 100 * Math.cos((segment.startAngle * Math.PI) / 180)},${128 + 100 * Math.sin((segment.startAngle * Math.PI) / 180)} A 100,100 0 ${segment.percentage > 50 ? 1 : 0},1 ${128 + 100 * Math.cos((segment.endAngle * Math.PI) / 180)},${128 + 100 * Math.sin((segment.endAngle * Math.PI) / 180)} Z`}
              fill={segment.color}
              stroke="white"
              strokeWidth="2"
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {totalValue ? (
                <>₹{totalValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</>
              ) : (
                <>₹0.00</>
              )}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Value</div>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {segments.map((segment, index) => (
          <div key={index} className="flex items-center justify-between text-sm">
            <div className="flex items-center">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: segment.color }}
              />
              <span className="text-gray-700 dark:text-gray-300">{segment.category}</span>
            </div>
            <div className="text-gray-600 dark:text-gray-400">
              {segment.percentage.toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Asset Management Component
const AssetManagement: React.FC<{
  portfolio: PortfolioAllocation;
  onUpdate: (portfolio: PortfolioAllocation) => void;
}> = ({ portfolio, onUpdate }) => {
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAsset, setNewAsset] = useState<Partial<Asset>>({
    symbol: '',
    name: '',
    category: 'equity',
    current_price: 0,
    quantity: 0,
    target_allocation: 0
  });

  const handleAddAsset = async () => {
    try {
      const asset = await portfolioAllocationApi.addAsset(portfolio.id, newAsset);
      const updatedPortfolio = {
        ...portfolio,
        assets: [...portfolio.assets, asset]
      };
      onUpdate(updatedPortfolio);
      setShowAddForm(false);
      setNewAsset({
        symbol: '',
        name: '',
        category: 'equity',
        current_price: 0,
        quantity: 0,
        target_allocation: 0
      });
      toast.success('Asset added successfully');
    } catch (error) {
      toast.error('Failed to add asset');
    }
  };

  const handleUpdateAsset = async (assetId: string, updates: Partial<Asset>) => {
    try {
      const updatedAsset = await portfolioAllocationApi.updateAsset(portfolio.id, assetId, updates);
      const updatedPortfolio = {
        ...portfolio,
        assets: portfolio.assets.map(asset => asset.id === assetId ? updatedAsset : asset)
      };
      onUpdate(updatedPortfolio);
      setEditingAsset(null);
      toast.success('Asset updated successfully');
    } catch (error) {
      toast.error('Failed to update asset');
    }
  };

  const handleRemoveAsset = async (assetId: string) => {
    try {
      await portfolioAllocationApi.removeAsset();
      const updatedPortfolio = {
        ...portfolio,
        assets: portfolio.assets.filter(asset => asset.id !== assetId)
      };
      onUpdate(updatedPortfolio);
      toast.success('Asset removed successfully');
    } catch (error) {
      toast.error('Failed to remove asset');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Asset Management</h3>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Asset
        </button>
      </div>

      {/* Add Asset Form */}
      {showAddForm && (
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <h4 className="font-medium mb-4">Add New Asset</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Symbol
              </label>
              <input
                type="text"
                value={newAsset.symbol || ''}
                onChange={(e) => setNewAsset(prev => ({ ...prev, symbol: e.target.value }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="e.g., AAPL"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Name
              </label>
              <input
                type="text"
                value={newAsset.name || ''}
                onChange={(e) => setNewAsset(prev => ({ ...prev, name: e.target.value }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="e.g., Apple Inc."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Category
              </label>
              <select
                value={newAsset.category || 'equity'}
                onChange={(e) => setNewAsset(prev => ({ ...prev, category: e.target.value as any }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
              >
                <option value="equity">Equity</option>
                <option value="bond">Bond</option>
                <option value="commodity">Commodity</option>
                <option value="crypto">Cryptocurrency</option>
                <option value="real_estate">Real Estate</option>
                <option value="cash">Cash</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Current Price
              </label>
              <input
                type="number"
                value={newAsset.current_price || ''}
                onChange={(e) => setNewAsset(prev => ({ ...prev, current_price: parseFloat(e.target.value) }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Quantity
              </label>
              <input
                type="number"
                value={newAsset.quantity || ''}
                onChange={(e) => setNewAsset(prev => ({ ...prev, quantity: parseFloat(e.target.value) }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Target Allocation (%)
              </label>
              <input
                type="number"
                value={newAsset.target_allocation || ''}
                onChange={(e) => setNewAsset(prev => ({ ...prev, target_allocation: parseFloat(e.target.value) }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="0.0"
              />
            </div>
          </div>
          <div className="flex justify-end space-x-2 mt-4">
            <button
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={handleAddAsset}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
              Add Asset
            </button>
          </div>
        </div>
      )}

      {/* Assets Table */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Symbol</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Category</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Price</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Quantity</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Market Value</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Allocation</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {portfolio.assets.map((asset) => (
              <tr key={asset.id}>
                <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{asset.symbol}</td>
                <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{asset.name}</td>
                <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                  <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded">
                    {asset.category}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                  ₹{asset.current_price.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{asset.quantity}</td>
                <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                  ₹{asset.market_value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                  <div className="flex items-center">
                    <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${asset.current_allocation}%` }}
                      />
                    </div>
                    <span>{asset.current_allocation.toFixed(1)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setEditingAsset(asset)}
                      className="text-blue-500 hover:text-blue-700"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleRemoveAsset(asset.id)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Holdings interface
interface Holding {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  total_value: number;
  invested_value: number;
  currency: string;
  currency_symbol: string;
  formatted_average_price: string;
  formatted_current_price: string;
  formatted_pnl: string;
  formatted_total_value: string;
  created_at: string;
  updated_at: string;
}

interface HoldingsData {
  success: boolean;
  holdings: Holding[];
  total_value: number;
  total_invested: number;
  total_pnl: number;
  total_pnl_percent: number;
  currency: string;
  currency_symbol: string;
  formatted_total_value: string;
  formatted_total_pnl: string;
  last_updated: string;
}

interface UnifiedPortfolioData {
  holdings: Holding[];
  holdings_summary: {
    total_value: number;
    total_invested: number;
    total_pnl: number;
    total_pnl_percent: number;
    wallet_balance?: number;
    total_allocated_cash?: number;
    total_net_worth?: number;
    formatted_wallet_balance?: string;
    formatted_total_allocated_cash?: string;
    formatted_total_net_worth?: string;
    currency: string;
    currency_symbol: string;
  };
  allocation: {
    current: Record<string, number>;
    target: Record<string, number>;
    drift: {
      equity_drift: number;
      bond_drift: number;
      cash_drift: number;
      max_drift: number;
      needs_rebalancing: boolean;
      drift_severity: string;
    };
    rebalancing_needed: boolean;
  };
  last_updated: string;
}

// Main Portfolio Allocation Tools Component
const PortfolioAllocationTools: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'holdings' | 'overview' | 'allocation' | 'rebalancing' | 'insights' | 'strategies' | 'optimization' | 'fno' | 'intraday'>('holdings');
  const [portfolios, setPortfolios] = useState<PortfolioAllocation[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<PortfolioAllocation | null>(null);
  const [strategies, setStrategies] = useState<AllocationStrategy[]>([]);
  const [rebalancingRecommendation, setRebalancingRecommendation] = useState<RebalancingRecommendation | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [holdingsSummary, setHoldingsSummary] = useState<any>(null);
  const [unifiedData, setUnifiedData] = useState<UnifiedPortfolioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [aiSignals, setAiSignals] = useState<any[]>([]);
  const [riskMetrics, setRiskMetrics] = useState<any>(null);
  const [sectorAllocation, setSectorAllocation] = useState<any>({});
  const [volumeAnalysis, setVolumeAnalysis] = useState<any>(null);
  const [marketInsights, setMarketInsights] = useState<any>(null);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [demoHoldings, setDemoHoldings] = useState<any[]>([]);
  const [showDemoForm, setShowDemoForm] = useState(false);
  const [newDemoHolding, setNewDemoHolding] = useState({ symbol: '', quantity: 0, averagePrice: 0 });
  const [selectedStockForTrade, setSelectedStockForTrade] = useState<string>('');
  const [newPortfolio, setNewPortfolio] = useState<Partial<PortfolioAllocation>>({
    name: '',
    description: '',
    total_value: 0
  });
  const [pendingOrders, setPendingOrders] = useState<any[]>([]);
  const [showPipelineOrders, setShowPipelineOrders] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch unified portfolio data (holdings + allocation)
      try {
        const unifiedResponse = await httpClient.get<any>('/api/portfolio-allocation/portfolio');
        
        if (unifiedResponse.success && unifiedResponse.data) {
          const data = unifiedResponse.data;
          setUnifiedData(data);
          setHoldings(data.holdings || []);
          setHoldingsSummary(data.holdings_summary || null);
          
          // Update selected portfolio with real data
          if (data.holdings && data.holdings.length > 0) {
            const portfolioValue = data.holdings_summary?.total_value || 0;
            setSelectedPortfolio({
              id: 'unified',
              name: 'My Portfolio',
              description: 'Unified portfolio with holdings and allocation',
              total_value: portfolioValue,
              assets: data.holdings.map((h: Holding) => ({
                id: h.symbol,
                symbol: h.symbol,
                name: h.symbol,
                category: 'equity' as any,
                current_price: h.current_price,
                quantity: h.quantity,
                market_value: h.total_value,
                target_allocation: 0,
                current_allocation: portfolioValue > 0 ? (h.total_value / portfolioValue) * 100 : 0,
                weight: 0,
                expected_return: 0,
                volatility: 0,
                beta: 0,
                correlation_matrix: {}
              })),
              target_allocation: data.allocation?.target || {},
              current_allocation: data.allocation?.current || {},
              allocation_drift: data.allocation?.drift || {},
              rebalancing_needed: data.allocation?.rebalancing_needed || false,
              rebalancing_priority: [],
              risk_metrics: {
                portfolio_volatility: 0,
                sharpe_ratio: 0,
                max_drawdown: 0,
                var_95: 0,
                expected_return: 0
              },
              constraints: {
                max_single_position: 20,
                max_sector_allocation: 30,
                min_liquidity_requirement: 5,
                rebalancing_threshold: 5
              },
              last_rebalanced: data.last_updated || new Date().toISOString(),
              next_rebalance_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString()
            } as PortfolioAllocation);
          }
        } else if (unifiedResponse?.error) {
          console.warn('Portfolio API returned error:', unifiedResponse.error);
          setError(unifiedResponse.error || 'Failed to load portfolio data');
        }
      } catch (unifiedError) {
        // Handle ApiError (401, 500, etc.)
        if (isApiError(unifiedError)) {
          if (unifiedError.status === 401) {
            console.log('Session expired during portfolio fetch');
            setError('Session expired. Please refresh and login again.');
            return;
          }
          setError(unifiedError.message || 'Failed to load portfolio data');
        } else {
          // Handle other errors
          console.warn('Error fetching unified portfolio:', unifiedError);
          // Continue - try to load other data even if unified portfolio fails
        }
      }
      
      // Also fetch strategies (only if user is authenticated)
      if (user) {
        try {
          const strategiesData = await portfolioAllocationApi.getAllocationStrategies();
          setStrategies(strategiesData);
        } catch (err) {
          // Handle 401 gracefully - user might not be authenticated
          const error = err as any;
          if (error?.response?.status === 401 || error?.status === 401) {
            console.log('User not authenticated, skipping strategies fetch');
          } else {
            console.warn('Failed to fetch strategies:', err);
          }
        }
      }
    } catch (err) {
      // Handle ApiError exceptions
      if (isApiError(err)) {
        if (err.status === 401) {
          console.log('Session expired, user needs to login again');
          setError('Session expired. Please refresh the page and login again.');
          // Don't show toast for 401 - it's expected
          return;
        }
        if (err.status === 503) {
          setError(err.message || 'Database connection error. Please try again.');
          toast.error(err.message || 'Database connection error. Please try again.');
          return;
        }
        setError(err.message || 'Failed to fetch data');
        toast.error(err.message || 'Failed to load portfolio');
        return;
      }
      
      // Handle other errors
      const error = err as any;
      const errorMessage = err instanceof Error ? err.message : (error?.response?.data?.detail || error?.message || 'Failed to fetch data');
      setError(errorMessage);
      console.error('Error fetching portfolio data:', err);
      console.error('Error details:', {
        message: error?.message,
        response: error?.response,
        status: error?.status,
        data: error?.response?.data
      });
      toast.error(`Failed to load portfolio: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Fetch user portfolios first
    const loadPortfolios = async () => {
      try {
        const userPortfolios = await portfolioAllocationApi.getUserPortfolios();
        if (userPortfolios && userPortfolios.length > 0) {
          setPortfolios(userPortfolios);
          // Select the first portfolio or the most recent one
          setSelectedPortfolio(userPortfolios[0]);
        } else {
          // Load default portfolios if none exist
          const defaultPortfolios = await portfolioAllocationApi.getPortfolioAllocations();
          setPortfolios(defaultPortfolios);
          if (defaultPortfolios.length > 0) {
            setSelectedPortfolio(defaultPortfolios[0]);
          }
        }
      } catch (error) {
        console.error('Failed to load portfolios:', error);
        // Fallback to default
        portfolioAllocationApi.getPortfolioAllocations().then(defaultPortfolios => {
          setPortfolios(defaultPortfolios);
          if (defaultPortfolios.length > 0) {
            setSelectedPortfolio(defaultPortfolios[0]);
          }
        });
      }
    };
    
    loadPortfolios();
    fetchData();
    fetchPendingOrders();
    
    // Auto-refresh P&L every 30 seconds for real-time updates (using centralized service)
    refreshService.register('portfolio-allocation', () => {
      fetchData();
      fetchPendingOrders();
    }, 30000, false);
    
    return () => {
      refreshService.clear('portfolio-allocation');
    };
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
      fetchRebalancingRecommendation();
    }
  }, [selectedPortfolio]);

  useEffect(() => {
    if (activeTab === 'rebalancing' && selectedPortfolio) {
      fetchRebalancingRecommendation();
    }
  }, [activeTab, selectedPortfolio]);

  useEffect(() => {
    if (activeTab === 'insights' && (user || holdings.length > 0)) {
      fetchInsightsData();
    }
  }, [activeTab, user, holdings.length]);

  const fetchRebalancingRecommendation = async () => {
    if (!selectedPortfolio) return;
    
    try {
      const recommendation = await portfolioAllocationApi.getRebalancingRecommendation(selectedPortfolio.id);
      setRebalancingRecommendation(recommendation);
    } catch (error) {
      console.error('Failed to fetch rebalancing recommendation:', error);
    }
  };

  const handleCreatePortfolio = async () => {
    if (!newPortfolio.name || !newPortfolio.name.trim()) {
      toast.error('Please enter a portfolio name');
      return;
    }
    
    if (!newPortfolio.total_value || newPortfolio.total_value <= 0) {
      toast.error('Please enter a valid total value (greater than 0)');
      return;
    }
    
    try {
      console.log('Creating portfolio with:', newPortfolio);
      const portfolio = await portfolioAllocationApi.createPortfolio(newPortfolio);
      console.log('Portfolio created:', portfolio);
      
      // Refresh portfolios list from database
      const updatedPortfolios = await portfolioAllocationApi.getUserPortfolios();
      setPortfolios(updatedPortfolios);
      
      // Select the newly created portfolio
      const createdPortfolio = updatedPortfolios.find(p => p.id === portfolio.id) || portfolio;
      setSelectedPortfolio(createdPortfolio);
      setShowCreateForm(false);
      setNewPortfolio({ name: '', description: '', total_value: 0 });
      
      // Wait a bit for database to commit, then refresh portfolio data
      await new Promise(resolve => setTimeout(resolve, 500));
      await fetchData();
      
      toast.success(`Portfolio "${portfolio.name}" created successfully. Wallet balance updated to ₹${newPortfolio.total_value?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}.`);
    } catch (error) {
      console.error('Failed to create portfolio:', error);
      const err = error as any;
      const errorMessage = err?.message || err?.response?.data?.detail || 'Failed to create portfolio';
      toast.error(errorMessage);
    }
  };

  const handleApplyStrategy = async (strategyId: string) => {
    if (!selectedPortfolio) return;
    
    try {
      const updatedPortfolio = await portfolioAllocationApi.applyStrategy(selectedPortfolio.id, strategyId);
      setSelectedPortfolio(updatedPortfolio);
      setPortfolios(prev => prev.map(p => p.id === updatedPortfolio.id ? updatedPortfolio : p));
      toast.success('Strategy applied successfully');
    } catch (error) {
      toast.error('Failed to apply strategy');
    }
  };

  const handleExecuteRebalancing = async () => {
    if (!selectedPortfolio || !rebalancingRecommendation) return;
    
    try {
      setLoading(true);
      const result = await portfolioAllocationApi.executeRebalancing(selectedPortfolio.id);
      
      if (result.success) {
        toast.success('Rebalancing analysis completed. Review recommendations before executing trades.');
        // Refresh data to get updated recommendations
        await fetchData();
        await fetchRebalancingRecommendation();
      } else {
        toast.error(result.message || 'Failed to execute rebalancing');
      }
    } catch (error) {
      console.error('Error executing rebalancing:', error);
      const err = error as any;
      toast.error(err?.response?.data?.detail || err?.message || 'Failed to execute rebalancing');
    } finally {
      setLoading(false);
    }
  };

  // Auto-enable demo mode if holdings exist
  useEffect(() => {
    if (holdings.length > 0) {
      setDemoMode(true);
    }
  }, [holdings]);

  const addDemoHolding = async () => {
    if (!newDemoHolding.symbol || newDemoHolding.quantity <= 0 || newDemoHolding.averagePrice <= 0) {
      toast.error('Please fill all fields with valid values');
      return;
    }

    if (!user) {
      toast.error('Please login to add holdings');
      return;
    }

    try {
      // Save to database via API
      const response = await httpClient.post('/api/portfolio-allocation/add-demo-holding', {
        symbol: newDemoHolding.symbol.toUpperCase(),
        quantity: newDemoHolding.quantity,
        average_price: newDemoHolding.averagePrice
      });

      if (response.success) {
        toast.success('Holding added to portfolio successfully');
        setNewDemoHolding({ symbol: '', quantity: 0, averagePrice: 0 });
        setShowDemoForm(false);
        
        // Refresh portfolio data
        await fetchData();
        
        // Refresh insights after adding
        setTimeout(() => fetchInsightsData(), 500);
      } else {
        toast.error(response.message || 'Failed to add holding');
      }
    } catch (error) {
      toast.error('Failed to add holding');
      console.error('Error adding holding:', error);
    }
  };


  const fetchPendingOrders = async () => {
    if (!user) return;
    
    try {
      const response = await httpClient.get<any>('/api/trading/orders', {
        params: {
          limit: 50
        }
      });
      
      if (response.data?.orders) {
        // Filter for pending orders only
        const pending = response.data.orders.filter((order: any) => order.order_status === 'PENDING');
        setPendingOrders(pending);
      }
    } catch (error) {
      console.error('Error fetching pending orders:', error);
      setPendingOrders([]);
    }
  };

  const fetchInsightsData = async () => {
    if (!user && holdings.length === 0) return;
    
    setLoadingInsights(true);
    try {
      // Use real holdings from database
      if (holdings.length === 0) {
        // For demo mode, we'll create a temporary portfolio and fetch insights
        // We'll need to modify backend to accept demo holdings or create them temporarily
        // For now, let's fetch market insights which don't require holdings
        const [insightsRes] = await Promise.all([
          httpClient.get<any>('/api/portfolio-allocation/market-insights')
        ]);
        
        if (insightsRes.success && insightsRes.data && typeof insightsRes.data === 'object' && 'insights' in insightsRes.data) {
          setMarketInsights((insightsRes.data as any).insights);
        }
        
        // No holdings - show message
        setAiSignals([]);
        setRiskMetrics(null);
        setSectorAllocation({});
        setVolumeAnalysis(null);
      } else {
        // Fetch all insights data in parallel for real holdings
        const [signalsRes, riskRes, sectorRes, volumeRes, insightsRes] = await Promise.all([
          httpClient.get<any>('/api/portfolio-allocation/ai-signals'),
          httpClient.get<any>('/api/portfolio-allocation/risk-metrics'),
          httpClient.get<any>('/api/portfolio-allocation/sector-allocation'),
          httpClient.get<any>('/api/portfolio-allocation/volume-analysis'),
          httpClient.get<any>('/api/portfolio-allocation/market-insights')
        ]);
        
        if (signalsRes.success && signalsRes.data && typeof signalsRes.data === 'object' && 'signals' in signalsRes.data) {
          setAiSignals((signalsRes.data as any).signals);
        }
        
        if (riskRes.success && riskRes.data) {
          setRiskMetrics(riskRes.data);
        }
        
        if (sectorRes.success && sectorRes.data && typeof sectorRes.data === 'object' && 'sector_allocation' in sectorRes.data) {
          setSectorAllocation(sectorRes.data);
        }
        
        if (volumeRes.success && volumeRes.data && typeof volumeRes.data === 'object' && 'analysis' in volumeRes.data) {
          setVolumeAnalysis((volumeRes.data as any).analysis);
        }
        
        if (insightsRes.success && insightsRes.data && typeof insightsRes.data === 'object' && 'insights' in insightsRes.data) {
          setMarketInsights((insightsRes.data as any).insights);
        }
      }
    } catch (error) {
      console.error('Error fetching insights:', error);
      toast.error('Failed to load insights data');
    } finally {
      setLoadingInsights(false);
    }
  };

  const renderTabContent = () => {
    if (activeTab === 'holdings') {
      return (
        <div className="space-y-6">
          {/* Holdings Summary Cards */}
          {holdingsSummary && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7 gap-6">
              {/* Total Allocated Cash - Most Prominent */}
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900 dark:to-pink-900 border-2 border-purple-300 dark:border-purple-700 rounded-lg p-4 shadow-lg">
                <div className="flex items-center">
                  <SparklesIcon className="h-5 w-5 text-purple-600 dark:text-purple-400 mr-2 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-0.5">Total Allocated Cash</h3>
                    <p className="text-sm font-bold text-purple-700 dark:text-purple-300 leading-tight break-words">
                      {holdingsSummary.formatted_total_allocated_cash || holdingsSummary.currency_symbol + (holdingsSummary.total_allocated_cash || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className="text-[10px] text-gray-600 dark:text-gray-400 mt-0.5">Initial allocation</p>
                  </div>
                </div>
              </div>

              {/* Wallet Balance - Prominent */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900 dark:to-indigo-900 border-2 border-blue-300 dark:border-blue-700 rounded-lg p-4 shadow-lg">
                <div className="flex items-center">
                  <WalletIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-0.5">Wallet Balance</h3>
                    <p className="text-sm font-bold text-blue-700 dark:text-blue-300 leading-tight break-words">
                      {holdingsSummary.formatted_wallet_balance || holdingsSummary.currency_symbol + (holdingsSummary.wallet_balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className="text-[10px] text-gray-600 dark:text-gray-400 mt-0.5">Available cash</p>
                  </div>
                </div>
              </div>

              {/* Total Net Worth - Prominent */}
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900 dark:to-emerald-900 border-2 border-green-300 dark:border-green-700 rounded-lg p-4 shadow-lg">
                <div className="flex items-center">
                  <CurrencyDollarIcon className="h-5 w-5 text-green-600 dark:text-green-400 mr-2 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-0.5">Total Net Worth</h3>
                    <p className="text-sm font-bold text-green-700 dark:text-green-300 leading-tight break-words">
                      {holdingsSummary.formatted_total_net_worth || holdingsSummary.currency_symbol + (holdingsSummary.total_net_worth || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className="text-[10px] text-gray-600 dark:text-gray-400 mt-0.5">Cash + Portfolio</p>
                  </div>
                </div>
              </div>

              {/* Portfolio Value */}
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center">
                  <ChartBarIcon className="h-5 w-5 text-indigo-500 mr-2 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-0.5">Portfolio Value</h3>
                    <p className="text-sm font-bold text-indigo-600 dark:text-indigo-400 leading-tight break-words">
                      {holdingsSummary.formatted_total_value || holdingsSummary.currency_symbol + holdingsSummary.total_value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">Live prices</p>
                  </div>
                </div>
              </div>

              {/* Invested */}
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center">
                  <ChartBarIcon className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-0.5">Invested</h3>
                    <p className="text-sm font-bold text-blue-600 dark:text-blue-400 leading-tight break-words">
                      {holdingsSummary.currency_symbol}{holdingsSummary.total_invested?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Total P&L */}
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center">
                  {holdingsSummary.total_pnl >= 0 ? (
                    <ArrowTrendingUpIcon className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" />
                  ) : (
                    <ArrowTrendingDownIcon className="h-5 w-5 text-red-500 mr-2 flex-shrink-0" />
                  )}
                  <div className="min-w-0 flex-1">
                    <h3 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-0.5">Total P&L</h3>
                    <p className={`text-sm font-bold leading-tight break-words ${holdingsSummary.total_pnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {holdingsSummary.formatted_total_pnl || holdingsSummary.currency_symbol + holdingsSummary.total_pnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: 'always' })}
                    </p>
                    <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">Unrealized P&L</p>
                  </div>
                </div>
              </div>

              {/* P&L % */}
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center">
                  <ChartPieIcon className="h-5 w-5 text-purple-500 mr-2 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-0.5">P&L %</h3>
                    <p className={`text-sm font-bold leading-tight ${holdingsSummary.total_pnl_percent >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {holdingsSummary.total_pnl_percent?.toFixed(2) || '0.00'}%
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Stock Selection and Trading Section */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Select Stock to Trade</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Stock Symbol
                </label>
                <StockSelector
                  value={selectedStockForTrade}
                  onChange={(symbol) => {
                    console.log('Portfolio Allocation - StockSelector onChange called with:', symbol);
                    if (symbol) {
                      setSelectedStockForTrade(symbol);
                    }
                  }}
                  showNavigateButton={false}
                  className="w-full"
                />
              </div>
              <div className="flex items-end">
                {selectedStockForTrade && (
                  <BuySellButton
                    symbol={selectedStockForTrade}
                    currentPrice={0}
                    size="md"
                    onOrderPlaced={async () => {
                      await fetchData();
                      toast.success('Portfolio updated!');
                      setSelectedStockForTrade('');
                    }}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Add Holding Section */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Add Holding to Portfolio</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Holdings are saved permanently. Use Buy/Sell buttons to manage.
                </p>
              </div>
              <button
                onClick={() => setShowDemoForm(!showDemoForm)}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm font-medium flex items-center gap-2"
              >
                <PlusIcon className="h-4 w-4" />
                {showDemoForm ? 'Cancel' : 'Add Holding'}
              </button>
            </div>

            {showDemoForm && (
              <div className="mt-4 border-t border-gray-200 dark:border-gray-700 pt-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Symbol (e.g., RELIANCE, TCS)
                    </label>
                    <input
                      type="text"
                      value={newDemoHolding.symbol}
                      onChange={(e) => setNewDemoHolding({ ...newDemoHolding, symbol: e.target.value.toUpperCase() })}
                      className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      placeholder="RELIANCE"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Quantity
                    </label>
                    <input
                      type="number"
                      value={newDemoHolding.quantity || ''}
                      onChange={(e) => setNewDemoHolding({ ...newDemoHolding, quantity: parseInt(e.target.value) || 0 })}
                      className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      placeholder="10"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Average Price (₹)
                    </label>
                    <input
                      type="number"
                      value={newDemoHolding.averagePrice || ''}
                      onChange={(e) => setNewDemoHolding({ ...newDemoHolding, averagePrice: parseFloat(e.target.value) || 0 })}
                      className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      placeholder="2500.00"
                    />
                  </div>
                </div>
                <div className="mt-4 flex justify-end">
                  <button
                    onClick={addDemoHolding}
                    className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                  >
                    Add Holding
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Pipeline Orders Section */}
          {user && pendingOrders.length > 0 && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ClockIcon className="h-5 w-5 text-yellow-500" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Pipeline Orders ({pendingOrders.length})
                  </h3>
                </div>
                <button
                  onClick={() => setShowPipelineOrders(!showPipelineOrders)}
                  className="text-sm text-blue-500 hover:text-blue-700 dark:text-blue-400"
                >
                  {showPipelineOrders ? 'Hide' : 'Show'} Details
                </button>
              </div>
              {showPipelineOrders && (
                <div className="p-4">
                  <div className="space-y-2">
                    {pendingOrders.map((order) => (
                      <div
                        key={order.id}
                        className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <ClockIcon className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">
                              {order.symbol} - {order.order_type} {order.order_side || 'MARKET'}
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              Qty: {order.quantity} @ {order.price ? `₹${order.price.toFixed(2)}` : 'Market Price'}
                            </div>
                          </div>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {new Date(order.order_time || order.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Holdings Table */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Stock Holdings</h3>
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <span className="text-xs">Last updated: {new Date().toLocaleTimeString()}</span>
                <button
                  onClick={fetchData}
                  className="text-blue-500 hover:text-blue-700 dark:text-blue-400"
                  title="Refresh prices"
                >
                  ↻ Refresh
                </button>
              </div>
            </div>
            {holdings.length === 0 ? (
              <div className="text-center py-12">
                <BriefcaseIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Holdings</h3>
                <p className="text-gray-600 dark:text-gray-400">You don't have any stock holdings yet.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Symbol</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Quantity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Avg Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Current Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Invested</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Current Value</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">P&L</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">P&L %</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {holdings.map((holding, index) => (
                      <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => navigate(`/comprehensive-trading-pro?symbol=${holding.symbol}`)}
                            className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:underline cursor-pointer transition-colors"
                            title={`View ${holding.symbol} on Comprehensive Trading Pro`}
                          >
                            {holding.symbol}
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">{holding.quantity}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">{holding.formatted_average_price || holding.currency_symbol + holding.average_price.toFixed(2)}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">{holding.formatted_current_price || holding.currency_symbol + holding.current_price.toFixed(2)}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">{holding.currency_symbol}{holding.invested_value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">{holding.formatted_total_value || holding.currency_symbol + holding.total_value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`text-sm font-medium ${holding.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {holding.formatted_pnl || holding.currency_symbol + holding.pnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: 'always' })}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`text-sm font-medium ${holding.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {holding.pnl_percent.toFixed(2)}%
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <BuySellButton
                            symbol={holding.symbol}
                            currentPrice={holding.current_price}
                            size="sm"
                            onOrderPlaced={async () => {
                              await fetchData();
                              await fetchPendingOrders();
                              toast.success('Portfolio updated!');
                            }}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Order Book Section - Executed and Pipeline Orders */}
          {user && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ClipboardDocumentListIcon className="h-5 w-5 text-blue-500" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Order Book</h3>
                    <span className="text-sm text-gray-500 dark:text-gray-400">(Executed & Pipeline Orders)</span>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                  View all your executed orders and pending pipeline orders. Filter by status or symbol to find specific orders.
                </p>
              </div>
              <div className="p-4">
                <OrderBook visible={true} />
              </div>
            </div>
          )}
        </div>
      );
    }

    if (!selectedPortfolio) {
      return (
        <div className="text-center py-12">
          <ChartPieIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Portfolio Selected</h3>
          <p className="text-gray-600 dark:text-gray-400">Select a portfolio or create a new one to get started.</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="flex items-center">
                  <CurrencyDollarIcon className="h-8 w-8 text-green-500 mr-3" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Total Value</h3>
                    <p className="text-2xl font-bold text-green-600">
                      ₹{selectedPortfolio.total_value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="flex items-center">
                  <ChartBarIcon className="h-8 w-8 text-blue-500 mr-3" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Assets</h3>
                    <p className="text-2xl font-bold text-blue-600">{selectedPortfolio.assets.length}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="h-8 w-8 text-orange-500 mr-3" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Rebalancing</h3>
                    <p className="text-lg font-bold text-orange-600">
                      {selectedPortfolio.rebalancing_needed ? 'Needed' : 'Not Needed'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Risk Metrics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Portfolio Volatility</span>
                    <span className="font-medium">{selectedPortfolio.risk_metrics.portfolio_volatility.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
                    <span className="font-medium">{selectedPortfolio.risk_metrics.sharpe_ratio.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Max Drawdown</span>
                    <span className="font-medium">{selectedPortfolio.risk_metrics.max_drawdown.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">VaR (95%)</span>
                    <span className="font-medium">₹{selectedPortfolio.risk_metrics.var_95.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Portfolio Information</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Last Rebalanced</span>
                    <span className="font-medium">
                      {new Date(selectedPortfolio.last_rebalanced).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Next Rebalance</span>
                    <span className="font-medium">
                      {new Date(selectedPortfolio.next_rebalance_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Max Single Position</span>
                    <span className="font-medium">{selectedPortfolio.constraints.max_single_position}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Max Sector Allocation</span>
                    <span className="font-medium">{selectedPortfolio.constraints.max_sector_allocation}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'allocation':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Current Allocation</h3>
                <AssetAllocationChart 
                  allocation={selectedPortfolio.current_allocation} 
                  totalValue={selectedPortfolio.total_value}
                />
              </div>

              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Target Allocation</h3>
                <AssetAllocationChart 
                  allocation={selectedPortfolio.target_allocation} 
                  totalValue={selectedPortfolio.total_value}
                />
              </div>
            </div>

            <AssetManagement portfolio={selectedPortfolio} onUpdate={setSelectedPortfolio} />
          </div>
        );

      case 'rebalancing':
        return (
          <div className="space-y-6">
            {/* Current vs Target Allocation Comparison */}
            {selectedPortfolio && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4">Current Allocation</h3>
                  <AssetAllocationChart 
                    allocation={selectedPortfolio.current_allocation} 
                    totalValue={selectedPortfolio.total_value}
                  />
                </div>
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4">Target Allocation</h3>
                  <AssetAllocationChart 
                    allocation={selectedPortfolio.target_allocation} 
                    totalValue={selectedPortfolio.total_value}
                  />
                </div>
              </div>
            )}

            {/* Allocation Drift Analysis */}
            {unifiedData?.allocation?.drift && (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Allocation Drift Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Equity Drift</div>
                    <div className={`text-2xl font-bold ${unifiedData.allocation.drift.equity_drift >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {unifiedData.allocation.drift.equity_drift > 0 ? '+' : ''}{unifiedData.allocation.drift.equity_drift.toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Bond Drift</div>
                    <div className={`text-2xl font-bold ${unifiedData.allocation.drift.bond_drift >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {unifiedData.allocation.drift.bond_drift > 0 ? '+' : ''}{unifiedData.allocation.drift.bond_drift.toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Cash Drift</div>
                    <div className={`text-2xl font-bold ${unifiedData.allocation.drift.cash_drift >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {unifiedData.allocation.drift.cash_drift > 0 ? '+' : ''}{unifiedData.allocation.drift.cash_drift.toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Max Drift</div>
                    <div className={`text-2xl font-bold ${unifiedData.allocation.drift.max_drift > 5 ? 'text-orange-600' : 'text-green-600'}`}>
                      {unifiedData.allocation.drift.max_drift.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {unifiedData.allocation.drift.drift_severity || 'Minimal'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Rebalancing Recommendation */}
            {rebalancingRecommendation ? (
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Rebalancing Recommendation</h3>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center">
                      {rebalancingRecommendation.rebalancing_needed ? (
                        <ExclamationTriangleIcon className="h-5 w-5 text-orange-500 mr-2" />
                      ) : (
                        <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      )}
                      <span className={cn(
                        "font-medium",
                        rebalancingRecommendation.rebalancing_needed ? "text-orange-600" : "text-green-600"
                      )}>
                        {rebalancingRecommendation.rebalancing_needed ? 'Rebalancing Needed' : 'Portfolio Balanced'}
                      </span>
                    </div>
                    <button
                      onClick={fetchRebalancingRecommendation}
                      className="text-sm text-blue-500 hover:text-blue-700 dark:text-blue-400"
                      title="Refresh recommendations"
                    >
                      ↻ Refresh
                    </button>
                    </div>
                  </div>

                {rebalancingRecommendation.rebalancing_needed ? (
                    <div className="space-y-4">
                    {/* Expected Benefits */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">
                            {rebalancingRecommendation.expected_benefits.risk_reduction.toFixed(2)}%
                          </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Risk Reduction</div>
                        </div>
                      <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">
                            {rebalancingRecommendation.expected_benefits.return_improvement.toFixed(2)}%
                          </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Return Improvement</div>
                        </div>
                      <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                          <div className="text-2xl font-bold text-purple-600">
                            ₹{rebalancingRecommendation.expected_benefits.transaction_costs.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Transaction Costs</div>
                      </div>
                      <div className="text-center p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                        <div className="text-2xl font-bold text-indigo-600">
                          ₹{rebalancingRecommendation.expected_benefits.net_benefit.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Net Benefit</div>
                        </div>
                      </div>

                    {/* Recommended Actions */}
                    {rebalancingRecommendation.recommended_actions.length > 0 ? (
                      <div className="space-y-3">
                        <h4 className="font-medium text-gray-900 dark:text-white">Recommended Actions</h4>
                        {rebalancingRecommendation.recommended_actions.map((action, index) => (
                          <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                            <div className="flex items-center gap-4">
                              <span className={cn(
                                "px-3 py-1 text-xs font-medium rounded-full",
                                action.priority === 'high' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                                action.priority === 'medium' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                                "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                              )}>
                                {action.priority.toUpperCase()}
                              </span>
                              <div>
                                <div className="font-semibold text-gray-900 dark:text-white">{action.symbol}</div>
                                <div className={cn(
                                  "text-sm font-medium",
                                  action.action === 'buy' ? "text-green-600" : "text-red-600"
                                )}>
                                  {action.action.toUpperCase()} - Deviation: {action.deviation > 0 ? '+' : ''}{action.deviation.toFixed(1)}%
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-semibold text-gray-900 dark:text-white">
                                ₹{action.value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </div>
                              <div className="text-sm text-gray-600 dark:text-gray-400">
                                {action.current_weight.toFixed(1)}% → {action.target_weight.toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-600 dark:text-gray-400">
                        No specific actions recommended. Portfolio is within acceptable drift range.
                      </div>
                    )}

                    {/* Implementation Plan */}
                    {rebalancingRecommendation.implementation_plan.phases.length > 0 && (
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <h4 className="font-medium mb-3 text-gray-900 dark:text-white">Implementation Plan</h4>
                        <div className="space-y-2">
                          {rebalancingRecommendation.implementation_plan.phases.map((phase, index) => (
                            <div key={index} className="text-sm text-gray-700 dark:text-gray-300">
                              <span className="font-medium">Phase {phase.phase}:</span> {phase.description} - {phase.timeline}
                            </div>
                          ))}
                        </div>
                        <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
                          Total Timeline: {rebalancingRecommendation.implementation_plan.total_timeline}
                        </div>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <button
                        onClick={fetchRebalancingRecommendation}
                        className="px-6 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-500"
                      >
                        Recalculate
                      </button>
                        <button
                          onClick={handleExecuteRebalancing}
                        disabled={loading}
                        className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        {loading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            Processing...
                          </>
                        ) : (
                          'Analyze Rebalancing'
                        )}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-4" />
                    <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">Portfolio is Balanced</p>
                    <p className="text-gray-600 dark:text-gray-400">
                      Your current allocation is within acceptable range of your target allocation.
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                      Current deviation: {rebalancingRecommendation.current_deviation.toFixed(2)}%
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="text-center py-8">
                  <p className="text-gray-600 dark:text-gray-400 mb-4">Loading rebalancing recommendations...</p>
                  <button
                    onClick={fetchRebalancingRecommendation}
                          className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                        >
                    Load Recommendations
                        </button>
                      </div>
                    </div>
                  )}

            {/* Order Book Section - Executed and Pipeline Orders */}
            {user && (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ClipboardDocumentListIcon className="h-5 w-5 text-blue-500" />
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Order Book</h3>
                      <span className="text-sm text-gray-500 dark:text-gray-400">(Executed & Pipeline Orders)</span>
                </div>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    View all your executed orders and pending pipeline orders. Filter by status or symbol to find specific orders.
                  </p>
                </div>
                <div className="p-4">
                  <OrderBook visible={true} />
                </div>
              </div>
            )}
          </div>
        );

      case 'strategies':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {strategies.map((strategy) => (
                <div
                  key={strategy.id}
                  className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-lg transition-shadow"
                >
                    <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{strategy.name}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{strategy.type}</p>
                    </div>
                    <span className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                      {strategy?.suitability?.risk_tolerance ?? 'medium'}
                    </span>
                  </div>

                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">{strategy.description}</p>

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Expected Return</span>
                      <span className="font-medium">{(strategy.expected_performance?.return ?? 0).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Volatility</span>
                      <span className="font-medium">{(strategy.expected_performance?.volatility ?? 0).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
                      <span className="font-medium">{(strategy.expected_performance?.sharpe_ratio ?? 0).toFixed(2)}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleApplyStrategy(strategy.id)}
                    className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors"
                  >
                    Apply Strategy
                  </button>
                </div>
              ))}
            </div>
          </div>
        );

      case 'optimization':
        return <PortfolioOptimization />;

      case 'fno':
        return user ? (
          <div className="h-full">
            <FNOTrading />
          </div>
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-gray-600 dark:text-gray-400 mb-4">Please log in to access F&O Trading</p>
            </div>
          </div>
        );

      case 'intraday':
        return user ? (
          <div className="h-full">
            <IntradayTrading />
          </div>
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-gray-600 dark:text-gray-400 mb-4">Please log in to access Intraday Trading</p>
            </div>
          </div>
        );

      case 'optimization':
        return (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Portfolio Optimization</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Optimize your portfolio allocation based on risk-return objectives and constraints.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Optimization Parameters</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Target Return (%)
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        placeholder="12.0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Risk Tolerance
                      </label>
                      <select className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white">
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Max Single Position (%)
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        placeholder="20"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-3">Constraints</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Max Sector Allocation (%)
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        placeholder="30"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Min Liquidity Requirement
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        placeholder="1000000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Rebalancing Threshold (%)
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        placeholder="5"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">
                  Optimize Portfolio
                </button>
              </div>
            </div>
          </div>
        );

      case 'insights':
        return (
          <div className="space-y-6">
            {loadingInsights ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-400">Loading insights...</p>
              </div>
            ) : (
              <>
                {/* AI Signals from Research Reports */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">AI Trading Signals</h3>
                    <button
                      onClick={fetchInsightsData}
                      className="text-sm text-blue-500 hover:text-blue-700"
                    >
                      Refresh
                    </button>
                  </div>
                  {aiSignals.length === 0 ? (
                    <p className="text-gray-600 dark:text-gray-400">No signals available. Generate research reports for your holdings.</p>
                  ) : (
                    <div className="space-y-3">
                      {aiSignals.map((signal, index) => (
                        <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-medium text-gray-900 dark:text-white">{signal.symbol}</div>
                              <div className={`text-sm font-medium ${
                                signal.action === 'BUY' ? 'text-green-600' :
                                signal.action === 'SELL' ? 'text-red-600' : 'text-yellow-600'
                              }`}>
                                {signal.action} - Confidence: {(signal.confidence * 100).toFixed(0)}%
                              </div>
                              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                {signal.reasoning || 'No reasoning provided'}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-gray-600 dark:text-gray-400">1M Target</div>
                              <div className="font-medium">₹{signal.price_target_1m?.toFixed(2) || 'N/A'}</div>
                              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">3M Target</div>
                              <div className="font-medium">₹{signal.price_target_3m?.toFixed(2) || 'N/A'}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Real Risk Metrics */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4">Risk Metrics (Historical Data)</h3>
                  {riskMetrics && riskMetrics.success ? (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</div>
                        <div className="text-xl font-bold">{riskMetrics.sharpe_ratio || 'N/A'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Beta</div>
                        <div className="text-xl font-bold">{riskMetrics.beta || 'N/A'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</div>
                        <div className="text-xl font-bold">{riskMetrics.max_drawdown?.toFixed(2) || 'N/A'}%</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Volatility</div>
                        <div className="text-xl font-bold">{riskMetrics.volatility?.toFixed(2) || 'N/A'}%</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Annual Return</div>
                        <div className="text-xl font-bold">{riskMetrics.annualized_return?.toFixed(2) || 'N/A'}%</div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400">Insufficient historical data for risk metrics calculation.</p>
                  )}
                </div>

                {/* Sector Allocation */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4">Sector Allocation</h3>
                  {sectorAllocation.sector_allocation && Object.keys(sectorAllocation.sector_allocation).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(sectorAllocation.sector_allocation).map(([sector, data]: [string, any]) => (
                        <div key={sector} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="font-medium text-gray-900 dark:text-white">{sector}</div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              {data.percentage.toFixed(2)}% - ₹{data.value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${data.percentage}%` }}
                            />
                          </div>
                          <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                            Holdings: {data.holdings.map((h: any) => h.symbol).join(', ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400">No sector allocation data available.</p>
                  )}
                </div>

                {/* Volume Analysis */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4">Volume Analysis</h3>
                  {volumeAnalysis ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">Total Volume</div>
                          <div className="text-xl font-bold">{volumeAnalysis.total_volume?.toLocaleString('en-IN') || '0'}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">Avg Volume</div>
                          <div className="text-xl font-bold">{volumeAnalysis.average_volume?.toLocaleString('en-IN') || '0'}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">Trend</div>
                          <div className={`text-xl font-bold ${
                            volumeAnalysis.volume_trend === 'INCREASING' ? 'text-green-600' :
                            volumeAnalysis.volume_trend === 'DECREASING' ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {volumeAnalysis.volume_trend || 'NEUTRAL'}
                          </div>
                        </div>
                      </div>
                      
                      {volumeAnalysis.volume_signals && volumeAnalysis.volume_signals.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Volume Signals</h4>
                          <div className="space-y-2">
                            {volumeAnalysis.volume_signals.map((signal: any, index: number) => (
                              <div key={index} className="flex items-center justify-between p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                                <span className="font-medium">{signal.symbol}</span>
                                <span className="text-sm">{signal.signal} - {signal.strength}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400">No volume analysis data available.</p>
                  )}
                </div>

                {/* Market Intelligence Insights */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4">Market Intelligence</h3>
                  {marketInsights ? (
                    <div className="space-y-4">
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Market Sentiment</div>
                        <div className="text-2xl font-bold">
                          {((marketInsights.market_sentiment || 0.5) * 100).toFixed(0)}%
                        </div>
                      </div>
                      
                      {marketInsights.key_insights && marketInsights.key_insights.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Key Insights</h4>
                          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                            {marketInsights.key_insights.slice(0, 5).map((insight: string, index: number) => (
                              <li key={index}>{insight}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {marketInsights.news_summary && marketInsights.news_summary.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Top News</h4>
                          <div className="space-y-2">
                            {marketInsights.news_summary.map((news: any, index: number) => (
                              <div key={index} className="p-2 bg-gray-50 dark:bg-gray-700 rounded text-sm">
                                <div className="font-medium">{news.title || 'No title'}</div>
                                <div className="text-gray-600 dark:text-gray-400 text-xs mt-1">
                                  {news.source || 'Unknown source'}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400">No market intelligence data available.</p>
                  )}
                </div>
              </>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} />;
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Portfolio Allocation Tools</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage and optimize your portfolio allocation</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={selectedPortfolio?.id || ''}
            onChange={(e) => {
              const portfolio = portfolios.find(p => p.id === e.target.value);
              setSelectedPortfolio(portfolio || null);
            }}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
          >
            <option value="">Select Portfolio</option>
            {portfolios.map((portfolio) => (
              <option key={portfolio.id} value={portfolio.id}>{portfolio.name}</option>
            ))}
          </select>
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            New Portfolio
          </button>
        </div>
      </div>

      {/* Create Portfolio Form */}
      {showCreateForm && (
        <div className="p-6 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <h3 className="text-lg font-semibold mb-4">Create New Portfolio</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Portfolio Name
              </label>
              <input
                type="text"
                value={newPortfolio.name || ''}
                onChange={(e) => setNewPortfolio(prev => ({ ...prev, name: e.target.value }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="My Portfolio"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <input
                type="text"
                value={newPortfolio.description || ''}
                onChange={(e) => setNewPortfolio(prev => ({ ...prev, description: e.target.value }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="Portfolio description"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Total Value (₹)
              </label>
              <input
                type="number"
                value={newPortfolio.total_value || ''}
                onChange={(e) => setNewPortfolio(prev => ({ ...prev, total_value: parseFloat(e.target.value) }))}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                placeholder="100000"
              />
            </div>
          </div>
          <div className="flex justify-end space-x-2 mt-4">
            <button
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={handleCreatePortfolio}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
              Create Portfolio
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b dark:border-gray-700 overflow-x-auto">
        {[
          { id: 'holdings', name: 'Holdings', icon: BriefcaseIcon },
          { id: 'overview', name: 'Overview', icon: ChartBarIcon },
          { id: 'allocation', name: 'Allocation', icon: ChartPieIcon },
          { id: 'rebalancing', name: 'Rebalancing', icon: AdjustmentsHorizontalIcon },
          { id: 'insights', name: 'Insights', icon: SparklesIcon },
          { id: 'strategies', name: 'Strategies', icon: CalculatorIcon },
          { id: 'optimization', name: 'Optimization', icon: ArrowTrendingUpIcon },
          ...(user ? [
            { id: 'fno', name: 'F&O Trading', icon: ChartBarIcon },
            { id: 'intraday', name: 'Intraday Trading', icon: ClockIcon }
          ] : [])
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              "flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors",
              activeTab === tab.id
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
            )}
          >
            <tab.icon className="h-5 w-5 mr-2" />
            {tab.name}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default PortfolioAllocationTools;
