"""
Official Scheme Discovery & Connector Framework
Defines the abstract connector interface and candidate models for registry-driven
discovery, snapshotting, parsing, and change detection across official Indian government sources.
Strict Architectural Invariant: Connectors NEVER create or publish authoritative EligibilityRule records.
"""
from __future__ import annotations
import abc
import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

class CandidateStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    SOURCE_CONFIRMED = "SOURCE_CONFIRMED"
    FETCHED = "FETCHED"
    PARSED = "PARSED"
    EXTRACTED = "EXTRACTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CERTIFIED = "CERTIFIED"
    REJECTED = "REJECTED"
    HISTORICAL = "HISTORICAL"

class OCRStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    OCR_REQUIRED = "OCR_REQUIRED"
    OCR_IN_PROGRESS = "OCR_IN_PROGRESS"
    OCR_COMPLETED = "OCR_COMPLETED"
    OCR_FAILED = "OCR_FAILED"

class SchemeDiscoveryCandidate(BaseModel):
    candidate_id: str
    name: str
    level: str = "Central"  # Central, State, UT
    state_ut: Optional[str] = None
    ministry: Optional[str] = None
    department: Optional[str] = None
    official_discovery_source: str  # e.g., "myScheme", "DBT Bharat", "India.gov.in"
    detail_url: str
    discovered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_hash: Optional[str] = None
    possible_existing_scheme_id: Optional[str] = None
    identity_confidence: float = 0.0  # 0.0 to 1.0
    status: CandidateStatus = CandidateStatus.DISCOVERED
    ocr_status: OCRStatus = OCRStatus.NOT_REQUIRED
    ocr_quality_score: Optional[float] = None
    candidate_rules: List[Dict[str, Any]] = Field(default_factory=list)
    candidate_benefits: List[Dict[str, Any]] = Field(default_factory=list)
    candidate_documents: List[str] = Field(default_factory=list)
    review_packet_generated: bool = False
    review_notes: Optional[str] = None

class BaseSchemeConnector(abc.ABC):
    """
    Abstract interface for official Indian government scheme discovery connectors.
    Maintains strict trust boundary:
    DISCOVERY / FETCHING != POLICY CERTIFICATION
    """
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url

    @abc.abstractmethod
    def discover(self, limit: int = 100) -> List[SchemeDiscoveryCandidate]:
        """Discovers scheme candidates from public official registry indexes."""
        pass

    @abc.abstractmethod
    def fetch(self, candidate: SchemeDiscoveryCandidate) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Fetches official page or public gazette PDF.
        Returns (success, content_or_error, http_metadata).
        """
        pass

    @abc.abstractmethod
    def snapshot(self, candidate_id: str, raw_content: str) -> str:
        """Stores immutable raw content snapshot with SHA-256 hash."""
        pass

    @abc.abstractmethod
    def parse(self, raw_content: str, content_type: str = "html") -> Dict[str, Any]:
        """Parses structured content into draft sections; flags OCR requirement if scanned PDF."""
        pass

    @abc.abstractmethod
    def extract_metadata(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts candidate eligibility conditions, benefits, and required documents."""
        pass

    @abc.abstractmethod
    def detect_changes(self, existing_hash: str, new_hash: str) -> bool:
        """Detects whether official policy document has changed since last snapshot."""
        pass

    def generate_review_packet(self, candidate: SchemeDiscoveryCandidate) -> Dict[str, Any]:
        """Generates a structured review packet for human governance certification."""
        return {
            "candidate_id": candidate.candidate_id,
            "name": candidate.name,
            "source": candidate.official_discovery_source,
            "source_url": candidate.detail_url,
            "level": candidate.level,
            "state_ut": candidate.state_ut,
            "ministry": candidate.ministry,
            "extracted_draft_rules": candidate.candidate_rules,
            "extracted_draft_benefits": candidate.candidate_benefits,
            "extracted_draft_documents": candidate.candidate_documents,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "governance_review_status": "REVIEW_REQUIRED",
            "certification_action_required": "Human statutory review & formal dossier sign-off"
        }
