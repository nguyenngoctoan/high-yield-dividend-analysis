'use client';

import { useState } from 'react';
import Header from '@/components/Header';

interface APIKey {
  id: string;
  name: string;
  key: string;
  created: string;
  lastUsed: string | null;
  requests: number;
}

export default function APIKeysPage() {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([
    {
      id: '1',
      name: 'Production Key',
      key: 'sk_live_""""""""""""""""1234',
      created: '2025-01-15',
      lastUsed: '2 hours ago',
      requests: 45231
    }
  ]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [showNewKey, setShowNewKey] = useState<string | null>(null);

  const handleCreateKey = () => {
    const newKey: APIKey = {
      id: Date.now().toString(),
      name: newKeyName || 'Untitled Key',
      key: `sk_live_${generateRandomKey()}`,
      created: new Date().toISOString().split('T')[0],
      lastUsed: null,
      requests: 0
    };

    setApiKeys([...apiKeys, newKey]);
    setShowNewKey(newKey.key);
    setNewKeyName('');
    setShowCreateModal(false);
  };

  const handleDeleteKey = (id: string) => {
    if (confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      setApiKeys(apiKeys.filter(key => key.id !== id));
    }
  };

  const generateRandomKey = () => {
    return Array.from({ length: 32 }, () =>
      Math.random().toString(36).charAt(2)
    ).join('');
  };

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="container mx-auto px-6 py-20">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                API Keys
              </h1>
              <p className="text-gray-600">
                Create and manage your API keys
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-all"
            >
              Create New Key
            </button>
          </div>

          {/* New Key Alert */}
          {showNewKey && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-semibold text-blue-900 mb-2">
                    Your new API key has been created
                  </p>
                  <div className="flex items-center gap-2 mb-2">
                    <code className="flex-1 px-3 py-2 bg-white border border-blue-200 rounded text-sm font-mono">
                      {showNewKey}
                    </code>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(showNewKey);
                        alert('Copied to clipboard!');
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      Copy
                    </button>
                  </div>
                  <p className="text-sm text-blue-700">
                    Make sure to copy your API key now. You won't be able to see it again!
                  </p>
                </div>
                <button
                  onClick={() => setShowNewKey(null)}
                  className="text-blue-400 hover:text-blue-600"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {/* Usage Stats */}
          <div className="grid grid-cols-3 gap-6 mb-8">
            <StatCard
              label="Total Keys"
              value={apiKeys.length.toString()}
            />
            <StatCard
              label="Total Requests"
              value={apiKeys.reduce((sum, key) => sum + key.requests, 0).toLocaleString()}
            />
            <StatCard
              label="Active Keys"
              value={apiKeys.filter(key => key.lastUsed).length.toString()}
            />
          </div>

          {/* API Keys List */}
          <div className="space-y-4">
            {apiKeys.map((apiKey) => (
              <div
                key={apiKey.id}
                className="p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-300 transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {apiKey.name}
                    </h3>
                    <code className="text-sm text-gray-600 font-mono">
                      {apiKey.key}
                    </code>
                  </div>
                  <button
                    onClick={() => handleDeleteKey(apiKey.id)}
                    className="text-red-600 hover:text-red-800 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Created</span>
                    <p className="font-medium text-gray-900">{apiKey.created}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Last Used</span>
                    <p className="font-medium text-gray-900">
                      {apiKey.lastUsed || 'Never'}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">Requests</span>
                    <p className="font-medium text-gray-900">
                      {apiKey.requests.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {apiKeys.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 mb-4">No API keys yet</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-6 py-2 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-all"
                >
                  Create Your First Key
                </button>
              </div>
            )}
          </div>

          {/* Best Practices */}
          <div className="mt-12 p-6 bg-gray-50 rounded-xl border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Best Practices
            </h2>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-gray-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Never share your API keys publicly or commit them to version control
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-gray-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Use environment variables to store your API keys in your applications
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-gray-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Create separate keys for different environments (development, staging, production)
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-gray-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Rotate your API keys regularly and delete unused keys
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Create Key Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Create New API Key
            </h2>
            <p className="text-gray-600 mb-6">
              Give your API key a name to help you identify it later.
            </p>

            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="e.g., Production Key"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-gray-900 focus:ring-1 focus:ring-gray-900 mb-6"
              autoFocus
            />

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewKeyName('');
                }}
                className="flex-1 px-6 py-3 border-2 border-gray-200 text-gray-700 rounded-lg font-medium hover:border-gray-300 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateKey}
                className="flex-1 px-6 py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-all"
              >
                Create Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-6 bg-white border border-gray-200 rounded-xl">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
