'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, ExternalLink, ShieldCheck, AlertCircle, Building2, 
  MapPin, Layers, FileText, CheckCircle2, Globe, Clock, 
  Share2, ArrowRight, RefreshCw, Bookmark, Sparkles, Scale, AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface CriterionItem {
  criterion_id?: string;
  exact_text?: string;
  fact_key?: string;
  operator?: string;
  expected_value?: any;
}

interface ProgrammeDetail {
  programme_id: string;
  canonical_name: string;
  programme_type: string;
  government_level: string;
  jurisdiction: string;
  authority?: string;
  ministry?: string;
  department?: string;
  category: string;
  state_or_ut?: string;
  beneficiary_type: string;
  description?: string;
  benefit_summary?: string;
  application_route?: string;
  official_url?: string;
  currentness: string;
  source_status: string;
  eligibility_available: boolean;
  eligibility_status: string;
  eligibility_status_label: string;
  eligibility_banner: string;
  banner_type: 'SUCCESS' | 'REVIEW' | 'UNAVAILABLE' | 'SCOPE';
  applicability: string;
  is_certified: boolean;
  extracted_criteria?: CriterionItem[];
  mandatory_documents?: string[];
  documents?: Array<{ title: string; url?: string; type?: string }>;
  source_records?: Array<{ source_id: string; url?: string }>;
  lineage?: Array<{ relationship: string; source_id?: string; title?: string }>;
  created_at?: string;
  updated_at?: string;
}

