'use client';

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useScrollRestoration } from '@/hooks/use-scroll-restoration';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ExternalLink, ArrowRight, ArrowLeft, SearchX, CheckCircle2, AlertCircle, XCircle, Search, ShieldCheck } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Chatbot from '@/components/Chatbot';

interface APIResponse {
  success: boolean;
  run_id?: string;
  session_id?: string;
  profile_hash?: string;
  source?: string;
  normalized_fact_keys?: string[];
  counts?: {
    total: number;
    eligible: number;
    needs_info: number;
    needs_verification: number;
    not_eligible: number;
  };
  discovery_schemes?: any[];
  discovery_pool?: any[];
  eligibleSchemes?: string[];
  eligible_schemes?: any[];
  needs_info_schemes?: any[];
  needs_verification_schemes?: any[];
  not_eligible_schemes?: any[];
  schemeDetails?: Array<{
    id?: string;
    name: string;
    eligible: boolean;
    confidence: number;
    threshold: number;
    eligibility_status?: string;
    application_readiness?: number;
    match_score?: number;
    benefit_score?: number;
    rank_score?: number;
    reasons?: string[];
    missing_inputs?: string[];
    missing_facts?: string[];
    description?: string;
    ministry?: string;
    level?: string;
    category?: string;
    states?: string;
    documents?: string | string[];
    url?: string;
    source_url?: string;
    benefit_type?: string;
    benefit_amount?: string;
    path_to_eligibility?: string[];
  }>;
  topSchemes?: Array<{
    scheme: string;
    confidence: number;
    threshold: number;
  }>;
  error?: string;
}

interface SchemeCardItem {
  id: string;
  scheme_name: string;
  confidence: number;
  eligibility_status: string;
  reasons: string[];
  missing_inputs: string[];
  benefit_amount?: string;
  benefit_type?: string;
  description?: string;
  ministry?: string;
  category?: string;
  url?: string;
  source_url?: string;
}

