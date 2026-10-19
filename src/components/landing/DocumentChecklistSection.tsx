'use client';

import { Card, CardContent } from "@/components/ui/card";
import { CheckSquare, FileText, BadgeCheck, ShieldAlert, Sparkles, Files } from "lucide-react";
import { ScrollWrapper } from "@/components/animations/ScrollWrapper";
import { Badge } from "@/components/ui/badge";

export function DocumentChecklistSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      {/* Decorative vertical line */}
      <div className="absolute right-0 top-0 h-full w-[1px] bg-gradient-to-b from-transparent via-white/10 to-transparent" />
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="grid lg:grid-cols-2 gap-20 items-center">
          <ScrollWrapper>
            <div className="max-w-xl space-y-10 order-2 lg:order-1">
              <div className="space-y-4">
                <Badge variant="outline" className="px-5 py-1.5 border-amber-500/30 bg-amber-500/10 text-amber-400 rounded-full font-black tracking-[0.2em] uppercase text-[11px]">
                   Eliminate Friction
                </Badge>
                <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.1]">
                  Know What You Need <br/>
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-600 italic">Before You Apply.</span>
                </h2>
                <p className="text-xl text-slate-400 font-medium leading-relaxed mt-6">
                  CivixAI cross-references official gazettes to generate precise checklists. No more wasted trips to government offices or rejected applications.
                </p>
              </div>
              
              <div className="grid sm:grid-cols-1 gap-6 pt-4">
                {[
                  { icon: <BadgeCheck className="text-emerald-400 w-6 h-6" />, title: 'Personalized Checklists', desc: 'Get a targeted list based on your specific eligibility match, updated in real-time.' },
                  { icon: <ShieldAlert className="text-rose-400 w-6 h-6" />, title: 'Zero Rejection Mission', desc: 'Avoid missing documents that cause 40% of all government scheme rejections in India.' }
                ].map((item, idx) => (
                  <div key={idx} className="flex gap-6 group p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.05] hover:border-amber-500/20 transition-all duration-500">
                    <div className="mt-1 p-3 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center h-14 w-14 shrink-0 transition-transform group-hover:scale-110">
                      {item.icon}
                    </div>
                    <div className="space-y-1">
                      <span className="block font-black text-white uppercase tracking-tight text-base mb-1">{item.title}</span>
                      <p className="text-slate-400 leading-relaxed text-sm font-medium">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </ScrollWrapper>

          <ScrollWrapper delay={0.2}>
            <div className="flex justify-center order-1 lg:order-2 perspective-1000">
              <div className="group relative w-full max-w-md">
                {/* Intense glowing orb behind card */}
                <div className="absolute -inset-10 bg-amber-500/10 rounded-full blur-[120px] opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none" />
                
                <Card className="relative bg-[#0a0a1a]/80 border border-white/10 shadow-2xl rounded-[3rem] backdrop-blur-2xl overflow-hidden group-hover:border-amber-500/40 transition-all duration-700 transform group-hover:rotate-y-[-5deg] group-hover:rotate-x-[2deg]">
                  {/* Subtle scanline animation */}
                  <div className="absolute inset-0 bg-gradient-to-b from-transparent via-amber-500/[0.02] to-transparent h-full w-full animate-scan pointer-events-none" />
                  
                  <div className="absolute top-0 right-0 p-10 opacity-5">
                    <Files className="w-48 h-48 text-amber-500" />
                  </div>
                  
                  <CardContent className="p-10 relative z-10">
                    <div className="flex items-center gap-5 mb-10 pb-6 border-b border-white/5">
                       <div className="h-14 w-14 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center shadow-[0_0_20px_rgba(245,158,11,0.2)]">
                          <FileText className="w-8 h-8 text-amber-400" />
                       </div>
                       <div>
                          <h3 className="text-xl font-black text-white tracking-tight leading-none uppercase">Smart Checklist</h3>
                          <p className="text-[10px] text-slate-500 font-black uppercase tracking-[0.2em] mt-2">Source: Digital India Portal</p>
                       </div>
                    </div>
                    
                    <ul className="space-y-4">
                        {[
                          { text: "Aadhar Card (e-KYC verified)", status: "Ready" },
                          { text: "Ration Card (NFSA Linked)", status: "Ready" },
                          { text: "Income Certificate (Current Year)", status: "Required" },
                          { text: "Bank Passbook (NCPI Mapping)", status: "Ready" }
                        ].map((doc, i) => (
                          <li key={i} className="flex items-center justify-between p-5 rounded-[1.5rem] bg-white/[0.03] border border-white/5 group-hover:bg-amber-500/[0.02] hover:border-amber-500/20 transition-all group/item">
                              <div className="flex items-center gap-4">
                                <div className={`h-6 w-6 rounded-md border-2 border-emerald-500/30 flex items-center justify-center ${doc.status === 'Ready' ? 'text-emerald-400' : 'text-slate-600'}`}>
                                    <CheckSquare className="w-4 h-4" />
                                </div>
                                <span className="text-slate-300 font-bold text-sm tracking-tight">{doc.text}</span>
                              </div>
                              <Badge variant="outline" className={`text-[9px] uppercase font-black tracking-widest ${doc.status === 'Ready' ? 'text-emerald-500 border-emerald-500/20' : 'text-amber-500 border-amber-500/20 animate-pulse'}`}>
                                {doc.status}
                              </Badge>
                          </li>
                        ))}
                    </ul>
                    
                    <div className="mt-10 p-6 rounded-3xl bg-white/5 border border-dashed border-white/10 text-center relative group-hover:bg-amber-500/5 transition-all">
                        <span className="text-[10px] text-slate-400 font-black uppercase tracking-[0.3em] flex items-center justify-center gap-2">
                           <Sparkles className="w-3 h-3 text-amber-400" />
                           Verified Intelligence Match
                        </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </ScrollWrapper>
        </div>
      </div>
    </section>
  );
}
