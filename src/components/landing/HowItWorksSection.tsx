'use client';

import React from 'react';
import { CheckCircle, FileText, BrainCircuit, BarChart, User, Bot } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';

const steps = [
  { icon: <User />, text: 'Tell us a bit about yourself' },
  { icon: <Bot />, text: 'Our AI checks thousands of rules' },
  { icon: <BrainCircuit />, text: 'See exactly why you might qualify' },
  { icon: <BarChart />, text: 'Get your top schemes and loans ranked' },
  { icon: <FileText />, text: 'Save a checklist of documents you need' },
  { icon: <CheckCircle />, text: 'Apply confidently without confusion' },
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
              Discover what belongs to you in just a few quick and easy steps. We do the hard work so you do not have to.
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

                    <div className="group relative transform transition-all duration-700 hover:-translate-y-1 hover:rotate-x-2">
                      {/* Subtler, narrower highlight */}
                      <div className="absolute -inset-[1px] bg-gradient-to-r from-blue-500/20 to-teal-500/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />

                      <div className="relative p-6 sm:p-8 bg-white/[0.03] border border-white/10 rounded-2xl flex items-center gap-6 shadow-2xl backdrop-blur-md group-hover:bg-white/[0.06] transition-all duration-500 hover:border-blue-500/20">

                        <div className="flex-shrink-0 h-16 w-16 sm:h-20 sm:w-20 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-400 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.2)] group-hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all duration-500">
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
