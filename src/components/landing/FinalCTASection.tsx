'use client';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight, Sparkles, Star } from 'lucide-react';
import { Badge } from '../ui/badge';

export function FinalCTASection() {
  return (
    <section className="relative py-32 bg-transparent overflow-hidden border-t border-white/10">
      <div className="container mx-auto px-4 relative z-10 text-center">
        <div className="max-w-4xl mx-auto space-y-12">

          <div className="flex flex-col items-center gap-4">
            <Badge variant="outline" className="px-6 py-2 border-blue-500/30 bg-blue-500/10 text-blue-400 rounded-full font-black tracking-[0.2em] uppercase text-[12px] animate-bounce">
              Start for free
            </Badge>

          </div>

          <h2 className="text-5xl sm:text-6xl md:text-7xl font-black text-white leading-[1.1] tracking-tight drop-shadow-2xl">
            Claim what's <span className="italic">rightfully</span> yours. <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400">
              CivixAI is your digital key.
            </span>
          </h2>

          <div className="flex flex-col items-center gap-8">
            <div className="inline-block relative group">
              <div className="absolute -inset-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-full blur-xl opacity-40 group-hover:opacity-100 transition duration-700 animate-pulse"></div>
              <Button className="relative h-20 px-16 text-2xl bg-white text-black hover:bg-slate-200 shadow-2xl transition-all duration-500 hover:scale-[1.05] hover:rotate-1 font-black rounded-full flex items-center gap-4 group" asChild>
                <Link href="/check-eligibility">
                  Check Eligibility
                  <div className="bg-black/10 rounded-full p-2 group-hover:translate-x-2 transition-transform">
                    <ArrowRight className="h-6 w-6 text-black" />
                  </div>
                </Link>
              </Button>
            </div>

            <div className="flex items-center gap-3 text-slate-500 font-bold uppercase tracking-widest text-[10px]">
              <Sparkles className="w-4 h-4 text-blue-500" />
              NO GOVERNMENT VISITS REQUIRED TO START
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
