from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utcnow():
    return datetime.now(timezone.utc)

# ── 1. Authorities & Categories ───────────────────────────────────────────────

class Authority(Base):
    __tablename__ = "authorities"

    id = Column(String(64), primary_key=True)  # e.g. "mohua", "moa_fw"
    name = Column(String(255), nullable=False)
    level = Column(String(32), default="Central")  # Central or State
    state = Column(String(64), nullable=True)     # None for Central, state name for State
    portal_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    schemes = relationship("Scheme", back_populates="authority")


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(64), primary_key=True)  # e.g. "agriculture", "education", "housing"
    name = Column(String(128), nullable=False)
    slug = Column(String(64), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    schemes = relationship("Scheme", back_populates="category")


# ── 2. Canonical Scheme & Versioning ──────────────────────────────────────────

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(String(128), primary_key=True)  # e.g. "pm-kisan", "pmay-u"
    canonical_name = Column(String(255), nullable=False)
    authority_id = Column(String(64), ForeignKey("authorities.id"), nullable=True)
    category_id = Column(String(64), ForeignKey("categories.id"), nullable=True)
    scheme_level = Column(String(32), default="Central")  # Central, State
    programme_kind = Column(String(32), default="welfare") # welfare, loan, insurance
    status = Column(String(32), default="active")          # active, draft, archived
    is_active = Column(Boolean, default=True)
    current_version_number = Column(Integer, default=1)
    popularity_score = Column(Float, default=5.0)
    applicant_type = Column(String(64), default="individual")
    beneficiary_type = Column(String(64), default="individual")
    audience_type = Column(String(64), default="DIRECT_CITIZEN_BENEFIT")
    lifecycle_status = Column(String(32), default="ACTIVE")  # ACTIVE, PAUSED, CLOSED, WITHDRAWN, SUBSUMED, SUPERSEDED, HISTORICAL
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_schemes_status_active", "status", "is_active"),
        Index("ix_schemes_programme_kind", "programme_kind"),
        Index("ix_schemes_audience_type", "audience_type"),
        Index("ix_schemes_lifecycle_active", "lifecycle_status", "is_active"),
    )

    authority = relationship("Authority", back_populates="schemes")
    category = relationship("Category", back_populates="schemes")
    versions = relationship("SchemeVersion", back_populates="scheme", cascade="all, delete-orphan")
    dossiers = relationship("SchemeCertificationDossier", back_populates="scheme", cascade="all, delete-orphan", foreign_keys="SchemeCertificationDossier.scheme_id")
    rag_documents = relationship("RagDocument", back_populates="scheme", cascade="all, delete-orphan", foreign_keys="RagDocument.scheme_id")


class SchemeVersion(Base):
    __tablename__ = "scheme_versions"

    id = Column(String(128), primary_key=True)  # e.g. "pm-kisan-v1"
    scheme_id = Column(String(128), ForeignKey("schemes.id"), nullable=False)
    version_number = Column(Integer, default=1)
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    published_at = Column(DateTime, default=utcnow)
    verified_at = Column(DateTime, default=utcnow)
    status = Column(String(32), default="published")  # published, review, draft
    verification_status = Column(String(32), default="imported_unverified") # imported_unverified, machine_extracted, human_reviewed, source_verified, superseded
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(64), nullable=True)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    application_url = Column(String(512), nullable=True)
    source_url = Column(String(512), nullable=True)
    source_hash = Column(String(128), nullable=True)
    processing_time = Column(String(64), nullable=True)
    applicant_type = Column(String(64), default="individual")
    beneficiary_type = Column(String(64), default="individual")
    audience_type = Column(String(64), default="DIRECT_CITIZEN_BENEFIT")
    allow_institutional = Column(Boolean, default=False)
    semantic_review_status = Column(String(32), default="not_reviewed") # not_reviewed, machine_checked, human_reviewed, certified, rejected
    currentness_status = Column(String(32), default="unknown")          # current, possibly_stale, superseded, future_effective, unknown
    completeness_status = Column(String(32), default="incomplete")      # incomplete, partial, complete

    __table_args__ = (
        Index("ix_scheme_versions_scheme_num", "scheme_id", "version_number"),
        Index("ix_scheme_versions_verification", "verification_status"),
        Index("ix_scheme_versions_semantic", "semantic_review_status", "currentness_status"),
    )

    scheme = relationship("Scheme", back_populates="versions")
    rules = relationship("EligibilityRule", back_populates="scheme_version", cascade="all, delete-orphan")
    benefits = relationship("Benefit", back_populates="scheme_version", cascade="all, delete-orphan")
    documents = relationship("DocumentRequirement", back_populates="scheme_version", cascade="all, delete-orphan")
    sources = relationship("SourceDocument", back_populates="scheme_version", cascade="all, delete-orphan", foreign_keys="SourceDocument.scheme_version_id")
    dossiers = relationship("SchemeCertificationDossier", back_populates="scheme_version", cascade="all, delete-orphan", foreign_keys="SchemeCertificationDossier.scheme_version_id")
    rag_documents = relationship("RagDocument", back_populates="scheme_version", cascade="all, delete-orphan", foreign_keys="RagDocument.scheme_version_id")


