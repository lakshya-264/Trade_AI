import React from 'react';

interface ComprehensiveEducationProps {
  onLessonSelect: (lessonId: string) => void;
  onShowTools: () => void;
}

const ComprehensiveEducation: React.FC<ComprehensiveEducationProps> = ({ onLessonSelect, onShowTools }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Comprehensive Education</h2>
      <div className="space-y-4">
        <div className="p-4 bg-indigo-50 rounded-lg">
          <h3 className="font-medium text-indigo-900">Complete Trading Course</h3>
          <p className="text-sm text-indigo-700 mt-1">Comprehensive educational content will be available here.</p>
          <div className="mt-3 space-x-2">
            <button
              onClick={() => onLessonSelect('lesson-1')}
              className="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition-colors"
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

export default ComprehensiveEducation;
