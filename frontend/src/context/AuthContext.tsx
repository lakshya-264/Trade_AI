import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { authConfig, getMockUser, isMockAuthEnabled, getApiBaseUrl } from '../config/authConfig';
import { api } from '../services/api';

interface User {
  id: number;
  username: string;
  email: string;
  mobile_number?: string;
  is_active: boolean;
  role: string;
  created_at: string;
  last_login?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string, rememberMe?: boolean) => Promise<boolean>;
  signup: (username: string, email: string, password: string, mobileNumber?: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
  token: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

const API_BASE_URL = getApiBaseUrl();
const USE_MOCK_AUTH = isMockAuthEnabled();

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Helper to get storage (sessionStorage by default, localStorage if "Remember Me" was checked)
  const getStorage = (): Storage => {
    // Check if user opted for "Remember Me" (in localStorage)
    const rememberMe = localStorage.getItem('rememberMe') === 'true';
    return rememberMe ? localStorage : sessionStorage;
  };

  useEffect(() => {
    // Check if user is already logged in (from sessionStorage or localStorage)
    const storage = getStorage();
    const savedUser = storage.getItem('user');
    const savedToken = storage.getItem('token');
    
    if (savedUser && savedToken) {
      try {
        setUser(JSON.parse(savedUser));
        setToken(savedToken);
      } catch (error) {
        console.error('Error parsing saved user:', error);
        storage.removeItem('user');
        storage.removeItem('token');
        localStorage.removeItem('rememberMe');
      }
    }
    setLoading(false);

    // Auto-logout on window close (clear sessionStorage)
    const handleBeforeUnload = () => {
      // Only clear if NOT using "Remember Me"
      if (localStorage.getItem('rememberMe') !== 'true') {
        sessionStorage.clear();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Handle session invalidation (from new login on another device)
    const handleSessionInvalidated = () => {
      console.warn('Session invalidated - logging out');
      // Clear user state immediately
      setUser(null);
      setToken(null);
      // Clear storage
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('rememberMe');
      sessionStorage.removeItem('user');
      sessionStorage.removeItem('token');
      // Redirect to login
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?reason=session_invalidated';
      }
    };
    
    window.addEventListener('session-invalidated', handleSessionInvalidated as EventListener);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('session-invalidated', handleSessionInvalidated as EventListener);
    };
  }, []);

  const login = async (username: string, password: string, rememberMe: boolean = false): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Store "Remember Me" preference
      if (rememberMe) {
        localStorage.setItem('rememberMe', 'true');
      } else {
        localStorage.removeItem('rememberMe');
      }
      
      // Use appropriate storage based on "Remember Me"
      const storage: Storage = rememberMe ? localStorage : sessionStorage;
      
      // MOCK AUTHENTICATION (Set USE_MOCK_AUTH = true to enable)
      if (USE_MOCK_AUTH) {
        console.log('Using mock authentication...');
        
        const mockUser = getMockUser(username, password);
        if (mockUser) {
          setUser(mockUser.userData);
          setToken('mock-token-' + Date.now());
          storage.setItem('user', JSON.stringify(mockUser.userData));
          storage.setItem('token', 'mock-token-' + Date.now());
          return true;
        }
        
        return false;
      }
      
      // REAL API AUTHENTICATION (Currently Active)
      const data = await api.loginForm(username, password);
      
      // Check if login was successful and has data
      if (!data.success || !data.data) {
        throw new Error('Login failed');
      }
      
      // Get user data from token (we need to fetch user details)
      try {
        const userData = await api.getCurrentUser();
        
        // Store user data and token in appropriate storage
        if (userData.success && userData.data) {
          setUser(userData.data);
          setToken(data.access_token || '');
          storage.setItem('user', JSON.stringify(userData.data));
          storage.setItem('token', data.access_token || '');
        } else {
          throw new Error('Failed to get user data');
        }
        
        return true;
      } catch (error) {
        // Fallback: create user object from token data
        // Extract user ID from token if possible
        let userId = 1; // Default fallback
        try {
          if (data.access_token) {
            const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]));
            userId = parseInt(tokenPayload.sub) || 1;
          }
        } catch (e) {
          console.warn('Could not extract user ID from token, using fallback');
        }
        
        const fallbackUser: User = {
          id: userId, // Use extracted ID or fallback to 1
          username: username,
          email: `${username}@traderai.com`,
          is_active: true,
          role: 'user',
          created_at: new Date().toISOString(),
        };
        
        setUser(fallbackUser);
        setToken(data.access_token || '');
        storage.setItem('user', JSON.stringify(fallbackUser));
        storage.setItem('token', data.access_token || '');
        
        return true;
      }
    } catch (error) {
      console.error('Login error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (username: string, email: string, password: string, mobileNumber?: string): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Use sessionStorage for signup (auto-logout on close)
      const storage = sessionStorage;
      
      // MOCK AUTHENTICATION (Set USE_MOCK_AUTH = true to enable)
      if (USE_MOCK_AUTH) {
        console.log('Using mock signup...');
        
        // Simulate successful signup
        const userData: User = {
          id: Date.now(),
          username: username,
          email: email,
          mobile_number: mobileNumber,
          is_active: true,
          role: 'user',
          created_at: new Date().toISOString(),
        };
        
        setUser(userData);
        setToken('mock-token-' + Date.now());
        storage.setItem('user', JSON.stringify(userData));
        storage.setItem('token', 'mock-token-' + Date.now());
        return true;
      }
      
      // REAL API AUTHENTICATION
      const data = await api.register(username, email, password, mobileNumber);
      
      // Backend returns user data directly on success (status 201)
      if (data && (data as any).id) {
        // Auto-login after successful signup
        return await login(username, password);
      } else {
        console.error('Signup failed:', (data as any)?.detail || 'Unknown error');
        return false;
      }
    } catch (error) {
      console.error('Signup error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    // Call logout endpoint to invalidate session on server
    try {
      if (token) {
        await api.logout();
      }
    } catch (error) {
      console.error('Error during logout:', error);
      // Continue with local logout even if API call fails
    }
    
    setUser(null);
    setToken(null);
    
    // Clear from both storages
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('rememberMe');
    sessionStorage.removeItem('user');
    sessionStorage.removeItem('token');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user && !!token,
    login,
    signup,
    logout,
    loading,
    token
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
