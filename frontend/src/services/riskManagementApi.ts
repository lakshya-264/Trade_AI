/**
 * Risk Management API Service
 * Integrates with backend /api/risk/* endpoints
 */

import { httpClient, APIResponse } from '../config/api';

// Risk Management API Response Interfaces
export interface RiskMetricsResponse {
  portfolio_risk: {
    total_value: number;
    total_risk: number;
    risk_percentage: number;
    var_95: number;
    var_99: number;
    expected_shortfall: number;
    max_drawdown: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    calmar_ratio: number;
  };
  position_risks: Array<{
    symbol: string;
    position_value: number;
    risk_contribution: number;
    beta: number;
    volatility: number;
    var_contribution: number;
    concentration_risk: 'low' | 'medium' | 'high';
  }>;
  sector_risks: Array<{
    sector: string;
    allocation: number;
    risk_contribution: number;
    concentration_risk: 'low' | 'medium' | 'high';
    correlation_risk: number;
  }>;
  correlation_matrix: Record<string, Record<string, number>>;
  stress_test_results: {
    market_crash_scenario: {
      portfolio_loss: number;
      worst_performing_positions: string[];
      recovery_time_estimate: string;
    };
    sector_rotation_scenario: {
      portfolio_impact: number;
      affected_sectors: string[];
      rebalancing_needed: boolean;
    };
    volatility_spike_scenario: {
      portfolio_impact: number;
      risk_increase: number;
      hedging_recommendations: string[];
    };
  };
  risk_limits: {
    max_position_size: number;
    max_sector_allocation: number;
    max_portfolio_risk: number;
    var_limit: number;
    drawdown_limit: number;
  };
  compliance_status: {
    position_limits_breached: string[];
    sector_limits_breached: string[];
    risk_limits_breached: string[];
    overall_compliance: 'compliant' | 'warning' | 'breach';
  };
  recommendations: Array<{
    type: 'position_adjustment' | 'sector_rebalancing' | 'risk_reduction' | 'hedging';
    priority: 'high' | 'medium' | 'low';
    description: string;
    impact: string;
    action_required: string;
  }>;
  last_updated: string;
}

export interface PortfolioAllocationResponse {
  current_allocation: Array<{
    symbol: string;
    sector: string;
    current_weight: number;
    target_weight: number;
    deviation: number;
    market_cap: 'small' | 'mid' | 'large';
    risk_level: 'low' | 'medium' | 'high';
  }>;
  sector_allocation: Array<{
    sector: string;
    current_weight: number;
    target_weight: number;
    deviation: number;
    risk_level: 'low' | 'medium' | 'high';
    top_holdings: string[];
  }>;
  market_cap_allocation: Array<{
    market_cap: 'small' | 'mid' | 'large';
    current_weight: number;
    target_weight: number;
    deviation: number;
    risk_level: 'low' | 'medium' | 'high';
  }>;
  rebalancing_needed: boolean;
  rebalancing_priority: Array<{
    symbol: string;
    action: 'BUY' | 'SELL' | 'HOLD';
    quantity: number;
    priority: 'high' | 'medium' | 'low';
    reasoning: string;
    impact: string;
  }>;
  risk_adjustments: Array<{
    type: 'position_size' | 'sector_weight' | 'correlation' | 'volatility';
    symbol?: string;
    sector?: string;
    current_value: number;
    recommended_value: number;
    reasoning: string;
  }>;
  last_updated: string;
}

export interface StressTestRequest {
  scenarios: Array<{
    name: string;
    type: 'market_crash' | 'sector_rotation' | 'volatility_spike' | 'interest_rate_change' | 'currency_movement';
    parameters: Record<string, number>;
    duration: '1_day' | '1_week' | '1_month' | '3_months' | '6_months' | '1_year';
  }>;
  portfolio_data: Array<{
    symbol: string;
    quantity: number;
    current_price: number;
    sector: string;
    market_cap: 'small' | 'mid' | 'large';
  }>;
}

