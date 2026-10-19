"""
Source Fetcher
Reliable HTTP fetcher with rate limiting, conditional headers (ETag/If-Modified-Since),
SSL resilience for government portals, and granular error categorization.
"""
import time
import urllib3
from urllib.parse import urlparse
from typing import Optional, Dict, Tuple
import requests

# Suppress InsecureRequestWarning when falling back for known government domains with national root CAs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from ..security.ssrf import validate_safe_url, SSRFSecurityViolation, SSRFSafeSession

DEFAULT_USER_AGENT = "CivixAI-GovVerificationBot/1.0 (+https://civix.ai/verification; compliance@civix.ai)"

class FetchResult:
    def __init__(
        self,
        url: str,
        status_code: int,
        content: bytes,
        content_type: str,
        outcome_category: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        error: Optional[str] = None,
        redirected: bool = False,
        original_url: Optional[str] = None,
        ssl_fallback_used: bool = False
    ):
        self.url = url
        self.status_code = status_code
        self.content = content
        self.content_type = content_type
        self.outcome_category = outcome_category # success, not_modified, redirected, timeout, unreachable, dns_error, 403_blocked, 404_not_found, 5xx_error, unsupported_content_type, manual_only
        self.etag = etag
        self.last_modified = last_modified
        self.error = error
        self.redirected = redirected
        self.original_url = original_url or url
        self.ssl_fallback_used = ssl_fallback_used
        self.success = 200 <= status_code < 300 and error is None
        self.is_not_modified = status_code == 304

ALLOWED_DOMAINS_SUFFIXES = (
    ".gov.in", ".nic.in", ".ac.in", ".edu.in", ".org.in", ".res.in",
    "jansamarth.in", "enps.nsdl.com", "indiapost.gov.in"
)
MAX_RESPONSE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max limit

class SourceFetcher:
    def __init__(
        self,
        timeout_seconds: int = 15,
        delay_between_domains: float = 0.5,
        max_retries: int = 2,
        enforce_domain_allowlist: bool = False,
        max_size_bytes: int = MAX_RESPONSE_SIZE_BYTES
    ):
        self.timeout = timeout_seconds
        self.delay = delay_between_domains
        self.max_retries = max_retries
        self.enforce_domain_allowlist = enforce_domain_allowlist
        self.max_size_bytes = max_size_bytes
        self.last_fetch_times: Dict[str, float] = {}

    def fetch(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> FetchResult:
        """
        Fetches official URL with rate limiting, conditional headers, SSL resilience, and error classification.
        """
        hostname = (urlparse(url).hostname or "").lower()
        if self.enforce_domain_allowlist:
            is_allowed = any(hostname == s.lstrip(".") or hostname.endswith(s) for s in ALLOWED_DOMAINS_SUFFIXES) or hostname.endswith(".test") or hostname == "testserver"
            if not is_allowed:
                return FetchResult(
                    url=url,
                    status_code=0,
                    content=b"",
                    content_type="text/html",
                    outcome_category="domain_not_allowed",
                    error=f"Domain '{hostname}' is not in the authorized government domain allowlist.",
                    original_url=url
                )

        try:
            validate_safe_url(url)
        except SSRFSecurityViolation as ssrf_err:
            return FetchResult(
                url=url,
                status_code=0,
                content=b"",
                content_type="text/html",
                outcome_category="ssrf_blocked",
                error=f"SSRF Security Violation: {ssrf_err}",
                original_url=url
            )

        domain = urlparse(url).netloc
        if domain in self.last_fetch_times:
            elapsed = time.time() - self.last_fetch_times[domain]
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self.last_fetch_times[domain] = time.time()

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8"
        }
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        last_error = None
        ssl_fallback = False

        for attempt in range(self.max_retries + 1):
            try:
                # Attempt 1: standard strict SSL verification
                verify_ssl = True if not ssl_fallback else False
                resp = requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=verify_ssl
                )

                content_type = resp.headers.get("Content-Type", "text/html").split(";")[0].strip()
                was_redirected = bool(resp.history)

                # Check max payload size
                content_length = resp.headers.get("Content-Length")
                if (content_length and int(content_length) > self.max_size_bytes) or len(resp.content) > self.max_size_bytes:
                    return FetchResult(
                        url=resp.url,
                        status_code=413,
                        content=b"",
                        content_type=content_type,
                        outcome_category="payload_too_large",
                        error=f"Payload exceeds maximum allowed limit ({self.max_size_bytes} bytes).",
                        original_url=url
                    )

                # Determine outcome category
                if resp.status_code == 304:
                    outcome = "not_modified"
                elif 200 <= resp.status_code < 300:
                    outcome = "redirected" if was_redirected else "success"
                elif resp.status_code in (401, 403):
                    outcome = "403_blocked"
                elif resp.status_code == 404:
                    outcome = "404_not_found"
                elif resp.status_code >= 500:
                    outcome = "5xx_error"
                else:
                    outcome = "unreachable"

                err_msg = None if (resp.ok or resp.status_code == 304) else f"HTTP {resp.status_code}"

                return FetchResult(
                    url=resp.url,
                    status_code=resp.status_code,
                    content=resp.content,
                    content_type=content_type,
                    outcome_category=outcome,
                    etag=resp.headers.get("ETag"),
                    last_modified=resp.headers.get("Last-Modified"),
                    error=err_msg,
                    redirected=was_redirected,
                    original_url=url,
                    ssl_fallback_used=ssl_fallback
                )

            except requests.exceptions.SSLError as ssl_err:
                # Many Indian portals (.gov.in, .nic.in) use national CCA root certificates not in Mozilla certifi
                if not ssl_fallback:
                    ssl_fallback = True
                    time.sleep(0.3)
                    continue
                last_error = f"SSL Error: {ssl_err}"
                return FetchResult(
                    url=url,
                    status_code=0,
                    content=b"",
                    content_type="text/html",
                    outcome_category="unreachable",
                    error=last_error,
                    original_url=url,
                    ssl_fallback_used=True
                )

            except requests.exceptions.ConnectTimeout as timeout_err:
                last_error = f"Connect Timeout: {timeout_err}"
                if attempt < self.max_retries:
                    time.sleep(0.5)
                    continue
                return FetchResult(
                    url=url,
                    status_code=0,
                    content=b"",
                    content_type="text/html",
                    outcome_category="timeout",
                    error=last_error,
                    original_url=url
                )

            except requests.exceptions.ConnectionError as conn_err:
                err_str = str(conn_err)
                if "getaddrinfo failed" in err_str or "NameResolutionError" in err_str:
                    outcome = "dns_error"
                else:
                    outcome = "unreachable"
                last_error = f"{outcome}: {conn_err}"
                if attempt < self.max_retries:
                    time.sleep(0.5)
                    continue
                return FetchResult(
                    url=url,
                    status_code=0,
                    content=b"",
                    content_type="text/html",
                    outcome_category=outcome,
                    error=last_error,
                    original_url=url
                )

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    time.sleep(0.5)
                    continue
                return FetchResult(
                    url=url,
                    status_code=0,
                    content=b"",
                    content_type="text/html",
                    outcome_category="unreachable",
                    error=last_error,
                    original_url=url
                )

        return FetchResult(
            url=url,
            status_code=0,
            content=b"",
            content_type="text/html",
            outcome_category="unreachable",
            error=last_error or "Unknown fetch error",
            original_url=url
        )
