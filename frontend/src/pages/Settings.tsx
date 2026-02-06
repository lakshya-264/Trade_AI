import React, { useState } from 'react';
import { 
  CogIcon,
  UserIcon,
  BellIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [settings, setSettings] = useState({
    profile: {
      username: 'demo',
      email: 'demo@traderai.com',
      firstName: 'Demo',
      lastName: 'User',
      phone: '+91 98765 43210'
    },
    notifications: {
      emailAlerts: true,
      smsAlerts: false,
      pushNotifications: true,
      tradingSignals: true,
      priceAlerts: true,
      newsUpdates: false
    },
    trading: {
      defaultOrderType: 'MARKET',
      defaultQuantity: 1,
      autoConfirmOrders: false,
      riskLimit: 2.0,
      maxPositionSize: 100000,
      stopLossPercentage: 5.0
    },
    risk: {
      maxPortfolioRisk: 2.0,
      maxConcentration: 20.0,
      maxCorrelation: 0.7,
      enableRiskAlerts: true,
      riskThreshold: 1.5
    }
  });

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'trading', name: 'Trading', icon: ChartBarIcon },
    { id: 'risk', name: 'Risk Management', icon: ShieldCheckIcon }
  ];

  const handleInputChange = (section: string, field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section as keyof typeof prev],
        [field]: value
      }
    }));
  };

  const handleSave = () => {
    // Save settings logic
    console.log('Saving settings:', settings);
  };

  const renderProfileSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
            <input
              type="text"
              value={settings.profile.firstName}
              onChange={(e) => handleInputChange('profile', 'firstName', e.target.value)}
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
            <input
              type="text"
              value={settings.profile.lastName}
              onChange={(e) => handleInputChange('profile', 'lastName', e.target.value)}
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={settings.profile.email}
              onChange={(e) => handleInputChange('profile', 'email', e.target.value)}
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
            <input
              type="tel"
              value={settings.profile.phone}
              onChange={(e) => handleInputChange('profile', 'phone', e.target.value)}
              className="input-field"
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
        <div className="space-y-4">
          {Object.entries(settings.notifications).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </label>
                <p className="text-sm text-gray-500">
                  {key === 'emailAlerts' && 'Receive alerts via email'}
                  {key === 'smsAlerts' && 'Receive alerts via SMS'}
                  {key === 'pushNotifications' && 'Receive push notifications'}
                  {key === 'tradingSignals' && 'Get notified about AI trading signals'}
                  {key === 'priceAlerts' && 'Get notified about price movements'}
                  {key === 'newsUpdates' && 'Receive market news updates'}
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={value as boolean}
                  onChange={(e) => handleInputChange('notifications', key, e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTradingSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Trading Preferences</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Default Order Type</label>
            <select
              value={settings.trading.defaultOrderType}
              onChange={(e) => handleInputChange('trading', 'defaultOrderType', e.target.value)}
              className="input-field"
            >
              <option value="MARKET">Market</option>
              <option value="LIMIT">Limit</option>
              <option value="STOP">Stop</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Default Quantity</label>
            <input
              type="number"
              value={settings.trading.defaultQuantity}
              onChange={(e) => handleInputChange('trading', 'defaultQuantity', parseInt(e.target.value))}
              className="input-field"
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Risk Limit (%)</label>
            <input
              type="number"
              value={settings.trading.riskLimit}
              onChange={(e) => handleInputChange('trading', 'riskLimit', parseFloat(e.target.value))}
              className="input-field"
              min="0.1"
              max="10"
              step="0.1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Max Position Size</label>
            <input
              type="number"
              value={settings.trading.maxPositionSize}
              onChange={(e) => handleInputChange('trading', 'maxPositionSize', parseInt(e.target.value))}
              className="input-field"
              min="1000"
            />
          </div>
        </div>
        <div className="mt-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.trading.autoConfirmOrders}
              onChange={(e) => handleInputChange('trading', 'autoConfirmOrders', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
            />
            <span className="ml-2 text-sm text-gray-700">Auto-confirm orders</span>
          </label>
        </div>
      </div>
    </div>
  );

  const renderRiskSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Risk Management Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Max Portfolio Risk (%)</label>
            <input
              type="number"
              value={settings.risk.maxPortfolioRisk}
              onChange={(e) => handleInputChange('risk', 'maxPortfolioRisk', parseFloat(e.target.value))}
              className="input-field"
              min="0.1"
              max="10"
              step="0.1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Max Concentration (%)</label>
            <input
              type="number"
              value={settings.risk.maxConcentration}
              onChange={(e) => handleInputChange('risk', 'maxConcentration', parseFloat(e.target.value))}
              className="input-field"
              min="1"
              max="100"
              step="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Max Correlation</label>
            <input
              type="number"
              value={settings.risk.maxCorrelation}
              onChange={(e) => handleInputChange('risk', 'maxCorrelation', parseFloat(e.target.value))}
              className="input-field"
              min="0.1"
              max="1"
              step="0.1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Risk Threshold (%)</label>
            <input
              type="number"
              value={settings.risk.riskThreshold}
              onChange={(e) => handleInputChange('risk', 'riskThreshold', parseFloat(e.target.value))}
              className="input-field"
              min="0.1"
              max="5"
              step="0.1"
            />
          </div>
        </div>
        <div className="mt-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.risk.enableRiskAlerts}
              onChange={(e) => handleInputChange('risk', 'enableRiskAlerts', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
            />
            <span className="ml-2 text-sm text-gray-700">Enable risk alerts</span>
          </label>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return renderProfileSettings();
      case 'notifications':
        return renderNotificationSettings();
      case 'trading':
        return renderTradingSettings();
      case 'risk':
        return renderRiskSettings();
      default:
        return renderProfileSettings();
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Manage your account and trading preferences</p>
        </div>
        <button onClick={handleSave} className="btn-primary">
          Save Changes
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="card">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
