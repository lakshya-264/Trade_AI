/**
 * Alert System API
 * Manage price alerts, structure break alerts, and notifications
 */

import { httpClient } from '../config/api';

export interface Alert {
  id?: string;
  symbol: string;
  alert_type: string;
  condition: string;
  target_price?: number;
  level_id?: string;
  threshold_percent: number;
  enabled: boolean;
  notify_browser: boolean;
  notify_sound: boolean;
  notify_email: boolean;
  created_at?: string;
  triggered_at?: string;
  trigger_count?: number;
}

export interface AlertResponse {
  success: boolean;
  message: string;
  alert?: Alert;
  alerts?: Alert[];
}

export interface CheckAlertsResponse {
  success: boolean;
  symbol: string;
  current_price: number;
  triggered_alerts: Array<{
    alert_id: string;
    alert: Alert;
    message: string;
    distance: number;
    distance_percent: number;
  }>;
  triggered_count: number;
}

class AlertApi {
  private readonly baseUrl = '/api/alerts';

  /**
   * Create a new alert
   */
  async createAlert(alert: Alert): Promise<AlertResponse> {
    const response = await httpClient.post<AlertResponse>(`${this.baseUrl}/create`, alert);
    return response.data!;
  }

  /**
   * Get all alerts, optionally filtered by symbol
   */
  async listAlerts(symbol?: string, enabledOnly: boolean = false): Promise<AlertResponse> {
    const params: any = {};
    if (symbol) params.symbol = symbol;
    if (enabledOnly) params.enabled_only = enabledOnly;

    const response = await httpClient.get<AlertResponse>(`${this.baseUrl}/list`, params);
    return response.data!;
  }

  /**
   * Update alert settings
   */
  async updateAlert(
    alertId: string,
    enabled?: boolean,
    thresholdPercent?: number
  ): Promise<AlertResponse> {
    const response = await httpClient.put<AlertResponse>(`${this.baseUrl}/update/${alertId}`, {
      enabled,
      threshold_percent: thresholdPercent,
    });
    return response.data!;
  }

  /**
   * Delete an alert
   */
  async deleteAlert(alertId: string): Promise<AlertResponse> {
    const response = await httpClient.delete<AlertResponse>(`${this.baseUrl}/delete/${alertId}`);
    return response.data!;
  }

  /**
   * Check if any alerts should trigger for current price
   */
  async checkAlerts(symbol: string, currentPrice: number): Promise<CheckAlertsResponse> {
    const response = await httpClient.post<CheckAlertsResponse>(`${this.baseUrl}/check`, {
      symbol,
      current_price: currentPrice,
    });
    return response.data!;
  }

  /**
   * Get alert trigger history
   */
  async getAlertHistory(limit: number = 50): Promise<any> {
    const response = await httpClient.get<any>(`${this.baseUrl}/history`, { limit });
    return response.data!;
  }

  /**
   * Clear all alerts
   */
  async clearAllAlerts(): Promise<AlertResponse> {
    const response = await httpClient.delete<AlertResponse>(`${this.baseUrl}/clear-all`);
    return response.data!;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<any> {
    const response = await httpClient.get<any>(`${this.baseUrl}/health`);
    return response.data!;
  }
}

export const alertApi = new AlertApi();

