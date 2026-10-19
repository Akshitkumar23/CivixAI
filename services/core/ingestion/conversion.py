"""
Bootstrap Conversion Workflows
Controlled, auditable transition of bootstrap records (rules, benefits, document requirements)
against authoritative official evidence.

Outcomes for Rules:
- confirmed_and_reviewed: Verified against official text without changes.
- modified_by_official_source: Rule parameters corrected against gazette/guideline.
- superseded: Replaced by newer official rule.
- still_unverified: Audit incomplete; remains unverified.
- conflicted: Contradicts another source; routed to conflict engine.
- removed_as_invalid: Deleted from production as erroneous bootstrap relic.

Every state transition produces an immutable AuditLog record. Bulk promotion is strictly prohibited.
"""
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from services.core.database.models import (
    EligibilityRule, Benefit, DocumentRequirement,
    SourceDocument, AuditLog, SchemeVersion
)

class RuleConversionOutcome(str, Enum):
    CONFIRMED_AND_REVIEWED = "confirmed_and_reviewed"
    MODIFIED_BY_OFFICIAL_SOURCE = "modified_by_official_source"
    SUPERSEDED = "superseded"
    STILL_UNVERIFIED = "still_unverified"
    CONFLICTED = "conflicted"
    REMOVED_AS_INVALID = "removed_as_invalid"

VALID_RULE_OUTCOMES = {o.value for o in RuleConversionOutcome}

