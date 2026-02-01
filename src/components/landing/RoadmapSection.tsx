'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Bot, Fingerprint, LayoutGrid, BarChart3, Badge } from 'lucide-react';

const roadmapItems = [
  { icon: <Fingerprint className="w-8 h-8 text-primary" />, title: 'Aadhaar & DigiLocker Integration' },
  { icon: <Bot className="w-8 h-8 text-primary" />, title: 'AI Chatbot & Voice Assistant' },
  { icon: <LayoutGrid className="w-8 h-8 text-primary" />, title: 'NGO & CSC Dashboards' },
  { icon: <BarChart3 className="w-8 h-8 text-primary" />, title: 'Government Analytics Platform' },
];

export function RoadmapSection() {
  return (
    <section className="py-16 sm:py-24 bg-muted">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
            Future-Safe: Our Roadmap Ahead
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            We are continuously evolving to build a more intelligent and integrated civic-tech ecosystem for India.
          </p>
        </div>
        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8">
          {roadmapItems.map((item) => (
            <div key={item.title} className="group relative">
              <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
              <Card className="relative overflow-hidden text-center bg-card shadow-lg h-full border-transparent transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
                <CardContent className="p-6 flex flex-col items-center justify-center gap-4 h-full">
                  <div className="bg-primary/10 rounded-full p-4">
                      {item.icon}
                  </div>
                  <p className="font-headline text-center flex-grow">{item.title}</p>
                  <div className="absolute top-2 right-2">
                      <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors bg-secondary/20 text-secondary-foreground">Coming Soon</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
