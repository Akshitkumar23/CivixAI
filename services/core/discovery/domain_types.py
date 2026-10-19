"""
CIVIXAI — GOVERNMENT PROGRAMME DISCOVERY FABRIC DOMAIN TYPES
=============================================================
Explicit enumeration of all programme entities, lineage relations,
currentness states, discovery life-cycles, and deduplication classes.
Prevents false inflation of scheme counts and separates discovery from eligibility.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProgrammeType(str, Enum):
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


class DiscoveryStatus(str, Enum):
    """Life-cycle status of an entity within the discovery fabric."""
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


class CurrentnessStatus(str, Enum):
    """Operational currentness verified from authoritative sources."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"
    SUBSUMED = "SUBSUMED"
    UNKNOWN = "UNKNOWN"


class LineageRelation(str, Enum):
    """Hierarchical and genealogical lineage connections between programmes."""
    PARENT = "PARENT"
    CHILD = "CHILD"
    SUB_SCHEME = "SUB_SCHEME"
    COMPONENT_OF = "COMPONENT_OF"
    VERSION_OF = "VERSION_OF"
    PHASE_OF = "PHASE_OF"
    STATE_IMPLEMENTATION_OF = "STATE_IMPLEMENTATION_OF"
    RENAMED_TO = "RENAMED_TO"
    SUPERSEDES = "SUPERSEDES"
    SUBSUMED_BY = "SUBSUMED_BY"
    CROSS_SOURCE_DUPLICATE = "CROSS_SOURCE_DUPLICATE"


class DeduplicationClass(str, Enum):
    """Deduplication evaluation result for cross-source signals."""
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    CROSS_SOURCE_DUPLICATE = "CROSS_SOURCE_DUPLICATE"
    STATE_IMPLEMENTATION = "STATE_IMPLEMENTATION"
    SUB_SCHEME = "SUB_SCHEME"
    COMPONENT = "COMPONENT"
    VERSION = "VERSION"
    DISTINCT_PROGRAMME = "DISTINCT_PROGRAMME"


class SourceTier(str, Enum):
    """Hierarchy tier of the authoritative discovery source."""
    TIER_1_NATIONAL = "TIER_1_NATIONAL"
    TIER_2_CENTRAL_MINISTRY = "TIER_2_CENTRAL_MINISTRY"
    TIER_3_STATE_UT = "TIER_3_STATE_UT"
    TIER_4_GOV_SERVICES = "TIER_4_GOV_SERVICES"
    TIER_5_DATASETS = "TIER_5_DATASETS"
    TIER_6_DOCUMENTS = "TIER_6_DOCUMENTS"


class SourceRecordReference(BaseModel):
    """Provenance record tracking which source contributed to this discovery."""
    source_id: str
    source_record_id: str
    retrieved_at: str
    source_url: str
    source_hash: str
    source_tier: SourceTier


class LineageLink(BaseModel):
    """Lineage pointer linking related entities."""
    relation: LineageRelation
    target_programme_id: str
    notes: Optional[str] = None


# Convenience alias
SourceRecordRef = SourceRecordReference
