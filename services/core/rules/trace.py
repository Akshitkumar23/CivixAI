from typing import List, Optional
from .schema import (
    RuleEvaluationResult, SchemeEvaluationSummary, EvidenceCitation
)

def _extract_leaf_results(result: RuleEvaluationResult) -> List[RuleEvaluationResult]:
    """Extracts all leaf condition evaluations from a nested result tree."""
    if not result.children:
        return [result]
    leaves = []
    for child in result.children:
        leaves.extend(_extract_leaf_results(child))
    return leaves

def build_scheme_evaluation(
    scheme_id: str,
    results: List[RuleEvaluationResult],
    evidence: Optional[List[EvidenceCitation]] = None
) -> SchemeEvaluationSummary:
    """
    Synthesizes overall SchemeEvaluationSummary adhering to 4-state legal classification:
    - ELIGIBLE: All conditions satisfied with verified legal basis.
    - NEEDS_INFO: One or more facts are unknown.
    - NEEDS_VERIFICATION: Unverified baseline rules fail or sources need human audit.
    - NOT_ELIGIBLE: One or more authoritative verified rules fail.
    - CONDITIONAL: Alternate or discretionary eligibility pathways available.
    """
    # Flatten leaf results for fine-grained reasons and diagnostics
    leaf_results: List[RuleEvaluationResult] = []
    for r in results:
        leaf_results.extend(_extract_leaf_results(r))

    matched = [r for r in leaf_results if r.state == "PASS"]
    failed = [r for r in leaf_results if r.state == "FAIL"]
    unknown = [r for r in leaf_results if r.state == "UNKNOWN"]

    # Separate verified failures vs unverified failures
    verified_fails = [
        r for r in failed
        if r.verification_status in ("source_verified", "human_reviewed")
    ]
    unverified_fails = [
        r for r in failed
        if r.verification_status not in ("source_verified", "human_reviewed")
    ]

    reasons: List[str] = []
    missing_facts: List[str] = []
    path_to_eligibility: List[str] = []

    for r in matched:
        reason_msg = None
        if r.fact_key == "person.age":
            reason_msg = f"Age {r.actual_value} meets criteria."
        elif r.fact_key == "household.annual_income":
            reason_msg = f"Household income ₹{r.actual_value:,.0f} satisfies income threshold."
        elif r.fact_key == "location.state":
            reason_msg = f"Available in {r.actual_value}."
        elif r.fact_key == "occupation.type":
            reason_msg = f"Occupation ({r.actual_value}) is eligible."
        else:
            reason_msg = r.message
        if reason_msg and reason_msg not in reasons:
            reasons.append(reason_msg)

    for r in unknown:
        if r.fact_key and r.fact_key not in missing_facts:
            missing_facts.append(r.fact_key)
            clean_fact = (
                r.fact_key
                .replace("applicant.", "")
                .replace("household.", "")
                .replace("person.", "")
                .replace("location.", "")
                .replace("student.", "")
                .replace("artisan.", "")
                .replace("enterprise.", "")
                .replace("family.", "")
                .replace("social.", "")
                .replace("agriculture.", "")
                .replace("health.", "")
                .replace("finance.", "")
                .replace("_", " ")
            )
            if r.operator == "eq" and r.expected_value is True:
                path_to_eligibility.append(f"Confirm {clean_fact} to fulfill statutory requirement.")
            elif r.operator == "eq" and r.expected_value is False:
                path_to_eligibility.append(f"Confirm non-applicability of {clean_fact}.")
            elif r.operator in ("gte", "lte", "gt", "lt"):
                path_to_eligibility.append(f"Declare verified {clean_fact} (statutory rule expects {r.operator} {r.expected_value}).")
            elif r.operator == "in":
                path_to_eligibility.append(f"Specify {clean_fact} matching statutory criteria.")
            else:
                path_to_eligibility.append(f"Declare verified {clean_fact}.")

    for r in verified_fails:
        if r.fact_key == "applicant.has_eligible_participating_account":
            path_to_eligibility.append("Open an eligible participating bank/Post Office account, then re-check enrollment eligibility.")
        elif r.fact_key == "applicant.auto_debit_consent":
            path_to_eligibility.append("Provide auto-debit consent for annual premium deduction at your bank/Post Office branch or netbanking.")
        elif r.fact_key == "household.annual_income":
            path_to_eligibility.append(f"Income ₹{r.actual_value:,.0f} exceeds verified ceiling ({r.expected_value}).")
        elif r.fact_key == "person.age":
            path_to_eligibility.append(f"Age {r.actual_value} is outside verified range ({r.expected_value}).")
        elif r.fact_key == "location.state":
            path_to_eligibility.append(f"Scheme is restricted to states: {r.expected_value}.")
        else:
            path_to_eligibility.append(f"Does not satisfy verified rule: {r.message}")

    for r in unverified_fails:
        path_to_eligibility.append(
            f"Unverified baseline rule '{r.fact_key}' ({r.operator} {r.expected_value}) flagged possible mismatch; requires manual or portal verification."
        )

    # Determine 4-state outcome and authoritative governance status
    if len(verified_fails) > 0:
        status = "NOT_ELIGIBLE"
        confidence = 1.0
        authority_level = "authoritative_source_verified"
        gov_notice = "Legally authoritative rejection based on source-verified government guideline/gazette evidence."
    elif len(unknown) > 0:
        status = "NEEDS_INFO"
        confidence = 0.6
        authority_level = "tentative_unverified_rule"
        gov_notice = f"Information needed: {len(missing_facts)} required fact(s) are missing to complete deterministic evaluation."
    elif len(unverified_fails) > 0:
        # If ONLY unverified baseline rules failed, do not hard-reject!
        status = "NEEDS_VERIFICATION"
        confidence = 0.4
        authority_level = "tentative_unverified_rule"
        gov_notice = "Tentative evaluation: Mismatch detected on unverified bootstrap rule. Rule requires official gazette/portal verification before legal disqualification."
    else:
        status = "ELIGIBLE"
        confidence = 1.0
        all_rules_verified = all(
            r.verification_status in ("source_verified", "human_reviewed")
            for r in matched
        ) if matched else False
        if all_rules_verified and evidence:
            authority_level = "authoritative_source_verified"
            gov_notice = "Authoritative match: All applicable criteria verified against official government source documents."
        else:
            authority_level = "tentative_unverified_rule"
            gov_notice = "Deterministic match based on bootstrap rule baseline. Official source verification is pending."

    return SchemeEvaluationSummary(
        scheme_id=scheme_id,
        status=status,
        deterministic_result=status,
        authority_level=authority_level,
        governance_notice=gov_notice,
        confidence_score=confidence,
        application_readiness=1.0,
        matched_rules=matched,
        failed_rules=failed,
        unknown_rules=unknown,
        unverified_rules=unverified_fails,
        reasons=reasons,
        missing_facts=missing_facts,
        path_to_eligibility=path_to_eligibility,
        evidence=evidence or []
    )
