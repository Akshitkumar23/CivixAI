"""
Admin & Governance Router
Protected internal endpoints for source management, ingestion runs, review queue,
data quality audits, human approval/rejection, and verification metrics.
"""
from typing import Optional, List, Dict, Any
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Query
import os
import secrets
import logging
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from services.core.database import (
    get_db, SourceRegistry, SourceSnapshot, IngestionRun, SchemeChangeSet,
    Scheme, SchemeVersion, EligibilityRule, Benefit, DocumentRequirement,
    AuditLog, SourceConflict, DuplicateCandidate, SchemeCertificationDossier
)
from services.core.ingestion import (
    SourceRegistryService, IngestionPipeline, GovernancePublisher,
    DataQualityEngine, FreshnessEvaluator, TRUST_POLICIES,
    SemanticCertificationEngine
)
from services.core.ingestion.conflict_engine import SourceConflictEngine, ConflictResolutionType, VALID_RESOLUTION_TYPES
from services.core.auth import (
    AuthenticatedPrincipal, get_current_principal,
    require_governance_mutation, ADMIN_TOKEN
)
from services.core.ingestion.maturity import SchemeMaturityService, SchemeMaturityState, CRITICAL_FACT_KEYS
from services.core.ingestion.prioritization import VerificationPrioritizationEngine
from services.core.ingestion.precedence import SupersessionGovernanceEngine
from services.core.ingestion.conversion import BootstrapConversionWorkflow
from services.core.ingestion.coverage import CorpusCoverageService
from services.core.ingestion.reconciliation import SchemeReconciliationService

logger = logging.getLogger("civixai.admin_auth")

router = APIRouter(prefix="/v1/admin", tags=["admin-governance"])

ADMIN_TOKEN = os.getenv("CIVIX_ADMIN_TOKEN", "civix-admin-secret")
IS_PRODUCTION = os.getenv("CIVIX_ENV", "").lower() == "production"

