"""
CivixAI Risk-Stratified Human Review Packet Generator
=====================================================
Compiles all deterministic evaluation stages into an immutable, prioritized
audit packet for Human Compliance Officers.

Risk Stratification Algorithm:
- 🟢 LOW RISK:
    - 100% semantically valid (0 contradictions).
    - 100% reachable facts (all statutory leaves askable/derivable).
    - 0 unresolved policy terms (no vague/discretionary clauses).
    - High evidence grounding (completeness >= 0.8).
- 🟡 MEDIUM RISK:
    - Semantically valid and reachable.
    - Minor unmapped clauses or moderate evidence grounding.
- 🔴 HIGH RISK:
    - Fatal semantic contradiction or inverted range.
    - Unreachable statutory fact (certification blocked by linter).
    - Unresolved discretionary policy terms ("as determined by authority").
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.core.discovery.models import ProgramCandidate
from services.core.rules.compiler import CompilationResult, UnresolvedPolicyTerm
from services.core.rules.semantic_validator import SemanticValidationReport
from services.core.benefits.formula_engine import BenefitFormula
from services.core.applications.route_extractor import ApplicationRoute
from services.core.discovery.governance import EvidenceAnchor


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReviewPacket(BaseModel):
    packet_id: str
    candidate_id: str
    official_name: str
    sector: str
    provider_name: str
    authority_tier: str
    source_url: str
    snapshot_id: Optional[str] = None
    risk_tier: RiskTier
    risk_reasons: List[str] = Field(default_factory=list)
    
    # Audit Sections
    ast_summary: Dict[str, Any]
    reachability_summary: Dict[str, Any]
    semantic_summary: Dict[str, Any]
    benefit_summary: Dict[str, Any]
    application_route_summary: Dict[str, Any]
    unresolved_policy_terms: List[UnresolvedPolicyTerm] = Field(default_factory=list)
    evidence_anchors_count: int = 0
    can_auto_certify_in_pilot: bool = False


class ReviewPacketGenerator:
    """Creates structured, risk-scored review packets for human governance."""

    def __init__(self):
        pass

    def create_packet(
        self,
        candidate: ProgramCandidate,
        compilation: CompilationResult,
        reachability: Dict[str, Any],
        semantic: SemanticValidationReport,
        benefit: BenefitFormula,
        route: ApplicationRoute,
    ) -> ReviewPacket:
        risk_reasons: List[str] = []
        is_high_risk = False
        is_medium_risk = False

        # 1. Semantic Check
        if not semantic.is_semantically_valid:
            is_high_risk = True
            for v in semantic.violations:
                if v.severity == "FATAL":
                    risk_reasons.append(f"Semantic Fatal Error: {v.message}")

        # 2. Reachability Check
        if not reachability.get("is_reachable", False):
            is_high_risk = True
            unresolved_keys = [leaf.get("fact_key") for leaf in reachability.get("unresolved_leaves", [])]
            risk_reasons.append(f"Linter Reachability Block: Unresolvable statutory facts {unresolved_keys}")

        # 3. Discretionary Policy Terms
        if compilation.unresolved_terms:
            is_high_risk = True
            for u in compilation.unresolved_terms:
                risk_reasons.append(f"Discretionary Policy Clause: {u.policy_code} ('{u.raw_clause[:60]}...')")

        # 4. Incomplete Criteria or Warnings
        if not is_high_risk:
            if compilation.compilation_warnings:
                is_medium_risk = True
                risk_reasons.append(f"Compilation Warnings: {len(compilation.compilation_warnings)} unmapped clauses")
            if semantic.completeness_score < 0.8:
                is_medium_risk = True
                risk_reasons.append(f"Moderate Evidence Grounding: Completeness score is {semantic.completeness_score}")
            if len(compilation.flat_conditions) == 0:
                is_high_risk = True
                risk_reasons.append("Zero statutory conditions extracted from eligibility summary.")

        # Assign Tier
        if is_high_risk:
            tier = RiskTier.HIGH
        elif is_medium_risk:
            tier = RiskTier.MEDIUM
        else:
            tier = RiskTier.LOW

        can_auto_certify = (tier == RiskTier.LOW and len(compilation.flat_conditions) > 0)

        return ReviewPacket(
            packet_id=f"packet-{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            official_name=candidate.official_name,
            sector=candidate.sector,
            provider_name=candidate.provider_name,
            authority_tier=candidate.authority_tier,
            source_url=candidate.source_url,
            snapshot_id=candidate.snapshot_id,
            risk_tier=tier,
            risk_reasons=risk_reasons,
            ast_summary={
                "has_root_node": compilation.root_node is not None,
                "conditions_count": len(compilation.flat_conditions),
                "conditions": [c.model_dump() for c in compilation.flat_conditions],
            },
            reachability_summary={
                "is_reachable": reachability.get("is_reachable", False),
                "total_leaves": reachability.get("total_leaves", 0),
                "unresolved_count": reachability.get("unresolved_count", 0),
            },
            semantic_summary={
                "is_valid": semantic.is_semantically_valid,
                "completeness_score": semantic.completeness_score,
                "fatal_count": semantic.fatal_violations_count,
            },
            benefit_summary={
                "benefit_type": benefit.benefit_type.value,
                "cadence": benefit.cadence.value,
                "nominal_amount": benefit.nominal_amount,
                "formula": benefit.formula_expression,
                "description": benefit.benefit_description,
            },
            application_route_summary={
                "channel_type": route.channel_type.value,
                "official_url": route.official_url,
                "is_gov_verified": route.is_url_gov_verified,
                "documents_required": route.documents_required,
                "instructions": route.instructions_summary,
            },
            unresolved_policy_terms=compilation.unresolved_terms,
            evidence_anchors_count=len(compilation.evidence_anchors),
            can_auto_certify_in_pilot=can_auto_certify,
        )
