'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { ArrowRight, PlayCircle } from 'lucide-react';
import Magnetic from '../Magnetic';

export function HeroSection() {
    const heroImage = {
      "id": "landing-hero",
      "description": "An AI bot assisting a family with civic services in front of government buildings.",
      "imageUrl": "https://storage.googleapis.com/gcp-kms-production-903522a1f496/12589578-8255-442b-8a75-7c093a207923",
      "imageHint": "empowered individual rural technology"
    };

    return (
        <section className="bg-muted py-12 sm:py-20">
            <div className="container mx-auto px-4">
                <div className="grid md:grid-cols-2 gap-8 items-center">
                    <div className="text-center md:text-left">
                        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-primary tracking-tight">
                            CivixAI – Smart Government Benefits, Powered by AI
                        </h1>
                        <p className="mt-4 max-w-2xl mx-auto md:mx-0 text-lg text-muted-foreground sm:text-xl">
                            Discover government schemes, loans, insurance, and welfare benefits you are eligible for — with clarity and confidence.
                        </p>
                        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
                            <Magnetic>
                                <Button size="lg" asChild>
                                    <Link href="/check-eligibility">
                                        Check My Eligibility
                                        <ArrowRight className="ml-2" />
                                    </Link>
                                </Button>
                            </Magnetic>
                             <Magnetic>
                                <Button size="lg" variant="outline" asChild>
                                    <Link href="/features">
                                        <PlayCircle className="mr-2" />
                                        Explore Benefits
                                    </Link>
                                </Button>
                            </Magnetic>
                        </div>
                    </div>
                    <div className="flex justify-center">
                        {heroImage && (
                            <Image
                                src={heroImage.imageUrl}
                                alt={heroImage.description}
                                width={600}
                                height={400}
                                className="rounded-lg shadow-xl"
                                data-ai-hint={heroImage.imageHint}
                            />
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
}
