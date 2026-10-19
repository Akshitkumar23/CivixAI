"""
CivixAI Rule Versioning & Semantic Diff Engine
=============================================
Computes semantic AST deltas and material changes across scheme versions when
official government gazettes or source criteria are updated.

Change Categories:
- ELIGIBILITY_EXPANDED: E.g., income ceiling increased, age bracket widened.
- ELIGIBILITY_RESTRICTED: E.g., new mandatory condition added, tighter bounds.
- BENEFIT_CHANGED: E.g., grant amount adjusted, installments modified.
- ROUTE_CHANGED: E.g., official portal URL migrated or application method changed.
- NO_MATERIAL_CHANGE: Text-only editorial changes.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.core.discovery.governance import ProgramVersionRecord


class SemanticChangeType(str, Enum):
    ELIGIBILITY_EXPANDED = "ELIGIBILITY_EXPANDED"
    ELIGIBILITY_RESTRICTED = "ELIGIBILITY_RESTRICTED"
    BENEFIT_CHANGED = "BENEFIT_CHANGED"
    ROUTE_CHANGED = "ROUTE_CHANGED"
    NO_MATERIAL_CHANGE = "NO_MATERIAL_CHANGE"


class VersionDiffReport(BaseModel):
    program_id: str
    old_version_number: int
    new_version_number: int
    primary_change_type: SemanticChangeType
    requires_human_re_review: bool
    added_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    removed_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    modified_bounds: List[Dict[str, Any]] = Field(default_factory=list)
    benefit_delta: Optional[str] = None
    route_delta: Optional[str] = None
    audit_notes: str = ""


class RuleSemanticDiffEngine:
    """Computes statutory diffs between scheme versions."""

    def __init__(self):
        pass

    def compare_versions(
        self,
        old_version: ProgramVersionRecord,
        new_version: ProgramVersionRecord
    ) -> VersionDiffReport:
        old_rules = old_version.eligibility_rules or {}
        new_rules = new_version.eligibility_rules or {}

        old_conds = self._extract_conditions(old_rules)
        new_conds = self._extract_conditions(new_rules)

        old_map = {c.get("fact") or c.get("fact_key"): c for c in old_conds if (c.get("fact") or c.get("fact_key"))}
        new_map = {c.get("fact") or c.get("fact_key"): c for c in new_conds if (c.get("fact") or c.get("fact_key"))}

        added = [c for k, c in new_map.items() if k not in old_map]
        removed = [c for k, c in old_map.items() if k not in new_map]
        modified = []

        is_restricted = False
        is_expanded = False

        # Condition added is generally a restriction
        if added:
            is_restricted = True

        # Condition removed is generally an expansion
        if removed:
            is_expanded = True

        # Compare existing common conditions
        for k in old_map:
            if k in new_map:
                o_c = old_map[k]
                n_c = new_map[k]
                o_val = o_c.get("value")
                n_val = n_c.get("value")
                o_op = o_c.get("operator")
                n_op = n_c.get("operator")

                if o_val != n_val or o_op != n_op:
                    mod_entry = {
                        "fact": k,
                        "old_operator": o_op,
                        "old_value": o_val,
                        "new_operator": n_op,
                        "new_value": n_val,
                    }
                    modified.append(mod_entry)

                    # Assess direction
                    if o_op in ("lte", "lt") and isinstance(o_val, (int, float)) and isinstance(n_val, (int, float)):
                        if n_val > o_val:
                            is_expanded = True
                        else:
                            is_restricted = True
                    elif o_op in ("gte", "gt") and isinstance(o_val, (int, float)) and isinstance(n_val, (int, float)):
                        if n_val < o_val:
                            is_expanded = True
                        else:
                            is_restricted = True

        # Compare Benefits
        old_ben = old_version.benefit_facts or {}
        new_ben = new_version.benefit_facts or {}
        benefit_delta = None
        if old_ben != new_ben:
            benefit_delta = f"Benefit updated from '{str(old_ben)[:80]}' to '{str(new_ben)[:80]}'"

        # Compare Routes
        old_route = old_version.application_facts or {}
        new_route = new_version.application_facts or {}
        route_delta = None
        if old_route != new_route:
            route_delta = f"Application route updated from '{str(old_route)[:80]}' to '{str(new_route)[:80]}'"

        # Classify Primary Change Type
        if is_restricted:
            change_type = SemanticChangeType.ELIGIBILITY_RESTRICTED
        elif is_expanded:
            change_type = SemanticChangeType.ELIGIBILITY_EXPANDED
        elif benefit_delta:
            change_type = SemanticChangeType.BENEFIT_CHANGED
        elif route_delta:
            change_type = SemanticChangeType.ROUTE_CHANGED
        else:
            change_type = SemanticChangeType.NO_MATERIAL_CHANGE

        requires_review = (change_type != SemanticChangeType.NO_MATERIAL_CHANGE)

        return VersionDiffReport(
            program_id=new_version.program_id,
            old_version_number=old_version.version_number,
            new_version_number=new_version.version_number,
            primary_change_type=change_type,
            requires_human_re_review=requires_review,
            added_conditions=added,
            removed_conditions=removed,
            modified_bounds=modified,
            benefit_delta=benefit_delta,
            route_delta=route_delta,
            audit_notes=f"Calculated statutory diff: {change_type.value}. Human re-review required: {requires_review}.",
        )

    def _extract_conditions(self, rules: Any) -> List[Dict[str, Any]]:
        conds: List[Dict[str, Any]] = []
        if isinstance(rules, list):
            for r in rules:
                if isinstance(r, dict):
                    conds.append(r)
        elif isinstance(rules, dict):
            if "conditions" in rules and isinstance(rules["conditions"], list):
                conds.extend(rules["conditions"])
            elif "all" in rules and isinstance(rules["all"], list):
                conds.extend(self._extract_conditions(rules["all"]))
            elif "any" in rules and isinstance(rules["any"], list):
                conds.extend(self._extract_conditions(rules["any"]))
            elif "fact" in rules or "fact_key" in rules:
                conds.append(rules)
        return conds
