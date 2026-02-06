/**
 * Alert Manager Component
 * Create, view, and manage price alerts
 */

import React, { useState, useEffect } from 'react';
import { alertApi, Alert, AlertResponse } from '../services/alertApi';
import { Bell, BellOff, Plus, Trash2, Volume2, VolumeX, Settings } from 'lucide-react';
import { autoAlertService, AutoAlertRule } from '../services/autoAlertService';

interface AlertManagerProps {
  symbol: string;
  currentPrice?: number;
  className?: string;
}

export const AlertManager: React.FC<AlertManagerProps> = ({
  symbol,
  currentPrice,
  className = '',
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(false);

  // New alert form state
  const [newAlert, setNewAlert] = useState<Partial<Alert>>({
    alert_type: 'price_level',
    condition: 'crosses',
    threshold_percent: 1.0,
    enabled: true,
    notify_browser: true,
    notify_sound: true,
    notify_email: false,
  });

  // Auto-refresh price checking
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  
  // Auto-alert settings
  const [showAutoAlertSettings, setShowAutoAlertSettings] = useState(false);
  const [autoAlertRules, setAutoAlertRules] = useState<AutoAlertRule[]>([]);
  
  // Load alerts for symbol
  useEffect(() => {
    if (symbol) {
      loadAlerts();
    }
  }, [symbol]);

  // Load auto-alert rules
  useEffect(() => {
    setAutoAlertRules(autoAlertService.getRules());
  }, []);

  // Auto-refresh: Check alerts every 5 seconds
  useEffect(() => {
    if (!autoRefresh || !symbol || !currentPrice || alerts.length === 0) {
      return;
    }

    const checkInterval = setInterval(async () => {
      try {
        const response = await alertApi.checkAlerts(symbol, currentPrice);
        setLastCheck(new Date());
        
        if (response.triggered_alerts && response.triggered_alerts.length > 0) {
          // Play sound if enabled
          response.triggered_alerts.forEach((alert: any) => {
            if (alert.notify_sound) {
              playAlertSound();
            }
            
            // Show browser notification
            if (alert.notify_browser && 'Notification' in window) {
              if (Notification.permission === 'granted') {
                new Notification(`Alert: ${symbol}`, {
                  body: `Price ${alert.condition} ${alert.target_price}. Current: ₹${currentPrice}`,
                  icon: '/logo192.png',
                });
              } else if (Notification.permission !== 'denied') {
                Notification.requestPermission();
              }
            }
          });
          
          // Reload alerts to update triggered status
          loadAlerts();
        }
      } catch (error) {
        console.error('Error checking alerts:', error);
      }
    }, 5000); // Check every 5 seconds

    return () => clearInterval(checkInterval);
  }, [autoRefresh, symbol, currentPrice, alerts]);

  const playAlertSound = () => {
    // Play alert sound
    const audio = new Audio('/alert-sound.mp3'); // You'll need to add this file
    audio.play().catch(err => console.log('Could not play sound:', err));
  };

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await alertApi.listAlerts(symbol);
      if (response.success && response.alerts) {
        setAlerts(response.alerts);
      }
    } catch (error) {
      console.error('Failed to load alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlert = async () => {
    if (!newAlert.target_price || newAlert.target_price <= 0) {
      window.alert('Please enter a valid target price');
      return;
    }

    try {
      const alertData: Alert = {
        ...newAlert,
        symbol,
      } as Alert;

      const response = await alertApi.createAlert(alertData);

      if (response.success) {
        // Show browser notification
        if (Notification.permission === 'granted') {
          new Notification('Alert Created', {
            body: `Alert set for ${symbol} at ₹${newAlert.target_price}`,
            icon: '/favicon.ico',
          });
        }

        // Play sound
        if (newAlert.notify_sound) {
          playSound('success');
        }

        // Reset form and reload
        setIsCreating(false);
        setNewAlert({
          alert_type: 'price_level',
          condition: 'crosses',
          threshold_percent: 1.0,
          enabled: true,
          notify_browser: true,
          notify_sound: true,
          notify_email: false,
        });
        loadAlerts();
      }
    } catch (error) {
      console.error('Failed to create alert:', error);
      window.alert('Failed to create alert');
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    if (!window.confirm('Delete this alert?')) return;

    try {
      await alertApi.deleteAlert(alertId);
      loadAlerts();
    } catch (error) {
      console.error('Failed to delete alert:', error);
    }
  };

  const handleToggleAlert = async (alertId: string, currentEnabled: boolean) => {
    try {
      await alertApi.updateAlert(alertId, !currentEnabled);
      loadAlerts();
    } catch (error) {
      console.error('Failed to toggle alert:', error);
    }
  };

  const requestNotificationPermission = async () => {
    if (Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        new Notification('Notifications Enabled', {
          body: 'You will receive alerts from Trader AI',
          icon: '/favicon.ico',
        });
      }
    }
  };

  const playSound = (type: 'success' | 'alert' = 'alert') => {
    // Simple audio feedback using Web Audio API
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = type === 'success' ? 800 : 1000;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.3);
  };

  return (
    <div className={`bg-[#1E222D] rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Price Alerts</h3>
          {currentPrice && (
            <span className="text-sm text-gray-400">
              Current: ₹{currentPrice.toFixed(2)}
            </span>
          )}
          {/* Auto-refresh indicator */}
          {autoRefresh && lastCheck && (
            <span className="text-xs text-green-400 flex items-center gap-1">
              <span className="animate-pulse">●</span>
              Live (checked {new Date().toLocaleTimeString()})
            </span>
          )}
        </div>
        
        {/* Auto-refresh toggle */}
        <button
          onClick={() => setAutoRefresh(!autoRefresh)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${
            autoRefresh 
              ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30' 
              : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
          }`}
          title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
        >
          {autoRefresh ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          <span className="text-sm font-medium">
            {autoRefresh ? 'Auto-Check ON' : 'Auto-Check OFF'}
          </span>
        </button>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAutoAlertSettings(!showAutoAlertSettings)}
            className="flex items-center gap-2 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm transition-colors"
            title="Auto-Alert Settings"
          >
            <Settings className="w-4 h-4" />
            Auto-Alerts
          </button>
          <button
            onClick={() => {
              setIsCreating(!isCreating);
              if (!isCreating) requestNotificationPermission();
            }}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Alert
          </button>
        </div>
      </div>

      {/* Auto-Alert Settings Panel */}
      {showAutoAlertSettings && (
        <div className="mb-4 p-4 bg-[#131722] rounded-lg border border-purple-700/30">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-white font-medium flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Auto-Alert Rules
            </h4>
            <button
              onClick={() => setShowAutoAlertSettings(false)}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>
          <p className="text-xs text-gray-400 mb-3">
            Automatically create alerts when analysis detects events (zone breaks, structure changes, patterns)
          </p>
          <div className="space-y-2">
            {autoAlertRules.map((rule) => (
              <div key={rule.id} className="flex items-center justify-between p-2 bg-[#1E222D] rounded">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={rule.enabled}
                    onChange={(e) => {
                      const updated = { ...rule, enabled: e.target.checked };
                      autoAlertService.setRule(updated);
                      setAutoAlertRules(autoAlertService.getRules());
                    }}
                    className="rounded"
                  />
                  <span className="text-sm text-white">{rule.name}</span>
                </div>
                <span className="text-xs text-gray-400 capitalize">
                  {rule.eventType.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create Alert Form */}
      {isCreating && (
        <div className="mb-4 p-4 bg-[#131722] rounded-lg border border-gray-700">
          <h4 className="text-white font-medium mb-3">Create New Alert</h4>

          <div className="space-y-3">
            {/* Target Price */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">Target Price (₹)</label>
              <input
                type="number"
                value={newAlert.target_price || ''}
                onChange={(e) =>
                  setNewAlert({ ...newAlert, target_price: parseFloat(e.target.value) })
                }
                placeholder="Enter target price"
                className="w-full px-3 py-2 bg-[#1E222D] text-white rounded border border-gray-700 focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Threshold */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                Threshold: {newAlert.threshold_percent}%
              </label>
              <input
                type="range"
                min="0.1"
                max="5"
                step="0.1"
                value={newAlert.threshold_percent || 1}
                onChange={(e) =>
                  setNewAlert({ ...newAlert, threshold_percent: parseFloat(e.target.value) })
                }
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Alert when price is within {newAlert.threshold_percent}% of target
              </p>
            </div>

            {/* Notification Options */}
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newAlert.notify_browser}
                  onChange={(e) =>
                    setNewAlert({ ...newAlert, notify_browser: e.target.checked })
                  }
                  className="rounded"
                />
                Browser Notification
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newAlert.notify_sound}
                  onChange={(e) =>
                    setNewAlert({ ...newAlert, notify_sound: e.target.checked })
                  }
                  className="rounded"
                />
                Sound Alert
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={handleCreateAlert}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Create Alert
              </button>
              <button
                onClick={() => setIsCreating(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Alert List */}
      <div className="space-y-2">
        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            No alerts set for {symbol}. Create one to get notified!
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border ${
                alert.enabled
                  ? 'bg-[#131722] border-blue-500/30'
                  : 'bg-[#131722]/50 border-gray-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">
                      ₹{alert.target_price?.toFixed(2)}
                    </span>
                    <span className="text-xs text-gray-500">
                      ±{alert.threshold_percent}%
                    </span>
                    {currentPrice && alert.target_price && (
                      <span
                        className={`text-xs font-medium ${
                          currentPrice > alert.target_price
                            ? 'text-green-400'
                            : 'text-red-400'
                        }`}
                      >
                        {currentPrice > alert.target_price ? '↑' : '↓'}
                        {Math.abs(
                          ((currentPrice - alert.target_price) / alert.target_price) * 100
                        ).toFixed(1)}
                        %
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                    {alert.notify_browser && <Bell className="w-3 h-3" />}
                    {alert.notify_sound && <Volume2 className="w-3 h-3" />}
                    {alert.created_at && (
                      <span>Created: {new Date(alert.created_at).toLocaleString()}</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleAlert(alert.id!, alert.enabled)}
                    className={`p-2 rounded-lg transition-colors ${
                      alert.enabled
                        ? 'text-blue-400 hover:bg-blue-500/10'
                        : 'text-gray-500 hover:bg-gray-700'
                    }`}
                    title={alert.enabled ? 'Disable alert' : 'Enable alert'}
                  >
                    {alert.enabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => handleDeleteAlert(alert.id!)}
                    className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Delete alert"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Notification Permission Reminder */}
      {Notification.permission === 'default' && (
        <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <p className="text-sm text-yellow-400">
            <Bell className="w-4 h-4 inline mr-2" />
            Enable browser notifications to receive alerts!
            <button
              onClick={requestNotificationPermission}
              className="ml-2 underline hover:text-yellow-300"
            >
              Enable Now
            </button>
          </p>
        </div>
      )}
    </div>
  );
};

