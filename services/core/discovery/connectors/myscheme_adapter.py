"""
myScheme Discovery Adapter
==========================
Connects to the official myScheme platform (https://www.myscheme.gov.in),
extracts indexed welfare programs via verified API and sitemap discovery,
and maps records into standardized ProgramCandidate instances.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
import hashlib
import json
import re

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
from services.core.ingestion.connectors.myscheme_crawler import MySchemeDiscoveryCrawler
from services.core.ingestion.fetcher import SourceFetcher


def classify_myscheme_program_type(title: str, tags: List[str]) -> str:
    """
    Classifies a myScheme program title and tags into the strict ProgramType taxonomy.
    """
    text = (title + " " + " ".join(tags)).lower()
    if any(w in text for w in ("scholarship", "fellowship", "stipend", "vidyarthi", "post matric", "pre matric")):
        return ProgramType.GOVERNMENT_SCHOLARSHIP.value
    if any(w in text for w in ("pension", "maandhan", "old age pension", "widow pension", "vridha")):
        return ProgramType.GOVERNMENT_PENSION.value
    if any(w in text for w in ("loan", "credit", "term loan", "micro-credit", "mudra", "stand-up")):
        return ProgramType.GOVERNMENT_LOAN.value
    if any(w in text for w in ("insurance", "bima", "suraksha", "accident insurance", "life insurance")):
        return ProgramType.GOVERNMENT_INSURANCE.value
    if any(w in text for w in ("housing", "awas", "shelter", "latrine", "ihhl")):
        return ProgramType.GOVERNMENT_HOUSING_PROGRAM.value
    if any(w in text for w in ("health", "medical", "treatment", "arogya", "swasthya", "disease", "hospital")):
        return ProgramType.GOVERNMENT_HEALTH_PROGRAM.value
    if any(w in text for w in ("kisan", "krishi", "agriculture", "farmer", "crop", "fisheries", "matsya")):
        return ProgramType.GOVERNMENT_AGRICULTURE_PROGRAM.value
    if any(w in text for w in ("employment", "rozgar", "shram", "skill", "training", "kaushalya")):
        return ProgramType.GOVERNMENT_EMPLOYMENT_PROGRAM.value
    if any(w in text for w in ("subsidy", "subsidies", "concession", "rebate")):
        return ProgramType.GOVERNMENT_SUBSIDY.value
    if any(w in text for w in ("grant", "assistance", "welfare fund", "financial assistance")):
        return ProgramType.GOVERNMENT_GRANT.value
    return ProgramType.GOVERNMENT_SCHEME.value


def classify_myscheme_sector(title: str, tags: List[str]) -> str:
    """
    Maps program title and tags to ProgramSector.
    """
    text = (title + " " + " ".join(tags)).lower()
    if any(w in text for w in ("kisan", "krishi", "agri", "farmer", "crop", "fisheries")):
        return ProgramSector.AGRICULTURE.value
    if any(w in text for w in ("health", "medical", "swasthya", "arogya", "treatment")):
        return ProgramSector.HEALTHCARE.value
    if any(w in text for w in ("scholarship", "education", "school", "college", "vidyarthi", "fellowship")):
        return ProgramSector.EDUCATION.value
    if any(w in text for w in ("housing", "awas", "shelter", "latrine")):
        return ProgramSector.HOUSING.value
    if any(w in text for w in ("employment", "rozgar", "shram", "kaushalya", "skill", "training")):
        return ProgramSector.EMPLOYMENT.value
    if any(w in text for w in ("loan", "credit", "banking", "finance", "mudra")):
        return ProgramSector.FINANCIAL_SERVICES.value
    if any(w in text for w in ("msme", "business", "enterprise", "industry")):
        return ProgramSector.BUSINESS_MSME.value
    return ProgramSector.SOCIAL_WELFARE.value


class MySchemeDiscoveryAdapter(BaseDiscoveryConnector):
    """
    Discovery connector adapter for the official myScheme portal.
    """

    def __init__(
        self,
        source_id: str = "src-myscheme-national",
        authority_tier: str = "tier3_myscheme",
        fetcher: Optional[SourceFetcher] = None,
    ):
        super().__init__(source_id=source_id, authority_tier=authority_tier)
        self.crawler = MySchemeDiscoveryCrawler(fetcher=fetcher)

    def discover(self, limit: Optional[int] = None) -> List[ProgramCandidate]:
        staged_dicts = self.crawler.discover(limit=limit)
        candidates: List[ProgramCandidate] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for d in staged_dicts:
            slug = d.get("slug", "")
            title = d.get("official_name") or d.get("title") or slug
            source_url = d.get("source_url") or f"https://www.myscheme.gov.in/schemes/{slug}"
            tags = d.get("tags") or []
            
            # Classify program type and sector
            prog_type = classify_myscheme_program_type(title, tags)
            sector = classify_myscheme_sector(title, tags)
            
            # Check jurisdiction
            is_state = d.get("state") or any("state" in t.lower() for t in tags)
            provider_type = (
                ProviderType.GOVERNMENT_STATE.value if is_state
                else ProviderType.GOVERNMENT_CENTRAL.value
            )
            provider_name = d.get("ministry") or ("State Government" if is_state else "Government of India")

            content_str = f"{title}|{source_url}|{slug}"
            content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

            cand_id = generate_candidate_id(self.source_id, slug or title)

            cand = ProgramCandidate(
                candidate_id=cand_id,
                program_type=prog_type,
                sector=sector,
                provider_type=provider_type,
                provider_name=provider_name,
                official_name=title,
                source_url=source_url,
                source_domain="myscheme.gov.in",
                source_id=self.source_id,
                authority_tier=self.authority_tier,
                discovery_method="myscheme_api_and_sitemap",
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
                    "slug": slug,
                    "tags": tags,
                    "ministry": d.get("ministry"),
                    "state": d.get("state"),
                },
            )
            candidates.append(cand)

        return candidates

    def fetch_source(self, candidate: ProgramCandidate) -> Tuple[int, bytes, str]:
        cand_dict = {
            "source_url": candidate.source_url,
            "slug": candidate.raw_metadata.get("slug", ""),
        }
        return self.crawler.fetch_source(cand_dict)
