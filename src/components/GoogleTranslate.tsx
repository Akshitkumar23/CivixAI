'use client';

import Script from 'next/script';
import { useEffect, useState } from 'react';
import { Languages } from 'lucide-react';

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
            <div className="relative w-10 h-10 flex items-center justify-center animate-pulse bg-white/5 rounded-xl ml-auto md:ml-6 flex-shrink-0 border border-white/10">
                <Languages className="w-5 h-5 text-slate-500" />
            </div>
        );
    }

    return (
        <>
            <Script
                src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"
                strategy="afterInteractive"
            />
            <div className="relative w-10 h-10 hover:bg-white/10 bg-white/5 border border-white/10 flex items-center justify-center rounded-xl ml-auto md:ml-4 flex-shrink-0 transition-all cursor-pointer group shadow-lg hover:border-blue-500/30">
                <Languages className="w-5 h-5 text-blue-400 group-hover:scale-110 transition-transform drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                <div
                    id="google_translate_element"
                    className="absolute inset-0 opacity-0 z-10 w-full h-full cursor-pointer overflow-hidden flex items-center justify-center scale-[2.5]"
                />
            </div>
        </>
    );
}
