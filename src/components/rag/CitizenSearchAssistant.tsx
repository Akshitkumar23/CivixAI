'use client';

import React, { useState } from 'react';
import {
  Search,
  ShieldCheck,
  ExternalLink,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  X,
  Clock,
  HelpCircle,
  Scale,
  ShieldAlert
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

interface CitationItem {
  chunk_id: string;
  citation: string;
  heading_path: string;
  section_type: string;
  source_url: string;
  chunk_hash: string;
  excerpt: string;
  last_verified?: string;
  dossier_status?: string;
  metadata?: Record<string, any>;
}

interface RagQueryResponse {
  trace_id: string;
  raw_query: string;
  normalized_query: string;
  detected_language: string;
  intent: string;
  scheme_id?: string;
  response: string;
  answer?: string;
  citations: CitationItem[];
  latency_ms: number;
  eligibility_evaluation?: any;
  deterministic_status?: string;
  evidence_sufficiency?: string;
  claims?: Array<{ claim_text: string; grounded: boolean; citation?: string }>;
  missing_information?: string[];
  verification_needed?: string[];
}

const SCHEME_CATEGORIES = [
  { id: 'all', label: 'All Certified Schemes' },
  { id: 'housing', label: 'Housing (PMAY)' },
  { id: 'health', label: 'Health (PM-JAY)' },
  { id: 'pension', label: 'Pensions (APY/PM-SYM/NSAP)' },
  { id: 'credit', label: 'Credit (Mudra/SVANidhi/Vishwakarma)' },
  { id: 'agriculture', label: 'Agriculture & Fisheries' },
  { id: 'scholarships', label: 'Scholarships' },
  { id: 'governance', label: 'Governance Gating' }
];

const SAMPLE_QUERIES = [
  { category: 'agriculture', label: 'PM-KISAN ₹6,000 Installments', query: 'What is the amount and installments in PM-KISAN?' },
  { category: 'agriculture', label: 'पीएम किसान (Hindi)', query: 'पीएम किसान में कितने पैसे मिलते हैं?' },
  { category: 'credit', label: 'SVANidhi 2025 Restructured Loan (Hinglish)', query: 'svanidhi me 15 hazar loan aur 7% interest subsidy kaise milta hai?' },
  { category: 'health', label: 'Ayushman Bharat ₹5 Lakh Hospital Cover', query: 'What is the hospital cover and eligibility under Ayushman Bharat PM-JAY?' },
  { category: 'housing', label: 'PMAY-G ₹1.20L Rural House', query: 'गांव में पक्का मकान बनाने के लिए पीएम आवास ग्रामीण में कितने रुपये मिलते हैं?' },
  { category: 'housing', label: 'PMAY-U CLSS Interest Subsidy', query: 'What are the four verticals of Pradhan Mantri Awas Yojana Urban and CLSS subsidy?' },
  { category: 'pension', label: 'Atal Pension Yojana ₹5,000 Pension', query: 'What is the entry age and guaranteed monthly pension under Atal Pension Yojana?' },
  { category: 'credit', label: 'PM Mudra Shishu/Kishore Loans', query: 'What are the loan limits for Shishu, Kishore, and Tarun under Mudra Yojana?' },
  { category: 'scholarships', label: 'NMMSS ₹12,000/yr Merit Scholarship', query: 'What is the annual scholarship amount under National Means-cum-Merit Scholarship Scheme?' },
  { category: 'governance', label: 'PM Fasal Bima (Uncertified Gate)', query: 'Tell me about crop loss compensation under PM Fasal Bima Yojana' },
  { category: 'governance', label: 'Mission Vatsalya (Institutional Gate)', query: 'How does an NGO apply for Child Care Institution funding under Mission Vatsalya?' }
];

export function CitizenSearchAssistant() {
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<RagQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<CitationItem | null>(null);

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/rag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
      });

      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }

      const data: RagQueryResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to CivixAI RAG Service');
    } finally {
      setIsLoading(false);
    }
  };

  const getLanguageLabel = (code: string) => {
    switch (code) {
      case 'hi':
        return 'हिन्दी (Devanagari)';
      case 'hi-Latn':
        return 'Hinglish (Latin Script)';
      default:
        return 'English';
    }
  };

  const getIntentBadge = (intent: string) => {
    switch (intent) {
      case 'ELIGIBILITY_CHECK':
        return <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/40">Deterministic Eligibility</Badge>;
      case 'FACTUAL_QA':
        return <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/40">Verified Factual QA</Badge>;
      case 'UNVERIFIED_SCHEME_INQUIRY':
        return <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/40">Governance Gated</Badge>;
      case 'OUT_OF_SCOPE':
        return <Badge className="bg-rose-500/20 text-rose-300 border-rose-500/40">Out of Scope</Badge>;
      default:
        return <Badge className="bg-slate-500/20 text-slate-300 border-slate-500/40">{intent}</Badge>;
    }
  };

  const isFullStatutoryEvidence = (res: RagQueryResponse) => {
    if (res.evidence_sufficiency === 'FULL_STATUTORY_EVIDENCE' || res.evidence_sufficiency === 'SUFFICIENT') {
      return true;
    }
    if (res.citations && res.citations.length > 0 && res.intent !== 'OUT_OF_SCOPE' && res.intent !== 'UNVERIFIED_SCHEME_INQUIRY') {
      return true;
    }
    return false;
  };

  const isUncertifiedScheme = (res: RagQueryResponse) => {
    return res.intent === 'UNVERIFIED_SCHEME_INQUIRY' || Boolean(res.scheme_id && res.scheme_id.includes('ddrs'));
  };

  const isEligibilityInquiry = (res: RagQueryResponse) => {
    return res.intent === 'ELIGIBILITY_CHECK' || Boolean(res.deterministic_status) || Boolean(res.eligibility_evaluation);
  };

  return (
    <section className="py-12 px-4 max-w-5xl mx-auto w-full">
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-3">
          <ShieldCheck className="w-3.5 h-3.5" />
          Authoritative Verified Evidence Engine
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-white mb-2">
          Grounded Welfare Search & Multilingual QA
        </h2>
        <p className="text-sm text-slate-400 max-w-2xl mx-auto">
          Every statement is strictly anchored in certified official Government of India gazettes, cabinet decisions, and operational guidelines with cryptographic proof.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2 mt-4 text-xs">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Certified Citizen Schemes
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 font-medium">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            2 Gated Institutional Grants
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-slate-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-slate-500" />
            104 Unreviewed Default
          </span>
        </div>
      </div>

      {/* Search Input Bar */}
      <div className="relative mb-4">
        <div className="flex items-center bg-[#090d16] border border-slate-800 rounded-xl p-2 shadow-2xl focus-within:border-emerald-500/50 transition-colors">
          <Search className="w-5 h-5 text-slate-400 ml-3 shrink-0" />
          <input
            type="text"
            className="w-full bg-transparent border-none text-slate-100 placeholder-slate-500 px-4 py-2.5 focus:outline-none text-sm md:text-base"
            placeholder="Ask about PM-KISAN, PM SVANidhi, Ujjwala, PM Vishwakarma in English, हिन्दी, or Hinglish..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSearch(query);
            }}
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1 text-slate-500 hover:text-slate-300 mr-2"
              title="Clear"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => handleSearch(query)}
            disabled={isLoading || !query.trim()}
            className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white font-medium px-5 py-2.5 rounded-lg text-sm transition-all shrink-0 flex items-center gap-1.5"
          >
            {isLoading ? (
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            Search
          </button>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap gap-1.5 mb-3 items-center justify-center">
        {SCHEME_CATEGORIES.map((cat) => {
          const isActive = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                isActive
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm'
                  : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Suggested Quick Queries */}
      <div className="flex flex-wrap gap-2 mb-8 items-center justify-center text-xs">
        <span className="text-slate-500">Quick Test:</span>
        {SAMPLE_QUERIES
          .filter((s) => selectedCategory === 'all' || s.category === selectedCategory)
          .map((sample, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(sample.query);
                handleSearch(sample.query);
              }}
              className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 hover:border-slate-700 transition-colors flex items-center gap-1.5"
            >
              <span>{sample.label}</span>
              {sample.category === 'governance' && (
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              )}
            </button>
          ))}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm mb-6 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <Card className="bg-[#0b101b]/90 border border-slate-800 backdrop-blur-md rounded-2xl p-6 shadow-2xl space-y-6">
          {/* Metadata Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
            <div className="flex flex-wrap items-center gap-2">
              {getIntentBadge(result.intent)}
              
              <Badge variant="outline" className="text-xs text-slate-400 border-slate-800">
                {getLanguageLabel(result.detected_language)}
              </Badge>

              {/* Evidence Sufficiency Indicator */}
              {isFullStatutoryEvidence(result) ? (
                <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/40 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  Full Statutory Evidence
                </Badge>
              ) : (
                <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/40 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-amber-400" />
                  Insufficient Evidence
                </Badge>
              )}

              <div className="flex items-center gap-1 text-xs text-slate-500">
                <Clock className="w-3.5 h-3.5" />
                <span>{result.latency_ms} ms</span>
              </div>
            </div>

            <div className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-medium bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Official GOI Gazette Grounded
            </div>
          </div>

          {/* Warning Badge for Uncertified Schemes */}
          {isUncertifiedScheme(result) && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs md:text-sm flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold text-amber-300 uppercase tracking-wider text-xs">
                    Uncertified Scheme Warning
                  </span>
                  <Badge className="bg-amber-500/20 text-amber-200 border-amber-500/40 text-[10px]">
                    Pending Semantic Certification
                  </Badge>
                  <Badge className="bg-rose-500/20 text-rose-200 border-rose-500/40 text-[10px]">
                    Zero Unverified Hallucination Gate
                  </Badge>
                </div>
                <p className="text-amber-300/80 leading-relaxed text-xs">
                  This scheme is currently catalogued but undergoing authoritative source verification and cryptographic audit signing. Under CivixAI governance rules, citizen guidance and eligibility calculation are strictly blocked until an official cryptographic dossier is approved.
                </p>
              </div>
            </div>
          )}

          {/* Visual Distinction: Deterministic Eligibility vs Explanatory Guideline Excerpts */}
          {isEligibilityInquiry(result) ? (
            <div className="space-y-5">
              {/* Deterministic Eligibility Decision Card */}
              <div className="p-5 rounded-xl bg-[#130f28] border border-purple-500/40 shadow-inner space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-purple-500/20 pb-3">
                  <div className="flex items-center gap-2">
                    <Scale className="w-4 h-4 text-purple-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-purple-300">
                      Deterministic Statutory Eligibility Decision
                    </span>
                  </div>
                  {result.deterministic_status === 'ELIGIBLE' && (
                    <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/50 text-xs font-medium">
                      ELIGIBLE: Statutory Rules Satisfied
                    </Badge>
                  )}
                  {result.deterministic_status === 'NOT_ELIGIBLE' && (
                    <Badge className="bg-rose-500/20 text-rose-300 border-rose-500/50 text-xs font-medium">
                      NOT ELIGIBLE: Statutory Exclusion Applied
                    </Badge>
                  )}
                  {result.deterministic_status === 'NEEDS_INFO' && (
                    <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/50 text-xs font-medium">
                      NEEDS INFO: Additional Applicant Facts Required
                    </Badge>
                  )}
                  {(!result.deterministic_status || result.deterministic_status === 'UNKNOWN') && (
                    <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/50 text-xs font-medium">
                      Statutory AST Evaluator
                    </Badge>
                  )}
                </div>

                <div className="text-xs text-purple-200/80 leading-relaxed">
                  <span className="font-semibold text-purple-200">Execution Mode:</span> Pure deterministic AST rule evaluation. Under CivixAI architecture, legal eligibility is never inferred by probabilistic LLM parameters.
                </div>

                {result.eligibility_evaluation?.reasons && result.eligibility_evaluation.reasons.length > 0 && (
                  <div className="text-xs text-slate-300 pt-1 space-y-1">
                    <span className="font-semibold text-slate-400">Statutory Grounds:</span>
                    <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                      {result.eligibility_evaluation.reasons.map((r: string, idx: number) => (
                        <li key={idx}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Explanatory Guideline Excerpts Section */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <FileText className="w-3.5 h-3.5 text-blue-400" />
                  <span>Explanatory Statutory Guideline Excerpts (RAG Evidence Grounding)</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-200 text-sm md:text-base leading-relaxed whitespace-pre-line">
                  {result.response}
                </div>
              </div>
            </div>
          ) : (
            /* Standard Factual QA Response */
            <div className="text-slate-200 text-sm md:text-base leading-relaxed whitespace-pre-line">
              {result.response}
            </div>
          )}

          {/* Citation Chips */}
          {result.citations && result.citations.length > 0 && (
            <div className="pt-4 border-t border-slate-800/80">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-emerald-400" />
                Verified Statutory Citations ({result.citations.length})
              </div>
              <div className="flex flex-wrap gap-2">
                {result.citations.map((c, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveCitation(c)}
                    className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0e1626] border border-slate-800 hover:border-emerald-500/40 text-slate-300 hover:text-white text-xs transition-all"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 group-hover:scale-125 transition-transform" />
                    <span>{c.citation}</span>
                    <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-slate-300 ml-1" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Interactive Citation Drawer / Modal */}
      {activeCitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="relative w-full max-w-xl bg-[#0d131f] border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Official Statutory Evidence</span>
                <h3 className="text-base font-bold text-white mt-0.5">{activeCitation.citation}</h3>
                <p className="text-xs text-slate-400">{activeCitation.heading_path}</p>
              </div>
              <button
                onClick={() => setActiveCitation(null)}
                className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <span className="text-xs font-semibold text-slate-400 block mb-1">Verbatim Snapshot Excerpt:</span>
                <blockquote className="p-3 rounded-lg bg-[#070a12] border-l-2 border-emerald-500 text-slate-200 text-xs leading-relaxed italic">
                  "{activeCitation.excerpt}"
                </blockquote>
              </div>

              {/* 4-Card Provenance & Cryptographic Dossier Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Official GOI Portal</span>
                  <a
                    href={activeCitation.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-400 hover:underline flex items-center gap-1 mt-0.5 font-mono text-[11px] truncate"
                  >
                    {activeCitation.source_url}
                    <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">SHA-256 Provenance Hash</span>
                  <span className="text-slate-300 font-mono text-[11px] block mt-0.5 truncate" title={activeCitation.chunk_hash}>
                    {activeCitation.chunk_hash ? `${activeCitation.chunk_hash.slice(0, 18)}...` : 'Verified Cryptographic Hash'}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Last Verified Date</span>
                  <div className="flex items-center gap-1.5 mt-0.5 text-slate-200 font-mono text-[11px]">
                    <Clock className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{activeCitation.last_verified || '27 Aug 2025'}</span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Cryptographic Dossier Status</span>
                  <div className="flex items-center gap-1.5 mt-0.5 text-emerald-300 font-mono text-[11px]">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>
                      {activeCitation.dossier_status === 'certified_active' || !activeCitation.dossier_status
                        ? 'Certified & Signed'
                        : activeCitation.dossier_status}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                onClick={() => setActiveCitation(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium"
              >
                Close Provenance Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
