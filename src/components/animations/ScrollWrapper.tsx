'use client';

import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

if (typeof window !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);
}

export function ScrollWrapper({ children }: { children: React.ReactNode }) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        const ctx = gsap.context(() => {
            // Find all elements with the class 'gsap-animate'
            const elements = gsap.utils.toArray('.gsap-animate');

            elements.forEach((el: any) => {
                gsap.fromTo(el,
                    {
                        y: 50,
                        opacity: 0,
                        rotationX: 15,
                        transformPerspective: 1000
                    },
                    {
                        y: 0,
                        opacity: 1,
                        rotationX: 0,
                        duration: 1,
                        ease: 'power3.out',
                        scrollTrigger: {
                            trigger: el,
                            start: 'top 85%',
                            toggleActions: 'play none none reverse',
                        }
                    }
                );
            });
        }, containerRef);

        return () => ctx.revert();
    }, []);

    return <div ref={containerRef}>{children}</div>;
}
