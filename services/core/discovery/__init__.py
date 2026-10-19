"""
CivixAI India-Wide Program Discovery Engine
===========================================
Scalable multi-source acquisition and discovery architecture for discovering
tens of thousands of Indian government schemes, subsidies, grants, pensions,
scholarships, loans, healthcare, agriculture, housing programs, and regulated
private financial products.
"""

from services.core.discovery.models import (
    ProgramType,
    ProviderType,
    ProgramSector,
    ProgramLifecycleStatus,
    DiscoveryStatus,
    EvidenceStatus,
    GovernanceStatus,
    ReviewAction,
    CurrentnessStatus,
    ConnectorStatus,
    ProgramCandidate,
    SourceRegistryDefinition,
    DiscoveryResult,
)
from services.core.discovery.registry import DiscoverySourceRegistry, GovernmentProgrammeSourceRegistry
from services.core.discovery.identity import ProgramIdentityEngine
from services.core.discovery.engine import DiscoveryEngine
from services.core.discovery.exporter import ProgramCandidateExporter

__all__ = [
    "ProgramType",
    "ProviderType",
    "ProgramSector",
    "ProgramLifecycleStatus",
    "DiscoveryStatus",
    "EvidenceStatus",
    "GovernanceStatus",
    "ReviewAction",
    "CurrentnessStatus",
    "ConnectorStatus",
    "ProgramCandidate",
    "SourceRegistryDefinition",
    "DiscoveryResult",
    "DiscoverySourceRegistry",
    "ProgramIdentityEngine",
    "DiscoveryEngine",
    "ProgramCandidateExporter",
]
