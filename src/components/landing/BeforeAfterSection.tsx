'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileSearch, Clock, AlertTriangle, BrainCircuit, CheckCircle, Smile } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';

export function BeforeAfterSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-4xl mx-auto mb-20 gsap-animate">
            <h2 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight drop-shadow-md">
              The Old Way vs. <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-400">The Simple Way</span>
            </h2>
            <p className="mt-6 text-xl text-slate-300 font-medium drop-shadow-sm">
              Stop struggling with confusing information and start getting clear answers instantly.
            </p>
          </div>
        </ScrollWrapper>

        <div className="mt-16 grid lg:grid-cols-2 gap-12 relative">
          {/* Central VS Badge */}
          <div className="hidden lg:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-20 w-16 h-16 rounded-full bg-[#050510] border border-white/20 items-center justify-center shadow-2xl backdrop-blur-xl">
             <span className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-slate-500">VS</span>
          </div>

          {/* Before Card */}
          <ScrollWrapper>
            <div className="group relative h-full transform transition-all duration-700 hover:-translate-y-2 hover:rotate-y-[-2deg] gsap-animate">
              <div className="absolute -inset-[1px] bg-gradient-to-br from-rose-500/20 to-transparent rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <Card className="relative bg-white/[0.02] border border-white/10 rounded-[2.5rem] p-8 sm:p-10 h-full shadow-2xl backdrop-blur-sm transition-all group-hover:bg-rose-500/[0.02] group-hover:border-rose-500/20">
                <CardHeader className="px-0 pt-0 mb-8 pb-6 border-b border-white/5">
                  <div className="flex items-center gap-4 mb-2">
                    <Badge variant="outline" className="bg-rose-500/10 text-rose-400 border-rose-500/20 rounded-full px-4 py-1 text-[10px] font-bold uppercase tracking-widest">Conventional Path</Badge>
                  </div>
                  <CardTitle className="text-3xl font-black text-white tracking-tight">The Usual Struggle</CardTitle>
                  <p className="text-slate-400 font-medium mt-2">Manual searching and frustration</p>
                </CardHeader>

                <CardContent className="space-y-10 px-0">
                  {[
                    { icon: <FileSearch />, text: 'Jumping between dozens of complicated government websites and local offices just to find basic details.' },
                    { icon: <AlertTriangle />, text: 'Very confusing rules and difficult application steps that easily result in mistakes or rejections.' },
                    { icon: <Clock />, text: 'Wasting hours or days trying to understand what to do, without even knowing if you qualify.' }
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-start gap-6 group/item">
                      <div className="p-4 rounded-2xl bg-white/5 border border-white/10 text-slate-500 transition-colors group-hover/item:text-rose-400 group-hover/item:border-rose-500/20 flex-shrink-0">
                        {item.icon}
                      </div>
                      <p className="text-slate-400 text-lg leading-relaxed group-hover/item:text-slate-300 transition-colors">{item.text}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </ScrollWrapper>

          {/* After Card */}
          <ScrollWrapper>
            <div className="group relative h-full transform transition-all duration-700 hover:-translate-y-2 hover:rotate-y-[2deg] z-10 gsap-animate">
              <div className="absolute -inset-[1px] bg-gradient-to-br from-blue-500/40 to-indigo-500/40 rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <Card className="relative bg-[#050510]/40 border border-blue-500/30 rounded-[2.5rem] p-8 sm:p-10 h-full shadow-[0_0_50px_rgba(59,130,246,0.1)] backdrop-blur-xl transition-all group-hover:bg-blue-500/[0.05] group-hover:border-blue-500/50">
                <CardHeader className="px-0 pt-0 mb-8 pb-6 border-b border-blue-500/20">
                  <div className="flex items-center gap-4 mb-2">
                    <Badge variant="outline" className="bg-blue-500/20 text-blue-400 border-blue-400/30 rounded-full px-4 py-1 text-[10px] font-bold uppercase tracking-widest animate-pulse">AI-Powered Path</Badge>
                  </div>
                  <CardTitle className="text-3xl font-black text-white tracking-tight">With CivixAI</CardTitle>
                  <p className="text-blue-300/80 font-medium mt-2">Crystal clear answers in minutes</p>
                </CardHeader>

                <CardContent className="space-y-10 px-0">
                  {[
                    { icon: <BrainCircuit />, text: 'Answer a few basic questions and let our smart AI instantly handle all the heavy lifting.' },
                    { icon: <CheckCircle />, text: 'Get a direct, prioritized list of government programs and loans that are actually made for you.' },
                    { icon: <Smile />, text: 'Feel totally confident with your own ready-to-use checklist and easy-to-read instructions.' }
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-start gap-6 group/item">
                      <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400/60 transition-all group-hover/item:text-blue-400 group-hover/item:border-blue-500/40 group-hover/item:scale-110 flex-shrink-0 shadow-lg">
                        {item.icon}
                      </div>
                      <p className="text-slate-200 text-lg font-semibold leading-relaxed">{item.text}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </ScrollWrapper>
        </div>
      </div>
    </section>
  );
}