# ── 3. Source Documents & Authoritative Provenance ─────────────────────────────

class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_version_id = Column(String(128), ForeignKey("scheme_versions.id"), nullable=False)
    url = Column(String(512), nullable=False)
    document_title = Column(String(255), nullable=True)
    publisher = Column(String(255), nullable=True)
    source_fragment = Column(String(255), nullable=True) # e.g. "Section 4.1 Eligibility Guidelines"
    content_hash = Column(String(128), nullable=True)
    fetched_at = Column(DateTime, default=utcnow)
    published_date = Column(DateTime, nullable=True)
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    document_type = Column(String(64), default="guideline") # gazette, portal, guideline, press_release
    trust_level = Column(String(16), default="A")          # A (Gazette/Govt), B (myScheme), C (Press), D (Secondary)
    verification_status = Column(String(32), default="imported_unverified") # imported_unverified, machine_extracted, human_reviewed, source_verified, superseded
    freshness_status = Column(String(32), default="fresh") # fresh, needs_recheck, source_changed, stale
    superseded_by_id = Column(String(128), ForeignKey("source_documents.id"), nullable=True)
    supersession_status = Column(String(32), default="none") # none, proposed, confirmed, rejected
    snapshot_id = Column(String(128), nullable=True) # Immutable ingested snapshot hash/tag

    __table_args__ = (
        Index("ix_sources_url_hash", "url", "content_hash"),
        Index("ix_sources_trust_level", "trust_level"),
    )

    scheme_version = relationship("SchemeVersion", back_populates="sources", foreign_keys=[scheme_version_id])
    rules = relationship("EligibilityRule", back_populates="source_evidence")


# ── 4. Declarative Rules, Benefits & Documents with Evidence Links ─────────────

class EligibilityRule(Base):
    __tablename__ = "eligibility_rules"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_version_id = Column(String(128), ForeignKey("scheme_versions.id"), nullable=False)
    source_evidence_id = Column(String(128), ForeignKey("source_documents.id"), nullable=True)
    source_fragment = Column(String(255), nullable=True) # e.g. "Para 3(b)"
    rule_group = Column(String(64), default="default")  # groups for OR / AND logic
    fact_key = Column(String(128), nullable=False)     # e.g. "person.age", "location.state"
    operator = Column(String(32), nullable=False)      # "between", "in", "lte", "gte", "eq"
    expected_value = Column(Text, nullable=False)      # JSON string representing target value
    rule_expression = Column(Text, nullable=True)      # JSON string for recursive AST (all, any, not)
    mandatory = Column(Boolean, default=True)
    verification_status = Column(String(32), default="imported_unverified") # imported_unverified, machine_extracted, human_reviewed, source_verified, superseded
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    scope = Column(String(32), default="applicant")    # applicant, household, property
    rule_scope = Column(String(64), default="applicant_eligibility") # applicant_eligibility, beneficiary_eligibility, household_eligibility, application_requirement, verification_requirement, benefit_progression_condition, post_approval_condition, exclusion, exception
    reason_code = Column(String(64), nullable=False)   # e.g. "AGE_ELIGIBILITY", "STATE_DOMICILE"

    __table_args__ = (
        Index("ix_rules_version_fact", "scheme_version_id", "fact_key", "mandatory"),
        Index("ix_rules_verification", "verification_status"),
        Index("ix_rules_scope", "rule_scope"),
    )

    scheme_version = relationship("SchemeVersion", back_populates="rules")
    source_evidence = relationship("SourceDocument", back_populates="rules")


