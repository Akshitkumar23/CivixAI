'use client';

import { Card, CardContent } from "@/components/ui/card";
import { BrainCircuit, ShieldCheck, Sparkles, Eye, Info, Database } from "lucide-react";
import { ScrollWrapper } from "@/components/animations/ScrollWrapper";
import { Badge } from "@/components/ui/badge";

export function ExplainableAISection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
        {/* Background glow effects */}
        <div className="absolute top-1/2 left-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-[120px] -translate-y-1/2 pointer-events-none" />

      <div className="container mx-auto px-4 relative z-10">
        <div className="grid lg:grid-cols-2 gap-20 items-center">
          
          <ScrollWrapper delay={0.2}>
            <div className="flex justify-center order-2 lg:order-1 perspective-1000">
              <div className="group relative w-full max-w-lg">
                <div className="absolute -inset-6 bg-indigo-500/10 rounded-[3rem] blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none" />
                
                <Card className="relative bg-[#050510]/90 border border-white/10 shadow-2xl rounded-[3rem] backdrop-blur-2xl overflow-hidden group-hover:border-indigo-500/40 transition-all duration-700 transform group-hover:rotate-y-[-5deg]">
                  <div className="absolute top-0 right-0 p-10 opacity-[0.03]">
                    <Database className="w-48 h-48 text-indigo-500" />
                  </div>
                  
                  <CardContent className="p-10 relative z-10">
                    <div className="flex items-center gap-5 mb-10 pb-6 border-b border-white/5">
                        <div className="h-16 w-16 rounded-[1.5rem] bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.2)]">
                           <BrainCircuit className="w-8 h-8 text-indigo-400" />
                        </div>
                        <div>
                           <h3 className="text-xl font-black text-white tracking-tight leading-none uppercase">Decision Logic</h3>
                           <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mt-2">Engine: Civix-Intelligence-Match</p>
                        </div>
                    </div>
                    
                    <div className="space-y-6">
                        <div className="p-8 rounded-[2.5rem] bg-emerald-500/[0.03] border border-emerald-500/20 relative group/card transition-all hover:bg-emerald-500/10">
                            <div className="flex items-center justify-between mb-4">
                               <div className="flex items-center gap-3">
                                  <Badge className="bg-emerald-500 text-white border-none rounded-full px-3 py-0.5 text-[9px] font-black uppercase tracking-widest">Match Found</Badge>
                                  <span className="text-emerald-400 font-black tracking-tight text-sm uppercase">PM-JAY (Ayushman)</span>
                               </div>
                               <Info className="w-4 h-4 text-emerald-500/40" />
                            </div>
                            <div className="space-y-4 pt-2">
                               <div className="flex items-center gap-4 text-xs font-bold text-slate-300">
                                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                                  <span>Annual Income (₹1.5L) meets criteria ({' <'} ₹2.5L)</span>
                               </div>
                               <div className="flex items-center gap-4 text-xs font-bold text-slate-300">
                                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                                  <span>Caste/Category verification (SC) Successful</span>
                               </div>
                            </div>
                        </div>

                        <div className="p-8 rounded-[2.5rem] bg-rose-500/[0.02] border border-rose-500/10 relative group/card transition-all hover:bg-rose-500/5">
                             <div className="flex items-center justify-between mb-4">
                               <div className="flex items-center gap-3">
                                 <Badge className="bg-rose-500/50 text-white border-none rounded-full px-3 py-0.5 text-[9px] font-black uppercase tracking-widest">Mismatch</Badge>
                                 <span className="text-rose-400/60 font-black tracking-tight text-sm uppercase">Interest Subsidy</span>
                               </div>
                               <ShieldCheck className="w-4 h-4 text-rose-500/20" />
                            </div>
                            <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
                               <div className="h-1.5 w-1.5 rounded-full bg-rose-500/30" />
                               <span>Selected scheme is currently inactive in Sikkim.</span>
                            </div>
                        </div>
                    </div>

                    <div className="mt-10 p-5 rounded-[1.5rem] bg-white/[0.02] border border-white/5 text-center">
                        <p className="text-[9px] text-slate-600 font-black uppercase tracking-[0.3em]">Auditable Transparency Log #8291</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </ScrollWrapper>

          <ScrollWrapper>
            <div className="max-w-xl space-y-10 order-1 lg:order-2">
              <div className="space-y-6">
                <Badge variant="outline" className="px-5 py-1.5 border-indigo-500/30 bg-indigo-500/10 text-indigo-400 rounded-full font-black tracking-[0.2em] uppercase text-[11px]">
                   Trust & Transparency
                </Badge>
                <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.1]">
                  AI That Explains, <br/>
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-blue-400 italic">Not Just Recommends.</span>
                </h2>
                <p className="text-xl text-slate-400 font-medium leading-relaxed mt-6">
                  CivixAI dismantles the "Black Box" of government eligibility. We provide human-readable logic for every match, ensuring you know exactly why you qualify.
                </p>
              </div>
              
              <div className="grid sm:grid-cols-2 gap-6 pt-4">
                 {[
                   { icon: <ShieldCheck className="text-emerald-400" />, title: 'Zero Guesswork', desc: 'Precise policy mapping.' },
                   { icon: <Eye className="text-blue-400" />, title: 'Audit Trail', desc: 'Trace every decision.' }
                 ].map((item, i) => (
                   <div key={i} className="group p-6 rounded-[2rem] bg-white/[0.02] border border-white/5 hover:bg-indigo-500/5 hover:border-indigo-500/20 transition-all duration-500">
                      <div className="mb-4 p-3 rounded-2xl bg-white/5 border border-white/10 w-fit group-hover:scale-110 transition-transform">
                        {item.icon}
                      </div>
                      <h4 className="font-black text-white text-sm uppercase tracking-tight mb-1">{item.title}</h4>
                      <p className="text-slate-500 text-xs font-medium">{item.desc}</p>
                   </div>
                 ))}
              </div>
            </div>
          </ScrollWrapper>
        </div>
      </div>
    </section>
  );
}
