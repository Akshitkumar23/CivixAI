"""
JanSamarth Discovery Adapter (Classification: PARTIAL)
======================================================
Connects to the JanSamarth National Portal for Credit-Linked Government Schemes
(https://www.jansamarth.in) to discover central loan subsidies and credit support programs.
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


class JanSamarthDiscoveryAdapter(BaseDiscoveryConnector):
    """
    Discovery connector adapter for JanSamarth credit-linked portal.
    Status: PARTIAL (indexes credit categories: Education, Agri, MSME, Livelihood).
    """

    def __init__(
        self,
        source_id: str = "src-jansamarth-national",
        authority_tier: str = "tier5_official_portal",
        fetcher: Optional[SourceFetcher] = None,
    ):
        super().__init__(source_id=source_id, authority_tier=authority_tier)
        self.fetcher = fetcher or SourceFetcher()

    def discover(self, limit: Optional[int] = None) -> List[ProgramCandidate]:
        candidates: List[ProgramCandidate] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # Representative credit schemes hosted on JanSamarth
        credit_schemes = [
            {
                "title": "Central Sector Interest Subsidy (CSIS)",
                "url": "https://www.jansamarth.in/education-loan-schemes",
                "sector": ProgramSector.EDUCATION.value,
                "prog_type": ProgramType.GOVERNMENT_CREDIT_SUPPORT.value,
            },
            {
                "title": "Prime Minister Employment Generation Programme (PMEGP)",
                "url": "https://www.jansamarth.in/business-activity-loan-schemes",
                "sector": ProgramSector.BUSINESS_MSME.value,
                "prog_type": ProgramType.GOVERNMENT_LOAN.value,
            },
            {
                "title": "Weaver Mudra Scheme",
                "url": "https://www.jansamarth.in/business-activity-loan-schemes",
                "sector": ProgramSector.BUSINESS_MSME.value,
                "prog_type": ProgramType.GOVERNMENT_LOAN.value,
            },
            {
                "title": "Agri Clinics and Agri Business Centres Scheme (ACABC)",
                "url": "https://www.jansamarth.in/agri-loan-schemes",
                "sector": ProgramSector.AGRICULTURE.value,
                "prog_type": ProgramType.GOVERNMENT_CREDIT_SUPPORT.value,
            },
        ]
        if limit:
            credit_schemes = credit_schemes[:limit]

        for item in credit_schemes:
            title = item["title"]
            url = item["url"]
            content_hash = hashlib.sha256(f"{title}|{url}".encode("utf-8")).hexdigest()
            cand_id = generate_candidate_id(self.source_id, title)

            cand = ProgramCandidate(
                candidate_id=cand_id,
                program_type=item["prog_type"],
                sector=item["sector"],
                provider_type=ProviderType.GOVERNMENT_CENTRAL.value,
                provider_name="Ministry of Finance / JanSamarth Platform",
                official_name=title,
                source_url=url,
                source_domain="jansamarth.in",
                source_id=self.source_id,
                authority_tier=self.authority_tier,
                discovery_method="credit_scheme_index",
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
                raw_metadata={"platform": "JanSamarth", "status_classification": "PARTIAL"},
            )
            candidates.append(cand)

        return candidates

    def fetch_source(self, candidate: ProgramCandidate) -> Tuple[int, bytes, str]:
        res = self.fetcher.fetch(candidate.source_url)
        return res.status_code, res.content, res.content_type
