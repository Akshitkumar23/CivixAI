"""
Deterministic Statutory Eligibility Engine
Phase 1/2 Core Architecture: Evaluates statutory eligibility rules deterministically.
Guarantees zero LLM hallucinations in legal eligibility decisions.
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session

from .schema import (
    ConditionNode, RuleEvaluationResult, SchemeEvaluationSummary,
    EvidenceCitation, RuleNode
)
from .evaluator import evaluate_condition, evaluate_rule_node
from .trace import build_scheme_evaluation


class EligibilityEngine:
    """
    Deterministic rule evaluation engine for CivixAI.
    Directly evaluates statutory scheme rules against citizen profile facts,
    producing verified 4-state verdicts (ELIGIBLE, NEEDS_INFO, NEEDS_VERIFICATION, NOT_ELIGIBLE).
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def evaluate_condition_node(
        self,
        condition: ConditionNode,
        facts: Dict[str, Any]
    ) -> RuleEvaluationResult:
        """Evaluates a single leaf ConditionNode."""
        return evaluate_condition(condition, facts)

    def evaluate_ast_node(
        self,
        node: Union[RuleNode, Dict[str, Any]],
        facts: Dict[str, Any]
    ) -> RuleEvaluationResult:
        """Evaluates a nested AST rule node."""
        return evaluate_rule_node(node, facts)

    def evaluate_rules_list(
        self,
        rules: List[Any],
        facts: Dict[str, Any],
        scheme_id: str = "scheme",
        evidence: Optional[List[EvidenceCitation]] = None
    ) -> SchemeEvaluationSummary:
        """
        Evaluates a list of rule records or ConditionNodes against user facts.
        """
        now_utc = datetime.now(timezone.utc)
        eval_results: List[RuleEvaluationResult] = []

        for r in rules:
            if isinstance(r, (ConditionNode, RuleEvaluationResult)):
                if isinstance(r, ConditionNode):
                    eval_results.append(evaluate_condition(r, facts))
                else:
                    eval_results.append(r)
                continue

            # Check effective dates if present
            r_from = getattr(r, "effective_from", None)
            r_to = getattr(r, "effective_to", None)
            if r_from:
                dt_from = r_from.replace(tzinfo=timezone.utc) if r_from.tzinfo is None else r_from
                if dt_from > now_utc:
                    continue
            if r_to:
                dt_to = r_to.replace(tzinfo=timezone.utc) if r_to.tzinfo is None else r_to
                if dt_to < now_utc:
                    continue

            # Check if rule has AST expression
            rule_expr = getattr(r, "rule_expression", None)
            if rule_expr:
                try:
                    parsed_ast = json.loads(rule_expr) if isinstance(rule_expr, str) else rule_expr
                    res = evaluate_rule_node(parsed_ast, facts)
                    eval_results.append(res)
                    continue
                except Exception:
                    pass

            # Flat condition fallback
            fact_key = getattr(r, "fact_key", None) or (r.get("fact_key", "") if isinstance(r, dict) else "")
            operator = getattr(r, "operator", None) or (r.get("operator", "eq") if isinstance(r, dict) else "eq")
            raw_val = getattr(r, "expected_value", None) or (r.get("expected_value", "") if isinstance(r, dict) else "")
            mandatory = getattr(r, "mandatory", True) if hasattr(r, "mandatory") else (r.get("mandatory", True) if isinstance(r, dict) else True)
            reason_code = getattr(r, "reason_code", None) or (r.get("reason_code", "STATUTORY_RULE") if isinstance(r, dict) else "STATUTORY_RULE")
            verification_status = getattr(r, "verification_status", "imported_unverified") if hasattr(r, "verification_status") else (r.get("verification_status", "imported_unverified") if isinstance(r, dict) else "imported_unverified")
            source_fragment = getattr(r, "source_fragment", None) or (r.get("source_fragment") if isinstance(r, dict) else None)

            parsed_val = raw_val
            if isinstance(raw_val, str):
                if raw_val.startswith("[") and raw_val.endswith("]"):
                    try:
                        parsed_val = json.loads(raw_val.replace("'", '"'))
                    except Exception:
                        parsed_val = [x.strip().strip("'").strip('"') for x in raw_val[1:-1].split(",")]
                elif raw_val.lower() in ("true", "false"):
                    parsed_val = raw_val.lower() == "true"
                else:
                    try:
                        parsed_val = float(raw_val)
                    except ValueError:
                        parsed_val = raw_val

            cond = ConditionNode(
                fact=fact_key,
                operator=operator,
                value=parsed_val,
                mandatory=mandatory,
                reason_code=reason_code,
                verification_status=verification_status or "imported_unverified",
                source_fragment=source_fragment
            )
            eval_results.append(evaluate_condition(cond, facts))

        return build_scheme_evaluation(scheme_id, eval_results, evidence=evidence)

    def evaluate_scheme(
        self,
        scheme_id: str,
        facts: Dict[str, Any]
    ) -> SchemeEvaluationSummary:
        """
        Loads the scheme and its active published rules from the DB and evaluates them.
        """
        if not self.db:
            raise ValueError("EligibilityEngine requires an active DB session to evaluate_scheme by ID.")

        from services.core.database.models import Scheme, SchemeVersion, SourceConflict

        scheme = self.db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            raise ValueError(f"Scheme not found: {scheme_id}")

        version = self.db.query(SchemeVersion).filter(
            SchemeVersion.scheme_id == scheme_id,
            SchemeVersion.status == "published"
        ).order_by(SchemeVersion.version_number.desc()).first()

        if not version:
            version = self.db.query(SchemeVersion).filter(
                SchemeVersion.scheme_id == scheme_id
            ).order_by(SchemeVersion.version_number.desc()).first()

        if not version:
            return SchemeEvaluationSummary(
                scheme_id=scheme_id,
                status="NEEDS_INFO",
                confidence_score=0.0,
                matched_rules=[],
                failed_rules=[],
                missing_facts=[],
                reasons=[f"No published version found for scheme {scheme_id}."],
                evidence=[],
                deterministic_result=False,
                authority_level="tentative_unverified_rule",
                governance_notice="No verified statutory guidelines on record."
            )

        evidence_citations: List[EvidenceCitation] = []
        for src in version.sources:
            evidence_citations.append(
                EvidenceCitation(
                    source_url=src.url,
                    document_title=src.document_title or scheme.canonical_name,
                    publisher=src.publisher or "Government of India",
                    source_fragment=src.source_fragment,
                    trust_level=src.trust_level or "B",
                    verification_status=src.verification_status or "imported_unverified",
                    verified_at=src.published_date.isoformat() if src.published_date else None
                )
            )
        if not evidence_citations and (version.source_url or version.application_url):
            evidence_citations.append(
                EvidenceCitation(
                    source_url=version.source_url or version.application_url or "",
                    document_title=scheme.canonical_name,
                    publisher="Government of India",
                    source_fragment=None,
                    trust_level="B",
                    verification_status="imported_unverified"
                )
            )

        summary = self.evaluate_rules_list(
            rules=version.rules,
            facts=facts,
            scheme_id=scheme_id,
            evidence=evidence_citations
        )

        # Check for unresolved source conflicts
        open_conflicts = self.db.query(SourceConflict).filter(
            SourceConflict.scheme_id == scheme_id,
            SourceConflict.status == "SOURCE_CONFLICT_OPEN"
        ).all()

        if open_conflicts:
            summary.authority_level = "tentative_unverified_rule"
            if summary.status in ("ELIGIBLE", "NOT_ELIGIBLE"):
                summary.status = "NEEDS_VERIFICATION"
            conflict_details = "; ".join(f"{c.conflict_type} on {c.disputed_fact_key}" for c in open_conflicts)
            summary.governance_notice = f"Unresolved official source conflict ({conflict_details}). Decision is routed for human verification."

        return summary

    def explain_rule(
        self,
        scheme_id: str,
        rule_id: Optional[str] = None,
        fact_key: Optional[str] = None,
        facts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explains why a specific statutory rule passed, failed, or is missing information.
        """
        facts = facts or {}
        if not self.db:
            raise ValueError("EligibilityEngine requires an active DB session to explain_rule by scheme_id.")

        from services.core.database.models import EligibilityRule, SchemeVersion

        query = self.db.query(EligibilityRule).join(
            SchemeVersion, EligibilityRule.scheme_version_id == SchemeVersion.id
        ).filter(SchemeVersion.scheme_id == scheme_id)

        if rule_id:
            query = query.filter(EligibilityRule.id == rule_id)
        elif fact_key:
            query = query.filter(EligibilityRule.fact_key == fact_key)

        rule = query.first()
        if not rule:
            return {
                "found": False,
                "scheme_id": scheme_id,
                "rule_id": rule_id,
                "fact_key": fact_key,
                "explanation": f"Rule not found for scheme {scheme_id}."
            }

        # Evaluate this rule
        res_summary = self.evaluate_rules_list([rule], facts, scheme_id=scheme_id)
        status = res_summary.status
        user_val = facts.get(rule.fact_key)

        explanation = ""
        if status == "ELIGIBLE":
            explanation = f"Criteria satisfied: {rule.fact_key} value '{user_val}' meets the requirement ({rule.operator} {rule.expected_value})."
        elif status == "NOT_ELIGIBLE":
            explanation = f"Statutory requirement not met: {rule.fact_key} is '{user_val}', but guideline requires {rule.operator} {rule.expected_value}."
        elif status == "NEEDS_INFO":
            explanation = f"Information needed: '{rule.fact_key}' is not specified. Guideline specifies {rule.operator} {rule.expected_value}."
        else:
            explanation = f"Status '{status}': requires verification against official guidelines."

        return {
            "found": True,
            "scheme_id": scheme_id,
            "rule_id": rule.id,
            "fact_key": rule.fact_key,
            "operator": rule.operator,
            "expected_value": rule.expected_value,
            "actual_value": user_val,
            "is_mandatory": rule.mandatory,
            "reason_code": rule.reason_code,
            "evaluation_state": "PASS" if status == "ELIGIBLE" else ("FAIL" if status == "NOT_ELIGIBLE" else "UNKNOWN"),
            "status": status,
            "explanation": explanation,
            "source_fragment": rule.source_fragment,
            "verification_status": rule.verification_status
        }
