from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .contract import CanonicalFactDefinition


@dataclass(frozen=True)
class FactResolution:
    """
    Result of resolving a Rule AST or queried fact representation against
    the available user profile / canonical facts.
    """
    rule_fact: str
    canonical_key: Optional[str]
    value: Any
    resolution_source: str  # DIRECT, SCHEMA_CANONICAL, SCHEMA_ALIAS, LEGACY_MAPPING, NESTED_PATH, CONFLICT, TYPE_MISMATCH, UNRESOLVED
    status: str             # RESOLVED, UNRESOLVED, CONFLICT, TYPE_MISMATCH
    is_resolved: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_fact": self.rule_fact,
            "canonical_lookup": self.canonical_key,
            "resolved_value": self.value,
            "resolution_source": self.resolution_source,
            "status": self.status,
            "is_resolved": self.is_resolved
        }


def _lookup_in_facts(facts: Dict[str, Any], key: str) -> Tuple[bool, Any]:
    """
    Looks up key in facts either as a direct dictionary key or
    by traversing nested dot-separated paths (e.g. person.age in {"person": {"age": 32}}).
    """
    if key in facts:
        return True, facts[key]

    if "." in key:
        parts = key.split(".")
        curr: Any = facts
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return False, None
        return True, curr

    return False, None