class Benefit(Base):
    __tablename__ = "benefits"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_version_id = Column(String(128), ForeignKey("scheme_versions.id"), nullable=False)
    source_evidence_id = Column(String(128), ForeignKey("source_documents.id"), nullable=True)
    benefit_type = Column(String(64), default="cash_transfer") # cash_transfer, subsidy, loan, insurance, in_kind
    amount_type = Column(String(32), default="fixed")          # fixed, recurring, percentage, limit
    fixed_amount = Column(Float, nullable=True)
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    frequency = Column(String(32), nullable=True)              # monthly, yearly, one_time
    cap_amount = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    formula = Column(String(255), nullable=True)
    tranche_number = Column(Integer, default=1)
    prerequisite_condition = Column(Text, nullable=True)
    interest_subsidy_percentage = Column(Float, nullable=True)
    benefit_version = Column(String(32), default="1.0.0")
    verification_status = Column(String(32), default="imported_unverified")
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)

    scheme_version = relationship("SchemeVersion", back_populates="benefits")


class DocumentRequirement(Base):
    __tablename__ = "document_requirements"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_version_id = Column(String(128), ForeignKey("scheme_versions.id"), nullable=False)
    source_evidence_id = Column(String(128), ForeignKey("source_documents.id"), nullable=True)
    document_type = Column(String(128), nullable=False) # e.g. "Aadhaar Card", "Income Certificate"
    is_mandatory = Column(Boolean, default=True)
    conditional_rule = Column(String(255), nullable=True)
    alternatives = Column(Text, nullable=True)          # comma-separated alternative doc types
    requirement_stage = Column(String(64), default="application_stage") # application_stage, verification_stage, disbursal_stage
    requirement_category = Column(String(64), default="mandatory")     # mandatory, conditional, alternative, verification_only, application_stage_only
    verification_status = Column(String(32), default="imported_unverified")

    scheme_version = relationship("SchemeVersion", back_populates="documents")


# ── 5. Sessions, Facts, Decisions & Feedback ──────────────────────────────────

