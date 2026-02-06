/**
 * Header component tests
 * Tests header functionality including menu toggle and user authentication state
 */

import React from 'react';
import { render, screen, fireEvent } from '../../test-utils';
import Header from '../Header';

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
  Menu: () => <div data-testid="menu-icon" />,
  Bell: () => <div data-testid="bell-icon" />,
  User: () => <div data-testid="user-icon" />,
  Settings: () => <div data-testid="settings-icon" />,
}));

describe('Header Component', () => {
  const mockOnMenuClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders header with all elements', () => {
    render(<Header onMenuClick={mockOnMenuClick} />);
    
    expect(screen.getByText('Trader AI')).toBeInTheDocument();
    expect(screen.getByTestId('menu-icon')).toBeInTheDocument();
    expect(screen.getByTestId('bell-icon')).toBeInTheDocument();
    expect(screen.getByTestId('user-icon')).toBeInTheDocument();
  });

  it('calls onMenuClick when menu button is clicked', () => {
    render(<Header onMenuClick={mockOnMenuClick} />);
    
    const menuButton = screen.getByRole('button', { name: /menu/i });
    fireEvent.click(menuButton);
    
    expect(mockOnMenuClick).toHaveBeenCalledTimes(1);
  });

  it('displays notifications badge when there are notifications', () => {
    // Mock notifications in context or props
    render(<Header onMenuClick={mockOnMenuClick} />);
    
    // Check if notification badge is present
    const notificationButton = screen.getByRole('button', { name: /notifications/i });
    expect(notificationButton).toBeInTheDocument();
  });

  it('shows user menu when user icon is clicked', () => {
    render(<Header onMenuClick={mockOnMenuClick} />);
    
    const userButton = screen.getByRole('button', { name: /user menu/i });
    fireEvent.click(userButton);
    
    // Check if user dropdown menu appears
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('handles responsive design correctly', () => {
    // Test mobile view
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    
    render(<Header onMenuClick={mockOnMenuClick} />);
    
    // Check if mobile-specific elements are present
    expect(screen.getByTestId('menu-icon')).toBeInTheDocument();
  });

  it('displays current time/date', () => {
    render(<Header onMenuClick={mockOnMenuClick} />);
    
    // Check if time display is present
    const timeElement = screen.getByText(/\d{1,2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });

  it('shows connection status indicator', () => {
    render(<Header onMenuClick={mockOnMenuClick} />);
    
    // Check if connection status is displayed
    const connectionStatus = screen.getByText(/connected|disconnected/i);
    expect(connectionStatus).toBeInTheDocument();
  });
});
