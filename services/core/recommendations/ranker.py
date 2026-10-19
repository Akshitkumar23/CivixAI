from typing import Any, Dict

def calculate_rank_score(
    scheme: Dict[str, Any],
    status: str,
    application_readiness: float,
    user_facts: Dict[str, Any]
) -> float:
    """
    Transparent multi-factor ranking function.
    Zero uncalibrated black-box weights.
    """
    # Base status multiplier
    status_weights = {
        "ELIGIBLE": 1.0,
        "NEEDS_INFO": 0.6,
        "NEEDS_VERIFICATION": 0.8,
        "CONDITIONAL": 0.5,
        "NOT_ELIGIBLE": 0.0,
    }
    status_mult = status_weights.get(status, 0.0)
    if status_mult == 0.0:
        return 0.0

    # 1. Need Fit / Profile Relevance (0.0 to 1.0)
    need_fit = 0.5
    occupation = str(user_facts.get("occupation.type", "")).lower()
    scheme_desc = (str(scheme.get("description", "")) + " " + str(scheme.get("scheme_name", ""))).lower()
    if occupation and (occupation in scheme_desc or ("farmer" in occupation and "kisan" in scheme_desc)):
        need_fit = 0.95

    # 2. Benefit Impact (0.0 to 1.0)
    benefits = scheme.get("benefits", [])
    benefit_val = 0.5
    if benefits:
        first_b = benefits[0]
        fixed = getattr(first_b, "fixed_amount", None)
        if fixed and fixed >= 100000:
            benefit_val = 0.9
        elif fixed and fixed >= 10000:
            benefit_val = 0.75

    # 3. Popularity / National Demand (normalized 0.0 to 1.0)
    pop_raw = float(scheme.get("popularity_score", 5.0))
    popularity = min(1.0, max(0.0, pop_raw / 10.0))

    # 4. Application Readiness (0.0 to 1.0) - Secondary tie-breaker, not a gating barrier
    readiness = application_readiness

    # Decoupled formula: legal relevance and citizen need dominate, document readiness acts as within-status tiebreaker
    base_score = (
        0.50 * need_fit +
        0.25 * benefit_val +
        0.15 * popularity +
        0.10 * readiness
    )

    # Missing facts penalty for NEEDS_INFO: fewer missing facts ranked higher
    missing_penalty = 0.0
    if status == "NEEDS_INFO":
        missing_count = len(scheme.get("missing_facts", []))
        missing_penalty = min(0.15, missing_count * 0.02)

    # Certified current policy bonus
    currentness_bonus = 0.05 if scheme.get("currentness_status") == "current" else 0.0

    score = max(0.01, (base_score - missing_penalty + currentness_bonus)) * status_mult
    return round(score, 4)
