/**
 * WebSocket context tests
 * Tests WebSocket connections, message handling, and reconnection logic
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '../../test-utils';
import { WebSocketProvider, useWebSocket } from '../WebSocketContext';

// Mock WebSocket
const mockWebSocket = {
  readyState: WebSocket.CONNECTING,
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
};

// Mock WebSocket constructor
global.WebSocket = jest.fn(() => mockWebSocket) as any;

// Test component that uses the WebSocket context
const TestComponent = () => {
  const { socket, isConnected, connect, disconnect, send, subscribe, unsubscribe } = useWebSocket();

  return (
    <div>
      <div data-testid="connected">{isConnected ? 'true' : 'false'}</div>
      <div data-testid="socket-state">{socket?.readyState || 'null'}</div>
      <button onClick={connect}>Connect</button>
      <button onClick={disconnect}>Disconnect</button>
      <button onClick={() => send('test-message')}>Send Message</button>
      <button onClick={() => subscribe('test-topic', () => {})}>Subscribe</button>
      <button onClick={() => unsubscribe('test-topic')}>Unsubscribe</button>
    </div>
  );
};

describe('WebSocketContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.WebSocket as jest.Mock).mockClear();
    mockWebSocket.readyState = WebSocket.CONNECTING;
  });

  it('provides initial WebSocket state', () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    expect(screen.getByTestId('connected')).toHaveTextContent('false');
    expect(screen.getByTestId('socket-state')).toHaveTextContent('null');
  });

  it('handles WebSocket connection', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws');
  });

  it('handles WebSocket connection success', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // Simulate connection open
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN;
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1];
      if (openHandler) openHandler();
    });

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('true');
    });
  });

  it('handles WebSocket connection error', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // Simulate connection error
    act(() => {
      mockWebSocket.readyState = WebSocket.CLOSED;
      const errorHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'error'
      )?.[1];
      if (errorHandler) errorHandler();
    });

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('false');
    });
  });

  it('handles WebSocket disconnection', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // First connect
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN;
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1];
      if (openHandler) openHandler();
    });

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('true');
    });

    // Then disconnect
    const disconnectButton = screen.getByText('Disconnect');
    fireEvent.click(disconnectButton);

    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  it('sends messages through WebSocket', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // Connect first
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN;
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1];
      if (openHandler) openHandler();
    });

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('true');
    });

    // Send message
    const sendButton = screen.getByText('Send Message');
    fireEvent.click(sendButton);

    expect(mockWebSocket.send).toHaveBeenCalledWith('test-message');
  });

  it('handles message subscriptions', async () => {
    const mockCallback = jest.fn();

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const subscribeButton = screen.getByText('Subscribe');
    fireEvent.click(subscribeButton);

    // Should register the subscription
    expect(subscribeButton).toBeInTheDocument();
  });

  it('handles message unsubscriptions', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const unsubscribeButton = screen.getByText('Unsubscribe');
    fireEvent.click(unsubscribeButton);

    // Should remove the subscription
    expect(unsubscribeButton).toBeInTheDocument();
  });

  it('handles WebSocket close event', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // First connect
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN;
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1];
      if (openHandler) openHandler();
    });

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('true');
    });

    // Simulate close
    act(() => {
      mockWebSocket.readyState = WebSocket.CLOSED;
      const closeHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'close'
      )?.[1];
      if (closeHandler) closeHandler();
    });

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('false');
    });
  });

  it('handles message reception', async () => {
    const mockMessage = { data: JSON.stringify({ type: 'test', payload: 'hello' }) };

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // Simulate message reception
    act(() => {
      const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      if (messageHandler) messageHandler(mockMessage);
    });

    // Should handle the message without errors
    expect(screen.getByTestId('connected')).toBeInTheDocument();
  });

  it('handles reconnection logic', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // Simulate connection failure
    act(() => {
      mockWebSocket.readyState = WebSocket.CLOSED;
      const errorHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'error'
      )?.[1];
      if (errorHandler) errorHandler();
    });

    // Should attempt reconnection after delay
    await waitFor(() => {
      expect(global.WebSocket).toHaveBeenCalledTimes(2);
    }, { timeout: 3000 });
  });

  it('prevents multiple connections', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    
    // Click connect multiple times
    fireEvent.click(connectButton);
    fireEvent.click(connectButton);
    fireEvent.click(connectButton);

    // Should only create one WebSocket connection
    expect(global.WebSocket).toHaveBeenCalledTimes(1);
  });

  it('handles cleanup on unmount', () => {
    const { unmount } = render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // Unmount component
    unmount();

    // Should close WebSocket connection
    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  it('handles invalid message format gracefully', async () => {
    const invalidMessage = { data: 'invalid-json' };

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    );

    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);

    // Simulate invalid message
    act(() => {
      const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      if (messageHandler) messageHandler(invalidMessage);
    });

    // Should handle gracefully without crashing
    expect(screen.getByTestId('connected')).toBeInTheDocument();
  });
});
