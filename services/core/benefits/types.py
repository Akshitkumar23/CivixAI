from typing import Literal, Optional
from pydantic import BaseModel

BenefitKind = Literal[
    "fixed_cash", "recurring_cash", "percentage_subsidy",
    "interest_subvention", "insurance_cover", "loan_limit",
    "pension", "in_kind"
]

class BaseBenefit(BaseModel):
    kind: BenefitKind
    description: str

class FixedCashBenefit(BaseBenefit):
    kind: Literal["fixed_cash"] = "fixed_cash"
    amount: float
    frequency: str = "one_time"

class RecurringCashBenefit(BaseBenefit):
    kind: Literal["recurring_cash"] = "recurring_cash"
    amount: float
    frequency: str = "yearly"  # monthly, quarterly, yearly

class PercentageSubsidy(BaseBenefit):
    kind: Literal["percentage_subsidy"] = "percentage_subsidy"
    percentage: float
    cap_amount: Optional[float] = None

class InterestSubvention(BaseBenefit):
    kind: Literal["interest_subvention"] = "interest_subvention"
    subvention_percentage: float
    max_loan_limit: Optional[float] = None

class InsuranceCover(BaseBenefit):
    kind: Literal["insurance_cover"] = "insurance_cover"
    sum_insured: float
    premium_annual: Optional[float] = None

class LoanLimit(BaseBenefit):
    kind: Literal["loan_limit"] = "loan_limit"
    max_loan_amount: float
    collateral_free: bool = False

class PensionBenefit(BaseBenefit):
    kind: Literal["pension"] = "pension"
    monthly_pension: float
    start_age: int = 60

class InKindBenefit(BaseBenefit):
    kind: Literal["in_kind"] = "in_kind"
    service_description: str
