"""
CivixAI Ingestion, Versioning & Governance Subsystem
"""
from .registry import SourceRegistryService, TRUST_POLICIES
from .fetcher import SourceFetcher, FetchResult
from .snapshot import SnapshotService, compute_content_hash
from .parser import DocumentParser, ParsedDocument, DocumentSection
from .normalizer import normalize_state, parse_currency_amount, extract_age_bounds
from .extractor import RuleExtractor, CandidateExtraction
from .diff_engine import DiffEngine, StructuredDiff, RuleDiffEngine
from .quality import DataQualityEngine, QualityReport, QualityViolation
from .freshness import FreshnessEvaluator
from .publisher import GovernancePublisher
from .pipeline import IngestionPipeline
from .maturity import SchemeMaturityService, SchemeMaturityState, CRITICAL_FACT_KEYS
from .prioritization import VerificationPrioritizationEngine
from .precedence import PrecedencePolicy, SupersessionGovernanceEngine
from .conflict_engine import SourceConflictEngine, ConflictResolutionType
from .conversion import BootstrapConversionWorkflow, RuleConversionOutcome
from .semantic import SemanticCertificationEngine, compute_certification_hash, NON_CITIZEN_AUDIENCES

__all__ = [
    "SourceRegistryService", "TRUST_POLICIES",
    "SourceFetcher", "FetchResult",
    "SnapshotService", "compute_content_hash",
    "DocumentParser", "ParsedDocument", "DocumentSection",
    "normalize_state", "parse_currency_amount", "extract_age_bounds",
    "RuleExtractor", "CandidateExtraction",
    "DiffEngine", "StructuredDiff", "RuleDiffEngine",
    "DataQualityEngine", "QualityReport", "QualityViolation",
    "FreshnessEvaluator",
    "GovernancePublisher",
    "IngestionPipeline",
    "SchemeMaturityService", "SchemeMaturityState", "CRITICAL_FACT_KEYS",
    "VerificationPrioritizationEngine",
    "PrecedencePolicy", "SupersessionGovernanceEngine",
    "SourceConflictEngine", "ConflictResolutionType",
    "BootstrapConversionWorkflow", "RuleConversionOutcome",
    "SemanticCertificationEngine", "compute_certification_hash", "NON_CITIZEN_AUDIENCES"
]
