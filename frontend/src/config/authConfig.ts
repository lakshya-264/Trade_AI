/**
 * Authentication Configuration
 * Control mock vs real authentication
 */

export interface AuthConfig {
  useMockAuth: boolean;
  mockUsers: {
    username: string;
    password: string;
    userData: {
      id: number;
      username: string;
      email: string;
      is_active: boolean;
      role: string;
      created_at: string;
    };
  }[];
  apiBaseUrl: string;
}

// Configuration object
export const authConfig: AuthConfig = {
  // Set to true for mock data, false for real backend
  useMockAuth: false,
  
  // Mock users for testing
  mockUsers: [
    {
      username: "admin",
      password: "AdminPass123",
      userData: {
        id: 1,
        username: "admin",
        email: "admin@traderai.com",
        is_active: true,
        role: "admin",
        created_at: new Date().toISOString(),
      }
    },
    {
      username: "demo",
      password: "demo", 
      userData: {
        id: 2,
        username: "demo",
        email: "demo@traderai.com",
        is_active: true,
        role: "user",
        created_at: new Date().toISOString(),
      }
    },
    {
      username: "trader",
      password: "trader",
      userData: {
        id: 3,
        username: "trader",
        email: "trader@traderai.com",
        is_active: true,
        role: "trader",
        created_at: new Date().toISOString(),
      }
    }
  ],
  
  // API base URL
  apiBaseUrl: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'
};

// Helper functions
export const getMockUser = (username: string, password: string) => {
  return authConfig.mockUsers.find(
    user => user.username === username && user.password === password
  );
};

export const isMockAuthEnabled = () => {
  // Check environment variable first, then config
  const envMockAuth = process.env.REACT_APP_USE_MOCK_AUTH;
  if (envMockAuth !== undefined) {
    return envMockAuth.toLowerCase() === 'true';
  }
  return authConfig.useMockAuth;
};

export const getApiBaseUrl = () => authConfig.apiBaseUrl;
