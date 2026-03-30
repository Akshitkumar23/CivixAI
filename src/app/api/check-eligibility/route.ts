import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type SchemeRow = {
  scheme_id?: string;
  scheme_name?: string;
  ministry?: string;
  scheme_level?: string;
  scheme_category?: string;
  applicable_states?: string;
  min_age?: string;
  max_age?: string;
  income_limit?: string;
  benefit_description?: string;
  real_description?: string;
  documents_required?: string;
  application_url?: string;
  source_url?: string;
  benefit_type?: string;
  // New enriched columns
  gender_eligibility?: string;
  caste_eligibility?: string;
  disability_required?: string;
  occupation_eligibility?: string;
  benefit_amount?: string;
  tags?: string;
  education_level_required?: string;
  urban_rural_eligibility?: string;
  marital_status_required?: string;
  employment_type_eligibility?: string;
  is_bpl_only?: string;
  application_deadline?: string;
  processing_time?: string;
  popularity_score?: string;
  is_scheme_active?: string;
};

type EligibilityPayload = {
  age?: number;
  income?: number;
  annualIncome?: number;
  state?: string;
  gender?: string;
  caste?: string;
  occupation?: string;
  educationLevel?: string;
  urbanRural?: string;
  maritalStatus?: string;
  isBPL?: boolean | number;
  isMinority?: boolean | number;
  hasDisability?: boolean | number;
  hasLand?: boolean | number;
};

const DATA_PATH = path.join(process.cwd(), 'data', 'master', 'schemes_master.csv');
const DEFAULT_THRESHOLD = 0.6;
const RESULT_LIMIT = 500;
const ML_TIMEOUT_MS = 60000;

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
    const trimmed = value.replace(/,/g, '').trim();
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

function computeConfidence(input: {
  specificState: boolean;
  hasConstraints: boolean;
  schemeName: string;
  schemeCategory: string;
  schemeDesc: string;
  schemeGenderEligibility?: string;
  schemeCasteEligibility?: string;
  schemeDisabilityRequired?: string;
  schemeOccupationEligibility?: string;
  userAge?: number;
  userIncome?: number;
  userCaste?: string;
  userOccupation?: string;
  userGender?: string;
  userHasDisability?: boolean;
}): number {
  let confidence = 0.50;

  if (input.specificState) confidence += 0.12;
  if (input.hasConstraints)  confidence += 0.08;

  // ── Structured Gender Matching (new column) ────────────────────────────────
  const schemeGender = (input.schemeGenderEligibility || 'all').toLowerCase();
  const userGender   = (input.userGender || '').toLowerCase();
  if (schemeGender === 'female') {
    if (userGender === 'female') confidence += 0.18;
    else if (userGender === 'male') confidence -= 0.55;
    // unknown gender → small penalty
    else confidence -= 0.05;
  } else if (schemeGender === 'male') {
    if (userGender === 'male') confidence += 0.12;
    else if (userGender === 'female') confidence -= 0.50;
  }

  // ── Structured Caste Matching ─────────────────────────────────────────────
  const schemeCastes = (input.schemeCasteEligibility || 'all').toLowerCase().split(',').map(s => s.trim());
  const userCaste    = (input.userCaste || '').toLowerCase();
  if (!schemeCastes.includes('all')) {
    if (userCaste && schemeCastes.some(c => c === userCaste || userCaste.includes(c))) {
      confidence += 0.18;
    } else if (userCaste && !schemeCastes.some(c => c === userCaste)) {
      confidence -= 0.55; // wrong caste, very likely ineligible
    } else {
      confidence -= 0.08; // caste unknown — reduce slightly
    }
  }

  // ── Structured Disability Matching ───────────────────────────────────────
  if (input.schemeDisabilityRequired === 'true') {
    if (input.userHasDisability === true)  confidence += 0.18;
    else if (input.userHasDisability === false) confidence -= 0.55;
    else confidence -= 0.05;
  }

  // ── Structured Occupation Matching ────────────────────────────────────────
  const schemeOccs = (input.schemeOccupationEligibility || 'all').toLowerCase().split(',').map(s => s.trim());
  const userOcc    = (input.userOccupation || '').toLowerCase();
  if (!schemeOccs.includes('all') && schemeOccs.length > 0) {
    if (userOcc && schemeOccs.some(o => userOcc.includes(o) || o.includes(userOcc))) {
      confidence += 0.15;
    } else if (userOcc && !schemeOccs.some(o => userOcc.includes(o) || o.includes(userOcc))) {
      confidence -= 0.45;
    } else {
      confidence -= 0.05;
    }
  } else {
    // all occupations — small bump for keyword match
    const combined = (input.schemeName + ' ' + input.schemeCategory).toLowerCase();
    if (userOcc === 'farmer' && (combined.includes('kisan') || combined.includes('agriculture'))) confidence += 0.10;
    if (userOcc === 'student' && combined.includes('scholarship')) confidence += 0.10;
  }

  return Math.max(0, Math.min(0.98, confidence));
}

