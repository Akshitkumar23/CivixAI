'use client';

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Landmark, ShieldCheck, PiggyBank } from "lucide-react";

const items = [
    {
        icon: <Landmark className="w-8 h-8 text-primary" />,
        title: "Government Loans",
        description: "Discover and compare loan options from public sector banks and government-backed credit programs.",
    },
    {
        icon: <ShieldCheck className="w-8 h-8 text-primary" />,
        title: "Insurance & Social Security",
        description: "Find insurance schemes like PM-JAY and social security benefits for a secure future.",
    },
    {
        icon: <PiggyBank className="w-8 h-8 text-primary" />,
        title: "Post Office Savings",
        description: "Explore safe and reliable investment and savings schemes available through the Indian Postal Service.",
    }
];

export function BeyondSchemesSection() {
  return (
    <section className="py-16 sm:py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="font-headline text-3xl sm:text-4xl font-bold text-primary">
            More Than Just Schemes
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            CivixAI provides a holistic view of all financial and social benefits available to you.
          </p>
        </div>
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          {items.map((item) => (
             <div key={item.title} className="group relative h-full">
                <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
                <Card className="relative bg-card shadow-lg h-full border-transparent transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
                  <CardHeader className="flex flex-row items-center gap-4">
                    <div className="bg-primary/10 p-3 rounded-full">
                        {item.icon}
                    </div>
                    <div>
                      <CardTitle className="font-headline text-xl">{item.title}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{item.description}</CardDescription>
                  </CardContent>
                </Card>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
