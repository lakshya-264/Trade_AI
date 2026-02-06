import React from 'react';

interface ArpitLessonViewerProps {
  lessonId: string;
  onClose: () => void;
}

const ArpitLessonViewer: React.FC<ArpitLessonViewerProps> = ({ lessonId, onClose }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Lesson Viewer</h2>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 transition-colors"
        >
          ✕
        </button>
      </div>
      <div className="space-y-4">
        <div className="p-4 bg-green-50 rounded-lg">
          <h3 className="font-medium text-green-900">Lesson ID: {lessonId}</h3>
          <p className="text-sm text-green-700 mt-1">Lesson content will be displayed here.</p>
        </div>
      </div>
    </div>
  );
};

export default ArpitLessonViewer;
