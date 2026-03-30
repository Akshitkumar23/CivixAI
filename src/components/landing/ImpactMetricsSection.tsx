'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Clock, Target, TrendingUp, CheckCircle, ShieldCheck, Zap } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';
import { Badge } from '@/components/ui/badge';

const metrics = [
  { icon: <Clock className="w-8 h-8 text-blue-400" />, label: '90%', sub: 'Time Saved', desc: 'Faster identification of schemes.' },
  { icon: <Target className="w-8 h-8 text-emerald-400" />, label: '98%', sub: 'Match Accuracy', desc: 'Reduced application rejections.' },
  { icon: <TrendingUp className="w-8 h-8 text-amber-400" />, label: '1M+', sub: 'Impact Scope', desc: 'Broad reach across citizens.' },
  { icon: <ShieldCheck className="w-8 h-8 text-indigo-400" />, label: 'Zero', sub: 'Information Gap', desc: 'Official data, zero confusion.' },
];

export function ImpactMetricsSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-20 space-y-4">
             <Badge variant="outline" className="px-5 py-1.5 border-emerald-500/30 bg-emerald-500/10 text-emerald-400 rounded-full font-black tracking-[0.2em] uppercase text-[11px] animate-pulse">
                Delivering Excellence
             </Badge>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.1]">
              Measuring Our <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-blue-500 italic">Impact.</span>
            </h2>
            <p className="text-xl text-slate-400 font-medium max-w-2xl mx-auto mt-6 leading-relaxed">
              Our success is defined by real-world efficiency and citizens empowered by accurate, data-driven decision making.
            </p>
          </div>
        </ScrollWrapper>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {metrics.map((metric, i) => (
            <ScrollWrapper key={i} delay={i * 0.1}>
              <div className="group relative perspective-1000">
                <div className="absolute -inset-1 bg-gradient-to-b from-white/10 to-transparent rounded-[2rem] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                
                <div className="relative p-10 h-full rounded-[2rem] bg-[#050510]/60 border border-white/10 text-center transition-all duration-500 hover:bg-white/[0.04] hover:border-white/20 hover:-translate-y-2 group-hover:rotate-y-[-5deg]">
                    <div className="flex justify-center mb-8 opacity-60 group-hover:opacity-100 group-hover:scale-110 transition-all duration-500">
                        {metric.icon}
                    </div>
                    <div className="space-y-4">
                        <h3 className="text-5xl font-black text-white tracking-tight leading-none group-hover:text-emerald-400 transition-colors">
                            {metric.label}
                        </h3>
                        <p className="text-sm font-black text-slate-400 uppercase tracking-widest">{metric.sub}</p>
                        <p className="text-xs font-medium text-slate-500 leading-relaxed max-w-[150px] mx-auto opacity-0 group-hover:opacity-100 transition-opacity duration-700">
                            {metric.desc}
                        </p>
                    </div>
                    
                    <div className="absolute top-4 right-4 group-hover:animate-spin-slow">
                        <Zap className="w-4 h-4 text-emerald-500/20 group-hover:text-emerald-500/60" />
                    </div>
                </div>
              </div>
            </ScrollWrapper>
          ))}
        </div>
      </div>
    </section>
  );
}
