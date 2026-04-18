import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://localhost:8000';

// ── Field name normaliser: frontend uses mixed names, backend expects specific names ──
function normalisePaylod(raw: Record<string, any>): Record<string, any> {
  return {
    // Core required — fix legacy field names
    age:           raw.age,
    annualIncome:  raw.annualIncome ?? raw.income ?? raw.annual_income ?? 0,
    state:         raw.state,
    caste:         raw.caste ?? raw.category,               // frontend sends category
    occupation:    raw.occupation,

    // Demographics
    gender:        raw.gender,
    maritalStatus: raw.maritalStatus ?? raw.marital_status,
    urbanRural:    raw.urbanRural ?? raw.urban_rural,

    // Education & digital
    educationLevel:   raw.educationLevel ?? raw.education_level,
    digitalLiteracy:  raw.digitalLiteracy ?? raw.digital_literacy,

    // Financial
    familyIncome:    raw.familyIncome ?? raw.family_income ?? 0,
    monthlyExpenses: raw.monthlyExpenses ?? raw.monthly_expenses ?? 0,
    monthlySavings:  raw.monthlySavings ?? raw.monthly_savings ?? 0,

    // Family
    familySize:       raw.familySize ?? raw.family_size ?? 1,
    landSize:         raw.landSize ?? raw.land_size ?? 0,
    isSingleGirlChild:raw.isSingleGirlChild ?? raw.is_single_girl_child ?? false,
    isWidowOrSenior:  raw.isWidowOrSenior ?? raw.is_widow_or_senior ?? false,

    // Employment
    employmentType:    raw.employmentType ?? raw.employment_type,
    skillCertification:raw.skillCertification ?? raw.skill_certification,
    loanRequirement:   raw.loanRequirement ?? raw.loan_requirement ?? 'none',

    // Flags
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

export async function POST(request: Request) {
  try {
    const rawPayload = await request.json();
    const payload = normalisePaylod(rawPayload);

    // Proxy request to Python ML Engine (5-agent pipeline)
    const response = await fetch(`${ML_SERVICE_URL}/api/check-eligibility`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`ML Service Error: ${response.status} - ${errorText}`);
      throw new Error(`ML Service failed: ${response.statusText}`);
    }

    const data = await response.json();

    // ── Handle BOTH new pipeline format (recommended[]) and legacy (eligible_schemes[]) ──
    // New pipeline returns: { recommended: [...], eligible_schemes: [...], summary: {...} }
    // Legacy returns: { eligible_schemes: [...], eligibility_reasoning: [...] }
    const rawSchemes: any[] = data.recommended ?? data.eligible_schemes ?? [];
    const reasoningList: any[] = data.eligibility_reasoning ?? [];
    const missingList:  any[] = data.missing_criteria ?? [];

    const results = rawSchemes.map((s: any) => {
      const reasoning = reasoningList.find((r: any) => r.scheme_id === s.scheme_id);
      const missingEntry = missingList.find((m: any) => m.scheme_id === s.scheme_id);

      // Normalise benefit type
      const rawType = (s.type || s.benefit_type || 'scheme').toLowerCase().trim();
      const benefitType = ['loan', 'insurance'].includes(rawType) ? rawType : 'scheme';

      // Confidence: new pipeline gives 0–1 float, legacy gives 0–100 int
      const rawConf = s.confidence ?? s.match_score ?? 0.5;
      const confidence = rawConf <= 1 ? Math.round(rawConf * 100) : Math.round(rawConf);

      return {
        // Identity
        id:           s.scheme_id,
        name:         s.scheme_name,
        type:         benefitType,
        benefit_type: benefitType,
        eligible:     true,

        // Scores
        confidence,
        rank_score:    s.rank_score,
        benefit_score: s.benefit_score,

        // ── New pipeline explanation fields ────────────────────────────────
        why:                s.why ?? '',
        eligibility_summary:s.eligibility_summary ?? '',
        tldr_bullets:       s.tldr_bullets ?? [],
        how_to_apply:       s.how_to_apply ?? [],
        // ──────────────────────────────────────────────────────────────────

        // Description (new field or legacy)
        description: s.description ?? s.benefit_description ?? '',

        // Eligibility reasoning
        reasons:             s.reasons ?? reasoning?.reasons ?? [],
        path_to_eligibility: s.path_to_eligibility ?? reasoning?.path_to_eligibility ?? [],
        missing_inputs:      s.missing_criteria ?? missingEntry?.missing ?? [],

        // Metadata
        benefit_amount: s.benefit_amount ?? '',
        benefits:       s.benefits ?? [],
        category:       s.category ?? '',
        ministry:       s.ministry ?? '',
        level:          s.level ?? '',
        url:            s.apply_link ?? s.url ?? '',
        source_url:     s.apply_link ?? s.url ?? '',
        documents:      s.documents_required ?? [],
      };
    });

    // Summary from new pipeline (or compute from results)
    const summary = data.summary ?? {
      total:     results.length,
      loans:     results.filter((r: any) => r.type === 'loan').length,
      insurance: results.filter((r: any) => r.type === 'insurance').length,
      schemes:   results.filter((r: any) => r.type === 'scheme').length,
    };

    return NextResponse.json({
      success:          true,
      schemeDetails:    results,
      eligibleSchemes:  results.map((r: any) => r.name),
      confidence_score: data.confidence_score ?? 0.8,
      summary,
      why_not_eligible: data.why_not_eligible ?? [],
      // Pass through pipeline timing for dev debugging
      _timings: data._timings,
    });

  } catch (error: any) {
    console.error('API Route Proxy Error:', error);
    return NextResponse.json({
      success:  false,
      error:    'The AI Discovery Engine is currently unavailable. Please ensure the backend is running on port 8000.',
      fallback: true,
    }, { status: 503 });
  }
}
