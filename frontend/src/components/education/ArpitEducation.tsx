import React from 'react';

interface ArpitEducationProps {
  onLessonSelect: (lessonId: string) => void;
  onShowTools: () => void;
}

const ArpitEducation: React.FC<ArpitEducationProps> = ({ onLessonSelect, onShowTools }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Arpit Education</h2>
      <div className="space-y-4">
        <div className="p-4 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-blue-900">Trading Lessons</h3>
          <p className="text-sm text-blue-700 mt-1">Educational content will be available here.</p>
          <div className="mt-3 space-x-2">
            <button
              onClick={() => onLessonSelect('lesson-1')}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
            >
              Start Lesson
            </button>
            <button
              onClick={onShowTools}
              className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
            >
              Show Tools
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArpitEducation;