async function loadSchemes(): Promise<SchemeRow[]> {
  try {
    const stat = await fs.stat(DATA_PATH);
    // Always reload — disable stale cache so enrich updates are reflected immediately
    void stat;

    const csvText = await fs.readFile(DATA_PATH, 'utf-8');
    const rows = parseCsv(csvText);
    if (rows.length === 0) {
      cachedSchemes = [];
      cachedMtimeMs = stat.mtimeMs;
      return [];
    }

    const headers = rows[0].map((header) => header.trim().replace(/^\uFEFF/, ''));
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
      real_description: getValue(row, 'real_description'),
      ministry: getValue(row, 'ministry'),
      scheme_level: getValue(row, 'scheme_level'),
      documents_required: getValue(row, 'documents_required'),
      application_url: getValue(row, 'application_url'),
      source_url: getValue(row, 'source_url'),
      benefit_type: getValue(row, 'benefit_type'),
      // New enriched columns
      gender_eligibility: getValue(row, 'gender_eligibility'),
      caste_eligibility: getValue(row, 'caste_eligibility'),
      disability_required: getValue(row, 'disability_required'),
      occupation_eligibility: getValue(row, 'occupation_eligibility'),
      benefit_amount: getValue(row, 'benefit_amount'),
      tags: getValue(row, 'tags'),
      education_level_required: getValue(row, 'education_level_required'),
      urban_rural_eligibility: getValue(row, 'urban_rural_eligibility'),
      marital_status_required: getValue(row, 'marital_status_required'),
      employment_type_eligibility: getValue(row, 'employment_type_eligibility'),
      is_bpl_only: getValue(row, 'is_bpl_only'),
      application_deadline: getValue(row, 'application_deadline'),
      processing_time: getValue(row, 'processing_time'),
      popularity_score: getValue(row, 'popularity_score'),
      is_scheme_active: getValue(row, 'is_scheme_active'),
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
  const baseUrl = process.env.ML_API_URL || process.env.NEXT_PUBLIC_ML_API_URL || 'http://127.0.0.1:8000';
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

    // Create maps for quick lookup of benefits, reasoning and knowledge graph
    const whyMap = new Map();
    if (Array.isArray(data?.why_this_scheme)) {
      data.why_this_scheme.forEach((w: any) => whyMap.set(w.scheme_id, w));
    }
    
    const kgMap = new Map();
    if (Array.isArray(data?.knowledge_graph)) {
      data.knowledge_graph.forEach((kg: any) => kgMap.set(kg.scheme_id, kg.related));
    }

    const schemes = await loadSchemes();
    const schemeMap = new Map();
    schemes.forEach((s) => {
      const key = (s.scheme_id || '').toLowerCase();
      if (key) schemeMap.set(key, s);
    });

    const schemeDetails = rankedSchemes.map((item: any) => {
      const name = item?.name || item?.scheme_name || item?.scheme_id || 'Unknown Scheme';
      const key = (item?.scheme_id || '').toLowerCase();
      const details = schemeMap.get(key);
      const why = whyMap.get(item?.scheme_id);
      const related = kgMap.get(item?.scheme_id) || [];

      return {
        id: item?.scheme_id,
        name,
        eligible: item?.eligible !== false,
        confidence: typeof item?.confidence === 'number' ? item.confidence * 100 : undefined,
        benefit_score: item?.benefit_score,
        rank_score: item?.rank_score,
        threshold: typeof item?.threshold === 'number' ? item.threshold : DEFAULT_THRESHOLD,
        description: item?.description || details?.benefit_description,
        ministry: item?.ministry || details?.ministry,
        level: item?.level || details?.scheme_level,
        category: item?.category || details?.scheme_category,
        states: item?.states || details?.applicable_states,
        documents: item?.documents || details?.documents_required,
        url: item?.url || details?.application_url || item?.application_url,
        benefit_type: item?.benefit_type || details?.benefit_type || 'scheme',
        reasons: item?.reasons || why?.reasons || [],
        missing_inputs: item?.missing || why?.missing || [],
        path_to_eligibility: item?.path_to_eligibility || why?.path_to_eligibility || [],
        related_schemes: related
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

      // Strict Demographic Rules: If explicit rules are broken, drop immediately
      const schemeGender = (scheme.gender_eligibility || 'all').toLowerCase().trim();
      const userGender = String(payload.gender || '').toLowerCase().trim();
      if (schemeGender !== 'all' && schemeGender !== 'nan' && schemeGender !== 'any' && userGender) {
        if (schemeGender !== userGender) return null;
      }

      const schemeOccs = (scheme.occupation_eligibility || 'all').toLowerCase().split(',').map(s => s.trim());
      const userOcc    = String(payload.occupation || '').toLowerCase().trim();
      if (!schemeOccs.includes('all') && !schemeOccs.includes('nan') && !schemeOccs.includes('any') && schemeOccs.length > 0 && userOcc) {
        if (!schemeOccs.some(o => userOcc.includes(o) || o.includes(userOcc) || userOcc === o)) {
          return null;
        }
      }

      const schemeCastes = (scheme.caste_eligibility || 'all').toLowerCase().split(',').map(s => s.trim());
      const userCaste = String(payload.caste || payload.category || '').toLowerCase().trim();
      if (!schemeCastes.includes('all') && !schemeCastes.includes('nan') && !schemeCastes.includes('any') && schemeCastes.length > 0 && userCaste) {
        if (!schemeCastes.some(c => userCaste.includes(c) || c.includes(userCaste) || userCaste === c)) {
          return null;
        }
      }
      
      const schemeDisab = String(scheme.disability_required || 'false').toLowerCase().trim();
      if (schemeDisab === 'true' && payload.hasDisability === false) {
        return null;
      }

      // Strict Text-based Keyword Rejections (Fallback since DB might lack structural occupation rules)
      const combinedText = `${scheme.scheme_name || ''} ${scheme.benefit_description || ''} ${scheme.scheme_category || ''}`.toLowerCase();
      
      if (userOcc === 'student') {
        if (combinedText.includes('farmer') || combinedText.includes('kisan') || combinedText.includes('agriculture') || combinedText.includes('krishi') || combinedText.includes('maternity') || combinedText.includes('pregnancy')) {
          return null; // A student should not get farmer or maternity schemes
        }
      }
      
      if (userOcc === 'farmer') {
        if (combinedText.includes('student') || combinedText.includes('scholarship') || combinedText.includes('fellowship') || combinedText.includes('school')) {
          return null; // A farmer should not get student scholarships
        }
      }

      if (userGender === 'male') {
        if (combinedText.includes('women') || combinedText.includes('girl') || combinedText.includes('maternity') || combinedText.includes('mother')) {
          return null; // A male should not get women's schemes
        }
      }
      
      if (userCaste !== 'sc' && userCaste !== 'st') {
        if (combinedText.includes('scheduled caste') || combinedText.includes(' sc ') || combinedText.includes('scheduled tribe') || combinedText.includes(' st ')) {
            return null;
        }
      }

      if (userCaste !== 'obc') {
        if (combinedText.includes('obc') || combinedText.includes('backward class')) {
            return null;
        }
      }
      
      if (payload.hasDisability === false) {
          if (combinedText.includes('disability') || combinedText.includes('pwd') || combinedText.includes('divyang')) {
              return null;
          }
      }

      const hasConstraints = minAge !== undefined || maxAge !== undefined || incomeLimit !== undefined;
      const confidence = computeConfidence({
        specificState: match.specific,
        hasConstraints,
        schemeName: scheme.scheme_name || '',
        schemeCategory: scheme.scheme_category || '',
        schemeDesc: scheme.benefit_description || '',
        schemeGenderEligibility: scheme.gender_eligibility,
        schemeCasteEligibility: scheme.caste_eligibility,
        schemeDisabilityRequired: scheme.disability_required,
        schemeOccupationEligibility: scheme.occupation_eligibility,
        userAge: age,
        userIncome: income,
        userCaste: String(payload.caste || payload.category || ''),
        userOccupation: String(payload.occupation || ''),
        userGender: String(payload.gender || ''),
        userHasDisability: payload.hasDisability as boolean | undefined,
      });

      // Filter out very low confidence
      if (confidence < 0.30) return null;

      // Compute missing inputs using new structured fields
      const missing_inputs: string[] = [];
      if (confidence < 0.95) {
        const genderElig = (scheme.gender_eligibility || 'all').toLowerCase();
        const casteElig  = (scheme.caste_eligibility  || 'all').toLowerCase();
        const disabReq   = scheme.disability_required === 'true';
        const occElig    = (scheme.occupation_eligibility || 'all').toLowerCase();

        if (genderElig !== 'all' && !payload.gender)
          missing_inputs.push('Gender');
        if (casteElig !== 'all' && !payload.caste && !payload.category)
          missing_inputs.push('Caste Category');
        if (disabReq && payload.hasDisability === undefined)
          missing_inputs.push('Disability Status');
        if (occElig !== 'all' && !payload.occupation)
          missing_inputs.push('Occupation');
        if (!payload.isBankLinked && (scheme.tags || '').includes('DBT'))
          missing_inputs.push('Bank Linked (DBT)');
        if (!payload.income && !payload.familyIncome && toNumber(scheme.income_limit))
          missing_inputs.push('Income Details');
      }

      return { scheme, confidence, missing_inputs };
    })
    .filter(Boolean) as Array<{ scheme: SchemeRow; confidence: number; missing_inputs: string[] }>;

  scored.sort((a, b) => b.confidence - a.confidence);

  const schemeDetails = scored.slice(0, RESULT_LIMIT).map((item) => ({
    id: item.scheme.scheme_id || item.scheme.scheme_name,
    name: item.scheme.scheme_name || item.scheme.scheme_id || 'Unknown Scheme',
    eligible: true,
    confidence: item.confidence * 100,
    threshold: DEFAULT_THRESHOLD,
    description: item.scheme.real_description || item.scheme.benefit_description,
    ministry: item.scheme.ministry,
    level: item.scheme.scheme_level,
    category: item.scheme.scheme_category,
    states: item.scheme.applicable_states,
    documents: item.scheme.documents_required,
    url: item.scheme.application_url,
    benefit_type: item.scheme.benefit_type || 'scheme',
    benefit_amount: item.scheme.benefit_amount,
    tags: item.scheme.tags,
    missing_inputs: item.missing_inputs
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
