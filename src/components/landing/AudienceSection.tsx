'use client';

import { Card, CardContent } from '@/components/ui/card';
import { User, GraduationCap, HardHat, ShieldHalf, LandPlot, Users, Building, Sparkles } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';
import { Badge } from '@/components/ui/badge';

const userGroups = [
  { icon: <User className="w-6 h-6" />, name: 'Citizens', desc: 'Find personal welfare & pension schemes.', color: 'text-blue-400' },
  { icon: <GraduationCap className="w-6 h-6" />, name: 'Students', desc: 'Secure scholarships & educational loans.', color: 'text-amber-400' },
  { icon: <HardHat className="w-6 h-6" />, name: 'Farmers', desc: 'Access KCC, subsidies & agricultural aid.', color: 'text-emerald-400' },
  { icon: <ShieldHalf className="w-6 h-6" />, name: 'NGOs', desc: 'Scale social impact with automated data.', color: 'text-rose-400' },
  { icon: <LandPlot className="w-6 h-6" />, name: 'Govt. Centers', desc: 'Empower local offices with AI matching.', color: 'text-sky-400' },
  { icon: <Building className="w-6 h-6" />, name: 'Research', desc: 'Analyze civic trends & benefit distribution.', color: 'text-indigo-400' },
];

export function AudienceSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.05),transparent_70%)] pointer-events-none" />

      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-20 space-y-4">
            <Badge variant="outline" className="px-5 py-1.5 border-blue-500/30 bg-blue-500/10 text-blue-400 rounded-full font-black tracking-[0.2em] uppercase text-[11px]">
               Social Impact Ecosystem
            </Badge>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.1]">
              Empowering Every <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500">Stakeholder.</span>
            </h2>
            <p className="text-xl text-slate-400 font-medium max-w-2xl mx-auto leading-relaxed mt-6">
              CivixAI bridge the gap between complex government policy and the people who need it most.
            </p>
          </div>
        </ScrollWrapper>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {userGroups.map((group, index) => (
                <ScrollWrapper key={group.name}>
                    <div className="group relative h-full perspective-1000">
                        {/* Hover glow */}
                        <div className="absolute -inset-[1px] bg-gradient-to-br from-blue-500/20 to-transparent rounded-[2.5rem] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                        
                        <Card className="relative h-full bg-[#050510]/60 border border-white/10 rounded-[2.5rem] p-8 backdrop-blur-xl transition-all duration-700 group-hover:bg-white/[0.04] group-hover:border-white/20 group-hover:-translate-y-2 group-hover:rotate-x-2">
                             <div className="flex flex-col gap-6">
                                <div className={`h-16 w-16 rounded-[1.5rem] bg-white/5 flex items-center justify-center ${group.color} transition-all duration-500 group-hover:scale-110 group-hover:bg-blue-500/10 shadow-lg`}>
                                    {group.icon}
                                </div>
                                <div className="space-y-3">
                                    <h3 className="text-2xl font-black text-white tracking-tight uppercase group-hover:text-blue-400 transition-colors">
                                        {group.name}
                                    </h3>
                                    <p className="text-slate-400 text-base leading-relaxed group-hover:text-slate-200 transition-colors">
                                        {group.desc}
                                    </p>
                                </div>
                             </div>
                             
                             <div className="absolute top-6 right-8 opacity-0 group-hover:opacity-40 transition-opacity">
                                <Sparkles className="w-5 h-5 text-blue-500" />
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
