import React, { useState, useEffect, useCallback } from 'react';
import {
  BellIcon, CogIcon, CheckCircleIcon, ExclamationTriangleIcon,
  InformationCircleIcon, XMarkIcon, EyeIcon, EyeSlashIcon,
  PlusIcon, PencilIcon, TrashIcon, ClockIcon, UserIcon,
  EnvelopeIcon, ChatBubbleLeftRightIcon, DevicePhoneMobileIcon,
  GlobeAltIcon, ShieldCheckIcon, FireIcon, ChartBarIcon, DocumentIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../LoadingSpinner';
import ErrorDisplay from '../ErrorDisplay';

// Types for Advanced Notifications
interface NotificationRule {
  id: string;
  name: string;
  description: string;
  category: 'price' | 'technical' | 'news' | 'portfolio' | 'system' | 'custom';
  conditions: Array<{
    field: string;
    operator: 'equals' | 'greater_than' | 'less_than' | 'contains' | 'between';
    value: any;
    value2?: any; // for between operator
  }>;
  channels: Array<'email' | 'sms' | 'push' | 'webhook' | 'in_app'>;
  frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_triggered?: string;
  trigger_count: number;
}

interface NotificationTemplate {
  id: string;
  name: string;
  category: string;
  subject_template: string;
  body_template: string;
  variables: Array<{
    name: string;
    type: 'string' | 'number' | 'date' | 'boolean';
    description: string;
    required: boolean;
  }>;
  channels: Array<'email' | 'sms' | 'push' | 'webhook' | 'in_app'>;
  created_at: string;
}

interface NotificationPreferences {
  user_id: string;
  global_enabled: boolean;
  channels: {
    email: {
      enabled: boolean;
      address: string;
      frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
      categories: string[];
    };
    sms: {
      enabled: boolean;
      phone: string;
      frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
      categories: string[];
    };
    push: {
      enabled: boolean;
      device_tokens: string[];
      frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
      categories: string[];
    };
    webhook: {
      enabled: boolean;
      url: string;
      secret: string;
      frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
      categories: string[];
    };
    in_app: {
      enabled: boolean;
      frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
      categories: string[];
    };
  };
  quiet_hours: {
    enabled: boolean;
    start_time: string; // HH:MM format
    end_time: string; // HH:MM format
    timezone: string;
  };
  categories: Record<string, {
    enabled: boolean;
    channels: string[];
    frequency: string;
  }>;
}

interface NotificationHistory {
  id: string;
  user_id: string;
  rule_id: string;
  category: string;
  title: string;
  message: string;
  channels: string[];
  status: 'sent' | 'failed' | 'pending' | 'delivered' | 'read';
  sent_at: string;
  delivered_at?: string;
  read_at?: string;
  error_message?: string;
  metadata: Record<string, any>;
}

interface NotificationAnalytics {
  total_sent: number;
  total_delivered: number;
  total_read: number;
  delivery_rate: number;
  read_rate: number;
  by_category: Record<string, {
    sent: number;
    delivered: number;
    read: number;
    delivery_rate: number;
    read_rate: number;
  }>;
  by_channel: Record<string, {
    sent: number;
    delivered: number;
    read: number;
    delivery_rate: number;
    read_rate: number;
  }>;
  by_time_period: Array<{
    period: string;
    sent: number;
    delivered: number;
    read: number;
  }>;
}

// Advanced Notifications API Service
class AdvancedNotificationsApiService {
  private baseUrl = '/api/notifications';

  async getNotificationRules(): Promise<NotificationRule[]> {
    const response = await fetch(`${this.baseUrl}/rules`);
    if (!response.ok) throw new Error('Failed to fetch notification rules');
    return response.json();
  }

  async createNotificationRule(rule: Partial<NotificationRule>): Promise<NotificationRule> {
    const response = await fetch(`${this.baseUrl}/rules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rule)
    });
    if (!response.ok) throw new Error('Failed to create notification rule');
    return response.json();
  }

  async updateNotificationRule(ruleId: string, updates: Partial<NotificationRule>): Promise<NotificationRule> {
    const response = await fetch(`${this.baseUrl}/rules/${ruleId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error('Failed to update notification rule');
    return response.json();
  }

  async deleteNotificationRule(ruleId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/rules/${ruleId}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete notification rule');
  }

  async getNotificationTemplates(): Promise<NotificationTemplate[]> {
    const response = await fetch(`${this.baseUrl}/templates`);
    if (!response.ok) throw new Error('Failed to fetch notification templates');
    return response.json();
  }

  async createNotificationTemplate(template: Partial<NotificationTemplate>): Promise<NotificationTemplate> {
    const response = await fetch(`${this.baseUrl}/templates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(template)
    });
    if (!response.ok) throw new Error('Failed to create notification template');
    return response.json();
  }

  async getNotificationPreferences(): Promise<NotificationPreferences> {
    const response = await fetch(`${this.baseUrl}/preferences`);
    if (!response.ok) throw new Error('Failed to fetch notification preferences');
    return response.json();
  }

  async updateNotificationPreferences(preferences: Partial<NotificationPreferences>): Promise<NotificationPreferences> {
    const response = await fetch(`${this.baseUrl}/preferences`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preferences)
    });
    if (!response.ok) throw new Error('Failed to update notification preferences');
    return response.json();
  }

  async getNotificationHistory(limit?: number, offset?: number): Promise<NotificationHistory[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const response = await fetch(`${this.baseUrl}/history?${params}`);
    if (!response.ok) throw new Error('Failed to fetch notification history');
    return response.json();
  }

  async getNotificationAnalytics(timeRange?: string): Promise<NotificationAnalytics> {
    const params = new URLSearchParams();
    if (timeRange) params.append('time_range', timeRange);
    
    const response = await fetch(`${this.baseUrl}/analytics?${params}`);
    if (!response.ok) throw new Error('Failed to fetch notification analytics');
    return response.json();
  }

  async testNotification(ruleId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/rules/${ruleId}/test`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to test notification');
  }

  async sendCustomNotification(notification: {
    title: string;
    message: string;
    category: string;
    channels: string[];
    recipients?: string[];
  }): Promise<void> {
    const response = await fetch(`${this.baseUrl}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(notification)
    });
    if (!response.ok) throw new Error('Failed to send custom notification');
  }
}

const notificationsApi = new AdvancedNotificationsApiService();

// Notification Rule Builder Component
const NotificationRuleBuilder: React.FC<{
  rule?: NotificationRule;
  onSave: (rule: NotificationRule) => void;
  onCancel: () => void;
}> = ({ rule, onSave, onCancel }) => {
  const [formData, setFormData] = useState<Partial<NotificationRule>>({
    name: '',
    description: '',
    category: 'price',
    conditions: [],
    channels: ['email'],
    frequency: 'immediate',
    enabled: true,
    ...rule
  });

  const [newCondition, setNewCondition] = useState<{
    field: string;
    operator: 'equals' | 'greater_than' | 'less_than' | 'contains' | 'between';
    value: any;
    value2?: any;
  }>({
    field: '',
    operator: 'equals',
    value: '',
    value2: ''
  });

  const fieldOptions = {
    price: ['symbol', 'price', 'change', 'change_percent', 'volume'],
    technical: ['rsi', 'macd', 'sma_20', 'sma_50', 'bollinger_upper', 'bollinger_lower'],
    news: ['sentiment', 'news_count', 'headline_keywords'],
    portfolio: ['portfolio_value', 'daily_pnl', 'position_size', 'unrealized_pnl'],
    system: ['cpu_usage', 'memory_usage', 'disk_usage', 'api_response_time'],
    custom: ['custom_field_1', 'custom_field_2', 'custom_field_3']
  };

  const handleAddCondition = () => {
    if (newCondition.field && newCondition.value) {
      setFormData(prev => ({
        ...prev,
        conditions: [...(prev.conditions || []), { ...newCondition }]
      }));
      setNewCondition({ field: '', operator: 'equals', value: '', value2: '' });
    }
  };

  const handleRemoveCondition = (index: number) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions?.filter((_, i) => i !== index) || []
    }));
  };

  const handleSave = async () => {
    try {
      const savedRule = rule?.id
        ? await notificationsApi.updateNotificationRule(rule.id, formData)
        : await notificationsApi.createNotificationRule(formData);
      onSave(savedRule);
      toast.success('Notification rule saved successfully');
    } catch (error) {
      toast.error('Failed to save notification rule');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {rule ? 'Edit Notification Rule' : 'Create Notification Rule'}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Rule Name
                  </label>
                  <input
                    type="text"
                    value={formData.name || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                    placeholder="e.g., Price Alert for AAPL"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.category || 'price'}
                    onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as any }))}
                    className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  >
                    <option value="price">Price</option>
                    <option value="technical">Technical</option>
                    <option value="news">News</option>
                    <option value="portfolio">Portfolio</option>
                    <option value="system">System</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  placeholder="Describe what this notification rule does..."
                />
              </div>
            </div>

            {/* Conditions */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Conditions</h3>
              
              {/* Existing Conditions */}
              {formData.conditions?.map((condition, index) => (
                <div key={index} className="flex items-center space-x-2 mb-2 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="text-sm font-medium">{condition.field}</span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">{condition.operator}</span>
                  <span className="text-sm">{condition.value}</span>
                  {condition.operator === 'between' && condition.value2 && (
                    <>
                      <span className="text-sm text-gray-600 dark:text-gray-400">and</span>
                      <span className="text-sm">{condition.value2}</span>
                    </>
                  )}
                  <button
                    onClick={() => handleRemoveCondition(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}

              {/* Add New Condition */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                <select
                  value={newCondition.field}
                  onChange={(e) => setNewCondition(prev => ({ ...prev, field: e.target.value }))}
                  className="p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                >
                  <option value="">Select Field</option>
                  {fieldOptions[formData.category as keyof typeof fieldOptions]?.map(field => (
                    <option key={field} value={field}>{field}</option>
                  ))}
                </select>
                <select
                  value={newCondition.operator}
                  onChange={(e) => setNewCondition(prev => ({ ...prev, operator: e.target.value as any }))}
                  className="p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                >
                  <option value="equals">Equals</option>
                  <option value="greater_than">Greater Than</option>
                  <option value="less_than">Less Than</option>
                  <option value="contains">Contains</option>
                  <option value="between">Between</option>
                </select>
                <input
                  type="text"
                  value={newCondition.value}
                  onChange={(e) => setNewCondition(prev => ({ ...prev, value: e.target.value }))}
                  placeholder="Value"
                  className="p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
                {newCondition.operator === 'between' && (
                  <input
                    type="text"
                    value={newCondition.value2}
                    onChange={(e) => setNewCondition(prev => ({ ...prev, value2: e.target.value }))}
                    placeholder="Value 2"
                    className="p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  />
                )}
              </div>
              <button
                onClick={handleAddCondition}
                className="mt-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                Add Condition
              </button>
            </div>

            {/* Channels and Frequency */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Delivery Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Notification Channels
                  </label>
                  <div className="space-y-2">
                    {['email', 'sms', 'push', 'webhook', 'in_app'].map(channel => (
                      <label key={channel} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.channels?.includes(channel as any)}
                          onChange={(e) => {
                            const channels = formData.channels || [];
                            if (e.target.checked) {
                              setFormData(prev => ({ ...prev, channels: [...channels, channel as any] }));
                            } else {
                              setFormData(prev => ({ ...prev, channels: channels.filter(c => c !== channel) }));
                            }
                          }}
                          className="mr-2"
                        />
                        <span className="text-sm capitalize">{channel}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Frequency
                  </label>
                  <select
                    value={formData.frequency || 'immediate'}
                    onChange={(e) => setFormData(prev => ({ ...prev, frequency: e.target.value as any }))}
                    className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  >
                    <option value="immediate">Immediate</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-2 p-6 border-t dark:border-gray-700">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Save Rule
          </button>
        </div>
      </div>
    </div>
  );
};

// Notification Preferences Component
const NotificationPreferencesCard: React.FC<{
  preferences: NotificationPreferences;
  onUpdate: (preferences: NotificationPreferences) => void;
}> = ({ preferences, onUpdate }) => {
  const [localPreferences, setLocalPreferences] = useState(preferences);

  useEffect(() => {
    setLocalPreferences(preferences);
  }, [preferences]);

  const handleSave = async () => {
    try {
      const updated = await notificationsApi.updateNotificationPreferences(localPreferences);
      onUpdate(updated);
      toast.success('Preferences updated successfully');
    } catch (error) {
      toast.error('Failed to update preferences');
    }
  };

  const updateChannelPreference = (channel: keyof NotificationPreferences['channels'], updates: Partial<NotificationPreferences['channels'][keyof NotificationPreferences['channels']]>) => {
    setLocalPreferences(prev => ({
      ...prev,
      channels: {
        ...prev.channels,
        [channel]: {
          ...prev.channels[channel],
          ...updates
        }
      }
    }));
  };

  const updateCategoryPreference = (category: string, updates: Partial<NotificationPreferences['categories'][string]>) => {
    setLocalPreferences(prev => ({
      ...prev,
      categories: {
        ...prev.categories,
        [category]: {
          ...prev.categories[category],
          ...updates
        }
      }
    }));
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Notification Preferences</h3>
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          Save Changes
        </button>
      </div>

      <div className="space-y-6">
        {/* Global Settings */}
        <div>
          <h4 className="font-medium mb-3">Global Settings</h4>
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={localPreferences.global_enabled}
                onChange={(e) => setLocalPreferences(prev => ({ ...prev, global_enabled: e.target.checked }))}
                className="mr-2"
              />
              Enable Notifications
            </label>
          </div>
        </div>

        {/* Channel Settings */}
        <div>
          <h4 className="font-medium mb-3">Channel Settings</h4>
          <div className="space-y-4">
            {Object.entries(localPreferences.channels).map(([channel, config]) => (
              <div key={channel} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-medium capitalize">{channel}</h5>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={config.enabled}
                      onChange={(e) => updateChannelPreference(channel as any, { enabled: e.target.checked })}
                      className="mr-2"
                    />
                    Enabled
                  </label>
                </div>
                {config.enabled && (
                  <div className="space-y-2">
                    {channel === 'email' && (
                      <input
                        type="email"
                        value={(config as any).address || ''}
                        onChange={(e) => updateChannelPreference(channel as any, { address: e.target.value })}
                        placeholder="Email address"
                        className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      />
                    )}
                    {channel === 'sms' && (
                      <input
                        type="tel"
                        value={(config as any).phone || ''}
                        onChange={(e) => updateChannelPreference(channel as any, { phone: e.target.value })}
                        placeholder="Phone number"
                        className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      />
                    )}
                    {channel === 'webhook' && (
                      <input
                        type="url"
                        value={(config as any).url || ''}
                        onChange={(e) => updateChannelPreference(channel as any, { url: e.target.value })}
                        placeholder="Webhook URL"
                        className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      />
                    )}
                    <select
                      value={config.frequency}
                      onChange={(e) => updateChannelPreference(channel as any, { frequency: e.target.value as any })}
                      className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                    >
                      <option value="immediate">Immediate</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Category Settings */}
        <div>
          <h4 className="font-medium mb-3">Category Settings</h4>
          <div className="space-y-2">
            {Object.entries(localPreferences.categories).map(([category, config]) => (
              <div key={category} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={config.enabled}
                      onChange={(e) => updateCategoryPreference(category, { enabled: e.target.checked })}
                      className="mr-2"
                    />
                    <span className="capitalize">{category}</span>
                  </label>
                  <select
                    value={config.frequency}
                    onChange={(e) => updateCategoryPreference(category, { frequency: e.target.value })}
                    className="p-1 border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                  >
                    <option value="immediate">Immediate</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quiet Hours */}
        <div>
          <h4 className="font-medium mb-3">Quiet Hours</h4>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={localPreferences.quiet_hours.enabled}
                onChange={(e) => setLocalPreferences(prev => ({
                  ...prev,
                  quiet_hours: { ...prev.quiet_hours, enabled: e.target.checked }
                }))}
                className="mr-2"
              />
              Enable Quiet Hours
            </label>
            {localPreferences.quiet_hours.enabled && (
              <div className="grid grid-cols-3 gap-2">
                <input
                  type="time"
                  value={localPreferences.quiet_hours.start_time}
                  onChange={(e) => setLocalPreferences(prev => ({
                    ...prev,
                    quiet_hours: { ...prev.quiet_hours, start_time: e.target.value }
                  }))}
                  className="p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
                <input
                  type="time"
                  value={localPreferences.quiet_hours.end_time}
                  onChange={(e) => setLocalPreferences(prev => ({
                    ...prev,
                    quiet_hours: { ...prev.quiet_hours, end_time: e.target.value }
                  }))}
                  className="p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
                <input
                  type="text"
                  value={localPreferences.quiet_hours.timezone}
                  onChange={(e) => setLocalPreferences(prev => ({
                    ...prev,
                    quiet_hours: { ...prev.quiet_hours, timezone: e.target.value }
                  }))}
                  placeholder="Timezone"
                  className="p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Advanced Notifications System Component
const AdvancedNotificationsSystem: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'rules' | 'templates' | 'preferences' | 'history' | 'analytics'>('rules');
  const [rules, setRules] = useState<NotificationRule[]>([]);
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [history, setHistory] = useState<NotificationHistory[]>([]);
  const [analytics, setAnalytics] = useState<NotificationAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRuleBuilder, setShowRuleBuilder] = useState(false);
  const [editingRule, setEditingRule] = useState<NotificationRule | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [rulesData, templatesData, preferencesData, historyData, analyticsData] = await Promise.all([
        notificationsApi.getNotificationRules(),
        notificationsApi.getNotificationTemplates(),
        notificationsApi.getNotificationPreferences(),
        notificationsApi.getNotificationHistory(50),
        notificationsApi.getNotificationAnalytics('30d')
      ]);

      setRules(rulesData);
      setTemplates(templatesData);
      setPreferences(preferencesData);
      setHistory(historyData);
      setAnalytics(analyticsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch notifications data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await notificationsApi.deleteNotificationRule(ruleId);
      setRules(prev => prev.filter(rule => rule.id !== ruleId));
      toast.success('Notification rule deleted successfully');
    } catch (error) {
      toast.error('Failed to delete notification rule');
    }
  };

  const handleTestRule = async (ruleId: string) => {
    try {
      await notificationsApi.testNotification(ruleId);
      toast.success('Test notification sent successfully');
    } catch (error) {
      toast.error('Failed to send test notification');
    }
  };

  const handleRuleSave = (rule: NotificationRule) => {
    setRules(prev => {
      const existingIndex = prev.findIndex(r => r.id === rule.id);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = rule;
        return updated;
      } else {
        return [...prev, rule];
      }
    });
    setShowRuleBuilder(false);
    setEditingRule(null);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'rules':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Notification Rules</h3>
              <button
                onClick={() => setShowRuleBuilder(true)}
                className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Create Rule
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {rules.map((rule) => (
                <div key={rule.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{rule.name}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{rule.description}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={cn(
                        "w-2 h-2 rounded-full",
                        rule.enabled ? "bg-green-500" : "bg-gray-400"
                      )} />
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {rule.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Category</span>
                      <span className="font-medium capitalize">{rule.category}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Channels</span>
                      <span className="font-medium">{rule.channels.length}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Triggers</span>
                      <span className="font-medium">{rule.trigger_count}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Last Triggered</span>
                      <span className="font-medium">
                        {rule.last_triggered ? new Date(rule.last_triggered).toLocaleDateString() : 'Never'}
                      </span>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => {
                        setEditingRule(rule);
                        setShowRuleBuilder(true);
                      }}
                      className="flex-1 px-3 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-500"
                    >
                      <PencilIcon className="h-4 w-4 mx-auto" />
                    </button>
                    <button
                      onClick={() => handleTestRule(rule.id)}
                      className="flex-1 px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                    >
                      Test
                    </button>
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      className="flex-1 px-3 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
                    >
                      <TrashIcon className="h-4 w-4 mx-auto" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'templates':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Notification Templates</h3>
              <button className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">
                <PlusIcon className="h-4 w-4 mr-2" />
                Create Template
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {templates.map((template) => (
                <div key={template.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">{template.name}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{template.category}</p>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm font-medium">Subject:</span>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{template.subject_template}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium">Body:</span>
                      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">{template.body_template}</p>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Channels</span>
                      <span className="font-medium">{template.channels.length}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'preferences':
        return preferences ? (
          <NotificationPreferencesCard
            preferences={preferences}
            onUpdate={setPreferences}
          />
        ) : null;

      case 'history':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Notification History</h3>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Title</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Category</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Channels</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Sent At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {history.map((notification) => (
                    <tr key={notification.id}>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{notification.title}</td>
                      <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 capitalize">{notification.category}</td>
                      <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{notification.channels.join(', ')}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={cn(
                          "px-2 py-1 text-xs rounded-full",
                          notification.status === 'delivered' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                          notification.status === 'sent' ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" :
                          notification.status === 'failed' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                          "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                        )}>
                          {notification.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                        {new Date(notification.sent_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );

      case 'analytics':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Notification Analytics</h3>
            {analytics && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center">
                  <div className="text-2xl font-bold text-blue-600">{analytics.total_sent}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Total Sent</div>
                </div>
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center">
                  <div className="text-2xl font-bold text-green-600">{analytics.delivery_rate.toFixed(1)}%</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Delivery Rate</div>
                </div>
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center">
                  <div className="text-2xl font-bold text-purple-600">{analytics.read_rate.toFixed(1)}%</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Read Rate</div>
                </div>
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center">
                  <div className="text-2xl font-bold text-orange-600">{analytics.total_read}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Total Read</div>
                </div>
              </div>
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Advanced Notifications System</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage notification rules, templates, and preferences</p>
        </div>
        <div className="flex items-center space-x-2">
          <BellIcon className="h-8 w-8 text-blue-500" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b dark:border-gray-700">
        {[
          { id: 'rules', name: 'Rules', icon: CogIcon },
          { id: 'templates', name: 'Templates', icon: DocumentIcon },
          { id: 'preferences', name: 'Preferences', icon: UserIcon },
          { id: 'history', name: 'History', icon: ClockIcon },
          { id: 'analytics', name: 'Analytics', icon: ChartBarIcon }
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

      {/* Rule Builder Modal */}
      {showRuleBuilder && (
        <NotificationRuleBuilder
          rule={editingRule || undefined}
          onSave={handleRuleSave}
          onCancel={() => {
            setShowRuleBuilder(false);
            setEditingRule(null);
          }}
        />
      )}
    </div>
  );
};

export default AdvancedNotificationsSystem;
