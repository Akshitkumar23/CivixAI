import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://localhost:8000';

// ── Field name normaliser ──
function normalisePaylod(raw: Record<string, any>): Record<string, any> {
  const result: Record<string, any> = {};

  const setIfDefined = (targetKey: string, val: any) => {
    if (val !== undefined && val !== null && val !== '') {
      result[targetKey] = val;
    }
  };

  setIfDefined('age', raw.age);
  setIfDefined('annualIncome', raw.annualIncome ?? raw.income ?? raw.annual_income);
  setIfDefined('state', raw.state);
  setIfDefined('caste', raw.caste ?? raw.category);
  setIfDefined('occupation', raw.occupation);
  setIfDefined('gender', raw.gender);
  setIfDefined('maritalStatus', raw.maritalStatus ?? raw.marital_status);
  setIfDefined('urbanRural', raw.urbanRural ?? raw.urban_rural);
  setIfDefined('educationLevel', raw.educationLevel ?? raw.education_level);
  setIfDefined('digitalLiteracy', raw.digitalLiteracy ?? raw.digital_literacy);
  setIfDefined('familyIncome', raw.familyIncome ?? raw.family_income);
  setIfDefined('monthlyExpenses', raw.monthlyExpenses ?? raw.monthly_expenses);
  setIfDefined('monthlySavings', raw.monthlySavings ?? raw.monthly_savings);
  setIfDefined('familySize', raw.familySize ?? raw.family_size);
  setIfDefined('landSize', raw.landSize ?? raw.land_size);
  setIfDefined('isSingleGirlChild', raw.isSingleGirlChild ?? raw.is_single_girl_child);
  setIfDefined('isWidowOrSenior', raw.isWidowOrSenior ?? raw.is_widow_or_senior);
  setIfDefined('employmentType', raw.employmentType ?? raw.employment_type);
  setIfDefined('skillCertification', raw.skillCertification ?? raw.skill_certification);
  setIfDefined('loanRequirement', raw.loanRequirement ?? raw.loan_requirement);
  setIfDefined('hasLand', raw.hasLand ?? raw.has_land);
  setIfDefined('hasDisability', raw.hasDisability ?? raw.has_disability);
  setIfDefined('hasAvailedSimilarScheme', raw.hasAvailedSimilarScheme ?? raw.has_availed_similar_scheme);
  setIfDefined('isTaxPayer', raw.isTaxPayer ?? raw.is_tax_payer);
  setIfDefined('isBankLinked', raw.isBankLinked ?? raw.is_bank_linked);
  setIfDefined('isBPL', raw.isBPL ?? raw.is_bpl);
  setIfDefined('isMinority', raw.isMinority ?? raw.is_minority);
  setIfDefined('hasSmartphone', raw.hasSmartphone ?? raw.has_smartphone);
  setIfDefined('hasInternet', raw.hasInternet ?? raw.has_internet);
  setIfDefined('hasInsurance', raw.hasInsurance ?? raw.has_insurance);
  setIfDefined('hasPension', raw.hasPension ?? raw.has_pension);
  if (Array.isArray(raw.prioritySchemes) && raw.prioritySchemes.length > 0) {
    result.prioritySchemes = raw.prioritySchemes;
  }
  return result;
}

