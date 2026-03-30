'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Smartphone, WifiOff, Users, Languages, MapPin, Zap } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';
import { Badge } from '@/components/ui/badge';

const features = [
  {
    icon: <Languages className="h-7 w-7 text-sky-400" />,
    title: 'Regional Support',
    description: 'CivixAI speaks your language. Content is automatically translated to ensure no rural citizen is left behind.',
    tag: 'Vernacular'
  },
  {
    icon: <WifiOff className="h-7 w-7 text-amber-400" />,
    title: 'Offline Optimized',
    description: 'Built as a high-performance PWA to work seamlessly on low-bandwidth networks in remote villages.',
    tag: 'Edge Ready'
  },
  {
    icon: <MapPin className="h-7 w-7 text-emerald-400" />,
    title: 'Village-Scale Data',
    description: 'We don\'t just map states; we map specific district and block-level schemes for extreme accuracy.',
    tag: 'Localized'
  },
];

export function AccessibilitySection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
        {/* Decorative Indian Map Pattern Background (Subtle) */}
        <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '30px 30px' }} />
        
      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-24 space-y-6">
            <div className="flex justify-center mb-4">
                <Badge variant="outline" className="px-6 py-1.5 border-orange-500/30 bg-orange-500/10 text-orange-400 rounded-full font-black tracking-[0.2em] uppercase text-[11px]">
                   Hyper-Localized Tech
                </Badge>
            </div>
            <h2 className="text-5xl sm:text-6xl font-black text-white tracking-tight leading-[1.1]">
              Built for <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-white to-emerald-400 italic">Real India.</span>
            </h2>
            <p className="text-xl text-slate-400 font-medium max-w-2xl mx-auto mt-6 leading-relaxed">
              From high-tech cities to remote villages, CivixAI is engineered to work everywhere, for everyone.
            </p>
          </div>
        </ScrollWrapper>

        <div className="grid gap-8 md:grid-cols-3">
          {features.map((feature, index) => (
            <ScrollWrapper key={index} delay={index * 0.1}>
              <div className="group relative h-full perspective-1000">
                <div className="absolute -inset-[1px] bg-gradient-to-b from-white/10 to-transparent rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                
                <Card className="relative bg-[#050510]/60 border border-white/10 rounded-[2.5rem] p-8 h-full shadow-2xl backdrop-blur-xl transition-all duration-700 group-hover:-translate-y-3 group-hover:bg-white/[0.05] group-hover:border-white/20 group-hover:rotate-x-2 flex flex-col justify-between">
                  <div>
                    <CardHeader className="p-0 mb-8">
                       <div className="flex justify-between items-start">
                          <div className="h-16 w-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 group-hover:bg-white/10 group-hover:border-blue-500/30 transition-all duration-500">
                            {feature.icon}
                          </div>
                          <Badge variant="outline" className="text-[9px] border-white/5 text-slate-600 uppercase font-black tracking-widest">{feature.tag}</Badge>
                       </div>
                    </CardHeader>
                    <CardContent className="p-0 space-y-4">
                      <CardTitle className="text-2xl font-black text-white tracking-tight uppercase group-hover:text-blue-400 transition-colors">
                        {feature.title}
                      </CardTitle>
                      <p className="text-slate-400 leading-relaxed text-base group-hover:text-slate-200 transition-colors">
                        {feature.description}
                      </p>
                    </CardContent>
                  </div>
                  
                  <div className="mt-8 pt-6 border-t border-white/5 flex items-center gap-3">
                     <Zap className="h-4 w-4 text-orange-500 opacity-40 group-hover:opacity-100 transition-opacity" />
                     <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Optimized for Tier 3 Cities</span>
                  </div>
                </Card>
              </div>
            </ScrollWrapper>
          ))}
        </div>
      </div>
    </section>
  );
}