class ProfileSession(Base):
    __tablename__ = "profile_sessions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_anonymous = Column(Boolean, default=True)
    current_question_key = Column(String(64), nullable=True)
    completed_at = Column(DateTime, nullable=True)

    facts = relationship("ProfileFact", back_populates="session", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationRun", back_populates="session", cascade="all, delete-orphan")


class ProfileFact(Base):
    __tablename__ = "profile_facts"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), ForeignKey("profile_sessions.id"), nullable=False)
    fact_key = Column(String(128), nullable=False)  # e.g. "person.age"
    fact_value = Column(Text, nullable=False)      # JSON encoded string representation
    verified = Column(Boolean, default=False)
    source = Column(String(32), default="self_declared") # self_declared, document_extracted, official_api, admin_verified
    verification_status = Column(String(32), default="unverified") # unverified, user_confirmed, verified
    answered_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    is_skipped = Column(Boolean, default=False)
    is_unknown = Column(Boolean, default=False)
    scope = Column(String(32), default="applicant") # applicant, spouse, household, child, landholding, business
    member_index = Column(Integer, default=0)       # 0 for primary applicant, 1..n for members
    evidence_reference = Column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_profile_facts_session_key", "session_id", "fact_key"),
        Index("ix_profile_facts_session_scope", "session_id", "scope", "member_index"),
    )

    session = relationship("ProfileSession", back_populates="facts")


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), ForeignKey("profile_sessions.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    total_considered = Column(Integer, default=0)
    total_eligible = Column(Integer, default=0)
    ranking_config = Column(Text, nullable=True)

    session = relationship("ProfileSession", back_populates="recommendations")
    items = relationship("RecommendationItem", back_populates="run", cascade="all, delete-orphan")


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(64), ForeignKey("recommendation_runs.id"), nullable=False)
    scheme_id = Column(String(128), nullable=False)
    eligibility_status = Column(String(32), default="ELIGIBLE") # ELIGIBLE, NEEDS_INFO, NEEDS_VERIFICATION, NOT_ELIGIBLE, CONDITIONAL
    confidence_score = Column(Float, default=1.0)
    application_readiness = Column(Float, default=1.0)
    rank_score = Column(Float, default=0.0)
    match_score = Column(Float, default=1.0)
    reasons_json = Column(Text, nullable=True)
    missing_facts_json = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_rec_items_run_status", "run_id", "eligibility_status"),
    )

    run = relationship("RecommendationRun", back_populates="items")


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), nullable=True)
    scheme_id = Column(String(128), nullable=False)
    event_type = Column(String(64), nullable=False) # helpful, not_relevant, apply_click, compare
    reason_code = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow)


# ── 6. Phase 3: Authoritative Ingestion, Staging & Governance ───────────────────

class SourceRegistry(Base):
    __tablename__ = "source_registries"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_url = Column(String(512), unique=True, nullable=False)
    final_url = Column(String(512), nullable=True)
    publisher = Column(String(255), nullable=True)
    authority_id = Column(String(64), ForeignKey("authorities.id"), nullable=True)
    jurisdiction = Column(String(64), default="Central")
    source_type = Column(String(64), default="official_guideline") # gazette, statutory_rule, official_guideline, scheme_portal, press_release, secondary
    trust_level = Column(String(16), default="B")                  # A (Gazette/Statutory), B (Official Portal/myScheme), C (Press), D (Secondary)
    source_authority_type = Column(String(64), default="operational_guideline") # statutory_act, operational_guideline, portal_spec, gazette_notification, executive_order
    legal_priority = Column(Integer, default=3)                    # 1 = highest legal priority (Acts/Gazettes), 2 = Notifications, 3 = Operational Guidelines, 4 = Scheme Portals, 5 = Press/Secondary
    supersedes_source_id = Column(String(128), nullable=True)     # id of older SourceRegistry being superseded
    supersession_status = Column(String(32), default="none")       # none, proposed, confirmed, rejected
    scheme_id = Column(String(128), ForeignKey("schemes.id"), nullable=True) # Direct scheme association
    latest_snapshot_id = Column(String(128), nullable=True)        # latest immutable snapshot id
    parser_health = Column(String(32), default="not_run")          # not_run, complete, partial, ocr_required, failed
    last_fetch_status = Column(String(32), default="not_attempted")# success, not_modified, changed, redirected, blocked, timeout, unreachable, parser_failed, ocr_required, not_attempted
    last_fetch_error = Column(Text, nullable=True)
    title = Column(String(255), nullable=True)
    language = Column(String(16), default="en")
    content_type = Column(String(64), default="text/html")         # text/html, application/pdf, application/json
    freshness_policy_days = Column(Integer, default=30)
    last_checked_at = Column(DateTime, nullable=True)
    last_changed_at = Column(DateTime, nullable=True)
    current_hash = Column(String(128), nullable=True)
    freshness_status = Column(String(32), default="fresh")         # fresh, needs_recheck, source_changed, stale, unreachable
    verification_status = Column(String(32), default="imported_unverified")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_source_registry_url", "canonical_url"),
        Index("ix_source_registry_trust", "trust_level"),
        Index("ix_source_registry_freshness", "freshness_status"),
        Index("ix_source_registry_scheme", "scheme_id"),
    )

    scheme = relationship("Scheme")
    snapshots = relationship("SourceSnapshot", back_populates="source_registry", cascade="all, delete-orphan", foreign_keys="SourceSnapshot.source_registry_id")


