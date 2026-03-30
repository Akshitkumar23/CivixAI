'use client';

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Landmark, ShieldCheck, PiggyBank, Briefcase, Zap, ShieldAlert, Sparkles } from "lucide-react";
import { ScrollWrapper } from "@/components/animations/ScrollWrapper";
import { Badge } from "@/components/ui/badge";

const items = [
    {
        icon: <Landmark className="w-8 h-8 text-blue-400" />,
        title: "Micro-Credit & Loans",
        description: "Access collateral-free loans for street vendors (PM-SVANidhi) and MSME sectors directly from official credit portals.",
        tag: "Credit",
        color: "group-hover:border-blue-500/30"
    },
    {
        icon: <ShieldAlert className="w-8 h-8 text-emerald-400" />,
        title: "Social Security Hub",
        description: "Unified access to pension schemes (APY), health insurance (PM-JAY), and accident cover (PM-JJBY) in one place.",
        tag: "Insurance",
        color: "group-hover:border-emerald-500/30"
    },
    {
        icon: <Briefcase className="w-8 h-8 text-amber-400" />,
        title: "Startup & Skilling",
        description: "Navigate incubation support, seed funding, and world-class skilling certifications through Startup India & Skill India.",
        tag: "Career",
        color: "group-hover:border-amber-500/30"
    }
];

export function BeyondSchemesSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      {/* Decorative radial background */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.03),transparent_70%)] pointer-events-none" />

      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-20 space-y-6">
            <Badge variant="outline" className="px-5 py-1.5 border-blue-500/30 bg-blue-500/10 text-blue-400 rounded-full font-black tracking-[0.2em] uppercase text-[11px]">
               Beyond Information
            </Badge>
            <h2 className="text-5xl sm:text-6xl font-black text-white tracking-tight leading-[1.1]">
              More Than Just <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-white to-emerald-400 italic">Schemes.</span>
            </h2>
            <p className="text-xl text-slate-400 font-medium max-w-2xl mx-auto mt-6">
              CivixAI provides a holistic, data-driven view of all financial, social, and professional benefits available to you.
            </p>
          </div>
        </ScrollWrapper>

        <div className="grid gap-8 md:grid-cols-3">
          {items.map((item, index) => (
             <ScrollWrapper key={item.title} delay={index * 0.1}>
                <div className="group relative h-full perspective-1000">
                    {/* Hover glow line */}
                    <div className="absolute -inset-[1px] bg-gradient-to-b from-white/10 to-transparent rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    
                    <Card className={`relative bg-[#050510]/60 border border-white/10 shadow-2xl h-full rounded-[2.5rem] p-4 backdrop-blur-xl transition-all duration-700 transform group-hover:-translate-y-3 group-hover:bg-white/[0.04] ${item.color} group-hover:rotate-x-2`}>
                      <CardHeader className="flex flex-col items-center text-center gap-8 pb-8">
                        <div className="relative group-hover:scale-110 transition-transform duration-700">
                            <div className="absolute -inset-4 bg-blue-500/10 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                            <div className="relative bg-white/5 p-6 rounded-[2rem] border border-white/10 group-hover:bg-blue-500/10 group-hover:border-blue-500/20 shadow-inner">
                                {item.icon}
                            </div>
                        </div>
                        <div className="space-y-4">
                          <div className="flex justify-center flex-wrap gap-2">
                             <Badge variant="secondary" className="bg-white/5 border-white/10 text-slate-500 text-[9px] uppercase font-black tracking-widest px-3">{item.tag}</Badge>
                             <Badge variant="outline" className="text-[9px] border-emerald-500/20 text-emerald-500 uppercase font-black tracking-widest px-3 flex items-center gap-1">
                                <Zap className="w-2.5 h-2.5" />
                                Instant Access
                             </Badge>
                          </div>
                          <CardTitle className="text-2xl font-black text-white tracking-tight leading-tight uppercase group-hover:text-blue-400 transition-colors">
                            {item.title}
                          </CardTitle>
                          <CardDescription className="text-slate-400 text-base leading-relaxed group-hover:text-slate-200 transition-colors">
                            {item.description}
                          </CardDescription>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-6 border-t border-white/5 flex justify-center">
                        <div className="text-[10px] text-slate-500 font-black uppercase tracking-[0.3em] flex items-center gap-3">
                           <Sparkles className="w-3 h-3 text-blue-500/40 group-hover:text-blue-400 transition-colors group-hover:animate-pulse" />
                           Official API Synchronization
                        </div>
                      </CardContent>
                    </Card>
                </div>
             </ScrollWrapper>
          ))}
        </div>
      </div>
    </section>
  );
}
