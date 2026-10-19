"""
Source Conflict Engine
Phase 3.6 Hardened Governance:
- Detects material discrepancies between authoritative sources for the same scheme.
- Records rich conflict assertions: source A assertion, source B assertion, authority metadata,
  effective dates, and disputed fact key.
- Supports standardized resolution types:
    * SOURCE_A_PREVAILS
    * SOURCE_B_PREVAILS
    * BOTH_APPLY_DIFFERENT_CONTEXT
    * SUPERSEDED
    * INSUFFICIENT_EVIDENCE
- Routes all disputed rules into human governance as SOURCE_CONFLICT_OPEN.
- Any open conflict forces governance status to NEEDS_VERIFICATION.
"""
import uuid
import json
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from services.core.database.models import (
    SourceConflict, Scheme, EligibilityRule, Benefit,
    DocumentRequirement, SourceRegistry, AuditLog
)

class ConflictResolutionType(str, Enum):
    SOURCE_A_PREVAILS = "SOURCE_A_PREVAILS"
    SOURCE_B_PREVAILS = "SOURCE_B_PREVAILS"
    BOTH_APPLY_DIFFERENT_CONTEXT = "BOTH_APPLY_DIFFERENT_CONTEXT"
    SUPERSEDED = "SUPERSEDED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

VALID_RESOLUTION_TYPES = {
    ConflictResolutionType.SOURCE_A_PREVAILS.value,
    ConflictResolutionType.SOURCE_B_PREVAILS.value,
    ConflictResolutionType.BOTH_APPLY_DIFFERENT_CONTEXT.value,
    ConflictResolutionType.SUPERSEDED.value,
    ConflictResolutionType.INSUFFICIENT_EVIDENCE.value,
}

