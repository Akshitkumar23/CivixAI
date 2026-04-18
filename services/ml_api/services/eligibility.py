from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel

# ─── Score Constants ───────────────────────────────────────────────────────────
BASE_MATCH_SCORE            = 0.40
AGE_MATCH_BONUS             = 0.15
INCOME_MATCH_BONUS          = 0.15
OCCUPATION_MATCH_BONUS      = 0.20
OCCUPATION_MISMATCH_PENALTY = 0.10
GENDER_MATCH_BONUS          = 0.15
CASTE_MATCH_BONUS           = 0.15
MIN_SCORE = 0.0
MAX_SCORE = 1.0

# ─── Education level ordering (low → high) ────────────────────────────────────
EDUCATION_RANK = {
    "illiterate": 0, "primary": 1, "secondary": 2,
    "higher_secondary": 3, "graduate": 4, "postgraduate": 5, "phd": 6,
}

# ─── Farmer-ONLY schemes (hard block for non-farmers without land) ─────────────
FARMER_HARD_KEYWORDS = [
    "fasal", "pmfby", "fasal bima", "crop insurance", "crop loan",
    "kisan credit", "kcc ", "pm kisan", "pmkisan", "pmksy",
    "pradhan mantri fasal", "agriculture mechanization",
    "matsya sampada", "fisheries", "livestock health", "pashu",
    "horticulture mission", "irrigation scheme", "soil health card",
    "national food security mission", "nfsm",
    "agriculture technology management",
]

FARMER_SOFT_KEYWORDS = [
    "farmer", "kisan", "agriculture", "agricultural", "krishi", "kheti",
    "kisaan", "agri ", "farming",
]

# ─── Student-ONLY schemes ──────────────────────────────────────────────────────
STUDENT_HARD_KEYWORDS = [
    "scholarship", "post matric scholarship", "pre matric scholarship",
    "national scholarship", "merit scholarship", "national fellowship",
    "central sector scholarship", "top class", "national overseas scholarship",
]

# ─── Widow / Senior pension schemes ───────────────────────────────────────────
WIDOW_SENIOR_KEYWORDS = [
    "widow", "vidhwa", "indira gandhi national widow",
    "old age pension", "vridha pension", "senior citizen pension",
    "indira gandhi national old age",
]

# ─── Schemes ONLY for persons with disabilities ───────────────────────────────
DISABILITY_HARD_KEYWORDS = [
    "disabled", "disability", "divyang", "handicapped",
    "deen dayal disabled", "scholarship for top class education for students with disabilities",
    "national overseas scholarship for students with disabilities",
]

# ─── Women-only schemes ────────────────────────────────────────────────────────
WOMEN_HARD_KEYWORDS = [
    "mahila", "beti bachao", "sukanya", "matru vandana",
    "janani suraksha", "lady", "nari", "stree shakti",
]

# ─── Formal employee ONLY schemes (ESI, EPF etc.) ─────────────────────────────
FORMAL_EMPLOYEE_KEYWORDS = [
    "employee state insurance", "esi ", "epf ", "employee provident fund",
    "gratuity", "employee pension scheme", "esic",
]

# ─── BPL-targeted schemes (text from special_conditions_required) ─────────────
BPL_CONDITION_KEYWORDS = [
    "bpl category", "listed in sec-2011", "bpl card",
    "below poverty", "bpl families",
]

# ─── Poverty-targeted welfare (exclude income-tax payers) ─────────────────────
POVERTY_WELFARE_KEYWORDS = [
    "below poverty", "bpl", "antyodaya", "destitute",
    "antodaya", "garib kalyan", "daridra", "ujjwala yojana",
    "pm ujjwala", "ration card",
]

# ─── Basic insurance schemes (skip if user already has insurance) ──────────────
BASIC_INSURANCE_SCHEMES = [
    "pradhan mantri jeevan jyoti bima", "pmjjby",
    "pradhan mantri suraksha bima", "pmsby",
]

# ─── Basic pension schemes (skip if user already has pension) ─────────────────
BASIC_PENSION_SCHEMES = [
    "atal pension yojana",  "employee pension scheme", "eps ",
]

