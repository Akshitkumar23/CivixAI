'use client';

import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

if (typeof window !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);
}

interface ScrollWrapperProps {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}

export function ScrollWrapper({ children, delay = 0, className = "" }: ScrollWrapperProps) {
    const elementRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!elementRef.current) return;

        const el = elementRef.current;
        
        gsap.fromTo(el,
            {
                y: 50,
                opacity: 0,
                rotationX: 10,
                transformPerspective: 1000
            },
            {
                y: 0,
                opacity: 1,
                rotationX: 0,
                duration: 1,
                delay: delay,
                ease: 'power3.out',
                scrollTrigger: {
                    trigger: el,
                    start: 'top 85%',
                    toggleActions: 'play none none reverse',
                }
            }
        );

    }, [delay]);

    return (
        <div ref={elementRef} className={className}>
            {children}
        </div>
    );
}
