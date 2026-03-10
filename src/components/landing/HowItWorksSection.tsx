'use client';

import React from 'react';
import { CheckCircle, FileText, BrainCircuit, BarChart, User, Bot } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';

const steps = [
  { icon: <User />, text: 'User enters basic details' },
  { icon: <Bot />, text: 'AI + rule engine checks eligibility' },
  { icon: <BrainCircuit />, text: 'Transparent explanation of results' },
  { icon: <BarChart />, text: 'Schemes, loans & insurance ranked' },
  { icon: <FileText />, text: 'Required documents list generated' },
  { icon: <CheckCircle />, text: 'Smarter application decisions' },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-20 gsap-animate">
            <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white drop-shadow-md">
              How CivixAI Works
            </h2>
            <p className="mt-6 text-xl text-slate-300 font-medium tracking-wide drop-shadow-sm">
              A simple, transparent, and intelligent process to connect you with your entitlements.
            </p>
          </div>
        </ScrollWrapper>

        <div className="relative max-w-5xl mx-auto">
          {/* The glowing vertical timeline */}
          <div className="absolute left-1/2 -translate-x-1/2 top-0 h-full w-[2px] bg-gradient-to-b from-blue-500/0 via-blue-500/50 to-blue-500/0" />

          <div className="space-y-16">
            {steps.map((step, index) => (
              <ScrollWrapper key={index}>
                <div className="relative z-10 perspective-1000 gsap-animate">
                  <div className={`w-full md:w-[45%] ${index % 2 === 0 ? 'ml-0 md:mr-auto' : 'ml-auto'}`}>

                    <div className="group relative transform transition-all duration-700 hover:scale-105">
                      {/* Glowing highlight on hover */}
                      <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-2xl blur-lg opacity-0 group-hover:opacity-40 transition-opacity duration-500" />

                      <div className="relative p-6 sm:p-8 bg-white/5 border border-white/10 rounded-2xl flex items-center gap-6 shadow-2xl backdrop-blur-xl group-hover:bg-white/10 transition-colors duration-500">

                        <div className="flex-shrink-0 h-16 w-16 sm:h-20 sm:w-20 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-400 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.3)] group-hover:shadow-[0_0_25px_rgba(59,130,246,0.6)] transition-all duration-500">
                          {React.cloneElement(step.icon as React.ReactElement, { className: 'w-8 h-8 sm:w-10 sm:h-10' })}
                        </div>

                        <div>
                          <div className="text-blue-300 text-xs sm:text-sm font-bold tracking-widest uppercase mb-1 drop-shadow-sm">
                            Phase 0{index + 1}
                          </div>
                          <p className="text-lg sm:text-xl font-bold text-white leading-snug tracking-wide">
                            {step.text}
                          </p>
                        </div>

                      </div>
                    </div>
                  </div>

                  {/* The glowing center dot on the timeline for desktop */}
                  <div className="hidden md:flex absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 h-6 w-6 rounded-full bg-[#050510] border-2 border-blue-500 z-10 items-center justify-center shadow-[0_0_10px_rgba(59,130,246,0.8)]">
                    <div className="h-2 w-2 rounded-full bg-blue-400 animate-pulse"></div>
                  </div>
                </div>
              </ScrollWrapper>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
