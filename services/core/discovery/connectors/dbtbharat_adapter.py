"""
DBT Bharat Discovery Adapter
============================
Connects to the official Direct Benefit Transfer (DBT) Bharat platform
(https://dbtbharat.gov.in/central-scheme/list), discovers active central benefit
programs across 56 Union Ministries, and stages ProgramCandidate instances.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
import hashlib
from urllib.parse import urlparse

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
from services.core.ingestion.connectors.dbtbharat_crawler import DBTBharatDiscoveryCrawler
from services.core.ingestion.fetcher import SourceFetcher


def classify_dbt_program_type(title: str, benefit_type: str = "") -> str:
    """
    Classifies a DBT Bharat program into the strict ProgramType taxonomy.
    """
    text = (title + " " + benefit_type).lower()
    if any(w in text for w in ("scholarship", "fellowship", "stipend", "jrf", "srf")):
        return ProgramType.GOVERNMENT_SCHOLARSHIP.value
    if any(w in text for w in ("pension", "nsap", "vridha", "widow")):
        return ProgramType.GOVERNMENT_PENSION.value
    if any(w in text for w in ("loan", "credit", "interest subvention", "fasal rin")):
        return ProgramType.GOVERNMENT_CREDIT_SUPPORT.value
    if any(w in text for w in ("bima", "insurance", "pmfby", "crop insurance")):
        return ProgramType.GOVERNMENT_INSURANCE.value
    if any(w in text for w in ("subsidy", "subsidies", "lpg", "fertilizer")):
        return ProgramType.GOVERNMENT_SUBSIDY.value
    if any(w in text for w in ("grant", "assistance", "fund", "financial assistance")):
        return ProgramType.GOVERNMENT_GRANT.value
    if any(w in text for w in ("housing", "awas", "pmay")):
        return ProgramType.GOVERNMENT_HOUSING_PROGRAM.value
    if any(w in text for w in ("health", "ayushman", "pmjay", "medical")):
        return ProgramType.GOVERNMENT_HEALTH_PROGRAM.value
    if any(w in text for w in ("kisan", "krishi", "agriculture", "farmer", "crop", "icar")):
        return ProgramType.GOVERNMENT_AGRICULTURE_PROGRAM.value
    if any(w in text for w in ("mgnrega", "employment", "rozgar", "shram")):
        return ProgramType.GOVERNMENT_EMPLOYMENT_PROGRAM.value
    return ProgramType.GOVERNMENT_SCHEME.value


def classify_dbt_sector(ministry: str, title: str) -> str:
    """
    Maps DBT Ministry name and program title to ProgramSector.
    """
    text = (ministry + " " + title).lower()
    if any(w in text for w in ("agriculture", "farmer", "kisan", "icar", "crop", "fisheries")):
        return ProgramSector.AGRICULTURE.value
    if any(w in text for w in ("health", "family welfare", "ayush", "medical")):
        return ProgramSector.HEALTHCARE.value
    if any(w in text for w in ("education", "scholarship", "school", "higher education")):
        return ProgramSector.EDUCATION.value
    if any(w in text for w in ("housing", "urban affairs", "rural development", "awas")):
        return ProgramSector.HOUSING.value
    if any(w in text for w in ("labour", "employment", "skill", "entrepreneurship", "shram")):
        return ProgramSector.EMPLOYMENT.value
    if any(w in text for w in ("finance", "financial services", "banking")):
        return ProgramSector.FINANCIAL_SERVICES.value
    if any(w in text for w in ("micro, small", "msme", "commerce", "industry")):
        return ProgramSector.BUSINESS_MSME.value
    return ProgramSector.SOCIAL_WELFARE.value


class DBTBharatDiscoveryAdapter(BaseDiscoveryConnector):
    """
    Discovery connector adapter for DBT Bharat.
    """

    def __init__(
        self,
        source_id: str = "src-dbt-bharat-central",
        authority_tier: str = "tier2_dbt_bharat",
        fetcher: Optional[SourceFetcher] = None,
    ):
        super().__init__(source_id=source_id, authority_tier=authority_tier)
        self.crawler = DBTBharatDiscoveryCrawler(fetcher=fetcher)

    def discover(self, limit: Optional[int] = None) -> List[ProgramCandidate]:
        staged_dicts = self.crawler.discover(limit=limit)
        candidates: List[ProgramCandidate] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for d in staged_dicts:
            scheme_id = d.get("scheme_id") or ""
            title = d.get("official_name") or d.get("title") or scheme_id
            source_url = d.get("source_url") or "https://dbtbharat.gov.in/central-scheme/list"
            ministry = d.get("ministry") or "Government of India"

            prog_type = classify_dbt_program_type(title)
            sector = classify_dbt_sector(ministry, title)

            domain = urlparse(source_url).netloc or "dbtbharat.gov.in"
            content_str = f"{title}|{source_url}|{scheme_id}"
            content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

            cand_id = generate_candidate_id(self.source_id, scheme_id or title)

            cand = ProgramCandidate(
                candidate_id=cand_id,
                program_type=prog_type,
                sector=sector,
                provider_type=ProviderType.GOVERNMENT_CENTRAL.value,
                provider_name=ministry,
                official_name=title,
                source_url=source_url,
                source_domain=domain,
                source_id=self.source_id,
                authority_tier=self.authority_tier,
                discovery_method="dbtbharat_central_list",
                discovery_timestamp=now_iso,
                content_hash=content_hash,
                identity_key="",  # Populated by ProgramIdentityEngine
                possible_duplicate_of=[],
                discovery_status=DiscoveryStatus.DISCOVERY_STAGED.value,
                verification_status="unverified",
                currentness_status=CurrentnessStatus.FRESH.value,
                evidence_status=EvidenceStatus.EVIDENCE_ABSENT.value,
                governance_status=GovernanceStatus.UNREVIEWED.value,
                eligibility_summary="UNKNOWN",  # Never invent
                benefit_summary="UNKNOWN",      # Never invent
                raw_metadata={
                    "scheme_id": scheme_id,
                    "ministry": ministry,
                    "benefit_type": d.get("benefit_type"),
                },
            )
            candidates.append(cand)

        return candidates

    def fetch_source(self, candidate: ProgramCandidate) -> Tuple[int, bytes, str]:
        cand_dict = {
            "source_url": candidate.source_url,
            "scheme_id": candidate.raw_metadata.get("scheme_id", ""),
        }
        return self.crawler.fetch_source(cand_dict)
