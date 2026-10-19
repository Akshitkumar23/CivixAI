"""
CIVIXAI — GOVERNMENT PROGRAMME DISCOVERY DATABASE & PYDANTIC MODELS
===================================================================
Unifies:
1. Pydantic models & Enums for Discovery Engine, Connectors, Identity, Governance
2. SQLAlchemy ORM models for:
   - raw_discovery_records (immutable raw ingestion layer)
   - programme_discovery (normalized, deduplicated, currentness-aware discovery layer)
Strictly separates discovery universe from production recommendation & certification.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    String, Text, Index
)
from services.core.database.models import Base

def utcnow():
    return datetime.now(timezone.utc)


# ── Domain Enumerations ─────────────────────────────────────────────────────────

class ProgramType(str, Enum):
    """Explicit domain types for all discovered government entities."""
    SCHEME = "SCHEME"
    SUB_SCHEME = "SUB_SCHEME"
    PROGRAMME = "PROGRAMME"
    COMPONENT = "COMPONENT"
    PHASE = "PHASE"
    BENEFIT_PROGRAMME = "BENEFIT_PROGRAMME"
    SCHOLARSHIP = "SCHOLARSHIP"
    PENSION = "PENSION"
    SUBSIDY = "SUBSIDY"
    INSURANCE_PROGRAMME = "INSURANCE_PROGRAMME"
    CREDIT_PROGRAMME = "CREDIT_PROGRAMME"
    GRANT = "GRANT"
    EMPLOYMENT_PROGRAMME = "EMPLOYMENT_PROGRAMME"
    SKILL_PROGRAMME = "SKILL_PROGRAMME"
    SERVICE = "SERVICE"
    CERTIFICATE_SERVICE = "CERTIFICATE_SERVICE"
    APPLICATION_SERVICE = "APPLICATION_SERVICE"
    REGISTRATION_SERVICE = "REGISTRATION_SERVICE"
    INSTITUTIONAL_PROGRAMME = "INSTITUTIONAL_PROGRAMME"
    EMPLOYER_PROGRAMME = "EMPLOYER_PROGRAMME"
    DEPARTMENT_PROGRAMME = "DEPARTMENT_PROGRAMME"
    INFORMATIONAL_PROGRAMME = "INFORMATIONAL_PROGRAMME"
    OTHER_GOVERNMENT_PROGRAMME = "OTHER_GOVERNMENT_PROGRAMME"

    # Backward-compatible aliases for legacy connectors
    GOVERNMENT_SCHEME = "GOVERNMENT_SCHEME"
    GOVERNMENT_WELFARE = "GOVERNMENT_WELFARE"
    GOVERNMENT_SCHOLARSHIP = "GOVERNMENT_SCHOLARSHIP"
    GOVERNMENT_PENSION = "GOVERNMENT_PENSION"
    GOVERNMENT_SUBSIDY = "GOVERNMENT_SUBSIDY"
    GOVERNMENT_LOAN = "GOVERNMENT_LOAN"
    GOVERNMENT_GRANT = "GOVERNMENT_GRANT"
    GOVERNMENT_INSURANCE = "GOVERNMENT_INSURANCE"
    GOVERNMENT_HEALTH = "GOVERNMENT_HEALTH"
    GOVERNMENT_HEALTH_PROGRAM = "GOVERNMENT_HEALTH_PROGRAM"
    GOVERNMENT_HOUSING = "GOVERNMENT_HOUSING"
    GOVERNMENT_HOUSING_PROGRAM = "GOVERNMENT_HOUSING_PROGRAM"
    GOVERNMENT_AGRI = "GOVERNMENT_AGRI"
    GOVERNMENT_AGRICULTURE_PROGRAM = "GOVERNMENT_AGRICULTURE_PROGRAM"
    GOVERNMENT_SKILL = "GOVERNMENT_SKILL"
    GOVERNMENT_EMPLOYMENT_PROGRAM = "GOVERNMENT_EMPLOYMENT_PROGRAM"
    GOVERNMENT_CREDIT_SUPPORT = "GOVERNMENT_CREDIT_SUPPORT"
    GOVERNMENT_WOMEN_CHILD_PROGRAM = "GOVERNMENT_WOMEN_CHILD_PROGRAM"
    PRIVATE_LOAN = "PRIVATE_LOAN"
    PRIVATE_EDUCATION_FINANCE = "PRIVATE_EDUCATION_FINANCE"
    PRIVATE_AGRI_FINANCE = "PRIVATE_AGRI_FINANCE"
    PRIVATE_MSME_FINANCE = "PRIVATE_MSME_FINANCE"
    PRIVATE_INSURANCE = "PRIVATE_INSURANCE"
    PRIVATE_HEALTH_COVER = "PRIVATE_HEALTH_COVER"
    REGULATED_BANK_LOAN = "REGULATED_BANK_LOAN"
    REGULATED_BANK_DEPOSIT = "REGULATED_BANK_DEPOSIT"
    REGULATED_INSURANCE_TERM = "REGULATED_INSURANCE_TERM"
    REGULATED_INSURANCE_HEALTH = "REGULATED_INSURANCE_HEALTH"
    REGULATED_INSURANCE_AGRI = "REGULATED_INSURANCE_AGRI"


class ProviderType(str, Enum):
    GOVERNMENT_CENTRAL = "GOVERNMENT_CENTRAL"
    GOVERNMENT_STATE = "GOVERNMENT_STATE"
    GOVERNMENT_UT = "GOVERNMENT_UT"
    PUBLIC_SECTOR_BANK = "PUBLIC_SECTOR_BANK"
    PRIVATE_BANK = "PRIVATE_BANK"
    BANK = "PUBLIC_SECTOR_BANK"
    BANK_PUBLIC = "PUBLIC_SECTOR_BANK"
    BANK_PRIVATE = "PRIVATE_BANK"
    INSURANCE_REGULATED = "INSURANCE_REGULATED"
    INSURANCE_COMPANY = "INSURANCE_REGULATED"
    INSURER = "INSURANCE_REGULATED"
    LOCAL_BODY = "LOCAL_BODY"


class ProgramSector(str, Enum):
    AGRICULTURE = "AGRICULTURE"
    EDUCATION = "EDUCATION"
    HEALTH = "HEALTH"
    HOUSING = "HOUSING"
    FINANCIAL_SERVICES = "FINANCIAL_SERVICES"
    SKILL_EMPLOYMENT = "SKILL_EMPLOYMENT"
    SOCIAL_WELFARE = "SOCIAL_WELFARE"
    WOMEN_CHILD = "WOMEN_CHILD"
    RURAL_DEVELOPMENT = "RURAL_DEVELOPMENT"
    URBAN_DEVELOPMENT = "URBAN_DEVELOPMENT"
    COMMERCE_MSME = "COMMERCE_MSME"
    OTHER = "OTHER"


class ProgramLifecycleStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    EXTRACTED = "EXTRACTED"
    STAGED = "STAGED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"
    SUBSUMED = "SUBSUMED"
    HISTORICAL = "HISTORICAL"


class DiscoveryStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    CURRENT = "CURRENT"
    CURRENTNESS_REVIEW = "CURRENTNESS_REVIEW"
    ENRICHMENT_PENDING = "ENRICHMENT_PENDING"
    ELIGIBILITY_AVAILABLE = "ELIGIBILITY_AVAILABLE"
    GOVERNANCE_REVIEW = "GOVERNANCE_REVIEW"
    CERTIFIED = "CERTIFIED"
    INSTITUTIONAL = "INSTITUTIONAL"
    EMPLOYER = "EMPLOYER"
    DEPARTMENT = "DEPARTMENT"
    IMPLEMENTATION = "IMPLEMENTATION"
    INFORMATIONAL = "INFORMATIONAL"
    DISCOVERY_STAGED = "DISCOVERY_STAGED"
    DISCOVERY_UNREVIEWED = "DISCOVERY_UNREVIEWED"


class EvidenceStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    EVIDENCE_ATTACHED = "EVIDENCE_ATTACHED"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"


class GovernanceStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    GOVERNANCE_PENDING = "GOVERNANCE_PENDING"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    AUTOMATED_GATE_PASSED = "AUTOMATED_GATE_PASSED"
    CERTIFIED = "CERTIFIED"
    DISCOVERY_CATALOGUE = "DISCOVERY_CATALOGUE"


class ReviewAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    HOLD = "HOLD"
    ESCALATE = "ESCALATE"
    QUARANTINE = "QUARANTINE"


class CurrentnessStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"
    SUBSUMED = "SUBSUMED"
    UNKNOWN = "UNKNOWN"


class ConnectorStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNCONFIGURED = "UNCONFIGURED"


# ── Pydantic DTOs & Staging Models ─────────────────────────────────────────────

class ProgramCandidate(BaseModel):
    """Normalized staging object for discovered programmes before persistence."""
    candidate_id: str
    program_type: str = ProgramType.SCHEME.value
    sector: str = ProgramSector.OTHER.value
    provider_type: str = ProviderType.GOVERNMENT_CENTRAL.value
    provider_name: str
    official_name: str
    source_url: str
    source_domain: str = ""
    source_id: str
    authority_tier: str = "CENTRAL_PORTAL"
    discovery_method: str = "STRUCTURED_DISCOVERY"
    discovery_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_hash: str = ""
    identity_key: str = ""
    source_authority: str = ""
    program_authority: str = ""
    implementing_authority: str = ""
    application_authority: str = ""
    snapshot_id: str = ""
    raw_content_sha256: str = ""
    lifecycle_status: str = ProgramLifecycleStatus.ACTIVE.value
    discovery_status: str = DiscoveryStatus.DISCOVERED.value
    governance_status: str = GovernanceStatus.DISCOVERY_CATALOGUE.value
    evidence_status: str = EvidenceStatus.EVIDENCE_ATTACHED.value
    currentness_status: str = CurrentnessStatus.ACTIVE.value
    is_certified: bool = False
    eligibility_summary: Optional[str] = None
    benefit_summary: Optional[str] = None
    state_or_ut: Optional[str] = None
    jurisdiction: str = "CENTRAL"
    category: str = "General"
    beneficiary_type: str = "individual"
    aliases: List[str] = Field(default_factory=list)
    application_route: Optional[str] = None
    documents_required: List[str] = Field(default_factory=list)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceRegistryDefinition(BaseModel):
    source_id: str
    name: str
    authority_tier: str = "CENTRAL_PORTAL"
    jurisdiction: str = "CENTRAL"
    base_url: str = ""
    api_endpoint: Optional[str] = None
    discovery_strategy: str = "dynamic_listing_crawl"
    rate_limit_per_sec: float = 2.0
    is_active: bool = True
    notes: Optional[str] = None


class DiscoveryResult(BaseModel):
    source_id: str
    status_code: int = 200
    candidate_count: int = 0
    unique_count: int = 0
    duplicate_count: int = 0
    failure_count: int = 0
    sample_urls: List[str] = Field(default_factory=list)
    program_types: Dict[str, int] = Field(default_factory=dict)
    provider_types: Dict[str, int] = Field(default_factory=dict)
    content_hashes: List[str] = Field(default_factory=list)
    db_mutation_delta: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = Field(default_factory=list)


# ── SQLAlchemy Database Models ─────────────────────────────────────────────────

class RawDiscoveryRecord(Base):
    """
    Immutable raw ingestion store.
    Captures exact API response or webpage extraction with HTTP metadata,
    source hashes, and temporal timestamps.
    """
    __tablename__ = "raw_discovery_records"

    discovery_id: Any = Column(String(128), primary_key=True, default=lambda: f"raw_{uuid.uuid4().hex[:16]}")
    source_id: Any = Column(String(128), nullable=False, index=True)
    source_record_id: Any = Column(String(255), nullable=False, index=True)
    raw_payload: Any = Column(Text, nullable=False)
    retrieved_at: Any = Column(DateTime, default=utcnow, nullable=False)
    source_url: Any = Column(String(1024), nullable=True)
    source_hash: Any = Column(String(128), nullable=True)
    source_version: Any = Column(String(64), nullable=True)
    http_metadata: Any = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_raw_discovery_source_rec", "source_id", "source_record_id"),
    )


class ProgrammeDiscovery(Base):
    """
    Normalized multi-source discovery entity.
    Maintains canonical identity, explicit programme type, operational currentness,
    provenance lineage, and eligibility availability indicator.
    
    IMPORTANT: is_certified is False by default. Discovered entities NEVER enter
    CandidateService or production eligibility RAG until explicit governance certification.
    """
    __tablename__ = "programme_discovery"

    programme_id: Any = Column(String(128), primary_key=True)
    canonical_name: Any = Column(String(255), nullable=False, index=True)
    aliases: Any = Column(Text, nullable=True)  # JSON string list
    authority: Any = Column(String(255), nullable=True, index=True)
    ministry: Any = Column(String(255), nullable=True, index=True)
    department: Any = Column(String(255), nullable=True)
    jurisdiction: Any = Column(String(32), default="CENTRAL", index=True)  # CENTRAL, STATE, UT
    state_or_ut: Any = Column(String(64), nullable=True, index=True)
    programme_type: Any = Column(String(64), default=ProgramType.SCHEME.value, index=True)
    category: Any = Column(String(128), default="General", index=True)
    beneficiary_type: Any = Column(String(64), default="individual", index=True)
    description: Any = Column(Text, nullable=True)
    benefit_summary: Any = Column(Text, nullable=True)
    application_route: Any = Column(String(255), nullable=True)
    official_url: Any = Column(String(1024), nullable=True)
    currentness: Any = Column(String(32), default=CurrentnessStatus.ACTIVE.value, index=True)
    source_status: Any = Column(String(64), default="SOURCE_VERIFIED")
    
    # Discovery separation flags
    eligibility_available: Any = Column(Boolean, default=False, index=True)
    governance_status: Any = Column(String(64), default=GovernanceStatus.DISCOVERY_CATALOGUE.value, index=True)
    eligibility_status: Any = Column(String(64), nullable=True, index=True)
    applicability: Any = Column(String(64), nullable=True, index=True)
    is_certified: Any = Column(Boolean, default=False, index=True)  # strictly False for non-certified discovery!
    
    # Provenance and Lineage
    source_records: Any = Column(Text, nullable=True)  # JSON string of source lineage references
    lineage: Any = Column(Text, nullable=True)  # JSON string of LineageLink relationships
    
    created_at: Any = Column(DateTime, default=utcnow)
    updated_at: Any = Column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_prog_disc_type_jurisdiction", "programme_type", "jurisdiction"),
        Index("ix_prog_disc_state_category", "state_or_ut", "category"),
        Index("ix_prog_disc_eligibility", "eligibility_available"),
        Index("ix_prog_disc_elig_status", "eligibility_status"),
        Index("ix_prog_disc_applicability", "applicability"),
    )
