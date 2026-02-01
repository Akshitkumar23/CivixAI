'use client';

import React from 'react';
import {
  CheckCircle,
  FileText,
  BrainCircuit,
  BarChart,
  User,
  Bot,
} from 'lucide-react';
import Magnetic from '../Magnetic';

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
    <section id="how-it-works" className="py-16 sm:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
            How CivixAI Works
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            A simple, transparent, and intelligent process to connect you with
            your entitlements.
          </p>
        </div>
        <div className="relative max-w-4xl mx-auto">
          {/* The vertical timeline */}
          <div
            className="absolute left-1/2 -translate-x-1/2 top-0 h-full w-0.5 bg-border"
            aria-hidden="true"
          ></div>

          <div className="space-y-16">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                {/* The card content and hover effect */}
                <div
                  className={`w-full md:w-1/2 ${
                    index % 2 === 0
                      ? 'ml-0 md:mr-auto md:pr-8'
                      : 'ml-auto md:pl-8'
                  }`}
                >
                  <div className="group relative">
                    {/* The animated gradient border */}
                    <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />

                    {/* The card itself */}
                    <div className="relative p-6 bg-card rounded-xl border border-transparent flex items-center gap-6 transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
                      <Magnetic>
                        <div className="flex-shrink-0 h-16 w-16 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                          {React.cloneElement(step.icon, {
                            className: 'w-8 h-8',
                          })}
                        </div>
                      </Magnetic>
                      <p
                        className={`font-headline text-lg text-foreground flex-grow text-left md:text-left`}
                      >
                        {step.text}
                      </p>
                    </div>
                  </div>
                </div>

                {/* The center dot on the timeline for desktop */}
                <div className="hidden md:flex absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 h-5 w-5 rounded-full bg-primary ring-4 ring-background z-10 items-center justify-center">
                  <div className="h-2 w-2 rounded-full bg-primary-foreground"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
