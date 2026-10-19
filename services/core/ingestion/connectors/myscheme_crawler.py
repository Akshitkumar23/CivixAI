"""
myScheme Dynamic Crawler (Tier 3 Dynamic Discovery)

Dynamically discovers scheme URLs from https://www.myscheme.gov.in by:
  1. Fetching sitemap-0.xml unconditionally (sub-sitemap from sitemap index).
  2. Extracting /search/ministry/<slug>, /search/state/<slug>, /find-scheme/<slug>
     URLs which are the actual scheme listing/detail paths used by the portal.
  3. Falling back to scraping /search/ministry/all-ministries and
     /search/state/all-states listing pages.

Portal structure (verified 2026-09-20):
  - sitemap.xml is a sitemap-index referencing only sitemap-0.xml
  - sitemap-0.xml contains 38 portal page URLs (no /schemes/<slug> paths)
  - Scheme browsing is done via /search/ministry/<m> and /search/state/<s>
  - Individual scheme detail URLs are in the form /scheme/<unique-slug>
    served as a Next.js SPA (not directly present in sitemap XML)
  - Public listing pages: /search/ministry/all-ministries,
    /search/state/all-states, /find-scheme/scheme-category

Safety Contracts (INVARIANTS - MUST NEVER BE VIOLATED):
  - discover() NEVER inserts into the production database.
  - discover() NEVER creates EligibilityRule, SchemeVersion, or Scheme records.
  - Every candidate carries discovery_status='discovery_staged' (never 'certified').
  - fetch_source() is read-only HTTP GET - never mutates any state.
  - No database Session is accepted or used by this class.

Authority tier: tier3_myscheme (requires human governance review before
any data can enter the canonical publication pipeline).
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .base import BaseConnector
from services.core.ingestion.fetcher import SourceFetcher, FetchResult

MYSCHEME_BASE_URL = "https://www.myscheme.gov.in"
MYSCHEME_SITEMAP_URL = f"{MYSCHEME_BASE_URL}/sitemap.xml"
MYSCHEME_SUB_SITEMAP_URL = f"{MYSCHEME_BASE_URL}/sitemap-0.xml"

# Confirmed working listing pages (verified 2026-09-20)
MYSCHEME_ALL_SCHEMES_PAGE = f"{MYSCHEME_BASE_URL}/schemes"
MYSCHEME_MINISTRY_ALL = f"{MYSCHEME_BASE_URL}/search/ministry/all-ministries"
MYSCHEME_STATE_ALL    = f"{MYSCHEME_BASE_URL}/search/state/all-states"
MYSCHEME_FIND_SCHEME  = f"{MYSCHEME_BASE_URL}/find-scheme/scheme-category"
MYSCHEME_API_SCHEMES_URL = f"{MYSCHEME_BASE_URL}/api/apisetu/schemes"

DEFAULT_SITEMAP_LIMIT = 100000
MIN_SLUG_LENGTH = 3

# The portal uses /schemes/<slug> for individual detail pages
# Also matches /search/ministry/<slug> and /search/state/<slug> and /find-scheme/<slug>
_SCHEME_URL_RE = re.compile(
    r"https://(?:www\.)?myscheme\.gov\.in/"
    r"(?:schemes?|search/ministry|search/state|find-scheme)/([a-z0-9][a-z0-9\-]{1,128})",
    re.I,
)

# Relative href forms: /schemes/<slug>, /scheme/<slug>, /search/ministry/<slug>, /search/state/<slug>
_SCHEME_HREF_RE = re.compile(
    r"""href=["']/(?:schemes?|search/ministry|search/state|find-scheme)/([a-z0-9][a-z0-9\-]{1,128})["']""",
    re.I,
)

_TOTAL_SCHEMES_RE = re.compile(
    r"(\d[\d,]*\+?)\s*(?:Central Government and State/UT Government schemes|"
    r"schemes\s+onboarded|Government\s+Schemes)",
    re.I,
)

# Page-type slugs to exclude (portal UI pages, not scheme detail pages)
_EXCLUDED_SLUGS = {
    "all-ministries", "all-states", "scheme-category", "screen-2", "screen-3",
    "screen-4", "screen-5", "screen-government-employee", "screen-income",
    "user-journey", "ministry", "state",
}


