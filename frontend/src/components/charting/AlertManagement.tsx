import React, { useState, useEffect, useCallback } from 'react';
import { 
  BellIcon, 
  PlusIcon, 
  XMarkIcon, 
  Cog6ToothIcon,
  PlayIcon,
  PauseIcon,
  TrashIcon,
  CheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

// Alert Types
export interface AlertCondition {
  id: string;
  type: 'price' | 'indicator' | 'volume' | 'time';
  operator: 'above' | 'below' | 'crosses_above' | 'crosses_below' | 'equals';
  value: number;
  symbol?: string;
  indicator?: string;
  timeframe?: string;
}

export interface Alert {
  id: string;
  name: string;
  symbol: string;
  conditions: AlertCondition[];
  isActive: boolean;
  isTriggered: boolean;
  triggerCount: number;
  lastTriggered?: Date;
  createdAt: Date;
  updatedAt: Date;
  notifications: {
    email: boolean;
    sms: boolean;
    webhook: boolean;
    webhookUrl?: string;
  };
  cooldownMinutes: number;
}

export interface AlertTrigger {
  id: string;
  alertId: string;
  symbol: string;
  triggeredAt: Date;
  condition: AlertCondition;
  currentValue: number;
  message: string;
}

// Alert Manager
export class AlertManager {
  private alerts: Map<string, Alert> = new Map();
  private triggers: AlertTrigger[] = [];
  private listeners: Array<(alerts: Alert[]) => void> = [];
  private triggerListeners: Array<(trigger: AlertTrigger) => void> = [];
  private isMonitoring: boolean = false;
  private monitoringInterval: NodeJS.Timeout | null = null;

  constructor() {
    // Initialize with sample alerts
    this.createSampleAlerts();
  }

  private createSampleAlerts() {
    const sampleAlerts: Alert[] = [
      {
        id: 'alert-1',
        name: 'RELIANCE Price Alert',
        symbol: 'RELIANCE',
        conditions: [{
          id: 'cond-1',
          type: 'price',
          operator: 'above',
          value: 2500,
          symbol: 'RELIANCE'
        }],
        isActive: true,
        isTriggered: false,
        triggerCount: 0,
        createdAt: new Date(),
        updatedAt: new Date(),
        notifications: {
          email: true,
          sms: false,
          webhook: false
        },
        cooldownMinutes: 30
      },
      {
        id: 'alert-2',
        name: 'TCS RSI Oversold',
        symbol: 'TCS',
        conditions: [{
          id: 'cond-2',
          type: 'indicator',
          operator: 'below',
          value: 30,
          symbol: 'TCS',
          indicator: 'RSI',
          timeframe: '1D'
        }],
        isActive: true,
        isTriggered: false,
        triggerCount: 0,
        createdAt: new Date(),
        updatedAt: new Date(),
        notifications: {
          email: true,
          sms: true,
          webhook: false
        },
        cooldownMinutes: 60
      }
    ];

    sampleAlerts.forEach(alert => {
      this.alerts.set(alert.id, alert);
    });
  }

  getAlerts(): Alert[] {
    return Array.from(this.alerts.values());
  }

  getAlert(id: string): Alert | undefined {
    return this.alerts.get(id);
  }

  createAlert(alert: Omit<Alert, 'id' | 'createdAt' | 'updatedAt' | 'isTriggered' | 'triggerCount'>): Alert {
    const newAlert: Alert = {
      ...alert,
      id: `alert-${Date.now()}`,
      createdAt: new Date(),
      updatedAt: new Date(),
      isTriggered: false,
      triggerCount: 0
    };
    
    this.alerts.set(newAlert.id, newAlert);
    this.notifyListeners();
    return newAlert;
  }

  updateAlert(id: string, updates: Partial<Alert>): void {
    const alert = this.alerts.get(id);
    if (alert) {
      this.alerts.set(id, { ...alert, ...updates, updatedAt: new Date() });
      this.notifyListeners();
    }
  }

  deleteAlert(id: string): void {
    this.alerts.delete(id);
    this.notifyListeners();
  }

  toggleAlert(id: string): void {
    const alert = this.alerts.get(id);
    if (alert) {
      this.alerts.set(id, { ...alert, isActive: !alert.isActive, updatedAt: new Date() });
      this.notifyListeners();
    }
  }

  getTriggers(): AlertTrigger[] {
    return [...this.triggers].reverse(); // Most recent first
  }

  clearTriggers(): void {
    this.triggers = [];
  }

  startMonitoring(): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.monitoringInterval = setInterval(() => {
      this.checkAlerts();
    }, 5000); // Check every 5 seconds
  }

  stopMonitoring(): void {
    this.isMonitoring = false;
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  private async checkAlerts(): Promise<void> {
    const activeAlerts = this.getAlerts().filter(alert => alert.isActive);
    
    for (const alert of activeAlerts) {
      try {
        const shouldTrigger = await this.evaluateAlertConditions(alert);
        
        if (shouldTrigger && this.canTriggerAlert(alert)) {
          this.triggerAlert(alert);
        }
      } catch (error) {
        console.error(`Error checking alert ${alert.id}:`, error);
      }
    }
  }

  private async evaluateAlertConditions(alert: Alert): Promise<boolean> {
    // Mock evaluation - in real implementation, this would check actual market data
    for (const condition of alert.conditions) {
      const currentValue = await this.getCurrentValue(condition);
      
      switch (condition.operator) {
        case 'above':
          if (currentValue <= condition.value) return false;
          break;
        case 'below':
          if (currentValue >= condition.value) return false;
          break;
        case 'crosses_above':
          // Would need previous value to detect crossing
          break;
        case 'crosses_below':
          // Would need previous value to detect crossing
          break;
        case 'equals':
          if (currentValue !== condition.value) return false;
          break;
      }
    }
    
    return true;
  }

  private async getCurrentValue(condition: AlertCondition): Promise<number> {
    // Mock data - replace with actual API calls
    const mockPrices: Record<string, number> = {
      'RELIANCE': 2450.50,
      'TCS': 3850.75,
      'HDFCBANK': 1650.20,
      'INFY': 1850.40
    };

    const mockIndicators: Record<string, Record<string, number>> = {
      'RELIANCE': { 'RSI': 65.5, 'MACD': 12.3 },
      'TCS': { 'RSI': 28.2, 'MACD': -5.7 },
      'HDFCBANK': { 'RSI': 45.8, 'MACD': 8.9 },
      'INFY': { 'RSI': 52.1, 'MACD': 3.2 }
    };

    if (condition.type === 'price') {
      return mockPrices[condition.symbol || ''] || 0;
    } else if (condition.type === 'indicator') {
      return mockIndicators[condition.symbol || '']?.[condition.indicator || ''] || 0;
    }

    return 0;
  }

  private canTriggerAlert(alert: Alert): boolean {
    if (!alert.lastTriggered) return true;
    
    const cooldownMs = alert.cooldownMinutes * 60 * 1000;
    const timeSinceLastTrigger = Date.now() - alert.lastTriggered.getTime();
    
    return timeSinceLastTrigger >= cooldownMs;
  }

  private triggerAlert(alert: Alert): void {
    const trigger: AlertTrigger = {
      id: `trigger-${Date.now()}`,
      alertId: alert.id,
      symbol: alert.symbol,
      triggeredAt: new Date(),
      condition: alert.conditions[0], // Simplified - would handle multiple conditions
      currentValue: 0, // Would be actual current value
      message: `${alert.name} triggered: ${alert.conditions[0].operator} ${alert.conditions[0].value}`
    };

    this.triggers.push(trigger);
    
    // Update alert
    this.alerts.set(alert.id, {
      ...alert,
      isTriggered: true,
      triggerCount: alert.triggerCount + 1,
      lastTriggered: new Date(),
      updatedAt: new Date()
    });

    // Send notifications
    this.sendNotifications(alert, trigger);
    
    // Notify listeners
    this.triggerListeners.forEach(listener => listener(trigger));
    this.notifyListeners();
  }

  private sendNotifications(alert: Alert, trigger: AlertTrigger): void {
    if (alert.notifications.email) {
      console.log('Sending email notification:', trigger.message);
    }
    
    if (alert.notifications.sms) {
      console.log('Sending SMS notification:', trigger.message);
    }
    
    if (alert.notifications.webhook && alert.notifications.webhookUrl) {
      console.log('Sending webhook notification:', trigger.message);
    }
  }

  subscribe(listener: (alerts: Alert[]) => void) {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  subscribeToTriggers(listener: (trigger: AlertTrigger) => void) {
    this.triggerListeners.push(listener);
    return () => {
      const index = this.triggerListeners.indexOf(listener);
      if (index > -1) {
        this.triggerListeners.splice(index, 1);
      }
    };
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.getAlerts()));
  }
}

