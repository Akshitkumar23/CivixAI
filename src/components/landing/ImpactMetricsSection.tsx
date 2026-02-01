'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Clock, Lightbulb, TrendingUp, CheckCircle } from 'lucide-react';

const metrics = [
  { icon: <Clock className="w-8 h-8" />, label: 'Time Saved for Citizens' },
  { icon: <Lightbulb className="w-8 h-8" />, label: 'Reduced Confusion' },
  { icon: <TrendingUp className="w-8 h-8" />, label: 'Increased Scheme Awareness' },
  { icon: <CheckCircle className="w-8 h-8" />, label: 'Smarter Benefit Utilization' },
];

export function ImpactMetricsSection() {
  return (
    <section className="py-16 sm:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
            Measuring Our Impact & Credibility
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Our success is defined by the real-world value we deliver to citizens and institutions, fostering a more informed and empowered society.
          </p>
        </div>
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          {metrics.map((metric) => (
            <div key={metric.label} className="group relative">
              <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
              <Card className="relative text-center bg-card shadow-lg h-full border-transparent transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
                <CardContent className="p-6">
                  <div className="mx-auto text-secondary mb-4">
                    {metric.icon}
                  </div>
                  <p className="font-headline">{metric.label}</p>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
