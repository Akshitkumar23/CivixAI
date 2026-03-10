'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileSearch, Clock, AlertTriangle, BrainCircuit, CheckCircle, Smile } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';

export function BeforeAfterSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-4xl mx-auto mb-20 gsap-animate">
            <h2 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight drop-shadow-md">
              The Old Way vs. <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-400">The CivixAI Way</span>
            </h2>
            <p className="mt-6 text-xl text-slate-300 font-medium drop-shadow-sm">
              Stop drowning in information. Start getting clear answers.
            </p>
          </div>
        </ScrollWrapper>

        <div className="mt-16 grid lg:grid-cols-2 gap-8 lg:gap-12 perspective-1000">

          {/* Before Card */}
          <ScrollWrapper>
            <div className="group relative h-full transform transition-all duration-500 hover:-translate-y-2 gsap-animate">
              <Card className="relative bg-white/5 border border-rose-500/30 rounded-[2rem] p-8 h-full shadow-2xl backdrop-blur-md">
                <CardHeader className="px-0 pt-0 border-b border-rose-500/20 mb-8 pb-6">
                  <div className="flex items-center gap-4">
                    <div className="h-4 w-4 rounded-full bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.6)] animate-pulse" />
                    <CardTitle className="text-3xl font-bold text-white tracking-wide">Without CivixAI</CardTitle>
                  </div>
                  <p className="text-rose-400 font-medium mt-2">The Search is Endless</p>
                </CardHeader>

                <CardContent className="space-y-8 px-0">
                  <div className="flex items-start gap-5">
                    <div className="p-3 rounded-2xl bg-black/40 border border-rose-500/20 text-rose-400 flex-shrink-0">
                      <FileSearch className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-slate-300 text-lg">Jumping between countless government websites, news articles, and local offices.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-5">
                    <div className="p-3 rounded-2xl bg-black/40 border border-rose-500/20 text-rose-400 flex-shrink-0">
                      <AlertTriangle className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-slate-300 text-lg">Confusing eligibility rules and unclear application processes lead to mistakes.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-5">
                    <div className="p-3 rounded-2xl bg-black/40 border border-rose-500/20 text-rose-400 flex-shrink-0">
                      <Clock className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-slate-300 text-lg">Hours, days, even weeks wasted on research with no guarantee of finding the right benefit.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScrollWrapper>


          {/* After Card */}
          <ScrollWrapper>
            <div className="group relative h-full transform transition-all duration-500 hover:-translate-y-2 z-10 gsap-animate">
              <div className="absolute -inset-1 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-[2rem] blur-xl opacity-30 group-hover:opacity-60 transition duration-700 pointer-events-none" />

              <Card className="relative bg-white/5 border border-blue-400/40 rounded-[2rem] p-8 h-full shadow-[0_0_40px_rgba(59,130,246,0.15)] backdrop-blur-xl">
                <CardHeader className="px-0 pt-0 border-b border-blue-500/30 mb-8 pb-6">
                  <div className="flex items-center gap-4">
                    <div className="h-4 w-4 rounded-full bg-blue-400 shadow-[0_0_15px_rgba(96,165,250,0.8)]" />
                    <CardTitle className="text-3xl font-bold text-white tracking-wide">With CivixAI</CardTitle>
                  </div>
                  <p className="text-blue-300 font-medium mt-2">Clarity in Minutes</p>
                </CardHeader>

                <CardContent className="space-y-8 px-0">
                  <div className="flex items-start gap-5">
                    <div className="p-3 rounded-2xl bg-black/40 border border-blue-500/30 text-blue-400 flex-shrink-0 shadow-inner">
                      <BrainCircuit className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-slate-200 text-lg font-medium">Answer a few simple questions and let our AI do the heavy lifting for you.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-5">
                    <div className="p-3 rounded-2xl bg-black/40 border border-blue-500/30 text-blue-400 flex-shrink-0 shadow-inner">
                      <CheckCircle className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-slate-200 text-lg font-medium">Get a clear, prioritized list of schemes you are actually eligible for.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-5">
                    <div className="p-3 rounded-2xl bg-black/40 border border-blue-500/30 text-blue-400 flex-shrink-0 shadow-inner">
                      <Smile className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-slate-200 text-lg font-medium">Feel confident and empowered with personalized checklists and transparent reasons.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScrollWrapper>

        </div>
      </div>
    </section>
  );
}