class SourceSnapshot(Base):
    __tablename__ = "source_snapshots"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_registry_id = Column(String(128), ForeignKey("source_registries.id"), nullable=False)
    content_hash = Column(String(128), nullable=False)
    content_type = Column(String(64), default="text/html")
    storage_path = Column(String(512), nullable=True) # relative or absolute path under data/snapshots/
    etag = Column(String(128), nullable=True)
    last_modified = Column(String(128), nullable=True)
    http_status = Column(Integer, default=200)
    fetched_at = Column(DateTime, default=utcnow)
    parser_version = Column(String(32), default="1.0.0")
    parser_health = Column(String(32), default="not_run") # not_run, complete, partial, ocr_required, failed
    parsed_at = Column(DateTime, nullable=True)
    extracted_chars = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    quality_score = Column(Float, default=0.0)
    quality_metadata = Column(Text, nullable=True)
    raw_size_bytes = Column(Integer, default=0)
    is_duplicate = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_snapshots_registry_hash", "source_registry_id", "content_hash"),
        Index("ix_snapshots_parser_health", "parser_health"),
    )

    source_registry = relationship("SourceRegistry", back_populates="snapshots", foreign_keys=[source_registry_id])
    changesets = relationship("SchemeChangeSet", back_populates="source_snapshot")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="running") # running, completed, failed
    sources_checked = Column(Integer, default=0)
    sources_changed = Column(Integer, default=0)
    changesets_created = Column(Integer, default=0)
    errors_json = Column(Text, nullable=True)

    changesets = relationship("SchemeChangeSet", back_populates="ingestion_run")


class SchemeChangeSet(Base):
    """
    Staging/Draft layer: machine-extracted changes reside here until approved by human reviewer.
    Isolates draft proposals completely from production scheme_versions.
    """
    __tablename__ = "scheme_changesets"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id = Column(String(128), ForeignKey("schemes.id"), nullable=False)
    source_snapshot_id = Column(String(128), ForeignKey("source_snapshots.id"), nullable=True)
    ingestion_run_id = Column(String(64), ForeignKey("ingestion_runs.id"), nullable=True)
    status = Column(String(32), default="pending") # pending, approved, rejected
    change_summary = Column(Text, nullable=True)
    structured_diff_json = Column(Text, nullable=True)
    quality_report_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(64), nullable=True)
    review_notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_changesets_scheme_status", "scheme_id", "status"),
    )

    scheme = relationship("Scheme")
    source_snapshot = relationship("SourceSnapshot", back_populates="changesets")
    ingestion_run = relationship("IngestionRun", back_populates="changesets")
    rule_drafts = relationship("RuleDraft", back_populates="changeset", cascade="all, delete-orphan")
    benefit_drafts = relationship("BenefitDraft", back_populates="changeset", cascade="all, delete-orphan")
    document_drafts = relationship("DocumentRequirementDraft", back_populates="changeset", cascade="all, delete-orphan")


class RuleDraft(Base):
    __tablename__ = "rule_drafts"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    changeset_id = Column(String(128), ForeignKey("scheme_changesets.id"), nullable=False)
    fact_key = Column(String(128), nullable=False)
    operator = Column(String(32), nullable=False)
    expected_value = Column(Text, nullable=False)
    rule_expression = Column(Text, nullable=True)
    mandatory = Column(Boolean, default=True)
    scope = Column(String(32), default="applicant")
    reason_code = Column(String(64), nullable=False)
    source_fragment = Column(String(255), nullable=True)
    change_type = Column(String(32), default="added") # added, modified, removed, unchanged

    changeset = relationship("SchemeChangeSet", back_populates="rule_drafts")

    @property
    def source_locator(self):
        if hasattr(self, "_source_locator") and self._source_locator:
            return self._source_locator
        if self.source_fragment:
            return self.source_fragment
        return None

    @source_locator.setter
    def source_locator(self, val):
        self._source_locator = val


