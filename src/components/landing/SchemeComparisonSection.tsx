'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GitCompareArrows, IndianRupee, FileText, CheckSquare, Clock, ArrowRight } from "lucide-react";
import { ScrollWrapper } from "@/components/animations/ScrollWrapper";
import { Badge } from "@/components/ui/badge";

const factors = [
    { icon: <IndianRupee className="w-5 h-5 text-blue-400"/>, text: "Benefit amount"},
    { icon: <CheckSquare className="w-5 h-5 text-emerald-400"/>, text: "Eligibility complexity"},
    { icon: <FileText className="w-5 h-5 text-amber-400"/>, text: "Documents required"},
    { icon: <Clock className="w-5 h-5 text-indigo-400"/>, text: "Processing time"},
]

export function SchemeComparisonSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      <div className="container mx-auto px-4 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <ScrollWrapper>
            <div className="space-y-8">
              <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20 rounded-full px-4 py-1 text-[10px] font-bold uppercase tracking-widest">Decision Matrix</Badge>
              <h2 className="text-4xl sm:text-5xl font-black text-white tracking-tight leading-tight">
                Compare. Decide. <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">Benefit More.</span>
              </h2>
              <p className="text-xl text-slate-400 font-medium leading-relaxed max-w-lg">
                CivixAI doesn't just list schemes. It helps you compare them on factors that matter, so you can make the smartest choice for your needs.
              </p>
              <div className="grid sm:grid-cols-2 gap-6 pt-4">
                  {factors.map(factor => (
                      <div key={factor.text} className="flex items-center gap-4 group">
                          <div className="p-3 rounded-xl bg-white/5 border border-white/10 group-hover:border-blue-500/30 transition-all duration-300">
                            {factor.icon}
                          </div>
                          <span className="font-bold text-slate-300 group-hover:text-white transition-colors">{factor.text}</span>
                      </div>
                  ))}
              </div>
            </div>
          </ScrollWrapper>

          <ScrollWrapper>
            <div className="group relative flex justify-center perspective-1000">
              <div className="absolute -inset-4 bg-blue-500/10 rounded-[2.5rem] blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
              
              <Card className="relative bg-[#050510]/80 border border-white/10 shadow-2xl w-full max-w-lg rounded-[2rem] overflow-hidden backdrop-blur-xl group-hover:border-blue-500/30 transition-all duration-500 transform group-hover:rotate-y-[-5deg]">
                <div className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
                
                <CardHeader className="bg-white/5 p-6 border-b border-white/5">
                    <CardTitle className="text-center text-lg font-black text-white tracking-widest uppercase flex items-center justify-center gap-3">
                      <GitCompareArrows className="w-5 h-5 text-blue-400" />
                      Comparison Widget
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-6 sm:p-8">
                  <div className="grid grid-cols-3 gap-3 text-center text-[10px] font-black uppercase tracking-widest text-slate-500 mb-4">
                      <div>FACTOR</div>
                      <div className="text-blue-400">SCHEME A</div>
                      <div className="text-emerald-400">SCHEME B</div>
                  </div>
                  
                  {[
                    { label: 'Benefit', a: '₹5L Insurance', b: '₹10K Stipend' },
                    { label: 'Docs', a: '3 Required', b: '2 Required' },
                    { label: 'Eligibility', a: 'Moderate', b: 'Direct' },
                    { label: 'Time', a: '15 Days', b: 'Instant' }
                  ].map((row, i) => (
                    <div key={i} className="grid grid-cols-3 gap-3 text-center items-center py-4 border-b border-white/5 last:border-0 group/row">
                        <div className="text-left font-bold text-slate-400 text-xs">{row.label}</div>
                        <div className="bg-white/5 p-2.5 rounded-xl text-xs text-white font-medium border border-transparent group-hover/row:border-blue-500/20">{row.a}</div>
                        <div className="bg-white/5 p-2.5 rounded-xl text-xs text-white font-medium border border-transparent group-hover/row:border-emerald-500/20">{row.b}</div>
                    </div>
                  ))}
                  
                  <div className="mt-8 pt-6 border-t border-white/5 text-center">
                    <span className="text-xs text-slate-500 font-bold tracking-widest uppercase">Intelligent Match Suggestion</span>
                    <div className="mt-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-3 rounded-2xl text-xs font-bold animate-pulse">
                      Scheme B is recommended for faster processing
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
