"""
Data.gov.in Discovery Adapter (Classification: PARTIAL)
======================================================
Connects to Open Government Data (OGD) platform catalog index to discover
dataset packages associated with Indian government welfare schemes.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
import hashlib

from services.core.discovery.connectors.base import BaseDiscoveryConnector
from services.core.discovery.models import (
    ProgramCandidate,
    ProgramType,
    ProviderType,
    ProgramSector,
    DiscoveryStatus,
    EvidenceStatus,
    CurrentnessStatus,
    GovernanceStatus,
)
from services.core.discovery.identity import generate_candidate_id
from services.core.ingestion.fetcher import SourceFetcher


class DataGovInDiscoveryAdapter(BaseDiscoveryConnector):
    """
    Discovery connector adapter for Data.gov.in catalog index.
    Status: PARTIAL (indexes datasets and indicators for welfare programs).
    """

    def __init__(
        self,
        source_id: str = "src-data-gov-in",
        authority_tier: str = "tier5_official_portal",
        fetcher: Optional[SourceFetcher] = None,
    ):
        super().__init__(source_id=source_id, authority_tier=authority_tier)
        self.fetcher = fetcher or SourceFetcher()

    def discover(self, limit: Optional[int] = None) -> List[ProgramCandidate]:
        # Implementation note: Data.gov.in API key required for full pagination.
        # In bounded discovery mode, returns curated high-level dataset program entries.
        candidates: List[ProgramCandidate] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        curated = [
            {
                "title": "National Social Assistance Programme (NSAP) Beneficiary Data",
                "url": "https://data.gov.in/catalog/national-social-assistance-programme-nsap",
                "ministry": "Ministry of Rural Development",
                "sector": ProgramSector.SOCIAL_WELFARE.value,
                "prog_type": ProgramType.GOVERNMENT_PENSION.value,
            },
            {
                "title": "Pradhan Mantri Gram Sadak Yojana (PMGSY) Road Works",
                "url": "https://data.gov.in/catalog/pradhan-mantri-gram-sadak-yojana-pmgsy",
                "ministry": "Ministry of Rural Development",
                "sector": ProgramSector.CROSS_SECTOR.value,
                "prog_type": ProgramType.GOVERNMENT_SCHEME.value,
            },
        ]
        if limit:
            curated = curated[:limit]

        for item in curated:
            title = item["title"]
            url = item["url"]
            content_hash = hashlib.sha256(f"{title}|{url}".encode("utf-8")).hexdigest()
            cand_id = generate_candidate_id(self.source_id, title)

            cand = ProgramCandidate(
                candidate_id=cand_id,
                program_type=item["prog_type"],
                sector=item["sector"],
                provider_type=ProviderType.GOVERNMENT_CENTRAL.value,
                provider_name=item["ministry"],
                official_name=title,
                source_url=url,
                source_domain="data.gov.in",
                source_id=self.source_id,
                authority_tier=self.authority_tier,
                discovery_method="ogd_catalog_index",
                discovery_timestamp=now_iso,
                content_hash=content_hash,
                identity_key="",
                possible_duplicate_of=[],
                discovery_status=DiscoveryStatus.DISCOVERY_STAGED.value,
                verification_status="unverified",
                currentness_status=CurrentnessStatus.FRESH.value,
                evidence_status=EvidenceStatus.EVIDENCE_ABSENT.value,
                governance_status=GovernanceStatus.UNREVIEWED.value,
                eligibility_summary="UNKNOWN",
                benefit_summary="UNKNOWN",
                raw_metadata={"status_classification": "PARTIAL"},
            )
            candidates.append(cand)

        return candidates

    def fetch_source(self, candidate: ProgramCandidate) -> Tuple[int, bytes, str]:
        res = self.fetcher.fetch(candidate.source_url)
        return res.status_code, res.content, res.content_type
