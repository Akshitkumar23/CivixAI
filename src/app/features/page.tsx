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

export default function FeaturesPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <Header />
      <main className="flex-grow">
        <div className="py-16 sm:py-24 bg-muted">
            <div className="container mx-auto px-4 text-center">
                 <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-primary tracking-tight">
                    A Deep Dive into CivixAI's Features
                </h1>
                <p className="mt-4 max-w-3xl mx-auto text-lg text-muted-foreground sm:text-xl">
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
