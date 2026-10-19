"""
DBT Bharat Dynamic Discovery Crawler (Tier 2 DBT Index)

Dynamically discovers government scheme URLs from https://dbtbharat.gov.in,
the official Direct Benefit Transfer portal maintained by DBTM, Cabinet Secretariat.

Discovery Strategy:
  1. Primary: Parse the public /scheme-list or /schemes listing HTML for scheme links.
  2. Secondary: Parse the sitemap at https://dbtbharat.gov.in/sitemap.xml.
  3. Tertiary: Walk known category index pages (DBT categories exposed in nav).

Authority: dbtbharat.gov.in is a Tier 2 source (official GOI portal, higher trust
than myScheme tier-3 index, but still requires human governance review and
government document evidence before any rule reaches certified/published status).

Safety Contracts (INVARIANTS - MUST NEVER BE VIOLATED):
  - discover() NEVER inserts into the production database.
  - discover() NEVER creates EligibilityRule, SchemeVersion, or Scheme records.
  - Every candidate carries discovery_status='discovery_staged' (never 'certified').
  - fetch_source() is read-only HTTP GET - it never mutates any state.
  - No database Session is accepted or used by this class.
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from urllib.parse import urljoin

from .base import BaseConnector
from services.core.ingestion.fetcher import SourceFetcher, FetchResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DBTBHARAT_BASE_URL = "https://dbtbharat.gov.in"
DBTBHARAT_SITEMAP_URL = f"{DBTBHARAT_BASE_URL}/sitemap.xml"

# Known scheme listing endpoints on dbtbharat.gov.in
DBTBHARAT_SCHEME_LIST_URL = f"{DBTBHARAT_BASE_URL}/scheme/schemeList"
DBTBHARAT_SCHEME_LIST_ALT = f"{DBTBHARAT_BASE_URL}/scheme-list"
DBTBHARAT_CENTRAL_SCHEMES_URL = f"{DBTBHARAT_BASE_URL}/central-scheme/list"
DBTBHARAT_SERVICES_URL = f"{DBTBHARAT_BASE_URL}/dbtcell/service-list"

# Category index pages (Central scheme categories exposed in portal navigation)
DBTBHARAT_CATEGORY_PAGES = [
    f"{DBTBHARAT_BASE_URL}/scheme/schemeList/1",   # Cash Transfer
    f"{DBTBHARAT_BASE_URL}/scheme/schemeList/2",   # Food subsidy
    f"{DBTBHARAT_BASE_URL}/scheme/schemeList/3",   # Scholarship
    f"{DBTBHARAT_BASE_URL}/scheme/schemeList/4",   # Housing
    f"{DBTBHARAT_BASE_URL}/scheme/schemeList/5",   # Health
]

# Regex patterns for extracting scheme detail URLs from DBT Bharat HTML.
# The portal uses URL patterns like /schemeDetail/<id> or /scheme-detail/<slug>.
# Matches absolute URLs: /scheme/schemeDetail/<id>, /schemeDetail/<id>, /scheme-detail/<slug>
_DBT_SCHEME_DETAIL_RE = re.compile(
    r"https?://(?:www\.)?dbtbharat\.gov\.in/scheme(?:/schemeDetail|Detail|[/-]detail)/([a-zA-Z0-9_\-]+)",
    re.I,
)
# Relative href forms: href="/scheme/schemeDetail/123" or href="/schemeDetail/123"
_DBT_HREF_RE = re.compile(
    r"""href=["']/scheme(?:/schemeDetail|Detail)/([a-zA-Z0-9_\-]+)["']""",
    re.I,
)
# Sitemap URL pattern: matches /scheme/schemeDetail/<id>, /schemeDetail/<id>, /scheme-detail/<slug>
_DBT_SITEMAP_SLUG_RE = re.compile(
    r"dbtbharat\.gov\.in/scheme(?:/schemeDetail|Detail|[/-]detail)/([a-zA-Z0-9_\-]+)",
    re.I,
)

DEFAULT_DISCOVERY_LIMIT = 100000
MIN_SCHEME_ID_LENGTH = 1


