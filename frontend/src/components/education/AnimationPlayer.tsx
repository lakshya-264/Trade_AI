import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';

interface AnimationPlayerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  src?: string; // local path like /animations/lesson1.mp4
  className?: string;
}

const AnimationPlayer: React.FC<AnimationPlayerProps> = ({ isOpen, onClose, title = 'Animation', src, className }) => {
  if (!isOpen) return null;
  const isVideo = !!src && /\.(mp4|webm|ogg)$/i.test(src);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className={cn('relative w-[96vw] max-w-4xl bg-card border border-border rounded-lg shadow-xl overflow-hidden', className)}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground truncate">{title}</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-muted/50 text-muted-foreground" aria-label="Close">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        <div className="bg-black">
          {isVideo ? (
            <video key={src} src={src} controls className="w-full max-h-[70vh]" preload="metadata" />
          ) : (
            <div className="p-6 text-center text-sm text-muted-foreground">Unsupported media type. Provide an MP4/WebM from local storage.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnimationPlayer;


