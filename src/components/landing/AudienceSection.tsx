'use client';

import { Card, CardContent } from '@/components/ui/card';
import { User, GraduationCap, HardHat, ShieldHalf, LandPlot, Users } from 'lucide-react';

const userGroups = [
  { icon: <User className="w-7 h-7" />, name: 'Citizens' },
  { icon: <GraduationCap className="w-7 h-7" />, name: 'Students' },
  { icon: <HardHat className="w-7 h-7" />, name: 'Farmers & Workers' },
  { icon: <ShieldHalf className="w-7 h-7" />, name: 'NGOs' },
  { icon: <LandPlot className="w-7 h-7" />, name: 'Govt. Help Centers' },
  { icon: <Users className="w-7 h-7" />, name: 'Policy & Research' },
];

export function AudienceSection() {
  return (
    <section className="py-16 sm:py-24 bg-muted">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-primary">
            Empowering Every Stakeholder
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            CivixAI is designed to serve a diverse range of users, from individual citizens to institutional partners, creating a connected civic ecosystem.
          </p>
        </div>
        <div className="mt-12 group relative">
          <div className="absolute -inset-px bg-gradient-to-r from-primary via-accent to-primary rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 group-hover:animate-gradient-pan bg-[length:200%_auto]" />
          <Card className="relative shadow-lg bg-card border-transparent transition-all duration-300 group-hover:bg-[radial-gradient(circle_at_center,_hsl(var(--primary)/0.15),_hsl(var(--card))_40%)]">
            <CardContent className="p-8 sm:p-10">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 text-center">
                {userGroups.map((group) => (
                  <div key={group.name} className="flex flex-col items-center gap-3">
                    <div className="text-primary">{group.icon}</div>
                    <p className="font-semibold text-foreground">{group.name}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
