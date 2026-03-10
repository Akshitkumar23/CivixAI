import csv
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MASTER_PATH = DATA_DIR / "master" / "schemes_master.csv"
SOURCES_PATH = Path(__file__).resolve().parent / "sources.json"


MASTER_COLUMNS = [
    "scheme_id",
    "scheme_name",
    "ministry",
    "scheme_level",
    "scheme_type",
    "scheme_category",
    "documents_required",
    "application_url",
    "benefit_description",
    "min_age",
    "max_age",
    "income_limit",
    "applicable_states",
    "special_conditions_required",
    "source_url",
    "benefit_type",
]


@dataclass
class Source:
    id: str
    type: str
    url: Optional[str] = None
    resource_id: Optional[str] = None
    scheme_level: str = "central"
    scheme_type: str = "central"
    scheme_category: str = "mixed"
    applicable_states: str = ""
    notes: str = ""


def load_sources() -> Tuple[str, float, List[Source]]:
    raw = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    user_agent = raw.get("user_agent", "CivixAI-SchemeScraper/1.0")
    rate_limit = float(raw.get("rate_limit_seconds", 1.5))
    sources = [Source(**s) for s in raw.get("sources", [])]
    return user_agent, rate_limit, sources


def can_fetch(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = requests.get(
            robots_url,
            headers={"User-Agent": user_agent},
            timeout=20,
        )
        if resp.status_code == 404:
            return True
        if resp.status_code >= 400:
            return False
        rp = RobotFileParser()
        rp.parse(resp.text.splitlines())
        return rp.can_fetch(user_agent, url)
    except Exception:
        # Network or TLS failure while reading robots: deny.
        return False


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    return text.strip("_")[:60]


def fetch_url(url: str, user_agent: str) -> str:
    headers = {"User-Agent": user_agent}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_dbt_haryana(html: str, source: Source) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict[str, Any]] = []

    # On DBT Haryana, departments are in h3 with ordered lists.
    for h3 in soup.find_all("h3"):
        department = h3.get_text(strip=True)
        ol = h3.find_next("ol")
        if not ol:
            continue
        for li in ol.find_all("li"):
            name = li.get_text(strip=True)
            if not name:
                continue
            scheme_id = f"{source.id}_{slugify(name)}"
            results.append(
                {
                    "scheme_id": scheme_id,
                    "scheme_name": name,
                    "ministry": department,
                    "scheme_level": source.scheme_level,
                    "scheme_type": source.scheme_type,
                    "scheme_category": source.scheme_category,
                    "documents_required": "",
                    "application_url": "",
                    "benefit_description": "",
                    "min_age": "",
                    "max_age": "",
                    "income_limit": "",
                    "applicable_states": source.applicable_states or "Haryana",
                    "special_conditions_required": "",
                    "source_url": source.url,
                }
            )
    return results


def extract_dbtbharat_central(html: str, source: Source) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict[str, Any]] = []
    for heading in soup.select("div.pageSubHeading.borderBottom"):
        heading_text = " ".join(heading.get_text(" ", strip=True).split())
        ministry = heading_text.split(":")[0].strip() if ":" in heading_text else heading_text
        ol = heading.find_next("ol")
        if not ol:
            continue
        for li in ol.find_all("li"):
            a = li.find("a")
            name = " ".join(li.get_text(" ", strip=True).split())
            if not name:
                continue
            href = ""
            if a and a.get("href"):
                href = a["href"].strip()
            scheme_id = f"{source.id}_{slugify(name)}"
            results.append(
                {
                    "scheme_id": scheme_id,
                    "scheme_name": name,
                    "ministry": ministry,
                    "scheme_level": source.scheme_level,
                    "scheme_type": source.scheme_type,
                    "scheme_category": source.scheme_category,
                    "documents_required": "",
                    "application_url": _clean_application_url(href),
                    "benefit_description": "",
                    "min_age": "",
                    "max_age": "",
                    "income_limit": "",
                    "applicable_states": source.applicable_states,
                    "special_conditions_required": "",
                    "source_url": source.url,
                }
            )
    return results


def _is_good_scheme_text(text: str) -> bool:
    text = " ".join((text or "").split())
    if len(text) < 8 or len(text) > 220:
        return False
    lower = text.lower()
    bad_tokens = [
        "login",
        "register",
        "home",
        "contact us",
        "privacy policy",
        "terms",
        "accessibility",
        "skip to main",
        "javascript",
        "cookie",
        "help",
    ]
    if any(tok in lower for tok in bad_tokens):
        return False
    keywords = r"\b(scheme|yojana|mission|programme|program|subsidy|benefit|pension|assistance)\b"
    return re.search(keywords, text, flags=re.IGNORECASE) is not None


def _clean_application_url(url: str) -> str:
    """Ensure the URL is an application portal and not just a PDF guideline."""
    if not url:
        return ""
    lower_url = url.lower()
    # If it's a document or circular, it's not the online application link
    bad_exts = [".pdf", ".doc", ".docx", "guideline", "notification", "circular", "download"]
    if any(ext in lower_url for ext in bad_exts):
        return "" # Clear it out so we don't send people to a PDF to 'apply'
        
    return url


