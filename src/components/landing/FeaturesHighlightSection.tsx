'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BrainCircuit, Target, FileCheck2, ArrowRight } from 'lucide-react';

const highlightedFeatures = [
  {
    icon: <BrainCircuit className="h-8 w-8 text-primary" />,
    title: 'AI Eligibility Engine',
    description: 'Answer a few simple questions and let our AI instantly find schemes you qualify for.',
  },
  {
    icon: <Target className="h-8 w-8 text-primary" />,
    title: 'Transparent Recommendations',
    description: 'Understand exactly why a scheme is recommended for you with clear, simple explanations.',
  },
  {
    icon: <FileCheck2 className="h-8 w-8 text-primary" />,
    title: 'Auto-Generated Checklists',
    description: 'Get a personalized list of all required documents for each application, reducing errors.',
  },
];

export function FeaturesHighlightSection() {
  return (
    <section className="py-16 sm:py-24 bg-muted">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
            Key Features at a Glance
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            We use technology to make finding and applying for benefits simple, transparent, and fast.
          </p>
        </div>
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          {highlightedFeatures.map((feature, index) => (
            <div key={index} className="group relative">
              <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
              <Card className="relative text-center bg-card shadow-lg h-full border-transparent p-4 transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
                <CardHeader>
                  <div className="mx-auto bg-primary/10 rounded-full h-16 w-16 flex items-center justify-center">
                    {feature.icon}
                  </div>
                </CardHeader>
                <CardContent>
                  <CardTitle className="font-headline text-xl mb-2">{feature.title}</CardTitle>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
        <div className="mt-12 text-center">
            <Button asChild size="lg">
                <Link href="/features">
                    Explore All Features
                    <ArrowRight className="ml-2" />
                </Link>
            </Button>
        </div>
      </div>
    </section>
  );
}