/**
 * POST /api/recommend
 * Proxies to the Python 5-agent pipeline's /api/recommend endpoint.
 * Returns the full recommendation response including personalized GenAI descriptions.
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get('session_id');

    if (!sessionId) {
      return NextResponse.json({ error: 'session_id query parameter required' }, { status: 400 });
    }

    const response = await fetch(`${ML_SERVICE_URL}/v1/recommendations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, top_k: 50 }),
      cache: 'no-store'
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(`[/api/recommend GET] ML Service Error ${response.status}: ${errText}`);
      throw new Error(`ML Service failed: ${response.statusText}`);
    }

    const data = await response.json();
    return formatRecommendationResponse(data);
  } catch (error: any) {
    console.error('[/api/recommend GET] Proxy Error:', error);
    return NextResponse.json({
      success: false,
      error: 'The AI Recommendation Engine is currently unavailable. Please ensure the backend is running on port 8000.',
      fallback: true,
    }, { status: 503 });
  }
}

function formatRecommendationResponse(data: any) {
  const ranked: any[] = data.ranked_schemes ?? data.recommended ?? [];
  const notEligible: any[] = data.not_eligible_schemes ?? [];

  // Combine all evaluated schemes so schemeDetails preserves ALL 4 statuses
  const seenIds = new Set<string>();
  const allEvaluatedSchemes: any[] = [];

  for (const s of ranked) {
    const id = s.scheme_id || s.id;
    if (id && !seenIds.has(id)) {
      seenIds.add(id);
      allEvaluatedSchemes.push(s);
    }
  }

  for (const s of notEligible) {
    const id = s.scheme_id || s.id;
    if (id && !seenIds.has(id)) {
      seenIds.add(id);
      allEvaluatedSchemes.push({
        ...s,
        eligibility_status: 'NOT_ELIGIBLE',
        eligible: false,
      });
    }
  }

  const schemeDetails = allEvaluatedSchemes.map((s: any) => {
    const rawType = (s.type || s.benefit_type || 'scheme').toLowerCase();
    const benefitType = ['loan', 'insurance'].includes(rawType) ? rawType : 'scheme';
    const rawConf = s.confidence ?? s.confidence_score ?? s.match_score ?? 0.5;
    const confidence = rawConf <= 1 ? Math.round(rawConf * 100) : Math.round(rawConf);

    return {
      id:                  s.scheme_id || s.id,
      name:                s.scheme_name ?? s.name,
      type:                benefitType,
      benefit_type:        benefitType,
      eligible:            s.eligible !== undefined ? s.eligible : (s.eligibility_status === 'ELIGIBLE'),
      eligibility_status:  s.eligibility_status || (s.eligible ? 'ELIGIBLE' : 'NEEDS_INFO'),
      confidence,
      application_readiness: s.application_readiness !== undefined ? s.application_readiness : 1.0,
      match_score:         s.match_score ?? s.confidence_score,
      rank_score:          s.rank_score,
      criteria_met_count:  s.criteria_met_count ?? (s.reasons?.length || (s.eligible ? 1 : 0)),
      criteria_total_count: s.criteria_total_count ?? Math.max(1, (s.reasons?.length || 0) + (s.missing_facts?.length || 0)),
      criteria_progress_pct: s.criteria_progress_pct ?? (s.eligibility_status === 'ELIGIBLE' ? 100 : Math.round(((s.reasons?.length || 0) / Math.max(1, (s.reasons?.length || 0) + (s.missing_facts?.length || 0))) * 100)),
      why:                 s.why ?? (s.reasons && s.reasons.length > 0 ? s.reasons[0] : ''),
      eligibility_summary: s.eligibility_summary ?? '',
      tldr_bullets:        s.tldr_bullets ?? [],
      how_to_apply:        s.how_to_apply ?? [],
      description:         s.description ?? s.benefit_description ?? '',
      benefit_amount:      s.benefit_amount ?? '',
      benefits:            s.benefits ?? [],
      reasons:             s.reasons ?? [],
      path_to_eligibility: s.path_to_eligibility ?? [],
      missing_inputs:      s.missing_facts ?? s.missing_criteria ?? [],
      missing_facts:       s.missing_facts ?? s.missing_criteria ?? [],
      category:            s.category ?? '',
      ministry:            s.ministry ?? '',
      level:               s.level ?? '',
      url:                 s.application_url ?? s.apply_link ?? s.url ?? '',
      source_url:          s.source_url ?? s.apply_link ?? s.url ?? '',
      documents:           s.documents_required ?? [],
    };
  });

  const eligibleItems = schemeDetails.filter(s => s.eligibility_status === 'ELIGIBLE');
  const needsInfoItems = schemeDetails.filter(s => s.eligibility_status === 'NEEDS_INFO');
  const needsVerificationItems = schemeDetails.filter(s => s.eligibility_status === 'NEEDS_VERIFICATION');
  const notEligibleItems = schemeDetails.filter(s => s.eligibility_status === 'NOT_ELIGIBLE');

  const counts = {
    total:              schemeDetails.length,
    eligible:           eligibleItems.length,
    needs_info:         needsInfoItems.length,
    needs_verification: needsVerificationItems.length,
    not_eligible:       notEligibleItems.length,
  };

  const summary = data.summary ?? {
    total:     schemeDetails.length,
    loans:     schemeDetails.filter((r: any) => r.type === 'loan').length,
    insurance: schemeDetails.filter((r: any) => r.type === 'insurance').length,
    schemes:   schemeDetails.filter((r: any) => r.type === 'scheme').length,
  };

  return NextResponse.json({
    success:          true,
    run_id:           data.run_id,
    session_id:       data.session_id,
    profile_hash:     data.profile_hash,
    source:           data.source,
    normalized_fact_keys: data.normalized_fact_keys,
    counts,
    schemeDetails,
    ranked_schemes:   schemeDetails.filter(s => s.eligibility_status !== 'NOT_ELIGIBLE'),
    eligibleSchemes:  eligibleItems.map((r: any) => r.name),
    eligible_schemes: eligibleItems,
    needs_info_schemes: needsInfoItems,
    needs_verification_schemes: needsVerificationItems,
    not_eligible_schemes: notEligibleItems,
    discovery_schemes: data.discovery_schemes ?? [],
    authoritative_pool: data.authoritative_pool,
    discovery_pool:   data.discovery_pool,
    confidence_score: data.confidence_score ?? 0.8,
    summary,
    why_not_eligible: data.why_not_eligible ?? [],
    knowledge_graph:  data.knowledge_graph ?? [],
    _timings:         data._timings,
  });
}

/**
 * POST /api/recommend
 * Proxies to Python recommendation engine.
 * Supports { session_id } or { ...profileFacts }.
 */
