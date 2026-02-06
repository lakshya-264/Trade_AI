import { useState, useEffect, useRef, useCallback } from 'react';

interface UseLazyLoadOptions {
  rootMargin?: string;
  threshold?: number;
  triggerOnce?: boolean;
}

export const useLazyLoad = (options: UseLazyLoadOptions = {}) => {
  const {
    rootMargin = '50px',
    threshold = 0.1,
    triggerOnce = true
  } = options;

  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasTriggered, setHasTriggered] = useState(false);
  const elementRef = useRef<HTMLElement>(null);

  const handleIntersection = useCallback((entries: IntersectionObserverEntry[]) => {
    const [entry] = entries;
    
    if (entry.isIntersecting) {
      setIsIntersecting(true);
      if (triggerOnce) {
        setHasTriggered(true);
      }
    } else if (!triggerOnce) {
      setIsIntersecting(false);
    }
  }, [triggerOnce]);

  useEffect(() => {
    const element = elementRef.current;
    if (!element || (triggerOnce && hasTriggered)) return;

    const observer = new IntersectionObserver(handleIntersection, {
      rootMargin,
      threshold
    });

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [handleIntersection, rootMargin, threshold, triggerOnce, hasTriggered]);

  return {
    elementRef,
    isIntersecting: triggerOnce ? hasTriggered : isIntersecting
  };
};

export default useLazyLoad;
