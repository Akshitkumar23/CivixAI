from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from .contract import (
    CanonicalFactDefinition, CollectionMethod, SubjectScope,
    DataType, VerificationLevel
)
from .derivation import apply_deterministic_derivations

# Backwards compatibility model
class FactDefinition(BaseModel):
    key: str
    type: str  # integer, float, string, boolean, enum
    sensitivity: str = "normal"  # normal, sensitive, financial
    allowed_values: Optional[List[Any]] = None
    description: str = ""
    unit: Optional[str] = None
    collection_method: str = "QUESTION"
    subject_scope: str = "applicant"

# ── Canonical Fact Contract (58+ Statutory Facts) ─────────────────────────────
CANONICAL_FACT_CONTRACT: Dict[str, CanonicalFactDefinition] = {
    # ── 1. Demographics & Personal ───────────────────────────────────────────
    "person.age": CanonicalFactDefinition(
        fact_key="person.age",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.INTEGER,
        aliases=["applicant.age", "age"],
        unit="years",
        sensitivity="normal",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Age in completed years as per official government photo ID."
    ),
    "person.gender": CanonicalFactDefinition(
        fact_key="person.gender",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.ENUM,
        allowed_values=["male", "female", "other", "all"],
        aliases=["applicant.gender", "gender"],
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory gender identity for targeted welfare quotas."
    ),
    "person.marital_status": CanonicalFactDefinition(
        fact_key="person.marital_status",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.ENUM,
        allowed_values=["single", "married", "widowed", "divorced"],
        aliases=["applicant.marital_status", "marital_status", "maritalStatus"],
        sensitivity="normal",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Marital status governing survivor/widow entitlements."
    ),
    "person.is_widow_or_senior": CanonicalFactDefinition(
        fact_key="person.is_widow_or_senior",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["applicant.is_widow_or_senior", "is_widow_or_senior", "isWidowOrSenior"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Flag for social security pensions and senior citizen support."
    ),
    "person.is_single_girl_child": CanonicalFactDefinition(
        fact_key="person.is_single_girl_child",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["applicant.is_single_girl_child", "is_single_girl_child", "isSingleGirlChild"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Self-declaration of being the sole girl child in family."
    ),
    "applicant.has_siblings_excluding_single_girl_status": CanonicalFactDefinition(
        fact_key="applicant.has_siblings_excluding_single_girl_status",
        subject_scope=SubjectScope.FAMILY,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Presence of siblings disqualifying single girl child status."
    ),
    "applicant.within_eligible_age_bracket": CanonicalFactDefinition(
        fact_key="applicant.within_eligible_age_bracket",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_pmjjby_within_age_bracket",
        question_available=False,
        source_semantics="Age between 18 and 50 years for life insurance enrollment."
    ),
    "applicant.outside_eligible_age_bracket": CanonicalFactDefinition(
        fact_key="applicant.outside_eligible_age_bracket",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_ddu_gky_outside_age_bracket",
        question_available=False,
        source_semantics="Age outside 15-35 years disqualifying rural youth training."
    ),
    "applicant.remarriage_occurred": CanonicalFactDefinition(
        fact_key="applicant.remarriage_occurred",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory remarriage clause for IGNWPS pension termination."
    ),
    "applicant.has_driving_license": CanonicalFactDefinition(
        fact_key="applicant.has_driving_license",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["has_driving_license", "driving_license", "drivingLicense", "applicant.driving_license"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Holding of a valid driving license for transport or self-employment vehicle schemes."
    ),
    "applicant.has_commercial_driving_license": CanonicalFactDefinition(
        fact_key="applicant.has_commercial_driving_license",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["has_commercial_driving_license", "commercial_driving_license"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Holding of a valid commercial or passenger transport driving license."
    ),
    "person.is_citizen_of_india": CanonicalFactDefinition(
        fact_key="person.is_citizen_of_india",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["is_citizen_of_india", "citizen_of_india", "is_indian_citizen", "applicant.is_citizen_of_india"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Indian citizenship requirement for statutory welfare entitlement."
    ),
    "applicant.eligible_statutory_beneficiary": CanonicalFactDefinition(
        fact_key="applicant.eligible_statutory_beneficiary",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["eligible_statutory_beneficiary"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory qualification under designated beneficiary list or gazetted order."
    ),
    "applicant.previous_benefit": CanonicalFactDefinition(
        fact_key="applicant.previous_benefit",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["previous_benefit", "has_received_previous_benefit"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Previous receipt of similar government subsidy or scheme benefit."
    ),
    "family.status": CanonicalFactDefinition(
        fact_key="family.status",
        subject_scope=SubjectScope.FAMILY,
        data_type=DataType.STRING,
        aliases=["family_status"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Family statutory condition (e.g. orphan, destitute, single parent, separated)."
    ),

    # ── 2. Geography & Jurisdiction ──────────────────────────────────────────
    "location.state": CanonicalFactDefinition(
        fact_key="location.state",
        subject_scope=SubjectScope.LOCATION,
        data_type=DataType.STRING,
        aliases=["applicant.state", "state"],
        collection_method=CollectionMethod.QUESTION,
        derivation_policy="derive_canonical_state",
        question_available=True,
        source_semantics="State or Union Territory of domicile/residence."
    ),
    "location.district": CanonicalFactDefinition(
        fact_key="location.district",
        subject_scope=SubjectScope.LOCATION,
        data_type=DataType.STRING,
        aliases=["applicant.district", "district"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="District of permanent residence."
    ),
    "location.urban_rural": CanonicalFactDefinition(
        fact_key="location.urban_rural",
        subject_scope=SubjectScope.LOCATION,
        data_type=DataType.ENUM,
        allowed_values=["urban", "rural", "all"],
        aliases=["urban_rural", "urbanRural"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Urban municipality vs rural panchayat jurisdiction."
    ),
    "location.area_type": CanonicalFactDefinition(
        fact_key="location.area_type",
        subject_scope=SubjectScope.LOCATION,
        data_type=DataType.ENUM,
        allowed_values=["urban", "rural", "peri_urban", "all"],
        aliases=["area_type", "areaType"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Granular area classification for housing schemes."
    ),
    "location.outside_urban_jurisdiction": CanonicalFactDefinition(
        fact_key="location.outside_urban_jurisdiction",
        subject_scope=SubjectScope.LOCATION,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_outside_urban_jurisdiction",
        question_available=False,
        source_semantics="Location outside ULB statutory limits for urban sanitation grants."
    ),
    "applicant.lacks_rural_domicile": CanonicalFactDefinition(
        fact_key="applicant.lacks_rural_domicile",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_lacks_rural_domicile",
        question_available=False,
        source_semantics="Absence of rural panchayat domicile disqualifying rural schemes."
    ),
    "applicant.has_ner_domicile": CanonicalFactDefinition(
        fact_key="applicant.has_ner_domicile",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_ner_domicile",
        question_available=False,
        source_semantics="Permanent resident of 8 North Eastern States for Ishan Uday."
    ),
    "student.domicile_state": CanonicalFactDefinition(
        fact_key="student.domicile_state",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.STRING,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_student_domicile_from_location",
        question_available=False,
        source_semantics="State domicile of student for state-quota scholarships."
    ),

    # ── 3. Social Category & Inclusion ───────────────────────────────────────
    "social.caste": CanonicalFactDefinition(
        fact_key="social.caste",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.ENUM,
        allowed_values=["general", "obc", "sc", "st", "all"],
        aliases=["applicant.caste", "caste", "category"],
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Social reservation category under Constitutional orders."
    ),
    "social.is_minority": CanonicalFactDefinition(
        fact_key="social.is_minority",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["applicant.is_minority", "is_minority", "isMinority"],
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Notified religious minority status (Muslim, Christian, Sikh, Buddhist, Jain, Parsi)."
    ),
    "applicant.not_belonging_to_minority_community": CanonicalFactDefinition(
        fact_key="applicant.not_belonging_to_minority_community",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        sensitivity="sensitive",
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_minority_community_exclusion",
        question_available=False,
        source_semantics="Disqualification from minority-exclusive welfare schemes."
    ),
    "social.is_bpl": CanonicalFactDefinition(
        fact_key="social.is_bpl",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        aliases=["household.is_bpl", "applicant.is_bpl", "is_bpl", "isBPL"],
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Self-declaration of Below Poverty Line / Antyodaya ration card."
    ),
    "household.bpl_status_verified": CanonicalFactDefinition(
        fact_key="household.bpl_status_verified",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        verification_level=VerificationLevel.DOCUMENT_SUPPORTED,
        question_available=True,
        source_semantics="Official BPL / SECC 2011 / Ration Card verification."
    ),

    # ── 4. Health & Disability ───────────────────────────────────────────────
    "health.has_disability": CanonicalFactDefinition(
        fact_key="health.has_disability",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["applicant.has_disability", "person.has_disability", "has_disability", "hasDisability"],
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Possession of benchmark disability under RPwD Act 2016."
    ),
    "health.disability_pct": CanonicalFactDefinition(
        fact_key="health.disability_pct",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.FLOAT,
        aliases=["person.disability_percentage", "applicant.disability_pct", "disability_pct", "disabilityPct"],
        unit="percentage",
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Benchmark disability percentage recorded on UDID card."
    ),
    "person.disability_percentage": CanonicalFactDefinition(
        fact_key="person.disability_percentage",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.FLOAT,
        aliases=["health.disability_pct", "applicant.disability_pct", "disability_pct", "disabilityPct"],
        unit="percentage",
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Disability percentage for IGNDPS / Saksham scholarship."
    ),
    "beneficiary.meets_severe_disability_threshold": CanonicalFactDefinition(
        fact_key="beneficiary.meets_severe_disability_threshold",
        subject_scope=SubjectScope.BENEFICIARY,
        data_type=DataType.BOOLEAN,
        sensitivity="sensitive",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Severe disability threshold (>=80% or multiple disability) for IGNDPS."
    ),
    "student.disability_below_disability_threshold": CanonicalFactDefinition(
        fact_key="student.disability_below_disability_threshold",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_disability_below_threshold",
        question_available=False,
        source_semantics="Disqualification if disability is below statutory benchmark 40%."
    ),
    "beneficiary.has_disability_certificate": CanonicalFactDefinition(
        fact_key="beneficiary.has_disability_certificate",
        subject_scope=SubjectScope.BENEFICIARY,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Valid UDID card or government medical board certificate."
    ),

    # ── 5. Household Finances & Living Conditions ────────────────────────────
    "household.annual_income": CanonicalFactDefinition(
        fact_key="household.annual_income",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.FLOAT,
        aliases=["annual_income", "annualIncome"],
        unit="INR",
        sensitivity="financial",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Total gross annual income of all household members from all sources."
    ),
    "student.family_annual_income": CanonicalFactDefinition(
        fact_key="student.family_annual_income",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.FLOAT,
        unit="INR",
        sensitivity="financial",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Parental/family annual income for scholarship ceilings."
    ),
    "family.income_exceeds_income_ceiling": CanonicalFactDefinition(
        fact_key="family.income_exceeds_income_ceiling",
        subject_scope=SubjectScope.FAMILY,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_ishan_uday_income_ceiling",
        question_available=False,
        source_semantics="Statutory income disqualification flag."
    ),
    "student.exceeds_family_income_ceiling": CanonicalFactDefinition(
        fact_key="student.exceeds_family_income_ceiling",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_nmms_exceeds_income_ceiling",
        question_available=False,
        source_semantics="Income exceeds INR 3.5 Lakh ceiling for NMMSS."
    ),
    "student.exceeds_pre_matric_minority_income_ceiling": CanonicalFactDefinition(
        fact_key="student.exceeds_pre_matric_minority_income_ceiling",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_pre_matric_minority_income_ceiling",
        question_available=False,
        source_semantics="Income exceeds INR 1.0 Lakh ceiling for Pre-Matric Minority."
    ),
    "student.exceeds_post_matric_minority_income_ceiling": CanonicalFactDefinition(
        fact_key="student.exceeds_post_matric_minority_income_ceiling",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_post_matric_minority_income_ceiling",
        question_available=False,
        source_semantics="Income exceeds INR 2.0 Lakh ceiling for Post-Matric Minority."
    ),
    "student.exceeds_aicte_family_income_ceiling": CanonicalFactDefinition(
        fact_key="student.exceeds_aicte_family_income_ceiling",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_aicte_income_ceiling",
        question_available=False,
        source_semantics="Income exceeds INR 8.0 Lakh ceiling for AICTE Pragati/Saksham."
    ),
    "household.exceeds_income_cap": CanonicalFactDefinition(
        fact_key="household.exceeds_income_cap",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.DETERMINISTIC_DERIVATION,
        derivation_policy="derive_pmay_u_income_cap",
        question_available=False,
        source_semantics="Income exceeds highest PMAY-U eligibility limit."
    ),
    "household.family_size": CanonicalFactDefinition(
        fact_key="household.family_size",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.INTEGER,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Number of dependent family members sharing common hearth."
    ),
    "family.exceeds_family_limit_girl_children": CanonicalFactDefinition(
        fact_key="family.exceeds_family_limit_girl_children",
        subject_scope=SubjectScope.FAMILY,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory cap on maximum 2 girl children per family for Pragati scholarship."
    ),

    # ── 6. Taxes, Banking & Formal Sector ────────────────────────────────────
    "finance.is_tax_payer": CanonicalFactDefinition(
        fact_key="finance.is_tax_payer",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["applicant.is_tax_payer", "is_tax_payer", "isTaxPayer"],
        sensitivity="financial",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Individual income tax payer or ITR filer in previous assessment year."
    ),
    "applicant.pays_income_tax": CanonicalFactDefinition(
        fact_key="applicant.pays_income_tax",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["pays_income_tax", "paysIncomeTax"],
        sensitivity="financial",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory tax exclusion clause under PM-KISAN, PMUY, pensions."
    ),
    "household.member_pays_income_tax": CanonicalFactDefinition(
        fact_key="household.member_pays_income_tax",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        sensitivity="financial",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Any family member paying income tax (PMUY exclusion)."
    ),
    "applicant.is_constitutional_post_holder": CanonicalFactDefinition(
        fact_key="applicant.is_constitutional_post_holder",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["is_constitutional_post_holder", "isConstitutionalPostHolder"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Current or former Minister, MP, MLA, Mayor, Zilla Panchayat Chairperson."
    ),
    "applicant.covered_under_epfo_esic_nps": CanonicalFactDefinition(
        fact_key="applicant.covered_under_epfo_esic_nps",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory exclusion from unorganised pensions (PM-SYM) if enrolled in EPFO/ESIC/NPS."
    ),
    "applicant.has_minimum_epf_service_years": CanonicalFactDefinition(
        fact_key="applicant.has_minimum_epf_service_years",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="10 years eligible pensionable service for EPS-95 pension."
    ),
    "finance.is_bank_linked": CanonicalFactDefinition(
        fact_key="finance.is_bank_linked",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["is_bank_linked", "isBankLinked"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Operative Aadhaar-seeded bank account for Direct Benefit Transfer."
    ),
    "applicant.has_savings_bank_account": CanonicalFactDefinition(
        fact_key="applicant.has_savings_bank_account",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["has_savings_bank_account", "hasSavingsAccount"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Active individual savings bank account with auto-debit facility."
    ),
    "applicant.completed_ekyc": CanonicalFactDefinition(
        fact_key="applicant.completed_ekyc",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["completed_ekyc", "completedEkyc"],
        collection_method=CollectionMethod.QUESTION,
        verification_level=VerificationLevel.GOVERNMENT_VERIFIED,
        question_available=True,
        source_semantics="Aadhaar OTP / biometric authentication completed on scheme portal."
    ),
    "finance.has_insurance": CanonicalFactDefinition(
        fact_key="finance.has_insurance",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["has_insurance", "hasInsurance"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Existing life or health insurance policy."
    ),
    "finance.has_pension": CanonicalFactDefinition(
        fact_key="finance.has_pension",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["has_pension", "hasPension"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Enrolled in existing government pension."
    ),
    "household.is_covered_under_other_govt_healthcare": CanonicalFactDefinition(
        fact_key="household.is_covered_under_other_govt_healthcare",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Covered by CGHS, ECHS, or state government employee health scheme."
    ),

    # ── 7. Housing, Sanitations & Utilities ──────────────────────────────────
    "household.owns_pucca_house": CanonicalFactDefinition(
        fact_key="household.owns_pucca_house",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        aliases=["owns_pucca_house", "ownsPuccaHouse"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Family owns an all-weather permanent pucca house (PMAY exclusion)."
    ),
    "household.owns_pucca_house_anywhere_in_india": CanonicalFactDefinition(
        fact_key="household.owns_pucca_house_anywhere_in_india",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Ownership of pucca dwelling anywhere in India by any family member."
    ),
    "household.is_homeless_or_kutcha_house": CanonicalFactDefinition(
        fact_key="household.is_homeless_or_kutcha_house",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        aliases=["is_homeless_or_kutcha_house", "isHomelessOrKutcha"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Residing in makeshift/kutcha dwelling or unhoused (PMAY-G priority)."
    ),
    "household.has_lpg_connection": CanonicalFactDefinition(
        fact_key="household.has_lpg_connection",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        aliases=["has_lpg_connection", "hasLpgConnection"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Existing domestic LPG connection in the name of any household member (PMUY exclusion)."
    ),
    "household.owns_functional_sanitary_latrine": CanonicalFactDefinition(
        fact_key="household.owns_functional_sanitary_latrine",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Household already possesses individual toilet (SBM IHHL exclusion)."
    ),
    "household.has_insanitary_or_no_latrine": CanonicalFactDefinition(
        fact_key="household.has_insanitary_or_no_latrine",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Lack of individual household toilet for Swachh Bharat grant."
    ),

    # ── 8. Agriculture & Allied ──────────────────────────────────────────────
    "occupation.type": CanonicalFactDefinition(
        fact_key="occupation.type",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.ENUM,
        allowed_values=["student", "employed", "farmer", "unemployed", "retired", "artisan", "self_employed", "daily_wage", "all"],
        aliases=["occupation", "applicant.occupation"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Primary livelihood or occupation category."
    ),
    "applicant.is_farmer_family": CanonicalFactDefinition(
        fact_key="applicant.is_farmer_family",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["is_farmer_family", "isFarmerFamily"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Farmer family consisting of husband, wife and minor children owning cultivable land."
    ),
    "applicant.owns_cultivable_land": CanonicalFactDefinition(
        fact_key="applicant.owns_cultivable_land",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["owns_cultivable_land", "ownsCultivableLand"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Legal ownership of cultivable agricultural land holding."
    ),
    "agriculture.has_land": CanonicalFactDefinition(
        fact_key="agriculture.has_land",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["has_land", "hasLand"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Ownership of agricultural land."
    ),
    "agriculture.land_size": CanonicalFactDefinition(
        fact_key="agriculture.land_size",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.FLOAT,
        unit="acres",
        aliases=["land_size", "landSize"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Total landholding size in acres."
    ),
    "applicant.is_institutional_landholder": CanonicalFactDefinition(
        fact_key="applicant.is_institutional_landholder",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["is_institutional_landholder", "isInstitutionalLandholder"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Land held by trust, company, institution (PM-KISAN exclusion)."
    ),
    "applicant.has_received_prior_subsidy_for_same_implement_last_5yr": CanonicalFactDefinition(
        fact_key="applicant.has_received_prior_subsidy_for_same_implement_last_5yr",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Prior subsidy received for same agricultural machinery in last 5 years."
    ),
    "applicant.is_fish_farmer_or_fisher": CanonicalFactDefinition(
        fact_key="applicant.is_fish_farmer_or_fisher",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Active traditional fisher, fish farmer, or aquaculture worker."
    ),
    "applicant.has_requisite_land_or_water_body": CanonicalFactDefinition(
        fact_key="applicant.has_requisite_land_or_water_body",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Ownership or lease of suitable water body for aquaculture."
    ),
    "applicant.has_duplicate_claim_for_same_asset": CanonicalFactDefinition(
        fact_key="applicant.has_duplicate_claim_for_same_asset",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Concurrent claim for same unit under another state/central scheme."
    ),

    # ── 9. Artisans, MSME & Credit ───────────────────────────────────────────
    "artisan.trade_type": CanonicalFactDefinition(
        fact_key="artisan.trade_type",
        subject_scope=SubjectScope.ARTISAN,
        data_type=DataType.ENUM,
        allowed_values=[
            "carpenter", "boat_maker", "armourer", "blacksmith", "hammer_and_tool_maker",
            "locksmith", "sculptor_stone_carver", "goldsmith", "potter", "cobbler",
            "moped_mason", "basket_mat_broom_maker", "doll_and_toy_maker", "barber",
            "garland_maker", "washerman", "tailor", "fishing_net_maker", "other"
        ],
        aliases=["artisan_trade", "artisanTrade"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="One of 18 traditional family-based trades eligible under PM Vishwakarma."
    ),
    "applicant.family_member_already_availed_pm_vishwakarma": CanonicalFactDefinition(
        fact_key="applicant.family_member_already_availed_pm_vishwakarma",
        subject_scope=SubjectScope.FAMILY,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory restriction limiting PM Vishwakarma benefits to 1 member per family."
    ),
    "applicant.has_unpaid_pmegp_mudra_svanidhi_credit_scheme_loan_last_5yr": CanonicalFactDefinition(
        fact_key="applicant.has_unpaid_pmegp_mudra_svanidhi_credit_scheme_loan_last_5yr",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Outstanding credit scheme loan disqualifying new subsidized loan."
    ),
    "applicant.is_non_corporate_small_business": CanonicalFactDefinition(
        fact_key="applicant.is_non_corporate_small_business",
        subject_scope=SubjectScope.ENTERPRISE,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Non-corporate, non-farm small/micro enterprise eligible for Mudra."
    ),
    "enterprise.is_farm_credit": CanonicalFactDefinition(
        fact_key="enterprise.is_farm_credit",
        subject_scope=SubjectScope.ENTERPRISE,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Direct crop agricultural credit excluded from general Mudra loans."
    ),
    "applicant.is_bank_defaulter": CanonicalFactDefinition(
        fact_key="applicant.is_bank_defaulter",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        sensitivity="financial",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="NPA or defaulter record in institutional credit bureaus."
    ),
    "finance.loan_requirement": CanonicalFactDefinition(
        fact_key="finance.loan_requirement",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.ENUM,
        allowed_values=["none", "education", "business", "housing", "agriculture", "emergency"],
        aliases=["loan_requirement", "loanRequirement"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Intent to apply for credit assistance."
    ),

    # ── 10. Education & Students ─────────────────────────────────────────────
    "education.level": CanonicalFactDefinition(
        fact_key="education.level",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.ENUM,
        allowed_values=["illiterate", "primary", "secondary", "higher_secondary", "graduate", "postgraduate", "phd", "all"],
        aliases=["education_level", "educationLevel"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Highest completed educational attainment."
    ),
    "student.class_level": CanonicalFactDefinition(
        fact_key="student.class_level",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.INTEGER,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Current class grade (Class 1 to 12) for school scholarships."
    ),
    "student.enrolled_in_technical_course": CanonicalFactDefinition(
        fact_key="student.enrolled_in_technical_course",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Admission to AICTE-approved Degree/Diploma technical course."
    ),
    "student.enrolled_in_residential_school": CanonicalFactDefinition(
        fact_key="student.enrolled_in_residential_school",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Enrolled in Sainik/Navodaya or government boarding school (NMMSS exclusion)."
    ),
    "student.enrolled_in_distance_education_course": CanonicalFactDefinition(
        fact_key="student.enrolled_in_distance_education_course",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Enrolled via distance/correspondence mode (Single Girl Child scholarship exclusion)."
    ),
    "applicant.received_prior_training_under_govt_scheme": CanonicalFactDefinition(
        fact_key="applicant.received_prior_training_under_govt_scheme",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Prior government skill development training in past 3 years."
    ),
    # ── Controlled Certification Pilot Statutory Facts ───────────────────────
    "household.willing_to_do_unskilled_manual_work": CanonicalFactDefinition(
        fact_key="household.willing_to_do_unskilled_manual_work",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Household adult willing to volunteer for unskilled manual labour under MGNREGA."
    ),
    "applicant.is_farmer": CanonicalFactDefinition(
        fact_key="applicant.is_farmer",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Active cultivator/farmer cultivating agricultural land."
    ),
    "applicant.owns_or_leases_agricultural_land": CanonicalFactDefinition(
        fact_key="applicant.owns_or_leases_agricultural_land",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Ownership or verified tenancy/sharecropping right in agricultural land."
    ),
    "applicant.growing_notified_crop_in_notified_area": CanonicalFactDefinition(
        fact_key="applicant.growing_notified_crop_in_notified_area",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Cultivating a crop notified by State Govt for crop insurance (PMFBY)."
    ),
    "applicant.has_insurable_interest_in_crop": CanonicalFactDefinition(
        fact_key="applicant.has_insurable_interest_in_crop",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Direct insurable financial stake in standing crop."
    ),
    "applicant.is_farmer_or_cultivator": CanonicalFactDefinition(
        fact_key="applicant.is_farmer_or_cultivator",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Farmer, tenant farmer, oral lessee or sharecropper seeking Kisan Credit Card."
    ),
    "household.is_aay_or_priority_household": CanonicalFactDefinition(
        fact_key="household.is_aay_or_priority_household",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Household designated under Antyodaya Anna Yojana (AAY) or Priority Household (PHH) under NFSA."
    ),
    "household.covered_under_ration_card": CanonicalFactDefinition(
        fact_key="household.covered_under_ration_card",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Family possessing valid national/state public distribution ration card."
    ),
    "household.owns_four_wheeler": CanonicalFactDefinition(
        fact_key="household.owns_four_wheeler",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Household owns four-wheeled motorized vehicle (NFSA exclusion)."
    ),
    "beneficiary.is_girl_child": CanonicalFactDefinition(
        fact_key="beneficiary.is_girl_child",
        subject_scope=SubjectScope.BENEFICIARY,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Target beneficiary is a girl child."
    ),
    "beneficiary.age": CanonicalFactDefinition(
        fact_key="beneficiary.age",
        subject_scope=SubjectScope.BENEFICIARY,
        data_type=DataType.INTEGER,
        unit="years",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Age of child beneficiary in completed years."
    ),
    "applicant.is_parent_or_legal_guardian": CanonicalFactDefinition(
        fact_key="applicant.is_parent_or_legal_guardian",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Applicant is biological parent or court-appointed legal guardian."
    ),
    "family.existing_ssy_accounts_count": CanonicalFactDefinition(
        fact_key="family.existing_ssy_accounts_count",
        subject_scope=SubjectScope.FAMILY,
        data_type=DataType.INTEGER,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Number of existing Sukanya Samriddhi accounts already opened in the family."
    ),
    "applicant.is_member_of_women_shg": CanonicalFactDefinition(
        fact_key="applicant.is_member_of_women_shg",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Active member of a recognized Women Self Help Group (DAY-NRLM)."
    ),
    "family.girl_children_count": CanonicalFactDefinition(
        fact_key="family.girl_children_count",
        subject_scope=SubjectScope.FAMILY,
        data_type=DataType.INTEGER,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Total number of girl children in the applicant's family."
    ),
    "student.educational_milestone_completed": CanonicalFactDefinition(
        fact_key="student.educational_milestone_completed",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.ENUM,
        allowed_values=["matriculation", "intermediate", "graduation", "post_graduation", "none"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Highest certified educational qualification milestone completed."
    ),
    "applicant.is_unmarried": CanonicalFactDefinition(
        fact_key="applicant.is_unmarried",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Marital status unmarried/spinster condition for education cash grants."
    ),
    "applicant.is_woman_head_of_family": CanonicalFactDefinition(
        fact_key="applicant.is_woman_head_of_family",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Designated woman head of household in BPL/AAY/APL ration card (Gruha Lakshmi)."
    ),
    "applicant.is_gst_registered_trader": CanonicalFactDefinition(
        fact_key="applicant.is_gst_registered_trader",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Registered taxpayer/merchant under Goods and Services Tax Act."
    ),
    "household.is_swasthya_sathi_enrolled": CanonicalFactDefinition(
        fact_key="household.is_swasthya_sathi_enrolled",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Family enrolled and holding active Swasthya Sathi health smart card (West Bengal)."
    ),
    "applicant.is_regular_government_employee": CanonicalFactDefinition(
        fact_key="applicant.is_regular_government_employee",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Employed in regular, permanent capacity in Central/State Government/PSU."
    ),
    "applicant.has_eligible_participating_account": CanonicalFactDefinition(
        fact_key="applicant.has_eligible_participating_account",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Individual savings account holder of participating commercial bank, RRB, or Post Office (PMJJBY)."
    ),
    "applicant.auto_debit_consent": CanonicalFactDefinition(
        fact_key="applicant.auto_debit_consent",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Executed annual auto-debit consent mandate enabling insurance premium deduction."
    ),
    "applicant.is_accident_victim_or_emergency": CanonicalFactDefinition(
        fact_key="applicant.is_accident_victim_or_emergency",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Individual requiring emergency ambulance, trauma care or disaster relief."
    ),
    "applicant.ration_card_type": CanonicalFactDefinition(
        fact_key="applicant.ration_card_type",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.ENUM,
        allowed_values=["bpl", "aay", "apl", "annapurna", "none", "all"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Public Distribution System (PDS) ration card classification."
    ),
    "applicant.has_pucca_house": CanonicalFactDefinition(
        fact_key="applicant.has_pucca_house",
        subject_scope=SubjectScope.HOUSEHOLD,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Ownership of a permanent concrete/brick pucca dwelling anywhere in India."
    ),
    "student.current_education_level": CanonicalFactDefinition(
        fact_key="student.current_education_level",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.ENUM,
        allowed_values=["primary", "secondary", "higher_secondary", "undergraduate", "postgraduate", "diploma", "iti", "phd", "all"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Current active educational enrollment grade or university level."
    ),
    "enterprise.annual_turnover": CanonicalFactDefinition(
        fact_key="enterprise.annual_turnover",
        subject_scope=SubjectScope.ENTERPRISE,
        data_type=DataType.FLOAT,
        unit="INR",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Annual financial turnover of the business or micro-enterprise."
    ),
    "enterprise.category": CanonicalFactDefinition(
        fact_key="enterprise.category",
        subject_scope=SubjectScope.ENTERPRISE,
        data_type=DataType.ENUM,
        allowed_values=["micro", "small", "medium", "large", "all"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory MSME enterprise classification under MSMED Act."
    ),
    "applicant.has_aadhaar": CanonicalFactDefinition(
        fact_key="applicant.has_aadhaar",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Possession of valid 12-digit Aadhaar identification card."
    ),
    "applicant.has_bank_account": CanonicalFactDefinition(
        fact_key="applicant.has_bank_account",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Active individual bank or post office savings account for DBT disbursement."
    ),

    # ── 11. Statutory Welfare & Labour Board Criteria (Phase 2.3 First-Class Facts) ──
    "student.is_enrolled": CanonicalFactDefinition(
        fact_key="student.is_enrolled",
        subject_scope=SubjectScope.STUDENT,
        data_type=DataType.BOOLEAN,
        aliases=["person.is_student", "applicant.is_student", "is_student", "is_enrolled_student"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Active enrolment as a bona fide regular or part-time student in an accredited educational institution."
    ),
    "applicant.is_registered_bocw_worker": CanonicalFactDefinition(
        fact_key="applicant.is_registered_bocw_worker",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["is_registered_bocw_worker", "is_bocw_worker"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory registration as a construction worker under the Building and Other Construction Workers (BOCW) Act, 1996."
    ),
    "applicant.parent_is_registered_bocw_worker": CanonicalFactDefinition(
        fact_key="applicant.parent_is_registered_bocw_worker",
        subject_scope=SubjectScope.FAMILY,
        data_type=DataType.BOOLEAN,
        aliases=["parent_is_registered_bocw_worker"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Whether either parent of the student applicant is an actively registered BOCW worker eligible for welfare board education assistance."
    ),
    "person.is_widow": CanonicalFactDefinition(
        fact_key="person.is_widow",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["applicant.is_widow", "is_widow"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Statutory widow status of female applicant following demise of spouse for widow pension and survivor schemes."
    ),
    "person.is_widow_or_destitute": CanonicalFactDefinition(
        fact_key="person.is_widow_or_destitute",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["applicant.is_widow_or_destitute", "is_widow_or_destitute"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Classification as a widow, deserted/divorced woman, or destitute person under state social security rules."
    ),
    "applicant.is_destitute": CanonicalFactDefinition(
        fact_key="applicant.is_destitute",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["person.is_destitute", "is_destitute"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Certified destitute or indigent person with no regular source of subsistence or landed property."
    ),
    "applicant.is_head_or_earning_member": CanonicalFactDefinition(
        fact_key="applicant.is_head_or_earning_member",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["is_head_or_earning_member"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Designated head of family or sole earning breadwinner under group insurance schemes such as Aam Aadmi Bima Yojana."
    ),
    "applicant.has_active_education_loan": CanonicalFactDefinition(
        fact_key="applicant.has_active_education_loan",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["has_active_education_loan"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Holding an active sanctioned education loan from a scheduled commercial bank eligible for interest subsidy."
    ),
    "financial.education_loan_amount": CanonicalFactDefinition(
        fact_key="financial.education_loan_amount",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.FLOAT,
        unit="INR",
        aliases=["education_loan_amount"],
        sensitivity="financial",
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Sanctioned principal amount of student education loan."
    ),
    "applicant.owns_cattle": CanonicalFactDefinition(
        fact_key="applicant.owns_cattle",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["scheme.owns_cattle", "owns_cattle", "ownsCattle"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Ownership of cattle, milch cows, buffaloes, or dairy livestock for livestock insurance and dairy development."
    ),
    "applicant.is_registered_worker": CanonicalFactDefinition(
        fact_key="applicant.is_registered_worker",
        subject_scope=SubjectScope.APPLICANT,
        data_type=DataType.BOOLEAN,
        aliases=["scheme.is_registered_worker", "is_registered_worker", "isRegisteredWorker"],
        collection_method=CollectionMethod.QUESTION,
        question_available=True,
        source_semantics="Registration with any statutory unorganised labour welfare board or state social security board."
    )
}


# Synchronize backwards compatibility FACT_CATALOGUE dictionary
FACT_CATALOGUE: Dict[str, FactDefinition] = {
    k: FactDefinition(
        key=v.fact_key,
        type=v.data_type.value,
        sensitivity=v.sensitivity,
        allowed_values=v.allowed_values,
        description=v.source_semantics,
        unit=v.unit,
        collection_method=v.collection_method.value,
        subject_scope=v.subject_scope.value
    )
    for k, v in CANONICAL_FACT_CONTRACT.items()
}

# ── Mapping Legacy / Frontend Keys to Canonical Fact Keys ─────────────────────
LEGACY_KEY_MAP: Dict[str, str] = {
    "age": "person.age",
    "gender": "person.gender",
    "maritalStatus": "person.marital_status",
    "marital_status": "person.marital_status",
    "isWidowOrSenior": "person.is_widow_or_senior",
    "is_widow_or_senior": "person.is_widow_or_senior",
    "isSingleGirlChild": "person.is_single_girl_child",
    "is_single_girl_child": "person.is_single_girl_child",

    "state": "location.state",
    "district": "location.district",
    "urbanRural": "location.urban_rural",
    "urban_rural": "location.urban_rural",
    "areaType": "location.area_type",
    "area_type": "location.area_type",

    "caste": "social.caste",
    "category": "social.caste",
    "isMinority": "social.is_minority",
    "is_minority": "social.is_minority",
    "isBPL": "social.is_bpl",
    "is_bpl": "social.is_bpl",

    "hasDisability": "health.has_disability",
    "has_disability": "health.has_disability",
    "disabilityPct": "health.disability_pct",
    "disability_pct": "health.disability_pct",

    "driving_license": "applicant.has_driving_license",
    "has_driving_license": "applicant.has_driving_license",
    "hasDrivingLicense": "applicant.has_driving_license",
    "commercial_driving_license": "applicant.has_commercial_driving_license",
    "has_commercial_driving_license": "applicant.has_commercial_driving_license",

    "annualIncome": "household.annual_income",
    "annual_income": "household.annual_income",
    "income": "household.annual_income",
    "familyIncome": "household.annual_income",
    "family_income": "household.annual_income",
    "familySize": "household.family_size",
    "family_size": "household.family_size",

    "isTaxPayer": "finance.is_tax_payer",
    "is_tax_payer": "finance.is_tax_payer",
    "isBankLinked": "finance.is_bank_linked",
    "is_bank_linked": "finance.is_bank_linked",
    "hasInsurance": "finance.has_insurance",
    "has_insurance": "finance.has_insurance",
    "hasPension": "finance.has_pension",
    "has_pension": "finance.has_pension",
    "loanRequirement": "finance.loan_requirement",
    "loan_requirement": "finance.loan_requirement",

    "occupation": "occupation.type",
    "applicant.occupation": "occupation.type",
    "applicant.employment_status": "occupation.type",
    "student.is_student": "occupation.type",
    "applicant.social_category": "social.caste",
    "applicant.domicile_state": "location.state",
    "applicant.is_widow": "person.is_widow_or_senior",
    "applicant.disability_status": "health.has_disability",
    "applicant.annual_income": "household.annual_income",
    "farmer.land_area_hectares": "agriculture.land_size",
    "household.ration_card_type": "applicant.ration_card_type",
    "hasLand": "agriculture.has_land",
    "has_land": "agriculture.has_land",
    "landSize": "agriculture.land_size",
    "land_size": "agriculture.land_size",
    "educationLevel": "education.level",
    "education_level": "education.level",

    # Direct mappings for new statutory fields if supplied
    "isFarmerFamily": "applicant.is_farmer_family",
    "is_farmer_family": "applicant.is_farmer_family",
    "ownsCultivableLand": "applicant.owns_cultivable_land",
    "owns_cultivable_land": "applicant.owns_cultivable_land",
    "paysIncomeTax": "applicant.pays_income_tax",
    "pays_income_tax": "applicant.pays_income_tax",
    "hasLpgConnection": "household.has_lpg_connection",
    "has_lpg_connection": "household.has_lpg_connection",
    "ownsPuccaHouse": "household.owns_pucca_house",
    "owns_pucca_house": "household.owns_pucca_house",
    "isHomelessOrKutcha": "household.is_homeless_or_kutcha_house",
    "is_homeless_or_kutcha_house": "household.is_homeless_or_kutcha_house",
    "artisanTrade": "artisan.trade_type",
    "artisan_trade": "artisan.trade_type",
    "completedEkyc": "applicant.completed_ekyc",
    "completed_ekyc": "applicant.completed_ekyc",
    "isConstitutionalPostHolder": "applicant.is_constitutional_post_holder",
    "is_constitutional_post_holder": "applicant.is_constitutional_post_holder",
    "isInstitutionalLandholder": "applicant.is_institutional_landholder",
    "is_institutional_landholder": "applicant.is_institutional_landholder",
    "hasSavingsAccount": "applicant.has_savings_bank_account",
    "has_savings_bank_account": "applicant.has_savings_bank_account",
    "rationCardType": "applicant.ration_card_type",
    "ration_card_type": "applicant.ration_card_type",
    "educationLevel": "student.current_education_level",
    "education_level": "student.current_education_level",
    "hasAadhaar": "applicant.has_aadhaar",
    "has_aadhaar": "applicant.has_aadhaar",
    "hasBankAccount": "applicant.has_bank_account",
    "has_bank_account": "applicant.has_bank_account",
    "applicant.disability_percentage": "health.disability_pct",
    "applicant.is_taxpayer": "applicant.pays_income_tax",
    "farmer.is_farmer": "applicant.is_farmer",
    "occupation.is_farmer": "applicant.is_farmer",
    "occupation.is_student": "student.is_student",
    "student.education_level": "student.current_education_level",
    "household.has_pucca_house": "household.owns_pucca_house",
    "person.caste_category": "social.caste",
    "person.occupation_farmer": "applicant.is_farmer",
    "financial.annual_income": "household.annual_income",
    "applicant.is_indian_citizen": "person.is_citizen_of_india"
}

def normalize_profile_to_facts(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms incoming user inputs (legacy or canonical) into typed,
    validated canonical facts and runs strict deterministic derivations.
    """
    canonical_facts: Dict[str, Any] = {}

    from .resolver import get_canonical_key

    for key, value in raw_dict.items():
        if value is None:
            continue
        mapped_key = LEGACY_KEY_MAP.get(key, key)
        canonical_key = get_canonical_key(mapped_key, CANONICAL_FACT_CONTRACT, LEGACY_KEY_MAP) or mapped_key

        if canonical_key in CANONICAL_FACT_CONTRACT:
            fact_def = CANONICAL_FACT_CONTRACT[canonical_key]
            try:
                canonical_facts[canonical_key] = fact_def.validate_value(value)
            except (ValueError, TypeError):
                continue
        else:
            canonical_facts[canonical_key] = value

    # 1-to-1 canonical identity synchronizations
    if "agriculture.has_land" in canonical_facts and "applicant.owns_cultivable_land" not in canonical_facts:
        canonical_facts["applicant.owns_cultivable_land"] = canonical_facts["agriculture.has_land"]
    elif "applicant.owns_cultivable_land" in canonical_facts and "agriculture.has_land" not in canonical_facts:
        canonical_facts["agriculture.has_land"] = canonical_facts["applicant.owns_cultivable_land"]

    if "finance.is_tax_payer" in canonical_facts and "applicant.pays_income_tax" not in canonical_facts:
        canonical_facts["applicant.pays_income_tax"] = canonical_facts["finance.is_tax_payer"]
    elif "applicant.pays_income_tax" in canonical_facts and "finance.is_tax_payer" not in canonical_facts:
        canonical_facts["finance.is_tax_payer"] = canonical_facts["applicant.pays_income_tax"]

    if "household.annual_income" in canonical_facts and "student.family_annual_income" not in canonical_facts:
        canonical_facts["student.family_annual_income"] = canonical_facts["household.annual_income"]

    if "health.disability_pct" in canonical_facts and "person.disability_percentage" not in canonical_facts:
        canonical_facts["person.disability_percentage"] = canonical_facts["health.disability_pct"]

    if "education.level" in canonical_facts and "student.current_education_level" not in canonical_facts:
        canonical_facts["student.current_education_level"] = canonical_facts["education.level"]
    elif "student.current_education_level" in canonical_facts and "education.level" not in canonical_facts:
        canonical_facts["education.level"] = canonical_facts["student.current_education_level"]

    # Run strict deterministic derivations (dob -> age, thresholds, etc.)
    canonical_facts = apply_deterministic_derivations(canonical_facts)

    return canonical_facts
