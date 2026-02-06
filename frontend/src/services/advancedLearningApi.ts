/**
 * Advanced Learning API Service
 * Frontend service for interacting with advanced learning endpoints
 */

import { httpClient, APIResponse } from '../config/api';

export interface ModelRetrainingStatus {
  status: string;
  current_accuracy?: number;
  average_accuracy?: number;
  trend?: string;
  needs_retraining?: boolean;
  last_retrained?: string;
  performance_history_count?: number;
}

export interface FeatureSelectionResult {
  success: boolean;
  method?: string;
  selected_features?: string[];
  feature_scores?: Record<string, number>;
  n_features?: number;
  total_features?: number;
  reduction?: string;
}

export interface AlgorithmSelectionResult {
  success: boolean;
  symbol?: string;
  selected_algorithm?: string;
  previous_algorithm?: string;
  algorithm_changed?: boolean;
  reasoning?: string;
  all_performances?: Record<string, any>;
}

export interface ParameterTuningResult {
  optimized: boolean;
  model_name?: string;
  old_parameters?: Record<string, number>;
  new_parameters?: Record<string, number>;
  performance?: Record<string, number>;
  optimization_target?: string;
  changes?: Record<string, any>;
}

export interface CurrentParametersResult {
  model_name: string;
  current_parameters: Record<string, number>;
  recent_history: Array<{
    parameters: Record<string, number>;
    performance: Record<string, number>;
    timestamp: string;
  }>;
}

export interface ThresholdAdjustmentResult {
  success: boolean;
  threshold_name?: string;
  old_value?: number;
  new_value?: number;
  adjustment?: number;
  reason?: string;
}

export interface AdvancedLearningStatus {
  success: boolean;
  data?: {
    timestamp?: string;
    services?: {
      retraining?: ModelRetrainingStatus;
      algorithm_selection?: any;
      parameter_tuning?: {
        current_parameters?: Record<string, number>;
        recent_history?: any[];
      };
      feature_selection?: {
        selected_features?: string[];
        feature_importance?: Record<string, number>;
      };
    };
  };
}

class AdvancedLearningApiService {
  private baseUrl = '/api/advanced-learning';

  /**
   * Check if model needs retraining
   */
  async checkModelRetraining(
    modelName: string,
    performanceMetrics: Record<string, number>
  ): Promise<ModelRetrainingStatus> {
    try {
      const response = await httpClient.post<ModelRetrainingStatus>(
        `${this.baseUrl}/model-retraining/check`,
        {
          model_name: modelName,
          performance_metrics: performanceMetrics,
          new_data_available: true
        }
      );

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to check model retraining');
      }

      return response.data;
    } catch (error: any) {
      console.error('Error checking model retraining:', error);
      throw error;
    }
  }

  /**
   * Get selected features for a model
   */
  async getSelectedFeatures(modelName: string): Promise<FeatureSelectionResult> {
    try {
      const response = await httpClient.get<FeatureSelectionResult>(
        `${this.baseUrl}/feature-selection/features/${modelName}`
      );

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get selected features');
      }

      return response.data;
    } catch (error: any) {
      console.error('Error getting selected features:', error);
      throw error;
    }
  }

  /**
   * Get algorithm recommendations for a symbol
   */
  async getAlgorithmRecommendations(symbol: string): Promise<AlgorithmSelectionResult> {
    try {
      const response = await httpClient.get<any>(
        `${this.baseUrl}/algorithm-selection/recommendations/${symbol}`
      );

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get algorithm recommendations');
      }

      return response.data;
    } catch (error: any) {
      console.error('Error getting algorithm recommendations:', error);
      throw error;
    }
  }

  /**
   * Get current parameters for a model
   */
  async getCurrentParameters(modelName: string): Promise<CurrentParametersResult> {
    try {
      const response = await httpClient.get<CurrentParametersResult>(
        `${this.baseUrl}/parameter-tuning/parameters/${modelName}`
      );

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get current parameters');
      }

      // response.data is guaranteed to be defined after the check above
      return response.data;
    } catch (error: any) {
      console.error('Error getting current parameters:', error);
      throw error;
    }
  }

  /**
   * Adjust threshold based on performance
   */
  async adjustThreshold(
    thresholdName: string,
    currentValue: number,
    performanceFeedback: Record<string, number>,
    adjustmentRate: number = 0.1
  ): Promise<ThresholdAdjustmentResult> {
    try {
      const response = await httpClient.post<ThresholdAdjustmentResult>(
        `${this.baseUrl}/parameter-tuning/adjust-threshold`,
        {
          threshold_name: thresholdName,
          current_value: currentValue,
          performance_feedback: performanceFeedback,
          adjustment_rate: adjustmentRate
        }
      );

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to adjust threshold');
      }

      return response.data;
    } catch (error: any) {
      console.error('Error adjusting threshold:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive status of all advanced learning features
   */
  async getStatus(symbol?: string, modelName?: string): Promise<AdvancedLearningStatus> {
    try {
      const params: Record<string, string> = {};
      if (symbol) params.symbol = symbol;
      if (modelName) params.model_name = modelName;

      const response = await httpClient.get<AdvancedLearningStatus['data']>(
        `${this.baseUrl}/status`,
        { params }
      );

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get advanced learning status');
      }

      return {
        success: true,
        data: response.data
      };
    } catch (error: any) {
      console.error('Error getting advanced learning status:', error);
      throw error;
    }
  }

  /**
   * Process a complete learning cycle
   */
  async processLearningCycle(
    symbol: string,
    modelName: string,
    performanceMetrics: Record<string, number>,
    context?: Record<string, any>
  ): Promise<any> {
    try {
      const response = await httpClient.post<any>(
        `${this.baseUrl}/learning-cycle`,
        {
          symbol,
          model_name: modelName,
          performance_metrics: performanceMetrics,
          context
        }
      );

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to process learning cycle');
      }

      return response.data;
    } catch (error: any) {
      console.error('Error processing learning cycle:', error);
      throw error;
    }
  }
}

export const advancedLearningApi = new AdvancedLearningApiService();
export default advancedLearningApi;