class DBTBharatDiscoveryCrawler(BaseConnector):
    """
    Dynamic DBT Bharat discovery crawler.

    Extends BaseConnector to integrate with the existing IngestionPipeline
    without creating a second ingestion architecture.

    DBT Bharat authority tier is tier2_dbt_bharat - higher trust than
    myScheme (tier-3) but still requires human governance + government
    document evidence before any rule is certified or published.

    Usage::

        crawler = DBTBharatDiscoveryCrawler()
        candidates = crawler.discover(limit=50)
        status, content, ctype = crawler.fetch_source(candidates[0])
    """

    def __init__(
        self,
        fetcher: Optional[SourceFetcher] = None,
        discovery_limit: int = DEFAULT_DISCOVERY_LIMIT,
    ):
        super().__init__(
            connector_id="dbtbharat_crawler",
            authority_tier="tier2_dbt_bharat",
        )
        # Allow injecting a mock fetcher for unit-testing without network I/O.
        self.fetcher = fetcher or SourceFetcher(
            enforce_domain_allowlist=True,   # dbtbharat.gov.in is in .gov.in allowlist
            timeout_seconds=25,
            max_retries=2,
        )
        self.base_url = DBTBHARAT_BASE_URL
        self.discovery_limit = discovery_limit

    # ------------------------------------------------------------------
    # Public Interface (BaseConnector contract)
    # ------------------------------------------------------------------

    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Dynamically discovers DBT Bharat scheme candidates.

        Strategy (in priority order):
          1. Fetch primary scheme listing page (/scheme/schemeList).
          2. Parse sitemap.xml for scheme detail URLs.
          3. Walk known category index pages.
          4. Deduplicate scheme IDs across all sources.

        Returns
        -------
        List[Dict[str, Any]]
            Each element is a discovery candidate dict with:
            - candidate_id      : globally unique, stable across runs
            - official_name     : id-derived heuristic label (NOT authoritative)
            - scheme_id         : DBT portal scheme ID or slug
            - source_url        : canonical DBT Bharat scheme detail URL
            - origin_domain     : "dbtbharat.gov.in"
            - authority_tier    : "tier2_dbt_bharat"
            - discovery_status  : "discovery_staged"  <-- INVARIANT: never "certified"
            - retrieved_at      : ISO-8601 UTC timestamp
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        effective_limit = limit or self.discovery_limit

        scheme_entries: List[Dict[str, Any]] = []
        seen: set = set()

        # Phase 1: Primary listing page
        phase1_ids = self._discover_from_listing_page(
            DBTBHARAT_SCHEME_LIST_URL, seen, effective_limit
        )
        for sid in phase1_ids:
            scheme_entries.append({"scheme_id": sid})

        # Phase 1b: Alt listing URL if primary gave < 3 results
        if len(scheme_entries) < 3:
            phase1b_ids = self._discover_from_listing_page(
                DBTBHARAT_SCHEME_LIST_ALT, seen, effective_limit - len(scheme_entries)
            )
            for sid in phase1b_ids:
                scheme_entries.append({"scheme_id": sid})

        # Phase 1c: Live portal central schemes listing page (/central-scheme/list)
        if len(scheme_entries) < effective_limit:
            central_entries = self._discover_from_central_schemes_page(
                seen, effective_limit - len(scheme_entries)
            )
            scheme_entries.extend(central_entries)

        # Phase 2: Sitemap
        if len(scheme_entries) < effective_limit:
            phase2_ids = self._discover_via_sitemap(seen, effective_limit - len(scheme_entries))
            for sid in phase2_ids:
                scheme_entries.append({"scheme_id": sid})

        # Phase 3: Category pages (only if still under limit)
        if len(scheme_entries) < effective_limit:
            for cat_url in DBTBHARAT_CATEGORY_PAGES:
                if len(scheme_entries) >= effective_limit:
                    break
                cat_ids = self._discover_from_listing_page(
                    cat_url, seen, effective_limit - len(scheme_entries)
                )
                for sid in cat_ids:
                    scheme_entries.append({"scheme_id": sid})

        portal_scheme_count = self._fetch_portal_scheme_count()

        candidates: List[Dict[str, Any]] = []
        for item in scheme_entries[:effective_limit]:
            sid = item["scheme_id"]
            name = item.get("official_name")
            surl = item.get("source_url")
            candidates.append(
                self._build_candidate(
                    sid,
                    retrieved_at,
                    portal_scheme_count,
                    official_name=name,
                    source_url=surl,
                )
            )
        return candidates

    def fetch_source(self, candidate: Dict[str, Any]) -> Tuple[int, bytes, str]:
        """
        Fetches the scheme detail page for a given candidate.

        Returns
        -------
        Tuple[int, bytes, str]
            (http_status, content_bytes, content_type)
        """
        url = candidate.get("source_url", "")
        if not url:
            return 0, b"", "text/html"
        res: FetchResult = self.fetcher.fetch(url)
        return res.status_code, res.content, res.content_type

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _discover_from_listing_page(
        self, url: str, seen: set, limit: int
    ) -> List[str]:
        """
        Fetches a DBT Bharat listing/category page and extracts scheme IDs
        from both absolute href patterns and relative href patterns.
        """
        if limit <= 0:
            return []

        res = self.fetcher.fetch(url)
        if not res.success or not res.content:
            return []

        html = res.content.decode("utf-8", errors="ignore")
        return self._extract_scheme_ids_from_html(html, seen, limit)

    def _discover_via_sitemap(self, seen: set, limit: int) -> List[str]:
        """
        Parses dbtbharat.gov.in/sitemap.xml for scheme detail URLs.
        Handles both sitemap-index and standard sitemap formats.
        """
        if limit <= 0:
            return []

        res = self.fetcher.fetch(DBTBHARAT_SITEMAP_URL)
        if not res.success or not res.content:
            return []

        raw_xml = res.content
        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError:
            return self._extract_scheme_ids_from_bytes(raw_xml, seen, limit)

        ns = self._detect_sitemap_ns(root.tag)

        if "sitemapindex" in root.tag.lower():
            scheme_ids: List[str] = []
            sub_urls = [
                loc.text.strip()
                for sitemap in root.findall(f"{ns}sitemap")
                for loc in sitemap.findall(f"{ns}loc")
                if loc.text and "scheme" in loc.text.lower()
            ]
            for sub_url in sub_urls[:4]:
                sub_res = self.fetcher.fetch(sub_url)
                if sub_res.success and sub_res.content:
                    sub_ids = self._extract_scheme_ids_from_bytes(
                        sub_res.content, seen, limit - len(scheme_ids)
                    )
                    scheme_ids.extend(sub_ids)
                    if len(scheme_ids) >= limit:
                        break
            return scheme_ids

        return self._extract_scheme_ids_from_bytes(raw_xml, seen, limit)

    def _discover_from_central_schemes_page(
        self, seen: set, limit: int
    ) -> List[Dict[str, Any]]:
        """
        Discovers active Central Government DBT schemes from the live portal
        at https://dbtbharat.gov.in/central-scheme/list (295 schemes).
        """
        if limit <= 0:
            return []
        res = self.fetcher.fetch(DBTBHARAT_CENTRAL_SCHEMES_URL)
        if not res.success or not res.content:
            return []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.content, "html.parser")
            main = soup.find(id="mainContent")
            if not main:
                return []
            links = main.find_all("a")
        except Exception:
            return []

        entries: List[Dict[str, Any]] = []
        for a in links:
            href = a.get("href", "").strip()
            text = a.get_text(strip=True)
            if (
                not href
                or href.startswith("javascript")
                or href.startswith("#")
                or href == self.base_url
                or href == f"{self.base_url}/"
                or not text
                or len(text) < 3
            ):
                continue

            slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
            if not slug or len(slug) < MIN_SCHEME_ID_LENGTH or slug in seen:
                continue
            seen.add(slug)
            entries.append({
                "scheme_id": slug,
                "official_name": text,
                "source_url": href,
            })
            if len(entries) >= limit:
                break

        return entries

    def _fetch_portal_scheme_count(self) -> Optional[int]:
        """
        Best-effort fetch of the total DBT scheme count from the portal home page.
        Returns None on any failure.
        """
        _COUNT_RE = re.compile(r"(\d[\d,]*)\s*(?:schemes?|beneficiary schemes)", re.I)
        _STAT_RE = re.compile(r"NO\.\s*OF\s*SCHEMES[^\d]{1,60}(\d+)", re.I)
        try:
            res = self.fetcher.fetch(self.base_url)
            if res.success and res.content:
                html = res.content.decode("utf-8", errors="ignore")
                m_stat = _STAT_RE.search(html)
                if m_stat:
                    return int(m_stat.group(1).replace(",", ""))
                m = _COUNT_RE.search(html)
                if m:
                    raw = m.group(1).replace(",", "")
                    return int(raw)
        except Exception:
            pass
        return None

    def _extract_scheme_ids_from_html(
        self, html: str, seen: set, limit: int
    ) -> List[str]:
        """Extracts DBT scheme IDs from HTML using both absolute and relative patterns."""
        scheme_ids: List[str] = []

        # Absolute URLs
        for m in _DBT_SCHEME_DETAIL_RE.finditer(html):
            sid = m.group(1).strip()
            if sid and len(sid) >= MIN_SCHEME_ID_LENGTH and sid not in seen:
                seen.add(sid)
                scheme_ids.append(sid)
            if len(scheme_ids) >= limit:
                return scheme_ids

        # Relative hrefs (href="/scheme/schemeDetail/123")
        for m in _DBT_HREF_RE.finditer(html):
            sid = m.group(1).strip()
            if sid and len(sid) >= MIN_SCHEME_ID_LENGTH and sid not in seen:
                seen.add(sid)
                scheme_ids.append(sid)
            if len(scheme_ids) >= limit:
                return scheme_ids

        return scheme_ids

    def _extract_scheme_ids_from_bytes(
        self, raw: bytes, seen: set, limit: int
    ) -> List[str]:
        """Extracts DBT scheme IDs from raw bytes (sitemap XML or HTML)."""
        text = raw.decode("utf-8", errors="ignore")
        scheme_ids: List[str] = []

        for m in _DBT_SITEMAP_SLUG_RE.finditer(text):
            sid = m.group(1).strip()
            if sid and len(sid) >= MIN_SCHEME_ID_LENGTH and sid not in seen:
                seen.add(sid)
                scheme_ids.append(sid)
            if len(scheme_ids) >= limit:
                break

        # Also try HTML patterns on the same text
        if len(scheme_ids) < limit:
            for m in _DBT_HREF_RE.finditer(text):
                sid = m.group(1).strip()
                if sid and len(sid) >= MIN_SCHEME_ID_LENGTH and sid not in seen:
                    seen.add(sid)
                    scheme_ids.append(sid)
                if len(scheme_ids) >= limit:
                    break

        return scheme_ids

    @staticmethod
    def _detect_sitemap_ns(tag: str) -> str:
        """Extracts XML namespace prefix from a root tag string."""
        if tag.startswith("{"):
            return "{" + tag.split("}")[0][1:] + "}"
        return ""

    @staticmethod
    def _scheme_id_to_display_name(scheme_id: str) -> str:
        """
        Converts a DBT scheme ID to a display label.
        CAUTION: heuristic label only - NOT an authoritative scheme name.
        """
        return str(scheme_id).replace("-", " ").replace("_", " ").title()

    def _build_candidate(
        self,
        scheme_id: str,
        retrieved_at: str,
        portal_scheme_count: Optional[int],
        official_name: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Constructs a discovery candidate dict for a given DBT scheme ID."""
        url = source_url or f"{self.base_url}/scheme/schemeDetail/{scheme_id}"
        name = official_name or self._scheme_id_to_display_name(scheme_id)
        return {
            "candidate_id": f"dbtbharat-dyn-{scheme_id}",
            "official_name": name,
            "scheme_id": scheme_id,
            "source_url": url,
            "origin_domain": "dbtbharat.gov.in",
            "authority_tier": self.authority_tier,
            "discovery_method": "dynamic_listing_crawler",
            "portal_scheme_count": portal_scheme_count,
            "discovery_status": "discovery_staged",
            "retrieved_at": retrieved_at,
        }