export interface StressTestResponse {
  test_results: Array<{
    scenario_name: string;
    scenario_type: string;
    duration: string;
    portfolio_impact: {
      total_loss: number;
      loss_percentage: number;
      worst_day_loss: number;
      recovery_time: string;
    };
    position_impacts: Array<{
      symbol: string;
      price_change: number;
      value_change: number;
      impact_percentage: number;
    }>;
    sector_impacts: Array<{
      sector: string;
      impact_percentage: number;
      worst_performers: string[];
    }>;
    risk_metrics: {
      var_95: number;
      var_99: number;
      expected_shortfall: number;
      max_drawdown: number;
    };
    recommendations: Array<{
      type: 'hedging' | 'rebalancing' | 'position_adjustment';
      priority: 'high' | 'medium' | 'low';
      description: string;
      expected_benefit: string;
    }>;
  }>;
  summary: {
    worst_case_scenario: string;
    maximum_loss: number;
    average_recovery_time: string;
    overall_portfolio_resilience: 'high' | 'medium' | 'low';
  };
  last_updated: string;
}

export interface RiskLimitsRequest {
  position_limits: {
    max_single_position: number;
    max_position_percentage: number;
  };
  sector_limits: {
    max_sector_allocation: number;
    restricted_sectors: string[];
  };
  risk_limits: {
    max_portfolio_var: number;
    max_drawdown_limit: number;
    max_volatility_limit: number;
  };
  compliance_settings: {
    alert_thresholds: {
      position_breach: number;
      sector_breach: number;
      risk_breach: number;
    };
    auto_rebalancing: boolean;
    stop_loss_enabled: boolean;
  };
}

export interface RiskLimitsResponse {
  current_limits: RiskLimitsRequest;
  compliance_status: {
    position_compliance: 'compliant' | 'warning' | 'breach';
    sector_compliance: 'compliant' | 'warning' | 'breach';
    risk_compliance: 'compliant' | 'warning' | 'breach';
    overall_status: 'compliant' | 'warning' | 'breach';
  };
  breaches: Array<{
    type: 'position' | 'sector' | 'risk';
    symbol?: string;
    sector?: string;
    current_value: number;
    limit_value: number;
    breach_percentage: number;
    severity: 'minor' | 'moderate' | 'severe';
  }>;
  recommendations: Array<{
    type: 'limit_adjustment' | 'position_reduction' | 'sector_rebalancing';
    priority: 'high' | 'medium' | 'low';
    description: string;
    action_required: string;
    expected_impact: string;
  }>;
  last_updated: string;
}

// Risk Management API Service Class
class RiskManagementApiService {
  
  // Get Risk Metrics
  async getRiskMetrics(): Promise<RiskMetricsResponse> {
    const response = await httpClient.get<RiskMetricsResponse>('/risk/metrics');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get risk metrics');
    }
    
    return response.data;
  }

  // Get Portfolio Allocation
  async getPortfolioAllocation(): Promise<PortfolioAllocationResponse> {
    const response = await httpClient.get<PortfolioAllocationResponse>('/risk/allocation');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get portfolio allocation');
    }
    
    return response.data;
  }

  // Run Stress Test
  async runStressTest(request: StressTestRequest): Promise<StressTestResponse> {
    const response = await httpClient.post<StressTestResponse>('/risk/stress-test', request);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to run stress test');
    }
    
    return response.data;
  }

  // Get Risk Limits
  async getRiskLimits(): Promise<RiskLimitsResponse> {
    const response = await httpClient.get<RiskLimitsResponse>('/risk/limits');
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to get risk limits');
    }
    
    return response.data;
  }

  // Update Risk Limits
  async updateRiskLimits(request: RiskLimitsRequest): Promise<RiskLimitsResponse> {
    const response = await httpClient.post<RiskLimitsResponse>('/risk/limits', request);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || 'Failed to update risk limits');
    }
    
    return response.data;
  }

  // Get Risk Alerts
  async getRiskAlerts(): Promise<APIResponse<any[]>> {
    const response = await httpClient.get<any[]>('/risk/alerts');
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get risk alerts');
    }
    
    return response;
  }

  // Get Risk Reports
  async getRiskReports(): Promise<APIResponse<any[]>> {
    const response = await httpClient.get<any[]>('/risk/reports');
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get risk reports');
    }
    
    return response;
  }
}

// Create and export service instance
export const riskManagementApi = new RiskManagementApiService();
export default riskManagementApi;
