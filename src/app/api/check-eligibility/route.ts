import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const runtime = 'nodejs';

type SchemeRow = {
  scheme_id?: string;
  scheme_name?: string;
  scheme_category?: string;
  applicable_states?: string;
  min_age?: string;
  max_age?: string;
  income_limit?: string;
  benefit_description?: string;
  documents_required?: string;
  application_url?: string;
  source_url?: string;
};

type EligibilityPayload = {
  age?: number;
  income?: number;
  annualIncome?: number;
  state?: string;
};

const DATA_PATH = path.join(process.cwd(), 'data', 'master', 'schemes_master.csv');
const DEFAULT_THRESHOLD = 0.6;
const RESULT_LIMIT = 50;
const ML_TIMEOUT_MS = 2500;

let cachedSchemes: SchemeRow[] | null = null;
let cachedMtimeMs: number | null = null;

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === ',' && !inQuotes) {
      row.push(field);
      field = '';
      continue;
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && next === '\n') {
        i += 1;
      }
      row.push(field);
      field = '';
      if (row.length > 1 || (row[0] && row[0].trim())) {
        rows.push(row);
      }
      row = [];
      continue;
    }

    field += char;
  }

  row.push(field);
  if (row.length > 1 || (row[0] && row[0].trim())) {
    rows.push(row);
  }
  return rows;
}

function toNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) return undefined;
    const parsed = Number(trimmed);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
}

function normalizeStates(value?: string): string[] {
  if (!value) return [];
  return value
    .split(/[,|]/)
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function stateMatch(schemeStates: string[], userState?: string): { matches: boolean; specific: boolean } {
  if (schemeStates.length === 0) {
    return { matches: true, specific: false };
  }
  if (schemeStates.includes('all')) {
    return { matches: true, specific: false };
  }
  if (!userState) {
    return { matches: false, specific: false };
  }
  const normalized = userState.trim().toLowerCase();
  const isSpecific = schemeStates.includes(normalized);
  return { matches: isSpecific, specific: isSpecific };
}

function computeConfidence(input: { specific: boolean; hasConstraints: boolean }): number {
  let confidence = 0.7;
  if (input.specific) confidence += 0.15;
  if (input.hasConstraints) confidence += 0.05;
  return Math.min(0.95, confidence);
}

async function loadSchemes(): Promise<SchemeRow[]> {
  try {
    const stat = await fs.stat(DATA_PATH);
    if (cachedSchemes && cachedMtimeMs === stat.mtimeMs) {
      return cachedSchemes;
    }

    const csvText = await fs.readFile(DATA_PATH, 'utf-8');
    const rows = parseCsv(csvText);
    if (rows.length === 0) {
      cachedSchemes = [];
      cachedMtimeMs = stat.mtimeMs;
      return [];
    }

    const headers = rows[0].map((header) => header.trim());
    const index = new Map<string, number>();
    headers.forEach((header, i) => index.set(header, i));

    const getValue = (row: string[], key: string): string | undefined => {
      const idx = index.get(key);
      if (idx === undefined) return undefined;
      return row[idx]?.trim();
    };

    const parsed = rows.slice(1).map((row) => ({
      scheme_id: getValue(row, 'scheme_id'),
      scheme_name: getValue(row, 'scheme_name'),
      scheme_category: getValue(row, 'scheme_category'),
      applicable_states: getValue(row, 'applicable_states'),
      min_age: getValue(row, 'min_age'),
      max_age: getValue(row, 'max_age'),
      income_limit: getValue(row, 'income_limit'),
      benefit_description: getValue(row, 'benefit_description'),
      documents_required: getValue(row, 'documents_required'),
      application_url: getValue(row, 'application_url'),
      source_url: getValue(row, 'source_url')
    }));

    cachedSchemes = parsed;
    cachedMtimeMs = stat.mtimeMs;
    return parsed;
  } catch (error) {
    console.warn('Failed to load schemes data:', error);
    cachedSchemes = [];
    cachedMtimeMs = null;
    return [];
  }
}

function normalizePayload(payload: EligibilityPayload & Record<string, unknown>) {
  const normalized: Record<string, unknown> = { ...payload };
  if (payload.income !== undefined && payload.annualIncome === undefined) {
    normalized.annualIncome = payload.income;
  }
  return normalized;
}

async function tryMlService(payload: EligibilityPayload & Record<string, unknown>) {
  const baseUrl = process.env.ML_API_URL || process.env.NEXT_PUBLIC_ML_API_URL;
  if (!baseUrl) return null;

  try {
    const url = new URL('/api/recommend', baseUrl);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), ML_TIMEOUT_MS);
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(normalizePayload(payload)),
      cache: 'no-store',
      signal: controller.signal
    });
    clearTimeout(timeout);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const rankedSchemes = Array.isArray(data?.ranked_schemes) ? data.ranked_schemes : [];

    // Create maps for quick lookup of benefits and reasoning
    const whyMap = new Map();
    if (Array.isArray(data?.why_this_scheme)) {
      data.why_this_scheme.forEach((w: any) => whyMap.set(w.scheme_id, w));
    }

    const schemes = await loadSchemes();
    const schemeMap = new Map();
    schemes.forEach((s) => {
      const key = (s.scheme_id || s.scheme_id || '').toLowerCase();
      if (key) schemeMap.set(key, s);
    });

    const schemeDetails = rankedSchemes.map((item: any) => {
      const name = item?.name || item?.scheme_name || item?.scheme_id || 'Unknown Scheme';
      const key = (item?.scheme_id || '').toLowerCase();
      const details = schemeMap.get(key);
      const why = whyMap.get(item?.scheme_id);

      return {
        id: item?.scheme_id,
        name,
        eligible: item?.eligible !== false,
        confidence: typeof item?.confidence === 'number' ? item.confidence * 100 : undefined,
        benefit_score: item?.benefit_score,
        rank_score: item?.rank_score,
        threshold: typeof item?.threshold === 'number' ? item.threshold : DEFAULT_THRESHOLD,
        description: details?.benefit_description,
        category: details?.scheme_category,
        states: details?.applicable_states,
        documents: details?.documents_required,
        url: details?.application_url || item?.application_url,
        reasons: why?.reasons || [],
        missing: why?.missing || []
      };
    });

    return {
      success: true,
      schemeDetails,
      eligibleSchemes: schemeDetails.filter(s => s.eligible).map((item: any) => item.name),
      mlPrediction: true,
      mlFallback: false
    };
  } catch (error) {
    console.warn('ML service unavailable, using fallback:', error);
    return null;
  }
}

