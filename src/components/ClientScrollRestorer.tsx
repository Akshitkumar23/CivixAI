'use client';
// This tiny component can be dropped inside any Server Component page
// to get scroll restoration without converting the whole page to 'use client'.
import { useScrollRestoration } from '@/hooks/use-scroll-restoration';

export function ClientScrollRestorer() {
  useScrollRestoration();
  return null; // renders nothing — purely a side-effect component
}
