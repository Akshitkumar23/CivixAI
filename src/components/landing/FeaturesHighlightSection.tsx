'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BrainCircuit, Target, FileCheck2, ArrowRight } from 'lucide-react';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';

const highlightedFeatures = [
  {
    icon: <BrainCircuit className="h-10 w-10 text-blue-400" />,
    title: 'AI Eligibility Engine',
    description: 'Answer a few simple questions and let our AI instantly find schemes you qualify for.',
  },
  {
    icon: <Target className="h-10 w-10 text-teal-400" />,
    title: 'Transparent Recommendations',
    description: 'Understand exactly why a scheme is recommended for you with clear, simple explanations.',
  },
  {
    icon: <FileCheck2 className="h-10 w-10 text-indigo-400" />,
    title: 'Auto-Generated Checklists',
    description: 'Get a personalized list of all required documents for each application, reducing errors.',
  },
];

export function FeaturesHighlightSection() {
  return (
    <section className="py-24 sm:py-32 bg-transparent relative overflow-hidden">

      <div className="container mx-auto px-4 relative z-10">
        <ScrollWrapper>
          <div className="text-center max-w-3xl mx-auto mb-20 gsap-animate">
            <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white drop-shadow-lg">
              Key Features at a Glance
            </h2>
            <p className="mt-6 text-xl text-slate-300 font-medium drop-shadow-md">
              We use technology to make finding and applying for benefits simple, transparent, and fast.
            </p>
          </div>
        </ScrollWrapper>

        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {highlightedFeatures.map((feature, index) => (
            <ScrollWrapper key={index}>
              <div className="group relative perspective-1000 gsap-animate h-full">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-teal-500 rounded-3xl blur-xl opacity-0 group-hover:opacity-30 transition-opacity duration-700 pointer-events-none" />

                <Card className="relative text-center bg-white/5 border border-white/10 shadow-2xl backdrop-blur-xl rounded-3xl p-6 transition-all duration-500 h-full group-hover:-translate-y-2 group-hover:bg-white/10">
                  <CardHeader className="pt-4">
                    <div className="mx-auto bg-black/40 border border-white/10 rounded-2xl h-20 w-20 flex items-center justify-center mb-6 shadow-inner group-hover:scale-110 transition-transform duration-500">
                      {feature.icon}
                    </div>
                    <CardTitle className="text-2xl font-bold text-white tracking-wide mb-2">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-300 text-lg leading-relaxed">{feature.description}</p>
                  </CardContent>
                </Card>
              </div>
            </ScrollWrapper>
          ))}
        </div>

        <div className="mt-20 text-center">
          <div className="inline-block relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full blur opacity-40 group-hover:opacity-80 transition duration-500"></div>
            <Button asChild className="relative h-14 px-10 text-lg bg-black border border-white/20 text-white hover:bg-white/10 backdrop-blur-md rounded-full transition-all duration-300 shadow-xl font-bold">
              <Link href="/features">
                Explore All Features
                <ArrowRight className="ml-2 w-5 h-5 text-blue-400 group-hover:translate-x-1 transition-transform" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
