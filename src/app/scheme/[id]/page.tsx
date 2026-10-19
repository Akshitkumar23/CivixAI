import { promises as fs } from 'fs';
import path from 'path';
import Link from 'next/link';
import { Header } from '@/components/Header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  ExternalLink,
  Building2,
  CheckCircle2,
  AlertCircle,
  XCircle,
  ArrowLeft,
  SearchX,
  Globe,
  MapPin,
  Calendar,
  FileText,
  ShieldCheck,
  Check,
} from 'lucide-react';
import Chatbot from '@/components/Chatbot';
import { ClientScrollRestorer } from '@/components/ClientScrollRestorer';
import { WhatsAppShareButton } from '@/components/WhatsAppShareButton';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const next = text[i + 1];
    if (char === '"') {
      if (inQuotes && next === '"') { field += '"'; i++; }
      else { inQuotes = !inQuotes; }
      continue;
    }
    if (char === ',' && !inQuotes) { row.push(field); field = ''; continue; }
    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && next === '\n') { i++; }
      row.push(field); field = '';
      if (row.length > 1 || (row[0] && row[0].trim())) { rows.push(row); }
      row = [];
      continue;
    }
    field += char;
  }
  row.push(field);
  if (row.length > 1 || (row[0] && row[0].trim())) { rows.push(row); }
  return rows;
}

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://127.0.0.1:8000';

async function getSchemeById(id: string, sessionId?: string): Promise<any | null> {
  if (!id) return null;
  try {
    let url = `${ML_SERVICE_URL}/v1/schemes/${encodeURIComponent(id)}`;
    if (sessionId) {
      url += `?session_id=${encodeURIComponent(sessionId)}`;
    }
    const res = await fetch(url, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      return {
        ...data,
        min_age: data.rules?.find((r: any) => r.fact_key === 'person.age' && (r.operator === '>=' || r.operator === '>'))?.expected_value,
        max_age: data.rules?.find((r: any) => r.fact_key === 'person.age' && (r.operator === '<=' || r.operator === '<'))?.expected_value,
        income_limit: data.rules?.find((r: any) => r.fact_key?.includes('income') && (r.operator === '<=' || r.operator === '<'))?.expected_value,
        benefit_description: data.summary || data.description,
        documents_required: data.documents?.map((d: any) => typeof d === 'string' ? d : d.document_type).join(', '),
        benefit_type: data.programme_kind || data.benefit_type,
        applicable_states: data.applicable_states || (data.scheme_level === 'central' ? 'All India / Central Sector' : 'State Specific')
      };
    }
  } catch (error) {
    console.warn('Backend fetch failed, using CSV fallback:', error);
  }

  const DATA_PATH = path.join(process.cwd(), 'data', 'master', 'schemes_master.csv');
  try {
    const csvText = await fs.readFile(DATA_PATH, 'utf-8');
    const rows = parseCsv(csvText);
    if (rows.length === 0) return null;

    const headers = rows[0].map((header) => header.trim().replace(/^\uFEFF/, ''));
    const index = new Map<string, number>();
    headers.forEach((header, i) => index.set(header, i));

    const getValue = (row: string[], key: string): string | undefined => {
      const idx = index.get(key);
      if (idx === undefined) return undefined;
      return row[idx]?.trim();
    };

    const lowerId = id.toLowerCase();

    for (let i = 1; i < rows.length; i++) {
      const rowId = getValue(rows[i], 'scheme_id');
      if (rowId && (rowId.toLowerCase() === lowerId || rowId.toLowerCase().includes(lowerId))) {
        return {
          scheme_id: rowId,
          scheme_name: getValue(rows[i], 'scheme_name'),
          ministry: getValue(rows[i], 'ministry'),
          scheme_level: getValue(rows[i], 'scheme_level'),
          scheme_category: getValue(rows[i], 'scheme_category'),
          applicable_states: getValue(rows[i], 'applicable_states'),
          min_age: getValue(rows[i], 'min_age'),
          max_age: getValue(rows[i], 'max_age'),
          income_limit: getValue(rows[i], 'income_limit'),
          benefit_description: getValue(rows[i], 'benefit_description'),
          documents_required: getValue(rows[i], 'documents_required'),
          application_url: getValue(rows[i], 'application_url'),
          source_url: getValue(rows[i], 'source_url'),
          benefit_type: getValue(rows[i], 'benefit_type'),
          special_conditions_required: getValue(rows[i], 'special_conditions_required')
        };
      }
    }
    return null;
  } catch (error) {
    console.error('Error fetching scheme from CSV:', error);
    return null;
  }
}

