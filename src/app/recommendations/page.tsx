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
    missing_inputs?: string[];
    description?: string;
    ministry?: string;
    level?: string;
    category?: string;
    states?: string;
    documents?: string;
    url?: string;
    source_url?: string;
    benefit_type?: string;
    benefit_amount?: string;
    tags?: string;
    application_deadline?: string;
    processing_time?: string;
    popularity_score?: string;
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

function DetailedSchemeCard({
  scheme, index, details, onFeedback, isInCompare, onToggleCompare
}: {
  scheme: any; index: number; details?: any;
  onFeedback: (schemeId: string, accepted: number) => void;
  isInCompare: boolean;
  onToggleCompare: (scheme: any, details?: any) => void;
}) {
  const confidence = scheme.confidence || 50;
  const isEligible = scheme.eligible !== false;
  const benefitAmount = scheme.benefit_amount;
  const [feedbackGiven, setFeedbackGiven] = useState<number | null>(null);

  const submitFeedback = (accepted: number) => {
    if (feedbackGiven !== null) return;
    setFeedbackGiven(accepted);
    onFeedback(scheme.id, accepted);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.25, delay: Math.min(index * 0.04, 0.4), ease: 'easeOut' }}
      className="group relative h-full"
      layout
    >
      <Card className="relative flex flex-col h-full overflow-hidden bg-[#0a0a0b]/80 border-white/5 shadow-none hover:bg-[#121214]/90 transition-all duration-300 rounded-2xl">
        <CardHeader className="p-5 pb-3">
          <div className="flex justify-between items-start gap-4">
            <div className="space-y-3 flex-1">
              <div className="flex items-center flex-wrap gap-2">
                {isEligible ? (
                  <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20 text-xs px-2.5 py-0.5 rounded-full font-medium">
                    <div className="w-1.5 h-1.5 rounded-full mr-1.5 bg-green-400" />
                    Eligible Match
                  </Badge>
                ) : (
                  <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20 text-xs px-2.5 py-0.5 rounded-full font-medium">
                    Check Criteria
                  </Badge>
                )}
                <span className="text-xs font-semibold text-slate-500">
                  {details?.benefit_type === 'loan' ? 'Loan / Credit' : details?.benefit_type === 'insurance' ? 'Insurance / Pension' : details?.category || 'General'}
                </span>
              </div>

              <CardTitle className="text-xl font-bold leading-tight text-white line-clamp-2">
                {details?.scheme_name || scheme.scheme_name}
              </CardTitle>
              {benefitAmount && (
                <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full w-fit">
                  <span className="text-emerald-300">₹</span> {benefitAmount}
                </div>
              )}
              {details?.popularity_score && (
                <div className="flex items-center gap-1.5 text-[10px] font-bold text-amber-400 bg-amber-400/5 border border-amber-400/10 px-2.5 py-1 rounded-full w-fit">
                  <TrendingUp className="h-3 w-3" />
                  Score: {details.popularity_score}
                </div>
              )}
            </div>

            <div className="flex flex-col items-end shrink-0">
              <div className={`text-2xl font-bold ${confidence > 80 ? 'text-blue-400' : 'text-slate-300'}`}>
                {Math.round(confidence)}%
              </div>
              <div className="text-xs text-slate-500 font-medium">Match</div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-5 pt-2 flex-grow">
          <p className="text-sm text-slate-400 leading-relaxed line-clamp-3">
            {details?.summary || 'AI has analyzed this scheme based on your profile and found a strong correlation with your current status.'}
          </p>

          <div className="flex flex-wrap gap-2 mt-4 pt-1">
            {details?.application_deadline && (
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-red-300 bg-red-400/10 border border-red-500/20 px-2 py-1 rounded-lg">
                <span className="opacity-70">ENDS</span> {details.application_deadline}
              </div>
            )}
            {details?.processing_time && (
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-blue-300 bg-blue-400/10 border border-blue-500/20 px-2 py-1 rounded-lg">
                <span className="opacity-70">WAIT</span> {details.processing_time}
              </div>
            )}
          </div>

          {scheme.missing_inputs && scheme.missing_inputs.length > 0 && confidence < 100 && (
            <div className="mt-4 p-3 rounded-xl bg-orange-500/10 border border-orange-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-bold text-orange-400 tracking-wide uppercase">Boost Match Score 🚀</span>
                <Link href="/check-eligibility" className="text-[10px] font-semibold text-orange-300 hover:text-white underline">Edit Profile</Link>
              </div>
              <p className="text-[10px] text-orange-300/80 mb-2 leading-snug">Add these details to verify 100% eligibility:</p>
              <div className="flex flex-wrap gap-1.5">
                {scheme.missing_inputs.map((input: string) => (
                  <span key={input} className="text-[9px] px-1.5 py-0.5 rounded-md flex items-center gap-1 bg-orange-500/20 text-orange-300 border border-orange-500/30">
                    <Zap className="h-2 w-2" /> {input}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>

        <CardFooter className="p-5 pt-0 mt-auto flex flex-wrap gap-3">
          <Button className="flex-1 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium border-0" size="sm" asChild>
            <a href={details?.url || details?.source_url || '#'} target="_blank">
              Apply Now <ExternalLink className="ml-1.5 h-3.5 w-3.5" />
            </a>
          </Button>
          <Button variant="outline" size="sm" className="rounded-xl border-white/10 bg-[#121214] hover:bg-white/5 text-white" asChild>
            <Link href={`/scheme/${scheme.id}`}>Details</Link>
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className={`rounded-xl px-3 border ${
              isInCompare
                ? 'border-blue-500/50 text-blue-400 bg-blue-500/10 hover:bg-blue-500/20'
                : 'border-white/10 text-slate-400 hover:text-white hover:bg-white/5'
            } transition-all`}
            onClick={() => onToggleCompare(scheme, details)}
          >
            {isInCompare ? '✓ Comparing' : '⇄ Compare'}
          </Button>
          <div className="flex items-center gap-1 border border-white/10 p-1 rounded-xl bg-[#121214]">
            <Button size="icon" variant="ghost" className={`h-8 w-8 rounded-lg ${feedbackGiven === 1 ? 'text-green-400 bg-green-500/10' : 'text-slate-400 hover:text-green-400 hover:bg-green-500/10'}`} onClick={(e) => { e.preventDefault(); submitFeedback(1); }}>
              <ThumbsUp className="h-4 w-4" />
            </Button>
            <Button size="icon" variant="ghost" className={`h-8 w-8 rounded-lg ${feedbackGiven === 0 ? 'text-red-400 bg-red-500/10' : 'text-slate-400 hover:text-red-400 hover:bg-red-500/10'}`} onClick={(e) => { e.preventDefault(); submitFeedback(0); }}>
              <ThumbsDown className="h-4 w-4" />
            </Button>
          </div>
        </CardFooter>
      </Card>
    </motion.div>
  );
}

function TopMatchHero({ scheme, details }: { scheme: any; details?: any }) {
  if (!scheme) return null;

  return (
    <Card className="mb-10 overflow-hidden bg-[#0A0A0A] border border-white/10 text-white rounded-3xl relative">
      <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-blue-900/10 to-transparent pointer-events-none" />

      <div className="relative z-10 p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
        <div className="space-y-4 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-xs font-semibold text-blue-400 border border-blue-500/20">
            <Sparkles className="h-3.5 w-3.5" />
            Top AI Prediction
          </div>

          <div>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white mb-2">
              {details?.scheme_name || scheme.scheme_name}
            </h2>
            <p className="text-slate-400 leading-relaxed text-sm md:text-base">
              {details?.ministry && <span className="text-white font-medium mr-2">{details.ministry} •</span>}
              {details?.summary || `A highly recommended ${scheme.category || 'governmental'} scheme tailored for your profile.`}
            </p>
          </div>

          <div className="flex flex-wrap gap-3 pt-2">
            <Button className="rounded-xl bg-white text-black hover:bg-slate-200 font-semibold" asChild>
              <a href={details?.source_url || '#'} target="_blank">
                Apply Immediately <ArrowRight className="ml-2 h-4 w-4" />
              </a>
            </Button>
            <Button variant="outline" className="rounded-xl border-white/10 hover:bg-white/5 text-white bg-transparent">
              Save for Later
            </Button>
          </div>
        </div>

        <div className="flex-shrink-0 flex flex-col items-center justify-center p-6 bg-[#121214] border border-white/5 rounded-2xl min-w-[160px]">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Match Score</div>
          <div className="text-5xl font-bold text-blue-400">{Math.round(scheme.confidence)}<span className="text-2xl text-blue-400/50">%</span></div>
          <div className="mt-2 flex items-center gap-1.5 text-xs font-medium text-green-400 bg-green-400/10 px-2.5 py-1 rounded-full">
            <ShieldCheck className="w-3.5 h-3.5" /> High Success
          </div>
        </div>
      </div>
    </Card>
  );
}

// ─── Compare Modal ───────────────────────────────────────────────────────────
function CompareModal({ items, onClose }: { items: { scheme: any; details?: any }[]; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-5xl bg-[#0a0a0b] border border-white/10 rounded-3xl shadow-2xl overflow-auto max-h-[90vh] z-10">
        <div className="sticky top-0 bg-[#0a0a0b]/95 border-b border-white/5 p-5 flex items-center justify-between z-10">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="text-blue-400">⇄</span> Scheme Comparison
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors text-2xl leading-none">&times;</button>
        </div>

        <div className="p-5 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left text-slate-500 font-semibold text-xs uppercase tracking-wide pb-4 w-36">Field</th>
                {items.map((item, i) => (
                  <th key={i} className="text-left pb-4 px-3">
                    <div className="text-white font-bold line-clamp-2 text-sm">{item.details?.scheme_name || item.scheme.scheme_name}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                { label: 'Match Score', render: (item: any) => <span className={`font-black text-lg ${item.scheme.confidence > 80 ? 'text-blue-400' : 'text-slate-300'}`}>{Math.round(item.scheme.confidence)}%</span> },
                { label: 'Type', render: (item: any) => <span className="capitalize text-slate-300">{item.details?.benefit_type || 'Scheme'}</span> },
                { label: 'Ministry', render: (item: any) => <span className="text-slate-400">{item.details?.ministry || '—'}</span> },
                { label: 'Eligibility', render: (item: any) => item.scheme.eligible ? <span className="text-green-400 font-semibold">✓ Eligible</span> : <span className="text-red-400">✗ Check Criteria</span> },
                { label: 'Key Benefits', render: (item: any) => <span className="text-slate-400 text-xs leading-snug line-clamp-3">{item.details?.summary || '—'}</span> },
                { label: 'Documents', render: (item: any) => <span className="text-slate-400 text-xs leading-snug">{item.details?.documents_snippets?.[0] || '—'}</span> },
                { label: 'Apply', render: (item: any) => item.details?.source_url ? <a href={item.details.source_url} target="_blank" className="text-blue-400 hover:underline text-xs flex items-center gap-1">Apply Now <ExternalLink className="h-3 w-3" /></a> : <span className="text-slate-500">—</span> },
              ].map(row => (
                <tr key={row.label}>
                  <td className="py-4 pr-3 text-slate-500 font-semibold text-xs uppercase tracking-wide align-top">{row.label}</td>
                  {items.map((item, i) => (
                    <td key={i} className="py-4 px-3 align-top">{row.render(item)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
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
  const [compareList, setCompareList] = useState<{ scheme: any; details?: any }[]>([]);
  const [showCompare, setShowCompare] = useState(false);

  const handleToggleCompare = (scheme: any, details?: any) => {
    setCompareList(prev => {
      const exists = prev.find(c => c.scheme.id === scheme.id);
      if (exists) return prev.filter(c => c.scheme.id !== scheme.id);
      if (prev.length >= 3) return prev; // max 3
      return [...prev, { scheme, details }];
    });
  };

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


  const handleExport = async () => {
    setIsExporting(true);
    try {
      const { jsPDF } = await import('jspdf');
      const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const pageW = doc.internal.pageSize.getWidth();
      let y = 20;

      // Header
      doc.setFillColor(10, 10, 15);
      doc.rect(0, 0, pageW, 30, 'F');
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text('CivixAI – My Matched Schemes', 15, 18);
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(150, 150, 170);
      doc.text(`Generated: ${new Date().toLocaleDateString('en-IN')}`, pageW - 15, 18, { align: 'right' });
      y = 40;

      filteredSchemes.slice(0, 30).forEach((scheme, idx) => {
        const details = structuredById.get(scheme.id);
        const name = details?.scheme_name || scheme.scheme_name || 'Unknown Scheme';
        const confidence = Math.round(scheme.confidence);
        const ministry = details?.ministry || 'Government of India';
        const summary = details?.summary || 'Matched based on your profile.';
        const docs = details?.documents_snippets?.[0] || 'Refer to official portal.';
        const url = details?.source_url || '';

        if (y > 260) { doc.addPage(); y = 20; }

        // Card background
        doc.setFillColor(18, 18, 20);
        doc.roundedRect(12, y, pageW - 24, 52, 3, 3, 'F');

        // Index + Name
        doc.setTextColor(100, 160, 255);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'bold');
        doc.text(`#${idx + 1}`, 17, y + 8);
        doc.setTextColor(240, 240, 255);
        doc.setFontSize(11);
        doc.text(name.slice(0, 60), 26, y + 8);

        // Confidence badge
        doc.setFillColor(confidence > 80 ? 30 : 60, confidence > 80 ? 100 : 60, confidence > 80 ? 220 : 80);
        doc.roundedRect(pageW - 40, y + 2, 26, 10, 2, 2, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'bold');
        doc.text(`${confidence}% Match`, pageW - 39, y + 9);

        // Ministry
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(120, 130, 160);
        doc.text(ministry.slice(0, 70), 17, y + 16);

        // Summary
        doc.setTextColor(180, 185, 200);
        doc.setFontSize(8);
        const summaryLines = doc.splitTextToSize(summary.slice(0, 200), pageW - 50);
        doc.text(summaryLines.slice(0, 2), 17, y + 24);

        // Documents
        doc.setTextColor(100, 160, 100);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7);
        doc.text('Docs:', 17, y + 38);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(140, 150, 170);
        doc.text(docs.slice(0, 90), 30, y + 38);

        // Apply URL
        if (url) {
          doc.setTextColor(80, 130, 220);
          doc.setFontSize(7);
          doc.text(url.slice(0, 70), 17, y + 46);
        }

        y += 58;
      });

      // Footer
      doc.setFontSize(8);
      doc.setTextColor(80, 80, 100);
      doc.text('Generated by CivixAI – AI-powered Government Schemes Platform', pageW / 2, 290, { align: 'center' });

      doc.save('CivixAI_My_Schemes.pdf');
    } catch (err) {
      console.error('PDF export failed:', err);
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
    const entries = apiData.schemeDetails.map((s): [string, any] => {
      const id = s.id || toSlug(s.name || '');
      const details = {
        scheme_name: s.name,
        summary: s.description,
        ministry: s.ministry,
        level: s.level,
        category: s.category,
        benefit_type: s.benefit_type || 'scheme',
        url: s.url,
        source_url: s.source_url,
        application_deadline: s.application_deadline,
        processing_time: s.processing_time,
        popularity_score: s.popularity_score,
        benefits_snippets: s.description ? [s.description] : [],
        documents_snippets: s.documents ? [s.documents] : []
      };
      return [id, details];
    });
    return new Map(entries);
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
    missing_inputs?: string[];
    benefit_amount?: string;
    tags?: string;
    application_deadline?: string;
    processing_time?: string;
    popularity_score?: string;
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
        threshold: item.threshold,
        missing_inputs: item.missing_inputs,
        benefit_amount: item.benefit_amount,
        tags: item.tags,
        application_deadline: item.application_deadline,
        processing_time: item.processing_time,
        popularity_score: item.popularity_score,
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
      missing_inputs: item.missing_inputs,
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

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            >
              <TopMatchHero scheme={topScheme} details={structuredById.get(topScheme?.id)} />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.15, ease: 'easeOut' }}
              className="mb-12"
            >
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8 pb-6 border-b border-white/5">
                <div className="space-y-2">
                  <h1 className="text-4xl font-bold text-white tracking-tight">Eligibility Matches</h1>
                  <p className="text-slate-400">Showing <span className="font-semibold text-white">{eligibleOnlySchemes.length}</span> prime schemes from a dataset of {schemes.length}.</p>
                </div>

                <div className="flex gap-4">
                  <div className="bg-[#121214] px-4 py-3 rounded-2xl border border-white/5 flex flex-col items-center justify-center min-w-[110px]">
                    <span className="text-2xl font-bold text-blue-400">{highPriorityCount}</span>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mt-1">High Priority</span>
                  </div>
                  <div className="bg-[#121214] px-4 py-3 rounded-2xl border border-white/5 flex flex-col items-center justify-center min-w-[110px]">
                    <span className="text-2xl font-bold text-green-400">{eligibleOnlySchemes.length}</span>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mt-1">Total Eligible</span>
                  </div>
                </div>
              </div>

              <Tabs defaultValue={activeTab} onValueChange={setActiveTab} className="w-full">
                <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-8">
                  <TabsList className="h-auto bg-[#0a0a0b]/80 border border-white/5 p-1 rounded-xl w-full md:w-auto overflow-x-auto">
                    <TabsTrigger value="All" className="rounded-lg py-2 px-6 font-medium text-sm text-slate-400 data-[state=active]:bg-[#222225] data-[state=active]:text-white transition-all">
                      All Items
                    </TabsTrigger>
                    <TabsTrigger value="scheme" className="rounded-lg py-2 px-6 font-medium text-sm text-slate-400 data-[state=active]:bg-[#222225] data-[state=active]:text-white transition-all">
                      Govt Schemes
                    </TabsTrigger>
                    <TabsTrigger value="loan" className="rounded-lg py-2 px-6 font-medium text-sm text-slate-400 data-[state=active]:bg-[#222225] data-[state=active]:text-orange-400 transition-all">
                      Loans
                    </TabsTrigger>
                    <TabsTrigger value="insurance" className="rounded-lg py-2 px-6 font-medium text-sm text-slate-400 data-[state=active]:bg-[#222225] data-[state=active]:text-purple-400 transition-all">
                      Insurance
                    </TabsTrigger>
                  </TabsList>

                  <div className="relative w-full md:w-80 group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <SearchX className="h-4 w-4 text-slate-500" />
                    </div>
                    <Input
                      placeholder="Search matches..."
                      className="h-10 border-white/5 bg-[#0a0a0b]/80 pl-10 rounded-xl text-white placeholder:text-slate-500 focus-visible:ring-1 focus-visible:ring-blue-500/50"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
                  <AnimatePresence mode="sync">
                    {finalSchemes.slice(0, 50).map((scheme, index) => (
                      <DetailedSchemeCard
                        key={scheme.id}
                        scheme={scheme}
                        index={index}
                        details={structuredById.get(scheme.id)}
                        onFeedback={handleFeedback}
                        isInCompare={compareList.some(c => c.scheme.id === scheme.id)}
                        onToggleCompare={handleToggleCompare}
                      />
                    ))}
                  </AnimatePresence>
                </div>

                {finalSchemes.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="text-center py-20 bg-white/5 rounded-3xl border border-white/10"
                  >
                    <p className="text-slate-400">No schemes found in this category. Please check another tab.</p>
                  </motion.div>
                )}
              </Tabs>
            </motion.div>

            {/* AI Insights & Footer Controls */}
            <div className="grid gap-6 lg:grid-cols-3 mt-12 mb-8">
              <Card className="lg:col-span-2 bg-[#0a0a0b]/80 border-white/5 p-6 md:p-8 rounded-2xl shadow-none">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-blue-500/10 rounded-xl">
                    <Sparkles className="h-5 w-5 text-blue-400" />
                  </div>
                  <h3 className="text-xl font-bold text-white">AI Strategy Summary</h3>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <div className="font-semibold text-white flex items-center gap-2 text-sm">
                      <Zap className="h-4 w-4 text-blue-400" /> Next Steps
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      Based on predictive modeling, your best course of action is to apply for <strong>{topScheme?.scheme_name}</strong>. It correlates highest with your demographic.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <div className="font-semibold text-white flex items-center gap-2 text-sm">
                      <ShieldCheck className="h-4 w-4 text-green-400" /> Smart Tip
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      Ensure your Aadhar is firmly linked to your bank account. Our AI detected {eligibleOnlySchemes.filter(s => s.id.includes('dbt')).length || 3} schemes operating via DBT.
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-6 md:p-8 rounded-2xl bg-[#0a0a0b]/80 border-white/5 shadow-none flex flex-col justify-center gap-6">
                <div>
                  <h4 className="text-lg font-bold mb-1 text-white">Actions</h4>
                  <p className="text-sm text-slate-400">Manage your results</p>
                </div>
                <div className="space-y-3">
                  <Button onClick={handleExport} disabled={isExporting} className="w-full rounded-xl bg-white text-black hover:bg-slate-200 font-semibold border-0" size="lg">
                    {isExporting ? 'Generating PDF...' : '⬇ Download PDF Report'}
                  </Button>
                  <Button asChild variant="outline" size="lg" className="w-full rounded-xl border-white/10 text-white hover:bg-white/5 bg-transparent">
                    <Link href="/check-eligibility">Refresh Profile</Link>
                  </Button>
                </div>
              </Card>
            </div>
          </section>
        </main>
      </ScrollWrapper>
      <Chatbot context={finalSchemes} />

      {/* Compare Sticky Bar */}
      {compareList.length >= 2 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-4 px-6 py-3 rounded-2xl bg-blue-600/90 backdrop-blur-md border border-blue-400/30 shadow-[0_8px_32px_rgba(37,99,235,0.4)]">
          <span className="text-white text-sm font-semibold">{compareList.length} schemes selected</span>
          <Button size="sm" onClick={() => setShowCompare(true)} className="bg-white text-blue-700 hover:bg-blue-50 rounded-xl font-bold text-xs px-4">Compare Now ⇄</Button>
          <button onClick={() => setCompareList([])} className="text-blue-200 hover:text-white text-xs underline">Clear</button>
        </div>
      )}

      {/* Compare Modal */}
      {showCompare && <CompareModal items={compareList} onClose={() => setShowCompare(false)} />}
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
