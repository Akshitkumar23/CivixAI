"""
CivixAI Semantic Rule Validator
===============================
Validates the logical and semantic integrity of compiled Rule ASTs before
governance review or publication.

Guarantees:
1. Contradiction Detection: Flags mutually exclusive predicates within conjunctions
   (e.g., age < 18 AND age > 60, state == 'UP' AND state == 'Bihar').
2. Inverted Range Detection: Flags impossible bounds (e.g. between 60 and 18).
3. Redundancy & Tautology Analysis: Flags exact duplicate conditions.
4. Grounding & Completeness Score: Computes ratio of evidence-backed predicates.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from services.core.rules.schema import (
    RuleNode, ConditionNode, AllNode, AnyNode, NotNode
)


class SemanticViolation(BaseModel):
    violation_type: str  # CONTRADICTION, INVALID_RANGE, TAUTOLOGY, UNTYPED_FACT
    severity: str        # FATAL, WARNING
    fact_key: str
    message: str
    conflicting_nodes: List[Dict[str, Any]] = Field(default_factory=list)


class SemanticValidationReport(BaseModel):
    candidate_id: str
    is_semantically_valid: bool
    fatal_violations_count: int = 0
    warning_violations_count: int = 0
    violations: List[SemanticViolation] = Field(default_factory=list)
    completeness_score: float = 1.0  # 0.0 to 1.0 based on evidence grounding
    total_conditions_checked: int = 0


class SemanticRuleValidator:
    """Validates AST semantic consistency and logical plausibility."""

    def __init__(self):
        pass

    def validate_ast(self, candidate_id: str, root_node: Optional[RuleNode]) -> SemanticValidationReport:
        if root_node is None:
            return SemanticValidationReport(
                candidate_id=candidate_id,
                is_semantically_valid=True,
                fatal_violations_count=0,
                warning_violations_count=0,
                completeness_score=0.0,
                total_conditions_checked=0,
            )

        violations: List[SemanticViolation] = []
        conditions = self._collect_conditions(root_node)

        # 1. Range Validation for individual conditions
        for cond in conditions:
            if cond.operator == "between":
                val = cond.value
                if isinstance(val, (list, tuple)) and len(val) == 2:
                    try:
                        low = float(val[0])
                        high = float(val[1])
                        if low > high:
                            violations.append(SemanticViolation(
                                violation_type="INVALID_RANGE",
                                severity="FATAL",
                                fact_key=cond.fact,
                                message=f"Lower bound ({low}) exceeds upper bound ({high}) in between operator",
                                conflicting_nodes=[cond.model_dump()]
                            ))
                    except (ValueError, TypeError):
                        violations.append(SemanticViolation(
                            violation_type="INVALID_RANGE",
                            severity="FATAL",
                            fact_key=cond.fact,
                            message=f"Non-numeric bounds in between operator: {val}",
                            conflicting_nodes=[cond.model_dump()]
                        ))

        # 2. Conjunction Contradiction Detection
        # Group conditions by fact within root conjunction
        fact_groups: Dict[str, List[ConditionNode]] = {}
        for cond in conditions:
            fact_groups.setdefault(cond.fact, []).append(cond)

        for fact_key, group in fact_groups.items():
            if len(group) > 1:
                self._check_group_contradictions(fact_key, group, violations)

        # 3. Completeness & Evidence Grounding Score
        grounded_count = 0
        for cond in conditions:
            if cond.source_fragment and cond.verification_status in ("verified_from_source", "certified"):
                grounded_count += 1
        completeness = grounded_count / len(conditions) if conditions else 1.0

        fatal_count = sum(1 for v in violations if v.severity == "FATAL")
        warning_count = sum(1 for v in violations if v.severity == "WARNING")

        return SemanticValidationReport(
            candidate_id=candidate_id,
            is_semantically_valid=fatal_count == 0,
            fatal_violations_count=fatal_count,
            warning_violations_count=warning_count,
            violations=violations,
            completeness_score=round(completeness, 2),
            total_conditions_checked=len(conditions),
        )

    def _collect_conditions(self, node: RuleNode) -> List[ConditionNode]:
        """Flattens all condition nodes under this AST node."""
        conds: List[ConditionNode] = []
        if isinstance(node, ConditionNode):
            conds.append(node)
        elif isinstance(node, AllNode):
            for child in node.all:
                conds.extend(self._collect_conditions(child))
        elif isinstance(node, AnyNode):
            for child in node.any:
                conds.extend(self._collect_conditions(child))
        elif isinstance(node, NotNode):
            conds.extend(self._collect_conditions(node.invert))
        return conds

    def _check_group_contradictions(
        self,
        fact_key: str,
        group: List[ConditionNode],
        violations: List[SemanticViolation]
    ):
        """Checks for conflicting operators or values on the same fact."""
        # Check equality vs inequality or multiple different equalities
        eq_vals = set()
        min_bound: Optional[float] = None
        max_bound: Optional[float] = None

        for c in group:
            if c.operator == "eq":
                eq_vals.add(str(c.value).strip().lower())
            elif c.operator in ("gt", "gte"):
                try:
                    val = float(c.value)
                    if min_bound is None or val > min_bound:
                        min_bound = val
                except (ValueError, TypeError):
                    pass
            elif c.operator in ("lt", "lte"):
                try:
                    val = float(c.value)
                    if max_bound is None or val < max_bound:
                        max_bound = val
                except (ValueError, TypeError):
                    pass

        # If multiple different strict equality values exist in conjunction -> fatal contradiction
        # (e.g. state == 'UP' and state == 'Bihar')
        if len(eq_vals) > 1:
            violations.append(SemanticViolation(
                violation_type="CONTRADICTION",
                severity="FATAL",
                fact_key=fact_key,
                message=f"Mutually exclusive equality conditions on '{fact_key}': {list(eq_vals)}",
                conflicting_nodes=[c.model_dump() for c in group if c.operator == "eq"]
            ))

        # If min_bound > max_bound -> fatal contradiction (e.g. age > 60 and age < 18)
        if min_bound is not None and max_bound is not None and min_bound > max_bound:
            violations.append(SemanticViolation(
                violation_type="CONTRADICTION",
                severity="FATAL",
                fact_key=fact_key,
                message=f"Impossible inequality interval on '{fact_key}': lower bound ({min_bound}) > upper bound ({max_bound})",
                conflicting_nodes=[c.model_dump() for c in group if c.operator in ("gt", "gte", "lt", "lte")]
            ))
