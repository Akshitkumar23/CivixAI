'use client';

import { Card, CardContent } from "@/components/ui/card";
import { Map, MapPin, Globe, Navigation, Building2 } from "lucide-react";
import Image from 'next/image';
import { PlaceHolderImages } from '@/lib/placeholder-images';
import { ScrollWrapper } from "@/components/animations/ScrollWrapper";
import { Badge } from "@/components/ui/badge";

export function LocationIntelligenceSection() {
  const locationImage = PlaceHolderImages.find(img => img.id === 'location-map');

  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      {/* Decorative dots background */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="grid lg:grid-cols-2 gap-20 items-center">
          <ScrollWrapper>
            <div className="max-w-xl space-y-8">
              <Badge variant="outline" className="bg-sky-500/10 text-sky-400 border-sky-500/20 rounded-full px-4 py-1 text-[10px] font-black uppercase tracking-widest">Geospatial Engine</Badge>
              <h2 className="text-4xl sm:text-5xl font-black text-white tracking-tight leading-tight">
                Local Rules. <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-indigo-400">Accurate Results.</span>
              </h2>
              <p className="text-xl text-slate-400 font-medium leading-relaxed">
                Government schemes vary by state and district. CivixAI's intelligence engine understands this local context, delivering pixel-perfect eligibility results.
              </p>
              
              <div className="space-y-6 pt-4">
                 {[
                   { icon: <Globe className="text-sky-400" />, title: 'State Variations', text: 'Captures unique state-level criteria and application windows.' },
                   { icon: <Building2 className="text-indigo-400" />, title: 'District Context', text: 'Incorporates local nuances for maximum matching accuracy.' }
                 ].map((feat, i) => (
                   <div key={i} className="flex gap-6 group">
                      <div className="p-4 rounded-2xl bg-white/5 border border-white/5 group-hover:bg-sky-500/10 group-hover:border-sky-500/20 transition-all duration-500">
                        {feat.icon}
                      </div>
                      <div>
                        <h4 className="text-lg font-black text-white tracking-tight leading-none uppercase mb-2">{feat.title}</h4>
                        <p className="text-slate-400 text-sm">{feat.text}</p>
                      </div>
                   </div>
                 ))}
              </div>
            </div>
          </ScrollWrapper>

          <ScrollWrapper>
            <div className="flex justify-center relative">
              <div className="absolute -inset-10 bg-sky-500/10 rounded-full blur-[100px] animate-pulse pointer-events-none" />
              
              {locationImage && (
                <div className="group relative perspective-1000">
                  <div className="absolute -inset-[1px] bg-gradient-to-br from-sky-500/30 to-indigo-500/30 rounded-[2rem] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
                  
                  <div className="relative p-2 rounded-[2.5rem] bg-white/5 border border-white/10 backdrop-blur-xl shadow-2xl transition-all duration-700 transform group-hover:rotate-x-2 group-hover:rotate-y-[-2deg]">
                    <Image 
                        src={locationImage.imageUrl}
                        alt={locationImage.description}
                        width={600}
                        height={500}
                        className="relative rounded-[2rem] shadow-xl grayscale-[0.5] group-hover:grayscale-0 transition-all duration-1000"
                        data-ai-hint={locationImage.imageHint}
                    />
                    
                    {/* Floating HUD Element */}
                    <div className="absolute bottom-10 left-10 p-6 bg-black/60 backdrop-blur-2xl border border-white/20 rounded-3xl shadow-2xl animate-bounce-slow">
                        <div className="flex items-center gap-4">
                           <div className="h-10 w-10 rounded-full bg-sky-500 flex items-center justify-center">
                              <Navigation className="w-5 h-5 text-white" />
                           </div>
                           <div className="text-left">
                              <p className="text-[10px] font-black text-sky-400 uppercase tracking-widest leading-none">Detection</p>
                              <p className="text-sm font-black text-white mt-1">Maharashtra, India</p>
                           </div>
                        </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollWrapper>
        </div>
      </div>
    </section>
  );
}