# ─── Urban-only / rural-only clues (keyword-based since CSV is sparse) ────────
RURAL_ONLY_KEYWORDS = [
    "grameen", "gramin", "gram sabha", "gram panchayat",
    "rural", "village", "pradhan mantri awaas yojana - gramin", "pmay-g",
    "mgnregs", "mnrega", "national rural",
]
URBAN_ONLY_KEYWORDS = [
    "urban", "city", "metro", "pradhan mantri sadak yojana urban",
    "smart city", "pm street vendor", "pm svanidhi",
]

# ─── Minority specific schemes ────────────────────────────────────────────────
MINORITY_SCHEME_KEYWORDS = [
    "minority", "maulana azad", "muslim", "waqf",
    "hunar haat", "nai manzil", "seekho aur kamao",
    "pradhan mantri jan vikas", "pmjvk",
]

# ─── Maternity / married woman schemes ────────────────────────────────────────
MATERNITY_KEYWORDS = [
    "matru vandana", "maternity", "janani", "pregnant", "pradhan mantri matru",
    "janani suraksha", "janani shishu", "maternity benefit",
]

# ─── Senior-only schemes (varishtha = elderly, for 55+ only) ──────────────────
SENIOR_ONLY_KEYWORDS = [
    "varishtha pension", "vrishth pension", "senior citizen savings",
    "pradhan mantri vaya vandana", "vaya vandana yojana", "pmvvy",
]

# ─── Freedom fighter / ex-serviceman exclusive schemes ───────────────────────
FREEDOM_FIGHTER_KEYWORDS = [
    "swatantrata sainik", "sainik samman", "freedom fighter",
    "ex-serviceman", "ex serviceman", "veer nari", "defence personnel",
    "war widow", "gallantry award",
]

# ─── Sector-specific worker schemes (coal, plantation, etc.) ─────────────────
SECTOR_WORKER_KEYWORDS = [
    "coal mines pension", "coal mine worker", "coal mines provident",
    "plantation workers", "beedi worker", "cine worker",
    "dock worker", "mine worker",
]

# ─── Sports achievement schemes (only for medal-winning sportspersons) ────────
SPORTS_ACHIEVEMENT_KEYWORDS = [
    "meritorious sportsperson", "pension to sportsperson",
    "welfare of sportspersons", "national welfare fund for sportsperson",
    "cash award for sportsperson", "arjuna award", "khel ratna",
]

# ─── Loan requirement → relevant keywords ─────────────────────────────────────
LOAN_CATEGORY_KEYWORDS = {
    "education":   ["education loan", "vidya lakshmi", "padho predesh", "interest subsidy on educational"],
    "business":    ["mudra", "stand-up india", "startup", "msme", "self employ", "entrepreneur"],
    "housing":     ["awas", "housing loan", "home loan", "pmay", "pradhan mantri awas"],
    "agriculture": ["kcc", "kisan credit", "agri loan", "agriculture loan", "crop loan"],
    "emergency":   ["emergency", "relief", "disaster"],
}

# ─── Skill → relevant scheme keywords ─────────────────────────────────────────
SKILL_SCHEME_KEYWORDS = {
    "it":          ["digital", "it skills", "pm e-vidya", "coding", "cyber", "computer", "digital india", "digilocker"],
    "technical":   ["skill", "vocational", "iti", "technical training", "pm kaushal", "pmkvy"],
    "agriculture": ["krishi vigyan", "agricultural extension", "atma", "agriculture technology"],
    "handicraft":  ["handloom", "handicraft", "artisan", "weaver", "weavers", "karigari", "khadi"],
    "other":       ["skill development", "training", "capacity building"],
}

# ─── Employment type → scheme keywords ────────────────────────────────────────
EMPLOYMENT_SCHEME_KEYWORDS = {
    "daily_wage":    ["mgnregs", "mnrega", "shramik", "labour", "labourer", "mazdoor", "unorganised worker", "e-shram"],
    "self_employed": ["mudra", "stand-up", "self employment", "startup", "msme", "pmegp"],
    "government":    ["central government employee", "cghs", "ex-serviceman", "armed forces"],
    "private":       ["employee state insurance", "esi", "epf", "gratuity"],
}


# ─── Result model ──────────────────────────────────────────────────────────────
class EligibilityResult(BaseModel):
    is_eligible: bool
    ml_confidence: float
    reasons: List[str]
    missing_criteria: List[str]
    path_to_eligibility: List[str]
    hard_reject: bool
    match_score: float