class BenefitDraft(Base):
    __tablename__ = "benefit_drafts"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    changeset_id = Column(String(128), ForeignKey("scheme_changesets.id"), nullable=False)
    benefit_type = Column(String(64), default="cash_transfer")
    amount_type = Column(String(32), default="fixed")
    fixed_amount = Column(Float, nullable=True)
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    frequency = Column(String(32), nullable=True)
    description = Column(Text, nullable=True)
    source_fragment = Column(String(255), nullable=True)
    change_type = Column(String(32), default="added")

    changeset = relationship("SchemeChangeSet", back_populates="benefit_drafts")


class DocumentRequirementDraft(Base):
    __tablename__ = "document_drafts"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    changeset_id = Column(String(128), ForeignKey("scheme_changesets.id"), nullable=False)
    document_type = Column(String(128), nullable=False)
    is_mandatory = Column(Boolean, default=True)
    source_fragment = Column(String(255), nullable=True)
    change_type = Column(String(32), default="added")

    changeset = relationship("SchemeChangeSet", back_populates="document_drafts")


class AuditLog(Base):
    """
    Immutable audit log for all governance, review, and verification actions.
    """
    __tablename__ = "audit_logs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(64), nullable=False) # scheme_version, rule, changeset, source
    entity_id = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)      # approve, reject, publish, extract, supersede
    actor_id = Column(String(64), default="system")
    previous_state_json = Column(Text, nullable=True)
    new_state_json = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_action", "action"),
    )


class SourceConflict(Base):
    """
    Explicit source conflict tracking. Discrepancies between official sources
    are gated under SOURCE_CONFLICT_OPEN and route into human review.
    """
    __tablename__ = "source_conflicts"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id = Column(String(128), ForeignKey("schemes.id"), nullable=False)
    rule_id = Column(String(128), ForeignKey("eligibility_rules.id"), nullable=True)
    conflict_type = Column(String(64), nullable=False) # threshold_conflict, age_conflict, benefit_conflict, document_conflict, effective_date_conflict, geographic_conflict, status_conflict
    status = Column(String(32), default="SOURCE_CONFLICT_OPEN") # SOURCE_CONFLICT_OPEN, SOURCE_CONFLICT_RESOLVED
    source_a_id = Column(String(128), nullable=True)
    source_b_id = Column(String(128), nullable=True)
    source_a_title = Column(String(255), nullable=True)
    source_b_title = Column(String(255), nullable=True)
    source_a_value = Column(Text, nullable=True)
    source_b_value = Column(Text, nullable=True)
    source_a_assertion = Column(Text, nullable=True)
    source_b_assertion = Column(Text, nullable=True)
    effective_dates = Column(String(128), nullable=True)
    source_authority_metadata = Column(Text, nullable=True)
    review_analysis = Column(Text, nullable=True)
    resolution_type = Column(String(64), nullable=True) # SOURCE_A_PREVAILS, SOURCE_B_PREVAILS, BOTH_APPLY_DIFFERENT_CONTEXT, SUPERSEDED, INSUFFICIENT_EVIDENCE
    winning_evidence = Column(Text, nullable=True)
    disputed_fact_key = Column(String(128), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(64), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_source_conflicts_scheme", "scheme_id"),
        Index("ix_source_conflicts_status", "status"),
        Index("ix_source_conflicts_fact", "disputed_fact_key"),
    )

    scheme = relationship("Scheme")
    rule = relationship("EligibilityRule")