// Alert Creation Form Component
interface AlertFormProps {
  alertManager: AlertManager;
  onClose: () => void;
  editAlert?: Alert;
}

const AlertForm: React.FC<AlertFormProps> = ({
  alertManager,
  onClose,
  editAlert
}) => {
  const [formData, setFormData] = useState({
    name: editAlert?.name || '',
    symbol: editAlert?.symbol || '',
    conditionType: 'price' as AlertCondition['type'],
    operator: 'above' as AlertCondition['operator'],
    value: editAlert?.conditions[0]?.value || 0,
    indicator: '',
    timeframe: '1D',
    cooldownMinutes: editAlert?.cooldownMinutes || 30,
    notifications: {
      email: editAlert?.notifications.email || false,
      sms: editAlert?.notifications.sms || false,
      webhook: editAlert?.notifications.webhook || false,
      webhookUrl: editAlert?.notifications.webhookUrl || ''
    }
  });

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    const condition: AlertCondition = {
      id: `cond-${Date.now()}`,
      type: formData.conditionType,
      operator: formData.operator,
      value: formData.value,
      symbol: formData.symbol,
      indicator: formData.conditionType === 'indicator' ? formData.indicator : undefined,
      timeframe: formData.conditionType === 'indicator' ? formData.timeframe : undefined
    };

    if (editAlert) {
      alertManager.updateAlert(editAlert.id, {
        name: formData.name,
        symbol: formData.symbol,
        conditions: [condition],
        cooldownMinutes: formData.cooldownMinutes,
        notifications: formData.notifications
      });
    } else {
      alertManager.createAlert({
        name: formData.name,
        symbol: formData.symbol,
        conditions: [condition],
        isActive: true,
        cooldownMinutes: formData.cooldownMinutes,
        notifications: formData.notifications
      });
    }
    
    onClose();
  }, [formData, alertManager, editAlert, onClose]);

  return (
    <div className="alert-form p-6 bg-gray-800 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">
          {editAlert ? 'Edit Alert' : 'Create New Alert'}
        </h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-white"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Alert Name */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Alert Name
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            required
          />
        </div>

        {/* Symbol */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Symbol
          </label>
          <input
            type="text"
            value={formData.symbol}
            onChange={(e) => setFormData(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            placeholder="e.g., RELIANCE, TCS"
            required
          />
        </div>

        {/* Condition Type */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Condition Type
          </label>
          <select
            value={formData.conditionType}
            onChange={(e) => setFormData(prev => ({ ...prev, conditionType: e.target.value as AlertCondition['type'] }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="price">Price</option>
            <option value="indicator">Technical Indicator</option>
            <option value="volume">Volume</option>
            <option value="time">Time-based</option>
          </select>
        </div>

        {/* Indicator Selection (if indicator type) */}
        {formData.conditionType === 'indicator' && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Indicator
            </label>
            <select
              value={formData.indicator}
              onChange={(e) => setFormData(prev => ({ ...prev, indicator: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="">Select Indicator</option>
              <option value="RSI">RSI</option>
              <option value="MACD">MACD</option>
              <option value="SMA">Simple Moving Average</option>
              <option value="EMA">Exponential Moving Average</option>
              <option value="BB">Bollinger Bands</option>
            </select>
          </div>
        )}

        {/* Operator */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Condition
          </label>
          <select
            value={formData.operator}
            onChange={(e) => setFormData(prev => ({ ...prev, operator: e.target.value as AlertCondition['operator'] }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="above">Above</option>
            <option value="below">Below</option>
            <option value="crosses_above">Crosses Above</option>
            <option value="crosses_below">Crosses Below</option>
            <option value="equals">Equals</option>
          </select>
        </div>

        {/* Value */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Value
          </label>
          <input
            type="number"
            step="0.01"
            value={formData.value}
            onChange={(e) => setFormData(prev => ({ ...prev, value: Number(e.target.value) }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            required
          />
        </div>

        {/* Cooldown */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Cooldown (minutes)
          </label>
          <input
            type="number"
            min="1"
            value={formData.cooldownMinutes}
            onChange={(e) => setFormData(prev => ({ ...prev, cooldownMinutes: Number(e.target.value) }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          />
        </div>

        {/* Notifications */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Notifications
          </label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.notifications.email}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  notifications: { ...prev.notifications, email: e.target.checked }
                }))}
                className="mr-2"
              />
              <span className="text-gray-300">Email</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.notifications.sms}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  notifications: { ...prev.notifications, sms: e.target.checked }
                }))}
                className="mr-2"
              />
              <span className="text-gray-300">SMS</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.notifications.webhook}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  notifications: { ...prev.notifications, webhook: e.target.checked }
                }))}
                className="mr-2"
              />
              <span className="text-gray-300">Webhook</span>
            </label>
            {formData.notifications.webhook && (
              <input
                type="url"
                value={formData.notifications.webhookUrl}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  notifications: { ...prev.notifications, webhookUrl: e.target.value }
                }))}
                placeholder="Webhook URL"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
              />
            )}
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex space-x-3 pt-4">
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
          >
            {editAlert ? 'Update Alert' : 'Create Alert'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

// Alert Management Component
interface AlertManagementProps {
  alertManager: AlertManager;
  className?: string;
}

const AlertManagement: React.FC<AlertManagementProps> = ({
  alertManager,
  className = ''
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [triggers, setTriggers] = useState<AlertTrigger[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editAlert, setEditAlert] = useState<Alert | undefined>();
  const [isMonitoring, setIsMonitoring] = useState(false);

  useEffect(() => {
    const unsubscribeAlerts = alertManager.subscribe(setAlerts);
    const unsubscribeTriggers = alertManager.subscribeToTriggers((trigger) => {
      setTriggers(prev => [trigger, ...prev]);
    });
    
    setAlerts(alertManager.getAlerts());
    setTriggers(alertManager.getTriggers());
    
    return () => {
      unsubscribeAlerts();
      unsubscribeTriggers();
    };
  }, [alertManager]);

  const handleToggleMonitoring = useCallback(() => {
    if (isMonitoring) {
      alertManager.stopMonitoring();
      setIsMonitoring(false);
    } else {
      alertManager.startMonitoring();
      setIsMonitoring(true);
    }
  }, [alertManager, isMonitoring]);

  const handleEditAlert = useCallback((alert: Alert) => {
    setEditAlert(alert);
    setShowForm(true);
  }, []);

  const handleDeleteAlert = useCallback((id: string) => {
    if (window.confirm('Are you sure you want to delete this alert?')) {
      alertManager.deleteAlert(id);
    }
  }, [alertManager]);

  const handleToggleAlert = useCallback((id: string) => {
    alertManager.toggleAlert(id);
  }, [alertManager]);

  const handleClearTriggers = useCallback(() => {
    alertManager.clearTriggers();
    setTriggers([]);
  }, [alertManager]);

  return (
    <div className={`alert-management ${className}`}>
      {/* Header */}
      <div className="alert-header p-4 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <BellIcon className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-semibold text-white">Alert Management</h2>
            <span className="text-sm text-gray-400">
              ({alerts.length} alerts, {triggers.length} triggers)
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleToggleMonitoring}
              className={`flex items-center space-x-1 px-3 py-1 rounded text-sm ${
                isMonitoring
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isMonitoring ? (
                <>
                  <PauseIcon className="w-4 h-4" />
                  <span>Stop</span>
                </>
              ) : (
                <>
                  <PlayIcon className="w-4 h-4" />
                  <span>Start</span>
                </>
              )}
            </button>
            
            <button
              onClick={() => {
                setEditAlert(undefined);
                setShowForm(true);
              }}
              className="flex items-center space-x-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
            >
              <PlusIcon className="w-4 h-4" />
              <span>New Alert</span>
            </button>
          </div>
        </div>
      </div>

      {/* Alert Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="max-w-md w-full mx-4">
            <AlertForm
              alertManager={alertManager}
              onClose={() => {
                setShowForm(false);
                setEditAlert(undefined);
              }}
              editAlert={editAlert}
            />
          </div>
        </div>
      )}

      <div className="flex">
        {/* Alerts List */}
        <div className="flex-1 p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Active Alerts</h3>
          
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <BellIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No alerts created yet</p>
              <p className="text-sm">Create your first alert to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`alert-item p-4 rounded-lg border ${
                    alert.isActive
                      ? 'bg-gray-800 border-gray-600'
                      : 'bg-gray-900 border-gray-700 opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-semibold text-white">{alert.name}</h4>
                      <span className="text-sm text-gray-400">{alert.symbol}</span>
                      {alert.isTriggered && (
                        <ExclamationTriangleIcon className="w-4 h-4 text-yellow-400" />
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => handleToggleAlert(alert.id)}
                        className={`p-1 rounded ${
                          alert.isActive
                            ? 'text-green-400 hover:bg-green-400 hover:text-white'
                            : 'text-gray-400 hover:bg-gray-600 hover:text-white'
                        }`}
                        title={alert.isActive ? 'Deactivate' : 'Activate'}
                      >
                        {alert.isActive ? <CheckIcon className="w-4 h-4" /> : <XMarkIcon className="w-4 h-4" />}
                      </button>
                      
                      <button
                        onClick={() => handleEditAlert(alert)}
                        className="p-1 text-gray-400 hover:bg-gray-600 hover:text-white rounded"
                        title="Edit"
                      >
                        <Cog6ToothIcon className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => handleDeleteAlert(alert.id)}
                        className="p-1 text-red-400 hover:bg-red-400 hover:text-white rounded"
                        title="Delete"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-300">
                    {alert.conditions.map((condition, index) => (
                      <div key={condition.id}>
                        {condition.type} {condition.operator} {condition.value}
                        {condition.indicator && ` (${condition.indicator})`}
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                    <span>Triggers: {alert.triggerCount}</span>
                    <span>Cooldown: {alert.cooldownMinutes}m</span>
                    {alert.lastTriggered && (
                      <span>Last: {alert.lastTriggered.toLocaleTimeString()}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Triggers List */}
        <div className="w-80 p-4 bg-gray-900 border-l border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Recent Triggers</h3>
            {triggers.length > 0 && (
              <button
                onClick={handleClearTriggers}
                className="text-sm text-gray-400 hover:text-white"
              >
                Clear All
              </button>
            )}
          </div>
          
          {triggers.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <BellIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No triggers yet</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {triggers.map((trigger) => (
                <div
                  key={trigger.id}
                  className="trigger-item p-3 bg-gray-800 rounded border border-gray-600"
                >
                  <div className="text-sm text-white font-medium">{trigger.symbol}</div>
                  <div className="text-xs text-gray-300 mt-1">{trigger.message}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {trigger.triggeredAt.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlertManagement;
