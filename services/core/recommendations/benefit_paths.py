"""
Benefit Paths & Multi-Programme Action Plans
Synthesizes structured, end-to-end multi-programme support pathways
(e.g., Udyam registration -> PM Mudra loan -> Credit Guarantee -> PMSBY/PMJJBY insurance)
based on structured scheme categories, taxonomy, and citizen goals without hardcoded scheme branching.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.core.database.models import Scheme, SchemeVersion, Category
from .candidate_service import CandidateService

class PathwayStageType(str, Enum):
    FOUNDATIONAL_REGISTRATION = "FOUNDATIONAL_REGISTRATION"
    WORKING_CAPITAL_FINANCING = "WORKING_CAPITAL_FINANCING"
    CREDIT_GUARANTEE_AND_RISK = "CREDIT_GUARANTEE_AND_RISK"
    RISK_AND_INSURANCE_PROTECTION = "RISK_AND_INSURANCE_PROTECTION"
    CAPACITY_BUILDING_AND_SKILLS = "CAPACITY_BUILDING_AND_SKILLS"
    PENSION_AND_LONG_TERM_SECURITY = "PENSION_AND_LONG_TERM_SECURITY"
    DIRECT_WELFARE_RELIEF = "DIRECT_WELFARE_RELIEF"

class CitizenGoal(str, Enum):
    START_OR_EXPAND_BUSINESS = "START_OR_EXPAND_BUSINESS"
    FARMING_AND_AGRICULTURE = "FARMING_AND_AGRICULTURE"
    UNORGANIZED_WORKER_SAFETY_NET = "UNORGANIZED_WORKER_SAFETY_NET"
    STUDENT_HIGHER_EDUCATION = "STUDENT_HIGHER_EDUCATION"
    FAMILY_HEALTH_AND_HOUSING = "FAMILY_HEALTH_AND_HOUSING"

@dataclass
class StageDefinition:
    stage_type: PathwayStageType
    title_template: str
    description_template: str
    action_template: str
    estimated_duration: str
    category_slugs: List[str]
    programme_kinds: List[str]
    keyword_patterns: List[str]
    output_deliverables: List[str]

GOAL_STAGE_CONFIGS: Dict[CitizenGoal, List[StageDefinition]] = {
    CitizenGoal.START_OR_EXPAND_BUSINESS: [
        StageDefinition(
            stage_type=PathwayStageType.FOUNDATIONAL_REGISTRATION,
            title_template="Step 1: Foundational Enterprise Registration & Compliance",
            description_template="Formally establish the enterprise identity to unlock MSME concessions, priority sector bank lending, and government vendor registration.",
            action_template="Register online on the official national MSME/enterprise portal using Aadhaar and PAN.",
            estimated_duration="1-2 working days",
            category_slugs=["business", "msme", "commerce", "registration", "enterprise"],
            programme_kinds=["welfare", "registration", "certification", "compliance"],
            keyword_patterns=["udyam", "msme", "registration", "shop", "gst", "enterprise", "startup"],
            output_deliverables=["Udyam Registration Certificate", "MSME Recognition Number"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.WORKING_CAPITAL_FINANCING,
            title_template="Step 2: Capital & Working Capital Financing",
            description_template="Secure collateral-free term loans and working capital credit facilities from nationalized banks or financial institutions.",
            action_template="Submit formal loan proposal to partner banks with the enterprise registration certificate.",
            estimated_duration="2-3 weeks",
            category_slugs=["financial_inclusion", "banking", "finance", "business", "credit"],
            programme_kinds=["loan", "credit", "grant", "subsidy"],
            keyword_patterns=["mudra", "loan", "working capital", "credit", "stand-up", "pmegp", "shishu", "kishore", "tarun"],
            output_deliverables=["Sanctioned Credit Facility", "Working Capital Account"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.CREDIT_GUARANTEE_AND_RISK,
            title_template="Step 3: Credit Guarantee & Collateral Risk Backing",
            description_template="Leverage government-backed sovereign credit guarantees so commercial banks disburse loans without demanding physical collateral or third-party guarantors.",
            action_template="Request partner bank to route sanction under the official national Credit Guarantee Trust scheme.",
            estimated_duration="Integrated with Bank Loan Sanction",
            category_slugs=["credit_guarantee", "risk_mitigation", "banking", "finance"],
            programme_kinds=["guarantee", "loan", "risk_support"],
            keyword_patterns=["guarantee", "cgtmse", "cgfmu", "credit guarantee", "collateral"],
            output_deliverables=["Credit Guarantee Coverage Certificate", "Zero-Collateral Lien Document"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.RISK_AND_INSURANCE_PROTECTION,
            title_template="Step 4: Entrepreneur & Workforce Social Insurance Protection",
            description_template="Insure key personnel, entrepreneurs, and workforce against accidental disablement and mortality to ensure business continuity.",
            action_template="Enroll in subsidized national accidental and life protection insurance schemes linked to your bank account.",
            estimated_duration="Instant on auto-debit consent",
            category_slugs=["insurance", "social_security", "financial_inclusion"],
            programme_kinds=["insurance", "social_security"],
            keyword_patterns=["pmsby", "pmjjby", "suraksha", "jeevan jyoti", "insurance", "bima"],
            output_deliverables=["Active PMSBY/PMJJBY Policy Receipts", "Designated Nominee Registration"]
        ),
    ],
    CitizenGoal.FARMING_AND_AGRICULTURE: [
        StageDefinition(
            stage_type=PathwayStageType.FOUNDATIONAL_REGISTRATION,
            title_template="Step 1: Landholding & Farmer Identity Validation",
            description_template="Validate agricultural landholder status and register in the central farmer portal for direct benefit transfers.",
            action_template="Link land records (Khata/Khasra) and Aadhaar in the agricultural portal.",
            estimated_duration="3-5 days",
            category_slugs=["agriculture", "farming", "rural_development"],
            programme_kinds=["welfare", "registration"],
            keyword_patterns=["pm-kisan", "kisan", "farmer", "land", "krishi"],
            output_deliverables=["PM-KISAN Farmer ID", "Verified Land Record Token"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.WORKING_CAPITAL_FINANCING,
            title_template="Step 2: Subsidized Agricultural Seasonal Credit (KCC)",
            description_template="Obtain flexible agricultural credit at subsidized interest subvention rates for seeds, fertilizers, and farm equipment.",
            action_template="Apply for Kisan Credit Card (KCC) at local bank branch or PACS with land record.",
            estimated_duration="1-2 weeks",
            category_slugs=["agriculture", "banking", "financial_inclusion"],
            programme_kinds=["loan", "credit"],
            keyword_patterns=["kcc", "kisan credit", "credit card", "crop loan", "interest subvention"],
            output_deliverables=["Kisan Credit Card (KCC)", "Revolving Crop Credit Limit"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.RISK_AND_INSURANCE_PROTECTION,
            title_template="Step 3: Comprehensive Crop & Weather Risk Insurance",
            description_template="Safeguard against crop losses from drought, floods, pests, or unseasonal weather variations.",
            action_template="Enroll sown crop acreage under PM Fasal Bima Yojana before seasonal cut-off.",
            estimated_duration="Cut-off date seasonal enrollment",
            category_slugs=["agriculture", "insurance"],
            programme_kinds=["insurance"],
            keyword_patterns=["fasal bima", "pmfby", "crop insurance", "weather"],
            output_deliverables=["Crop Insurance Policy Certificate", "Acreage Under Risk Cover"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.PENSION_AND_LONG_TERM_SECURITY,
            title_template="Step 4: Old-Age Farmer Pension & Social Security",
            description_template="Build a guaranteed monthly pension of ₹3,000/month after age 60 to ensure dignity in senior years.",
            action_template="Enroll in PM Kisan Maan Dhan Yojana (PM-KMY) via nearest CSC center.",
            estimated_duration="Same day enrollment",
            category_slugs=["social_security", "pension", "agriculture"],
            programme_kinds=["welfare", "pension"],
            keyword_patterns=["maan dhan", "pm-kmy", "pension", "farmer pension"],
            output_deliverables=["KMY Pension Card", "Guaranteed Monthly Annuity Receipt"]
        ),
    ],
    CitizenGoal.UNORGANIZED_WORKER_SAFETY_NET: [
        StageDefinition(
            stage_type=PathwayStageType.FOUNDATIONAL_REGISTRATION,
            title_template="Step 1: National Unorganized Worker Registration (e-Shram)",
            description_template="Obtain a permanent 12-digit Universal Account Number (UAN) as legal recognition in the unorganized workforce.",
            action_template="Register on e-Shram portal with Aadhaar and active mobile number.",
            estimated_duration="Instant online / CSC",
            category_slugs=["employment", "labour", "social_security"],
            programme_kinds=["welfare", "registration"],
            keyword_patterns=["e-shram", "eshram", "uan", "labour", "worker", "unorganized"],
            output_deliverables=["e-Shram Digital Card", "Universal Account Number (UAN)"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.WORKING_CAPITAL_FINANCING,
            title_template="Step 2: Micro-Livelihood & Street Vendor Working Capital",
            description_template="Access collateral-free micro-credit loans for enterprise capital with timely repayment interest cashbacks.",
            action_template="Apply for micro-credit on PM SVANidhi or Mudra micro portal.",
            estimated_duration="7-10 days",
            category_slugs=["financial_inclusion", "urban_development", "credit"],
            programme_kinds=["loan", "credit"],
            keyword_patterns=["svanidhi", "street vendor", "micro", "shishu"],
            output_deliverables=["Sanctioned Micro Credit", "Digital Cashback Eligibility"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.RISK_AND_INSURANCE_PROTECTION,
            title_template="Step 3: Universal Health & Accidental Safety Net",
            description_template="Attain cashless secondary and tertiary hospitalization cover and accidental disability insurance.",
            action_template="Generate Ayushman Bharat card and link PMSBY to bank account.",
            estimated_duration="1-3 days",
            category_slugs=["health", "insurance", "social_security"],
            programme_kinds=["insurance", "welfare"],
            keyword_patterns=["ayushman", "pm-jay", "pmsby", "suraksha", "health card"],
            output_deliverables=["Ayushman Bharat Golden Card", "₹5 Lakh Family Health Cover"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.PENSION_AND_LONG_TERM_SECURITY,
            title_template="Step 4: Contributory Old-Age Pension (PM-SYM / APY)",
            description_template="Ensure ₹3,000 monthly pension post 60 with 50% matching government co-contribution.",
            action_template="Complete auto-debit mandate for PM Shram Yogi Maan-dhan at bank/CSC.",
            estimated_duration="Instant activation",
            category_slugs=["pension", "social_security"],
            programme_kinds=["welfare", "pension"],
            keyword_patterns=["pm-sym", "shram yogi", "atal pension", "apy", "pension"],
            output_deliverables=["PM-SYM Pension Ledger", "Guaranteed Minimum Pension Guarantee"]
        ),
    ],
    CitizenGoal.STUDENT_HIGHER_EDUCATION: [
        StageDefinition(
            stage_type=PathwayStageType.FOUNDATIONAL_REGISTRATION,
            title_template="Step 1: Academic Identity & National Scholarship Registration",
            description_template="Establish unified student identity (APAAR / NSP) for direct DBT scholarship disbursement.",
            action_template="Register profile on National Scholarship Portal (NSP) with institute verification.",
            estimated_duration="3-5 days",
            category_slugs=["education", "higher_education"],
            programme_kinds=["welfare", "registration"],
            keyword_patterns=["nsp", "scholarship", "apaar", "student", "matric"],
            output_deliverables=["NSP Application ID", "Institute Verification Status"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.WORKING_CAPITAL_FINANCING,
            title_template="Step 2: Subsidized Education Financing & Tuition Grants",
            description_template="Receive direct tuition fee concessions, maintenance allowances, or interest-subsidized student loans.",
            action_template="Apply via Vidya Lakshmi portal or central scholarship department.",
            estimated_duration="2-4 weeks",
            category_slugs=["education", "financial_inclusion"],
            programme_kinds=["grant", "loan", "scholarship", "welfare"],
            keyword_patterns=["vidya lakshmi", "education loan", "fellowship", "post-matric", "merit"],
            output_deliverables=["Sanctioned Education Credit", "Direct Tuition Fee Reimbursement"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.CAPACITY_BUILDING_AND_SKILLS,
            title_template="Step 3: Industry Certification & Apprenticeship Stipends",
            description_template="Acquire industry-accredited technical certifications with government-paid monthly apprenticeships.",
            action_template="Enroll in NSDC Skill India training center or National Apprenticeship Promotion Scheme (NAPS).",
            estimated_duration="1-3 months",
            category_slugs=["skills", "employment", "training"],
            programme_kinds=["training", "welfare"],
            keyword_patterns=["pmkvy", "skill india", "apprenticeship", "naps", "vocational"],
            output_deliverables=["Govt Certified Skill Badge", "Monthly Apprenticeship Stipend"]
        ),
    ],
    CitizenGoal.FAMILY_HEALTH_AND_HOUSING: [
        StageDefinition(
            stage_type=PathwayStageType.FOUNDATIONAL_REGISTRATION,
            title_template="Step 1: Family Ration & Socio-Economic Verification",
            description_template="Verify family inclusion in state food security and socio-economic databases.",
            action_template="Confirm Aadhaar seeding on state food and civil supplies portal.",
            estimated_duration="2-3 days",
            category_slugs=["food_security", "social_security", "housing"],
            programme_kinds=["welfare", "registration"],
            keyword_patterns=["ration", "bpl", "secc", "nfsa", "family"],
            output_deliverables=["Active Digital Ration Card", "Verified Family Registry"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.RISK_AND_INSURANCE_PROTECTION,
            title_template="Step 2: Comprehensive Cashless Family Healthcare (PM-JAY)",
            description_template="Attain ₹5,00,000 per family per year for secondary and tertiary hospitalized treatments.",
            action_template="Generate ABHA ID and Ayushman cards for every household member.",
            estimated_duration="1-2 days",
            category_slugs=["health", "medical", "insurance"],
            programme_kinds=["insurance", "welfare"],
            keyword_patterns=["ayushman", "pm-jay", "health", "hospital"],
            output_deliverables=["Family Ayushman Cards", "Empaneled Hospital Access"]
        ),
        StageDefinition(
            stage_type=PathwayStageType.WORKING_CAPITAL_FINANCING,
            title_template="Step 3: Pucca Housing Financial Assistance (PMAY)",
            description_template="Access direct financial grant assistance for construction or interest subsidy on home construction.",
            action_template="Submit housing beneficiary application to Urban Local Body or Gram Panchayat.",
            estimated_duration="3-6 weeks",
            category_slugs=["housing", "urban_development", "rural_development"],
            programme_kinds=["grant", "subsidy", "welfare"],
            keyword_patterns=["pmay", "awas", "housing", "pucca house"],
            output_deliverables=["Sanctioned PMAY Beneficiary ID", "Direct Construction Tranches"]
        ),
    ]
}

# ── Pydantic Response Models ──────────────────────────────────────────────────

class PathwayStep(BaseModel):
    step_number: int
    stage_title: str
    stage_type: str
    description: str
    action_item: str
    estimated_duration: str
    schemes: List[Dict[str, Any]] = Field(default_factory=list)
    prerequisites_unlocked: List[str] = Field(default_factory=list)

class BenefitPathway(BaseModel):
    pathway_id: str
    goal_id: str
    goal_title: str
    description: str
    target_citizen_profile: str
    total_milestones: int
    total_schemes_count: int
    steps: List[PathwayStep]
    cumulative_benefits_summary: str
    printable_action_plan_markdown: str

# ── Benefit Path Synthesizer Engine ──────────────────────────────────────────

class BenefitPathEngine:
    """
    Synthesizes multi-programme support pathways by mapping scheme categories,
    taxonomies, and prerequisites dynamically without hardcoded branching.
    """
    def __init__(self, db: Session):
        self.db = db
        self.candidate_service = CandidateService(db)

    def detect_recommended_goals(self, facts: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Dynamically infers the most relevant Citizen Goals based on profile facts.
        """
        goals: List[Dict[str, str]] = []
        occ = str(facts.get("person.occupation") or facts.get("occupation") or "").lower()
        has_business = facts.get("business.is_owner") or "business" in occ or "shop" in occ or "self_employed" in occ
        is_farmer = facts.get("farmer.is_farmer") or "farmer" in occ or "agriculture" in occ or facts.get("land.has_agricultural_land")
        is_student = facts.get("student.is_enrolled") or "student" in occ
        is_daily_wage = "daily_wage" in occ or "unorganized" in occ or "vendor" in occ or facts.get("social.is_bpl")

        if has_business:
            goals.append({
                "goal_id": CitizenGoal.START_OR_EXPAND_BUSINESS.value,
                "title": "Start & Scale a Micro/Small Business",
                "rationale": "Matches your declared enterprise interest or business ownership."
            })
        if is_farmer:
            goals.append({
                "goal_id": CitizenGoal.FARMING_AND_AGRICULTURE.value,
                "title": "Agricultural Prosperity & Crop Protection",
                "rationale": "Matches your farming occupation or agricultural landholding."
            })
        if is_daily_wage or not (has_business or is_farmer or is_student):
            goals.append({
                "goal_id": CitizenGoal.UNORGANIZED_WORKER_SAFETY_NET.value,
                "title": "Unorganized Worker Livelihood & Safety Net",
                "rationale": "Provides essential institutional identity, micro-capital, and insurance."
            })
        if is_student:
            goals.append({
                "goal_id": CitizenGoal.STUDENT_HIGHER_EDUCATION.value,
                "title": "Higher Education, Scholarships & Career Skilling",
                "rationale": "Matches your student profile to access education financing and stipends."
            })

        # Universal fallback: Family Health & Housing
        goals.append({
            "goal_id": CitizenGoal.FAMILY_HEALTH_AND_HOUSING.value,
            "title": "Comprehensive Family Health & Housing Security",
            "rationale": "Foundational safety net recommended for every citizen household."
        })

        return goals

    def _match_schemes_for_stage(
        self,
        stage: StageDefinition,
        candidates: List[Dict[str, Any]],
        evaluated_schemes_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Dynamically scores and matches candidate schemes to a pathway stage
        based on category, programme_kind, and semantic keywords.
        """
        matched: List[Dict[str, Any]] = []

        for cand in candidates:
            scheme_id = cand["scheme_id"]
            name = cand.get("scheme_name", "").lower()
            summary = cand.get("summary", "").lower()
            kind = (cand.get("programme_kind") or "").lower()
            eval_info = evaluated_schemes_map.get(scheme_id, {})
            elig_status = eval_info.get("eligibility_status", "NEEDS_INFO")

            score = 0
            # 1. Match programme kind
            if kind in stage.programme_kinds:
                score += 3

            # 2. Match keyword patterns
            for kw in stage.keyword_patterns:
                if kw in name:
                    score += 5
                elif kw in summary:
                    score += 2

            if score > 0:
                benefit_str = eval_info.get("benefit_amount") or cand.get("summary") or "Government sanctioned assistance"
                matched.append({
                    "scheme_id": scheme_id,
                    "scheme_name": cand.get("scheme_name"),
                    "programme_kind": cand.get("programme_kind"),
                    "eligibility_status": elig_status,
                    "benefit_amount": benefit_str,
                    "application_url": cand.get("application_url") or cand.get("source_url", ""),
                    "match_score": score
                })

        # Sort: ELIGIBLE first, then by match_score descending
        status_weight = {"ELIGIBLE": 1, "NEEDS_INFO": 2, "NEEDS_VERIFICATION": 3, "NOT_ELIGIBLE": 4}
        matched.sort(key=lambda x: (status_weight.get(x["eligibility_status"], 99), -x["match_score"]))
        return matched[:3]

    def synthesize_pathway(
        self,
        goal_id: str,
        facts: Optional[Dict[str, Any]] = None,
        evaluated_schemes: Optional[List[Dict[str, Any]]] = None
    ) -> BenefitPathway:
        """
        Synthesizes an end-to-end structured pathway for a citizen goal.
        """
        facts = facts or {}
        try:
            goal_enum = CitizenGoal(goal_id)
        except ValueError:
            goal_enum = CitizenGoal.START_OR_EXPAND_BUSINESS

        stage_defs = GOAL_STAGE_CONFIGS.get(goal_enum, GOAL_STAGE_CONFIGS[CitizenGoal.START_OR_EXPAND_BUSINESS])

        # Retrieve candidates from DB
        candidates = self.candidate_service.get_candidates(limit=100)

        # Build lookup for evaluated schemes if provided
        eval_map: Dict[str, Dict[str, Any]] = {}
        if evaluated_schemes:
            for s in evaluated_schemes:
                eval_map[s["scheme_id"]] = s

        steps: List[PathwayStep] = []
        total_schemes_count = 0
        previous_unlocks: List[str] = []

        for idx, stage in enumerate(stage_defs, start=1):
            matched_schemes = self._match_schemes_for_stage(stage, candidates, eval_map)
            total_schemes_count += len(matched_schemes)

            step = PathwayStep(
                step_number=idx,
                stage_title=stage.title_template,
                stage_type=stage.stage_type.value,
                description=stage.description_template,
                action_item=stage.action_template,
                estimated_duration=stage.estimated_duration,
                schemes=matched_schemes,
                prerequisites_unlocked=stage.output_deliverables
            )
            steps.append(step)
            previous_unlocks.extend(stage.output_deliverables)

        # Generate human-readable goal title and cumulative summary
        goal_titles = {
            CitizenGoal.START_OR_EXPAND_BUSINESS: "Enterprise Growth Pathway: Registration to Working Capital & Safety",
            CitizenGoal.FARMING_AND_AGRICULTURE: "Farmer Empowerment Pathway: Land Registry to Subsidized Credit & Insurance",
            CitizenGoal.UNORGANIZED_WORKER_SAFETY_NET: "Gig & Unorganized Worker Safety Net: e-Shram to Micro-Loans & Health Cover",
            CitizenGoal.STUDENT_HIGHER_EDUCATION: "Student Empowerment Pathway: NSP Scholarships to Skilling & Career Loans",
            CitizenGoal.FAMILY_HEALTH_AND_HOUSING: "Family Security Pathway: Ration Seeding to PM-JAY & Housing Assistance"
        }
        title = goal_titles.get(goal_enum, "Citizen Welfare & Empowerment Pathway")

        cumulative_summaries = {
            CitizenGoal.START_OR_EXPAND_BUSINESS: "Unlocks formal MSME status, collateral-free loans up to ₹10-20 Lakhs, sovereign credit guarantees, and full workforce risk protection.",
            CitizenGoal.FARMING_AND_AGRICULTURE: "Provides annual direct income transfer, seasonal revolving crop credit at 4% subvention, 100% crop damage insurance, and ₹3,000 monthly old-age pension.",
            CitizenGoal.UNORGANIZED_WORKER_SAFETY_NET: "Grants national UAN labor identity, ₹10k-50k working capital loans, ₹5 Lakh family cashless health coverage, and contributory retirement security.",
            CitizenGoal.STUDENT_HIGHER_EDUCATION: "Secures direct tuition grants, zero-interest education loans, and paid monthly apprenticeship stipends.",
            CitizenGoal.FAMILY_HEALTH_AND_HOUSING: "Combines digital food security ration, ₹5 Lakhs per family annual cashless hospitalization, and direct pucca housing construction grants."
        }
        cumulative_text = cumulative_summaries.get(goal_enum, "Coordinated multi-programme public entitlement support.")

        # Markdown Action Plan
        md_lines = [
            f"# {title}",
            f"**Pathway Goal ID**: `{goal_enum.value}`  ",
            f"**Total Sequential Milestones**: {len(steps)} | **Recommended Programmes**: {total_schemes_count}  ",
            f"**Cumulative Benefit Summary**: {cumulative_text}\n",
            "---",
            "## Structured Action Roadmap\n"
        ]

        for s in steps:
            md_lines.append(f"### {s.stage_title}")
            md_lines.append(f"- **Purpose**: {s.description}")
            md_lines.append(f"- **Citizen Action Required**: {s.action_item}")
            md_lines.append(f"- **Estimated Timeline**: {s.estimated_duration}")
            if s.schemes:
                md_lines.append("- **Relevant Official Programmes**:")
                for sc in s.schemes:
                    st_badge = f"[{sc['eligibility_status']}]"
                    md_lines.append(f"  - **{sc['scheme_name']}** {st_badge}: {sc['benefit_amount']}")
            if s.prerequisites_unlocked:
                md_lines.append(f"- **Milestones Unlocked for Subsequent Steps**: {', '.join(s.prerequisites_unlocked)}")
            md_lines.append("")

        action_plan_md = "\n".join(md_lines)

        return BenefitPathway(
            pathway_id=str(uuid.uuid4()),
            goal_id=goal_enum.value,
            goal_title=title,
            description=stage_defs[0].description_template,
            target_citizen_profile=f"Citizen aiming for {goal_enum.value.replace('_', ' ').title()}",
            total_milestones=len(steps),
            total_schemes_count=total_schemes_count,
            steps=steps,
            cumulative_benefits_summary=cumulative_text,
            printable_action_plan_markdown=action_plan_md
        )