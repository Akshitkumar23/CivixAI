"""
InputAgent — Stage 1 of the CivixAI Agent Pipeline
====================================================
Responsibilities:
  - Accepts raw user profile data (from Pydantic model or dict)
  - Validates all fields against business rules
  - Fills sensible defaults for missing optional fields
  - Normalises values (lowercase strings, int/float casts, etc.)
  - Returns a clean, fully-populated dict that every downstream agent can trust

This agent NEVER reaches the DB or the ML model — it is purely a
validation / normalisation layer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Valid enum values (mirror form-config.ts) ─────────────────────────────────
VALID_CASTES         = {"general", "obc", "sc", "st"}
VALID_OCCUPATIONS    = {"student", "employed", "farmer", "unemployed", "retired"}
VALID_GENDERS        = {"male", "female", "other"}
VALID_EDU_LEVELS     = {
    "illiterate", "primary", "secondary",
    "higher_secondary", "graduate", "postgraduate", "phd",
}
VALID_DIGITAL_LIT    = {"none", "basic", "intermediate", "advanced"}
VALID_URBAN_RURAL    = {"urban", "rural"}
VALID_MARITAL        = {"single", "married", "widowed", "divorced"}
VALID_EMP_TYPES      = {
    "government", "private", "self_employed",
    "daily_wage", "not_applicable",
}
VALID_SKILL_CERTS    = {"none", "it", "technical", "agriculture", "handicraft", "other"}
VALID_LOAN_REQS      = {"none", "education", "business", "housing", "agriculture", "emergency"}


class InputValidationError(ValueError):
    """Raised when a required field is missing or invalid."""
    def __init__(self, field: str, message: str):
        self.field   = field
        self.message = message
        super().__init__(f"[InputAgent] Field '{field}': {message}")


class InputAgent:
    """
    Agent 1 — Input Validation & Normalisation

    Usage:
        agent  = InputAgent()
        clean  = agent.process(raw_user_dict_or_pydantic_model)
        errors = agent.last_warnings   # soft warnings (non-blocking)
    """

    def __init__(self):
        self.last_warnings: List[str] = []

    # ──────────────────────────────────────────────────────────────────────────
    # Public entry-point
    # ──────────────────────────────────────────────────────────────────────────
    def process(self, raw: Any) -> Dict[str, Any]:
        """
        Main entry point.

        Parameters
        ----------
        raw : dict | Pydantic BaseModel
            The user profile coming from the FastAPI request.

        Returns
        -------
        dict
            Clean, validated, normalised user profile ready for downstream agents.

        Raises
        ------
        InputValidationError
            If a *required* field is missing or fundamentally invalid.
        """
        self.last_warnings = []

        # Accept Pydantic models or plain dicts
        data = raw.model_dump() if hasattr(raw, "model_dump") else dict(raw)

        # ── Step 1: Extract & hard-validate required fields ──────────────────
        age    = self._require_int(data, "age", min_val=0, max_val=120)
        income = self._require_int(data, "annualIncome", aliases=["annual_income"], min_val=0)
        state  = self._require_str(data, "state")
        caste  = self._require_enum(data, "caste", VALID_CASTES, aliases=["category"])
        occ    = self._require_enum(data, "occupation", VALID_OCCUPATIONS)

        # ── Step 2: Optional fields with defaults ─────────────────────────────
        gender       = self._opt_enum(data, "gender",          VALID_GENDERS,    default="")
        education    = self._opt_enum(data, "educationLevel",  VALID_EDU_LEVELS, aliases=["education_level"], default="")
        urban_rural  = self._opt_enum(data, "urbanRural",      VALID_URBAN_RURAL, aliases=["urban_rural"], default="")
        marital      = self._opt_enum(data, "maritalStatus",   VALID_MARITAL,    aliases=["marital_status"], default="")
        emp_type     = self._opt_enum(data, "employmentType",  VALID_EMP_TYPES,  aliases=["employment_type"], default="")
        skill_cert   = self._opt_enum(data, "skillCertification", VALID_SKILL_CERTS, aliases=["skill_certification"], default="none")
        loan_req     = self._opt_enum(data, "loanRequirement", VALID_LOAN_REQS,  aliases=["loan_requirement"], default="none")
        digital_lit  = self._opt_enum(data, "digitalLiteracy", VALID_DIGITAL_LIT, aliases=["digital_literacy"], default="none")

        family_income = self._opt_int(data, "familyIncome",   aliases=["family_income"],  default=income)
        fam_size      = self._opt_int(data, "familySize",      aliases=["family_size"],    default=1,  min_val=1)
        land_size     = self._opt_float(data, "landSize",       aliases=["land_size"],      default=0.0)
        monthly_exp   = self._opt_int(data, "monthlyExpenses", aliases=["monthly_expenses"], default=0, min_val=0)
        monthly_sav   = self._opt_int(data, "monthlySavings",  aliases=["monthly_savings"],  default=0, min_val=0)

        has_land      = self._opt_bool(data, "hasLand",              aliases=["has_land"],               default=False)
        has_disability= self._opt_bool(data, "hasDisability",        aliases=["has_disability"],          default=False)
        has_availed   = self._opt_bool(data, "hasAvailedSimilarScheme", aliases=["has_availed_similar_scheme"], default=False)
        is_single_girl= self._opt_bool(data, "isSingleGirlChild",   aliases=["is_single_girl_child"],   default=False)
        is_widow_sen  = self._opt_bool(data, "isWidowOrSenior",      aliases=["is_widow_or_senior"],     default=False)
        is_tax_payer  = self._opt_bool(data, "isTaxPayer",           aliases=["is_tax_payer"],           default=False)
        is_bank_link  = self._opt_bool(data, "isBankLinked",         aliases=["is_bank_linked"],         default=False)
        is_bpl        = self._opt_bool(data, "isBPL",                aliases=["is_bpl"],                 default=False)
        is_minority   = self._opt_bool(data, "isMinority",           aliases=["is_minority"],            default=False)
        has_smartphone= self._opt_bool(data, "hasSmartphone",        aliases=["has_smartphone"],         default=False)
        has_internet  = self._opt_bool(data, "hasInternet",          aliases=["has_internet"],           default=False)
        has_insurance = self._opt_bool(data, "hasInsurance",         aliases=["has_insurance"],          default=False)
        has_pension   = self._opt_bool(data, "hasPension",           aliases=["has_pension"],            default=False)

        priority_schemes = self._opt_list(data, "prioritySchemes", aliases=["priority_schemes"])

        # ── Step 3: Cross-field business rules ────────────────────────────────
        # Farmer occupation should logically align with has_land
        if occ == "farmer" and not has_land:
            self.last_warnings.append(
                "Occupation is 'farmer' but has_land=False — land flag auto-set for consistency."
            )
            has_land = True

        # Widow/Senior auto-inference
        if marital == "widowed" and not is_widow_sen:
            is_widow_sen = True
            self.last_warnings.append("Marital status 'widowed' → isWidowOrSenior set to True.")

        if age >= 60 and not is_widow_sen:
            is_widow_sen = True
            self.last_warnings.append(f"Age {age} ≥ 60 → isWidowOrSenior auto-set to True.")

        # Senior-age pension hint
        if age >= 60 and not has_pension:
            self.last_warnings.append(
                "Age ≥ 60 detected. Consider enabling has_pension to filter pension schemes."
            )

        # Income sanity: family_income should be >= individual income in most cases
        if family_income < income:
            self.last_warnings.append(
                f"familyIncome ({family_income}) < annualIncome ({income}) — using annualIncome as family income."
            )
            family_income = income

        # Log all warnings
        for w in self.last_warnings:
            logger.warning("[InputAgent] %s", w)

        # ── Step 4: Build clean profile dict ──────────────────────────────────
        clean: Dict[str, Any] = {
            # Core required
            "age":                     age,
            "annualIncome":            income,
            "state":                   state,
            "caste":                   caste,
            "occupation":              occ,

            # Demographics
            "gender":                  gender,
            "maritalStatus":           marital,
            "urbanRural":              urban_rural,

            # Education & Digital
            "educationLevel":          education,
            "digitalLiteracy":         digital_lit,

            # Financial
            "familyIncome":            family_income,
            "monthlyExpenses":         monthly_exp,
            "monthlySavings":          monthly_sav,

            # Family
            "familySize":              fam_size,
            "isSingleGirlChild":       is_single_girl,
            "isWidowOrSenior":         is_widow_sen,

            # Land
            "hasLand":                 has_land,
            "landSize":                land_size,

            # Employment
            "employmentType":          emp_type,
            "skillCertification":      skill_cert,
            "loanRequirement":         loan_req,

            # Flags
            "hasDisability":           has_disability,
            "hasAvailedSimilarScheme": has_availed,
            "isTaxPayer":              is_tax_payer,
            "isBankLinked":            is_bank_link,
            "isBPL":                   is_bpl,
            "isMinority":              is_minority,
            "hasSmartphone":           has_smartphone,
            "hasInternet":             has_internet,
            "hasInsurance":            has_insurance,
            "hasPension":              has_pension,

            # Preferences
            "prioritySchemes":         priority_schemes,

            # Agent metadata
            "_agent":                  "InputAgent",
            "_warnings":               list(self.last_warnings),
        }

        logger.info(
            "[InputAgent] ✅ Processed profile: age=%d, occ=%s, income=%d, state=%s",
            age, occ, income, state
        )
        return clean

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _get(self, data: Dict, key: str, aliases: Optional[List[str]] = None) -> Any:
        """Fetch value from data dict, trying key and all aliases."""
        if key in data and data[key] is not None:
            return data[key]
        for alias in (aliases or []):
            if alias in data and data[alias] is not None:
                return data[alias]
        return None

    def _require_int(
        self, data: Dict, key: str,
        aliases: Optional[List[str]] = None,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
    ) -> int:
        val = self._get(data, key, aliases)
        if val is None:
            raise InputValidationError(key, "Required field is missing.")
        try:
            val = int(float(str(val)))
        except (ValueError, TypeError):
            raise InputValidationError(key, f"Must be a number, got: {val!r}")
        if min_val is not None and val < min_val:
            raise InputValidationError(key, f"Must be ≥ {min_val}, got: {val}")
        if max_val is not None and val > max_val:
            raise InputValidationError(key, f"Must be ≤ {max_val}, got: {val}")
        return val

    def _require_str(self, data: Dict, key: str, aliases: Optional[List[str]] = None) -> str:
        val = self._get(data, key, aliases)
        if val is None or str(val).strip() == "":
            raise InputValidationError(key, "Required string field is missing or empty.")
        return str(val).strip()

    def _require_enum(
        self, data: Dict, key: str,
        valid: set,
        aliases: Optional[List[str]] = None,
    ) -> str:
        val = self._get(data, key, aliases)
        if val is None:
            raise InputValidationError(key, f"Required field is missing. Must be one of: {sorted(valid)}")
        normalised = str(val).strip().lower()
        if normalised not in valid:
            raise InputValidationError(key, f"Invalid value '{val}'. Must be one of: {sorted(valid)}")
        return normalised

    def _opt_enum(
        self, data: Dict, key: str,
        valid: set,
        aliases: Optional[List[str]] = None,
        default: str = "",
    ) -> str:
        val = self._get(data, key, aliases)
        if val is None or str(val).strip() == "":
            return default
        normalised = str(val).strip().lower()
        if normalised not in valid:
            self.last_warnings.append(f"Field '{key}' has invalid value '{val}' — using default '{default}'.")
            return default
        return normalised

    def _opt_int(
        self, data: Dict, key: str,
        aliases: Optional[List[str]] = None,
        default: int = 0,
        min_val: Optional[int] = None,
    ) -> int:
        val = self._get(data, key, aliases)
        if val is None:
            return default
        try:
            result = int(float(str(val)))
        except (ValueError, TypeError):
            self.last_warnings.append(f"Field '{key}' could not be parsed as int — using default {default}.")
            return default
        if min_val is not None:
            result = max(min_val, result)
        return result

    def _opt_float(
        self, data: Dict, key: str,
        aliases: Optional[List[str]] = None,
        default: float = 0.0,
    ) -> float:
        val = self._get(data, key, aliases)
        if val is None:
            return default
        try:
            return float(str(val))
        except (ValueError, TypeError):
            self.last_warnings.append(f"Field '{key}' could not be parsed as float — using default {default}.")
            return default

    def _opt_bool(
        self, data: Dict, key: str,
        aliases: Optional[List[str]] = None,
        default: bool = False,
    ) -> bool:
        val = self._get(data, key, aliases)
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        if s in ("true", "1", "yes"):
            return True
        if s in ("false", "0", "no"):
            return False
        self.last_warnings.append(f"Field '{key}' could not be parsed as bool — using default {default}.")
        return default

    def _opt_list(
        self, data: Dict, key: str,
        aliases: Optional[List[str]] = None,
    ) -> List[str]:
        val = self._get(data, key, aliases)
        if val is None:
            return []
        if isinstance(val, list):
            return [str(v) for v in val]
        return []
