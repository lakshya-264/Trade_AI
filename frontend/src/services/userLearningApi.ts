/**
 * User Learning API Service
 * Handles user feedback and behavior tracking
 */

import { httpClient, APIResponse } from '../config/api';

export interface FeedbackRequest {
  entity_type: 'prediction' | 'recommendation' | 'analysis';
  entity_id: string;
  feedback_type: 'helpful' | 'not_helpful' | 'accurate' | 'inaccurate' | 'useful' | 'not_useful';
  symbol?: string;
  rating?: number; // 1-5
  comment?: string;
  metadata?: Record<string, any>;
}

export interface BehaviorTrackingRequest {
  action_type: 'viewed_prediction' | 'followed_recommendation' | 'ignored_recommendation' | 'placed_order' | 'viewed_analysis';
  entity_type: 'prediction' | 'recommendation' | 'analysis' | 'order';
  entity_id: string;
  symbol?: string;
  metadata?: Record<string, any>;
  session_id?: string;
  referrer?: string;
}

export interface FeedbackStats {
  total_feedback: number;
  positive_feedback: number;
  negative_feedback: number;
  satisfaction_rate: number;
  average_rating: number | null;
  feedback_by_type: Record<string, number>;
}

export interface BehaviorInsights {
  total_actions: number;
  action_breakdown: Record<string, number>;
  entity_type_breakdown: Record<string, number>;
  top_symbols: Record<string, number>;
  recommendation_acceptance_rate: number;
  most_active_day: string | null;
}

export interface InferredPreferences {
  inferred_risk_tolerance: string;
  preferred_symbols: Record<string, number>;
  preferred_analysis_types: string[];
  confidence_threshold: number;
  trading_frequency: string;
}

class UserLearningApiService {
  private baseUrl = '/api/user-learning';

  /**
   * Submit user feedback
   */
  async submitFeedback(request: FeedbackRequest): Promise<APIResponse<any>> {
    try {
      const response = await httpClient.post<APIResponse<any>>(
        `${this.baseUrl}/feedback`,
        request
      );
      return response;
    } catch (error: any) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
  }

  /**
   * Track user behavior
   */
  async trackBehavior(request: BehaviorTrackingRequest): Promise<APIResponse<any>> {
    try {
      const response = await httpClient.post<APIResponse<any>>(
        `${this.baseUrl}/behavior`,
        request
      );
      return response;
    } catch (error: any) {
      console.error('Error tracking behavior:', error);
      throw error;
    }
  }

  /**
   * Get user feedback statistics
   */
  async getFeedbackStats(days: number = 30): Promise<FeedbackStats> {
    try {
      const response = await httpClient.get<FeedbackStats>(
        `${this.baseUrl}/feedback/stats`,
        { params: { days } }
      );
      
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get feedback stats');
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error getting feedback stats:', error);
      throw error;
    }
  }

  /**
   * Get user behavior insights
   */
  async getBehaviorInsights(days: number = 30): Promise<BehaviorInsights> {
    try {
      const response = await httpClient.get<BehaviorInsights>(
        `${this.baseUrl}/behavior/insights`,
        { params: { days } }
      );
      
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get behavior insights');
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error getting behavior insights:', error);
      throw error;
    }
  }

  /**
   * Get inferred user preferences
   */
  async getInferredPreferences(): Promise<InferredPreferences> {
    try {
      const response = await httpClient.get<InferredPreferences>(
        `${this.baseUrl}/preferences/inferred`
      );
      
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get inferred preferences');
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error getting inferred preferences:', error);
      throw error;
    }
  }
}

export const userLearningApi = new UserLearningApiService();
export default userLearningApi;

