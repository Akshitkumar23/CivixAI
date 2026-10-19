# CivixAI — Fact Registry Architecture & Canonical Fact Contract

## 1. Executive Summary & Problem Context
The forensic audit of CivixAI revealed a critical disconnect between the intake questionnaire and the rule evaluation engine: **53 out of 58 required statutory facts were absent from the questionnaire catalogue**. Rules queried primitive keys (`applicant.is_farmer_family`, `household.owns_pucca_house`, `household.has_lpg_connection`, etc.) that citizens were never asked. Furthermore, loose semantic derivations previously tried to infer legal facts from sociological labels (e.g. `occupation.type == 'farmer' → applicant.is_farmer_family = true`), violating public law standards.

This document establishes the **Canonical Fact Contract**, **Strict Derivation Policy**, and **Adaptive Questioning Architecture** implemented during the remediation.

---

## 2. Canonical Fact Contract

Every legal condition evaluated in CivixAI must reference a registered fact conforming to the `CanonicalFactDefinition` schema (`services/core/facts/contract.py`):

```python
class CanonicalFactDefinition(BaseModel):
    fact_key: str
    subject_scope: SubjectScope  # APPLICANT, BENEFICIARY, HOUSEHOLD, FAMILY, STUDENT, ARTISAN, ENTERPRISE, LOCATION
    data_type: DataType          # INTEGER, FLOAT, STRING, BOOLEAN, ENUM
    allowed_values: Optional[List[Any]] = None
    unit: Optional[str] = None
    sensitivity: str = "normal"  # normal, sensitive, financial
    collection_method: CollectionMethod # QUESTION, DETERMINISTIC_DERIVATION, USER_DECLARATION, DOCUMENT_VERIFICATION, EXTERNAL_VERIFICATION, SYSTEM_CONTEXT
    verification_level: VerificationLevel # SELF_DECLARED, DOCUMENT_SUPPORTED, GOVERNMENT_VERIFIED
    question_available: bool = True
    derivation_policy: Optional[str] = None
    normalization_policy: str = "standard_trim_casefold"
    schemes_using_fact: List[str] = Field(default_factory=list)
    source_semantics: str = ""
```

### 2.1 Subject Scopes
CivixAI enforces strict subject scoping to prevent household conflation:
- `applicant`: The citizen filing the intake form.
- `beneficiary`: The designated recipient of the scheme (e.g. the child, student, or senior member).
- `household`: The collective residential family sharing a hearth/ration card.
- `family`: Blood/marital relations (relevant for girl child limits and family caps).
- `student`: The student pursuing education.
- `artisan`: The craftsman practicing traditional manual trades.
- `enterprise`: The business/farm entity applying for credit or subsidies.
- `location`: The geographic jurisdiction of domicile/residence.

---

## 3. Strict Derivation Policy

### 3.1 Absolute Prohibition of Loose Sociological Inferences
Under the statutory remediation invariants, CivixAI **strictly forbids** loose, heuristic, or sociological implications.

#### Forbidden Examples:
- `occupation.type == farmer → applicant.is_farmer_family = true` *(Unsafe: Many agricultural labourers identify as farmers but do not own landholding rights required under PM-KISAN).*
- `social.is_bpl == true → household.bpl_status_verified = true` *(Unsafe: Self-declared poverty is distinct from verified administrative SECC/ration card records).*
- `health.has_disability == true → disability_percentage >= 40` *(Unsafe: Benchmark disability requires certified UDID medical assessment).*
- `unknown exclusion → false` *(Unsafe: Missing exclusion criteria cannot be assumed false; doing so produces false ELIGIBLE results).*

### 3.2 Permitted Deterministic Derivations
Only logically deterministic, mathematical, or canonical normalizations are permitted in `services/core/facts/derivation.py`:
1. `person.date_of_birth → person.age` (Exact Gregorian year calculation).
2. `location.state` normalization (Maps aliases and ISO codes across India's 28 States and 8 UTs).
3. `person.age + bracket [min, max] → applicant.within_eligible_age_bracket` (Deterministic arithmetic boundary comparison).
4. `household.annual_income + statutory threshold → household.exceeds_income_cap` (Deterministic arithmetic ceiling comparison).
5. `person.disability_percentage >= 80.0 → beneficiary.meets_severe_disability_threshold` (Statutory mathematical threshold).
6. `location.state in NE_STATES → applicant.has_ner_domicile` (Geographic boundary membership).
7. `location.area_type == 'rural' → location.outside_urban_jurisdiction = true` (Jurisdictional partition).

Every registered derivation rule specifies `rule_id`, `source_facts`, `target_fact`, type validation, and unit test coverage.

---

## 4. Adaptive Question Planning & Invalidation

### 4.1 Dependency-Aware Planner
The questionnaire orchestrator (`services/core/questionnaire/orchestrator.py`) selects questions dynamically based on the **Authoritative Eligibility Pool** (27 certified citizen schemes):
1. **Candidate Identification:** Identifies viable certified schemes whose rules have not short-circuited to `FAIL`.
2. **Consequential Leaf Inspection:** Traverses the AST of viable schemes to find collectable facts that remain `UNKNOWN`.
3. **Multi-Factor Ranking:** `QuestionRanker` ranks candidate questions by:
   - Scheme coverage (number of viable schemes affected).
   - Mandatory vs alternate condition impact.
   - User cognitive friction (booleans/radios prioritized over free text).
   - Privacy minimization (sensitive and financial questions delayed until strictly consequential).
4. **Active Selection:** Asks the single highest-value question.

### 4.2 Edit & Back Invalidation
When a user edits an earlier answer or clicks "Back":
- Downstream derived facts registered in `get_dependent_derived_facts(fact_key)` are deleted from session storage.
- Dynamic derivations (`apply_deterministic_derivations`) recalculate fresh from the updated base facts.
- Scheme relevance, missing fact counts, eligibility statuses, and next question rankings are recomputed in-memory without stale cache artifacts.

---

## 5. Verification & Reachability Gate

The static reachability linter (`RuleFactReachabilityValidator`) runs at publication time. It traverses every AST rule leaf of every certified scheme version and guarantees that every leaf resolves to one of:
- `COLLECTABLE`: Defined in `QUESTION_METADATA_CATALOGUE`.
- `DETERMINISTICALLY_DERIVABLE`: Registered in `DERIVATION_REGISTRY`.
- `DOCUMENT_VERIFIABLE`: Supported by document upload.
- `EXTERNALLY_VERIFIABLE`: Verified via DBT/Aadhaar/civil API.

**Post-Remediation Status:**
- Total Fact Leaves: **94**
- Unresolved Fact Leaves: **0** (100% Reachable Scheme Rate across all 27 certified schemes).