def verify_admin_token(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> bool:
    """
    Hardened admin token verification:
    - Uses constant-time string comparison (secrets.compare_digest)
    - Supports X-Admin-Token and Authorization: Bearer
    - Safely logs unauthorized access attempts
    - Rejects invalid tokens in all environments
    """
    provided = x_admin_token
    if not provided and authorization:
        if authorization.startswith("Bearer "):
            provided = authorization[7:].strip()

    if provided:
        if secrets.compare_digest(provided, ADMIN_TOKEN):
            return True
        logger.warning("Failed admin authentication attempt from unauthorized caller.")
        raise HTTPException(status_code=403, detail="Invalid admin authorization token.")

    if IS_PRODUCTION:
        logger.warning("Rejected unauthenticated admin request in production environment.")
        raise HTTPException(status_code=401, detail="Admin authorization token required.")

    return True

def require_admin_token(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> bool:
    """Strictly requires valid admin token for mutation routes in all environments."""
    provided = x_admin_token
    if not provided and authorization:
        if authorization.startswith("Bearer "):
            provided = authorization[7:].strip()

    if not provided or not secrets.compare_digest(provided, ADMIN_TOKEN):
        logger.warning("Mutation governance route accessed without valid admin credentials.")
        raise HTTPException(status_code=403, detail="Admin authorization token required for governance mutations.")
    return True

# ── 1. Verification Coverage & System Health ─────────────────────────────────

@router.get("/verification-coverage")
def get_verification_coverage(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    total_schemes = db.query(Scheme).count()
    total_versions = db.query(SchemeVersion).count()
    total_rules = db.query(EligibilityRule).count()

    verified_rules = db.query(EligibilityRule).filter(
        EligibilityRule.verification_status.in_(["source_verified", "human_reviewed"])
    ).count()

    unverified_bootstrap_rules = db.query(EligibilityRule).filter(
        EligibilityRule.verification_status == "imported_unverified"
    ).count()

    rules_without_evidence = db.query(EligibilityRule).filter(
        (EligibilityRule.source_fragment == None) | (EligibilityRule.source_fragment == "")
    ).count()

    total_sources = db.query(SourceRegistry).count()
    stale_sources = db.query(SourceRegistry).filter(SourceRegistry.freshness_status == "stale").count()
    unreachable_sources = db.query(SourceRegistry).filter(SourceRegistry.freshness_status == "unreachable").count()
    pending_reviews = db.query(SchemeChangeSet).filter(SchemeChangeSet.status == "pending").count()

    # Semantic certification & RAG readiness metrics
    semantic_certified_count = db.query(SchemeVersion).filter(
        SchemeVersion.status == "published",
        SchemeVersion.semantic_review_status == "certified"
    ).count()

    active_dossiers_count = db.query(SchemeCertificationDossier).filter(
        SchemeCertificationDossier.is_active == True,
        SchemeCertificationDossier.semantic_review_status == "certified"
    ).count()

    rag_certified_count = 0
    cert_engine = SemanticCertificationEngine(db)
    published_versions = db.query(SchemeVersion).filter(SchemeVersion.status == "published").all()
    for pv in published_versions:
        ok, _ = cert_engine.is_rag_certified(pv, allow_institutional=False)
        if ok:
            rag_certified_count += 1

    coverage_pct = round((verified_rules / max(1, total_rules)) * 100, 1)

    return {
        "total_schemes": total_schemes,
        "total_versions": total_versions,
        "total_rules": total_rules,
        "verified_rules": verified_rules,
        "unverified_bootstrap_rules": unverified_bootstrap_rules,
        "rules_without_evidence": rules_without_evidence,
        "verification_coverage_pct": coverage_pct,
        "total_sources": total_sources,
        "stale_sources": stale_sources,
        "unreachable_sources": unreachable_sources,
        "pending_reviews": pending_reviews,
        "semantic_certified_schemes": semantic_certified_count,
        "active_certification_dossiers": active_dossiers_count,
        "rag_certified_citizen_schemes": rag_certified_count,
        "rag_readiness": "READY_FOR_VERIFIED_SUBSET" if rag_certified_count > 0 else "NOT_READY",
        "governance_claim": "Verification coverage reflects only rules with human/official source verification and semantic certification. Institutional grants are excluded from citizen RAG."
    }

# ── 2. Source Registry Management ─────────────────────────────────────────────

class RegisterSourcePayload(BaseModel):
    canonical_url: str
    publisher: str
    title: str
    trust_level: str = "B"
    source_type: str = "official_guideline"
    jurisdiction: str = "Central"
    authority_id: Optional[str] = None
    freshness_policy_days: Optional[int] = None

@router.get("/sources")
def list_sources(
    trust_level: Optional[str] = None,
    freshness_status: Optional[str] = None,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    service = SourceRegistryService(db)
    sources = service.list_sources(trust_level=trust_level, freshness_status=freshness_status)
    return [
        {
            "id": s.id,
            "canonical_url": s.canonical_url,
            "title": s.title,
            "publisher": s.publisher,
            "trust_level": s.trust_level,
            "source_type": s.source_type,
            "freshness_status": s.freshness_status,
            "last_checked_at": s.last_checked_at.isoformat() if s.last_checked_at else None,
            "last_changed_at": s.last_changed_at.isoformat() if s.last_changed_at else None,
            "current_hash": s.current_hash
        }
        for s in sources
    ]

@router.post("/sources")
def register_source(
    payload: RegisterSourcePayload,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    service = SourceRegistryService(db)
    source = service.register_source(
        canonical_url=payload.canonical_url,
        publisher=payload.publisher,
        title=payload.title,
        trust_level=payload.trust_level,
        source_type=payload.source_type,
        jurisdiction=payload.jurisdiction,
        authority_id=payload.authority_id,
        freshness_policy_days=payload.freshness_policy_days
    )
    return {"status": "success", "source_id": source.id, "canonical_url": source.canonical_url}

@router.get("/sources/{source_id}/snapshots")
def get_source_snapshots(
    source_id: str,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    snapshots = db.query(SourceSnapshot).filter(
        SourceSnapshot.source_registry_id == source_id
    ).order_by(desc(SourceSnapshot.fetched_at)).all()
    return [
        {
            "id": snap.id,
            "content_hash": snap.content_hash,
            "content_type": snap.content_type,
            "raw_size_bytes": snap.raw_size_bytes,
            "http_status": snap.http_status,
            "fetched_at": snap.fetched_at.isoformat() if snap.fetched_at else None,
            "is_duplicate": snap.is_duplicate
        }
        for snap in snapshots
    ]

# ── 3. Ingestion Runs & Triggering ─────────────────────────────────────────────

class IngestionRunPayload(BaseModel):
    source_ids: Optional[List[str]] = None

@router.get("/ingestion-runs")
def list_ingestion_runs(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    runs = db.query(IngestionRun).order_by(desc(IngestionRun.started_at)).limit(50).all()
    return [
        {
            "id": r.id,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "status": r.status,
            "sources_checked": r.sources_checked,
            "sources_changed": r.sources_changed,
            "changesets_created": r.changesets_created,
            "errors": json.loads(r.errors_json) if r.errors_json else []
        }
        for r in runs
    ]

@router.post("/ingestion-runs")
def trigger_ingestion_run(
    payload: IngestionRunPayload,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    pipeline = IngestionPipeline(db)
    run = pipeline.run_batch(source_ids=payload.source_ids)
    return {
        "status": "success",
        "run_id": run.id,
        "sources_checked": run.sources_checked,
        "sources_changed": run.sources_changed,
        "changesets_created": run.changesets_created
    }

# ── 4. Human Review Queue & Decisions ─────────────────────────────────────────

@router.get("/review-queue")
def list_review_queue(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    query = db.query(SchemeChangeSet)
    if status:
        query = query.filter(SchemeChangeSet.status == status)
    else:
        query = query.filter(SchemeChangeSet.status.in_(["pending", "in_review", "pending_governance_signoff", "certified"]))
    changesets = query.order_by(desc(SchemeChangeSet.created_at)).all()

    items = []
    for cs in changesets:
        scheme = cs.scheme
        source = cs.source_snapshot.source_registry if cs.source_snapshot else None
        diff_data = json.loads(cs.structured_diff_json) if cs.structured_diff_json else {}
        quality_data = json.loads(cs.quality_report_json) if cs.quality_report_json else {}

        items.append({
            "id": cs.id,
            "scheme_id": cs.scheme_id,
            "scheme_name": scheme.canonical_name if scheme else cs.scheme_id,
            "source_title": source.title if source else "Unknown Source",
            "source_url": source.canonical_url if source else None,
            "trust_level": source.trust_level if source else "C",
            "status": cs.status,
            "summary": cs.change_summary or diff_data.get("summary", ""),
            "has_material_changes": diff_data.get("has_material_changes", True),
            "quality_critical_count": quality_data.get("critical_count", 0),
            "quality_warning_count": quality_data.get("warning_count", 0),
            "rules_count": len(cs.rule_drafts),
            "created_at": cs.created_at.isoformat() if cs.created_at else None
        })
    return items

@router.get("/review-queue/{changeset_id}")
def get_review_item(
    changeset_id: str,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    cs = db.query(SchemeChangeSet).filter(SchemeChangeSet.id == changeset_id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="Changeset not found.")

    scheme = cs.scheme
    source = cs.source_snapshot.source_registry if cs.source_snapshot else None
    diff_data = json.loads(cs.structured_diff_json) if cs.structured_diff_json else {}
    quality_data = json.loads(cs.quality_report_json) if cs.quality_report_json else {}

    return {
        "id": cs.id,
        "scheme_id": cs.scheme_id,
        "scheme_name": scheme.canonical_name if scheme else cs.scheme_id,
        "status": cs.status,
        "source": {
            "title": source.title if source else "Unknown",
            "canonical_url": source.canonical_url if source else None,
            "trust_level": source.trust_level if source else "C",
            "publisher": source.publisher if source else "Unknown"
        },
        "summary": cs.change_summary,
        "structured_diff": diff_data,
        "quality_report": quality_data,
        "rule_drafts": [
            {
                "id": r.id,
                "fact_key": r.fact_key,
                "operator": r.operator,
                "expected_value": r.expected_value,
                "mandatory": r.mandatory,
                "source_fragment": r.source_fragment,
                "change_type": r.change_type
            }
            for r in cs.rule_drafts
        ],
        "benefit_drafts": [
            {
                "id": b.id,
                "benefit_type": b.benefit_type,
                "fixed_amount": b.fixed_amount,
                "frequency": b.frequency,
                "description": b.description,
                "source_fragment": b.source_fragment
            }
            for b in cs.benefit_drafts
        ],
        "document_drafts": [
            {
                "id": d.id,
                "document_type": d.document_type,
                "is_mandatory": d.is_mandatory,
                "source_fragment": d.source_fragment
            }
            for d in cs.document_drafts
        ],
        "review_notes": cs.review_notes,
        "reviewed_by": cs.reviewed_by,
        "reviewed_at": cs.reviewed_at.isoformat() if cs.reviewed_at else None
    }

class ApproveDecisionPayload(BaseModel):
    reviewer_id: str = "compliance_officer"
    review_notes: str = "Verified against official gazette/guidelines."
    promote_to_source_verified: bool = True

@router.post("/review-queue/{changeset_id}/approve")
def approve_changeset(
    changeset_id: str,
    payload: ApproveDecisionPayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    publisher = GovernancePublisher(db)
    try:
        reviewer = principal.actor_id if principal.actor_id != "dev_admin" else (payload.reviewer_id or "dev_admin")
        role = principal.role if principal.role in ("compliance_officer", "legal_reviewer", "lead_compliance_officer") else "compliance_officer"
        new_version = publisher.approve_and_publish(
            changeset_id=changeset_id,
            reviewer_id=reviewer,
            is_authenticated_human=True,
            governance_role=role,
            review_notes=payload.review_notes,
            promote_to_source_verified=payload.promote_to_source_verified
        )
        return {
            "status": "approved",
            "new_version_id": new_version.id,
            "version_number": new_version.version_number,
            "verification_status": new_version.verification_status,
            "published_at": new_version.published_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class RejectDecisionPayload(BaseModel):
    reviewer_id: str = "compliance_officer"
    reason: str = "Document evidence mismatch"
    review_notes: str = "Extracted income ceiling contradicts Gazette paragraph 4(b)."

@router.post("/review-queue/{changeset_id}/reject")
def reject_changeset(
    changeset_id: str,
    payload: RejectDecisionPayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    publisher = GovernancePublisher(db)
    reviewer = principal.actor_id if principal.actor_id != "dev_admin" else (payload.reviewer_id or "dev_admin")
    try:
        cs = publisher.reject_changeset(
            changeset_id=changeset_id,
            reviewer_id=reviewer,
            reason=payload.reason,
            review_notes=payload.review_notes
        )
        return {
            "status": "rejected",
            "changeset_id": cs.id,
            "review_notes": cs.review_notes
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── 5. System Data Quality & Audit Trail ──────────────────────────────────────

@router.get("/data-quality")
def run_system_data_quality_audit(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    versions = db.query(SchemeVersion).filter(SchemeVersion.status == "published").all()
    all_violations = []

    for v in versions:
        report = DataQualityEngine.audit_scheme_version(v)
        if report.violations:
            all_violations.append({
                "scheme_id": v.scheme_id,
                "version_number": v.version_number,
                "critical_count": len(report.critical_errors),
                "warning_count": len(report.warnings),
                "violations": [vio.to_dict() for vio in report.violations]
            })

    return {
        "audited_versions_count": len(versions),
        "versions_with_issues": len(all_violations),
        "findings": all_violations
    }

@router.get("/audit-logs")
def list_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
    return [
        {
            "id": a.id,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "action": a.action,
            "actor_id": a.actor_id,
            "reason": a.reason,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in logs
    ]

# ── 6. Live Corpus Health & Source Conflict Endpoints ─────────────────────────

@router.get("/corpus-health")
def get_corpus_health(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Returns live, verified database counts across schemes, official sources,
    ingestion outcomes, parser health, conflicts, and verification coverage.
    """
    total_schemes = db.query(Scheme).count()
    active_schemes = db.query(Scheme).filter(Scheme.is_active == True).count()
    total_versions = db.query(SchemeVersion).count()
    published_versions = db.query(SchemeVersion).filter(SchemeVersion.status == "published").count()
    archived_versions = db.query(SchemeVersion).filter(SchemeVersion.status == "archived").count()

    total_sources = db.query(SourceRegistry).count()
    trust_a = db.query(SourceRegistry).filter(SourceRegistry.trust_level == "A").count()
    trust_b = db.query(SourceRegistry).filter(SourceRegistry.trust_level == "B").count()
    trust_c = db.query(SourceRegistry).filter(SourceRegistry.trust_level == "C").count()

    fetch_success = db.query(SourceRegistry).filter(SourceRegistry.last_fetch_status == "success").count()
    fetch_not_mod = db.query(SourceRegistry).filter(SourceRegistry.last_fetch_status == "not_modified").count()
    fetch_unreachable = db.query(SourceRegistry).filter(SourceRegistry.last_fetch_status.in_(["unreachable", "timeout", "failed"])).count()
    fetch_pending = db.query(SourceRegistry).filter(SourceRegistry.last_fetch_status == "not_attempted").count()

    ocr_req = db.query(SourceRegistry).filter(SourceRegistry.parser_health == "ocr_required").count()
    parser_fail = db.query(SourceRegistry).filter(SourceRegistry.parser_health == "failed").count()

    fresh_count = db.query(SourceRegistry).filter(SourceRegistry.freshness_status == "fresh").count()
    stale_count = db.query(SourceRegistry).filter(SourceRegistry.freshness_status == "stale").count()
    changed_count = db.query(SourceRegistry).filter(SourceRegistry.freshness_status == "source_changed").count()

    # Rule verification stats
    total_rules = db.query(EligibilityRule).count()
    rules_unverified = db.query(EligibilityRule).filter(EligibilityRule.verification_status == "imported_unverified").count()
    rules_verified = db.query(EligibilityRule).filter(EligibilityRule.verification_status == "source_verified").count()
    rules_human = db.query(EligibilityRule).filter(EligibilityRule.verification_status == "human_reviewed").count()

    # Benefit & doc stats
    total_benefits = db.query(Benefit).count()
    benefits_verified = db.query(Benefit).filter(Benefit.verification_status == "source_verified").count()
    benefits_unverified = db.query(Benefit).filter(Benefit.verification_status == "imported_unverified").count()

    total_docs = db.query(DocumentRequirement).count()
    docs_verified = db.query(DocumentRequirement).filter(DocumentRequirement.verification_status == "source_verified").count()
    docs_unverified = db.query(DocumentRequirement).filter(DocumentRequirement.verification_status == "imported_unverified").count()

    # Conflicts & changesets
    open_conflicts = db.query(SourceConflict).filter(SourceConflict.status == "SOURCE_CONFLICT_OPEN").count()
    resolved_conflicts = db.query(SourceConflict).filter(SourceConflict.status == "SOURCE_CONFLICT_RESOLVED").count()
    pending_changesets = db.query(SchemeChangeSet).filter(SchemeChangeSet.status == "pending").count()

    return {
        "schemes": {
            "total": total_schemes,
            "active": active_schemes,
            "versions_total": total_versions,
            "published_versions": published_versions,
            "archived_versions": archived_versions
        },
        "sources": {
            "total_registered": total_sources,
            "tier_a": trust_a,
            "tier_b": trust_b,
            "tier_c": trust_c,
            "fetch_successful": fetch_success,
            "fetch_not_modified": fetch_not_mod,
            "fetch_unreachable": fetch_unreachable,
            "fetch_pending": fetch_pending,
            "ocr_required": ocr_req,
            "parser_failed": parser_fail,
            "fresh": fresh_count,
            "stale": stale_count,
            "source_changed": changed_count
        },
        "rules": {
            "total": total_rules,
            "imported_unverified": rules_unverified,
            "source_verified": rules_verified,
            "human_reviewed": rules_human
        },
        "benefits": {
            "total": total_benefits,
            "source_verified": benefits_verified,
            "imported_unverified": benefits_unverified
        },
        "document_requirements": {
            "total": total_docs,
            "source_verified": docs_verified,
            "imported_unverified": docs_unverified
        },
        "governance": {
            "open_conflicts": open_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "pending_changesets": pending_changesets
        }
    }

@router.get("/conflicts")
def list_source_conflicts(
    status: Optional[str] = Query(None, description="Filter by status: SOURCE_CONFLICT_OPEN or SOURCE_CONFLICT_RESOLVED"),
    scheme_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    query = db.query(SourceConflict)
    if status:
        query = query.filter(SourceConflict.status == status)
    if scheme_id:
        query = query.filter(SourceConflict.scheme_id == scheme_id)
    conflicts = query.order_by(desc(SourceConflict.created_at)).all()
    return [
        {
            "id": c.id,
            "scheme_id": c.scheme_id,
            "conflict_type": c.conflict_type,
            "status": c.status,
            "disputed_fact_key": c.disputed_fact_key,
            "source_a_title": c.source_a_title,
            "source_a_value": c.source_a_value,
            "source_b_title": c.source_b_title,
            "source_b_value": c.source_b_value,
            "resolution_notes": c.resolution_notes,
            "resolved_by": c.resolved_by,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None
        }
        for c in conflicts
    ]

class ResolveConflictPayload(BaseModel):
    reviewer_id: Optional[str] = "compliance_officer"
    resolution_type: str = Field(default="SOURCE_A_PREVAILS", description="SOURCE_A_PREVAILS, SOURCE_B_PREVAILS, BOTH_APPLY_DIFFERENT_CONTEXT, SUPERSEDED, INSUFFICIENT_EVIDENCE")
    resolution_notes: str = Field(..., description="Documented justification for conflict resolution")
    winning_evidence: Optional[str] = None
    review_analysis: Optional[str] = None

@router.post("/conflicts/{conflict_id}/resolve")
def resolve_source_conflict(
    conflict_id: str,
    payload: ResolveConflictPayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    engine = SourceConflictEngine(db)
    reviewer = principal.actor_id if principal.actor_id != "dev_admin" else (payload.reviewer_id or "dev_admin")
    try:
        resolved = engine.resolve_conflict(
            conflict_id=conflict_id,
            resolved_by=reviewer,
            resolution_type=payload.resolution_type,
            resolution_notes=payload.resolution_notes,
            winning_evidence=payload.winning_evidence,
            review_analysis=payload.review_analysis
        )
        return {
            "status": "resolved",
            "conflict_id": resolved.id,
            "resolution_type": resolved.resolution_type,
            "resolved_by": resolved.resolved_by,
            "resolution_notes": resolved.resolution_notes,
            "resolved_at": resolved.resolved_at.isoformat() if resolved.resolved_at else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── 7. Corpus Coverage Matrix & Discovery Queue ───────────────────────────────

@router.get("/corpus-coverage-matrix")
def get_corpus_coverage_matrix(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Returns database-backed coverage record and maturity state for every scheme.
    Zero synthetic metrics.
    """
    maturity_service = SchemeMaturityService(db)
    schemes = db.query(Scheme).all()
    matrix = []

    for s in schemes:
        cur_v = db.query(SchemeVersion).filter(
            SchemeVersion.scheme_id == s.id,
            SchemeVersion.status == "published"
        ).order_by(SchemeVersion.version_number.desc()).first()

        sources = db.query(SourceRegistry).filter(
            SourceRegistry.title.ilike(f"%{s.canonical_name[:20]}%")
        ).all()
        version_sources = cur_v.sources if cur_v else []
        total_sources = len(sources) + len(version_sources)

        source_ids = [src.id for src in sources]
        snapshots = db.query(SourceSnapshot).filter(
            SourceSnapshot.source_registry_id.in_(source_ids)
        ).all() if source_ids else []
        has_snapshot = (len(snapshots) > 0) or any(src.snapshot_id for src in version_sources)

        parser_health = "none"
        if sources:
            if any(src.parser_health == "ocr_required" for src in sources):
                parser_health = "ocr_required"
            elif any(src.parser_health == "failed" for src in sources):
                parser_health = "failed"
            elif any(src.parser_health == "complete" for src in sources):
                parser_health = "complete"
            elif any(src.parser_health == "partial" for src in sources):
                parser_health = "partial"

        freshness = "unknown"
        if sources:
            freshness = sources[0].freshness_status

        rules = cur_v.rules if cur_v else []
        benefits = cur_v.benefits if cur_v else []
        docs = cur_v.documents if cur_v else []

        open_conflicts = db.query(SourceConflict).filter(
            SourceConflict.scheme_id == s.id,
            SourceConflict.status == "SOURCE_CONFLICT_OPEN"
        ).count()

        pending_items = db.query(SchemeChangeSet).filter(
            SchemeChangeSet.scheme_id == s.id,
            SchemeChangeSet.status == "pending"
        ).count()

        mat_res = maturity_service.evaluate_scheme_maturity(s.id)

        matrix.append({
            "scheme_id": s.id,
            "canonical_name": s.canonical_name,
            "official_source_identified": total_sources > 0,
            "number_of_registered_sources": total_sources,
            "successful_snapshot_available": has_snapshot,
            "parser_health": parser_health,
            "current_source_freshness": freshness,
            "eligibility_rules_total": len(rules),
            "eligibility_rules_verified": sum(1 for r in rules if r.verification_status in ("source_verified", "human_reviewed")),
            "benefits_total": len(benefits),
            "benefits_verified": sum(1 for b in benefits if b.verification_status == "source_verified"),
            "document_requirements_total": len(docs),
            "document_requirements_verified": sum(1 for d in docs if d.verification_status == "source_verified"),
            "open_conflicts": open_conflicts,
            "pending_review_items": pending_items,
            "current_verification_maturity": mat_res["maturity_state"],
            "maturity_reason": mat_res["reason"]
        })

    return matrix

@router.get("/discovery-queue")
def get_source_discovery_queue(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Categorizes all schemes across source discovery availability:
    - Authoritative source (Tier A/B)
    - Only secondary source (Tier C/D)
    - No source registered
    - Broken source URL
    - Stale source
    """
    schemes = db.query(Scheme).all()
    with_auth = []
    only_secondary = []
    no_source = []
    broken_source = []
    stale_source = []

    for s in schemes:
        sources = db.query(SourceRegistry).filter(
            SourceRegistry.title.ilike(f"%{s.canonical_name[:20]}%")
        ).all()

        if not sources:
            no_source.append({"scheme_id": s.id, "name": s.canonical_name})
            continue

        has_a_b = any(src.trust_level in ("A", "B") for src in sources)
        if has_a_b:
            with_auth.append({"scheme_id": s.id, "name": s.canonical_name, "sources_count": len(sources)})
        else:
            only_secondary.append({"scheme_id": s.id, "name": s.canonical_name, "sources_count": len(sources)})

        if any(src.last_fetch_status in ("timeout", "unreachable", "failed") or (src.last_fetch_status and "HTTP 4" in src.last_fetch_status) for src in sources):
            broken_source.append({"scheme_id": s.id, "name": s.canonical_name})

        if any(src.freshness_status in ("stale", "unreachable") for src in sources):
            stale_source.append({"scheme_id": s.id, "name": s.canonical_name})

    return {
        "summary": {
            "total_schemes": len(schemes),
            "with_authoritative_source": len(with_auth),
            "with_only_secondary_source": len(only_secondary),
            "with_no_source": len(no_source),
            "with_broken_source": len(broken_source),
            "with_stale_source": len(stale_source)
        },
        "queues": {
            "missing_authoritative_source": no_source + only_secondary,
            "broken_source_urls": broken_source,
            "stale_sources": stale_source
        }
    }

@router.get("/verification-priorities")
def get_verification_priorities(
    limit: int = Query(25, ge=1, le=135),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Returns ranked verification priorities using deterministic risk-weighted scoring.
    Zero hardcoded scheme names.
    """
    engine = VerificationPrioritizationEngine(db)
    return engine.get_ranked_schemes_for_verification(limit=limit)

# ── 8. Supersession Governance Endpoints ──────────────────────────────────────

class ProposeSupersessionPayload(BaseModel):
    superseded_source_id: str
    notes: str = "Candidate newer statutory notification detected"

@router.post("/supersessions/{source_id}/propose")
def propose_source_supersession(
    source_id: str,
    payload: ProposeSupersessionPayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    engine = SupersessionGovernanceEngine(db)
    try:
        src = engine.propose_supersession(
            new_source_id=source_id,
            superseded_source_id=payload.superseded_source_id,
            proposer_id=principal.actor_id,
            notes=payload.notes
        )
        return {
            "status": "proposed",
            "source_id": src.id,
            "supersedes_source_id": src.supersedes_source_id,
            "supersession_status": src.supersession_status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class ConfirmSupersessionPayload(BaseModel):
    resolution_notes: str = "Confirmed: newer order repeals former circular"

@router.post("/supersessions/{source_id}/confirm")
def confirm_source_supersession(
    source_id: str,
    payload: ConfirmSupersessionPayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    engine = SupersessionGovernanceEngine(db)
    try:
        src = engine.confirm_supersession(
            new_source_id=source_id,
            reviewer_id=principal.actor_id,
            resolution_notes=payload.resolution_notes
        )
        return {
            "status": "confirmed",
            "source_id": src.id,
            "supersession_status": src.supersession_status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class RejectSupersessionPayload(BaseModel):
    rejection_reason: str = "Different jurisdiction or co-existing guidelines"

@router.post("/supersessions/{source_id}/reject")
def reject_source_supersession(
    source_id: str,
    payload: RejectSupersessionPayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    engine = SupersessionGovernanceEngine(db)
    try:
        src = engine.reject_supersession(
            new_source_id=source_id,
            reviewer_id=principal.actor_id,
            rejection_reason=payload.rejection_reason
        )
        return {
            "status": "rejected",
            "source_id": src.id,
            "supersession_status": src.supersession_status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── 9. Bootstrap Conversion Endpoints (Rules, Benefits, Documents) ────────────

class ConvertRulePayload(BaseModel):
    outcome: str = Field(..., description="confirmed_and_reviewed, modified_by_official_source, superseded, still_unverified, conflicted, removed_as_invalid")
    notes: str = "Audited against Section 3(a) of gazette notification"
    source_evidence_id: Optional[str] = None
    source_fragment: Optional[str] = None
    modified_operator: Optional[str] = None
    modified_expected_value: Optional[str] = None

@router.post("/conversion/rule/{rule_id}")
def convert_bootstrap_rule(
    rule_id: str,
    payload: ConvertRulePayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    workflow = BootstrapConversionWorkflow(db)
    try:
        res = workflow.convert_rule(
            rule_id=rule_id,
            outcome=payload.outcome,
            reviewer_id=principal.actor_id,
            notes=payload.notes,
            source_evidence_id=payload.source_evidence_id,
            source_fragment=payload.source_fragment,
            modified_operator=payload.modified_operator,
            modified_expected_value=payload.modified_expected_value
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class ConvertBenefitPayload(BaseModel):
    notes: str = "Verified financial payout from ministry guidelines"
    source_evidence_id: Optional[str] = None
    verified_details: Optional[Dict[str, Any]] = None

@router.post("/conversion/benefit/{benefit_id}")
def convert_bootstrap_benefit(
    benefit_id: str,
    payload: ConvertBenefitPayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    workflow = BootstrapConversionWorkflow(db)
    try:
        res = workflow.convert_benefit(
            benefit_id=benefit_id,
            reviewer_id=principal.actor_id,
            notes=payload.notes,
            source_evidence_id=payload.source_evidence_id,
            verified_details=payload.verified_details
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class ConvertDocumentPayload(BaseModel):
    notes: str = "Verified document requirement from official application checklist"
    requirement_category: str = "mandatory"
    requirement_stage: str = "application_stage"
    source_evidence_id: Optional[str] = None
    alternatives: Optional[str] = None

@router.post("/conversion/document/{doc_id}")
def convert_bootstrap_document(
    doc_id: str,
    payload: ConvertDocumentPayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    workflow = BootstrapConversionWorkflow(db)
    try:
        res = workflow.convert_document(
            doc_req_id=doc_id,
            reviewer_id=principal.actor_id,
            notes=payload.notes,
            requirement_category=payload.requirement_category,
            requirement_stage=payload.requirement_stage,
            source_evidence_id=payload.source_evidence_id,
            alternatives=payload.alternatives
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class ResolveDuplicatePayload(BaseModel):
    status: str = "confirmed_distinct" # confirmed_duplicate, confirmed_distinct, merged, archived
    review_notes: str = ""

@router.get("/reconciliation/report")
def get_scheme_reconciliation_report(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Produces the formal Scheme Count Reconciliation Report (135 vs 157).
    Audits every scheme created after the baseline migration.
    """
    recon_service = SchemeReconciliationService(db)
    return recon_service.get_full_reconciliation_report()

@router.get("/duplicate-candidates")
def list_duplicate_candidates(
    status: Optional[str] = Query(None, description="Filter by candidate status (e.g. pending_review)"),
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Returns reviewable duplicate candidates. Zero destructive automatic merges.
    """
    query = db.query(DuplicateCandidate)
    if status:
        query = query.filter(DuplicateCandidate.status == status)
    return query.all()

@router.post("/duplicate-candidates/{candidate_id}/resolve")
def resolve_duplicate_candidate(
    candidate_id: str,
    payload: ResolveDuplicatePayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    """
    Governed human resolution for duplicate candidates.
    """
    cand = db.query(DuplicateCandidate).filter(DuplicateCandidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail=f"Duplicate candidate '{candidate_id}' not found")

    cand.status = payload.status
    cand.review_notes = payload.review_notes
    cand.reviewed_by = principal.actor_id
    cand.reviewed_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        id=f"aud-dup-{uuid.uuid4().hex[:10]}",
        entity_type="DuplicateCandidate",
        entity_id=candidate_id,
        action="RESOLVE_DUPLICATE_CANDIDATE",
        actor_id=principal.actor_id,
        previous_state_json=json.dumps({"status": "pending_review"}),
        new_state_json=json.dumps({"status": payload.status, "notes": payload.review_notes}),
        reason=payload.review_notes,
        created_at=datetime.now(timezone.utc)
    ))
    db.commit()
    return {"id": candidate_id, "status": cand.status, "reviewed_by": cand.reviewed_by}

@router.post("/reconciliation/archive-test-artifacts")
def archive_test_artifacts_endpoint(
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    """
    Safely archives test fixture schemes and test conflicts in data/civix.db with audit logging,
    restoring the active canonical schemes count to exactly 135.
    """
    recon_service = SchemeReconciliationService(db)
    res = recon_service.archive_test_artifacts(
        reviewed_by=principal.actor_id,
        reason="Governed archival of test suite execution artifacts"
    )
    return res


# ── 12. Semantic Certification Dossiers ──────────────────────────────────────

class CertifySchemePayload(BaseModel):
    applicant_type: str = "individual"
    beneficiary_type: str = "individual"
    audience_type: str = "DIRECT_CITIZEN_BENEFIT"
    latest_source_reference: Optional[str] = None
    notes: Optional[str] = None

@router.get("/semantic-dossiers")
def list_semantic_dossiers(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    dossiers = db.query(SchemeCertificationDossier).filter(
        SchemeCertificationDossier.is_active == True
    ).order_by(SchemeCertificationDossier.certified_at.desc()).all()
    
    cert_engine = SemanticCertificationEngine(db)
    items = []
    for d in dossiers:
        rag_ok, rag_reason = cert_engine.is_rag_certified(d.scheme_version_id, allow_institutional=False)
        items.append({
            "dossier_id": d.id,
            "scheme_id": d.scheme_id,
            "scheme_version_id": d.scheme_version_id,
            "applicant_type": d.applicant_type,
            "beneficiary_type": d.beneficiary_type,
            "audience_type": d.audience_type,
            "semantic_review_status": d.semantic_review_status,
            "completeness_status": d.completeness_status,
            "currentness_status": d.currentness_status,
            "certification_hash": d.certification_hash,
            "certified_at": d.certified_at.isoformat() if d.certified_at else None,
            "certified_by": d.certified_by,
            "is_rag_certified_for_citizens": rag_ok,
            "rag_reason": rag_reason
        })
    return {"total": len(items), "dossiers": items}

@router.get("/semantic-dossiers/{scheme_id}")
def get_semantic_dossier(
    scheme_id: str,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_admin_token)
):
    dossier = db.query(SchemeCertificationDossier).filter(
        SchemeCertificationDossier.scheme_id == scheme_id,
        SchemeCertificationDossier.is_active == True
    ).order_by(SchemeCertificationDossier.certified_at.desc()).first()

    if not dossier:
        raise HTTPException(status_code=404, detail=f"No active certification dossier found for scheme '{scheme_id}'")

    cert_engine = SemanticCertificationEngine(db)
    rag_ok, rag_reason = cert_engine.is_rag_certified(dossier.scheme_version_id, allow_institutional=False)

    return {
        "dossier_id": dossier.id,
        "scheme_id": dossier.scheme_id,
        "scheme_version_id": dossier.scheme_version_id,
        "applicant_type": dossier.applicant_type,
        "beneficiary_type": dossier.beneficiary_type,
        "audience_type": dossier.audience_type,
        "latest_source_reference": dossier.latest_source_reference,
        "semantic_review_status": dossier.semantic_review_status,
        "completeness_status": dossier.completeness_status,
        "currentness_status": dossier.currentness_status,
        "certification_hash": dossier.certification_hash,
        "certified_at": dossier.certified_at.isoformat() if dossier.certified_at else None,
        "certified_by": dossier.certified_by,
        "is_rag_certified_for_citizens": rag_ok,
        "rag_reason": rag_reason,
        "open_findings": json.loads(dossier.open_findings_json or "[]"),
        "notes": dossier.notes
    }

@router.post("/semantic-dossiers/{scheme_id}/certify")
def certify_scheme_endpoint(
    scheme_id: str,
    payload: CertifySchemePayload,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(require_governance_mutation)
):
    version = db.query(SchemeVersion).filter(
        SchemeVersion.scheme_id == scheme_id,
        SchemeVersion.status == "published"
    ).order_by(SchemeVersion.version_number.desc()).first()

    if not version:
        raise HTTPException(status_code=404, detail=f"No published version found for scheme '{scheme_id}'")

    cert_engine = SemanticCertificationEngine(db)
    dossier = cert_engine.certify_scheme_version(
        scheme_id=scheme_id,
        version_id=version.id,
        certified_by=principal.actor_id,
        applicant_type=payload.applicant_type,
        beneficiary_type=payload.beneficiary_type,
        audience_type=payload.audience_type,
        latest_source_reference=payload.latest_source_reference,
        notes=payload.notes
    )

    rag_ok, rag_reason = cert_engine.is_rag_certified(version.id, allow_institutional=False)

    return {
        "status": "success",
        "dossier_id": dossier.id,
        "scheme_id": scheme_id,
        "version_id": version.id,
        "semantic_review_status": dossier.semantic_review_status,
        "completeness_status": dossier.completeness_status,
        "currentness_status": dossier.currentness_status,
        "certification_hash": dossier.certification_hash,
        "is_rag_certified_for_citizens": rag_ok,
        "rag_reason": rag_reason
    }

