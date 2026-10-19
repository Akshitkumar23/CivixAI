"""
myScheme Deep Acquisition & Extraction Engine
=============================================
Performs client-rendered deep acquisition of myScheme detail pages using Playwright.
Enforces:
- Exact raw snapshot preservation (compressed HTML bytes + SHA-256)
- Strict field extraction contract (missing fields default to UNKNOWN)
- Zero canonical DB mutation
- Decoupled evidence metadata
"""

import re
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from services.core.discovery.models import (
    ProgramCandidate,
    ProgramType,
    ProviderType,
    ProgramSector,
    SourceSnapshotRecord,
)
from services.core.discovery.snapshots import DurableSnapshotStore


class MySchemeDeepExtractor:
    """
    Automated client-rendered deep extractor for myScheme detail pages.
    """

    def __init__(
        self,
        snapshot_store: Optional[DurableSnapshotStore] = None,
        headless: bool = True,
    ):
        self.snapshot_store = snapshot_store or DurableSnapshotStore()
        self.headless = headless
        self._browser: Optional[Browser] = None
        self._playwright = None
        self._static_cache: Dict[str, Dict[str, Any]] = {}

    def setup_cache_route(self, context_or_page):
        """
        Intercepts requests to cdn.myscheme.in to cache static JS/CSS chunks in memory,
        preventing CloudFront rate-limiting (HTTP 429) across large batch crawls.
        """
        def handle_route(route):
            url = route.request.url
            if "cdn.myscheme.in" in url and any(
                ext in url for ext in [".js", ".css", ".svg", ".png", ".woff2", "_ssgManifest.js", "_buildManifest.js"]
            ):
                cached = self._static_cache.get(url)
                if cached:
                    try:
                        route.fulfill(body=cached["body"], status=200, headers=cached["headers"])
                        return
                    except Exception:
                        pass
                else:
                    try:
                        resp = route.fetch()
                        if resp.status == 200:
                            self._static_cache[url] = {"body": resp.body(), "headers": resp.headers}
                        route.fulfill(response=resp)
                        return
                    except Exception:
                        pass
            try:
                route.continue_()
            except Exception:
                pass

        try:
            context_or_page.route("**/*", handle_route)
        except Exception:
            pass

    def start(self):
        if not self._browser:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)

    def stop(self):
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def acquire_detail(self, slug: str, page: Optional[Page] = None, max_retries: int = 1) -> Dict[str, Any]:
        """
        Fetches the hydrated detail page, stores durable raw snapshot,
        and parses structured fields according to the strict extraction contract.
        Supports passing an existing Page or creating a fresh context.
        """
        if not self._browser:
            self.start()

        target_url = f"https://www.myscheme.gov.in/schemes/{slug}"
        t0 = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        owns_page = False
        context = None
        if page is None:
            owns_page = True
            context = self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            self.setup_cache_route(page)

        http_status = 200
        raw_html_bytes = b""
        extraction_status = "SUCCESS"
        template_category = "STANDARD_TEMPLATE"
        failure_reason = None
        error_msg = None
        nav_duration = 0.0
        hyd_duration = 0.0
        title = ""
        ministry = "UNKNOWN"
        sections: Dict[str, Optional[str]] = {}
        docs_list: List[str] = []
        structured_criteria: Dict[str, Any] = {}
        retries_performed = 0

        try:
            for attempt in range(max_retries + 1):
                failure_reason = None
                error_msg = None
                http_status = 200

                # 1. Direct navigation with domcontentloaded
                t_nav_0 = time.time()
                try:
                    resp = page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
                    if resp:
                        http_status = resp.status
                except Exception as e_nav:
                    err_str = str(e_nav).lower()
                    if "timeout" in err_str:
                        failure_reason = "FAILED_TIMEOUT"
                    else:
                        failure_reason = "FAILED_NETWORK"
                    error_msg = str(e_nav)
                nav_duration = round(time.time() - t_nav_0, 2)

                if http_status >= 400:
                    extraction_status = "FAILED"
                    failure_reason = f"HTTP_{http_status // 100}XX"
                    template_category = "EXTRACTION_ERROR"

                # 2. Explicit DOM hydration polling
                if not failure_reason:
                    t_hyd_0 = time.time()
                    try:
                        page.wait_for_function(
                            """() => {
                                const details = document.querySelector('#details');
                                const elig = document.querySelector('#eligibility');
                                const ben = document.querySelector('#benefits');
                                const bodyText = document.body ? document.body.innerText : '';
                                const is404 = bodyText.includes('Page not found') || bodyText.includes("couldn't find the page");
                                const hasHydrated = (details && details.innerText.trim().length > 0) ||
                                                    (elig && elig.innerText.trim().length > 0) ||
                                                    (ben && ben.innerText.trim().length > 0);
                                return hasHydrated || is404;
                            }""",
                            timeout=15000
                        )
                        page.wait_for_timeout(300)
                    except Exception as e_hyd:
                        err_str = str(e_hyd).lower()
                        if "timeout" in err_str:
                            failure_reason = "FAILED_TIMEOUT"
                        else:
                            failure_reason = "FAILED_EXTRACTION_ERROR"
                        error_msg = str(e_hyd)
                    hyd_duration = round(time.time() - t_hyd_0, 2)

                # 3. Capture DOM and analyze
                raw_html = page.content()
                raw_html_bytes = raw_html.encode("utf-8")
                body_text = page.locator("body").inner_text() if page.locator("body").count() > 0 else ""
                p_title = (page.title() or "").strip()

                is_404 = (
                    "page not found" in body_text.lower()
                    or "couldn't find the page" in body_text.lower()
                    or "page not found" in p_title.lower()
                    or http_status == 404
                )

                if is_404:
                    extraction_status = "FAILED"
                    failure_reason = "FAILED_PAGE_NOT_FOUND"
                    template_category = "EXTRACTION_ERROR"
                    break

                # Check for unhydrated SPA shell
                has_details = bool(page.locator("#details").count() > 0 and len(page.locator("#details").inner_text().strip()) > 0)
                has_elig = bool(page.locator("#eligibility").count() > 0 and len(page.locator("#eligibility").inner_text().strip()) > 0)
                has_ben = bool(page.locator("#benefits").count() > 0 and len(page.locator("#benefits").inner_text().strip()) > 0)

                if not is_404 and not (has_details or has_elig or has_ben):
                    extraction_status = "FAILED"
                    if len(raw_html_bytes) < 75000:
                        failure_reason = "FAILED_UNHYDRATED_SHELL"
                    elif not failure_reason:
                        failure_reason = "FAILED_SOURCE_STRUCTURE_UNKNOWN"
                    template_category = "EXTRACTION_ERROR"

                # If timeout or unhydrated shell occurred on early attempt, retry
                if failure_reason in ("FAILED_TIMEOUT", "FAILED_NETWORK", "FAILED_UNHYDRATED_SHELL") and attempt < max_retries:
                    retries_performed += 1
                    time.sleep(1.0)
                    continue

                if not failure_reason:
                    # Extract Title
                    valid_h1s = [
                        h.strip()
                        for h in page.locator("h1, h2").all_text_contents()
                        if h.strip() and len(h.strip()) > 3 and "myscheme" not in h.lower() and "page not found" not in h.lower()
                    ]
                    if valid_h1s:
                        title = valid_h1s[0]
                    if not title and p_title:
                        cand_title = p_title.split("|")[0].split("-")[0].strip()
                        if cand_title and "myscheme" not in cand_title.lower() and "page not found" not in cand_title.lower():
                            title = cand_title

                    # Extract Ministry
                    try:
                        ministry_el = page.locator("text=Ministry").first
                        if ministry_el.count() > 0:
                            text_val = ministry_el.text_content().strip()
                            if text_val and len(text_val) > 4:
                                ministry = text_val
                    except Exception:
                        pass

                    # Extract Sections
                    for sec_id in ["details", "benefits", "eligibility", "application-process", "documents-required", "faqs"]:
                        try:
                            el = page.locator(f"#{sec_id}")
                            if el.count() > 0:
                                sections[sec_id] = el.inner_text().strip()
                            else:
                                matches = page.locator(
                                    f"xpath=//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sec_id.replace('-', ' ')}')]"
                                )
                                if matches.count() > 0:
                                    sections[sec_id] = matches.first.locator("xpath=..").inner_text().strip()
                                else:
                                    sections[sec_id] = None
                        except Exception:
                            sections[sec_id] = None

                    # Extract Documents Required List
                    try:
                        docs_el = page.locator("#documents-required li, #documents-required p")
                        count = docs_el.count()
                        for i in range(count):
                            txt = docs_el.nth(i).text_content().strip()
                            if txt and len(txt) > 2 and txt not in docs_list:
                                docs_list.append(txt)
                    except Exception:
                        pass

                    # Parse Structured Criteria
                    eligibility_full = sections.get("eligibility") or ""
                    structured_criteria = self._parse_structured_criteria(eligibility_full, sections.get("details") or "")

                    # Strict Success / Partial Contract
                    has_core = bool(title and sections.get("details") and sections.get("eligibility") and sections.get("benefits"))
                    has_optional = bool(sections.get("application-process") or docs_list)

                    if has_core and has_optional:
                        extraction_status = "SUCCESS"
                        template_category = "STANDARD_TEMPLATE"
                        failure_reason = None
                    elif has_core:
                        extraction_status = "PARTIAL"
                        failure_reason = "PARTIAL_OPTIONAL_FIELD_MISSING"
                        template_category = "STANDARD_TEMPLATE"
                    elif title and (sections.get("details") or sections.get("eligibility") or sections.get("benefits")):
                        extraction_status = "PARTIAL"
                        failure_reason = "PARTIAL_SOURCE_SPARSE"
                        template_category = "ALTERNATIVE_TEMPLATE"
                    else:
                        extraction_status = "FAILED"
                        failure_reason = "FAILED_SOURCE_STRUCTURE_UNKNOWN"
                        template_category = "EXTRACTION_ERROR"

                break

        except Exception as e:
            extraction_status = "FAILED"
            template_category = "EXTRACTION_ERROR"
            if not failure_reason:
                failure_reason = "FAILED_TIMEOUT" if "timeout" in str(e).lower() else "FAILED_EXTRACTION_ERROR"
            error_msg = str(e)
            title = ""
            ministry = "UNKNOWN"
            sections = {}
            docs_list = []
            structured_criteria = {}
        finally:
            if owns_page and context:
                try:
                    context.close()
                except Exception:
                    pass

        dur = time.time() - t0

        # Store raw snapshot
        snapshot_rec = None
        if raw_html_bytes:
            snapshot_rec = self.snapshot_store.record_snapshot(
                source_id="src-myscheme-national",
                url=target_url,
                canonical_url=target_url,
                http_status=http_status,
                content=raw_html_bytes,
                content_type="text/html; charset=utf-8",
            )

        fields_extracted = []
        fields_missing = []

        field_map = {
            "official_name": title if title else None,
            "ministry": ministry if ministry != "UNKNOWN" else None,
            "description": sections.get("details"),
            "benefits": sections.get("benefits"),
            "eligibility": sections.get("eligibility"),
            "application_process": sections.get("application-process"),
            "documents_required": docs_list if docs_list else None,
        }

        for f_name, f_val in field_map.items():
            if f_val:
                fields_extracted.append(f_name)
            else:
                fields_missing.append(f_name)

        return {
            "slug": slug,
            "source_url": target_url,
            "http_status": http_status,
            "duration_sec": round(dur, 2),
            "nav_duration_sec": nav_duration,
            "hyd_duration_sec": hyd_duration,
            "retry_count": retries_performed,
            "bytes_downloaded": len(raw_html_bytes),
            "snapshot_id": snapshot_rec.snapshot_id if snapshot_rec else None,
            "snapshot_hash": snapshot_rec.content_sha256 if snapshot_rec else None,
            "snapshot_path": snapshot_rec.storage_uri if snapshot_rec else None,
            "extraction_status": extraction_status,
            "template_category": template_category,
            "failure_reason": failure_reason,
            "error": error_msg,
            "parser_version": "v3.2_domcontentloaded_polled",
            "extraction_version": "v3.2_hardened_contract",
            "first_seen_at": now_iso,
            "last_attempted_fetch": now_iso,
            "last_successful_fetch": now_iso if extraction_status == "SUCCESS" else None,
            "change_status": snapshot_rec.change_status if snapshot_rec else "NEW",
            "previous_content_hash": None,
            "official_name": title or "UNKNOWN",
            "ministry": ministry,
            "description": sections.get("details") or "UNKNOWN",
            "benefits": sections.get("benefits") or "UNKNOWN",
            "eligibility_text": sections.get("eligibility") or "UNKNOWN",
            "application_process": sections.get("application-process") or "UNKNOWN",
            "documents_required": docs_list,
            "structured_criteria": structured_criteria,
            "fields_extracted": fields_extracted,
            "fields_missing": fields_missing,
            "retrieval_time": now_iso,
        }

    @staticmethod
    def _parse_structured_criteria(eligibility_text: str, details_text: str) -> Dict[str, Any]:
        """
        Extracts structured eligibility criteria without fabricating missing variables.
        """
        combined = f"{eligibility_text} {details_text}".lower()
        criteria = {
            "min_age": "UNKNOWN",
            "max_age": "UNKNOWN",
            "gender": "UNKNOWN",
            "occupation": "UNKNOWN",
            "income_limit": "UNKNOWN",
            "caste_category": "UNKNOWN",
            "scope": "National",
        }

        # Age patterns (e.g. between 18 and 59 years, age 18 to 60)
        age_m = re.search(r"between\s+(\d{1,2})\s+(?:and|to)\s+(\d{1,2})\s+years?", combined)
        if age_m:
            criteria["min_age"] = int(age_m.group(1))
            criteria["max_age"] = int(age_m.group(2))
        else:
            min_m = re.search(r"(?:minimum|at least)\s+age\s+(?:of\s+)?(\d{1,2})", combined)
            if min_m:
                criteria["min_age"] = int(min_m.group(1))
            max_m = re.search(r"(?:maximum|up to)\s+age\s+(?:of\s+)?(\d{1,2})", combined)
            if max_m:
                criteria["max_age"] = int(max_m.group(1))

        # Gender restrictions
        if "only women" in combined or "female only" in combined or "for women" in combined:
            criteria["gender"] = "Female"
        elif "only men" in combined or "male only" in combined:
            criteria["gender"] = "Male"

        # Occupation
        if "artisan" in combined or "weaver" in combined or "spinner" in combined:
            criteria["occupation"] = "Artisan / Weaver"
        elif "farmer" in combined or "kisan" in combined:
            criteria["occupation"] = "Farmer"
        elif "student" in combined or "vidyarthi" in combined:
            criteria["occupation"] = "Student"

        # Income limit
        inc_m = re.search(r"(?:income|annual income)[^\d]{1,30}(?:rs\.?|₹)\s*([\d,]+)", combined)
        if inc_m:
            criteria["income_limit"] = inc_m.group(1).replace(",", "")

        # Caste / Social category
        if "sc/st" in combined or "sc / st" in combined:
            criteria["caste_category"] = "SC/ST"
        elif "minority" in combined:
            criteria["caste_category"] = "Minority"

        return criteria
