import { useEffect, useRef } from 'react';
import Lenis from 'lenis';

/**
 * useSmoothScroll: Initializes Lenis smooth inertia scrolling on the document body.
 * Provides natural weighted momentum and resistance without hijacking native keyboard or accessibility.
 */
export function useSmoothScroll(enabled = true) {
  const lenisRef = useRef(null);

  useEffect(() => {
    if (!enabled) return;

    // Respect user's motion preferences
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }

    let lenisInstance;
    let animationFrameId;

    try {
      lenisInstance = new Lenis({
        duration: 0.35,
        easing: (t) => 1 - Math.pow(1 - t, 3),
        orientation: 'vertical',
        gestureOrientation: 'vertical',
        smoothWheel: true,
        wheelMultiplier: 1.0,
        touchMultiplier: 1.0,
        infinite: false,
      });

      lenisRef.current = lenisInstance;
      window.__lenis = lenisInstance;

      const raf = (time) => {
        lenisInstance.raf(time);
        animationFrameId = requestAnimationFrame(raf);
      };

      animationFrameId = requestAnimationFrame(raf);
    } catch (err) {
      console.warn('Lenis smooth scroll initialization skipped:', err);
    }

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      if (lenisInstance) {
        lenisInstance.destroy();
        lenisRef.current = null;
        delete window.__lenis;
      }
    };
  }, [enabled]);

  return lenisRef;
}

export default useSmoothScroll;
