import { Header } from '@/components/Header';
import { FeaturesSection } from '@/components/landing/FeaturesSection';
import { SchemeComparisonSection } from '@/components/landing/SchemeComparisonSection';
import { DocumentChecklistSection } from '@/components/landing/DocumentChecklistSection';
import { BeyondSchemesSection } from '@/components/landing/BeyondSchemesSection';
import { LocationIntelligenceSection } from '@/components/landing/LocationIntelligenceSection';
import { ExplainableAISection } from '@/components/landing/ExplainableAISection';
import { AccessibilitySection } from '@/components/landing/AccessibilitySection';
import { AudienceSection } from '@/components/landing/AudienceSection';
import { ImpactMetricsSection } from '@/components/landing/ImpactMetricsSection';
import { RoadmapSection } from '@/components/landing/RoadmapSection';
import { Footer } from '@/components/landing/Footer';
import Chatbot from '@/components/Chatbot';
import { FinalCTASection } from '@/components/landing/FinalCTASection';
import { FeaturesHighlightSection } from '@/components/landing/FeaturesHighlightSection';
import { FeaturesBannerBackground } from '@/components/canvas/FeaturesBannerBackground';
import { ClientScrollRestorer } from '@/components/ClientScrollRestorer';

export default function FeaturesPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[#020205] text-slate-200">
      <ClientScrollRestorer />
      <Header />
      <main className="flex-grow">

        {/* Features Page Hero Banner with 3D Wave */}
        <div className="relative py-20 sm:py-32 overflow-hidden bg-[#020205] border-b border-white/10 flex items-center justify-center min-h-[50vh]">

          {/* The 3D Wave Interactive Map */}
          <FeaturesBannerBackground />

          {/* Dark overlay gradients for text readability and fading out at bottom */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#020205]/60 via-[#050510]/30 to-[#020205] pointer-events-none" />

          {/* Content */}
          <div className="container mx-auto px-4 text-center relative z-10">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-emerald-300 text-sm font-medium mb-6 backdrop-blur-md shadow-lg shadow-emerald-500/10">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              Civic Data Grid
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-white tracking-tight drop-shadow-2xl">
              A Deep Dive into <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-[#10b981]">CivixAI's Features</span>
            </h1>
            <p className="mt-8 max-w-3xl mx-auto text-lg text-slate-300 sm:text-xl font-medium drop-shadow-md">
              Explore the powerful, intelligent tools we've built to bring clarity and confidence to your search for government benefits.
            </p>
          </div>
        </div>

        <FeaturesHighlightSection />
        <FeaturesSection />
        <SchemeComparisonSection />
        <DocumentChecklistSection />
        <ExplainableAISection />
        <BeyondSchemesSection />
        <LocationIntelligenceSection />
        <AccessibilitySection />
        <AudienceSection />
        <ImpactMetricsSection />
        <RoadmapSection />
        <FinalCTASection />
      </main>
      <Footer />
      <Chatbot />
    </div>
  );
}
