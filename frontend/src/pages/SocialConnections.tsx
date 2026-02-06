/**
 * Social Connections Page
 * Allows users to connect with other registered users
 * Similar to LinkedIn/Facebook friend connections
 */

import React, { useState, useEffect } from 'react';
import { 
  Users, UserPlus, UserCheck, UserX, Search, 
  CheckCircle, XCircle, Clock, Trash2, RefreshCw
} from 'lucide-react';
import { httpClient } from '../config/api';
import { toast } from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';

interface User {
  id: number;
  username: string;
  email: string;
  created_at?: string;
  connection_status?: string | null;
}

interface Connection {
  id: number;
  user: User;
  status: string;
  is_requester: boolean;
  created_at: string;
  updated_at: string;
}

const SocialConnections: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [filter, setFilter] = useState<'all' | 'accepted' | 'pending' | 'sent'>('all');
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    fetchConnections();
  }, [filter]);

  const fetchConnections = async () => {
    setLoading(true);
    try {
      const statusParam = filter === 'all' ? undefined : filter === 'sent' ? 'pending' : filter;
      let url = '/api/social/connections';
      if (statusParam) {
        url += `?status=${statusParam}`;
      }
      
      const response = await httpClient.get(url) as any;
      
      console.log('Connections response:', response);
      
      // Handle different response formats
      let conns: Connection[] = [];
      if (response.data) {
        if (Array.isArray(response.data)) {
          conns = response.data;
        } else if (response.data.connections) {
          conns = response.data.connections;
        }
      } else if (Array.isArray(response)) {
        conns = response;
      }
      
      // Filter sent requests if needed
      if (filter === 'sent') {
        conns = conns.filter((c: Connection) => c.is_requester && c.status === 'pending');
      }
      
      setConnections(conns);
    } catch (error: any) {
      console.error('Error fetching connections:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to load connections';
      toast.error(errorMsg);
      setConnections([]);
    } finally {
      setLoading(false);
    }
  };

  const searchUsers = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const url = `/api/social/users/search?q=${encodeURIComponent(searchQuery)}`;
      const response = await httpClient.get(url) as any;
      
      console.log('Search response:', response);
      
      // Handle different response formats
      let results: User[] = [];
      if (response.data) {
        if (Array.isArray(response.data)) {
          results = response.data;
        } else if (Array.isArray(response)) {
          results = response;
        }
      } else if (Array.isArray(response)) {
        results = response;
      }
      
      setSearchResults(results);
    } catch (error: any) {
      console.error('Error searching users:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to search users';
      toast.error(errorMsg);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const sendConnectionRequest = async (userId: number) => {
    try {
      const response = await httpClient.post('/api/social/connections/request', { user_id: userId }) as any;
      
      if (response.success !== false) {
        toast.success('Connection request sent!');
        // Update search results
        setSearchResults(prev => 
          prev.map(u => u.id === userId ? { ...u, connection_status: 'pending' } : u)
        );
        fetchConnections();
      }
    } catch (error: any) {
      console.error('Error sending connection request:', error);
      toast.error(error.response?.data?.detail || 'Failed to send connection request');
    }
  };

  const acceptConnection = async (connectionId: number) => {
    try {
      const response = await httpClient.post(`/api/social/connections/${connectionId}/accept`) as any;
      
      if (response.success !== false) {
        toast.success('Connection accepted!');
        fetchConnections();
      }
    } catch (error: any) {
      console.error('Error accepting connection:', error);
      toast.error(error.response?.data?.detail || 'Failed to accept connection');
    }
  };

  const rejectConnection = async (connectionId: number) => {
    try {
      const response = await httpClient.post(`/api/social/connections/${connectionId}/reject`) as any;
      
      if (response.success !== false) {
        toast.success('Connection request rejected');
        fetchConnections();
      }
    } catch (error: any) {
      console.error('Error rejecting connection:', error);
      toast.error(error.response?.data?.detail || 'Failed to reject connection');
    }
  };

  const removeConnection = async (connectionId: number) => {
    if (!window.confirm('Are you sure you want to remove this connection?')) {
      return;
    }

    try {
      await httpClient.delete(`/api/social/connections/${connectionId}`) as any;
      toast.success('Connection removed');
      fetchConnections();
    } catch (error: any) {
      console.error('Error removing connection:', error);
      toast.error(error.response?.data?.detail || 'Failed to remove connection');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'accepted':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-400" />;
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'accepted':
        return <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">Connected</span>;
      case 'pending':
        return <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">Pending</span>;
      case 'rejected':
        return <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">Rejected</span>;
      default:
        return null;
    }
  };

  // Debug: Log when component renders
  useEffect(() => {
    console.log('SocialConnections component mounted');
    console.log('Current user:', currentUser);
  }, []);

  return (
    <div className="min-h-screen bg-[#131722] text-white p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold flex items-center gap-3 mb-2">
            <Users className="w-8 h-8 text-blue-400" />
            Social Connections
          </h1>
          <p className="text-gray-400">
            Connect with other traders and share insights
          </p>
        </div>

        {/* Search Section */}
        <div className="bg-[#1a1d28] rounded-lg p-6 border border-gray-700 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Search className="w-5 h-5" />
            Find Users
          </h2>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by username or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchUsers()}
                className="w-full bg-[#2a2e39] border border-gray-600 rounded-lg px-10 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={searchUsers}
              disabled={searching || !searchQuery.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {searching ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Search
                </>
              )}
            </button>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2">
              {searchResults.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 bg-[#2a2e39] rounded-lg border border-gray-700"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-xl font-bold">
                      {user.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-semibold">{user.username}</div>
                      <div className="text-sm text-gray-400">{user.email}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {user.connection_status && getStatusBadge(user.connection_status)}
                    {!user.connection_status || user.connection_status === 'rejected' ? (
                      <button
                        onClick={() => sendConnectionRequest(user.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium"
                      >
                        <UserPlus className="w-4 h-4" />
                        Connect
                      </button>
                    ) : user.connection_status === 'pending' ? (
                      <span className="text-sm text-gray-400">Request sent</span>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Connections Section */}
        <div className="bg-[#1a1d28] rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Users className="w-5 h-5" />
              My Connections
            </h2>
            <div className="flex items-center gap-2">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="bg-[#2a2e39] border border-gray-600 rounded px-3 py-2 text-white text-sm"
              >
                <option value="all">All</option>
                <option value="accepted">Connected</option>
                <option value="pending">Pending Requests</option>
                <option value="sent">Sent Requests</option>
              </select>
              <button
                onClick={fetchConnections}
                disabled={loading}
                className="p-2 bg-[#2a2e39] hover:bg-[#353a47] rounded-lg disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400 mb-2" />
              <p className="text-gray-400">Loading connections...</p>
            </div>
          ) : connections.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 mx-auto text-gray-600 mb-4" />
              <p className="text-gray-400">
                {filter === 'all' 
                  ? 'No connections yet. Search for users to connect!'
                  : `No ${filter} connections found.`
                }
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {connections.map((connection) => (
                <div
                  key={connection.id}
                  className="flex items-center justify-between p-4 bg-[#2a2e39] rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-xl font-bold">
                      {connection.user.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{connection.user.username}</span>
                        {getStatusIcon(connection.status)}
                        {getStatusBadge(connection.status)}
                      </div>
                      <div className="text-sm text-gray-400">{connection.user.email}</div>
                      {connection.is_requester && connection.status === 'pending' && (
                        <div className="text-xs text-yellow-400 mt-1">You sent this request</div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {connection.status === 'pending' && !connection.is_requester && (
                      <>
                        <button
                          onClick={() => acceptConnection(connection.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-medium"
                        >
                          <UserCheck className="w-4 h-4" />
                          Accept
                        </button>
                        <button
                          onClick={() => rejectConnection(connection.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium"
                        >
                          <UserX className="w-4 h-4" />
                          Reject
                        </button>
                      </>
                    )}
                    {connection.status === 'accepted' && (
                      <button
                        onClick={() => removeConnection(connection.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium"
                        title="Remove connection"
                      >
                        <Trash2 className="w-4 h-4" />
                        Remove
                      </button>
                    )}
                    {connection.status === 'pending' && connection.is_requester && (
                      <span className="text-sm text-gray-400">Waiting for response...</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SocialConnections;

