from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime, date

@dataclass(frozen=True)
class DeterministicDerivationRule:
    rule_id: str
    source_facts: List[str]
    target_fact: str
    transform: Callable[[Dict[str, Any]], Optional[Any]]
    description: str
    semantic_basis: str = "canonical_contract"

# Canonical State Name Normalizer for India's 28 States + 8 UTs
STATE_CANONICAL_MAP: Dict[str, str] = {
    "andhra pradesh": "Andhra Pradesh", "ap": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh", "ar": "Arunachal Pradesh",
    "assam": "Assam", "as": "Assam",
    "bihar": "Bihar", "br": "Bihar",
    "chhattisgarh": "Chhattisgarh", "cg": "Chhattisgarh", "chattisgarh": "Chhattisgarh",
    "goa": "Goa", "ga": "Goa",
    "gujarat": "Gujarat", "gj": "Gujarat",
    "haryana": "Haryana", "hr": "Haryana",
    "himachal pradesh": "Himachal Pradesh", "hp": "Himachal Pradesh",
    "jharkhand": "Jharkhand", "jh": "Jharkhand",
    "karnataka": "Karnataka", "ka": "Karnataka",
    "kerala": "Kerala", "kl": "Kerala",
    "madhya pradesh": "Madhya Pradesh", "mp": "Madhya Pradesh",
    "maharashtra": "Maharashtra", "mh": "Maharashtra",
    "manipur": "Manipur", "mn": "Manipur",
    "meghalaya": "Meghalaya", "ml": "Meghalaya",
    "mizoram": "Mizoram", "mz": "Mizoram",
    "nagaland": "Nagaland", "nl": "Nagaland",
    "odisha": "Odisha", "orissa": "Odisha", "or": "Odisha", "od": "Odisha",
    "punjab": "Punjab", "pb": "Punjab",
    "rajasthan": "Rajasthan", "rj": "Rajasthan",
    "sikkim": "Sikkim", "sk": "Sikkim",
    "tamil nadu": "Tamil Nadu", "tn": "Tamil Nadu", "tamilnadu": "Tamil Nadu",
    "telangana": "Telangana", "ts": "Telangana", "tg": "Telangana",
    "tripura": "Tripura", "tr": "Tripura",
    "uttar pradesh": "Uttar Pradesh", "up": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand", "uk": "Uttarakhand", "ua": "Uttarakhand",
    "west bengal": "West Bengal", "wb": "West Bengal",
    "andaman and nicobar islands": "Andaman and Nicobar Islands", "an": "Andaman and Nicobar Islands",
    "chandigarh": "Chandigarh", "ch": "Chandigarh",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi", "nct of delhi": "Delhi", "dl": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir", "j&k": "Jammu and Kashmir", "jk": "Jammu and Kashmir",
    "ladakh": "Ladakh", "la": "Ladakh",
    "lakshadweep": "Lakshadweep", "ld": "Lakshadweep",
    "puducherry": "Puducherry", "pondicherry": "Puducherry", "py": "Puducherry"
}

def derive_age_from_dob(facts: Dict[str, Any]) -> Optional[int]:
    dob_str = facts.get("person.date_of_birth")
    if not dob_str:
        return None
    try:
        # support YYYY-MM-DD
        dt = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    except Exception:
        return None

def derive_canonical_state(facts: Dict[str, Any]) -> Optional[str]:
    raw_state = facts.get("location.state")
    if not raw_state:
        return None
    cleaned = str(raw_state).strip().lower()
    return STATE_CANONICAL_MAP.get(cleaned, str(raw_state).strip())

# Strict Deterministic Registry — Only Pure Mathematical & Canonical Transformations
DETERMINISTIC_DERIVATION_RULES: List[DeterministicDerivationRule] = [
    DeterministicDerivationRule(
        rule_id="derive_age_from_dob",
        source_facts=["person.date_of_birth"],
        target_fact="person.age",
        transform=derive_age_from_dob,
        description="Calculates completed years of age from ISO date of birth.",
        semantic_basis="mathematical_date_arithmetic"
    ),
    DeterministicDerivationRule(
        rule_id="derive_canonical_state",
        source_facts=["location.state"],
        target_fact="location.state",
        transform=derive_canonical_state,
        description="Canonicalizes state string across official State/UT nomenclature.",
        semantic_basis="lexical_canonicalization"
    ),
    DeterministicDerivationRule(
        rule_id="derive_minority_community_exclusion",
        source_facts=["social.is_minority"],
        target_fact="applicant.not_belonging_to_minority_community",
        transform=lambda facts: (not bool(facts.get("social.is_minority", facts.get("social.is_minority_community")))) if (facts.get("social.is_minority") is not None or facts.get("social.is_minority_community") is not None) else None,
        description="Inversion of explicitly confirmed is_minority status.",
        semantic_basis="logical_boolean_negation"
    ),
    DeterministicDerivationRule(
        rule_id="derive_minority_community_alias",
        source_facts=["social.is_minority_community"],
        target_fact="social.is_minority",
        transform=lambda facts: bool(facts.get("social.is_minority_community")) if facts.get("social.is_minority_community") is not None else None,
        description="Canonical alias mapping from social.is_minority_community to social.is_minority.",
        semantic_basis="canonical_contract_alias"
    ),
]

DERIVATION_REGISTRY: Dict[str, DeterministicDerivationRule] = {
    r.rule_id: r for r in DETERMINISTIC_DERIVATION_RULES
}

def apply_deterministic_derivations(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies only deterministic, logically sound derivations.
    Guarantees:
    - Never defaults unknown facts to false or true.
    - Never makes loose sociological inferences.
    - Preserves all incoming facts.
    - Multi-pass fixed-point evaluation for chained derivations (up to 3 passes).
    """
    enriched = dict(facts)

    for _ in range(3):
        added_any = False
        for rule in DETERMINISTIC_DERIVATION_RULES:
            if rule.target_fact in enriched and enriched[rule.target_fact] is not None:
                if rule.target_fact in rule.source_facts:
                    # In-place canonicalizer (e.g. state string normalization)
                    canonicalized = rule.transform(enriched)
                    if canonicalized is not None and canonicalized != enriched[rule.target_fact]:
                        enriched[rule.target_fact] = canonicalized
                        added_any = True
                continue

            if all(sf in enriched and enriched[sf] is not None for sf in rule.source_facts):
                derived_val = rule.transform(enriched)
                if derived_val is not None:
                    enriched[rule.target_fact] = derived_val
                    added_any = True
        if not added_any:
            break

    return enriched

def get_dependent_derived_facts(fact_key: str, visited: Optional[Set[str]] = None) -> Set[str]:
    """Returns all target facts that depend on fact_key as a source fact, recursively."""
    if visited is None:
        visited = set()
    if fact_key in visited:
        return set()
    visited.add(fact_key)

    dependent: Set[str] = set()
    for rule in DETERMINISTIC_DERIVATION_RULES:
        if fact_key in rule.source_facts:
            dependent.add(rule.target_fact)
            dependent.update(get_dependent_derived_facts(rule.target_fact, visited))
    return dependent