def get_canonical_key(
    fact_key: str,
    contract: Optional[Dict[str, CanonicalFactDefinition]] = None,
    legacy_map: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Deterministically resolves any valid representation (canonical, alias, legacy)
    to its canonical fact key declared centrally in the schema.
    """
    if not fact_key:
        return None

    if contract is None:
        from .registry import CANONICAL_FACT_CONTRACT
        contract = CANONICAL_FACT_CONTRACT

    if legacy_map is None:
        from .registry import LEGACY_KEY_MAP
        legacy_map = LEGACY_KEY_MAP

    # 1. Direct canonical match
    if fact_key in contract:
        return fact_key

    # 2. Check declared aliases across all canonical fact definitions
    for canon_k, fact_def in contract.items():
        if fact_key in fact_def.aliases:
            return canon_k

    # 3. Check legacy key map
    if fact_key in legacy_map:
        target = legacy_map[fact_key]
        if target in contract:
            return target
        # Recurse once if target points to an alias
        rec = get_canonical_key(target, contract, legacy_map)
        if rec:
            return rec
        return target

    return None


def get_equivalent_representations(
    fact_key: str,
    contract: Optional[Dict[str, CanonicalFactDefinition]] = None,
    legacy_map: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    Returns an ordered, deduplicated list of all equivalent valid representations
    for a given fact key according to the central schema.
    """
    if contract is None:
        from .registry import CANONICAL_FACT_CONTRACT
        contract = CANONICAL_FACT_CONTRACT

    if legacy_map is None:
        from .registry import LEGACY_KEY_MAP
        legacy_map = LEGACY_KEY_MAP

    canonical = get_canonical_key(fact_key, contract, legacy_map) or fact_key

    reps: List[str] = [fact_key]
    if canonical != fact_key:
        reps.append(canonical)

    if canonical in contract:
        for alias in contract[canonical].aliases:
            if alias not in reps:
                reps.append(alias)

    for k, v in legacy_map.items():
        if v == canonical or v == fact_key:
            if k not in reps:
                reps.append(k)

    return reps


def are_values_consistent(val1: Any, val2: Any) -> bool:
    """
    Checks if two candidate values for the same canonical fact are semantically equal.
    Prevents silent ambiguity or conflict between multiple supplied representations.
    """
    if val1 == val2:
        return True

    # Boolean strictness
    if isinstance(val1, bool) or isinstance(val2, bool):
        return isinstance(val1, bool) and isinstance(val2, bool) and val1 is val2

    # Numeric equivalence (e.g. 50000 == 50000.0)
    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        try:
            return float(val1) == float(val2)
        except Exception:
            return False

    # String / enum case-insensitive equivalence
    if isinstance(val1, str) and isinstance(val2, str):
        return val1.strip().lower() == val2.strip().lower()

    return False


def resolve_fact(
    rule_fact: str,
    facts: Dict[str, Any],
    contract: Optional[Dict[str, CanonicalFactDefinition]] = None,
    legacy_map: Optional[Dict[str, str]] = None
) -> FactResolution:
    """
    Centrally resolves a Rule AST fact key against the user's provided profile facts.

    Guarantees:
    - Scheme-agnostic: Operates purely on declared schema definitions and metadata.
    - Deterministic: Explicit mappings only. No fuzzy or substring matching.
    - Tri-State Preserving: Never coerces UNKNOWN to FALSE or TRUE.
    - Conflict-Safe: Detects conflicting values across multiple supplied representations.
    - Type-Safe: Type-validates values against the canonical contract.
    """
    if not rule_fact or not isinstance(rule_fact, str) or rule_fact.strip() == "":
        return FactResolution(
            rule_fact=str(rule_fact),
            canonical_key=None,
            value=None,
            resolution_source="UNRESOLVED",
            status="UNRESOLVED",
            is_resolved=False
        )

    clean_fact = rule_fact.strip()

    if contract is None:
        from .registry import CANONICAL_FACT_CONTRACT
        contract = CANONICAL_FACT_CONTRACT

    if legacy_map is None:
        from .registry import LEGACY_KEY_MAP
        legacy_map = LEGACY_KEY_MAP

    canonical_key = get_canonical_key(clean_fact, contract, legacy_map)
    equivalent_reps = get_equivalent_representations(clean_fact, contract, legacy_map)

    # Search for all present representations in provided facts
    candidates: List[Tuple[str, Any]] = []
    for rep in equivalent_reps:
        found, val = _lookup_in_facts(facts, rep)
        if found and val is not None:
            # Check for empty string on non-string facts
            candidates.append((rep, val))

    if not candidates:
        return FactResolution(
            rule_fact=clean_fact,
            canonical_key=canonical_key,
            value=None,
            resolution_source="UNRESOLVED",
            status="UNRESOLVED",
            is_resolved=False
        )

    # Check for value conflicts across multiple representations
    first_rep, first_val = candidates[0]
    for other_rep, other_val in candidates[1:]:
        if not are_values_consistent(first_val, other_val):
            return FactResolution(
                rule_fact=clean_fact,
                canonical_key=canonical_key,
                value=None,
                resolution_source="CONFLICT",
                status="CONFLICT",
                is_resolved=False
            )

    # Type validate against the canonical definition
    target_def_key = canonical_key or clean_fact
    fact_def = contract.get(target_def_key) if contract else None

    validated_val = first_val
    if fact_def is not None:
        try:
            validated_val = fact_def.validate_value(first_val)
        except (ValueError, TypeError):
            return FactResolution(
                rule_fact=clean_fact,
                canonical_key=canonical_key,
                value=None,
                resolution_source="TYPE_MISMATCH",
                status="TYPE_MISMATCH",
                is_resolved=False
            )

    # Determine resolution source for transparent lineage
    if first_rep == clean_fact:
        if "." in clean_fact and clean_fact not in facts:
            source = "NESTED_PATH"
        else:
            source = "DIRECT"
    elif first_rep == canonical_key:
        source = "SCHEMA_CANONICAL"
    elif canonical_key and fact_def and first_rep in getattr(fact_def, "aliases", []):
        source = "SCHEMA_ALIAS"
    elif legacy_map and (first_rep in legacy_map or clean_fact in legacy_map):
        source = "LEGACY_MAPPING"
    else:
        source = "SCHEMA_MAPPING"

    return FactResolution(
        rule_fact=clean_fact,
        canonical_key=canonical_key or first_rep,
        value=validated_val,
        resolution_source=source,
        status="RESOLVED",
        is_resolved=True
    )