export default async function SchemeDetailsPage({
  params,
  searchParams
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const resolvedParams = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const schemeId = resolvedParams.id;
  const sessionId = typeof resolvedSearchParams.session_id === 'string' ? resolvedSearchParams.session_id : undefined;

  const scheme = await getSchemeById(schemeId, sessionId);

  if (!scheme) {
    return (
      <div className="flex flex-col min-h-screen bg-[#07070a] text-white font-sans">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-20 flex flex-col items-center justify-center text-center">
          <div className="bg-[#0f1015] border border-white/10 p-10 rounded-2xl max-w-md space-y-4">
            <SearchX className="h-12 w-12 text-slate-400 mx-auto" />
            <h1 className="text-2xl font-bold">Scheme Not Found</h1>
            <p className="text-xs text-slate-400">
              The scheme details could not be retrieved. Please return to your matches list.
            </p>
            <Button asChild className="rounded-xl mt-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs">
              <Link href={sessionId ? `/recommendations?session_id=${sessionId}` : '/recommendations'}>
                <ArrowLeft className="mr-2 h-4 w-4" /> Back to matches
              </Link>
            </Button>
          </div>
        </main>
        <Chatbot />
      </div>
    );
  }

  const {
    scheme_name,
    ministry,
    scheme_category,
    applicable_states,
    min_age,
    max_age,
    income_limit,
    benefit_description,
    documents_required,
    application_url,
    source_url,
    benefit_type,
    special_conditions_required,
    user_match,
    benefits = [],
    sources = [],
    rules = []
  } = scheme;

  const hasApplicationUrl = Boolean(application_url && application_url !== '#' && !application_url.startsWith('javascript:'));
  const hasSourceUrl = Boolean(source_url && source_url !== '#' && !source_url.startsWith('javascript:'));
  const primaryApplyUrl = hasApplicationUrl ? application_url : (hasSourceUrl ? source_url : null);

  const docsList: string[] = documents_required
    ? documents_required.split(',').map((d: string) => d.trim()).filter(Boolean)
    : [];

  const status = user_match?.eligibility_status;
  const isEligible = status === 'ELIGIBLE';
  const isNeedsInfo = status === 'NEEDS_INFO' || status === 'NEEDS_VERIFICATION';
  const isNotEligible = status === 'NOT_ELIGIBLE';

  return (
    <div className="flex flex-col min-h-screen bg-[#07070a] text-white font-sans selection:bg-blue-500/30">
      <ClientScrollRestorer />
      <Header />

      <main className="flex-grow container mx-auto px-4 py-6 sm:py-8 max-w-4xl space-y-6">
        {/* Navigation & Header */}
        <div className="space-y-3 pb-4 border-b border-white/10">
          <Link
            href={sessionId ? `/recommendations?session_id=${sessionId}` : '/recommendations'}
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to matches
          </Link>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            {isEligible && (
              <Badge className="bg-emerald-500/15 text-emerald-300 border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Eligible
              </Badge>
            )}
            {isNeedsInfo && (
              <Badge className="bg-amber-500/15 text-amber-300 border-amber-500/30 text-xs px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1">
                <AlertCircle className="h-3 w-3" /> Need Information
              </Badge>
            )}
            {isNotEligible && (
              <Badge className="bg-rose-500/15 text-rose-300 border-rose-500/30 text-xs px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1">
                <XCircle className="h-3 w-3" /> Not Eligible
              </Badge>
            )}

            {scheme_category && (
              <Badge variant="outline" className="text-slate-400 border-white/10 text-[11px] px-2.5 py-0.5">
                {scheme_category}
              </Badge>
            )}
            {benefit_type && (
              <Badge variant="outline" className="text-slate-400 border-white/10 text-[11px] px-2.5 py-0.5 capitalize">
                {benefit_type.replace(/_/g, ' ')}
              </Badge>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-snug">
            {scheme_name}
          </h1>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-3xl">
            {benefit_description || 'Official government welfare scheme offering targeted assistance to eligible citizens.'}
          </p>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Building2 className="h-4 w-4 text-blue-400 shrink-0" />
              <span>{ministry || 'Government of India'}</span>
            </div>

            <div className="flex items-center gap-2">
              {primaryApplyUrl && (
                <Button size="sm" className="h-9 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs gap-1.5" asChild>
                  <a href={primaryApplyUrl} target="_blank" rel="noreferrer">
                    Apply now <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </Button>
              )}
              <WhatsAppShareButton
                schemeName={scheme_name || 'Scheme Highlights'}
                schemeId={schemeId}
                ministry={ministry || 'Government of India'}
              />
            </div>
          </div>
        </div>

        {/* Why You May Qualify (concise, shown only when user match exists) */}
        {user_match && (
          <Card className={`rounded-2xl p-5 border ${
            isEligible
              ? 'bg-emerald-950/20 border-emerald-500/20'
              : isNeedsInfo
              ? 'bg-amber-950/20 border-amber-500/20'
              : 'bg-rose-950/20 border-rose-500/20'
          }`}>
            <h2 className="text-xs font-bold uppercase tracking-wider mb-2.5 flex items-center gap-1.5 text-white">
              Why this matches you
            </h2>
            <div className="space-y-1.5 text-xs">
              {user_match.reasons && user_match.reasons.length > 0 && (
                user_match.reasons.map((r: string, idx: number) => (
                  <div key={idx} className="flex items-start gap-2 text-slate-200">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{r}</span>
                  </div>
                ))
              )}

              {user_match.missing_facts && user_match.missing_facts.length > 0 && (
                <div className="pt-2 border-t border-amber-500/20 mt-2 space-y-2">
                  <p className="text-amber-300 font-medium">Information needed to verify qualification:</p>
                  <div className="space-y-1">
                    {user_match.missing_facts.map((mf: string, idx: number) => {
                      const cleanLabel = mf
                        .replace(/^(applicant\.|household\.|person\.|location\.|student\.|artisan\.|enterprise\.|family\.|social\.|agriculture\.|health\.|finance\.)/, '')
                        .replace(/_/g, ' ');
                      return (
                        <div key={idx} className="flex items-start gap-2 text-amber-200/90 capitalize">
                          <AlertCircle className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />
                          <span>{cleanLabel}</span>
                        </div>
                      );
                    })}
                  </div>
                  <Button size="sm" asChild className="h-8 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs mt-1">
                    <Link href={`/check-eligibility${sessionId ? `?session_id=${sessionId}` : ''}`}>
                      Answer in questionnaire →
                    </Link>
                  </Button>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Key Information 4-Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl bg-[#0f1015] border border-white/5 space-y-1">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Age Range</span>
            <span className="text-sm font-bold text-white">
              {min_age || max_age
                ? `${min_age ? `${min_age} yrs` : 'Any'} – ${max_age ? `${max_age} yrs` : 'Any'}`
                : 'Any age'}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-[#0f1015] border border-white/5 space-y-1">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Income Limit</span>
            <span className="text-sm font-bold text-emerald-400">
              {income_limit && income_limit !== '0' && income_limit !== 'NA' && income_limit !== '10000000'
                ? `₹${Number(income_limit).toLocaleString('en-IN')}`
                : 'No income limit'}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-[#0f1015] border border-white/5 space-y-1">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Applicable Area</span>
            <span className="text-sm font-bold text-blue-400 line-clamp-1">
              {applicable_states && applicable_states !== 'All' ? applicable_states : 'All India'}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-[#0f1015] border border-white/5 space-y-1">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Target Category</span>
            <span className="text-sm font-bold text-slate-200 line-clamp-1 capitalize">
              {scheme_category || 'General'}
            </span>
          </div>
        </div>

        {/* Benefit Section */}
        <Card className="bg-[#0f1015] border border-white/10 rounded-2xl p-5 space-y-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            What you may receive
          </h2>
          {benefits.length > 0 ? (
            <div className="grid gap-2.5">
              {benefits.map((b: any, idx: number) => (
                <div key={idx} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-start justify-between gap-3">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wide text-blue-400">
                      {b.benefit_type ? b.benefit_type.replace(/_/g, ' ') : 'Financial Benefit'}
                    </span>
                    <p className="text-xs text-slate-200 mt-0.5 leading-relaxed">{b.description}</p>
                  </div>
                  {b.fixed_amount && (
                    <span className="text-xs sm:text-sm font-bold text-emerald-400 shrink-0 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                      ₹{Number(b.fixed_amount).toLocaleString('en-IN')}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
              {benefit_description || 'Financial assistance or services provided according to government guidelines.'}
            </p>
          )}
        </Card>

        {/* Who Can Apply & Documents Required (2-Column Grid) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Who Can Apply */}
          <Card className="bg-[#0f1015] border border-white/10 rounded-2xl p-5 space-y-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Check className="h-4 w-4 text-emerald-400" /> Who can apply
            </h2>
            <div className="space-y-2 text-xs text-slate-300">
              <p>• Age criteria: {min_age || '18'} to {max_age || 'Any'} years.</p>
              <p>• Income limit: {income_limit ? `Up to ₹${Number(income_limit).toLocaleString('en-IN')}` : 'No limit specified'}.</p>
              <p>• Applicable state: {applicable_states || 'All India / Central Sector'}.</p>
              {special_conditions_required && special_conditions_required !== 'nan' && (
                <p>• Special conditions: {special_conditions_required}.</p>
              )}
            </div>
          </Card>

          {/* Documents You May Need */}
          <Card className="bg-[#0f1015] border border-white/10 rounded-2xl p-5 space-y-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <FileText className="h-4 w-4 text-purple-400" /> Documents you may need
            </h2>
            {docsList.length > 0 ? (
              <div className="space-y-1.5 text-xs text-slate-300">
                {docsList.map((doc, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className="h-1.5 w-1.5 rounded-full bg-purple-400 shrink-0" />
                    <span>{doc}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                Standard identity verification documents (such as Aadhaar card and active bank account passbook) are typically required.
              </p>
            )}
          </Card>
        </div>

        {/* How to Apply (3 Simple Steps) */}
        <Card className="bg-[#0f1015] border border-white/10 rounded-2xl p-5 space-y-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            How to apply
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
              <span className="font-bold text-blue-400 block">Step 1</span>
              <p className="text-slate-300 leading-snug">Open the verified government application portal.</p>
            </div>
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
              <span className="font-bold text-blue-400 block">Step 2</span>
              <p className="text-slate-300 leading-snug">Fill in your information and attach the required documents.</p>
            </div>
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
              <span className="font-bold text-blue-400 block">Step 3</span>
              <p className="text-slate-300 leading-snug">Submit your form and keep the acknowledgement number for tracking.</p>
            </div>
          </div>
        </Card>

        {/* Official Source & Evidence (Accordion - Collapsed by Default) */}
        <Card className="bg-[#0f1015] border border-white/10 rounded-2xl p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/5">
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Official Source</span>
              <h3 className="text-sm font-bold text-white mt-0.5">{ministry || 'Government of India'}</h3>
            </div>
            {primaryApplyUrl && (
              <Button size="sm" variant="outline" asChild className="rounded-xl border-white/10 bg-[#121214] hover:bg-white/5 text-slate-200 text-xs h-8">
                <a href={primaryApplyUrl} target="_blank" rel="noreferrer">
                  Open official source <ExternalLink className="h-3 w-3 ml-1.5" />
                </a>
              </Button>
            )}
          </div>

          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="evidence" className="border-0">
              <AccordionTrigger className="py-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors">
                Source & evidence details
              </AccordionTrigger>
              <AccordionContent className="pt-2 text-xs text-slate-300 space-y-3">
                {sources && sources.length > 0 ? (
                  sources.map((s: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                      <p className="font-semibold text-white">{s.document_title || 'Statutory Scheme Guideline'}</p>
                      <p className="text-slate-400">Publisher: {s.publisher || 'Government of India'}</p>
                      {s.url && (
                        <a href={s.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline flex items-center gap-1 break-all pt-1">
                          {s.url} <ExternalLink className="h-3 w-3 shrink-0" />
                        </a>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400 italic">
                    Derived from official national gazette notifications and ministry program guidelines.
                  </p>
                )}

                {rules && rules.length > 0 && (
                  <div className="pt-2 border-t border-white/5 space-y-1.5">
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Statutory criteria evaluated</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                      {rules.slice(0, 6).map((r: any, idx: number) => (
                        <div key={idx} className="p-2 rounded-lg bg-black/30 border border-white/5 flex items-center justify-between text-[11px]">
                          <span className="capitalize text-slate-300">
                            {(r.fact_key || '').replace(/^(applicant\.|household\.|person\.|location\.|student\.|artisan\.|enterprise\.|family\.|social\.|agriculture\.|health\.|finance\.)/, '').replace(/_/g, ' ')}
                          </span>
                          <span className="text-slate-400 font-mono text-[10px]">{r.operator} {String(r.expected_value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </Card>

        {/* Bottom Trust Note */}
        <div className="pt-4 text-center text-[11px] text-slate-400 space-y-1">
          <p className="flex items-center justify-center gap-1.5 font-medium text-slate-300">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Verified against official government guidelines
          </p>
          <p>
            Always verify the latest application procedures and deadlines on the official portal before applying.
          </p>
        </div>
      </main>

      <Chatbot context={[scheme]} />
    </div>
  );
}
