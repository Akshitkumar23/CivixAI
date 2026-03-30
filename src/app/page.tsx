'use client';

import { Header } from '@/components/Header';
import { HeroSection } from '@/components/landing/HeroSection';
import { ProblemSection } from '@/components/landing/ProblemSection';
import { HowItWorksSection } from '@/components/landing/HowItWorksSection';
import { BeforeAfterSection } from '@/components/landing/BeforeAfterSection';
import { FinalCTASection } from '@/components/landing/FinalCTASection';
import { Footer } from '@/components/landing/Footer';
import Chatbot from '@/components/Chatbot';
import { FeaturesHighlightSection } from '@/components/landing/FeaturesHighlightSection';
import { CoreAIHeroBackground } from '@/components/canvas/CoreAIHeroBackground';
import { useScrollRestoration } from '@/hooks/use-scroll-restoration';

export default function LandingPage() {
  useScrollRestoration();
  return (
    <div className="flex flex-col min-h-screen relative bg-[#020205] text-slate-200">
      {/* Global 3D Universe Background */}
      <div className="fixed inset-0 z-0 opacity-80 pointer-events-none">
        <CoreAIHeroBackground />
      </div>

      {/* Subtle overlay to ensure text is readable */}
      <div className="fixed inset-0 z-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-900/10 via-[#050510]/60 to-[#020205]/90 pointer-events-none" />

      <div className="relative z-10 flex flex-col min-h-screen">
        <Header />
        <main className="flex-grow">
          <HeroSection />
          <ProblemSection />
          <HowItWorksSection />
          <FeaturesHighlightSection />
          <BeforeAfterSection />
          <FinalCTASection />
        </main>
        <Footer />
        <Chatbot />
      </div>
    </div>
  );
}
