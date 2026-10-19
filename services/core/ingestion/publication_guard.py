"""
Canonical Publication Guard (P0 Security & Governance Hardening)
Enforces inviolable boundary gates between staging/extraction and canonical statutory publication.
Fails closed on missing evidence, missing source locators, uncertified changesets, or synthetic reviewer identities.
"""
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from services.core.database.models import (
    SchemeChangeSet, SchemeVersion, Scheme, EligibilityRule,
    Benefit, DocumentRequirement, SourceDocument, SchemeCertificationDossier
)


class CanonicalPublicationGuard:
    """
    P0 Canonical Publication Guard.
    Prevents unreviewed, unverified, or synthetically approved scheme changesets
    from achieving active/published statutory SchemeVersion status.
    """

    SYNTHETIC_OR_DISALLOWED_REVIEWERS: Set[str] = {
        "admin",
        "system",
        "auto",
        "auto_evaluator",
        "civix-lead-governance-evaluator",
        "gov_semantic_auditor_v1",
        "test_auditor",
        "test_reviewer",
        "script",
        "evaluator",
        "automated",
        "bot"
    }

    AUTHORIZED_GOVERNANCE_ROLES: Set[str] = {
        "compliance_officer",
        "legal_reviewer",
        "lead_compliance_officer",
        "statutory_auditor"
    }

    @classmethod
    def validate_for_publication(
        cls,
        changeset: SchemeChangeSet,
        reviewer_id: Optional[str] = None,
        is_authenticated_human: bool = False,
        governance_role: Optional[str] = None,
        dossier: Optional[SchemeCertificationDossier] = None
    ) -> Dict[str, Any]:
        """
        Validates all statutory publication prerequisites.
        Fails closed with ValueError upon detecting any governance, evidence, or identity defect.
        """
        # 1. Reviewer Identity & Authentication Gate
        if not reviewer_id or not str(reviewer_id).strip():
            raise ValueError(
                "Publication blocked: Missing reviewer_id. Statutory publication requires verified human reviewer."
            )

        clean_reviewer = str(reviewer_id).strip().lower()
        if clean_reviewer in cls.SYNTHETIC_OR_DISALLOWED_REVIEWERS:
            raise ValueError(
                f"Publication blocked: Reviewer '{reviewer_id}' is an automated, synthetic, or default identity. "
                "Only verified human governance officers may authorize publication."
            )

        if not is_authenticated_human:
            raise ValueError(
                "Publication blocked: Reviewer identity is not an authenticated human officer (fails closed)."
            )

        if not governance_role or governance_role.lower() not in cls.AUTHORIZED_GOVERNANCE_ROLES:
            raise ValueError(
                f"Publication blocked: Role '{governance_role}' is not authorized for statutory publication. "
                f"Required role in {cls.AUTHORIZED_GOVERNANCE_ROLES}."
            )

        # 2. Changeset State Gate
        if not changeset:
            raise ValueError("Publication blocked: Changeset is missing or null.")

        cs_status = getattr(changeset, "status", None)
        if cs_status not in ("approved", "certified", "in_review", "pending_governance_signoff"):
            raise ValueError(
                f"Publication blocked: Changeset status '{cs_status}' is uncertified. "
                "Publication requires an approved/certified changeset."
            )

        # 3. Source Snapshot & Trust Level Gate
        snapshot = changeset.source_snapshot
        if not snapshot:
            raise ValueError("Publication blocked: Changeset lacks required SourceSnapshot.")

        if not getattr(snapshot, "content_hash", None):
            raise ValueError("Publication blocked: SourceSnapshot lacks cryptographic content_hash (SHA-256).")

        source = getattr(snapshot, "source_registry", None)
        if source:
            trust_level = getattr(source, "trust_level", None)
            if trust_level not in ("A", "B"):
                raise ValueError(
                    f"Publication blocked: Source trust level '{trust_level}' is below required statutory threshold (A/B)."
                )

            freshness = getattr(source, "freshness_status", "fresh")
            if freshness in ("stale", "superseded", "expired"):
                raise ValueError(
                    f"Publication blocked: Source evidence is marked '{freshness}'."
                )

        # 4. Evidence & Verbatim Quotation Gate
        rule_drafts = getattr(changeset, "rule_drafts", [])
        if not rule_drafts:
            raise ValueError("Publication blocked: Changeset contains no evidence or rule drafts.")

        for r in rule_drafts:
            fact_key = getattr(r, "fact_key", "unknown")
            fragment = getattr(r, "source_fragment", None)
            if not fragment or not str(fragment).strip():
                raise ValueError(
                    f"Publication blocked: Rule draft for '{fact_key}' lacks mandatory verbatim source_fragment."
                )

            # Check statutory source locator (section, clause, paragraph, page)
            locator = getattr(r, "source_locator", None)
            if not locator or not str(locator).strip():
                raise ValueError(
                    f"Publication blocked: Rule draft for '{fact_key}' lacks mandatory statutory source_locator."
                )

        # 5. Certification Dossier Gate
        if not dossier:
            raise ValueError(
                "Publication blocked: Missing SchemeCertificationDossier. Publication requires an active approved dossier."
            )

        dossier_status = getattr(dossier, "semantic_review_status", getattr(dossier, "review_status", getattr(dossier, "status", None)))
        if dossier_status not in ("approved", "certified") and not getattr(dossier, "governance_approved", False):
            raise ValueError(
                f"Publication blocked: Certification dossier status is '{dossier_status}', required 'approved' or 'certified'."
            )

        dossier_certifier = getattr(dossier, "certified_by", None)
        if not dossier_certifier or str(dossier_certifier).strip().lower() in cls.SYNTHETIC_OR_DISALLOWED_REVIEWERS:
            raise ValueError(
                f"Publication blocked: Dossier was certified by synthetic actor '{dossier_certifier}'."
            )

        return {
            "status": "validated",
            "reviewer_id": clean_reviewer,
            "governance_role": governance_role,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
