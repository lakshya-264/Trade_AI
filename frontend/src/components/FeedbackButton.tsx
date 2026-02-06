/**
 * Feedback Button Component
 * Allows users to provide feedback on predictions/recommendations
 */

import React, { useState } from 'react';
import { HandThumbUpIcon, HandThumbDownIcon, StarIcon } from '@heroicons/react/24/outline';
import { HandThumbUpIcon as HandThumbUpIconSolid, HandThumbDownIcon as HandThumbDownIconSolid } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import { userLearningApi, FeedbackRequest } from '../services/userLearningApi';

interface FeedbackButtonProps {
  entityType: 'prediction' | 'recommendation' | 'analysis';
  entityId: string;
  symbol?: string;
  className?: string;
  showRating?: boolean;
  onFeedbackSubmitted?: () => void;
}

const FeedbackButton: React.FC<FeedbackButtonProps> = ({
  entityType,
  entityId,
  symbol,
  className = '',
  showRating = false,
  onFeedbackSubmitted
}) => {
  const [feedback, setFeedback] = useState<'helpful' | 'not_helpful' | null>(null);
  const [rating, setRating] = useState<number | null>(null);
  const [showRatingInput, setShowRatingInput] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleFeedback = async (feedbackType: 'helpful' | 'not_helpful') => {
    if (submitting) return;
    
    setFeedback(feedbackType);
    setSubmitting(true);

    try {
      const request: FeedbackRequest = {
        entity_type: entityType,
        entity_id: entityId,
        feedback_type: feedbackType === 'helpful' ? 'helpful' : 'not_helpful',
        symbol: symbol,
        rating: rating || undefined,
        metadata: {
          timestamp: new Date().toISOString()
        }
      };

      const response = await userLearningApi.submitFeedback(request);

      if (response.success) {
        toast.success('Thank you for your feedback!');
        if (showRating && !rating) {
          setShowRatingInput(true);
        } else {
          onFeedbackSubmitted?.();
        }
      } else {
        toast.error('Failed to submit feedback');
        setFeedback(null);
      }
    } catch (error: any) {
      console.error('Error submitting feedback:', error);
      toast.error('Failed to submit feedback');
      setFeedback(null);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRating = async (selectedRating: number) => {
    if (submitting) return;
    
    setRating(selectedRating);
    setSubmitting(true);

    try {
      const request: FeedbackRequest = {
        entity_type: entityType,
        entity_id: entityId,
        feedback_type: feedback || 'helpful',
        symbol: symbol,
        rating: selectedRating,
        metadata: {
          timestamp: new Date().toISOString()
        }
      };

      const response = await userLearningApi.submitFeedback(request);

      if (response.success) {
        toast.success('Rating submitted!');
        onFeedbackSubmitted?.();
      } else {
        toast.error('Failed to submit rating');
      }
    } catch (error: any) {
      console.error('Error submitting rating:', error);
      toast.error('Failed to submit rating');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Thumbs Up/Down */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => handleFeedback('helpful')}
          disabled={submitting}
          className={`p-1.5 rounded-md transition-colors ${
            feedback === 'helpful'
              ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
              : 'text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-gray-100 dark:hover:bg-gray-700'
          } ${submitting ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="Helpful"
        >
          {feedback === 'helpful' ? (
            <HandThumbUpIconSolid className="w-5 h-5" />
          ) : (
            <HandThumbUpIcon className="w-5 h-5" />
          )}
        </button>
        
        <button
          onClick={() => handleFeedback('not_helpful')}
          disabled={submitting}
          className={`p-1.5 rounded-md transition-colors ${
            feedback === 'not_helpful'
              ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
              : 'text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700'
          } ${submitting ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="Not Helpful"
        >
          {feedback === 'not_helpful' ? (
            <HandThumbDownIconSolid className="w-5 h-5" />
          ) : (
            <HandThumbDownIcon className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Rating Stars */}
      {showRating && (showRatingInput || feedback) && (
        <div className="flex items-center gap-1 ml-2">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => handleRating(star)}
              disabled={submitting}
              className={`transition-colors ${
                rating && rating >= star
                  ? 'text-yellow-400'
                  : 'text-gray-300 dark:text-gray-600 hover:text-yellow-400'
              } ${submitting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              title={`Rate ${star} star${star > 1 ? 's' : ''}`}
            >
              <StarIcon className="w-4 h-4" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default FeedbackButton;