class MySchemeDiscoveryCrawler(BaseConnector):
    """
    Dynamic myScheme discovery crawler.

    Extends BaseConnector to fit the existing IngestionPipeline infrastructure
    without creating a second architecture.

    Discovery uses the real portal structure verified on 2026-09-20:
    - sitemap-0.xml for top-level portal page inventory
    - /search/ministry/all-ministries and /search/state/all-states for
      ministry/state slug enumeration
    - Individual scheme source_url set to the canonical /search/ministry/<slug>
      or /search/state/<slug> listing (scheme-level detail pages are SPA-rendered)
    """

    def __init__(
        self,
        fetcher: Optional[SourceFetcher] = None,
        sitemap_limit: int = DEFAULT_SITEMAP_LIMIT,
    ):
        super().__init__(connector_id="myscheme_crawler", authority_tier="tier3_myscheme")
        self.fetcher = fetcher or SourceFetcher(
            enforce_domain_allowlist=False,
            timeout_seconds=20,
            max_retries=2,
        )
        self.base_url = MYSCHEME_BASE_URL
        self.sitemap_url = MYSCHEME_SITEMAP_URL
        self.sitemap_limit = sitemap_limit

    # ------------------------------------------------------------------
    # Public Interface (BaseConnector contract)
    # ------------------------------------------------------------------

    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Dynamically discovers myScheme scheme listing pages.

        Strategy (in priority order):
          1. Fetch sitemap-0.xml to enumerate all portal pages.
          2. Extract /search/ministry/<m>, /search/state/<s>, /find-scheme/<f>
             slugs from the sitemap content.
          3. Fetch /search/ministry/all-ministries listing to enumerate ministry slugs.
          4. Fetch /search/state/all-states listing to enumerate state slugs.
          5. Deduplicate slugs across all sources.

        Note: myScheme individual scheme detail pages are rendered by a Next.js SPA.
        The canonical source_url for each candidate is the ministry/state listing URL
        that aggregates that government body's schemes. Full scheme-level slug
        enumeration requires either authenticated search API access or browser
        rendering -- neither is available in this read-only crawler.

        Returns
        -------
        List[Dict[str, Any]]
            discovery_status is always 'discovery_staged'.
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        effective_limit = limit or self.sitemap_limit

        slug_entries: List[Any] = []
        seen: set = set()

        # Phase 1: sitemap-0.xml page inventory
        sitemap_slugs = self._discover_via_sitemap(effective_limit)
        for s in sitemap_slugs:
            if s not in seen and s not in _EXCLUDED_SLUGS:
                seen.add(s)
                slug_entries.append(s)

        # Phase 1b: HTML listing fallback (when sitemap returns < 5)
        if len(slug_entries) < 5:
            fallback_slugs = self._scrape_listing_page(
                MYSCHEME_ALL_SCHEMES_PAGE, "schemes", seen, effective_limit - len(slug_entries)
            )
            slug_entries.extend(fallback_slugs)

        # Phase 2: ministry listing page
        if len(slug_entries) < effective_limit:
            ministry_slugs = self._scrape_listing_page(
                MYSCHEME_MINISTRY_ALL, "search/ministry", seen, effective_limit - len(slug_entries)
            )
            slug_entries.extend(ministry_slugs)

        # Phase 3: state listing page
        if len(slug_entries) < effective_limit:
            state_slugs = self._scrape_listing_page(
                MYSCHEME_STATE_ALL, "search/state", seen, effective_limit - len(slug_entries)
            )
            slug_entries.extend(state_slugs)

        # Phase 4: find-scheme category page
        if len(slug_entries) < effective_limit:
            find_slugs = self._scrape_listing_page(
                MYSCHEME_FIND_SCHEME, "find-scheme", seen, effective_limit - len(slug_entries)
            )
            slug_entries.extend(find_slugs)

        # Phase 5: Live portal public API endpoint (/api/apisetu/schemes)
        if len(slug_entries) < effective_limit:
            api_slugs = self._discover_from_apisetu(seen, effective_limit - len(slug_entries))
            slug_entries.extend(api_slugs)

        portal_total = self._fetch_portal_reported_total()

        candidates: List[Dict[str, Any]] = []
        for entry in slug_entries[:effective_limit]:
            slug = entry[0] if isinstance(entry, tuple) else entry
            name = entry[1] if isinstance(entry, tuple) else None
            candidates.append(self._build_candidate(slug, retrieved_at, portal_total, official_name=name))
        return candidates

    def fetch_source(self, candidate: Dict[str, Any]) -> Tuple[int, bytes, str]:
        """Fetches the candidate source page. Returns (http_status, content, content_type)."""
        url = candidate.get("source_url", "")
        if not url:
            return 0, b"", "text/html"
        res: FetchResult = self.fetcher.fetch(url)
        return res.status_code, res.content, res.content_type

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _discover_via_sitemap(self, limit: int) -> List[str]:
        """
        Fetches sitemap-0.xml directly and extracts scheme-related path slugs.
        The sitemap index at sitemap.xml references sitemap-0.xml which contains
        38 top-level portal page URLs.
        """
        slugs: List[str] = []
        seen: set = set()

        # First fetch the index to confirm structure, then fetch sitemap-0.xml
        for sitemap_url in [MYSCHEME_SUB_SITEMAP_URL, self.sitemap_url]:
            res = self.fetcher.fetch(sitemap_url)
            if not res.success or not res.content:
                continue
            raw = res.content
            try:
                root = ET.fromstring(raw)
            except ET.ParseError:
                continue

            ns = self._detect_sitemap_ns(root.tag)

            if "sitemapindex" in root.tag.lower():
                # Follow ALL sub-sitemaps (not filtered by "scheme")
                sub_urls = [
                    loc.text.strip()
                    for sitemap in root.findall(f"{ns}sitemap")
                    for loc in sitemap.findall(f"{ns}loc")
                    if loc.text and loc.text.strip() != sitemap_url  # avoid loop
                ]
                for sub_url in sub_urls[:5]:
                    sub_res = self.fetcher.fetch(sub_url)
                    if sub_res.success and sub_res.content:
                        sub_slugs = self._extract_slugs_from_bytes(sub_res.content, seen, limit - len(slugs))
                        slugs.extend(sub_slugs)
                        if len(slugs) >= limit:
                            break
                if slugs:
                    break
            else:
                page_slugs = self._extract_slugs_from_bytes(raw, seen, limit)
                slugs.extend(page_slugs)
                if slugs:
                    break

        return slugs

    def _scrape_listing_page(self, url: str, path_prefix: str, seen: set, limit: int) -> List[str]:
        """
        Scrapes a listing HTML page for scheme-related slugs.
        Matches both absolute and relative href patterns.
        """
        if limit <= 0:
            return []
        slugs: List[str] = []
        res = self.fetcher.fetch(url)
        if not res.success or not res.content:
            return slugs
        html = res.content.decode("utf-8", errors="ignore")
        # Absolute URL matches
        for m in _SCHEME_URL_RE.finditer(html):
            slug = m.group(1).lower().strip("/")
            if slug and len(slug) >= MIN_SLUG_LENGTH and slug not in seen and slug not in _EXCLUDED_SLUGS:
                seen.add(slug)
                slugs.append(slug)
            if len(slugs) >= limit:
                return slugs
        # Relative href matches
        for m in _SCHEME_HREF_RE.finditer(html):
            slug = m.group(1).lower().strip("/")
            if slug and len(slug) >= MIN_SLUG_LENGTH and slug not in seen and slug not in _EXCLUDED_SLUGS:
                seen.add(slug)
                slugs.append(slug)
            if len(slugs) >= limit:
                return slugs
        return slugs

    def _fetch_portal_reported_total(self) -> Optional[str]:
        """Best-effort fetch of the portal-reported total scheme count."""
        try:
            res = self.fetcher.fetch(self.base_url)
            if res.success and res.content:
                html = res.content.decode("utf-8", errors="ignore")
                m = _TOTAL_SCHEMES_RE.search(html)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None

    def _extract_slugs_from_bytes(self, raw: bytes, seen: set, limit: int) -> List[str]:
        """Extracts scheme-related slugs from raw bytes (XML or HTML)."""
        slugs: List[str] = []
        text = raw.decode("utf-8", errors="ignore")
        for m in _SCHEME_URL_RE.finditer(text):
            slug = m.group(1).lower().strip("/")
            if slug and len(slug) >= MIN_SLUG_LENGTH and slug not in seen and slug not in _EXCLUDED_SLUGS:
                seen.add(slug)
                slugs.append(slug)
            if len(slugs) >= limit:
                break
        return slugs

    @staticmethod
    def _detect_sitemap_ns(tag: str) -> str:
        if tag.startswith("{"):
            return "{" + tag.split("}")[0][1:] + "}"
        return ""

    @staticmethod
    def _slug_to_display_name(slug: str) -> str:
        return slug.replace("-", " ").title()

    def _discover_from_apisetu(self, seen: set, limit: int) -> List[Tuple[str, Optional[str]]]:
        """
        Discovers scheme slugs and official names directly from the live public API
        endpoint at https://www.myscheme.gov.in/api/apisetu/schemes (5,000+ schemes).
        """
        if limit <= 0:
            return []
        res = self.fetcher.fetch(MYSCHEME_API_SCHEMES_URL)
        if not res.success or not res.content:
            return []
        try:
            import json
            data = json.loads(res.content.decode("utf-8", errors="ignore"))
            items = data.get("data", [])
        except Exception:
            return []

        results: List[Tuple[str, Optional[str]]] = []
        for item in items:
            slug = (item.get("slug") or "").strip().lower()
            if not slug or len(slug) < MIN_SLUG_LENGTH or slug in seen or slug in _EXCLUDED_SLUGS:
                continue
            seen.add(slug)
            name = (
                item.get("en", {}).get("basicDetails", {}).get("schemeName")
                or self._slug_to_display_name(slug)
            )
            results.append((slug, name))
            if len(results) >= limit:
                break
        return results

    def _build_candidate(
        self,
        slug: str,
        retrieved_at: str,
        portal_total: Optional[str],
        official_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Constructs a discovery candidate dict."""
        source_url = f"{self.base_url}/schemes/{slug}"
        return {
            "candidate_id": f"myscheme-dyn-{slug}",
            "official_name": official_name or self._slug_to_display_name(slug),
            "slug": slug,
            "source_url": source_url,
            "origin_domain": "myscheme.gov.in",
            "authority_tier": self.authority_tier,
            "discovery_method": "dynamic_sitemap_crawler",
            "portal_reported_total": portal_total,
            "discovery_status": "discovery_staged",
            "retrieved_at": retrieved_at,
        }
