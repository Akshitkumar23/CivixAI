from typing import Any, Dict
from .types import (
    BaseBenefit, FixedCashBenefit, RecurringCashBenefit,
    PercentageSubsidy, InterestSubvention, InsuranceCover,
    LoanLimit, PensionBenefit, InKindBenefit
)

def format_benefit_summary(benefit_dict: Dict[str, Any]) -> str:
    """
    Format a benefit record into human-readable INR format.
    Zero arbitrary ML regressions.
    """
    b_type = str(benefit_dict.get("benefit_type", "")).lower()
    fixed = benefit_dict.get("fixed_amount")
    pct = benefit_dict.get("percentage")
    cap = benefit_dict.get("cap_amount")
    desc = benefit_dict.get("description") or ""

    if "insurance" in b_type:
        if fixed and fixed >= 100000:
            return f"₹{fixed/100000:.1f} Lakh health/life insurance coverage"
        return "Comprehensive subsidized insurance cover"

    if "pension" in b_type:
        if fixed:
            return f"₹{fixed:,.0f} / month assured pension"
        return "Guaranteed post-retirement monthly pension"

    if "loan" in b_type or "credit" in b_type:
        if fixed and fixed >= 100000:
            return f"Subsidized loan assistance up to ₹{fixed/100000:.1f} Lakh"
        elif fixed:
            return f"Credit support up to ₹{fixed:,.0f}"
        return "Collateral-free institutional credit"

    if "subsidy" in b_type:
        if pct and cap:
            return f"{pct}% subsidy (up to ₹{cap:,.0f})"
        elif fixed:
            return f"Capital subsidy of ₹{fixed:,.0f}"

    if fixed and fixed > 0:
        freq = benefit_dict.get("frequency", "yearly")
        if freq == "monthly":
            return f"₹{fixed:,.0f} / month direct benefit"
        return f"₹{fixed:,.0f} direct financial transfer"

    return desc if desc else "Government sponsored benefit & support"
