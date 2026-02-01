'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileSearch, Clock, AlertTriangle, BrainCircuit, CheckCircle, Smile } from 'lucide-react';

export function BeforeAfterSection() {
  return (
    <section className="py-16 sm:py-24 bg-muted">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
            The Old Way vs. The CivixAI Way
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Stop drowning in information. Start getting clear answers.
          </p>
        </div>
        <div className="mt-12 grid md:grid-cols-2 gap-8 lg:gap-12">
          {/* Before Card */}
          <Card className="border-destructive/50 border-2 shadow-lg bg-card">
            <CardHeader>
              <CardTitle className="font-headline text-2xl text-destructive text-center">
                Without CivixAI: The Search is Endless
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-start gap-4">
                <FileSearch className="w-10 h-10 text-destructive flex-shrink-0" />
                <p className="text-foreground/80">Jumping between countless government websites, news articles, and local offices.</p>
              </div>
              <div className="flex items-start gap-4">
                <AlertTriangle className="w-10 h-10 text-destructive flex-shrink-0" />
                <p className="text-foreground/80">Confusing eligibility rules and unclear application processes lead to mistakes.</p>
              </div>
              <div className="flex items-start gap-4">
                <Clock className="w-10 h-10 text-destructive flex-shrink-0" />
                <p className="text-foreground/80">Hours, days, even weeks wasted on research with no guarantee of finding the right benefit.</p>
              </div>
            </CardContent>
          </Card>

          {/* After Card */}
           <div className="group relative">
             <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-80 transition-opacity duration-300 animate-gradient-pan bg-[length:200%_auto]" />
              <Card className="relative bg-card shadow-lg border-2 border-transparent h-full transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
                <CardHeader>
                  <CardTitle className="font-headline text-2xl text-primary text-center">
                    With CivixAI: Clarity in Minutes
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-start gap-4">
                    <BrainCircuit className="w-10 h-10 text-primary flex-shrink-0" />
                    <p className="text-foreground/80">Answer a few simple questions and let our AI do the heavy lifting for you.</p>
                  </div>
                  <div className="flex items-start gap-4">
                    <CheckCircle className="w-10 h-10 text-primary flex-shrink-0" />
                    <p className="text-foreground/80">Get a clear, prioritized list of schemes you are actually eligible for.</p>
                  </div>
                  <div className="flex items-start gap-4">
                    <Smile className="w-10 h-10 text-primary flex-shrink-0" />
                    <p className="text-foreground/80">Feel confident and empowered with personalized checklists and transparent reasons.</p>
                  </div>
                </CardContent>
              </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
