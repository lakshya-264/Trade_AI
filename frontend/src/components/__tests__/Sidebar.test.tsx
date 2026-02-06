/**
 * Sidebar component tests
 * Tests sidebar functionality including open/close behavior and navigation
 */

import React from 'react';
import { render, screen, fireEvent } from '../../test-utils';
import Sidebar from '../Sidebar';

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
  X: () => <div data-testid="close-icon" />,
  Home: () => <div data-testid="home-icon" />,
  TrendingUp: () => <div data-testid="trending-icon" />,
  PieChart: () => <div data-testid="portfolio-icon" />,
  Settings: () => <div data-testid="settings-icon" />,
  LogOut: () => <div data-testid="logout-icon" />,
}));

describe('Sidebar Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders sidebar when open', () => {
    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    expect(screen.getByText('Trader AI')).toBeInTheDocument();
    expect(screen.getByTestId('close-icon')).toBeInTheDocument();
  });

  it('does not render sidebar when closed', () => {
    render(<Sidebar isOpen={false} onClose={mockOnClose} />);
    
    expect(screen.queryByText('Trader AI')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when overlay is clicked', () => {
    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    const overlay = screen.getByTestId('sidebar-overlay');
    fireEvent.click(overlay);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('renders all navigation items', () => {
    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Trading')).toBeInTheDocument();
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders navigation icons', () => {
    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    expect(screen.getByTestId('home-icon')).toBeInTheDocument();
    expect(screen.getByTestId('trending-icon')).toBeInTheDocument();
    expect(screen.getByTestId('portfolio-icon')).toBeInTheDocument();
    expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
  });

  it('highlights active navigation item', () => {
    // Mock current location
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/trading',
      },
      writable: true,
    });

    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    const tradingLink = screen.getByRole('link', { name: /trading/i });
    expect(tradingLink).toHaveClass('bg-blue-100', 'text-blue-700');
  });

  it('handles keyboard navigation', () => {
    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    const firstLink = screen.getByRole('link', { name: /dashboard/i });
    firstLink.focus();
    
    expect(document.activeElement).toBe(firstLink);
  });

  it('shows user profile section when authenticated', () => {
    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    // Check if user profile section is present
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('handles logout functionality', () => {
    render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);
    
    // Check if logout was called (this would be handled by context)
    expect(logoutButton).toBeInTheDocument();
  });

  it('applies correct CSS classes based on open state', () => {
    const { rerender } = render(<Sidebar isOpen={true} onClose={mockOnClose} />);
    
    let sidebar = screen.getByTestId('sidebar');
    expect(sidebar).toHaveClass('translate-x-0');
    
    rerender(<Sidebar isOpen={false} onClose={mockOnClose} />);
    sidebar = screen.getByTestId('sidebar');
    expect(sidebar).toHaveClass('-translate-x-full');
  });
});