export default function ProgrammeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [programme, setProgramme] = useState<ProgrammeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetch(`/api/programmes/${id}`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error('Programme not found');
        }
        return res.json();
      })
      .then((data) => {
        setProgramme(data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load programme detail');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050510] text-slate-100 flex flex-col items-center justify-center pt-24">
        <RefreshCw className="w-10 h-10 animate-spin text-blue-500 mb-4" />
        <p className="text-slate-400 text-sm">Retrieving Official Programme Dossier...</p>
      </div>
    );
  }

  if (error || !programme) {
    return (
      <div className="min-h-screen bg-[#050510] text-slate-100 pt-28 pb-20">
        <div className="container mx-auto px-4 max-w-3xl text-center py-20 bg-white/[0.02] border border-white/10 rounded-3xl">
          <AlertCircle className="w-16 h-16 text-rose-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Programme Dossier Not Found</h2>
          <p className="text-slate-400 text-sm mb-6">
            The requested identifier &apos;{id}&apos; could not be matched against current discovery records.
          </p>
          <Button asChild className="bg-blue-600 hover:bg-blue-500 text-white rounded-xl">
            <Link href="/programmes">
              <ArrowLeft className="w-4 h-4 mr-2" /> Return to Discovery Catalogue
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const isCert = programme.is_certified || programme.eligibility_status === 'ELIGIBILITY_READY';

  const renderBanner = () => {
    if (programme.banner_type === 'SUCCESS') {
      return (
        <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 flex items-start gap-3 text-emerald-300">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-sm text-emerald-200">{programme.eligibility_banner}</div>
            <div className="text-xs text-emerald-400/80 mt-0.5">
              This programme is part of the governed production pool. Deterministic automated eligibility assessment is active.
            </div>
          </div>
        </div>
      );
    }
    if (programme.banner_type === 'REVIEW') {
      return (
        <div className="p-4 rounded-2xl bg-indigo-950/40 border border-indigo-500/40 flex items-start gap-3 text-indigo-300">
          <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-sm text-indigo-200">{programme.eligibility_banner}</div>
            <div className="text-xs text-indigo-400/80 mt-0.5">
              Official criteria have been forensically extracted from government gazettes and are awaiting human governance sign-off.
            </div>
          </div>
        </div>
      );
    }
    if (programme.banner_type === 'UNAVAILABLE') {
      return (
        <div className="p-4 rounded-2xl bg-amber-950/30 border border-amber-600/30 flex items-start gap-3 text-amber-300">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-sm text-amber-200">{programme.eligibility_banner}</div>
            <div className="text-xs text-amber-400/80 mt-0.5">
              Automated verification is not offered without complete official statutory evidence. You may consult the official portal directly.
            </div>
          </div>
        </div>
      );
    }
    return (
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex items-start gap-3 text-slate-300">
        <Building2 className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
        <div>
          <div className="font-bold text-sm text-white">{programme.eligibility_banner}</div>
          <div className="text-xs text-slate-400 mt-0.5">
            This entity operates at an institutional, employer, or statutory service level.
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#050510] text-slate-100 pt-24 pb-24 selection:bg-blue-600 selection:text-white">
      {/* Background Accent */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-16 left-1/2 -translate-x-1/2 w-[900px] h-[400px] bg-blue-600/10 blur-[120px] rounded-full"></div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-5xl">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between mb-6">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            className="text-slate-400 hover:text-white hover:bg-white/5 -ml-3 rounded-xl text-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Discovery Catalogue
          </Button>
          <span className="text-xs font-mono text-slate-500 bg-white/5 px-2.5 py-1 rounded-lg border border-white/5">
            ID: {programme.programme_id}
          </span>
        </div>

        {/* Header Dossier Card */}
        <div className="bg-[#0a0a1c] border border-white/10 rounded-3xl p-6 sm:p-8 mb-6 shadow-2xl backdrop-blur-xl relative overflow-hidden">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span className="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/30">
              {programme.programme_type.replace(/_/g, ' ')}
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/5 text-slate-300 border border-white/10">
              {programme.government_level} Government
            </span>
            {programme.state_or_ut && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-indigo-950/50 text-indigo-300 border border-indigo-700/40">
                <MapPin className="w-3 h-3" /> {programme.state_or_ut}
              </span>
            )}
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/40 text-emerald-300 border border-emerald-700/30">
              ● {programme.currentness}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight mb-4">
            {programme.canonical_name}
          </h1>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-slate-400 mb-6">
            <div className="flex items-start gap-2.5">
              <Building2 className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
              <div>
                <span className="text-slate-500 block text-xs">Authority / Ministry</span>
                <span className="text-slate-200 font-medium">
                  {programme.ministry || programme.authority || 'Government of India'}
                </span>
                {programme.department && (
                  <span className="text-slate-400 block text-xs mt-0.5">{programme.department}</span>
                )}
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <Layers className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
              <div>
                <span className="text-slate-500 block text-xs">Sector Category</span>
                <span className="text-slate-200 font-medium">{programme.category || 'General Welfare'}</span>
                <span className="text-slate-400 block text-xs mt-0.5 capitalize">
                  Beneficiary: {programme.beneficiary_type}
                </span>
              </div>
            </div>
          </div>

          {/* Eligibility Banner (Section 9 Requirement) */}
          <div className="mb-6">
            {renderBanner()}
          </div>

          {/* Action Row */}
          <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-white/5">
            {isCert ? (
              <Button asChild className="bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold shadow-lg shadow-emerald-500/20">
                <Link href={`/check-eligibility?scheme=${programme.programme_id}`}>
                  Check Eligibility <ArrowRight className="w-4 h-4 ml-1.5" />
                </Link>
              </Button>
            ) : (
              <Button asChild variant="outline" className="border-indigo-500/40 bg-indigo-950/20 text-indigo-300 rounded-xl">
                <a href="#eligibility-criteria">
                  <Scale className="w-4 h-4 mr-1.5" /> Review Eligibility Criteria
                </a>
              </Button>
            )}

            {programme.official_url && (
              <Button asChild variant="outline" className="bg-white/5 hover:bg-white/10 border-white/10 text-white rounded-xl">
                <a href={programme.official_url} target="_blank" rel="noopener noreferrer">
                  Official Source <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
                </a>
              </Button>
            )}
          </div>
        </div>

        {/* 10-Section Detailed Body Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Dossier Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Section 1: Overview */}
            <div className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-6">
              <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" /> 1. Programme Overview & Scope
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
                {programme.description || 'Official government welfare programme. Detailed objectives and citizen entitlement parameters are governed under statutory departmental guidelines.'}
              </p>
            </div>

            {/* Section 3: Benefit Details */}
            <div className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-6">
              <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> 3. Entitlement & Benefit Structure
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
                {programme.benefit_summary || 'Assistance and welfare subsidies provided according to official scheme sanction guidelines.'}
              </p>
            </div>

            {/* Section 5: Extracted Official Criteria */}
            <div id="eligibility-criteria" className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-6 scroll-mt-28">
              <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                <Scale className="w-4 h-4 text-purple-400" /> 5. Official Eligibility Criteria
              </h2>
              
              {programme.extracted_criteria && programme.extracted_criteria.length > 0 ? (
                <div className="space-y-3 mt-4">
                  {programme.extracted_criteria.map((c, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col gap-1.5">
                      <div className="text-xs font-semibold text-purple-300 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" />
                        Statutory Condition: <code className="font-mono bg-purple-950/40 px-1 py-0.5 rounded text-[11px]">{c.fact_key || 'Fact'}</code>
                        {c.operator && <span className="text-slate-400 text-[10px]">({c.operator})</span>}
                      </div>
                      <p className="text-xs text-slate-300 italic pl-5 border-l-2 border-purple-500/30">
                        &ldquo;{c.exact_text}&rdquo;
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-slate-400 leading-relaxed">
                  {programme.eligibility_status === 'INSUFFICIENT_OFFICIAL_EVIDENCE' ? (
                    <span>Official eligibility criteria text is not currently documented in the local statutory evidence cache. You may inspect the official source portal for detailed eligibility rules.</span>
                  ) : (
                    <span>Eligibility parameters are governed by statutory criteria. Consult official source guidelines for complete eligibility conditions.</span>
                  )}
                </div>
              )}
            </div>

            {/* Section 6: Required Documents */}
            <div className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-6">
              <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-amber-400" /> 6. Required Documents & Verifications
              </h2>
              {programme.mandatory_documents && programme.mandatory_documents.length > 0 ? (
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
                  {programme.mandatory_documents.map((doc, idx) => (
                    <li key={idx} className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-slate-300 flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                      <span>{doc}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-xs text-slate-400 leading-relaxed">
                  Identity proof (Aadhaar / Voter ID), residence proof, and applicable category or income certificates as mandated by administering department.
                </div>
              )}
            </div>

            {/* Section 7: Application Process & Route */}
            <div className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-6">
              <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                <Globe className="w-4 h-4 text-indigo-400" /> 7. Application Process & Delivery Route
              </h2>
              <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-slate-300 leading-relaxed">
                {programme.application_route || 'Applications are processed online through official department or state e-District portals.'}
              </div>
            </div>
          </div>

          {/* Sidebar Column: Authority, Source, Metadata, Governance */}
          <div className="space-y-6">
            {/* Section 8: Official Source */}
            <div className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-6">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                8. Official Source Link
              </h3>
              {programme.official_url ? (
                <div>
                  <a
                    href={programme.official_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-xs font-semibold text-blue-400 hover:text-blue-300 bg-blue-950/40 border border-blue-500/30 p-3 rounded-xl w-full break-all"
                  >
                    <ExternalLink className="w-4 h-4 shrink-0" />
                    <span>{programme.official_url}</span>
                  </a>
                  <p className="text-[10px] text-slate-500 mt-2">
                    Primary source URL recorded from official government portal.
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-500">Government gazette record maintained.</p>
              )}
            </div>

            {/* Section 9: Last Verified / Currentness */}
            <div className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-6">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                9. Verification & Currentness
              </h3>
              <div className="space-y-2.5 text-xs">
                <div>
                  <span className="text-slate-500 block text-[11px]">Currentness State</span>
                  <span className="text-emerald-400 font-semibold">{programme.currentness}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Discovery Provenance</span>
                  <span className="text-slate-300 font-mono">{programme.source_status}</span>
                </div>
                {programme.updated_at && (
                  <div>
                    <span className="text-slate-500 block text-[11px]">Last Audited</span>
                    <span className="text-slate-400 font-mono">{programme.updated_at.slice(0, 10)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Section 10: Governance Status */}
            <div className="bg-[#0a0a1a] border border-white/10 rounded-2xl p-6">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                10. Governance & Recommendation State
              </h3>
              <div className="space-y-2.5 text-xs">
                <div>
                  <span className="text-slate-500 block text-[11px]">Governance Inclusion</span>
                  <span className="text-slate-200 font-medium">
                    {isCert ? 'Certified Production Pool' : 'Discovery Catalogue (Awaiting Governance Signoff)'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Personalized Evaluation</span>
                  <span className="text-slate-400">
                    {isCert ? 'Active in automated evaluation' : 'Isolated from candidate evaluation'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Applicability Scope</span>
                  <span className="text-slate-300 font-semibold">{programme.applicability}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
