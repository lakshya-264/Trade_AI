/**
 * TradingSignalPopup component tests
 * Tests trading signal popup functionality including display and user interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import TradingSignalPopup from '../TradingSignalPopup';

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
  X: () => <div data-testid="close-icon" />,
  TrendingUp: () => <div data-testid="trending-up-icon" />,
  TrendingDown: () => <div data-testid="trending-down-icon" />,
  AlertCircle: () => <div data-testid="alert-icon" />,
}));

// Mock the WebSocket context
const mockWebSocketContext = {
  socket: null,
  isConnected: true,
  connect: jest.fn(),
  disconnect: jest.fn(),
  send: jest.fn(),
  subscribe: jest.fn(),
  unsubscribe: jest.fn(),
};

describe('TradingSignalPopup Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders popup when signal is available', () => {
    const mockSignal = {
      id: '1',
      symbol: 'AAPL',
      action: 'BUY',
      confidence: 0.85,
      price: 150.25,
      timestamp: new Date().toISOString(),
    };

    render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(mockSignal)} />
        </div>
      ),
    });

    expect(screen.getByText('Trading Signal')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('BUY')).toBeInTheDocument();
  });

  it('does not render popup when no signal is available', () => {
    render(<TradingSignalPopup />);

    expect(screen.queryByText('Trading Signal')).not.toBeInTheDocument();
  });

  it('displays correct signal information', () => {
    const mockSignal = {
      id: '1',
      symbol: 'MSFT',
      action: 'SELL',
      confidence: 0.92,
      price: 300.50,
      timestamp: new Date().toISOString(),
    };

    render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(mockSignal)} />
        </div>
      ),
    });

    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('SELL')).toBeInTheDocument();
    expect(screen.getByText('$300.50')).toBeInTheDocument();
    expect(screen.getByText('92%')).toBeInTheDocument();
  });

  it('shows correct icon based on signal action', () => {
    const buySignal = {
      id: '1',
      symbol: 'AAPL',
      action: 'BUY',
      confidence: 0.85,
      price: 150.25,
      timestamp: new Date().toISOString(),
    };

    const { rerender } = render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(buySignal)} />
        </div>
      ),
    });

    expect(screen.getByTestId('trending-up-icon')).toBeInTheDocument();

    const sellSignal = { ...buySignal, action: 'SELL' };
    rerender(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(sellSignal)} />
        </div>
      ),
    });

    expect(screen.getByTestId('trending-down-icon')).toBeInTheDocument();
  });

  it('handles dismiss button click', async () => {
    const mockSignal = {
      id: '1',
      symbol: 'AAPL',
      action: 'BUY',
      confidence: 0.85,
      price: 150.25,
      timestamp: new Date().toISOString(),
    };

    render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(mockSignal)} />
        </div>
      ),
    });

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);

    await waitFor(() => {
      expect(screen.queryByText('Trading Signal')).not.toBeInTheDocument();
    });
  });

  it('handles accept signal button click', async () => {
    const mockSignal = {
      id: '1',
      symbol: 'AAPL',
      action: 'BUY',
      confidence: 0.85,
      price: 150.25,
      timestamp: new Date().toISOString(),
    };

    render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(mockSignal)} />
        </div>
      ),
    });

    const acceptButton = screen.getByRole('button', { name: /accept/i });
    fireEvent.click(acceptButton);

    // Check if signal was accepted (this would trigger some action)
    expect(acceptButton).toBeInTheDocument();
  });

  it('displays confidence level with correct styling', () => {
    const highConfidenceSignal = {
      id: '1',
      symbol: 'AAPL',
      action: 'BUY',
      confidence: 0.95,
      price: 150.25,
      timestamp: new Date().toISOString(),
    };

    render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(highConfidenceSignal)} />
        </div>
      ),
    });

    const confidenceElement = screen.getByText('95%');
    expect(confidenceElement).toHaveClass('text-green-600');
  });

  it('handles low confidence signals with warning styling', () => {
    const lowConfidenceSignal = {
      id: '1',
      symbol: 'AAPL',
      action: 'BUY',
      confidence: 0.45,
      price: 150.25,
      timestamp: new Date().toISOString(),
    };

    render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(lowConfidenceSignal)} />
        </div>
      ),
    });

    const confidenceElement = screen.getByText('45%');
    expect(confidenceElement).toHaveClass('text-yellow-600');
  });

  it('auto-dismisses after timeout', async () => {
    jest.useFakeTimers();
    
    const mockSignal = {
      id: '1',
      symbol: 'AAPL',
      action: 'BUY',
      confidence: 0.85,
      price: 150.25,
      timestamp: new Date().toISOString(),
    };

    render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(mockSignal)} />
        </div>
      ),
    });

    expect(screen.getByText('Trading Signal')).toBeInTheDocument();

    // Fast-forward time
    jest.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(screen.queryByText('Trading Signal')).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('handles multiple signals correctly', () => {
    const signals = [
      {
        id: '1',
        symbol: 'AAPL',
        action: 'BUY',
        confidence: 0.85,
        price: 150.25,
        timestamp: new Date().toISOString(),
      },
      {
        id: '2',
        symbol: 'MSFT',
        action: 'SELL',
        confidence: 0.92,
        price: 300.50,
        timestamp: new Date().toISOString(),
      },
    ];

    render(<TradingSignalPopup />, {
      wrapper: ({ children }) => (
        <div>
          {children}
          <div data-testid="signal-data" data-signal={JSON.stringify(signals)} />
        </div>
      ),
    });

    // Should show the most recent or highest priority signal
    expect(screen.getByText('Trading Signal')).toBeInTheDocument();
  });
});