class EligibilityService:

    def __init__(self, model, schema: Dict[str, Any]):
        self.model  = model
        self.schema = schema

    # ──────────────────────────────────────────────────────────────────────────
    # Helper : safely read user attribute, fallback to default
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _g(user: Any, field: str, default=None):
        return getattr(user, field, default) if getattr(user, field, default) is not None else default

    @staticmethod
    def _nan(v) -> bool:
        return v is None or (isinstance(v, float) and np.isnan(v))

    # ──────────────────────────────────────────────────────────────────────────
    # PRE-FILTER  (runs BEFORE ML — hard pass/fail only)
    # ──────────────────────────────────────────────────────────────────────────
    def _passes_basic_filters(self, user: Any, scheme: Dict[str, Any]) -> Tuple[bool, str]:
        """
        14-point hard rule check.  Every check maps 1-to-1 to a user input field.
        Returns (True, "") or (False, reason).
        """
        g = self._g

        u_age      = int(g(user, "age", 0))
        u_income   = int(g(user, "annualIncome", 0))
        u_famincome= int(g(user, "familyIncome", u_income))     # fall back to annualIncome
        u_occ      = str(g(user, "occupation", "")).lower().strip()
        u_gender   = str(g(user, "gender", "")).lower().strip()
        u_caste    = str(g(user, "caste", "")).lower().strip()
        u_state    = str(g(user, "state", "")).strip()
        u_edu      = str(g(user, "educationLevel", "")).lower().strip()
        u_urban    = str(g(user, "urbanRural", "")).lower().strip()
        u_emp_type = str(g(user, "employmentType", "")).lower().strip()
        u_mar_stat = str(g(user, "maritalStatus", "")).lower().strip()
        u_land     = bool(g(user, "hasLand", False))
        u_disabled = bool(g(user, "hasDisability", False))
        u_bpl      = bool(g(user, "isBPL", False))
        u_tax      = bool(g(user, "isTaxPayer", False))
        u_widsen   = bool(g(user, "isWidowOrSenior", False))
        u_minority = bool(g(user, "isMinority", False))
        u_insured  = bool(g(user, "hasInsurance", False))
        u_pension  = bool(g(user, "hasPension", False))
        u_phone    = bool(g(user, "hasSmartphone", False))
        u_net      = bool(g(user, "hasInternet", False))
        u_availed  = bool(g(user, "hasAvailedSimilarScheme", False))
        u_fam_size = int(g(user, "familySize", 1))

        s_name = str(scheme.get("scheme_name", "")).lower()
        s_desc = str(scheme.get("benefit_description", "")).lower()
        txt    = f"{s_name} {s_desc}"

        # ─── 1. FARMER HARD-BLOCK ─────────────────────────────────────────────
        if any(kw in txt for kw in FARMER_HARD_KEYWORDS):
            if u_occ != "farmer" and not u_land:
                return False, "Exclusive to farmers / agricultural workers"

        # ─── 2. FARMER SOFT-BLOCK ─────────────────────────────────────────────
        if any(kw in txt for kw in FARMER_SOFT_KEYWORDS):
            if u_occ != "farmer" and not u_land:
                if not any(ex in txt for ex in ["health", "ration", "food security", "nutrition"]):
                    return False, "Scheme targets farmers"

        # ─── 3. STUDENT HARD-BLOCK ────────────────────────────────────────────
        if any(kw in txt for kw in STUDENT_HARD_KEYWORDS):
            if u_occ not in ["student", "unemployed"]:
                return False, "Exclusive to students"

        # ─── 4. DISABILITY HARD-BLOCK ─────────────────────────────────────────
        if any(kw in s_name for kw in DISABILITY_HARD_KEYWORDS):
            if not u_disabled:
                return False, "Exclusive to persons with disabilities"

        # ─── 5. WIDOW / SENIOR BLOCK ──────────────────────────────────────────
        if any(kw in txt for kw in WIDOW_SENIOR_KEYWORDS):
            if not u_widsen and u_age < 50:
                return False, "Scheme is for widows or senior citizens (50+)"

        # ─── 6. GENDER BLOCK (CSV column) ─────────────────────────────────────
        gender_elig = str(scheme.get("gender_eligibility", "all")).lower().strip()
        if gender_elig == "female" and u_gender not in ["female", ""]:
            return False, "Exclusive to female applicants"
        if gender_elig == "male" and u_gender not in ["male", ""]:
            return False, "Exclusive to male applicants"

        # ─── 7. MATERNITY / PREGNANCY SCHEMES ────────────────────────────────
        if any(kw in txt for kw in MATERNITY_KEYWORDS):
            if u_gender == "male":
                return False, "Maternity/pregnancy scheme — not applicable for males"
            # Block for single young students (maritalStatus may not always be set)
            if u_occ == "student" and u_age < 25:
                return False, "Maternity scheme not applicable for students under 25"
            if u_mar_stat in ["single"]:
                return False, "Maternity scheme requires married status"

        # ─── 8. FORMAL EMPLOYEE ONLY (ESI/EPF) ────────────────────────────────
        if any(kw in txt for kw in FORMAL_EMPLOYEE_KEYWORDS):
            if u_occ != "employed" or u_emp_type not in ["government", "private", ""]:
                return False, "Exclusive to formal sector employees (ESI/EPF)"

        # ─── 9. CASTE FILTER (CSV column) ─────────────────────────────────────
        caste_elig = str(scheme.get("caste_eligibility", "all")).lower().strip()
        if caste_elig not in ["all", "nan", "any", ""] and u_caste:
            valid = [c.strip() for c in caste_elig.split(",") if c.strip()]
            if valid and not any(u_caste == c or u_caste in c for c in valid):
                return False, f"Scheme is for {caste_elig.upper()} category only"

        # ─── 10. INCOME FILTER (CSV column) ───────────────────────────────────
        income_limit = scheme.get("income_limit")
        if not self._nan(income_limit):
            try:
                limit = float(income_limit)
                # Use family income if it's lower (more conservative eligibility check)
                effective_income = min(u_income, u_famincome) if u_famincome > 0 else u_income
                if limit > 0 and effective_income > limit:
                    return False, f"Income Rs.{effective_income} exceeds scheme limit Rs.{int(limit)}"
            except (ValueError, TypeError):
                pass

        # ─── 11. AGE FILTER (CSV column) ──────────────────────────────────────
        min_age = scheme.get("min_age")
        max_age = scheme.get("max_age")
        if not self._nan(min_age):
            try:
                if u_age < int(float(min_age)):
                    return False, f"Minimum age {int(float(min_age))} years required (you: {u_age})"
            except (ValueError, TypeError): pass
        if not self._nan(max_age):
            try:
                if u_age > int(float(max_age)):
                    return False, f"Maximum age {int(float(max_age))} years exceeded (you: {u_age})"
            except (ValueError, TypeError): pass

        # ─── 12. STATE FILTER (CSV column) ────────────────────────────────────
        applicable_states = str(scheme.get("applicable_states", "ALL")).upper().strip()
        if applicable_states not in ["", "ALL", "NAN", "ALL STATES"] and u_state:
            state_list = [s.strip().upper() for s in applicable_states.replace(";", ",").split(",") if s.strip()]
            if state_list and u_state.upper() not in state_list:
                return False, f"Scheme only available in: {', '.join(state_list)}"

        # ─── 13. URBAN / RURAL FILTER ─────────────────────────────────────────
        # CSV column (often empty, so also keyword-based fallback)
        urban_rural_csv = str(scheme.get("urban_rural_eligibility", "")).lower().strip()
        if urban_rural_csv == "rural" and u_urban == "urban":
            return False, "Scheme is for rural residents only"
        if urban_rural_csv == "urban" and u_urban == "rural":
            return False, "Scheme is for urban residents only"
        # Keyword-based when CSV is empty
        if u_urban == "urban" and any(kw in txt for kw in RURAL_ONLY_KEYWORDS):
            if not any(ex in txt for ex in ["urban", "city"]):
                return False, "Scheme is for rural residents only"
        if u_urban == "rural" and any(kw in txt for kw in URBAN_ONLY_KEYWORDS):
            return False, "Scheme is for urban residents only"

        # ─── 14. MINORITY SCHEME FILTER ───────────────────────────────────────
        if any(kw in txt for kw in MINORITY_SCHEME_KEYWORDS):
            if not u_minority:
                # Only hard block if scheme name EXPLICITLY says minority
                if "minority" in s_name or "maulana azad" in s_name:
                    return False, "Scheme is exclusively for minority communities"

        # ─── 15. TAX PAYER EXCLUSION ──────────────────────────────────────────
        if u_tax and any(kw in txt for kw in POVERTY_WELFARE_KEYWORDS):
            return False, "Scheme targets BPL households. Income-tax payers are excluded."

        # ─── 16. BPL-ONLY FROM special_conditions ─────────────────────────────
        special_cond = str(scheme.get("special_conditions_required", "") or "").lower()
        if any(kw in special_cond for kw in BPL_CONDITION_KEYWORDS):
            if not u_bpl:
                return False, "Scheme requires BPL card / Below Poverty Line status"

        # ─── 17. ALREADY HAS INSURANCE ────────────────────────────────────────
        if u_insured and any(kw in s_name for kw in BASIC_INSURANCE_SCHEMES):
            return False, "You already have insurance coverage"

        # ─── 18. ALREADY HAS PENSION ──────────────────────────────────────────
        if u_pension and any(kw in s_name for kw in BASIC_PENSION_SCHEMES):
            return False, "You already have a pension plan"

        # ─── 19. EDUCATION LEVEL FILTER ───────────────────────────────────────
        edu_req = str(scheme.get("education_level_required", "") or "").lower().strip()
        if edu_req and edu_req not in ["nan", "none", "any", "all", ""]:
            # If scheme requires graduate and user is below graduate → block
            for lvl in ["graduate", "postgraduate", "phd", "higher_secondary", "secondary"]:
                if lvl in edu_req and u_edu:
                    user_rank   = EDUCATION_RANK.get(u_edu, 0)
                    req_rank    = EDUCATION_RANK.get(lvl, 0)
                    if user_rank < req_rank:
                        return False, f"Scheme requires {lvl} education level (you: {u_edu or 'not specified'})"
                    break

        # ─── 20. OCCUPATION_ELIGIBILITY CSV COLUMN ────────────────────────────
        occ_elig = str(scheme.get("occupation_eligibility", "all")).lower().strip()
        if occ_elig not in ["all", "nan", "any", ""]:
            if ("farmer" in occ_elig or "agriculture" in occ_elig) and u_occ != "farmer" and not u_land:
                return False, "Scheme requires farmer occupation"
            if "student" in occ_elig and u_occ not in ["student", "unemployed"]:
                return False, "Scheme requires student occupation"
            if "employed" in occ_elig and u_occ not in ["employed", "retired"]:
                occ_exception = any(ex in occ_elig for ex in ["self", "un", "any"])
                if not occ_exception:
                    return False, "Scheme requires employed status"

        # ─── 21. COMMON-SENSE AGE BLOCKS ──────────────────────────────────────
        if u_age < 18:
            if any(kw in txt for kw in ["loan", "startup", "entrepreneur", "pension", "mudra"]):
                if "vidya" not in txt and "education loan" not in txt:
                    return False, "Financial/pension schemes require age 18+"
        if u_age < 14:
            if any(kw in txt for kw in ["employment", "rozgar", "insurance", "maternity"]):
                return False, "Not applicable for children under 14"

        # ─── 22. HAS AVAILED SIMILAR SCHEME (soft block via CSV tag) ──────────
        # If user said they've already availed a similar scheme,
        # block schemes that explicitly say "new applicants only"
        if u_availed:
            if any(kw in special_cond for kw in ["first time only", "new beneficiary", "not availed previously"]):
                return False, "Scheme is for first-time applicants only"

        # ─── 23. VARISHTHA / SENIOR-ONLY PENSION  ─────────────────────────────
        # These are investment/pension products designed for 60+ only
        if any(kw in txt for kw in SENIOR_ONLY_KEYWORDS):
            if u_age < 55 and not u_widsen:
                return False, "Scheme is for senior citizens aged 55+ only"

        # ─── 24. FREEDOM FIGHTER / SAINIK SAMMAN  ─────────────────────────────
        # These require proof of freedom fighting / military service
        if any(kw in txt for kw in FREEDOM_FIGHTER_KEYWORDS):
            return False, "Scheme is exclusively for freedom fighters / ex-servicemen"

        # ─── 25. SECTOR-SPECIFIC WORKER SCHEMES  ──────────────────────────────
        # Coal mines, beedi, plantation — require being in that sector
        if any(kw in txt for kw in SECTOR_WORKER_KEYWORDS):
            return False, "Scheme is for workers in a specific sector (coal/plantation/beedi)"

        # ─── 26. SPORTS ACHIEVEMENT SCHEMES  ──────────────────────────────────
        # Require national/international sports medals — not general public
        if any(kw in txt for kw in SPORTS_ACHIEVEMENT_KEYWORDS):
            return False, "Scheme is for meritorious sportspersons with national achievements"

        return True, ""

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN CHECK ELIGIBILITY  (pre-filter + ML + rule scoring)
    # ──────────────────────────────────────────────────────────────────────────
    def check_eligibility(self, user_profile: Any, scheme: Dict[str, Any], ml_prob: float) -> EligibilityResult:
        explanation = self._rule_based_explain(user_profile, scheme)
        hard_reject  = explanation.get("hard_reject", False)
        rule_eligible= explanation["eligible_rules"]

        if hard_reject:
            is_eligible = False
        elif rule_eligible:
            is_eligible = True
        else:
            is_eligible = ml_prob >= 0.55   # soft-mismatch needs high ML confidence

        return EligibilityResult(
            is_eligible=is_eligible,
            ml_confidence=ml_prob,
            reasons=explanation["reasons"],
            missing_criteria=explanation["missing"],
            path_to_eligibility=explanation["path_to_eligibility"],
            hard_reject=hard_reject,
            match_score=explanation.get("match_score", BASE_MATCH_SCORE),
        )

    # ──────────────────────────────────────────────────────────────────────────
    # RULE-BASED SCORING ENGINE  (produces match_score + reasons)
    # ──────────────────────────────────────────────────────────────────────────
    def _rule_based_explain(self, user: Any, scheme: Dict[str, Any]) -> Dict[str, Any]:
        g = self._g

        reasons: List[str] = []
        missing: List[str] = []
        eligible    = True
        hard_reject = False
        match_score = BASE_MATCH_SCORE
        path: List[str] = []

        u_age      = int(g(user, "age", 0))
        u_income   = int(g(user, "annualIncome", 0))
        u_occ      = str(g(user, "occupation", "")).lower().strip()
        u_gender   = str(g(user, "gender", "")).lower().strip()
        u_caste    = str(g(user, "caste", "")).lower().strip()
        u_edu      = str(g(user, "educationLevel", "")).lower().strip()
        u_urban    = str(g(user, "urbanRural", "")).lower().strip()
        u_emp_type = str(g(user, "employmentType", "")).lower().strip()
        u_skill    = str(g(user, "skillCertification", "")).lower().strip()
        u_loan_req = str(g(user, "loanRequirement", "none") or "none").lower()
        u_land     = bool(g(user, "hasLand", False))
        u_disabled = bool(g(user, "hasDisability", False))
        u_widsen   = bool(g(user, "isWidowOrSenior", False))
        u_single_g = bool(g(user, "isSingleGirlChild", False))
        u_bank     = bool(g(user, "isBankLinked", False))
        u_minority = bool(g(user, "isMinority", False))
        u_savings  = int(g(user, "monthlySavings", 0))
        u_fam_size = int(g(user, "familySize", 1))
        u_availed  = bool(g(user, "hasAvailedSimilarScheme", False))
        u_phone    = bool(g(user, "hasSmartphone", False))
        u_net      = bool(g(user, "hasInternet", False))

        s_name = str(scheme.get("scheme_name", "")).lower()
        s_desc = str(scheme.get("benefit_description", "")).lower()
        txt    = f"{s_name} {s_desc}"

        # ── A. AGE limits (CSV) ───────────────────────────────────────────────
        min_age = scheme.get("min_age")
        max_age = scheme.get("max_age")
        if not self._nan(min_age):
            try:
                if u_age < int(float(min_age)):
                    eligible = False; reasons.append(f"Below min age {int(float(min_age))}")
                else:
                    match_score += AGE_MATCH_BONUS
            except: pass
        if not self._nan(max_age):
            try:
                if u_age > int(float(max_age)):
                    eligible = False; reasons.append(f"Exceeds max age {int(float(max_age))}")
                else:
                    match_score += AGE_MATCH_BONUS
            except: pass

        # ── B. INCOME limit (CSV) ─────────────────────────────────────────────
        income_limit = scheme.get("income_limit")
        if not self._nan(income_limit):
            try:
                limit = float(income_limit)
                if limit > 0:
                    if u_income > limit:
                        eligible = False; reasons.append(f"Income Rs.{u_income} > limit Rs.{int(limit)}")
                    else:
                        match_score += INCOME_MATCH_BONUS
                        reasons.append(f"Income Rs.{u_income} within limit Rs.{int(limit)}")
            except: pass

        # ── C. OCCUPATION scoring ─────────────────────────────────────────────
        # Farmer schemes
        if any(kw in txt for kw in FARMER_HARD_KEYWORDS + FARMER_SOFT_KEYWORDS):
            if u_occ == "farmer" or u_land:
                match_score += OCCUPATION_MATCH_BONUS
                reasons.append("Farmer/landowner profile matches this agricultural scheme")
            else:
                eligible = False; hard_reject = True
                reasons.append("Scheme is for agricultural workers")

        # Student schemes
        if any(kw in txt for kw in STUDENT_HARD_KEYWORDS):
            if u_occ in ["student", "unemployed"]:
                match_score += OCCUPATION_MATCH_BONUS
                reasons.append("Student profile matches this scholarship scheme")
            else:
                eligible = False; hard_reject = True
                reasons.append("Scheme is exclusively for students")

        # Explicit occupation_eligibility CSV column
        occ_elig = str(scheme.get("occupation_eligibility", "all")).lower().strip()
        if occ_elig not in ["all", "nan", "any", ""]:
            if ("farmer" in occ_elig or "agriculture" in occ_elig) and u_occ != "farmer" and not u_land:
                eligible = False; hard_reject = True; reasons.append("Requires farmer occupation")
            elif "student" in occ_elig and u_occ not in ["student", "unemployed"]:
                eligible = False; hard_reject = True; reasons.append("Requires student occupation")

        # ── D. GENDER (CSV) ───────────────────────────────────────────────────
        gender_elig = str(scheme.get("gender_eligibility", "all")).lower().strip()
        if gender_elig not in ["all", "nan", "any", ""] and u_gender:
            if gender_elig == "female" and u_gender != "female":
                eligible = False; hard_reject = True; reasons.append("Reserved for female applicants")
            elif gender_elig == "female" and u_gender == "female":
                match_score += GENDER_MATCH_BONUS; reasons.append("Gender match: female scheme")
            elif gender_elig == "male" and u_gender != "male":
                eligible = False; hard_reject = True; reasons.append("Reserved for male applicants")

        # ── E. CASTE (CSV) ────────────────────────────────────────────────────
        caste_elig = str(scheme.get("caste_eligibility", "all")).lower().strip()
        if caste_elig not in ["all", "nan", "any", ""] and u_caste:
            valid = [c.strip() for c in caste_elig.split(",") if c.strip()]
            if valid:
                if any(u_caste == c or u_caste in c for c in valid):
                    match_score += CASTE_MATCH_BONUS; reasons.append(f"{u_caste.upper()} caste matches")
                else:
                    eligible = False; hard_reject = True
                    reasons.append(f"Reserved for {caste_elig.upper()}, you are {u_caste.upper()}")

        # ── F. DISABILITY (scheme name keywords) ──────────────────────────────
        if any(kw in s_name for kw in DISABILITY_HARD_KEYWORDS):
            if not u_disabled:
                eligible = False; hard_reject = True; reasons.append("Exclusive to persons with disabilities")
            else:
                match_score += OCCUPATION_MATCH_BONUS; reasons.append("Disability profile matches")

        # ── G. WIDOW/SENIOR ───────────────────────────────────────────────────
        if any(kw in txt for kw in WIDOW_SENIOR_KEYWORDS):
            if u_widsen or u_age >= 50:
                match_score += 0.25; reasons.append("Widow/Senior status is a strong match")
            else:
                eligible = False; hard_reject = True; reasons.append("Scheme is for widows or senior citizens")

        # ── H. WOMEN KEYWORDS + gender check ──────────────────────────────────
        if any(kw in s_name for kw in WOMEN_HARD_KEYWORDS):
            if gender_elig == "female" and u_gender != "female":
                eligible = False; hard_reject = True; reasons.append("Exclusive to women")

        # ─────────────────────────────────────────────────────────────────────
        # BONUS SCORING  (never blocks — only raises/lowers confidence score)
        # ─────────────────────────────────────────────────────────────────────

        # Loan requirement match
        if u_loan_req and u_loan_req != "none" and u_loan_req in LOAN_CATEGORY_KEYWORDS:
            if any(kw in txt for kw in LOAN_CATEGORY_KEYWORDS[u_loan_req]):
                match_score += 0.20; reasons.append(f"Matches your loan need: {u_loan_req}")

        # Skill certification match
        if u_skill and u_skill != "none" and u_skill in SKILL_SCHEME_KEYWORDS:
            if any(kw in txt for kw in SKILL_SCHEME_KEYWORDS[u_skill]):
                match_score += 0.15; reasons.append(f"Matches your {u_skill} skill profile")

        # Employment type match
        if u_emp_type and u_emp_type in EMPLOYMENT_SCHEME_KEYWORDS:
            if any(kw in txt for kw in EMPLOYMENT_SCHEME_KEYWORDS[u_emp_type]):
                match_score += 0.15; reasons.append(f"Matches your employment type: {u_emp_type}")

        # Single girl child → Sukanya / Beti schemes
        if u_single_g and any(kw in txt for kw in ["sukanya", "beti bachao", "single girl", "girl child"]):
            match_score += 0.20; reasons.append("Single girl child profile matches")

        # Minority match
        if u_minority and any(kw in txt for kw in MINORITY_SCHEME_KEYWORDS):
            match_score += 0.20; reasons.append("Minority community profile matches")

        # Urban / Rural alignment
        if u_urban == "rural" and any(kw in txt for kw in RURAL_ONLY_KEYWORDS):
            match_score += 0.10; reasons.append("Rural profile matches this scheme")
        if u_urban == "urban" and any(kw in txt for kw in URBAN_ONLY_KEYWORDS):
            match_score += 0.10; reasons.append("Urban profile matches this scheme")

        # Large family → food security / ration schemes
        if u_fam_size >= 5 and any(kw in txt for kw in ["ration", "food security", "anganwadi", "pds", "jan dhan"]):
            match_score += 0.10; reasons.append(f"Large family ({u_fam_size} members) prioritized")

        # Low savings → direct benefit / cash transfer priority
        if u_savings < 2000 and any(kw in txt for kw in ["direct benefit", "dbt", "cash transfer", "stipend", "financial assistance"]):
            match_score += 0.10; reasons.append("Low savings profile prioritized for cash-transfer schemes")

        # Bank-linked → DBT accessible
        if u_bank and any(kw in txt for kw in ["dbt", "direct benefit", "bank account"]):
            match_score += 0.05

        # Has smartphone + internet → digital scheme accessibility bonus
        if (u_phone or u_net) and any(kw in txt for kw in ["digital", "online", "digilocker", "e-portal", "pm e-vidya"]):
            match_score += 0.05

        # Education level boost → graduate-level research / fellowship schemes
        if u_edu in ["postgraduate", "phd"] and any(kw in txt for kw in ["research", "fellowship", "doctoral", "phd", "postdoctoral"]):
            match_score += 0.15; reasons.append(f"Education level ({u_edu}) matches research scheme")

        # Already availed similar scheme → slight de-prioritization
        if u_availed:
            match_score -= 0.05

        # ── Summary ───────────────────────────────────────────────────────────
        if eligible and not reasons:
            reasons.append("Profile satisfies all eligibility criteria")
        elif eligible:
            reasons.append("Advanced eligibility check passed")

        return {
            "eligible_rules": eligible,
            "hard_reject": hard_reject,
            "reasons": reasons,
            "missing": list(set(missing)),
            "match_score": min(MAX_SCORE, max(MIN_SCORE, match_score)),
            "path_to_eligibility": path,
        }

    # ── Compatibility helpers ──────────────────────────────────────────────────
    def _build_scheme_text(self, scheme: Dict[str, Any]) -> str:
        return f"{str(scheme.get('scheme_name','')).lower()} {str(scheme.get('benefit_description','')).lower()}"

    def _is_agriculture_scheme(self, t: str) -> bool:
        return any(k in t for k in FARMER_HARD_KEYWORDS + FARMER_SOFT_KEYWORDS)

    def _is_education_scheme(self, t: str) -> bool:
        return any(k in t for k in STUDENT_HARD_KEYWORDS)

    def _is_women_scheme(self, t: str) -> bool:
        return any(k in t for k in WOMEN_HARD_KEYWORDS)

    def _is_senior_scheme(self, t: str) -> bool:
        return any(k in t for k in WIDOW_SENIOR_KEYWORDS)

    def _is_disability_scheme(self, t: str) -> bool:
        return any(k in t for k in DISABILITY_HARD_KEYWORDS)

    def _is_child_scheme(self, t: str) -> bool:
        return any(k in t.split() for k in ["child", "children", "minor", "bal"])
