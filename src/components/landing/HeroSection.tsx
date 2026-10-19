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

                    <div className="text-center lg:text-left space-y-6">
                        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-semibold backdrop-blur-md">
                            <span className="flex h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
                            Official Welfare Intelligence • No Login Required
                        </div>

                        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-tight drop-shadow-2xl">
                            Find Government Schemes <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400">You May Qualify For</span>
                        </h1>
                        <p className="max-w-2xl mx-auto lg:mx-0 text-base sm:text-lg text-slate-300 font-medium leading-relaxed drop-shadow-md">
                            Answer a few questions. CivixAI checks your information against verified official scheme rules to find your eligible benefits.
                        </p>

                        {/* Micro-trust indicators */}
                        <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3 text-xs text-slate-400 font-medium pt-1">
                            <span className="flex items-center gap-1">✓ No account or OTP required</span>
                            <span className="text-slate-600">•</span>
                            <span className="flex items-center gap-1">✓ Official government guidelines</span>
                            <span className="text-slate-600">•</span>
                            <span className="flex items-center gap-1">✓ 100% Private</span>
                        </div>

                        <div className="pt-2 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                            <Magnetic>
                                <Button className="h-14 px-8 text-base sm:text-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-[0_0_25px_rgba(59,130,246,0.4)] transition-all font-bold rounded-2xl" asChild>
                                    <Link href="/check-eligibility">
                                        Check Eligibility
                                        <ArrowRight className="ml-2 w-5 h-5" />
                                    </Link>
                                </Button>
                            </Magnetic>
                            <Magnetic>
                                <Button className="h-14 px-8 text-base sm:text-lg bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white backdrop-blur-md rounded-2xl" variant="outline" asChild>
                                    <Link href="/features">
                                        <PlayCircle className="mr-2 w-5 h-5 text-blue-400" />
                                        Explore Schemes
                                    </Link>
                                </Button>
                            </Magnetic>
                        </div>

                        {/* Need-based quick entry cards */}
                        <div className="pt-6 border-t border-white/10 space-y-3">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block text-center lg:text-left">
                                What are you looking for?
                            </span>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                                <Link href="/check-eligibility?goal=STUDENT_HIGHER_EDUCATION" className="p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-left transition-all group">
                                    <span className="text-base block mb-1">🎓</span>
                                    <span className="text-xs font-bold text-white group-hover:text-blue-300 block">I am studying</span>
                                    <span className="text-[10px] text-slate-400 block">Scholarships & education</span>
                                </Link>
                                <Link href="/check-eligibility?goal=START_OR_EXPAND_BUSINESS" className="p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-left transition-all group">
                                    <span className="text-base block mb-1">💼</span>
                                    <span className="text-xs font-bold text-white group-hover:text-blue-300 block">I need business funding</span>
                                    <span className="text-[10px] text-slate-400 block">MSME, Mudra & guarantees</span>
                                </Link>
                                <Link href="/check-eligibility?goal=FARMING_AND_AGRICULTURE" className="p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-left transition-all group">
                                    <span className="text-base block mb-1">🌾</span>
                                    <span className="text-xs font-bold text-white group-hover:text-blue-300 block">I work in agriculture</span>
                                    <span className="text-[10px] text-slate-400 block">PM-Kisan, KCC & credit</span>
                                </Link>
                                <Link href="/check-eligibility?goal=FAMILY_HEALTH_AND_HOUSING" className="p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-left transition-all group">
                                    <span className="text-base block mb-1">🏠</span>
                                    <span className="text-xs font-bold text-white group-hover:text-blue-300 block">I need housing support</span>
                                    <span className="text-[10px] text-slate-400 block">PMAY subsidy & homes</span>
                                </Link>
                                <Link href="/check-eligibility?goal=UNORGANIZED_WORKER_SAFETY_NET" className="p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-left transition-all group">
                                    <span className="text-base block mb-1">🛡️</span>
                                    <span className="text-xs font-bold text-white group-hover:text-blue-300 block">Worker safety net</span>
                                    <span className="text-[10px] text-slate-400 block">Pensions & insurance cover</span>
                                </Link>
                                <Link href="/features" className="p-3 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 text-left transition-all group">
                                    <span className="text-base block mb-1">✨</span>
                                    <span className="text-xs font-bold text-blue-300 group-hover:text-white block">Explore all support</span>
                                    <span className="text-[10px] text-slate-400 block">Browse 135 programmes</span>
                                </Link>
                            </div>
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