function CitizenRecommendationCard({
  item,
  sessionId
}: {
  item: SchemeCardItem;
  sessionId?: string | null;
}) {
  const status = item.eligibility_status;
  const isEligible = status === 'ELIGIBLE';
  const isNeedsInfo = status === 'NEEDS_INFO' || status === 'NEEDS_VERIFICATION';
  const isNotEligible = status === 'NOT_ELIGIBLE';

  const detailsUrl = `/scheme/${encodeURIComponent(item.id)}${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`;
  const hasOfficialApplicationUrl = Boolean(item.url && item.url !== '#' && !item.url.startsWith('javascript:'));
  const hasOfficialSourceUrl = Boolean(item.source_url && item.source_url !== '#' && !item.source_url.startsWith('javascript:'));
  const targetApplicationUrl = hasOfficialApplicationUrl ? item.url : (hasOfficialSourceUrl ? item.source_url : null);

  // Clean missing inputs for citizen readability
  const cleanMissingInputs = (item.missing_inputs || []).map((input) => {
    return input
      .replace(/^(applicant\.|household\.|person\.|location\.|student\.|artisan\.|enterprise\.|family\.|social\.|agriculture\.|health\.|finance\.)/, '')
      .replace(/_/g, ' ');
  });

  return (
    <Card className="flex flex-col h-full bg-[#0c0d12] border border-white/10 hover:border-white/20 transition-all rounded-2xl overflow-hidden shadow-sm">
      <CardHeader className="p-5 pb-3">
        <div className="flex justify-between items-start gap-3">
          <div className="space-y-1 flex-1 min-w-0">
            <CardTitle className="text-base sm:text-lg font-bold leading-snug text-white line-clamp-2">
              {item.scheme_name}
            </CardTitle>
            <CardDescription className="text-xs text-slate-400 line-clamp-1">
              {item.ministry || item.category || 'Government of India'}
            </CardDescription>
          </div>

          <div className="shrink-0">
            {isEligible && (
              <Badge variant="outline" className="bg-emerald-500/15 text-emerald-300 border-emerald-500/30 text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Eligible
              </Badge>
            )}
            {isNeedsInfo && (
              <Badge variant="outline" className="bg-amber-500/15 text-amber-300 border-amber-500/30 text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1">
                <AlertCircle className="h-3 w-3" /> Need Info
              </Badge>
            )}
            {isNotEligible && (
              <Badge variant="outline" className="bg-rose-500/15 text-rose-300 border-rose-500/30 text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1">
                <XCircle className="h-3 w-3" /> Not Eligible
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-5 pt-1 flex-grow space-y-3">
        {/* Short source-backed description */}
        <p className="text-xs sm:text-sm text-slate-300 line-clamp-2 leading-relaxed">
          {item.description || 'Verified government citizen benefit scheme matching your background.'}
        </p>

        {/* Prominent Benefit Block */}
        {item.benefit_amount ? (
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
            <span className="text-[11px] font-semibold text-emerald-300 uppercase tracking-wide">Benefit</span>
            <span className="text-xs sm:text-sm font-bold text-emerald-400">₹ {item.benefit_amount}</span>
          </div>
        ) : (
          <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/5 flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Category</span>
            <span className="text-xs font-medium text-slate-300 capitalize">{item.benefit_type || 'Welfare Support'}</span>
          </div>
        )}

        {/* Why / Rule-backed reason or missing information */}
        {isEligible && item.reasons && item.reasons.length > 0 && (
          <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/15 space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block">
              Why you qualify
            </span>
            {item.reasons.slice(0, 2).map((r, i) => (
              <div key={i} className="text-xs text-emerald-200/90 flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold shrink-0">✓</span>
                <span className="line-clamp-2">{r}</span>
              </div>
            ))}
          </div>
        )}

        {isNeedsInfo && (
          <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/15 space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block">
              Need a little more information
            </span>
            {cleanMissingInputs.length > 0 ? (
              cleanMissingInputs.slice(0, 2).map((input, i) => (
                <div key={i} className="text-xs text-amber-200/90 flex items-start gap-1.5 capitalize">
                  <span className="text-amber-400 font-bold shrink-0">•</span>
                  <span className="line-clamp-1">{input}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-amber-200/80">A few additional questions will confirm your qualification.</p>
            )}
          </div>
        )}

        {isNotEligible && (
          <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/15 space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400 block">
              Eligibility condition
            </span>
            <div className="text-xs text-rose-200/90 flex items-start gap-1.5">
              <span className="text-rose-400 font-bold shrink-0">✗</span>
              <span className="line-clamp-2">
                {item.reasons && item.reasons.length > 0 ? item.reasons[0] : 'Specific statutory threshold outside eligible range for this scheme.'}
              </span>
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="p-5 pt-0 mt-auto flex items-center gap-2 border-t border-white/5 pt-3">
        {isEligible && targetApplicationUrl ? (
          <>
            <Button size="sm" className="flex-1 h-9 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs gap-1.5" asChild>
              <a href={targetApplicationUrl} target="_blank" rel="noreferrer">
                Apply now <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </Button>
            <Button size="sm" variant="outline" className="h-9 rounded-xl border-white/10 bg-[#121214] hover:bg-white/5 text-slate-300 text-xs px-3.5" asChild>
              <Link href={detailsUrl}>
                View details
              </Link>
            </Button>
          </>
        ) : isNeedsInfo ? (
          <>
            <Button size="sm" className="flex-1 h-9 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs gap-1.5" asChild>
              <Link href={`/check-eligibility${sessionId ? `?session_id=${sessionId}` : ''}`}>
                Answer questions <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
            <Button size="sm" variant="outline" className="h-9 rounded-xl border-white/10 bg-[#121214] hover:bg-white/5 text-slate-300 text-xs px-3.5" asChild>
              <Link href={detailsUrl}>
                View details
              </Link>
            </Button>
          </>
        ) : (
          <Button size="sm" variant="secondary" className="w-full h-9 rounded-xl bg-white/10 hover:bg-white/15 text-slate-200 font-medium text-xs gap-1.5 justify-center" asChild>
            <Link href={detailsUrl}>
              View details <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}

function RecommendationsContent() {
  const searchParams = useSearchParams();
  useScrollRestoration();

  const [apiData, setApiData] = useState<APIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Tab & Domain filters
  const [activeTab, setActiveTab] = useState<'all' | 'eligible' | 'needs_info' | 'not_eligible'>('all');
  const [domainFilter, setDomainFilter] = useState<'all' | 'welfare' | 'loan' | 'insurance'>('all');

  // Extract compact profile summary if provided in search params
  const profileSummary = useMemo(() => {
    const parts: string[] = [];
    const age = searchParams?.get('age');
    const state = searchParams?.get('state');
    const occupation = searchParams?.get('occupation');
    const income = searchParams?.get('annualIncome') || searchParams?.get('income');

    if (age) parts.push(`${age} yrs`);
    if (state) parts.push(state);
    if (occupation) parts.push(occupation.charAt(0).toUpperCase() + occupation.slice(1).replace(/_/g, ' '));
    if (income) parts.push(`₹${Number(income).toLocaleString('en-IN')}`);

    return parts.length > 0 ? parts.join(' · ') : null;
  }, [searchParams]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const getParam = (key: string) => searchParams?.get(key);
        const explicitSessionId = getParam('session_id');
        const hasProfileParams = Boolean(getParam('age') || getParam('occupation') || getParam('annualIncome') || getParam('income') || getParam('state'));

        let resolvedSessionId: string | null = null;
        if (explicitSessionId) {
          resolvedSessionId = explicitSessionId;
        } else if (!hasProfileParams && typeof window !== 'undefined') {
          resolvedSessionId = localStorage.getItem('civix_profile_session_id');
        }
        setSessionId(resolvedSessionId);

        let response;
        if (resolvedSessionId) {
          response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: resolvedSessionId,
              programme_kind: getParam('programme_kind') || getParam('type') || undefined,
            }),
          });
        } else {
          const toBool = (val?: string | null) => (val === 'true' ? true : val === 'false' ? false : undefined);
          const toNum = (val?: string | null) => {
            if (!val) return undefined;
            const n = Number(val);
            return isNaN(n) ? undefined : n;
          };

          const requestData: Record<string, any> = {
            source: 'CLASSIC',
            programme_kind: getParam('programme_kind') || getParam('type') || undefined,
          };
          const setIfVal = (k: string, v: any) => {
            if (v !== undefined && v !== null && v !== '') {
              requestData[k] = v;
            }
          };

          setIfVal('age', toNum(getParam('age')));
          setIfVal('annualIncome', toNum(getParam('annualIncome')) ?? toNum(getParam('income')));
          setIfVal('state', getParam('state'));
          setIfVal('caste', getParam('caste') || getParam('category'));
          setIfVal('occupation', getParam('occupation'));
          setIfVal('gender', getParam('gender'));
          setIfVal('hasDisability', toBool(getParam('hasDisability')));
          setIfVal('hasLand', toBool(getParam('hasLand')));
          setIfVal('familyIncome', toNum(getParam('familyIncome')));
          setIfVal('landSize', toNum(getParam('landSize')));
          setIfVal('familySize', toNum(getParam('familySize')));
          setIfVal('isSingleGirlChild', toBool(getParam('isSingleGirlChild')));
          setIfVal('isWidowOrSenior', toBool(getParam('isWidowOrSenior')));
          setIfVal('isTaxPayer', toBool(getParam('isTaxPayer')));
          setIfVal('isBankLinked', toBool(getParam('isBankLinked')));
          setIfVal('educationLevel', getParam('educationLevel'));
          setIfVal('digitalLiteracy', getParam('digitalLiteracy'));
          setIfVal('urbanRural', getParam('urbanRural'));
          setIfVal('maritalStatus', getParam('maritalStatus'));
          setIfVal('isBPL', toBool(getParam('isBPL')));
          setIfVal('isMinority', toBool(getParam('isMinority')));
          setIfVal('monthlyExpenses', toNum(getParam('monthlyExpenses')));
          setIfVal('hasSmartphone', toBool(getParam('hasSmartphone')));
          setIfVal('hasInternet', toBool(getParam('hasInternet')));
          setIfVal('employmentType', getParam('employmentType'));
          setIfVal('skillCertification', getParam('skillCertification'));
          setIfVal('loanRequirement', getParam('loanRequirement'));
          setIfVal('monthlySavings', toNum(getParam('monthlySavings')));
          setIfVal('hasInsurance', toBool(getParam('hasInsurance')));
          setIfVal('hasPension', toBool(getParam('hasPension')));

          response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData),
          });
        }

        if (!response.ok) {
          throw new Error(`API returned status ${response.status}`);
        }

        const data: APIResponse = await response.json();
        setApiData(data);
        if (data.session_id) {
          setSessionId(data.session_id);
          if (typeof window !== 'undefined') {
            localStorage.setItem('civix_profile_session_id', data.session_id);
          }
        }
      } catch (err) {
        console.error('Error fetching recommendations:', err);
        setError('Something went wrong while loading your matches. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchParams]);

  // Transform backend items into structured items
  const allItems: SchemeCardItem[] = useMemo(() => {
    if (!apiData) return [];

    if (apiData.schemeDetails && apiData.schemeDetails.length > 0) {
      return apiData.schemeDetails.map((s) => ({
        id: s.id || s.name,
        scheme_name: s.name,
        confidence: s.confidence || 50,
        eligibility_status: s.eligibility_status || (s.eligible !== false ? 'ELIGIBLE' : 'NEEDS_INFO'),
        reasons: s.reasons || [],
        missing_inputs: s.missing_inputs || s.missing_facts || [],
        benefit_amount: s.benefit_amount || '',
        benefit_type: s.benefit_type || 'scheme',
        description: s.description || '',
        ministry: s.ministry || '',
        category: s.category || '',
        url: s.url || '',
        source_url: s.source_url || '',
      }));
    }

    if (apiData.eligible_schemes || apiData.needs_info_schemes || apiData.not_eligible_schemes) {
      const out: SchemeCardItem[] = [];
      const addGroup = (group: any[] = [], defaultStatus: string) => {
        group.forEach((s) => {
          out.push({
            id: s.scheme_id || s.id || s.canonical_name,
            scheme_name: s.scheme_name || s.canonical_name || s.name || s.scheme_id,
            confidence: s.confidence_score ? Math.round(s.confidence_score * 100) : 50,
            eligibility_status: s.eligibility_status || defaultStatus,
            reasons: s.reasons || [],
            missing_inputs: s.missing_facts || s.missing_inputs || [],
            benefit_amount: s.benefit_summary || '',
            benefit_type: s.programme_kind || 'scheme',
            description: s.summary || s.description || '',
            ministry: s.ministry || '',
            category: s.category || '',
            url: s.application_url || '',
            source_url: s.source_url || '',
          });
        });
      };

      addGroup(apiData.eligible_schemes, 'ELIGIBLE');
      addGroup(apiData.needs_info_schemes, 'NEEDS_INFO');
      addGroup(apiData.needs_verification_schemes, 'NEEDS_VERIFICATION');
      addGroup(apiData.not_eligible_schemes, 'NOT_ELIGIBLE');
      return out;
    }

    return [];
  }, [apiData]);

  // Domain filtering (All vs Welfare vs Loans vs Insurance)
  const domainFilteredItems = useMemo(() => {
    if (domainFilter === 'all') return allItems;
    return allItems.filter((item) => {
      const kind = (item.benefit_type || '').toLowerCase();
      if (domainFilter === 'welfare') return kind === 'scheme' || kind === 'welfare' || kind === 'grant_in_aid' || !kind;
      if (domainFilter === 'loan') return kind === 'loan' || kind === 'credit';
      if (domainFilter === 'insurance') return kind === 'insurance';
      return true;
    });
  }, [allItems, domainFilter]);

  // Count tallies calculated from the authoritative API dataset
  const counts = useMemo(() => {
    let eligible = 0;
    let needs_info = 0;
    let not_eligible = 0;

    domainFilteredItems.forEach((item) => {
      if (item.eligibility_status === 'ELIGIBLE') eligible++;
      else if (item.eligibility_status === 'NOT_ELIGIBLE') not_eligible++;
      else needs_info++;
    });

    return {
      total: domainFilteredItems.length,
      eligible,
      needs_info,
      not_eligible,
    };
  }, [domainFilteredItems]);

  // Tab filtering (All vs Eligible vs Need Info vs Not Eligible)
  const tabFilteredItems = useMemo(() => {
    if (activeTab === 'eligible') {
      return domainFilteredItems.filter((i) => i.eligibility_status === 'ELIGIBLE');
    }
    if (activeTab === 'needs_info') {
      return domainFilteredItems.filter((i) => i.eligibility_status === 'NEEDS_INFO' || i.eligibility_status === 'NEEDS_VERIFICATION');
    }
    if (activeTab === 'not_eligible') {
      return domainFilteredItems.filter((i) => i.eligibility_status === 'NOT_ELIGIBLE');
    }
    return domainFilteredItems;
  }, [domainFilteredItems, activeTab]);

  // Search filtering
  const visibleItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return tabFilteredItems;
    return tabFilteredItems.filter((i) => {
      const name = i.scheme_name.toLowerCase();
      const desc = (i.description || '').toLowerCase();
      const ministry = (i.ministry || '').toLowerCase();
      const cat = (i.category || '').toLowerCase();
      return name.includes(q) || desc.includes(q) || ministry.includes(q) || cat.includes(q);
    });
  }, [tabFilteredItems, searchQuery]);

  // Domain breakdown counts for domain filter pills
  const domainPillCounts = useMemo(() => {
    let welfare = 0;
    let loan = 0;
    let insurance = 0;
    allItems.forEach((i) => {
      const k = (i.benefit_type || '').toLowerCase();
      if (k === 'loan' || k === 'credit') loan++;
      else if (k === 'insurance') insurance++;
      else welfare++;
    });
    return { all: allItems.length, welfare, loan, insurance };
  }, [allItems]);

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen bg-[#07070a] text-white font-sans">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-8 max-w-6xl">
          <div className="mb-6 space-y-2">
            <div className="h-5 w-24 bg-white/10 rounded-md animate-pulse" />
            <div className="h-8 w-64 bg-white/10 rounded-lg animate-pulse" />
            <div className="h-4 w-72 bg-white/10 rounded-md animate-pulse" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-64 rounded-2xl bg-[#0f1015] border border-white/5 animate-pulse" />
            ))}
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-screen bg-[#07070a] text-white font-sans">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-16 max-w-md flex flex-col items-center justify-center text-center">
          <Alert className="bg-[#0f1015] border-white/10 text-white rounded-2xl p-6">
            <SearchX className="h-6 w-6 text-rose-400 mb-2" />
            <AlertTitle className="text-lg font-bold">Unable to load matches</AlertTitle>
            <AlertDescription className="text-sm text-slate-300 mt-2">
              {error}
            </AlertDescription>
          </Alert>
          <Button asChild className="mt-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold">
            <Link href="/check-eligibility">Try again</Link>
          </Button>
        </main>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#07070a] text-white font-sans selection:bg-blue-500/30">
      <Header />

      <main className="flex-grow container mx-auto px-4 py-6 sm:py-8 max-w-6xl">
        {/* Navigation & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-white/10">
          <div className="space-y-1">
            <Link
              href={`/check-eligibility${sessionId ? `?session_id=${sessionId}` : ''}`}
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors mb-1"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Back to form
            </Link>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Your Scheme Matches
            </h1>
            <p className="text-xs sm:text-sm text-slate-400">
              Based on the information you provided
              {profileSummary && (
                <span className="text-slate-300 ml-1.5 font-medium">({profileSummary})</span>
              )}
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              asChild
              className="rounded-xl border-white/10 bg-[#121214] hover:bg-white/5 text-slate-200 text-xs px-3.5 h-9"
            >
              <Link href={`/check-eligibility${sessionId ? `?session_id=${sessionId}` : ''}`}>
                Edit profile
              </Link>
            </Button>
          </div>
        </div>

        {/* Compact Summary Strip */}
        <div className="flex flex-wrap items-center gap-2.5 my-5">
          <div className="px-3.5 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs font-semibold text-slate-300">
            {counts.total} Total Schemes
          </div>
          <div className="px-3.5 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400">
            {counts.eligible} Eligible
          </div>
          <div className="px-3.5 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs font-semibold text-amber-300">
            {counts.needs_info} Need Information
          </div>
          <div className="px-3.5 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-semibold text-rose-400">
            {counts.not_eligible} Not Eligible
          </div>
        </div>

        {/* Controls: Status Tabs & Search */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3.5 mb-5">
          <Tabs
            value={activeTab}
            onValueChange={(val) => setActiveTab(val as any)}
            className="w-full md:w-auto"
          >
            <TabsList className="bg-[#121214] border border-white/10 p-1 rounded-xl h-auto flex flex-wrap gap-1">
              <TabsTrigger
                value="all"
                className="rounded-lg text-xs py-1.5 px-3 data-[state=active]:bg-white/15 data-[state=active]:text-white text-slate-400"
              >
                All ({counts.total})
              </TabsTrigger>
              <TabsTrigger
                value="eligible"
                className="rounded-lg text-xs py-1.5 px-3 data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-300 text-slate-400"
              >
                ✓ Eligible ({counts.eligible})
              </TabsTrigger>
              <TabsTrigger
                value="needs_info"
                className="rounded-lg text-xs py-1.5 px-3 data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-300 text-slate-400"
              >
                ! Need info ({counts.needs_info})
              </TabsTrigger>
              <TabsTrigger
                value="not_eligible"
                className="rounded-lg text-xs py-1.5 px-3 data-[state=active]:bg-rose-500/20 data-[state=active]:text-rose-300 text-slate-400"
              >
                × Not eligible ({counts.not_eligible})
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="relative w-full md:w-64">
            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search schemes..."
              className="h-9 pl-9 pr-3 rounded-xl bg-[#121214] border-white/10 text-xs text-white placeholder:text-slate-500 focus-visible:ring-1 focus-visible:ring-blue-500"
            />
          </div>
        </div>

        {/* Optional Domain Filter Chips (only if domain data is present) */}
        {(domainPillCounts.loan > 0 || domainPillCounts.insurance > 0) && (
          <div className="flex flex-wrap items-center gap-1.5 mb-6 text-xs">
            <span className="text-slate-500 text-[11px] font-medium mr-1">Category:</span>
            <button
              onClick={() => setDomainFilter('all')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${
                domainFilter === 'all'
                  ? 'bg-white text-black font-semibold'
                  : 'bg-white/5 hover:bg-white/10 text-slate-400'
              }`}
            >
              All ({domainPillCounts.all})
            </button>
            <button
              onClick={() => setDomainFilter('welfare')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${
                domainFilter === 'welfare'
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'bg-white/5 hover:bg-white/10 text-slate-400'
              }`}
            >
              Welfare ({domainPillCounts.welfare})
            </button>
            <button
              onClick={() => setDomainFilter('loan')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${
                domainFilter === 'loan'
                  ? 'bg-orange-600 text-white font-semibold'
                  : 'bg-white/5 hover:bg-white/10 text-slate-400'
              }`}
            >
              Loans & Credit ({domainPillCounts.loan})
            </button>
            <button
              onClick={() => setDomainFilter('insurance')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${
                domainFilter === 'insurance'
                  ? 'bg-purple-600 text-white font-semibold'
                  : 'bg-white/5 hover:bg-white/10 text-slate-400'
              }`}
            >
              Insurance ({domainPillCounts.insurance})
            </button>
          </div>
        )}

        {/* 2-Column Responsive Card Grid */}
        {visibleItems.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {visibleItems.map((item) => (
              <CitizenRecommendationCard
                key={item.id}
                item={item}
                sessionId={sessionId}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 px-4 rounded-2xl bg-[#0f1015] border border-white/5 space-y-3">
            <SearchX className="h-8 w-8 text-slate-500 mx-auto" />
            <h3 className="text-base font-semibold text-white">No schemes here yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Try selecting another category tab or update your profile details to discover matching benefits.
            </p>
            <div className="pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setActiveTab('all');
                  setDomainFilter('all');
                  setSearchQuery('');
                }}
                className="rounded-xl border-white/10 text-xs"
              >
                Clear filters
              </Button>
            </div>
          </div>
        )}

        {/* Trust Note at Bottom */}
        <div className="mt-12 pt-6 border-t border-white/10 text-center text-[11px] text-slate-400 max-w-2xl mx-auto space-y-1">
          <p className="flex items-center justify-center gap-1.5 font-medium text-slate-300">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Information from official government sources
          </p>
          <p>
            Eligibility is checked against the guidelines available for each scheme. Always verify final requirements on the official application portal.
          </p>
        </div>
      </main>

      <Chatbot context={allItems} />
    </div>
  );
}

export default function RecommendationsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col min-h-screen bg-[#07070a] text-white">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8 max-w-6xl">
            <div className="h-8 w-48 bg-white/10 rounded-lg animate-pulse mb-6" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-64 rounded-2xl bg-[#0f1015] border border-white/5 animate-pulse" />
              ))}
            </div>
          </main>
        </div>
      }
    >
      <RecommendationsContent />
    </Suspense>
  );
}
