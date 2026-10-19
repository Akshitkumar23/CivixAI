import React from 'react';
import { CheckCircle, FileText, BarChart, User, ShieldCheck, ExternalLink } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';

const steps = [
  { icon: <User />, phase: 'Discover', title: 'Adaptive Profile Discovery', text: 'Answer a few high-impact questions. Irrelevant questions are automatically omitted using next-best-question logic.' },
  { icon: <ShieldCheck />, phase: 'Verify', title: 'Deterministic Statutory Rules', text: 'Official Gazette rules evaluate your exact eligibility (ELIGIBLE, NEEDS_INFO, NEEDS_VERIFICATION). No LLM guesses.' },
  { icon: <FileText />, phase: 'Explain', title: 'Grounded Evidence Citations', text: 'Inspect exact reason codes backed by verifiable .gov.in official Gazette and ministry sources.' },
  { icon: <BarChart />, phase: 'Compare', title: 'Domain-Aware Comparison', text: 'Compare welfare subsidies, government loans, and credit terms side-by-side with transparent scoring.' },
  { icon: <CheckCircle />, phase: 'Prepare', title: 'Document Readiness (0–100%)', text: 'Track your preparation progress with clear document checklists and safe offline autofill assistance.' },
  { icon: <ExternalLink />, phase: 'Apply', title: 'Safe Official Portal Redirection', text: 'Apply directly through verified .gov.in department portals with zero third-party submission risks.' },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 sm:py-32 bg-transparent relative overflow-hidden">
      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-20 gsap-animate">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-semibold backdrop-blur-md mb-4">
              End-to-End Citizen Decision Lifecycle
            </div>
            <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white drop-shadow-md">
              How CivixAI Works
            </h2>
            <p className="mt-4 text-base sm:text-lg text-slate-300 font-medium tracking-wide drop-shadow-sm">
              From discovering hidden government benefits to statutory verification, evidence explanation, and safe application.
            </p>
          </div>
        </ScrollWrapper>

        <div className="relative max-w-5xl mx-auto">
          {/* The glowing vertical timeline */}
          <div className="absolute left-1/2 -translate-x-1/2 top-0 h-full w-[2px] bg-gradient-to-b from-blue-500/0 via-blue-500/50 to-blue-500/0" />

          <div className="space-y-12">
            {steps.map((step, index) => (
              <ScrollWrapper key={index}>
                <div className="relative z-10 perspective-1000 gsap-animate">
                  <div className={`w-full md:w-[46%] ${index % 2 === 0 ? 'ml-0 md:mr-auto' : 'ml-auto'}`}>
                    <div className="group relative transform transition-all duration-500 hover:-translate-y-1">
                      <div className="relative p-6 sm:p-7 bg-white/[0.03] border border-white/10 rounded-2xl flex items-start gap-5 shadow-2xl backdrop-blur-md group-hover:bg-white/[0.06] transition-all duration-300 hover:border-blue-500/30">
                        <div className="flex-shrink-0 h-14 w-14 rounded-2xl bg-blue-500/15 border border-blue-400/25 text-blue-400 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.2)] group-hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all duration-300">
                          {React.cloneElement(step.icon as React.ReactElement, { className: 'w-7 h-7' })}
                        </div>

                        <div>
                          <div className="text-blue-300 text-[11px] font-extrabold tracking-widest uppercase mb-0.5">
                            Stage 0{index + 1} • {step.phase}
                          </div>
                          <h3 className="text-lg font-bold text-white mb-1.5">
                            {step.title}
                          </h3>
                          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
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
