'use client';

import { Card, CardContent } from '@/components/ui/card';
import {
  BrainCircuit,
  Target,
  Calculator,
  GitCompareArrows,
  FileCheck2,
  MapPin,
  Landmark,
  ShieldCheck,
  Languages,
  Smartphone,
} from 'lucide-react';

const features = [
  { icon: <BrainCircuit className="w-7 h-7" />, title: 'AI Eligibility Engine' },
  { icon: <Target className="w-7 h-7" />, title: 'Smart Recommendations' },
  { icon: <Calculator className="w-7 h-7" />, title: 'Benefit Estimation' },
  { icon: <GitCompareArrows className="w-7 h-7" />, title: 'Scheme Comparison Tool' },
  { icon: <FileCheck2 className="w-7 h-7" />, title: 'Document Generator' },
  { icon: <MapPin className="w-7 h-7" />, title: 'State & District Rules' },
  { icon: <Landmark className="w-7 h-7" />, title: 'Loan & Insurance Finder' },
  { icon: <ShieldCheck className="w-7 h-7" />, title: 'Post Office Schemes' },
  { icon: <Languages className="w-7 h-7" />, title: 'Multi-language Ready' },
  { icon: <Smartphone className="w-7 h-7" />, title: 'Mobile & PWA Optimized' },
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-16 sm:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
            Core Intelligence Features
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            A comprehensive suite of tools designed to bring clarity and confidence to your search for government benefits.
          </p>
        </div>
        <div className="mt-12 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {features.map((feature, index) => (
             <div key={index} className="group relative">
                <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
                <Card className="relative text-center p-4 bg-card shadow-lg h-full border-transparent transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
                  <CardContent className="flex flex-col items-center justify-center gap-3 p-2">
                    <div className="text-primary">{feature.icon}</div>
                    <p className="font-headline text-sm leading-tight">{feature.title}</p>
                  </CardContent>
                </Card>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
