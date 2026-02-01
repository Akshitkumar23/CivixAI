'use client';

import { Card, CardContent } from "@/components/ui/card";
import { BrainCircuit, Lightbulb, Check, X } from "lucide-react";

export function ExplainableAISection() {
  return (
    <section className="py-16 sm:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-2 gap-12 items-center">
           <div className="flex justify-center">
            <Card className="p-6 bg-muted shadow-xl w-full max-w-md">
              <CardContent className="p-0">
                <div className="flex items-center gap-4 mb-6">
                    <BrainCircuit className="w-10 h-10 text-primary flex-shrink-0" />
                    <h3 className="text-xl font-bold">Eligibility Decision for PM-JAY</h3>
                </div>
                
                <div className="space-y-4">
                    <div className="p-4 border rounded-lg bg-background">
                        <p className="font-semibold text-green-700 flex items-center gap-2"><Check className="w-5 h-5"/> You are likely ELIGIBLE</p>
                        <p className="text-sm text-muted-foreground mt-2">Reasoning:</p>
                         <ul className="list-disc list-inside text-sm space-y-1 mt-1">
                            <li>Your annual income of ₹1,50,000 is below the ₹2,50,000 threshold.</li>
                            <li>Your caste category (SC) is included in the scheme's criteria.</li>
                         </ul>
                    </div>
                     <div className="p-4 border rounded-lg bg-background">
                        <p className="font-semibold text-destructive flex items-center gap-2"><X className="w-5 h-5"/> Ineligible for PMAY-U (Interest Subsidy)</p>
                         <p className="text-sm text-muted-foreground mt-2">Reasoning:</p>
                         <ul className="list-disc list-inside text-sm space-y-1 mt-1">
                            <li>Scheme is not available in your state (e.g. Sikkim).</li>
                         </ul>
                    </div>
                </div>

              </CardContent>
            </Card>
          </div>
          <div className="max-w-md">
            <div className="flex items-center gap-3 text-secondary font-semibold">
                <Lightbulb className="w-5 h-5" />
                <span>TRUST & TRANSPARENCY</span>
            </div>
            <h2 className="mt-2 text-3xl sm:text-4xl font-bold text-primary">
              AI That Explains, Not Just Recommends
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              We believe in transparent AI. CivixAI moves beyond "black box" algorithms to provide clear, human-readable reasons for every recommendation, building trust and empowering you to make confident decisions.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
