"""
Scheme Maturity State Engine
Deterministic, evidence-backed maturity state calculation for welfare schemes.

Maturity States (10 Deterministic States):
1. CONFLICTED: Open material source conflict exists on the scheme.
2. STALE: Registered source exceeded freshness SLA or is unreachable.
3. UNSOURCED: Zero registered official sources.
4. SOURCE_IDENTIFIED: Sources registered, but no snapshots fetched yet.
5. SOURCE_FETCHED: Snapshot fetched, but parsing failed or OCR required.
6. PARSED: Snapshot parsed, but no candidate rules extracted yet.
7. MACHINE_EXTRACTED: Candidate draft changeset exists, pending human review.
8. PARTIALLY_REVIEWED: Human reviewer acted on drafts, but source verification incomplete.
9. PARTIALLY_VERIFIED: Some rules/benefits source_verified, but critical rules unverified.
10. FULLY_VERIFIED: All critical rules verified, zero unverified rules, zero conflicts.
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session

from services.core.database.models import (
    Scheme, SchemeVersion, EligibilityRule, Benefit,
    DocumentRequirement, SourceRegistry, SourceSnapshot,
    SchemeChangeSet, SourceConflict, AuditLog, SchemeCertificationDossier
)

class SchemeMaturityState(str, Enum):
    CONFLICTED = "CONFLICTED"
    STALE = "STALE"
    UNSOURCED = "UNSOURCED"
    SOURCE_IDENTIFIED = "SOURCE_IDENTIFIED"
    SOURCE_FETCHED = "SOURCE_FETCHED"
    PARSED = "PARSED"
    MACHINE_EXTRACTED = "MACHINE_EXTRACTED"
    PARTIALLY_REVIEWED = "PARTIALLY_REVIEWED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FULLY_VERIFIED = "FULLY_VERIFIED"

CRITICAL_FACT_KEYS: Set[str] = {
    "person.age",
    "person.income",
    "person.annual_income",
    "household.income",
    "household.annual_income",
    "person.gender",
    "person.category",
    "person.caste",
    "person.occupation",
    "location.state",
    "location.district",
    "location.area_type",
    "scheme.is_active",
    "applicant.disability",
    "applicant.landholding",
    "scheme.benefit_amount",
    "scheme.application_deadline",
}

from services.core.ingestion.coverage import CorpusCoverageService, CRITICAL_FACT_KEYS

class SchemeMaturityService:
    def __init__(self, db: Session):
        self.db = db
        self.coverage_service = CorpusCoverageService(db)

    def evaluate_scheme_maturity(self, scheme_id: str) -> Dict[str, Any]:
        """
        Calculates the exact deterministic maturity state and diagnostic metrics for a scheme.
        Zero synthetic metrics.
        """
        scheme = self.db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            raise ValueError(f"Scheme '{scheme_id}' not found.")

        # 1. Check open conflicts
        open_conflicts = self.db.query(SourceConflict).filter(
            SourceConflict.scheme_id == scheme_id,
            SourceConflict.status == "SOURCE_CONFLICT_OPEN"
        ).all()
        if open_conflicts:
            return {
                "scheme_id": scheme_id,
                "canonical_name": scheme.canonical_name,
                "maturity_state": SchemeMaturityState.CONFLICTED.value,
                "reason": f"{len(open_conflicts)} open source conflict(s) require resolution",
                "open_conflicts_count": len(open_conflicts),
                "critical_rules_unverified": 0,
                "is_fully_verified": False
            }

        # 2. Canonical source coverage resolution
        cov = self.coverage_service.get_sources_for_scheme(scheme_id)
        sources = cov["registered_sources"]
        version_sources = cov["version_sources"]
        total_sources_count = cov["total_count"]

        current_version = self.db.query(SchemeVersion).filter(
            SchemeVersion.scheme_id == scheme_id,
            SchemeVersion.status == "published"
        ).order_by(SchemeVersion.version_number.desc()).first()

        # If zero sources, scheme is unequivocally UNSOURCED
        if total_sources_count == 0:
            return {
                "scheme_id": scheme_id,
                "canonical_name": scheme.canonical_name,
                "maturity_state": SchemeMaturityState.UNSOURCED.value,
                "reason": "No registered official sources found",
                "open_conflicts_count": 0,
                "critical_rules_unverified": 0,
                "is_fully_verified": False
            }

        # 3. Check source staleness / unreachability
        has_stale_source = any(
            s.freshness_status in ("stale", "unreachable") or s.last_fetch_status in ("timeout", "unreachable", "failed", "dns_error")
            for s in sources
        )
        if has_stale_source:
            return {
                "scheme_id": scheme_id,
                "canonical_name": scheme.canonical_name,
                "maturity_state": SchemeMaturityState.STALE.value,
                "reason": "One or more registered official sources are stale or unreachable",
                "open_conflicts_count": 0,
                "critical_rules_unverified": 0,
                "is_fully_verified": False
            }

        # 4. Check snapshots
        source_ids = [s.id for s in sources]
        snapshots = self.db.query(SourceSnapshot).filter(
            SourceSnapshot.source_registry_id.in_(source_ids)
        ).all() if source_ids else []

        if not snapshots and not any(s.snapshot_id for s in version_sources):
            return {
                "scheme_id": scheme_id,
                "canonical_name": scheme.canonical_name,
                "maturity_state": SchemeMaturityState.SOURCE_IDENTIFIED.value,
                "reason": "Official sources registered but no snapshots fetched yet",
                "open_conflicts_count": 0,
                "critical_rules_unverified": 0,
                "is_fully_verified": False
            }

        # 5. Check parser health
        has_ocr_or_failed = any(
            s.parser_health in ("ocr_required", "failed") for s in sources
        )
        if has_ocr_or_failed:
            return {
                "scheme_id": scheme_id,
                "canonical_name": scheme.canonical_name,
                "maturity_state": SchemeMaturityState.SOURCE_FETCHED.value,
                "reason": "Snapshot fetched but parsing incomplete or OCR required",
                "open_conflicts_count": 0,
                "critical_rules_unverified": 0,
                "is_fully_verified": False
            }

        # 6. Check pending changesets / drafts
        pending_changesets = self.db.query(SchemeChangeSet).filter(
            SchemeChangeSet.scheme_id == scheme_id,
            SchemeChangeSet.status == "pending"
        ).all()

        reviewed_changesets = self.db.query(SchemeChangeSet).filter(
            SchemeChangeSet.scheme_id == scheme_id,
            SchemeChangeSet.status.in_(["approved", "rejected"])
        ).all()

        # 7. Check current production rules
        rules = current_version.rules if current_version else []
        total_rules = len(rules)
        unverified_rules = [r for r in rules if r.verification_status == "imported_unverified"]
        verified_rules = [r for r in rules if r.verification_status == "source_verified"]
        human_rules = [r for r in rules if r.verification_status == "human_reviewed"]

        # Critical rules analysis
        critical_rules = [r for r in rules if r.fact_key in CRITICAL_FACT_KEYS]
        unverified_critical = [r for r in critical_rules if r.verification_status == "imported_unverified"]

        # 8. Deterministic state classification
        if total_rules > 0 and len(unverified_rules) == 0 and len(unverified_critical) == 0 and len(verified_rules) > 0:
            if current_version and current_version.verification_status == "source_verified":
                # Strict Phase 3.8 check: must also be semantically certified, current, complete, and have active dossier
                is_sem_certified = (getattr(current_version, "semantic_review_status", None) == "certified")
                is_current = (getattr(current_version, "currentness_status", None) == "current")
                is_complete = (getattr(current_version, "completeness_status", None) == "complete")

                active_dossier = self.db.query(SchemeCertificationDossier).filter(
                    SchemeCertificationDossier.scheme_version_id == current_version.id,
                    SchemeCertificationDossier.is_active == True,
                    SchemeCertificationDossier.semantic_review_status == "certified"
                ).first() if current_version else None

                if is_sem_certified and is_current and is_complete and active_dossier:
                    return {
                        "scheme_id": scheme_id,
                        "canonical_name": scheme.canonical_name,
                        "maturity_state": SchemeMaturityState.FULLY_VERIFIED.value,
                        "reason": "All eligibility rules, semantic models, policy currentness, and certification dossier are verified",
                        "open_conflicts_count": 0,
                        "critical_rules_unverified": 0,
                        "is_fully_verified": True,
                        "dossier_id": active_dossier.id
                    }
                else:
                    pending_reasons = []
                    if not is_sem_certified:
                        pending_reasons.append("semantic certification pending")
                    if not is_current:
                        pending_reasons.append("latest policy currentness check pending")
                    if not is_complete:
                        pending_reasons.append("statutory rule completeness pending")
                    if not active_dossier:
                        pending_reasons.append("active certification dossier missing")
                    return {
                        "scheme_id": scheme_id,
                        "canonical_name": scheme.canonical_name,
                        "maturity_state": SchemeMaturityState.PARTIALLY_VERIFIED.value,
                        "reason": f"Source verified, but {', '.join(pending_reasons)}",
                        "open_conflicts_count": 0,
                        "critical_rules_unverified": 0,
                        "is_fully_verified": False
                    }

        if len(verified_rules) > 0 or len(human_rules) > 0:
            return {
                "scheme_id": scheme_id,
                "canonical_name": scheme.canonical_name,
                "maturity_state": SchemeMaturityState.PARTIALLY_VERIFIED.value,
                "reason": f"{len(verified_rules)} verified rules, but {len(unverified_critical)} critical rules unverified",
                "open_conflicts_count": 0,
                "critical_rules_unverified": len(unverified_critical),
                "is_fully_verified": False
            }

        if reviewed_changesets:
            return {
                "scheme_id": scheme_id,
                "canonical_name": scheme.canonical_name,
                "maturity_state": SchemeMaturityState.PARTIALLY_REVIEWED.value,
                "reason": f"Human review initiated ({len(reviewed_changesets)} changesets reviewed)",
                "open_conflicts_count": 0,
                "critical_rules_unverified": len(unverified_critical),
                "is_fully_verified": False
            }

        if pending_changesets:
            return {
                "scheme_id": scheme_id,
                "canonical_name": scheme.canonical_name,
                "maturity_state": SchemeMaturityState.MACHINE_EXTRACTED.value,
                "reason": f"{len(pending_changesets)} machine-extracted draft changeset(s) awaiting review",
                "open_conflicts_count": 0,
                "critical_rules_unverified": len(unverified_critical),
                "is_fully_verified": False
            }

        return {
            "scheme_id": scheme_id,
            "canonical_name": scheme.canonical_name,
            "maturity_state": SchemeMaturityState.PARSED.value,
            "reason": "Source snapshots parsed, candidate extraction pending",
            "open_conflicts_count": 0,
            "critical_rules_unverified": len(unverified_critical),
            "is_fully_verified": False
        }