async function fallbackEligibility(payload: EligibilityPayload & Record<string, unknown>) {
  const schemes = await loadSchemes();
  const age = toNumber(payload.age);
  const income = toNumber(payload.income ?? payload.annualIncome);
  const state = typeof payload.state === 'string' ? payload.state.trim() : '';

  const scored = schemes
    .map((scheme) => {
      const minAge = toNumber(scheme.min_age);
      const maxAge = toNumber(scheme.max_age);
      const incomeLimit = toNumber(scheme.income_limit);

      if (minAge !== undefined && age !== undefined && age < minAge) return null;
      if (maxAge !== undefined && age !== undefined && age > maxAge) return null;
      if (incomeLimit !== undefined && income !== undefined && income > incomeLimit) return null;

      const states = normalizeStates(scheme.applicable_states);
      const match = stateMatch(states, state);
      if (!match.matches) return null;

      const hasConstraints = minAge !== undefined || maxAge !== undefined || incomeLimit !== undefined;
      const confidence = computeConfidence({ specific: match.specific, hasConstraints });

      return {
        scheme,
        confidence
      };
    })
    .filter(Boolean) as Array<{ scheme: SchemeRow; confidence: number }>;

  scored.sort((a, b) => b.confidence - a.confidence);

  const schemeDetails = scored.slice(0, RESULT_LIMIT).map((item) => ({
    id: item.scheme.scheme_id || item.scheme.scheme_name,
    name: item.scheme.scheme_name || item.scheme.scheme_id || 'Unknown Scheme',
    eligible: true,
    confidence: item.confidence,
    threshold: DEFAULT_THRESHOLD,
    description: item.scheme.benefit_description,
    category: item.scheme.scheme_category,
    states: item.scheme.applicable_states,
    documents: item.scheme.documents_required,
    url: item.scheme.application_url
  }));

  return {
    success: true,
    schemeDetails,
    eligibleSchemes: schemeDetails.map((item) => item.name),
    mlPrediction: false,
    mlFallback: true
  };
}

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => ({}))) as EligibilityPayload &
    Record<string, unknown>;

  const mlResponse = await tryMlService(payload);
  if (mlResponse) {
    return NextResponse.json(mlResponse);
  }

  const fallbackResponse = await fallbackEligibility(payload);
  return NextResponse.json(fallbackResponse);
}
