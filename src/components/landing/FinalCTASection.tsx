'use client';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import Magnetic from '../Magnetic';

export function FinalCTASection() {
  return (
    <section className="py-16 sm:py-24 bg-primary text-primary-foreground">
      <div className="container mx-auto px-4 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold max-w-3xl mx-auto">
          Millions miss benefits they deserve. CivixAI brings clarity, intelligence, and access.
        </h2>
        <div className="mt-8">
            <Magnetic>
                <Button size="lg" variant="secondary" className="bg-background text-primary hover:bg-background/90" asChild>
                    <Link href="/check-eligibility">
                        Get Started with CivixAI
                        <ArrowRight className="ml-2 h-5 w-5" />
                    </Link>
                </Button>
            </Magnetic>
        </div>
      </div>
    </section>
  );
}