export async function POST(request: Request) {
  try {
    const rawPayload = await request.json();
    const programmeKind = rawPayload.programme_kind || rawPayload.type;

    const requestBody: Record<string, any> = { top_k: 50 };
    if (programmeKind && programmeKind !== 'all') {
      requestBody.programme_kind = programmeKind;
    }
    if (rawPayload.source) {
      requestBody.source = rawPayload.source;
    }

    let response;
    if (rawPayload.session_id) {
      requestBody.session_id = rawPayload.session_id;
      if (rawPayload.profile) {
        requestBody.profile = normalisePaylod(rawPayload.profile);
      }
      response = await fetch(`${ML_SERVICE_URL}/v1/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });
    } else {
      const rawProfile = (rawPayload && typeof rawPayload === 'object' && rawPayload.profile) ? rawPayload.profile : rawPayload;
      requestBody.profile = normalisePaylod(rawProfile);
      response = await fetch(`${ML_SERVICE_URL}/v1/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });
      // Fallback to legacy endpoint if v1/recommendations failed
      if (!response.ok) {
        response = await fetch(`${ML_SERVICE_URL}/api/recommend`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody.profile),
        });
      }
    }

    if (!response.ok) {
      const errText = await response.text();
      console.error(`[/api/recommend POST] ML Service Error ${response.status}: ${errText}`);
      throw new Error(`ML Service failed: ${response.statusText}`);
    }

    const data = await response.json();
    return formatRecommendationResponse(data);
  } catch (error: any) {
    console.error('[/api/recommend] Proxy Error:', error);
    return NextResponse.json({
      success:  false,
      error:    'The AI Recommendation Engine is currently unavailable. Please ensure the backend is running on port 8000.',
      fallback: true,
    }, { status: 503 });
  }
}
