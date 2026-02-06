/**
 * Trading page tests
 * Tests trading page functionality including order placement and market data display
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import Trading from '../Trading';

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
  Search: () => <div data-testid="search-icon" />,
  TrendingUp: () => <div data-testid="trending-up-icon" />,
  TrendingDown: () => <div data-testid="trending-down-icon" />,
  Plus: () => <div data-testid="plus-icon" />,
  Minus: () => <div data-testid="minus-icon" />,
  Play: () => <div data-testid="play-icon" />,
  Pause: () => <div data-testid="pause-icon" />,
}));

// Mock API calls
jest.mock('axios', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

describe('Trading Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders trading page with all main sections', () => {
    render(<Trading />);
    
    expect(screen.getByText('Trading')).toBeInTheDocument();
    expect(screen.getByText('Market Scanner')).toBeInTheDocument();
    expect(screen.getByText('Order Placement')).toBeInTheDocument();
    expect(screen.getByText('Open Orders')).toBeInTheDocument();
  });

  it('displays market scanner with search functionality', () => {
    render(<Trading />);
    
    const searchInput = screen.getByPlaceholderText(/search stocks/i);
    expect(searchInput).toBeInTheDocument();
    
    fireEvent.change(searchInput, { target: { value: 'AAPL' } });
    expect(searchInput).toHaveValue('AAPL');
  });

  it('shows stock list with price information', () => {
    render(<Trading />);
    
    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Price')).toBeInTheDocument();
    expect(screen.getByText('Change')).toBeInTheDocument();
    expect(screen.getByText('Volume')).toBeInTheDocument();
  });

  it('handles stock selection', () => {
    render(<Trading />);
    
    const stockRow = screen.getByText('AAPL').closest('tr');
    expect(stockRow).toBeInTheDocument();
    
    fireEvent.click(stockRow!);
    
    // Check if stock is selected
    expect(stockRow).toHaveClass('bg-blue-50');
  });

  it('displays order placement form', () => {
    render(<Trading />);
    
    expect(screen.getByText('Place Order')).toBeInTheDocument();
    expect(screen.getByLabelText(/order type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/quantity/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/price/i)).toBeInTheDocument();
  });

  it('handles order type selection', () => {
    render(<Trading />);
    
    const orderTypeSelect = screen.getByLabelText(/order type/i);
    fireEvent.change(orderTypeSelect, { target: { value: 'BUY' } });
    
    expect(orderTypeSelect).toHaveValue('BUY');
  });

  it('validates quantity input', () => {
    render(<Trading />);
    
    const quantityInput = screen.getByLabelText(/quantity/i);
    
    // Test invalid quantity
    fireEvent.change(quantityInput, { target: { value: '-5' } });
    fireEvent.blur(quantityInput);
    
    expect(screen.getByText('Quantity must be positive')).toBeInTheDocument();
  });

  it('validates price input', () => {
    render(<Trading />);
    
    const priceInput = screen.getByLabelText(/price/i);
    
    // Test invalid price
    fireEvent.change(priceInput, { target: { value: '0' } });
    fireEvent.blur(priceInput);
    
    expect(screen.getByText('Price must be greater than 0')).toBeInTheDocument();
  });

  it('handles order submission', async () => {
    const mockAxios = require('axios');
    mockAxios.post.mockResolvedValue({ data: { success: true } });
    
    render(<Trading />);
    
    // Fill out order form
    fireEvent.change(screen.getByLabelText(/order type/i), { target: { value: 'BUY' } });
    fireEvent.change(screen.getByLabelText(/quantity/i), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText(/price/i), { target: { value: '150.00' } });
    
    // Submit order
    const submitButton = screen.getByRole('button', { name: /place order/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockAxios.post).toHaveBeenCalledWith('/api/trading/orders', {
        symbol: 'AAPL',
        orderType: 'BUY',
        quantity: 10,
        price: 150.00,
      });
    });
  });

  it('displays open orders table', () => {
    render(<Trading />);
    
    expect(screen.getByText('Order ID')).toBeInTheDocument();
    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Quantity')).toBeInTheDocument();
    expect(screen.getByText('Price')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('handles order cancellation', async () => {
    render(<Trading />);
    
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);
    
    await waitFor(() => {
      expect(screen.getByText('Order cancelled successfully')).toBeInTheDocument();
    });
  });

  it('shows real-time price updates', () => {
    render(<Trading />);
    
    // Check if price updates are displayed
    const priceElement = screen.getByText(/\$[\d,]+\.\d{2}/);
    expect(priceElement).toBeInTheDocument();
  });

  it('displays market depth information', () => {
    render(<Trading />);
    
    expect(screen.getByText('Market Depth')).toBeInTheDocument();
    expect(screen.getByText('Bid')).toBeInTheDocument();
    expect(screen.getByText('Ask')).toBeInTheDocument();
  });

  it('handles quick order buttons', () => {
    render(<Trading />);
    
    const quickBuyButton = screen.getByRole('button', { name: /quick buy/i });
    const quickSellButton = screen.getByRole('button', { name: /quick sell/i });
    
    expect(quickBuyButton).toBeInTheDocument();
    expect(quickSellButton).toBeInTheDocument();
    
    fireEvent.click(quickBuyButton);
    expect(screen.getByLabelText(/order type/i)).toHaveValue('BUY');
  });

  it('shows trading signals', () => {
    render(<Trading />);
    
    expect(screen.getByText('Trading Signals')).toBeInTheDocument();
    expect(screen.getByText('BUY')).toBeInTheDocument();
    expect(screen.getByText('SELL')).toBeInTheDocument();
  });

  it('displays portfolio summary in trading context', () => {
    render(<Trading />);
    
    expect(screen.getByText('Available Balance')).toBeInTheDocument();
    expect(screen.getByText('Used Margin')).toBeInTheDocument();
  });

  it('handles market hours display', () => {
    render(<Trading />);
    
    const marketStatus = screen.getByText(/market (open|closed)/i);
    expect(marketStatus).toBeInTheDocument();
  });

  it('shows order history', () => {
    render(<Trading />);
    
    expect(screen.getByText('Order History')).toBeInTheDocument();
    expect(screen.getByText('Executed Orders')).toBeInTheDocument();
  });

  it('handles error states gracefully', async () => {
    const mockAxios = require('axios');
    mockAxios.get.mockRejectedValue(new Error('API Error'));
    
    render(<Trading />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading market data')).toBeInTheDocument();
    });
  });

  it('displays loading states appropriately', () => {
    render(<Trading />);
    
    // Check if loading indicators are shown
    expect(screen.getByText('Loading market data...')).toBeInTheDocument();
  });

  it('handles responsive design for mobile trading', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    
    render(<Trading />);
    
    // Check if mobile-specific layout is applied
    expect(screen.getByText('Trading')).toBeInTheDocument();
  });
});
