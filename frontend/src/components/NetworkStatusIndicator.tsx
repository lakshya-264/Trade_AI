import React from 'react';
import { 
  WifiIcon, 
  SignalSlashIcon, 
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import { useNetworkStatus } from '../hooks/useNetworkStatus';

const NetworkStatusIndicator: React.FC = () => {
  const { isOnline, isSlowConnection, connectionType } = useNetworkStatus();

  if (!isOnline) {
    return (
      <div className="flex items-center space-x-2 px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
        <SignalSlashIcon className="h-4 w-4" />
        <span>Offline</span>
      </div>
    );
  }

  if (isSlowConnection) {
    return (
      <div className="flex items-center space-x-2 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
        <ExclamationTriangleIcon className="h-4 w-4" />
        <span>Slow Connection</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
      <WifiIcon className="h-4 w-4" />
      <span>Online</span>
      {connectionType && (
        <span className="text-xs opacity-75">({connectionType})</span>
      )}
    </div>
  );
};

export default NetworkStatusIndicator;
