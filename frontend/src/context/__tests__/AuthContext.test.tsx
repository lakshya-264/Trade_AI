/**
 * Authentication context tests
 * Tests authentication logic including login/logout functionality and token management
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '../../test-utils';
import { AuthProvider, useAuth } from '../AuthContext';

// Mock axios
const mockAxios = {
  post: jest.fn(),
  get: jest.fn(),
  defaults: {
    headers: {
      common: {},
    },
  },
};

jest.mock('axios', () => mockAxios);

// Test component that uses the auth context
const TestComponent = () => {
  const { user, isAuthenticated, login, logout, loading } = useAuth();

  return (
    <div>
      <div data-testid="user">{user ? user.username : 'No user'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'true' : 'false'}</div>
      <div data-testid="loading">{loading ? 'true' : 'false'}</div>
      <button onClick={() => login('testuser', 'password')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('provides initial auth state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('user')).toHaveTextContent('No user');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('loading')).toHaveTextContent('false');
  });

  it('handles successful login', async () => {
    const mockResponse = {
      data: {
        user: { id: 1, username: 'testuser', email: 'test@example.com' },
        token: 'mock-jwt-token',
      },
    };

    mockAxios.post.mockResolvedValue(mockResponse);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    expect(mockAxios.post).toHaveBeenCalledWith('/api/auth/login', {
      username: 'testuser',
      password: 'password',
    });
  });

  it('handles login failure', async () => {
    mockAxios.post.mockRejectedValue(new Error('Invalid credentials'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });
  });

  it('handles logout', async () => {
    // First login
    const mockResponse = {
      data: {
        user: { id: 1, username: 'testuser', email: 'test@example.com' },
        token: 'mock-jwt-token',
      },
    };

    mockAxios.post.mockResolvedValue(mockResponse);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Login
    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    // Logout
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No user');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });
  });

  it('persists auth state in localStorage', async () => {
    const mockResponse = {
      data: {
        user: { id: 1, username: 'testuser', email: 'test@example.com' },
        token: 'mock-jwt-token',
      },
    };

    mockAxios.post.mockResolvedValue(mockResponse);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(localStorage.getItem('auth_token')).toBe('mock-jwt-token');
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockResponse.data.user));
    });
  });

  it('restores auth state from localStorage on mount', () => {
    const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
    localStorage.setItem('auth_token', 'mock-jwt-token');
    localStorage.setItem('user', JSON.stringify(mockUser));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('user')).toHaveTextContent('testuser');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
  });

  it('handles token expiration', async () => {
    // Mock expired token response
    mockAxios.get.mockRejectedValue({ response: { status: 401 } });

    const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
    localStorage.setItem('auth_token', 'expired-token');
    localStorage.setItem('user', JSON.stringify(mockUser));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Should automatically logout on token expiration
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });
  });

  it('shows loading state during login', async () => {
    let resolveLogin: (value: any) => void;
    const loginPromise = new Promise((resolve) => {
      resolveLogin = resolve;
    });

    mockAxios.post.mockReturnValue(loginPromise);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    // Should show loading state
    expect(screen.getByTestId('loading')).toHaveTextContent('true');

    // Resolve the login
    act(() => {
      resolveLogin!({
        data: {
          user: { id: 1, username: 'testuser', email: 'test@example.com' },
          token: 'mock-jwt-token',
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });
  });

  it('handles network errors gracefully', async () => {
    mockAxios.post.mockRejectedValue(new Error('Network error'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });
  });

  it('clears auth state on logout', async () => {
    // First login
    const mockResponse = {
      data: {
        user: { id: 1, username: 'testuser', email: 'test@example.com' },
        token: 'mock-jwt-token',
      },
    };

    mockAxios.post.mockResolvedValue(mockResponse);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Login
    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    // Logout
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });
  });

  it('handles malformed stored data gracefully', () => {
    localStorage.setItem('auth_token', 'invalid-token');
    localStorage.setItem('user', 'invalid-json');

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
  });
});