class BootstrapConversionWorkflow:
    def __init__(self, db: Session):
        self.db = db

    def convert_rule(
        self,
        rule_id: str,
        outcome: str,
        reviewer_id: str,
        notes: str,
        source_evidence_id: Optional[str] = None,
        source_fragment: Optional[str] = None,
        modified_operator: Optional[str] = None,
        modified_expected_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transitions a single bootstrap eligibility rule with audit logging."""
        if outcome not in VALID_RULE_OUTCOMES:
            raise ValueError(f"Invalid outcome '{outcome}'. Must be one of: {sorted(list(VALID_RULE_OUTCOMES))}")

        rule = self.db.query(EligibilityRule).filter(EligibilityRule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Eligibility rule '{rule_id}' not found.")

        prev_state = {
            "fact_key": rule.fact_key,
            "operator": rule.operator,
            "expected_value": rule.expected_value,
            "verification_status": rule.verification_status,
            "source_evidence_id": rule.source_evidence_id,
            "source_fragment": rule.source_fragment
        }

        now_utc = datetime.now(timezone.utc)

        if outcome == RuleConversionOutcome.CONFIRMED_AND_REVIEWED.value:
            rule.verification_status = "source_verified" if source_evidence_id else "human_reviewed"
            if source_evidence_id:
                rule.source_evidence_id = source_evidence_id
            if source_fragment:
                rule.source_fragment = source_fragment

        elif outcome == RuleConversionOutcome.MODIFIED_BY_OFFICIAL_SOURCE.value:
            if not modified_operator or modified_expected_value is None:
                raise ValueError("Modified rules must supply modified_operator and modified_expected_value.")
            rule.operator = modified_operator
            rule.expected_value = str(modified_expected_value)
            rule.verification_status = "source_verified" if source_evidence_id else "human_reviewed"
            if source_evidence_id:
                rule.source_evidence_id = source_evidence_id
            if source_fragment:
                rule.source_fragment = source_fragment

        elif outcome == RuleConversionOutcome.SUPERSEDED.value:
            rule.verification_status = "superseded"

        elif outcome == RuleConversionOutcome.CONFLICTED.value:
            rule.verification_status = "conflicted"

        elif outcome == RuleConversionOutcome.REMOVED_AS_INVALID.value:
            self.db.delete(rule)
            audit = AuditLog(
                id=f"audit-rule-{uuid.uuid4().hex[:10]}",
                entity_type="eligibility_rule",
                entity_id=rule_id,
                action="delete_invalid_rule",
                actor_id=reviewer_id,
                previous_state_json=json.dumps(prev_state),
                new_state_json=None,
                reason=f"Removed invalid bootstrap rule: {notes}",
                created_at=now_utc
            )
            self.db.add(audit)
            self.db.commit()
            return {"rule_id": rule_id, "status": "deleted", "outcome": outcome}

        # For non-delete outcomes:
        new_state = {
            "fact_key": rule.fact_key,
            "operator": rule.operator,
            "expected_value": rule.expected_value,
            "verification_status": rule.verification_status,
            "source_evidence_id": rule.source_evidence_id,
            "source_fragment": rule.source_fragment
        }

        audit = AuditLog(
            id=f"audit-rule-{uuid.uuid4().hex[:10]}",
            entity_type="eligibility_rule",
            entity_id=rule_id,
            action=f"convert_rule_{outcome}",
            actor_id=reviewer_id,
            previous_state_json=json.dumps(prev_state),
            new_state_json=json.dumps(new_state),
            reason=notes,
            created_at=now_utc
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(rule)

        return {
            "rule_id": rule.id,
            "verification_status": rule.verification_status,
            "outcome": outcome,
            "source_evidence_id": rule.source_evidence_id
        }

    def convert_benefit(
        self,
        benefit_id: str,
        reviewer_id: str,
        notes: str,
        source_evidence_id: Optional[str] = None,
        verified_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transitions and verifies a bootstrap benefit against official evidence."""
        benefit = self.db.query(Benefit).filter(Benefit.id == benefit_id).first()
        if not benefit:
            raise ValueError(f"Benefit '{benefit_id}' not found.")

        prev_state = {
            "benefit_type": benefit.benefit_type,
            "fixed_amount": benefit.fixed_amount,
            "frequency": benefit.frequency,
            "verification_status": benefit.verification_status
        }

        now_utc = datetime.now(timezone.utc)
        if verified_details:
            if "benefit_type" in verified_details:
                benefit.benefit_type = verified_details["benefit_type"]
            if "fixed_amount" in verified_details:
                benefit.fixed_amount = verified_details["fixed_amount"]
            if "min_amount" in verified_details:
                benefit.min_amount = verified_details["min_amount"]
            if "max_amount" in verified_details:
                benefit.max_amount = verified_details["max_amount"]
            if "frequency" in verified_details:
                benefit.frequency = verified_details["frequency"]
            if "percentage" in verified_details:
                benefit.percentage = verified_details["percentage"]

        if source_evidence_id:
            benefit.source_evidence_id = source_evidence_id
            benefit.verification_status = "source_verified"
        else:
            benefit.verification_status = "human_reviewed"

        new_state = {
            "benefit_type": benefit.benefit_type,
            "fixed_amount": benefit.fixed_amount,
            "frequency": benefit.frequency,
            "verification_status": benefit.verification_status,
            "source_evidence_id": benefit.source_evidence_id
        }

        audit = AuditLog(
            id=f"audit-ben-{uuid.uuid4().hex[:10]}",
            entity_type="benefit",
            entity_id=benefit_id,
            action="verify_benefit",
            actor_id=reviewer_id,
            previous_state_json=json.dumps(prev_state),
            new_state_json=json.dumps(new_state),
            reason=notes,
            created_at=now_utc
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(benefit)

        return {
            "benefit_id": benefit.id,
            "verification_status": benefit.verification_status,
            "source_evidence_id": benefit.source_evidence_id
        }

    def convert_document(
        self,
        doc_req_id: str,
        reviewer_id: str,
        notes: str,
        requirement_category: str = "mandatory",
        requirement_stage: str = "application_stage",
        source_evidence_id: Optional[str] = None,
        alternatives: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classifies and verifies a bootstrap document requirement against official evidence."""
        doc = self.db.query(DocumentRequirement).filter(DocumentRequirement.id == doc_req_id).first()
        if not doc:
            raise ValueError(f"DocumentRequirement '{doc_req_id}' not found.")

        prev_state = {
            "document_type": doc.document_type,
            "is_mandatory": doc.is_mandatory,
            "requirement_category": getattr(doc, "requirement_category", "mandatory"),
            "requirement_stage": getattr(doc, "requirement_stage", "application_stage"),
            "verification_status": doc.verification_status
        }

        doc.requirement_category = requirement_category
        doc.requirement_stage = requirement_stage
        doc.is_mandatory = (requirement_category == "mandatory")
        if alternatives is not None:
            doc.alternatives = alternatives

        if source_evidence_id:
            doc.source_evidence_id = source_evidence_id
            doc.verification_status = "source_verified"
        else:
            doc.verification_status = "human_reviewed"

        now_utc = datetime.now(timezone.utc)
        new_state = {
            "document_type": doc.document_type,
            "is_mandatory": doc.is_mandatory,
            "requirement_category": doc.requirement_category,
            "requirement_stage": doc.requirement_stage,
            "verification_status": doc.verification_status,
            "source_evidence_id": doc.source_evidence_id
        }

        audit = AuditLog(
            id=f"audit-doc-{uuid.uuid4().hex[:10]}",
            entity_type="document_requirement",
            entity_id=doc_req_id,
            action="verify_document_requirement",
            actor_id=reviewer_id,
            previous_state_json=json.dumps(prev_state),
            new_state_json=json.dumps(new_state),
            reason=notes,
            created_at=now_utc
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(doc)

        return {
            "document_id": doc.id,
            "verification_status": doc.verification_status,
            "requirement_category": doc.requirement_category,
            "requirement_stage": doc.requirement_stage,
            "source_evidence_id": doc.source_evidence_id
        }
