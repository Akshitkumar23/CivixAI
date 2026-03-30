'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BrainCircuit, Sparkles, FileStack, ArrowRight, Zap, Target } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';
import { Badge } from '@/components/ui/badge';

const highlightedFeatures = [
  {
    icon: <BrainCircuit className="h-10 w-10 text-blue-400" />,
    title: 'Smart AI Matcher',
    description: 'Our engine cross-references 100+ variables with 400+ schemes to find your perfect benefit match instantly.',
    stat: '98% Accuracy'
  },
  {
    icon: <Sparkles className="h-10 w-10 text-emerald-400" />,
    title: 'Instant Clarity',
    description: 'No more legal jargon. We break down complex scheme rules into simple, actionable steps you can actually understand.',
    stat: 'Human-Readable'
  },
  {
    icon: <FileStack className="h-10 w-10 text-indigo-400" />,
    title: 'Smart Checklists',
    description: 'Get a precise list of required documents fetched directly from official government guidelines for each scheme.',
    stat: 'Zero Friction'
  },
];

export function FeaturesHighlightSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-20 space-y-6">
            <Badge variant="outline" className="px-6 py-1.5 border-blue-500/30 bg-blue-500/10 text-blue-400 rounded-full font-black tracking-[0.2em] uppercase text-[11px] animate-bounce-slow">
                Digital Public Infrastructure
            </Badge>
            <h2 className="text-5xl sm:text-6xl font-black text-white tracking-tight leading-[1.1]">
              Everything You Need, <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-teal-400 italic">Redefined.</span>
            </h2>
            <p className="text-xl text-slate-400 font-medium max-w-2xl mx-auto mt-6">
              CivixAI simplifies the chaos of government bureaucracy into a fast, clear, and high-performance digital journey.
            </p>
          </div>
        </ScrollWrapper>

        <div className="grid gap-10 md:grid-cols-3">
          {highlightedFeatures.map((feature, index) => (
            <ScrollWrapper key={index} delay={index * 0.1}>
              <div className="group relative perspective-1000 h-full">
                <div className="absolute -inset-1 bg-gradient-to-br from-blue-500/20 to-transparent rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />

                <Card className="relative bg-[#050510]/60 border border-white/10 shadow-2xl rounded-[2.5rem] p-8 transition-all duration-700 h-full group-hover:-translate-y-2 group-hover:bg-white/[0.04] group-hover:border-white/20 group-hover:rotate-x-2">
                  <div className="absolute top-6 right-8">
                     <Badge className="bg-white/5 border-white/10 text-slate-500 text-[10px] uppercase font-black tracking-widest px-3 py-1 group-hover:text-blue-400 group-hover:border-blue-500/30 transition-all">
                        {feature.stat}
                     </Badge>
                  </div>
                  
                  <CardHeader className="pt-4 p-0 mb-8 text-left">
                    <div className="bg-white/5 border border-white/10 rounded-2xl h-20 w-20 flex items-center justify-center mb-10 shadow-inner group-hover:scale-110 group-hover:bg-blue-500/10 group-hover:border-blue-500/20 transition-all duration-700">
                      {feature.icon}
                    </div>
                    <CardTitle className="text-2xl font-black text-white tracking-tight uppercase group-hover:text-blue-400 transition-colors">
                        {feature.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <p className="text-slate-400 text-base leading-relaxed group-hover:text-slate-200 transition-colors">
                        {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </div>
            </ScrollWrapper>
          ))}
        </div>

        <div className="mt-24 text-center">
          <div className="inline-block relative group">
            <div className="absolute -inset-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full blur-xl opacity-30 group-hover:opacity-100 transition-all duration-700 animate-pulse"></div>
            <Button asChild className="relative h-16 px-12 text-lg bg-white text-black hover:bg-slate-200 shadow-2xl rounded-full transition-all duration-500 font-black hover:scale-[1.05] flex items-center gap-4 group">
              <Link href="/features">
                Explore The Engine
                <div className="bg-black/10 rounded-full p-2 group-hover:translate-x-2 transition-transform">
                    <ArrowRight className="h-5 w-5 text-black" />
                </div>
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