class SourceConflictEngine:
    def __init__(self, db: Session):
        self.db = db

    def check_rule_conflict(
        self,
        scheme_id: str,
        fact_key: str,
        new_operator: str,
        new_expected_value: Any,
        source_a_id: Optional[str] = None,
        source_a_title: Optional[str] = None,
        source_b_id: Optional[str] = None,
        source_b_title: Optional[str] = None,
        effective_dates: Optional[str] = None,
        source_authority_metadata: Optional[str] = None
    ) -> Optional[SourceConflict]:
        """
        Checks if candidate rule contradicts an existing published rule or secondary source.
        If discrepancy is found, creates and persists a rich SourceConflict record.
        """
        existing_rules = self.db.query(EligibilityRule).join(
            EligibilityRule.scheme_version
        ).filter(
            EligibilityRule.scheme_version.has(scheme_id=scheme_id),
            EligibilityRule.fact_key == fact_key
        ).all()

        for ex_rule in existing_rules:
            # Check if values differ materially
            if ex_rule.operator != new_operator or str(ex_rule.expected_value) != str(new_expected_value):
                conflict_type = "threshold_conflict"
                if "age" in fact_key:
                    conflict_type = "age_conflict"
                elif "state" in fact_key or "district" in fact_key:
                    conflict_type = "geographic_conflict"
                elif "gender" in fact_key or "caste" in fact_key:
                    conflict_type = "category_conflict"

                # Check if conflict is already recorded and open
                existing_conflict = self.db.query(SourceConflict).filter(
                    SourceConflict.scheme_id == scheme_id,
                    SourceConflict.disputed_fact_key == fact_key,
                    SourceConflict.status == "SOURCE_CONFLICT_OPEN"
                ).first()

                if existing_conflict:
                    return existing_conflict

                val_a = f"{ex_rule.operator} {ex_rule.expected_value}"
                val_b = f"{new_operator} {new_expected_value}"
                conflict = SourceConflict(
                    id=f"conf-{uuid.uuid4().hex[:12]}",
                    scheme_id=scheme_id,
                    rule_id=ex_rule.id,
                    conflict_type=conflict_type,
                    status="SOURCE_CONFLICT_OPEN",
                    source_a_id=source_a_id,
                    source_a_title=source_a_title or "Published Baseline Rule",
                    source_a_value=val_a,
                    source_a_assertion=f"Published baseline asserts: {fact_key} {val_a}",
                    source_b_id=source_b_id,
                    source_b_title=source_b_title or "Newly Ingested Official Document",
                    source_b_value=val_b,
                    source_b_assertion=f"Ingested document asserts: {fact_key} {val_b}",
                    effective_dates=effective_dates,
                    source_authority_metadata=source_authority_metadata or json.dumps({
                        "rule_reason": ex_rule.reason_code,
                        "mandatory": ex_rule.mandatory
                    }),
                    disputed_fact_key=fact_key,
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(conflict)
                self.db.commit()
                self.db.refresh(conflict)
                return conflict

        return None

    def check_benefit_conflict(
        self,
        scheme_id: str,
        new_fixed_amount: Optional[float],
        source_a_title: str,
        source_b_title: str,
        source_a_id: Optional[str] = None,
        source_b_id: Optional[str] = None
    ) -> Optional[SourceConflict]:
        """Detects discrepancies in financial assistance or benefit payouts."""
        if new_fixed_amount is None:
            return None

        existing_benefits = self.db.query(Benefit).join(
            Benefit.scheme_version
        ).filter(
            Benefit.scheme_version.has(scheme_id=scheme_id)
        ).all()

        for b in existing_benefits:
            if b.fixed_amount is not None and abs(b.fixed_amount - new_fixed_amount) > 1.0:
                conflict = SourceConflict(
                    id=f"conf-ben-{uuid.uuid4().hex[:10]}",
                    scheme_id=scheme_id,
                    conflict_type="benefit_conflict",
                    status="SOURCE_CONFLICT_OPEN",
                    source_a_id=source_a_id,
                    source_a_title=source_a_title,
                    source_a_value=f"₹{b.fixed_amount:,.2f}",
                    source_a_assertion=f"Baseline benefit asserts fixed amount of ₹{b.fixed_amount:,.2f}",
                    source_b_id=source_b_id,
                    source_b_title=source_b_title,
                    source_b_value=f"₹{new_fixed_amount:,.2f}",
                    source_b_assertion=f"Ingested source asserts fixed amount of ₹{new_fixed_amount:,.2f}",
                    disputed_fact_key="scheme.benefit_amount",
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(conflict)
                self.db.commit()
                self.db.refresh(conflict)
                return conflict
        return None

    def get_open_conflicts_for_scheme(self, scheme_id: str) -> List[SourceConflict]:
        return self.db.query(SourceConflict).filter(
            SourceConflict.scheme_id == scheme_id,
            SourceConflict.status == "SOURCE_CONFLICT_OPEN"
        ).all()

    def resolve_conflict(
        self,
        conflict_id: str,
        resolved_by: str,
        resolution_type: str = "SOURCE_A_PREVAILS",
        resolution_notes: str = "",
        winning_evidence: Optional[str] = None,
        review_analysis: Optional[str] = None
    ) -> SourceConflict:
        """
        Resolves an open conflict with a certified resolution type, evidence, and audit log.
        """
        conflict = self.db.query(SourceConflict).filter(SourceConflict.id == conflict_id).first()
        if not conflict:
            raise ValueError(f"Source conflict '{conflict_id}' not found")

        if resolution_type not in VALID_RESOLUTION_TYPES:
            raise ValueError(
                f"Invalid resolution_type '{resolution_type}'. Must be one of: {sorted(list(VALID_RESOLUTION_TYPES))}"
            )

        now_utc = datetime.now(timezone.utc)
        conflict.status = "SOURCE_CONFLICT_RESOLVED"
        conflict.resolution_type = resolution_type
        conflict.resolved_by = resolved_by
        conflict.resolution_notes = resolution_notes
        conflict.winning_evidence = winning_evidence
        conflict.review_analysis = review_analysis
        conflict.resolved_at = now_utc

        # Record compliance audit log
        audit = AuditLog(
            id=f"audit-conf-{uuid.uuid4().hex[:10]}",
            entity_type="source_conflict",
            entity_id=conflict_id,
            action="resolve_conflict",
            actor_id=resolved_by,
            reason=f"Resolved with type '{resolution_type}': {resolution_notes}",
            created_at=now_utc
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(conflict)
        return conflict
