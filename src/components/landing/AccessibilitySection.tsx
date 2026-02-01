'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Smartphone, WifiOff, Users } from 'lucide-react';

const features = [
  {
    icon: <Smartphone className="h-8 w-8 text-primary" />,
    title: 'Mobile-First Design',
    description: 'Access information seamlessly on any device, from basic smartphones to desktops.',
  },
  {
    icon: <WifiOff className="h-8 w-8 text-primary" />,
    title: 'Offline-Ready (PWA)',
    description: 'Works even with low or no internet, ensuring access for citizens in remote areas.',
  },
  {
    icon: <Users className="h-8 w-8 text-primary" />,
    title: 'Inclusive & Simple UX',
    description: 'Designed for everyone, with a clear and simple interface that is easy to navigate.',
  },
];

export function AccessibilitySection() {
  return (
    <section className="py-16 sm:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
            Built for Real India
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            We are committed to making civic technology accessible to every Indian, regardless of location or internet connectivity.
          </p>
        </div>
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          {features.map((feature, index) => (
            <div key={index} className="group relative">
              <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
              <Card className="relative text-center bg-card shadow-lg h-full border-transparent transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
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
      </div>
    </section>
  );
}
