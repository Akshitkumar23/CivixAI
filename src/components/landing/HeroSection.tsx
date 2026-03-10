'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { ArrowRight, PlayCircle } from 'lucide-react';
import Magnetic from '../Magnetic';
import { CoreAIHeroBackground } from '@/components/canvas/CoreAIHeroBackground';

export function HeroSection() {
    const heroImage = {
        "id": "landing-hero",
        "description": "An AI bot assisting a family with civic services in front of government buildings.",
        "imageUrl": "/images/hero-image.png",
        "imageHint": "empowered individual rural technology"
    };

    return (
        <section className="relative py-12 sm:py-24 overflow-hidden min-h-[90vh] flex items-center bg-transparent">
            {/* Dark Mode Ambient Glow Fallback */}
            <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent opacity-50 pointer-events-none" />

            <div className="container mx-auto px-4 relative z-10">
                <div className="grid lg:grid-cols-2 gap-12 items-center">

                    <div className="text-center lg:text-left space-y-8">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-blue-300 text-sm font-medium mb-4 backdrop-blur-md">
                            <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                            AI Engine
                        </div>

                        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-white tracking-tight leading-tight drop-shadow-2xl">
                            CivixAI – Smart Government Benefits, <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Powered by AI</span>
                        </h1>
                        <p className="max-w-2xl mx-auto lg:mx-0 text-lg sm:text-xl text-slate-300 font-medium leading-relaxed drop-shadow-md">
                            Discover government schemes, loans, insurance, and welfare benefits you are eligible for — with clarity and confidence.
                        </p>
                        <div className="pt-4 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                            <Magnetic>
                                <Button className="h-14 px-8 text-lg bg-white text-black hover:bg-slate-200 shadow-[0_0_20px_rgba(255,255,255,0.3)] transition-all font-bold rounded-2xl" asChild>
                                    <Link href="/check-eligibility">
                                        Check My Eligibility
                                        <ArrowRight className="ml-2 w-5 h-5" />
                                    </Link>
                                </Button>
                            </Magnetic>
                            <Magnetic>
                                <Button className="h-14 px-8 text-lg bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white backdrop-blur-md rounded-2xl" variant="outline" asChild>
                                    <Link href="/features">
                                        <PlayCircle className="mr-2 w-5 h-5 text-blue-400" />
                                        Explore Benefits
                                    </Link>
                                </Button>
                            </Magnetic>
                        </div>
                    </div>

                    <div className="relative flex justify-center w-full mt-8 lg:mt-0 perspective-1000">
                        {heroImage && (
                            <div className="relative group perspective-1000 transform transition-all duration-700 hover:scale-[1.02] hover:rotate-y-2 z-10 w-full max-w-lg">
                                {/* Intense Floating Glow behind image */}
                                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-[2rem] blur-2xl opacity-30 group-hover:opacity-50 transition duration-700 pointer-events-none" />

                                <div className="relative p-2 rounded-[2rem] bg-white/5 backdrop-blur-2xl border border-white/20 shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] overflow-hidden">
                                    <Image
                                        src={heroImage.imageUrl}
                                        alt={heroImage.description}
                                        width={800}
                                        height={600}
                                        className="rounded-[1.5rem] object-cover w-full h-auto brightness-90 group-hover:brightness-110 transition-all duration-700"
                                        data-ai-hint={heroImage.imageHint}
                                        unoptimized
                                        priority
                                    />
                                    {/* Glass reflection overlay */}
                                    <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/5 to-white/20 pointer-events-none rounded-[1.5rem]" />
                                </div >
                            </div >
                        )
                        }
                    </div >
                </div >
            </div >
        </section >
    );
}
