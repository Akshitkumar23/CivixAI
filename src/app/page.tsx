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

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
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
  );
}
