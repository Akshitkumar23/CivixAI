'use client';

import { Card, CardContent } from "@/components/ui/card";
import { Map, MapPin } from "lucide-react";
import Image from 'next/image';
import { PlaceHolderImages } from '@/lib/placeholder-images';

export function LocationIntelligenceSection() {
  const locationImage = PlaceHolderImages.find(img => img.id === 'location-map');

  return (
    <section className="py-16 sm:py-24 bg-muted">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="max-w-md">
            <h2 className="text-3xl sm:text-4xl font-bold text-primary">
              Local Rules. Accurate Results.
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Government schemes often have specific rules that vary by state or even district. CivixAI's intelligence engine is designed to understand this local context, delivering more accurate and relevant eligibility results.
            </p>
            <ul className="mt-6 space-y-4">
              <li className="flex items-start gap-3">
                <MapPin className="w-6 h-6 text-secondary mt-1 flex-shrink-0" />
                <span><span className="font-semibold">State-wise Variations:</span> Captures unique eligibility criteria, application windows, and benefits at the state level.</span>
              </li>
              <li className="flex items-start gap-3">
                <MapPin className="w-6 h-6 text-secondary mt-1 flex-shrink-0" />
                <span><span className="font-semibold">District-level Conditions:</span> Incorporates district-specific nuances where applicable for higher accuracy.</span>
              </li>
            </ul>
          </div>
          <div className="flex justify-center">
            {locationImage && (
              <div className="group relative">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-accent to-primary rounded-lg blur opacity-0 group-hover:opacity-60 transition duration-300"></div>
                <Image 
                    src={locationImage.imageUrl}
                    alt={locationImage.description}
                    width={600}
                    height={500}
                    className="relative rounded-lg shadow-xl"
                    data-ai-hint={locationImage.imageHint}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
