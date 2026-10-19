'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

/**
 * useScrollRestoration
 *
 * Saves the scroll position of a scrollable container (or window) before the
 * user navigates away, and restores it when they come back.
 *
 * Usage — to restore page-level scroll (window):
 *   useScrollRestoration();
 *
 * Usage — to restore scroll inside a custom container (e.g., a div with overflow-y-auto):
 *   const ref = useScrollRestoration<HTMLDivElement>();
 *   <div ref={ref} className="overflow-y-auto">…</div>
 */
export function useScrollRestoration<T extends HTMLElement = HTMLElement>() {
  const pathname = usePathname();
  const containerRef = useRef<T>(null);

  // Key is unique per route so each page remembers its own scroll
  const key = `scroll_pos:${pathname}`;

  useEffect(() => {
    const el = containerRef.current;

    // Restore saved position
    const saved = sessionStorage.getItem(key);
    if (saved !== null) {
      const pos = parseInt(saved, 10);
      if (el) {
        el.scrollTop = pos;
      } else {
        // window-level scroll
        window.scrollTo({ top: pos, behavior: 'instant' });
      }
    }

    // Save position before leaving
    const handleBeforeLeave = () => {
      const current = el ? el.scrollTop : window.scrollY;
      sessionStorage.setItem(key, String(current));
    };

    window.addEventListener('beforeunload', handleBeforeLeave);

    return () => {
      // Also save when the component unmounts (client-side navigation)
      handleBeforeLeave();
      window.removeEventListener('beforeunload', handleBeforeLeave);
    };
  }, [key]);

  return containerRef;
}
