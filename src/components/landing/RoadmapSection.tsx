'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Bot, Fingerprint, LayoutGrid, BarChart3, Sparkles, Navigation, ShieldPlus, Cpu } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';
import { Badge } from '@/components/ui/badge';

const roadmapItems = [
  { icon: <Fingerprint className="w-7 h-7 text-indigo-400" />, title: 'Aadhaar & DigiLocker', status: 'In Dev', desc: 'Auto-fill application forms using verified identity data.' },
  { icon: <Bot className="w-7 h-7 text-blue-400" />, title: 'Voice AI Navigator', status: 'Q3 2026', desc: 'Support for multiple regional dialects via vocal interface.' },
  { icon: <LayoutGrid className="w-7 h-7 text-emerald-400" />, title: 'Institutional Dashboards', status: 'Planning', desc: 'Tools for NGOs & local offices to manage bulk applications.' },
  { icon: <BarChart3 className="w-7 h-7 text-sky-400" />, title: 'Policy Insights Beta', status: 'Q4 2026', desc: 'Advanced analytics for government outcome tracking.' },
];

export function RoadmapSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
        {/* Futuristic circuit line decoration */}
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-500/10 to-transparent" />
        
      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-20 space-y-4">
             <Badge variant="outline" className="px-5 py-1.5 border-blue-500/30 bg-blue-500/10 text-blue-400 rounded-full font-black tracking-[0.2em] uppercase text-[11px]">
               Vision 2026
            </Badge>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.1]">
              Future-Safe: Our <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500 italic">Roadmap.</span>
            </h2>
            <p className="text-xl text-slate-400 font-medium max-w-2xl mx-auto mt-6 leading-relaxed">
              We are continuously evolving to build the most intelligent, integrated, and accessible civic-tech engine in India.
            </p>
          </div>
        </ScrollWrapper>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {roadmapItems.map((item, i) => (
            <ScrollWrapper key={i} delay={i * 0.1}>
              <div className="group relative h-full perspective-1000">
                <div className="absolute -inset-[1px] bg-gradient-to-tr from-blue-500/20 to-transparent rounded-[2rem] opacity-0 group-hover:opacity-100 transition-all duration-700 pointer-events-none" />
                
                <Card className="relative bg-[#050510]/80 border border-white/10 rounded-[2rem] p-8 h-full shadow-2xl backdrop-blur-xl transition-all duration-700 group-hover:bg-white/[0.06] group-hover:border-blue-500/30 group-hover:rotate-x-[-2deg] flex flex-col justify-between">
                  <div className="space-y-6">
                    <div className="h-16 w-16 rounded-[1.5rem] bg-white/5 border border-white/5 flex items-center justify-center group-hover:scale-110 group-hover:bg-blue-500/10 group-hover:border-blue-500/20 transition-all duration-700 shadow-lg">
                      <div className="relative">
                        {item.icon}
                        <Sparkles className="absolute -top-1 -right-1 w-3 h-3 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                    <div className="space-y-3">
                       <h3 className="text-lg font-black text-white tracking-tight leading-snug uppercase group-hover:text-blue-400 transition-colors">
                          {item.title}
                       </h3>
                       <p className="text-sm text-slate-400 leading-relaxed group-hover:text-slate-300">
                          {item.desc}
                       </p>
                    </div>
                  </div>
                  
                  <div className="mt-8 flex items-center justify-between">
                      <Badge variant="outline" className="text-[10px] border-white/10 text-slate-500 uppercase tracking-widest font-black group-hover:text-blue-400 group-hover:border-blue-500/20 transition-all">
                        {item.status}
                      </Badge>
                      <Cpu className="w-5 h-5 text-slate-700 group-hover:text-blue-500/40 group-hover:animate-pulse" />
                  </div>
                </Card>
              </div>
            </ScrollWrapper>
          ))}
        </div>
        
        {/* Bottom CTA within Roadmap */}
        <ScrollWrapper delay={0.4}>
            <div className="mt-20 text-center">
                <p className="text-xs font-black text-slate-500 tracking-[0.3em] uppercase mb-4 flex items-center justify-center gap-3">
                   <Navigation className="w-3 h-3 text-blue-500" />
                   Building the Digital Public Infrastructure
                </p>
            </div>
        </ScrollWrapper>
      </div>
    </section>
  );
}
