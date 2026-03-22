'use client';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

export function FinalCTASection() {
  return (
    <section className="relative py-32 bg-transparent overflow-hidden border-t border-white/10">
      <div className="container mx-auto px-4 relative z-10 text-center">
        <div className="max-w-4xl mx-auto">

          <h2 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white leading-tight mb-8 drop-shadow-2xl">
            Don't miss the benefits you deserve. <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Let CivixAI find them for you today.
            </span>
          </h2>

          <div className="mt-12">
            <div className="inline-block relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full blur-lg opacity-60 group-hover:opacity-100 transition duration-500 animate-pulse"></div>
              <Button className="relative h-16 px-12 text-xl bg-white text-black hover:bg-slate-200 shadow-2xl transition-transform hover:scale-105 font-bold rounded-full" asChild>
                <Link href="/check-eligibility">
                  Find My Benefits Now
                  <ArrowRight className="ml-3 h-6 w-6 text-black" />
                </Link>
              </Button>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
