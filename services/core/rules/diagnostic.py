"""
Generic Fact-Resolution & Eligibility Diagnostic Tool
CivixAI Core Governance / Developer Tool

Zero scheme-specific logic. Operates purely on candidate_id and canonical AST facts.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session

from services.core.facts.registry import CANONICAL_FACT_CONTRACT, normalize_profile_to_facts, LEGACY_KEY_MAP
from services.core.rules.engine import EligibilityEngine
from services.core.rules.schema import (
    RuleNode, ConditionNode, AllNode, AnyNode, NotNode, SchemeEvaluationSummary
)


def _extract_ast_fact_keys(node: Any) -> Set[str]:
    """Recursively extracts all required fact keys from an AST node or raw dict."""
    facts: Set[str] = set()
    if not node:
        return facts

    if isinstance(node, dict):
        if "fact" in node and node["fact"]:
            facts.add(str(node["fact"]))
        if "all" in node and isinstance(node["all"], list):
            for child in node["all"]:
                facts.update(_extract_ast_fact_keys(child))
        if "any" in node and isinstance(node["any"], list):
            for child in node["any"]:
                facts.update(_extract_ast_fact_keys(child))
        if "not" in node:
            facts.update(_extract_ast_fact_keys(node["not"]))
        if "invert" in node:
            facts.update(_extract_ast_fact_keys(node["invert"]))
    elif isinstance(node, ConditionNode):
        if node.fact:
            facts.add(node.fact)
    elif isinstance(node, AllNode):
        for child in node.all:
            facts.update(_extract_ast_fact_keys(child))
    elif isinstance(node, AnyNode):
        for child in node.any:
            facts.update(_extract_ast_fact_keys(child))
    elif isinstance(node, NotNode):
        facts.update(_extract_ast_fact_keys(node.invert))

    return facts


def diagnose_candidate(
    candidate_id: str,
    facts: Dict[str, Any],
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Generic, scheme-agnostic diagnostic inspector.
    Evaluates candidate AST rules against profile facts and returns
    full transparency on fact resolution, AST requirements, and deterministic verdicts.
    """
    fact_resolution_errors: List[Dict[str, Any]] = []

    # 1. Track profile source mappings
    raw_keys_by_canonical: Dict[str, str] = {}
    for raw_k, raw_v in facts.items():
        mapped_k = LEGACY_KEY_MAP.get(raw_k, raw_k)
        raw_keys_by_canonical[mapped_k] = raw_k

        # Validate against contract if present
        if mapped_k in CANONICAL_FACT_CONTRACT and raw_v is not None:
            fact_def = CANONICAL_FACT_CONTRACT[mapped_k]
            try:
                fact_def.validate_value(raw_v)
            except Exception as e:
                fact_resolution_errors.append({
                    "raw_key": raw_k,
                    "canonical_key": mapped_k,
                    "raw_value": raw_v,
                    "error": str(e)
                })

    # 2. Normalize and apply deterministic derivations
    resolved_facts_map = normalize_profile_to_facts(facts)

    # 3. Format resolved facts list
    resolved_facts: List[Dict[str, Any]] = []
    for k, v in resolved_facts_map.items():
        profile_src = raw_keys_by_canonical.get(k, "deterministic_derivation")
        if v is True:
            state = "TRUE"
        elif v is False:
            state = "FALSE"
        elif v is None:
            state = "UNKNOWN"
        else:
            state = "TRUE"  # Known non-null value

        resolved_facts.append({
            "canonical_fact": k,
            "profile_source": profile_src,
            "value": v,
            "state": state
        })

    # 4. Extract candidate AST facts from DB rules if DB is available
    ast_facts_set: Set[str] = set()
    evaluation_result: Dict[str, Any] = {}
    final_status = "UNKNOWN"

    if db is not None:
        from services.core.database.models import Scheme, SchemeVersion

        scheme = db.query(Scheme).filter(Scheme.id == candidate_id).first()
        if scheme:
            version = db.query(SchemeVersion).filter_by(
                scheme_id=candidate_id,
                status="published"
            ).order_by(SchemeVersion.version_number.desc()).first()

            if not version:
                version = db.query(SchemeVersion).filter_by(
                    scheme_id=candidate_id
                ).order_by(SchemeVersion.version_number.desc()).first()

            if version:
                for r in version.rules:
                    expr = getattr(r, "rule_expression", None)
                    if expr:
                        try:
                            parsed_ast = json.loads(expr) if isinstance(expr, str) else expr
                            ast_facts_set.update(_extract_ast_fact_keys(parsed_ast))
                        except Exception:
                            pass
                    else:
                        fact_k = getattr(r, "fact_key", None)
                        if fact_k:
                            ast_facts_set.add(fact_k)

            # Run engine evaluation
            engine = EligibilityEngine(db)
            summary: SchemeEvaluationSummary = engine.evaluate_scheme(candidate_id, resolved_facts_map)
            final_status = summary.status
            evaluation_result = {
                "status": summary.status,
                "confidence_score": summary.confidence_score,
                "matched_rules": summary.matched_rules,
                "failed_rules": summary.failed_rules,
                "missing_facts": summary.missing_facts,
                "reasons": summary.reasons,
                "deterministic_result": summary.deterministic_result,
                "authority_level": summary.authority_level
            }
        else:
            final_status = "NOT_FOUND"
            fact_resolution_errors.append({
                "candidate_id": candidate_id,
                "error": f"Candidate scheme {candidate_id} not found in database"
            })

    ast_facts = sorted(list(ast_facts_set))
    unresolved_facts = sorted([f for f in ast_facts if resolved_facts_map.get(f) is None])

    return {
        "candidate_id": candidate_id,
        "resolved_facts": resolved_facts,
        "ast_facts": ast_facts,
        "unresolved_facts": unresolved_facts,
        "fact_resolution_errors": fact_resolution_errors,
        "rule_evaluation": evaluation_result,
        "final_status": final_status
    }
