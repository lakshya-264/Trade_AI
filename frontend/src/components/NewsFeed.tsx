import React from 'react';

const NewsFeed: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">News Feed</h2>
      <div className="space-y-4">
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900">Market News</h3>
          <p className="text-sm text-gray-600 mt-1">Latest market updates and news will appear here.</p>
        </div>
      </div>
    </div>
  );
};

export default NewsFeed;