class DuplicateCandidate(Base):
    """
    Candidate scheme duplication, alias, or variant record requiring human governance review.
    Enforces the zero destructive automated merges invariant.
    """
    __tablename__ = "duplicate_candidates"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_a_id = Column(String(128), ForeignKey("schemes.id"), nullable=False)
    scheme_b_id = Column(String(128), ForeignKey("schemes.id"), nullable=False)
    scheme_a_name = Column(String(255), nullable=False)
    scheme_b_name = Column(String(255), nullable=False)
    similarity_score = Column(Float, default=0.0)
    matching_criteria_json = Column(Text, nullable=True) # JSON list of criteria e.g. ["acronym_match", "authority_match"]
    candidate_type = Column(String(64), default="potential_duplicate") # potential_duplicate, alias, state_variant, test_artifact
    status = Column(String(32), default="pending_review") # pending_review, confirmed_duplicate, confirmed_distinct, merged, archived
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(64), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_dup_candidates_schemes", "scheme_a_id", "scheme_b_id"),
        Index("ix_dup_candidates_status", "status"),
        Index("ix_dup_candidates_type", "candidate_type"),
    )

    scheme_a = relationship("Scheme", foreign_keys=[scheme_a_id])
    scheme_b = relationship("Scheme", foreign_keys=[scheme_b_id])


class SchemeCertificationDossier(Base):
    """
    Forensic record certifying that a scheme version has undergone semantic validation,
    applicant/beneficiary model verification, source currentness check, and statutory
    rule completeness verification.
    """
    __tablename__ = "scheme_certification_dossiers"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id = Column(String(128), ForeignKey("schemes.id"), nullable=False)
    scheme_version_id = Column(String(128), ForeignKey("scheme_versions.id"), nullable=False)
    certified_at = Column(DateTime, default=utcnow)
    certified_by = Column(String(64), default="system")
    applicant_type = Column(String(64), default="individual")
    beneficiary_type = Column(String(64), default="individual")
    audience_type = Column(String(64), default="DIRECT_CITIZEN_BENEFIT")
    source_ids_json = Column(Text, nullable=True)
    latest_source_checked_at = Column(DateTime, nullable=True)
    latest_source_reference = Column(String(255), nullable=True)
    eligibility_rule_ids_json = Column(Text, nullable=True)
    exclusion_rule_ids_json = Column(Text, nullable=True)
    benefit_ids_json = Column(Text, nullable=True)
    document_requirement_ids_json = Column(Text, nullable=True)
    open_findings_json = Column(Text, nullable=True)
    semantic_review_status = Column(String(32), default="certified")
    completeness_status = Column(String(32), default="complete")
    currentness_status = Column(String(32), default="current")
    lifecycle_status = Column(String(32), default="ACTIVE")  # ACTIVE, PAUSED, CLOSED, WITHDRAWN, SUBSUMED, SUPERSEDED, HISTORICAL
    last_currentness_check = Column(DateTime, default=utcnow)
    next_currentness_check = Column(DateTime, nullable=True)
    currentness_check_source = Column(String(512), nullable=True)
    invalidation_reason = Column(Text, nullable=True)
    certification_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_dossiers_scheme_version", "scheme_id", "scheme_version_id"),
        Index("ix_dossiers_active_status", "is_active", "semantic_review_status"),
        Index("ix_dossiers_lifecycle_active", "lifecycle_status", "is_active"),
    )

    scheme = relationship("Scheme", back_populates="dossiers", foreign_keys=[scheme_id])
    scheme_version = relationship("SchemeVersion", back_populates="dossiers", foreign_keys=[scheme_version_id])


# ── 12. RAG & Grounded Retrieval Models (Phase 4) ────────────────────────────

