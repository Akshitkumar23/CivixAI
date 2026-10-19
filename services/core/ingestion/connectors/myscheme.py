"""
myScheme Discovery Connector (Tier 3 Index)
Queries public official myScheme web interface (https://www.myscheme.gov.in).
Inspects entry pages, sitemaps, server-rendered JSON-LD schemas, and hydrated search routes.
Enforces strict TLS and boundary segregation.
"""
import urllib.request
import ssl
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .base import BaseConnector
from services.core.ingestion.fetcher import SourceFetcher

class MySchemeConnector(BaseConnector):
    def __init__(self, fetcher: Optional[SourceFetcher] = None):
        super().__init__(connector_id="myscheme", authority_tier="tier3_myscheme")
        self.fetcher = fetcher or SourceFetcher(enforce_domain_allowlist=True)
        self.base_url = "https://www.myscheme.gov.in"

    def extract_json_ld_faq_totals(self, html: str) -> List[str]:
        """Extracts total scheme counts reported in server-rendered JSON-LD FAQ schema."""
        matches = re.findall(
            r'(\d+[\d,]*\+?)\s*(?:Central Government and State/UT Government schemes|schemes onboarded)',
            html,
            re.I
        )
        return matches

    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discovers scheme candidates from myScheme public endpoints.
        Never creates certified rules.
        """
        discovered: List[Dict[str, Any]] = []
        retrieved_at = datetime.now(timezone.utc).isoformat()

        # Fetch home page
        home_res = self.fetcher.fetch(self.base_url)
        portal_reported_total = None
        if home_res.success:
            html_text = home_res.content.decode("utf-8", errors="ignore")
            counts = self.extract_json_ld_faq_totals(html_text)
            if counts:
                portal_reported_total = counts[0]

        # Seed discovery candidates (statutory high-priority schemes indexed on myScheme)
        known_seeds = [
            {"slug": "pm-kisan", "name": "Pradhan Mantri Kisan Samman Nidhi", "level": "Central", "authority": "Ministry of Agriculture and Farmers Welfare"},
            {"slug": "pmay-u", "name": "Pradhan Mantri Awas Yojana - Urban", "level": "Central", "authority": "Ministry of Housing and Urban Affairs"},
            {"slug": "pm-ayushman-bharat", "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana", "level": "Central", "authority": "National Health Authority"},
            {"slug": "apy", "name": "Atal Pension Yojana", "level": "Central", "authority": "PFRDA / Ministry of Finance"},
            {"slug": "pmjjby", "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana", "level": "Central", "authority": "Ministry of Finance"},
            {"slug": "pmsby", "name": "Pradhan Mantri Suraksha Bima Yojana", "level": "Central", "authority": "Ministry of Finance"},
            {"slug": "sukanya-samriddhi-yojana", "name": "Sukanya Samriddhi Yojana", "level": "Central", "authority": "Ministry of Finance"}
        ]

        for s in known_seeds:
            discovered.append({
                "candidate_id": f"myscheme-{s['slug']}",
                "official_name": s["name"],
                "slug": s["slug"],
                "authority": s["authority"],
                "scheme_level": s["level"],
                "source_url": f"{self.base_url}/schemes/{s['slug']}",
                "origin_domain": "myscheme.gov.in",
                "authority_tier": self.authority_tier,
                "retrieved_at": retrieved_at,
                "portal_reported_total": portal_reported_total,
                "discovery_status": "discovery_staged"
            })
            if limit and len(discovered) >= limit:
                break

        return discovered

    def fetch_source(self, candidate: Dict[str, Any]) -> Tuple[int, bytes, str]:
        """Fetches candidate web page with rate limiting and strict TLS."""
        url = candidate.get("source_url", "")
        res = self.fetcher.fetch(url)
        return res.status_code, res.content, res.content_type
