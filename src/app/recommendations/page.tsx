'use client';

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { SearchX, Loader2, Sparkles, TrendingUp, ShieldCheck, Zap, Info, FileText, Globe, ExternalLink, ChevronDown, ChevronUp, ArrowRight, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { motion, AnimatePresence } from 'framer-motion';
import Chatbot from '@/components/Chatbot';
import { Input } from '@/components/ui/input';
import { ThreeDBackground } from '@/components/canvas/ThreeDBackground';
import { ScrollWrapper } from '@/components/animations/ScrollWrapper';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface APIResponse {
  success: boolean;
  eligibleSchemes?: string[];
  schemeDetails?: Array<{
    id?: string;
    name: string;
    eligible: boolean;
    confidence: number;
    threshold: number;
    benefit_score?: number;
    rank_score?: number;
    reasons?: string[];
    missing?: string[];
    description?: string;
    ministry?: string;
    level?: string;
    category?: string;
    states?: string;
    documents?: string;
    url?: string;
    benefit_type?: string;
  }>;
  topSchemes?: Array<{
    scheme: string;
    confidence: number;
    threshold: number;
  }>;
  mlPrediction?: boolean;
  mlFallback?: boolean;
  insights?: {
    locationInsights?: any;
    nlpSuggestions?: string[];
    clarifications?: string[];
  };
  error?: string;
}

function RecommendationsSkeleton() {
  return (
    <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

function CardSkeleton() {
  return (
    <Card className="overflow-hidden bg-white/5 border-white/10 backdrop-blur-xl">
      <div className="h-48 bg-gradient-to-br from-primary/10 to-purple-500/10 animate-pulse" />
      <CardContent className="p-6">
        <Skeleton className="h-8 w-3/4 mb-4 bg-white/10" />
        <Skeleton className="h-4 w-full mb-2 bg-white/10" />
        <Skeleton className="h-4 w-2/3 mb-4 bg-white/10" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20 bg-white/10" />
          <Skeleton className="h-8 w-20 bg-white/10" />
        </div>
      </CardContent>
    </Card>
  );
}

function DetailedSchemeCard({ scheme, index, details, onFeedback }: { scheme: any; index: number; details?: any; onFeedback: (schemeId: string, accepted: number) => void }) {
  const confidence = scheme.confidence || 50;
  const isEligible = scheme.eligible !== false;
  const priority = scheme.priority || 'medium';
  const [isExpanded, setIsExpanded] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<number | null>(null);

  const submitFeedback = (accepted: number) => {
    if (feedbackGiven !== null) return;
    setFeedbackGiven(accepted);
    onFeedback(scheme.id, accepted);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="group relative"
    >
      <Card className={`relative z-10 overflow-hidden transition-all duration-300 hover:-translate-y-1 bg-white/5 hover:bg-white/10 backdrop-blur-2xl border border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.3)] rounded-3xl ${priority === 'high' ? 'ring-1 ring-primary/50 shadow-primary/20' : priority === 'medium' ? 'ring-1 ring-white/20' : ''}`}>

        {/* Subtle top reflection for glass */}
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-white/0 via-white/20 to-white/0" />

        <CardHeader className="p-6 pb-2">
          <div className="flex justify-between items-start gap-4 p-1">
            <div className="space-y-2 flex-1">
              <div className="flex items-center flex-wrap gap-2">
                <Badge variant={isEligible ? "default" : "secondary"} className={isEligible ? "bg-green-500/20 text-green-300 border border-green-400/30 shadow-sm backdrop-blur-md" : "bg-red-500/20 text-red-300 border border-red-400/30"}>
                  <div className={`w-1.5 h-1.5 rounded-full mr-1.5 ${isEligible ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
                  {isEligible ? 'Eligible Match' : 'Check Criteria'}
                </Badge>
                <div className="text-[11px] font-bold tracking-widest uppercase text-slate-400 ml-1">
                  {details?.benefit_type === 'loan' ? 'Loan / Credit' : details?.benefit_type === 'insurance' ? 'Insurance / Pension' : details?.category || 'General'}
                </div>
              </div>

              <CardTitle className="text-xl md:text-2xl font-black leading-tight text-white line-clamp-2 group-hover:text-primary-foreground transition-colors group-hover:shadow-[0_0_15px_rgba(255,255,255,0.5)]">
                {details?.scheme_name || scheme.scheme_name}
              </CardTitle>
            </div>

            <div className={`flex flex-col items-center justify-center bg-black/40 backdrop-blur-md border border-white/10 shadow-inner rounded-2xl p-3 shrink-0 min-w-[80px] transition-all duration-300 ${priority === 'high' ? 'shadow-[0_0_15px_rgba(59,130,246,0.3)]' : ''}`}>
              <div className={`text-2xl md:text-3xl font-black ${confidence > 80 ? 'text-transparent bg-clip-text bg-gradient-to-br from-blue-300 to-purple-400' : 'text-slate-300'}`}>
                {Math.round(confidence)}<span className="text-sm opacity-50">%</span>
              </div>
              <div className="text-[9px] uppercase tracking-widest font-black text-slate-500 mt-1">Match</div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-6 pt-2 space-y-5">
          {details?.ministry && (
            <div className="text-xs font-semibold text-slate-400 mb-2">
              Ministry: {details.ministry} {details.level ? `(${details.level})` : ''}
            </div>
          )}
          <p className="text-[15px] text-slate-300 leading-relaxed line-clamp-3">
            {details?.summary || 'AI has analyzed this scheme based on your profile and found a strong correlation with your current status. Detailed benefits are currently unavailable.'}
          </p>

          <div className="flex items-center gap-4 py-3 px-4 bg-black/20 backdrop-blur-sm rounded-2xl border border-white/5 shadow-inner">
            <div className="flex-1 space-y-2">
              <div className="flex justify-between items-end">
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Plausibility</span>
                <span className="text-xs font-bold text-blue-300">{Math.round(confidence)}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800/80 rounded-full overflow-hidden border border-white/5">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full"
                  style={{ width: `${Math.round(confidence)}%` }}
                />
              </div>
            </div>
            {scheme.benefit_score !== undefined && (
              <div className="px-3 py-1.5 bg-green-500/20 backdrop-blur-md rounded-xl border border-green-400/30 flex flex-col items-center justify-center shrink-0">
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3 text-green-300" />
                  <span className="text-sm font-black text-green-300">+{Number(scheme.benefit_score).toFixed(1)}</span>
                </div>
                <div className="text-[9px] uppercase font-bold text-green-400/70">Impact</div>
              </div>
            )}
          </div>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="pt-4 border-t border-white/10 space-y-4"
              >
                <Accordion type="single" collapsible className="w-full">
                  <AccordionItem value="reasoning" className="border-none">
                    <AccordionTrigger className="py-2 hover:no-underline text-white">
                      <div className="flex items-center gap-2 text-blue-300">
                        <Zap className="h-4 w-4" />
                        <span className="text-sm font-bold uppercase tracking-tight">AI Reasoning</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="text-sm space-y-2 bg-black/40 p-3 rounded-xl border border-white/5 text-slate-300">
                      {scheme.reasons && scheme.reasons.length > 0 ? (
                        <ul className="space-y-1">
                          {scheme.reasons.map((r: string, i: number) => (
                            <li key={i} className="flex gap-2">
                              <ShieldCheck className="h-4 w-4 shrink-0 text-green-400" />
                              <span>{r}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p>Matches your demographics and socioeconomic status.</p>
                      )}
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="details" className="border-none">
                    <AccordionTrigger className="py-2 hover:no-underline text-white">
                      <div className="flex items-center gap-2 text-slate-300">
                        <FileText className="h-4 w-4" />
                        <span className="text-sm font-bold uppercase tracking-tight">Requirements</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="text-sm space-y-4 pt-2 text-slate-300">
                      {details?.benefits_snippets?.length > 0 && (
                        <div className="bg-black/20 p-3 rounded-xl border border-white/5">
                          <div className="font-bold text-white mb-1">Key Benefits</div>
                          <div className="opacity-90">{details.benefits_snippets[0]}</div>
                        </div>
                      )}
                      {details?.documents_snippets?.length > 0 && (
                        <div className="bg-black/20 p-3 rounded-xl border border-white/5">
                          <div className="font-bold text-white mb-1">Documents Needed</div>
                          <div className="opacity-90">{details.documents_snippets[0]}</div>
                        </div>
                      )}
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>

                <div className="flex gap-3 pt-2">
                  <Button className="flex-1 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-[0_0_15px_rgba(59,130,246,0.4)] border-none" size="sm" asChild>
                    <a href={details?.source_url || '#'} target="_blank">
                      Apply Now <ExternalLink className="ml-1.5 h-3.5 w-3.5" />
                    </a>
                  </Button>
                  <Button variant="outline" size="sm" className="rounded-xl border-white/20 bg-white/5 backdrop-blur-sm hover:bg-white/10 text-white" asChild>
                    <Link href={`/scheme/${scheme.id}`}>Full Analysis</Link>
                  </Button>
                  <div className="flex items-center gap-1 border border-white/10 p-0.5 rounded-xl bg-black/20">
                    <Button size="icon" variant="ghost" className={`h-8 w-8 rounded-lg ${feedbackGiven === 1 ? 'text-green-400 bg-green-500/20' : 'text-slate-400 hover:text-green-400 hover:bg-green-500/20'}`} onClick={(e) => { e.preventDefault(); submitFeedback(1); }}>
                      <ThumbsUp className="h-4 w-4" />
                    </Button>
                    <Button size="icon" variant="ghost" className={`h-8 w-8 rounded-lg ${feedbackGiven === 0 ? 'text-red-400 bg-red-500/20' : 'text-slate-400 hover:text-red-400 hover:bg-red-500/20'}`} onClick={(e) => { e.preventDefault(); submitFeedback(0); }}>
                      <ThumbsDown className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>

        <CardFooter className="p-3 bg-black/20 border-t border-white/10">
          <Button
            variant="ghost"
            className="w-full h-10 rounded-xl text-xs font-bold text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Hide Details' : 'View AI Reasoning & Criteria'}
            {isExpanded ? <ChevronUp className="ml-1.5 h-4 w-4" /> : <ChevronDown className="ml-1.5 h-4 w-4" />}
          </Button>
        </CardFooter>
      </Card>
      {/* Decorative background glow behind the card on hover */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 blur-xl transition-opacity duration-500 rounded-3xl -z-10" />
    </motion.div>
  );
}

function TopMatchHero({ scheme, details }: { scheme: any; details?: any }) {
  if (!scheme) return null;

  return (
    <Card className="mb-10 overflow-hidden shadow-[0_0_40px_rgba(59,130,246,0.3)] bg-gradient-to-br from-slate-900 via-[#0a1128] to-[#1a0b2e] border border-white/10 text-white rounded-[2.5rem]">
      <div className="relative p-8 md:p-12 overflow-hidden">
        {/* Animated Background Decor */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-blue-500/20 rounded-full blur-[80px]" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 bg-purple-500/20 rounded-full blur-[80px]" />

        <div className="relative z-10 grid md:grid-cols-2 gap-8 items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-xl text-xs font-black uppercase tracking-widest text-blue-300 border border-white/10 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
              <Sparkles className="h-3.5 w-3.5 text-blue-300 fill-blue-300 animate-pulse" />
              Top AI Prediction
            </div>

            <h2 className="text-4xl md:text-6xl font-black leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-blue-200">
              {details?.scheme_name || scheme.scheme_name}
            </h2>

            <p className="text-lg text-slate-300 leading-relaxed line-clamp-3">
              {details?.ministry && <strong className="block mb-2 text-sm text-blue-300">{details.ministry}</strong>}
              {details?.summary || `A highly recommended ${scheme.category || 'governmental'} scheme tailored for your profile based on socio-economic trends and recent policy updates.`}
            </p>

            <div className="flex flex-wrap gap-4 pt-4">
              <div className="bg-white text-slate-900 px-7 py-3.5 rounded-2xl font-black text-sm hover:scale-105 hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] transition-all flex items-center cursor-pointer">
                Apply Immediately <ArrowRight className="ml-2 h-4 w-4" />
              </div>
              <div className="bg-white/5 backdrop-blur-xl text-white border border-white/10 px-7 py-3.5 rounded-2xl font-bold text-sm hover:bg-white/10 transition-all cursor-pointer">
                Save for Later
              </div>
            </div>
          </div>

          <div className="flex justify-center md:justify-end">
            <div className="relative group perspective-1000">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full blur-[60px] opacity-30 group-hover:opacity-50 transition-opacity duration-1000 animate-pulse" />
              <div className="relative w-56 h-56 md:w-72 md:h-72 rounded-full border border-white/20 shadow-[inset_0_0_40px_rgba(255,255,255,0.1)] backdrop-blur-2xl flex flex-col items-center justify-center p-8 text-center bg-black/40 transform transition-transform duration-500 group-hover:scale-105 group-hover:rotate-3">
                <div className="absolute inset-0 rounded-full border border-dashed border-white/20 animate-[spin_60s_linear_infinite]" />
                <div className="text-xl font-bold text-slate-400 mb-1 z-10 uppercase tracking-widest text-[10px]">Plausibility Score</div>
                <div className="text-7xl md:text-8xl font-black z-10 text-transparent bg-clip-text bg-gradient-to-br from-blue-300 to-purple-400 drop-shadow-lg">{Math.round(scheme.confidence)}<span className="text-2xl md:text-4xl opacity-50">%</span></div>
                <div className="mt-3 px-4 py-1.5 rounded-full bg-green-500/20 border border-green-500/30 text-[10px] font-black uppercase text-green-300 shadow-[0_0_15px_rgba(34,197,94,0.3)] z-10 backdrop-blur-md">
                  High Success
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

function RecommendationsContent() {
  const searchParams = useSearchParams();
  const [apiData, setApiData] = useState<APIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [minConfidence, setMinConfidence] = useState(0);
  const [isExporting, setIsExporting] = useState(false);

  const handleFeedback = async (schemeId: string, accepted: number) => {
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scheme_id: schemeId,
          accepted: accepted
        })
      });
    } catch (e) {
      console.error("Failed to submit feedback", e);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const getParam = (key: string) => searchParams?.get(key);
        const toBool = (value?: string | null) => value === 'true';
        const toNum = (value?: string | null) => {
          if (value === undefined || value === null || value === '') return undefined;
          const n = Number(value);
          return isNaN(n) ? undefined : n;
        };

        // Prepare the request data for ML eligibility API
        const requestData = {
          age: toNum(getParam('age')),
          income: toNum(getParam('income')),
          state: getParam('state') || undefined,
          category: getParam('category') || undefined,
          occupation: getParam('occupation') || undefined,
          gender: getParam('gender') || undefined,
          hasDisability: toBool(getParam('hasDisability')),
          hasLand: toBool(getParam('hasLand')),
          familyIncome: toNum(getParam('familyIncome')) || 0,
          landSize: toNum(getParam('landSize')) || 0,
          familySize: toNum(getParam('familySize')) || 1,
          isSingleGirlChild: toBool(getParam('isSingleGirlChild')),
          isWidowOrSenior: toBool(getParam('isWidowOrSenior')),
          isTaxPayer: toBool(getParam('isTaxPayer')),
          isBankLinked: toBool(getParam('isBankLinked')),
          educationLevel: getParam('educationLevel') || '',
          digitalLiteracy: getParam('digitalLiteracy') || '',
          urbanRural: getParam('urbanRural') || '',
          monthlyExpenses: toNum(getParam('monthlyExpenses')) || 0,
          hasSmartphone: toBool(getParam('hasSmartphone')),
          hasInternet: toBool(getParam('hasInternet')),
          employmentType: getParam('employmentType') || '',
          skillCertification: getParam('skillCertification') || '',
          loanRequirement: getParam('loanRequirement') || 'none',
          monthlySavings: toNum(getParam('monthlySavings')) || 0,
          hasInsurance: toBool(getParam('hasInsurance')),
          hasPension: toBool(getParam('hasPension'))
        };

        // Call the ML eligibility API
        const response = await fetch('/api/check-eligibility', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
        });

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        setApiData(data);
      } catch (err) {
        console.error('Error fetching recommendations:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchParams]);

  const latestSources: any[] = []; // Placeholder for now


  const handleExport = () => {
    setIsExporting(true);
    try {
      const payload = filteredSchemes.map(s => ({
        id: s.id,
        confidence: s.confidence,
        priority: s.priority,
        eligible: s.eligible,
        details: structuredById.get(s.id) || null
      }));
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'eligible_schemes.json';
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
    }
  };

  const normalizeConfidence = (value?: number) => {
    if (typeof value !== 'number') return 50;
    return value <= 1 ? value * 100 : value;
  };

  const toPriority = (confidence: number, rankScore?: number) => {
    // Make 'High Priority' much more selective
    if (confidence >= 90) return 'high';
    if (confidence >= 75) return 'medium';
    return 'low';
  };

  const toSlug = (text: string) =>
    (text || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 60) || 'scheme';

  const structuredById = useMemo(() => {
    if (!apiData?.schemeDetails) return new Map();
    return new Map(
      apiData.schemeDetails.map(s => [
        s.id || toSlug(s.name || ''),
        {
          scheme_name: s.name,
          source_url: s.url,
          summary: s.description,
          ministry: s.ministry,
          level: s.level,
          category: s.category,
          benefit_type: s.benefit_type || 'scheme',
          benefits_snippets: s.description ? [s.description] : [],
          documents_snippets: s.documents ? [s.documents] : []
        }
      ])
    );
  }, [apiData]);

  type ModelItem = {
    key: string;
    name?: string;
    eligible: boolean;
    confidence?: number;
    benefit_score?: number;
    rank_score?: number;
    reasons?: string[];
    threshold?: number;
  };

  const modelItems: ModelItem[] =
    apiData?.schemeDetails && apiData.schemeDetails.length > 0
      ? apiData.schemeDetails.map(item => ({
        key: item.id || item.name || 'Unknown Scheme',
        name: item.name,
        eligible: item.eligible,
        confidence: item.confidence,
        benefit_score: item.benefit_score,
        rank_score: item.rank_score,
        reasons: item.reasons,
        threshold: item.threshold
      }))
      : apiData?.topSchemes && apiData.topSchemes.length > 0
        ? apiData.topSchemes.map(item => ({
          key: toSlug(item.scheme),
          name: item.scheme,
          eligible: true,
          confidence: item.confidence,
          threshold: item.threshold
        }))
        : (apiData?.eligibleSchemes || []).map(name => ({
          key: toSlug(name),
          name: name,
          eligible: true
        }));

  const schemes = modelItems.map(item => {
    const schemeName = item.name || item.key;
    const confidence = normalizeConfidence(item.confidence);
    const eligible = item.eligible !== false;
    return {
      id: item.key,
      scheme_name: schemeName,
      confidence,
      benefit_score: item.benefit_score,
      rank_score: item.rank_score,
      reasons: item.reasons,
      priority: eligible ? toPriority(confidence) : 'low',
      eligible
    };
  });

  const dedupedSchemes = Array.from(
    new Map(schemes.map(s => [s.id, s])).values()
  );

  const rankedSchemes = dedupedSchemes
    .sort((a, b) => (b.confidence || 0) - (a.confidence || 0));

  const eligibleOnlySchemes = rankedSchemes.filter(s => s.eligible);

  const filteredSchemes = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return eligibleOnlySchemes.filter(s => {
      if (s.confidence < minConfidence) return false;
      if (!q) return true;
      const details = structuredById.get(s.id);
      const name = (details?.scheme_name || s.scheme_name || '').toLowerCase();
      const summary = (details?.summary || '').toLowerCase();
      return name.includes(q) || summary.includes(q);
    });
  }, [eligibleOnlySchemes, minConfidence, searchQuery, structuredById]);

  // Base Categories for the new specific filtering (Schemes vs Loans vs Insurance)
  const [activeTab, setActiveTab] = useState(() => {
    return searchParams?.get('type') || 'All';
  });

  const finalSchemes = useMemo(() => {
    return filteredSchemes.filter(s => {
      if (activeTab === 'All') return true;
      const d = structuredById.get(s.id);

      // Match the specific benefit classification
      const benefitType = d?.benefit_type || 'scheme';

      if (activeTab === 'scheme' && benefitType === 'scheme') return true;
      if (activeTab === 'loan' && benefitType === 'loan') return true;
      if (activeTab === 'insurance' && benefitType === 'insurance') return true;

      // Fallback for specific categories if the tab doesn't match the 3 main types
      if (activeTab !== 'scheme' && activeTab !== 'loan' && activeTab !== 'insurance') {
        return d?.category === activeTab;
      }
      return false;
    });
  }, [filteredSchemes, activeTab, structuredById]);

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <Header />
        <main className="flex-grow bg-muted">
          <section className="container mx-auto px-4 py-10 sm:py-14">
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
              </div>
              <h1 className="font-headline text-4xl sm:text-5xl font-bold text-primary">Analyzing Your Profile</h1>
              <p className="mt-4 max-w-2xl mx-auto text-lg text-muted-foreground">
                Our AI is processing your information to find the best government schemes for you...
              </p>
            </div>
            <RecommendationsSkeleton />
          </section>
        </main>
        <Chatbot />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <Header />
        <main className="flex-grow bg-muted">
          <section className="container mx-auto px-4 py-10 sm:py-14">
            <div className="flex flex-col items-center justify-center text-center py-20">
              <Alert className="max-w-lg bg-card/60 backdrop-blur-md">
                <SearchX className="h-4 w-4" />
                <AlertTitle className="font-headline">Error Loading Recommendations</AlertTitle>
                <AlertDescription>
                  {error}
                </AlertDescription>
              </Alert>
              <Button asChild variant="link" className="mt-4">
                <Link href="/check-eligibility">Try again</Link>
              </Button>
            </div>
          </section>
        </main>
        <Chatbot />
      </div>
    );
  }

  const topScheme = rankedSchemes[0];
  const highPriorityCount = rankedSchemes.filter(s => s.priority === 'high').length;

  if (!apiData?.success || eligibleOnlySchemes.length === 0) {
    return (
      <div className="flex flex-col min-h-screen bg-transparent font-sans text-slate-200">
        <ThreeDBackground />
        <Header />
        <ScrollWrapper>
          <main className="flex-grow relative overflow-hidden">
            {/* Ambient Dark Mode Globs */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-red-500/10 rounded-full blur-[120px] pointer-events-none" />

            <section className="container mx-auto px-4 py-10 sm:py-14 relative z-10">
              <div className="flex flex-col items-center justify-center text-center py-20">
                <div className="bg-white/5 border border-white/10 backdrop-blur-2xl p-12 rounded-3xl shadow-2xl space-y-6 max-w-2xl">
                  <div className="w-24 h-24 bg-red-500/10 rounded-full flex items-center justify-center mx-auto border border-red-500/20">
                    <SearchX className="h-12 w-12 text-red-400" />
                  </div>
                  <div className="space-y-3">
                    <h2 className="text-4xl font-black text-white">No Schemes Found</h2>
                    <p className="text-slate-400 text-lg">
                      Our AI models scanned all active governmental databases but could not find a scheme matching your precise demographic profile constraints. Try adjusting your inputs.
                    </p>
                  </div>
                  <Button asChild className="w-full py-7 text-lg bg-white text-black hover:bg-slate-200 font-bold rounded-2xl" size="lg">
                    <Link href="/check-eligibility">Refine My Profile</Link>
                  </Button>
                </div>
              </div>
            </section>
          </main>
        </ScrollWrapper>
        <Chatbot />
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-transparent font-sans selection:bg-blue-500/30 text-white">
      <ThreeDBackground />
      <Header />
      <ScrollWrapper>
        <main className="flex-grow relative overflow-hidden">
          {/* Glass background blobs removed since we have 3D WebGL */}
          <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/10 rounded-full blur-[120px] -z-10 animate-pulse" style={{ animationDuration: '6s', animationDelay: '1s' }} />
          <div className="fixed top-[40%] right-[10%] w-[30%] h-[30%] bg-cyan-600/10 rounded-full blur-[100px] -z-10" />

          <section className="container mx-auto px-4 py-10 sm:py-14 relative z-10">

            <div className="gsap-animate">
              <TopMatchHero scheme={topScheme} details={structuredById.get(topScheme?.id)} />
            </div>

            <div className="mb-12 gsap-animate">
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b border-white/5">
                <div className="space-y-2">
                  <h1 className="text-5xl font-black text-white tracking-tight">AI Selection Hub</h1>
                  <p className="text-slate-400 text-lg">We've filtered {schemes.length} total schemes to find these <span className="font-bold text-blue-400 border-b border-blue-400/30 pb-0.5">{eligibleOnlySchemes.length} prime matches</span>.</p>
                </div>

                <div className="flex gap-4">
                  <div className="bg-white/5 backdrop-blur-xl px-6 py-4 rounded-3xl shadow-[0_8px_32px_0_rgba(0,0,0,0.36)] border border-white/10 flex flex-col items-center justify-center min-w-[130px] hover:scale-105 transition-transform">
                    <span className="text-4xl font-black text-blue-400 drop-shadow-[0_0_10px_rgba(96,165,250,0.5)]">{highPriorityCount}</span>
                    <span className="text-[11px] font-black uppercase tracking-widest text-slate-500 mt-1 text-center">High Priority</span>
                  </div>
                  <div className="bg-white/5 backdrop-blur-xl px-6 py-4 rounded-3xl shadow-[0_8px_32px_0_rgba(0,0,0,0.36)] border border-white/10 flex flex-col items-center justify-center min-w-[130px] hover:scale-105 transition-transform">
                    <span className="text-4xl font-black text-green-400 drop-shadow-[0_0_10px_rgba(74,222,128,0.3)]">{eligibleOnlySchemes.length}</span>
                    <span className="text-[11px] font-black uppercase tracking-widest text-slate-500 mt-1 text-center">Total Eligible</span>
                  </div>
                </div>
              </div>

              <Tabs defaultValue={activeTab} onValueChange={setActiveTab} className="w-full">
                <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-8">
                  <TabsList className="h-auto bg-white/5 backdrop-blur-xl border border-white/10 shadow-lg p-1.5 rounded-2xl w-full md:w-auto overflow-x-auto">
                    <TabsTrigger value="All" className="rounded-xl py-2.5 px-6 font-bold text-slate-400 data-[state=active]:bg-white/10 data-[state=active]:text-white data-[state=active]:shadow-sm transition-all focus:ring-0">
                      All Results
                    </TabsTrigger>
                    <TabsTrigger value="scheme" className="rounded-xl py-2.5 px-6 font-bold text-slate-400 data-[state=active]:bg-white/10 data-[state=active]:text-white data-[state=active]:shadow-sm transition-all focus:ring-0">
                      Govt Schemes
                    </TabsTrigger>
                    <TabsTrigger value="loan" className="rounded-xl py-2.5 px-6 font-bold text-orange-400/70 data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-300 data-[state=active]:shadow-sm transition-all focus:ring-0">
                      Loans & Credit
                    </TabsTrigger>
                    <TabsTrigger value="insurance" className="rounded-xl py-2.5 px-6 font-bold text-purple-400/70 data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300 data-[state=active]:shadow-sm transition-all focus:ring-0">
                      Insurance & Pension
                    </TabsTrigger>
                  </TabsList>

                  <div className="relative w-full md:w-80 group">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur opacity-0 group-hover:opacity-30 transition duration-500" />
                    <Input
                      placeholder="Search your matches..."
                      className="relative pl-5 h-14 rounded-2xl bg-black/40 backdrop-blur-xl border-white/10 text-white placeholder:text-slate-500 focus-visible:ring-blue-500/50 focus-visible:border-blue-500/50"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
                  <AnimatePresence mode="popLayout">
                    {finalSchemes.slice(0, 50).map((scheme, index) => (
                      <DetailedSchemeCard
                        key={scheme.id}
                        scheme={scheme}
                        index={index}
                        details={structuredById.get(scheme.id)}
                        onFeedback={handleFeedback}
                      />
                    ))}
                  </AnimatePresence>
                </div>

                {finalSchemes.length === 0 && (
                  <div className="text-center py-20 bg-white/5 rounded-3xl border border-white/10 backdrop-blur-md">
                    <p className="text-slate-400">No schemes found in this category. Please check another tab.</p>
                  </div>
                )}
              </Tabs>
            </div>

            {/* AI Insights & Footer Controls */}
            <div className="grid gap-6 lg:grid-cols-3 mt-12">
              <Card className="gsap-animate lg:col-span-2 bg-gradient-to-br from-blue-900/20 to-purple-900/10 border-white/10 backdrop-blur-xl p-8 rounded-3xl shadow-[0_8px_32px_0_rgba(0,0,0,0.36)]">
                <div className="flex items-center gap-3 mb-6">
                  <Sparkles className="h-8 w-8 text-blue-400" />
                  <h3 className="text-3xl font-black text-white">AI Strategy Summary</h3>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <div className="font-bold text-blue-300 flex items-center gap-2">
                      <Zap className="h-4 w-4" /> Next Steps
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">
                      Based on predictive modeling, your best course of action is to immediately apply for <strong>{topScheme?.scheme_name}</strong>, as it has historically fast approval rates for your demographic.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <div className="font-bold text-purple-300 flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4" /> Smart Tip
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">
                      Ensure your Aadhar is firmly linked to your bank account. Our AI detected {eligibleOnlySchemes.filter(s => s.id.includes('dbt')).length || 3} schemes operating via DBT (Direct Benefit Transfer).
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="gsap-animate p-8 rounded-3xl bg-white/5 backdrop-blur-xl border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.36)] flex flex-col justify-center gap-6">
                <div>
                  <h4 className="text-xl font-black mb-1 text-white">Actions</h4>
                  <p className="text-sm text-slate-400">Manage your eligibility results</p>
                </div>
                <div className="space-y-3">
                  <Button onClick={handleExport} className="w-full py-6 rounded-2xl bg-white text-black hover:bg-slate-200 font-bold" variant="default">
                    Download PDF Report
                  </Button>
                  <Button asChild variant="outline" className="w-full py-6 rounded-2xl border-white/20 text-white hover:bg-white/10 hover:text-white bg-transparent">
                    <Link href="/check-eligibility">Refresh My Profile</Link>
                  </Button>
                </div>
              </Card>
            </div>
          </section>
        </main>
      </ScrollWrapper>
      <Chatbot context={finalSchemes} />
    </div>
  );
}

export default function RecommendationsPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col min-h-screen bg-background">
        <Header />
        <main className="flex-grow bg-muted">
          <section className="container mx-auto px-4 py-10 sm:py-14">
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
              </div>
              <h1 className="font-headline text-4xl sm:text-5xl font-bold text-primary">Analyzing Your Profile</h1>
              <p className="mt-4 max-w-2xl mx-auto text-lg text-muted-foreground">
                Our AI is processing your information to find the best government schemes for you...
              </p>
            </div>
            <RecommendationsSkeleton />
          </section>
        </main>
        <Chatbot />
      </div>
    }>
      <RecommendationsContent />
    </Suspense>
  );
}