class RagDocument(Base):
    """
    Authoritative document representation indexed for RAG retrieval.
    Derived strictly from verified SourceDocument and SourceSnapshot.
    """
    __tablename__ = "rag_documents"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id = Column(String(128), ForeignKey("schemes.id"), nullable=False)
    scheme_version_id = Column(String(128), ForeignKey("scheme_versions.id"), nullable=False)
    source_id = Column(String(128), nullable=True)
    source_snapshot_id = Column(String(128), nullable=True)
    source_url = Column(Text, nullable=False)
    document_title = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    doc_type = Column(String(64), default="guidelines") # guidelines, order, gazette, portal
    generation_id = Column(String(128), nullable=True, index=True)
    generation_status = Column(String(32), default="active") # staging, active, superseded, rolled_back
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_rag_docs_scheme_version", "scheme_id", "scheme_version_id"),
        Index("ix_rag_docs_hash", "content_hash"),
        Index("ix_rag_docs_active", "is_active"),
        Index("ix_rag_docs_gen_active", "generation_id", "is_active"),
    )

    scheme = relationship("Scheme", back_populates="rag_documents", foreign_keys=[scheme_id])
    scheme_version = relationship("SchemeVersion", back_populates="rag_documents", foreign_keys=[scheme_version_id])
    chunks = relationship("RagChunk", back_populates="document", cascade="all, delete-orphan")


class RagChunk(Base):
    """
    Structure-aware chunk containing statutory text, clauses, benefits,
    or document requirements tied directly to verified provenance.
    """
    __tablename__ = "rag_chunks"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(128), ForeignKey("rag_documents.id"), nullable=False)
    scheme_id = Column(String(128), ForeignKey("schemes.id"), nullable=False)
    scheme_version_id = Column(String(128), ForeignKey("scheme_versions.id"), nullable=False)
    section_type = Column(String(64), default="general") # eligibility_criteria, exclusions, benefits_and_tranches, documents_required, application_process, general
    heading_path = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    char_length = Column(Integer, nullable=False)
    token_estimate = Column(Integer, nullable=False)
    chunk_hash = Column(String(64), nullable=False)
    source_citation = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    generation_id = Column(String(128), nullable=True, index=True)
    generation_status = Column(String(32), default="active") # staging, active, superseded, rolled_back
    policy_status = Column(String(32), default="CURRENT_POLICY") # CURRENT_POLICY, HISTORICAL_POLICY
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_rag_chunks_doc_section", "document_id", "section_type"),
        Index("ix_rag_chunks_scheme_active", "scheme_id", "is_active"),
        Index("ix_rag_chunks_hash", "chunk_hash"),
        Index("ix_rag_chunks_gen_active", "generation_id", "is_active"),
        Index("ix_rag_chunks_policy_active", "policy_status", "is_active"),
    )

    document = relationship("RagDocument", back_populates="chunks")
    scheme = relationship("Scheme", foreign_keys=[scheme_id])
    scheme_version = relationship("SchemeVersion", foreign_keys=[scheme_version_id])


class RagIndexRun(Base):
    """
    Audit log of RAG indexing runs, tracking execution time, chunks created,
    and indexed schemes.
    """
    __tablename__ = "rag_index_runs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    generation_id = Column(String(128), nullable=True, index=True)
    generation_status = Column(String(32), default="staging") # staging, active, superseded, rolled_back, failed
    schemes_indexed = Column(Integer, default=0)
    chunks_created = Column(Integer, default=0)
    status = Column(String(32), default="running") # running, completed, failed
    run_log_json = Column(Text, default="{}")

    __table_args__ = (
        Index("ix_rag_index_runs_generation", "generation_id"),
    )


class RagQueryTrace(Base):
    """
    Forensic trace of incoming user queries, language detection, intent classification,
    retrieved evidence chunks, response text, citations, and execution latency.
    """
    __tablename__ = "rag_query_traces"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    raw_query = Column(Text, nullable=False)
    normalized_query = Column(Text, nullable=False)
    detected_language = Column(String(16), default="en")
    intent = Column(String(32), nullable=False) # ELIGIBILITY_CHECK, FACTUAL_QA, UNVERIFIED_SCHEME_INQUIRY, OUT_OF_SCOPE
    retrieved_chunk_ids_json = Column(Text, default="[]")
    response_text = Column(Text, nullable=False)
    citations_json = Column(Text, default="[]")
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_rag_query_traces_intent", "intent"),
        Index("ix_rag_query_traces_created", "created_at"),
    )