def extract_generic_page(html: str, source: Source) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def push(name: str, href: str = "", ministry: str = "") -> None:
        normalized = " ".join(name.split())
        key = normalized.lower()
        if not normalized or key in seen:
            return
        if not _is_good_scheme_text(normalized):
            return
        seen.add(key)
        scheme_id = f"{source.id}_{slugify(normalized)}"
        results.append(
            {
                "scheme_id": scheme_id,
                "scheme_name": normalized,
                "ministry": ministry,
                "scheme_level": source.scheme_level,
                "scheme_type": source.scheme_type,
                "scheme_category": source.scheme_category,
                "documents_required": "",
                "application_url": _clean_application_url(href),
                "benefit_description": "",
                "min_age": "",
                "max_age": "",
                "income_limit": "",
                "applicable_states": source.applicable_states,
                "special_conditions_required": "",
                "source_url": source.url,
            }
        )

    for li in soup.find_all("li"):
        text = " ".join(li.get_text(" ", strip=True).split())
        anchor = li.find("a", href=True)
        href = urljoin(source.url or "", anchor["href"]) if anchor else ""
        push(text, href=href)

    for tr in soup.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        text = " ".join(" ".join(c.get_text(" ", strip=True).split()) for c in cells)
        anchor = tr.find("a", href=True)
        href = urljoin(source.url or "", anchor["href"]) if anchor else ""
        push(text, href=href)

    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split())
        if text.lower().startswith("http"):
            continue
        href = urljoin(source.url or "", a["href"])
        push(text, href=href)

    return results


def extract_data_gov_in(source: Source, user_agent: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("DATAGOVINDIA_API_KEY")
    if not api_key or not source.resource_id:
        return []

    url = (
        "https://api.data.gov.in/resource/"
        f"{source.resource_id}?api-key={api_key}&format=json&limit=5000"
    )
    if not can_fetch(url, user_agent):
        return []
    text = fetch_url(url, user_agent)
    payload = json.loads(text)
    records = payload.get("records", [])

    results: List[Dict[str, Any]] = []
    for item in records:
        name = (
            item.get("scheme_name")
            or item.get("scheme")
            or item.get("name")
            or ""
        )
        if not name:
            continue
        scheme_id = f"{source.id}_{slugify(name)}"
        results.append(
            {
                "scheme_id": scheme_id,
                "scheme_name": name,
                "ministry": item.get("ministry") or item.get("department") or "",
                "scheme_level": source.scheme_level,
                "scheme_type": source.scheme_type,
                "scheme_category": source.scheme_category,
                "documents_required": item.get("documents_required") or "",
                "application_url": item.get("application_url") or "",
                "benefit_description": item.get("benefit_description") or "",
                "min_age": item.get("min_age") or "",
                "max_age": item.get("max_age") or "",
                "income_limit": item.get("income_limit") or "",
                "applicable_states": item.get("applicable_states") or "",
                "special_conditions_required": item.get("special_conditions_required") or "",
                "source_url": source.url or "https://data.gov.in",
            }
        )
    return results


def scrape_source(source: Source, user_agent: str) -> List[Dict[str, Any]]:
    if source.type == "dbt_haryana_list":
        if not source.url or not can_fetch(source.url, user_agent):
            return []
        html = fetch_url(source.url, user_agent)
        return extract_dbt_haryana(html, source)
    if source.type == "dbtbharat_central_list":
        if not source.url or not can_fetch(source.url, user_agent):
            return []
        html = fetch_url(source.url, user_agent)
        return extract_dbtbharat_central(html, source)
    if source.type == "generic_gov_page":
        if not source.url or not can_fetch(source.url, user_agent):
            return []
        html = fetch_url(source.url, user_agent)
        return extract_generic_page(html, source)
    if source.type == "data_gov_in_api":
        return extract_data_gov_in(source, user_agent)
    return []


def dedupe_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped = []
    for row in rows:
        key = (row.get("scheme_name", "").lower(), row.get("application_url", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def write_master(rows: List[Dict[str, Any]]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    for col in MASTER_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[MASTER_COLUMNS]
    df.to_csv(MASTER_PATH, index=False, encoding="utf-8")


def run():
    user_agent, rate_limit, sources = load_sources()
    all_rows: List[Dict[str, Any]] = []

    for source in sources:
        rows = scrape_source(source, user_agent)
        # Ensure scraped schemes have benefit_type="scheme"
        for r in rows:
            if "benefit_type" not in r:
                r["benefit_type"] = "scheme"
        all_rows.extend(rows)
        time.sleep(rate_limit)

    all_rows = dedupe_rows(all_rows)
    
    # Merge financial schemes so they are not overwritten
    try:
        from scrape_financials import FINANCIAL_SCHEMES
        all_rows.extend(FINANCIAL_SCHEMES)
    except Exception as e:
        print(f"Warning: Could not import financial schemes - {e}")

    write_master(all_rows)
    return len(all_rows)


if __name__ == "__main__":
    count = run()
    print(f"Saved {count} schemes to {MASTER_PATH}")
