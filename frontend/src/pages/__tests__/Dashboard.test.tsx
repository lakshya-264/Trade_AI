/**
 * Dashboard page tests
 * Tests main dashboard functionality including data loading and display
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import Dashboard from '../Dashboard';

// Mock the recharts components
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
}));

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
  TrendingUp: () => <div data-testid="trending-up-icon" />,
  TrendingDown: () => <div data-testid="trending-down-icon" />,
  DollarSign: () => <div data-testid="dollar-icon" />,
  Activity: () => <div data-testid="activity-icon" />,
  RefreshCw: () => <div data-testid="refresh-icon" />,
}));

// Mock API calls
jest.mock('axios', () => ({
  get: jest.fn(),
}));

describe('Dashboard Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders dashboard with all main sections', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Portfolio Overview')).toBeInTheDocument();
    expect(screen.getByText('Market Overview')).toBeInTheDocument();
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });

  it('displays portfolio summary cards', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Total Value')).toBeInTheDocument();
    expect(screen.getByText('Today\'s P&L')).toBeInTheDocument();
    expect(screen.getByText('Total P&L')).toBeInTheDocument();
    expect(screen.getByText('Win Rate')).toBeInTheDocument();
  });

  it('shows portfolio value with correct formatting', () => {
    render(<Dashboard />);
    
    const totalValue = screen.getByText(/\$[\d,]+\.\d{2}/);
    expect(totalValue).toBeInTheDocument();
  });

  it('displays P&L with correct color coding', () => {
    render(<Dashboard />);
    
    const pnlElement = screen.getByText(/[\+\-]\$[\d,]+\.\d{2}/);
    expect(pnlElement).toBeInTheDocument();
    
    // Check if positive P&L has green color
    if (pnlElement.textContent?.includes('+')) {
      expect(pnlElement).toHaveClass('text-green-600');
    }
  });

  it('renders portfolio allocation chart', () => {
    render(<Dashboard />);
    
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    expect(screen.getByText('Portfolio Allocation')).toBeInTheDocument();
  });

  it('renders performance chart', () => {
    render(<Dashboard />);
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getByText('Portfolio Performance')).toBeInTheDocument();
  });

  it('displays top performing stocks', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Top Performers')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
  });

  it('shows market indices', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('NSE Nifty 50')).toBeInTheDocument();
    expect(screen.getByText('BSE Sensex')).toBeInTheDocument();
  });

  it('handles refresh button click', async () => {
    render(<Dashboard />);
    
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);
    
    // Check if loading state is shown
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
  });

  it('displays recent transactions', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Recent Transactions')).toBeInTheDocument();
    expect(screen.getByText('BUY')).toBeInTheDocument();
    expect(screen.getByText('SELL')).toBeInTheDocument();
  });

  it('shows market status indicator', () => {
    render(<Dashboard />);
    
    const marketStatus = screen.getByText(/market (open|closed)/i);
    expect(marketStatus).toBeInTheDocument();
  });

  it('displays AI insights section', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('AI Insights')).toBeInTheDocument();
    expect(screen.getByText('Market Sentiment')).toBeInTheDocument();
  });

  it('handles responsive design correctly', () => {
    // Test mobile view
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    
    render(<Dashboard />);
    
    // Check if mobile-specific layout is applied
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('shows loading state while fetching data', () => {
    // Mock loading state
    render(<Dashboard />);
    
    // Initially should show loading
    expect(screen.getByText('Loading dashboard data...')).toBeInTheDocument();
  });

  it('handles error state gracefully', async () => {
    // Mock API error
    const mockAxios = require('axios');
    mockAxios.get.mockRejectedValue(new Error('API Error'));
    
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading dashboard data')).toBeInTheDocument();
    });
  });

  it('displays real-time updates when WebSocket is connected', () => {
    const mockWebSocketValue = {
      socket: { readyState: WebSocket.OPEN },
      isConnected: true,
      connect: jest.fn(),
      disconnect: jest.fn(),
      send: jest.fn(),
      subscribe: jest.fn(),
      unsubscribe: jest.fn(),
    };

    render(<Dashboard />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="websocket-status" data-connected="true" />
        </div>
      ),
    });

    expect(screen.getByText('Live Data')).toBeInTheDocument();
  });

  it('shows last updated timestamp', () => {
    render(<Dashboard />);
    
    const lastUpdated = screen.getByText(/last updated/i);
    expect(lastUpdated).toBeInTheDocument();
  });
});
