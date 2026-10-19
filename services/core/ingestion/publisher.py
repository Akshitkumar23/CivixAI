"""
Governance Publisher
Handles controlled human review, quality gates, version transitions, and immutable audit logging.
Critical quality failures strictly block publication.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from services.core.database.models import (
    SchemeChangeSet, SchemeVersion, Scheme, EligibilityRule,
    Benefit, DocumentRequirement, SourceDocument, AuditLog, SourceRegistry,
    SchemeCertificationDossier
)
from .quality import DataQualityEngine
from .publication_guard import CanonicalPublicationGuard

class GovernancePublisher:
    def __init__(self, db: Session):
        self.db = db

    def approve_and_publish(
        self,
        changeset_id: str,
        reviewer_id: Optional[str] = None,
        is_authenticated_human: bool = False,
        governance_role: Optional[str] = None,
        dossier: Optional[SchemeCertificationDossier] = None,
        review_notes: str = "",
        promote_to_source_verified: bool = True
    ) -> SchemeVersion:
        """
        Approves a staging changeset and publishes it as a new production SchemeVersion.
        Ensures strict statutory publication gating via CanonicalPublicationGuard.
        """
        changeset = self.db.query(SchemeChangeSet).filter(SchemeChangeSet.id == changeset_id).first()
        if not changeset:
            raise ValueError(f"Changeset '{changeset_id}' not found.")

        if changeset.status == "approved":
            raise ValueError(f"Changeset '{changeset_id}' has already been approved.")

        # If dossier is not passed explicitly, attempt lookup of active approved dossier
        if dossier is None:
            dossier = self.db.query(SchemeCertificationDossier).filter(
                SchemeCertificationDossier.scheme_id == changeset.scheme_id,
                SchemeCertificationDossier.semantic_review_status.in_(["approved", "certified"]),
                SchemeCertificationDossier.is_active == True
            ).first()

        # Enforce Canonical Publication Guard (Fails closed on missing or synthetic governance)
        CanonicalPublicationGuard.validate_for_publication(
            changeset=changeset,
            reviewer_id=reviewer_id,
            is_authenticated_human=is_authenticated_human,
            governance_role=governance_role,
            dossier=dossier
        )

        # 1. Enforce Data Quality Gate
        source = None
        if changeset.source_snapshot and changeset.source_snapshot.source_registry:
            source = changeset.source_snapshot.source_registry
        report = DataQualityEngine.audit_changeset(changeset, source=source)

        if not report.is_valid_for_publication:
            err_msgs = [e.message for e in report.critical_errors]
            raise ValueError(f"Publication blocked by data quality gate: {'; '.join(err_msgs)}")

        now_utc = datetime.now(timezone.utc)

        # 2. Get existing active scheme version
        scheme = self.db.query(Scheme).filter(Scheme.id == changeset.scheme_id).first()
        if not scheme:
            raise ValueError(f"Scheme '{changeset.scheme_id}' does not exist.")

        prev_version = self.db.query(SchemeVersion).filter(
            SchemeVersion.scheme_id == scheme.id,
            SchemeVersion.status == "published"
        ).order_by(SchemeVersion.version_number.desc()).first()

        next_version_num = (prev_version.version_number + 1) if prev_version else 1

        # Determine verification status
        # Only Trust Level A/B official sources with human review can achieve source_verified!
        ver_status = "human_reviewed"
        if promote_to_source_verified and source and source.trust_level in ("A", "B"):
            ver_status = "source_verified"

        # Archive previous active version
        if prev_version:
            prev_version.status = "archived"
            prev_version.verification_status = "superseded"

        # 3. Create new SchemeVersion
        new_version_id = f"{scheme.id}-v{next_version_num}"
        new_version = SchemeVersion(
            id=new_version_id,
            scheme_id=scheme.id,
            version_number=next_version_num,
            effective_from=now_utc,
            effective_to=None,
            published_at=now_utc,
            verified_at=now_utc,
            status="published",
            verification_status=ver_status,
            review_notes=review_notes,
            reviewed_by=reviewer_id,
            summary=changeset.change_summary or (prev_version.summary if prev_version else scheme.canonical_name),
            description=prev_version.description if prev_version else "",
            application_url=prev_version.application_url if prev_version else "",
            source_url=source.canonical_url if source else (prev_version.source_url if prev_version else None),
            source_hash=changeset.source_snapshot.content_hash if changeset.source_snapshot else None
        )
        self.db.add(new_version)
        scheme.current_version_number = next_version_num

        # 4. Create authoritative SourceDocument provenance record
        source_doc_id = f"srcdoc-{uuid.uuid4().hex[:12]}"
        if source:
            source_doc = SourceDocument(
                id=source_doc_id,
                scheme_version_id=new_version_id,
                url=source.canonical_url,
                document_title=source.title,
                publisher=source.publisher,
                source_fragment="Full Guidelines Snapshot",
                content_hash=changeset.source_snapshot.content_hash if changeset.source_snapshot else None,
                fetched_at=now_utc,
                published_date=now_utc,
                effective_from=now_utc,
                document_type=source.source_type,
                trust_level=source.trust_level,
                verification_status=ver_status,
                freshness_status="fresh",
                snapshot_id=changeset.source_snapshot_id
            )
            self.db.add(source_doc)

        # 5. Promote draft rules into production
        for rd in changeset.rule_drafts:
            rule = EligibilityRule(
                id=f"rule-{uuid.uuid4().hex[:12]}",
                scheme_version_id=new_version_id,
                source_evidence_id=source_doc_id if source else None,
                source_fragment=rd.source_fragment,
                rule_group="default",
                fact_key=rd.fact_key,
                operator=rd.operator,
                expected_value=rd.expected_value,
                rule_expression=rd.rule_expression,
                mandatory=rd.mandatory,
                verification_status=ver_status,
                effective_from=now_utc,
                scope=rd.scope,
                reason_code=rd.reason_code
            )
            self.db.add(rule)

        # 6. Promote draft benefits
        for bd in changeset.benefit_drafts:
            benefit = Benefit(
                id=f"ben-{uuid.uuid4().hex[:12]}",
                scheme_version_id=new_version_id,
                source_evidence_id=source_doc_id if source else None,
                benefit_type=bd.benefit_type,
                amount_type=bd.amount_type,
                fixed_amount=bd.fixed_amount,
                min_amount=bd.min_amount,
                max_amount=bd.max_amount,
                frequency=bd.frequency,
                description=bd.description,
                verification_status=ver_status,
                effective_from=now_utc
            )
            self.db.add(benefit)

        # 7. Promote draft document requirements
        for dd in changeset.document_drafts:
            doc_req = DocumentRequirement(
                id=f"doc-{uuid.uuid4().hex[:12]}",
                scheme_version_id=new_version_id,
                source_evidence_id=source_doc_id if source else None,
                document_type=dd.document_type,
                is_mandatory=dd.is_mandatory,
                verification_status=ver_status
            )
            self.db.add(doc_req)

        # 8. Mark changeset approved
        changeset.status = "approved"
        changeset.reviewed_at = now_utc
        changeset.reviewed_by = reviewer_id
        changeset.review_notes = review_notes

        # 9. Immutable Audit Log
        audit = AuditLog(
            id=f"audit-{uuid.uuid4().hex[:12]}",
            entity_type="scheme_version",
            entity_id=new_version_id,
            action="publish_approved_version",
            actor_id=reviewer_id,
            previous_state_json=json.dumps({"version": prev_version.version_number if prev_version else None}),
            new_state_json=json.dumps({"version": next_version_num, "status": ver_status, "rules_count": len(changeset.rule_drafts)}),
            reason=f"Approved changeset {changeset_id}: {review_notes}"
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(new_version)
        return new_version

    def reject_changeset(
        self,
        changeset_id: str,
        reviewer_id: str = "admin",
        reason: str = "Evidence mismatch",
        review_notes: str = ""
    ) -> SchemeChangeSet:
        """
        Rejects a staging changeset without modifying production tables.
        Records an immutable audit log entry.
        """
        changeset = self.db.query(SchemeChangeSet).filter(SchemeChangeSet.id == changeset_id).first()
        if not changeset:
            raise ValueError(f"Changeset '{changeset_id}' not found.")

        now_utc = datetime.now(timezone.utc)
        changeset.status = "rejected"
        changeset.reviewed_at = now_utc
        changeset.reviewed_by = reviewer_id
        changeset.review_notes = f"REJECTED [{reason}]: {review_notes}"

        audit = AuditLog(
            id=f"audit-{uuid.uuid4().hex[:12]}",
            entity_type="scheme_changeset",
            entity_id=changeset_id,
            action="reject_changeset",
            actor_id=reviewer_id,
            previous_state_json=json.dumps({"status": "pending"}),
            new_state_json=json.dumps({"status": "rejected", "reason": reason}),
            reason=review_notes
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(changeset)
        return changeset
