import React, { useState, useEffect } from 'react';
import { 
  BookOpenIcon, 
  ChartBarIcon, 
  TrophyIcon,
  PlayIcon,
  CheckCircleIcon,
  ClockIcon,
  AcademicCapIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';
import { api } from '../../services/api';

interface LearningPath {
  level: string;
  path: {
    name: string;
    duration: string;
    modules: Array<{
      id: string;
      title: string;
      lessons: string[];
    }>;
  };
  progress: {
    completed_modules: number;
    total_modules: number;
    completed_lessons: number;
    total_lessons: number;
    progress_percentage: number;
  };
}

interface LearningDashboardProps {
  className?: string;
}

const LearningDashboard: React.FC<LearningDashboardProps> = ({ className = '' }) => {
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);
  const [currentLevel, setCurrentLevel] = useState('beginner');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLearningPath();
  }, [currentLevel]);

  const fetchLearningPath = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.getLearningPaths(currentLevel);
      
      if (response.success) {
        setLearningPath(response.data);
      } else {
        setError('Failed to load learning path');
      }
    } catch (err) {
      console.error('Error fetching learning path:', err);
      setError('Error loading learning content');
    } finally {
      setLoading(false);
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    if (percentage >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-center text-red-600">
          <p>{error}</p>
          <button 
            onClick={fetchLearningPath}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!learningPath) {
    return null;
  }

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <AcademicCapIcon className="h-8 w-8 text-blue-600 mr-3" />
              Learning Dashboard
            </h2>
            <p className="text-gray-600 mt-1">Master stock market trading step by step</p>
          </div>
          
          {/* Level Selector */}
          <div className="flex space-x-2">
            {['beginner', 'intermediate', 'advanced'].map((level) => (
              <button
                key={level}
                onClick={() => setCurrentLevel(level)}
                className={`px-4 py-2 rounded-lg font-medium capitalize transition-colors ${
                  currentLevel === level
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Overall Progress */}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-900">Overall Progress</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLevelColor(currentLevel)}`}>
                {currentLevel}
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex-1">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Progress</span>
                  <span>{learningPath.progress.progress_percentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(learningPath.progress.progress_percentage)}`}
                    style={{ width: `${learningPath.progress.progress_percentage}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Modules Completed */}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-center mb-2">
              <BookOpenIcon className="h-5 w-5 text-green-600 mr-2" />
              <h3 className="font-semibold text-gray-900">Modules</h3>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {learningPath.progress.completed_modules}/{learningPath.progress.total_modules}
            </div>
            <p className="text-sm text-gray-600">Completed</p>
          </div>

          {/* Lessons Completed */}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-center mb-2">
              <CheckCircleIcon className="h-5 w-5 text-blue-600 mr-2" />
              <h3 className="font-semibold text-gray-900">Lessons</h3>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {learningPath.progress.completed_lessons}/{learningPath.progress.total_lessons}
            </div>
            <p className="text-sm text-gray-600">Completed</p>
          </div>
        </div>
      </div>

      {/* Learning Path Content */}
      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-gray-900 mb-2">{learningPath.path.name}</h3>
          <div className="flex items-center text-gray-600">
            <ClockIcon className="h-4 w-4 mr-2" />
            <span>Duration: {learningPath.path.duration}</span>
          </div>
        </div>

        {/* Modules */}
        <div className="space-y-6">
          {learningPath.path.modules.map((module, moduleIndex) => (
            <div key={module.id} className="border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-blue-600 font-bold">{moduleIndex + 1}</span>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900">{module.title}</h4>
                </div>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center">
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Start Module
                </button>
              </div>

              {/* Lessons */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {module.lessons.map((lesson, lessonIndex) => (
                  <div key={lessonIndex} className="flex items-center p-3 bg-gray-50 rounded-lg">
                    <div className="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center mr-3">
                      <span className="text-xs text-gray-600">{lessonIndex + 1}</span>
                    </div>
                    <span className="text-gray-700">{lesson}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-6 bg-gray-50 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow text-left">
            <LightBulbIcon className="h-6 w-6 text-yellow-600 mb-2" />
            <h4 className="font-medium text-gray-900">Trading Tips</h4>
            <p className="text-sm text-gray-600">Essential trading strategies</p>
          </button>
          
          <button className="p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow text-left">
            <ChartBarIcon className="h-6 w-6 text-green-600 mb-2" />
            <h4 className="font-medium text-gray-900">Technical Analysis</h4>
            <p className="text-sm text-gray-600">Learn chart patterns</p>
          </button>
          
          <button className="p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow text-left">
            <TrophyIcon className="h-6 w-6 text-purple-600 mb-2" />
            <h4 className="font-medium text-gray-900">Take Quiz</h4>
            <p className="text-sm text-gray-600">Test your knowledge</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default LearningDashboard;
