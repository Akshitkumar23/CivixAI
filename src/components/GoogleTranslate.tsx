'use client';

import Script from 'next/script';
import { useEffect, useState } from 'react';
import { Globe } from 'lucide-react';

export function GoogleTranslate() {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        // @ts-ignore
        window.googleTranslateElementInit = () => {
            // @ts-ignore
            new window.google.translate.TranslateElement(
                {
                    pageLanguage: 'en',
                    includedLanguages: 'en,hi,bn,te,mr,ta,gu,kn,ml,pa',
                },
                'google_translate_element'
            );
        };
    }, []);

    if (!mounted) {
        return (
            <div className="relative w-10 h-10 flex items-center justify-center animate-pulse bg-secondary/50 rounded-full ml-auto md:ml-6 flex-shrink-0">
                <Globe className="w-5 h-5 text-muted-foreground" />
            </div>
        );
    }

    return (
        <>
            <Script
                src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"
                strategy="afterInteractive"
            />
            <div className="relative w-10 h-10 hover:bg-secondary/80 bg-secondary flex items-center justify-center rounded-full ml-auto md:ml-6 flex-shrink-0 transition-colors cursor-pointer group">
                <Globe className="w-5 h-5 text-primary group-hover:scale-110 transition-transform" />
                <div
                    id="google_translate_element"
                    className="absolute inset-0 opacity-0 z-10 w-full h-full cursor-pointer overflow-hidden flex items-center justify-center"
                />
            </div>
        </>
    );
}
