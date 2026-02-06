/**
 * Auto-Alert Service
 * Automatically generates alerts based on analysis events
 */

export interface AutoAlertRule {
  id: string;
  name: string;
  enabled: boolean;
  eventType: 'zone_break' | 'structure_change' | 'pattern_detected' | 'signal_change' | 'level_touch';
  conditions: {
    minConfidence?: number;
    patternTypes?: string[];
    signalTypes?: ('BUY' | 'SELL')[];
  };
  alertConfig: {
    notify_browser: boolean;
    notify_sound: boolean;
    notify_email: boolean;
  };
}

export interface AnalysisEvent {
  type: 'zone_break' | 'structure_change' | 'pattern_detected' | 'signal_change' | 'level_touch';
  symbol: string;
  timestamp: Date;
  data: any;
  confidence?: number;
}

class AutoAlertService {
  private rules: AutoAlertRule[] = [];
  private eventListeners: ((event: AnalysisEvent) => void)[] = [];

  constructor() {
    this.loadRules();
  }

  /**
   * Load auto-alert rules from localStorage
   */
  private loadRules(): void {
    try {
      const saved = localStorage.getItem('auto_alert_rules');
      if (saved) {
        this.rules = JSON.parse(saved);
      } else {
        // Default rules
        this.rules = [
          {
            id: 'zone_break_default',
            name: 'Zone Break Alerts',
            enabled: true,
            eventType: 'zone_break',
            conditions: { minConfidence: 0.7 },
            alertConfig: {
              notify_browser: true,
              notify_sound: true,
              notify_email: false
            }
          },
          {
            id: 'structure_change_default',
            name: 'Structure Change Alerts',
            enabled: true,
            eventType: 'structure_change',
            conditions: {},
            alertConfig: {
              notify_browser: true,
              notify_sound: true,
              notify_email: false
            }
          },
          {
            id: 'strong_pattern_default',
            name: 'Strong Pattern Alerts',
            enabled: true,
            eventType: 'pattern_detected',
            conditions: { minConfidence: 0.8 },
            alertConfig: {
              notify_browser: true,
              notify_sound: true,
              notify_email: false
            }
          }
        ];
        this.saveRules();
      }
    } catch (error) {
      console.error('Error loading auto-alert rules:', error);
      this.rules = [];
    }
  }

  /**
   * Save auto-alert rules to localStorage
   */
  private saveRules(): void {
    try {
      localStorage.setItem('auto_alert_rules', JSON.stringify(this.rules));
    } catch (error) {
      console.error('Error saving auto-alert rules:', error);
    }
  }

  /**
   * Get all rules
   */
  getRules(): AutoAlertRule[] {
    return [...this.rules];
  }

  /**
   * Add or update a rule
   */
  setRule(rule: AutoAlertRule): void {
    const index = this.rules.findIndex(r => r.id === rule.id);
    if (index >= 0) {
      this.rules[index] = rule;
    } else {
      this.rules.push(rule);
    }
    this.saveRules();
  }

  /**
   * Remove a rule
   */
  removeRule(ruleId: string): void {
    this.rules = this.rules.filter(r => r.id !== ruleId);
    this.saveRules();
  }

  /**
   * Check if an event matches any enabled rules
   */
  shouldCreateAlert(event: AnalysisEvent): { shouldCreate: boolean; rule?: AutoAlertRule } {
    for (const rule of this.rules) {
      if (!rule.enabled || rule.eventType !== event.type) {
        continue;
      }

      // Check conditions
      if (rule.conditions.minConfidence && (event.confidence || 0) < rule.conditions.minConfidence) {
        continue;
      }

      if (rule.conditions.patternTypes && event.data?.patternType) {
        if (!rule.conditions.patternTypes.includes(event.data.patternType)) {
          continue;
        }
      }

      if (rule.conditions.signalTypes && event.data?.signalType) {
        if (!rule.conditions.signalTypes.includes(event.data.signalType)) {
          continue;
        }
      }

      return { shouldCreate: true, rule };
    }

    return { shouldCreate: false };
  }

  /**
   * Process an analysis event and generate alert if needed
   */
  processEvent(event: AnalysisEvent): { shouldCreate: boolean; rule?: AutoAlertRule; alertData?: any } {
    const { shouldCreate, rule } = this.shouldCreateAlert(event);
    
    if (!shouldCreate || !rule) {
      return { shouldCreate: false };
    }

    // Generate alert data based on event type
    const alertData = this.generateAlertData(event, rule);
    
    return { shouldCreate: true, rule, alertData };
  }

  /**
   * Generate alert data from event
   */
  private generateAlertData(event: AnalysisEvent, rule: AutoAlertRule): any {
    const baseAlert = {
      symbol: event.symbol,
      enabled: true,
      ...rule.alertConfig
    };

    switch (event.type) {
      case 'zone_break':
        return {
          ...baseAlert,
          alert_type: 'zone_break',
          condition: 'breaks',
          target_price: event.data.price || event.data.breakPrice,
          threshold_percent: 0.5
        };

      case 'structure_change':
        return {
          ...baseAlert,
          alert_type: 'structure_change',
          condition: 'changes',
          target_price: event.data.price || event.data.currentPrice,
          threshold_percent: 1.0
        };

      case 'pattern_detected':
        return {
          ...baseAlert,
          alert_type: 'pattern_detected',
          condition: 'detected',
          target_price: event.data.price || event.data.currentPrice,
          threshold_percent: 0.0
        };

      case 'signal_change':
        return {
          ...baseAlert,
          alert_type: 'signal_change',
          condition: event.data.signalType === 'BUY' ? 'crosses_above' : 'crosses_below',
          target_price: event.data.price || event.data.currentPrice,
          threshold_percent: 1.0
        };

      case 'level_touch':
        return {
          ...baseAlert,
          alert_type: 'price_level',
          condition: 'touches',
          target_price: event.data.price || event.data.level,
          threshold_percent: 0.5
        };

      default:
        return baseAlert;
    }
  }

  /**
   * Subscribe to analysis events
   */
  subscribe(listener: (event: AnalysisEvent) => void): () => void {
    this.eventListeners.push(listener);
    return () => {
      this.eventListeners = this.eventListeners.filter(l => l !== listener);
    };
  }

  /**
   * Emit an analysis event
   */
  emit(event: AnalysisEvent): void {
    this.eventListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in event listener:', error);
      }
    });
  }
}

// Export singleton instance
export const autoAlertService = new AutoAlertService();

