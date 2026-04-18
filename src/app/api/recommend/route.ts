import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://localhost:8000';

// ── Field name normaliser ──
function normalisePaylod(raw: Record<string, any>): Record<string, any> {
  return {
    age:           raw.age,
    annualIncome:  raw.annualIncome ?? raw.income ?? raw.annual_income ?? 0,
    state:         raw.state,
    caste:         raw.caste ?? raw.category,
    occupation:    raw.occupation,
    gender:        raw.gender,
    maritalStatus: raw.maritalStatus ?? raw.marital_status,
    urbanRural:    raw.urbanRural ?? raw.urban_rural,
    educationLevel:   raw.educationLevel ?? raw.education_level,
    digitalLiteracy:  raw.digitalLiteracy ?? raw.digital_literacy,
    familyIncome:    raw.familyIncome ?? raw.family_income ?? 0,
    monthlyExpenses: raw.monthlyExpenses ?? raw.monthly_expenses ?? 0,
    monthlySavings:  raw.monthlySavings ?? raw.monthly_savings ?? 0,
    familySize:       raw.familySize ?? raw.family_size ?? 1,
    landSize:         raw.landSize ?? raw.land_size ?? 0,
    isSingleGirlChild:raw.isSingleGirlChild ?? raw.is_single_girl_child ?? false,
    isWidowOrSenior:  raw.isWidowOrSenior ?? raw.is_widow_or_senior ?? false,
    employmentType:    raw.employmentType ?? raw.employment_type,
    skillCertification:raw.skillCertification ?? raw.skill_certification,
    loanRequirement:   raw.loanRequirement ?? raw.loan_requirement ?? 'none',
    hasLand:               raw.hasLand ?? raw.has_land ?? false,
    hasDisability:         raw.hasDisability ?? raw.has_disability ?? false,
    hasAvailedSimilarScheme:raw.hasAvailedSimilarScheme ?? raw.has_availed_similar_scheme ?? false,
    isTaxPayer:            raw.isTaxPayer ?? raw.is_tax_payer ?? false,
    isBankLinked:          raw.isBankLinked ?? raw.is_bank_linked ?? false,
    isBPL:                 raw.isBPL ?? raw.is_bpl ?? false,
    isMinority:            raw.isMinority ?? raw.is_minority ?? false,
    hasSmartphone:         raw.hasSmartphone ?? raw.has_smartphone ?? false,
    hasInternet:           raw.hasInternet ?? raw.has_internet ?? false,
    hasInsurance:          raw.hasInsurance ?? raw.has_insurance ?? false,
    hasPension:            raw.hasPension ?? raw.has_pension ?? false,
    prioritySchemes:       raw.prioritySchemes ?? raw.priority_schemes ?? [],
  };
}

/**
 * POST /api/recommend
 * Proxies to the Python 5-agent pipeline's /api/recommend endpoint.
 * Returns the full recommendation response including personalized GenAI descriptions.
 */
export async function POST(request: Request) {
  try {
    const rawPayload = await request.json();
    const payload = normalisePaylod(rawPayload);

    const response = await fetch(`${ML_SERVICE_URL}/api/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(`[/api/recommend] ML Service Error ${response.status}: ${errText}`);
      throw new Error(`ML Service failed: ${response.statusText}`);
    }

    const data = await response.json();

    // Map ranked_schemes to schemeDetails format so the frontend works with both endpoints
    const rawSchemes: any[] = data.ranked_schemes ?? data.recommended ?? [];

    const schemeDetails = rawSchemes.map((s: any) => {
      const rawType = (s.type || s.benefit_type || 'scheme').toLowerCase();
      const benefitType = ['loan', 'insurance'].includes(rawType) ? rawType : 'scheme';
      const rawConf = s.confidence ?? s.match_score ?? 0.5;
      const confidence = rawConf <= 1 ? Math.round(rawConf * 100) : Math.round(rawConf);

      return {
        id:                  s.scheme_id,
        name:                s.scheme_name ?? s.name,
        type:                benefitType,
        benefit_type:        benefitType,
        eligible:            true,
        confidence,
        match_score:         s.match_score,
        rank_score:          s.rank_score,
        why:                 s.why ?? '',
        eligibility_summary: s.eligibility_summary ?? '',
        tldr_bullets:        s.tldr_bullets ?? [],
        how_to_apply:        s.how_to_apply ?? [],
        description:         s.description ?? s.benefit_description ?? '',
        benefit_amount:      s.benefit_amount ?? '',
        benefits:            s.benefits ?? [],
        reasons:             s.reasons ?? [],
        path_to_eligibility: s.path_to_eligibility ?? [],
        missing_inputs:      s.missing_criteria ?? [],
        category:            s.category ?? '',
        ministry:            s.ministry ?? '',
        level:               s.level ?? '',
        url:                 s.apply_link ?? s.url ?? '',
        source_url:          s.apply_link ?? s.url ?? '',
        documents:           s.documents_required ?? [],
      };
    });

    const summary = data.summary ?? {
      total:     schemeDetails.length,
      loans:     schemeDetails.filter((r: any) => r.type === 'loan').length,
      insurance: schemeDetails.filter((r: any) => r.type === 'insurance').length,
      schemes:   schemeDetails.filter((r: any) => r.type === 'scheme').length,
    };

    return NextResponse.json({
      success:          true,
      schemeDetails,
      eligibleSchemes:  schemeDetails.map((r: any) => r.name),
      confidence_score: data.confidence_score ?? 0.8,
      summary,
      why_not_eligible: data.why_not_eligible ?? [],
      knowledge_graph:  data.knowledge_graph ?? [],
      _timings:         data._timings,
    });

  } catch (error: any) {
    console.error('[/api/recommend] Proxy Error:', error);
    return NextResponse.json({
      success:  false,
      error:    'The AI Recommendation Engine is currently unavailable. Please ensure the backend is running on port 8000.',
      fallback: true,
    }, { status: 503 });
  }
}
