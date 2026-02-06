import { useState, useEffect } from 'react';

interface NetworkStatus {
  isOnline: boolean;
  isSlowConnection: boolean;
  connectionType?: string;
}

export const useNetworkStatus = (): NetworkStatus => {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>({
    isOnline: navigator.onLine,
    isSlowConnection: false,
    connectionType: undefined
  });

  useEffect(() => {
    const updateNetworkStatus = () => {
      const isOnline = navigator.onLine;
      
      // Check connection speed (basic heuristic)
      const isSlowConnection = !('connection' in navigator) || 
        (navigator as any).connection?.effectiveType === 'slow-2g' ||
        (navigator as any).connection?.effectiveType === '2g';
      
      const connectionType = (navigator as any).connection?.effectiveType;

      setNetworkStatus({
        isOnline,
        isSlowConnection,
        connectionType
      });
    };

    // Initial check
    updateNetworkStatus();

    // Listen for online/offline events
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);

    // Listen for connection changes
    if ('connection' in navigator) {
      (navigator as any).connection.addEventListener('change', updateNetworkStatus);
    }

    return () => {
      window.removeEventListener('online', updateNetworkStatus);
      window.removeEventListener('offline', updateNetworkStatus);
      
      if ('connection' in navigator) {
        (navigator as any).connection.removeEventListener('change', updateNetworkStatus);
      }
    };
  }, []);

  return networkStatus;
};
