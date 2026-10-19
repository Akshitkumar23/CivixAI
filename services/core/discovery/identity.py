"""
Identity & Layered Deduplication Engine
=======================================
Provides deterministic identity resolution, evidence-based matching, and collision
handling across multi-source program candidates.
Enforces:
1. Official Program ID / Code priority
2. Rural vs Urban separation (PMAY-G != PMAY-U)
3. Government vs Private separation (Government Loan != Private Bank Loan)
4. Cross-source resolution (myScheme PM-KISAN == DBT PM-KISAN == Ministry PM-KISAN)
5. Zero silent merges for ambiguous matches (possible_duplicate_of review flag)
"""

import re
import hashlib
from typing import Dict, List, Optional, Tuple, Set, Any
from urllib.parse import urlparse

from services.core.discovery.models import (
    ProgramCandidate,
    ProviderType,
)


def canonicalize_url(url: str) -> str:
    """
    Normalizes a URL by lowercasing hostname, removing tracking parameters,
    and stripping trailing slashes.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"
        query = parsed.query
        if query:
            params = [
                p for p in query.split("&")
                if not any(p.lower().startswith(trk) for trk in ("utm_", "fbclid=", "gclid=", "ref="))
            ]
            query_str = f"?{'&'.join(params)}" if params else ""
        else:
            query_str = ""
        return f"{scheme}://{netloc}{path}{query_str}"
    except Exception:
        return url.strip().lower()


def extract_official_code(text: str, url: str) -> Optional[str]:
    """
    Extracts high-confidence official program codes (e.g. pm-kisan, pmay-g, pmay-u, apy, pmsby, pmjjby).
    Preserves rural vs urban and variant qualifiers.
    """
    combined = (text + " " + url).lower()
    
    # Specific known scheme codes with variants
    if "pmay-g" in combined or "pmayg" in combined or ("awaas" in combined and "gramin" in combined) or ("awas" in combined and "gramin" in combined):
        return "pmay-g"
    if "pmay-u" in combined or "pmayu" in combined or ("awaas" in combined and "urban" in combined) or ("awas" in combined and "urban" in combined):
        return "pmay-u"
    if "pm-kisan" in combined or "pmkisan" in combined or "kisan samman nidhi" in combined:
        return "pm-kisan"
    if "pm-jay" in combined or "pmjay" in combined or "ayushman bharat" in combined:
        return "pm-jay"
    if "pm-jjby" in combined or "pmjjby" in combined or "jeevan jyoti" in combined:
        return "pm-jjby"
    if "pm-sby" in combined or "pmsby" in combined or "suraksha bima" in combined:
        return "pm-sby"
    if "apy" in combined or "atal pension" in combined:
        return "atal-pension-yojana"
    if "mgnrega" in combined or "nrega" in combined:
        return "mgnrega"

    # Match slug from URL if it looks like an official code
    parsed = urlparse(url)
    slug = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
    if slug and len(slug) >= 3 and len(slug) <= 32 and re.match(r"^[a-z0-9_\-]+$", slug):
        # Exclude generic directory words
        if slug not in {"schemes", "loans", "services", "list", "index", "pension", "all"}:
            return slug

    return None


def normalize_program_title(title: str) -> str:
    """
    Normalizes an official program or scheme title:
    - Lowercases
    - Normalizes common variants (e.g., 'PM' -> 'pradhan mantri')
    - Preserves specific qualifier tokens ('gramin', 'urban', 'g', 'u')
    - Strips non-alphanumeric punctuation
    - Collapses whitespace
    """
    if not title:
        return ""
    t = title.lower()
    t = re.sub(r"\b(pm)\b", "pradhan mantri", t)
    t = re.sub(r"\b(yojna)\b", "yojana", t)
    t = re.sub(r"\b(sch)\b", "scheme", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def generate_candidate_id(source_id: str, unique_key: str) -> str:
    """
    Generates a deterministic candidate ID.
    """
    raw = f"{source_id}:{unique_key}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"cand-{source_id[:10]}-{h}"


def generate_identity_key(
    provider_type: str,
    identity_discriminator: str,
) -> str:
    """
    Generates a deterministic SHA-256 identity key based on provider category and official discriminator.
    """
    raw = f"{provider_type}|{identity_discriminator}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ProgramIdentityEngine:
    """
    Deterministic, layered identity resolution and deduplication engine.
    Ensures:
    - Cross-source match: myScheme PM-KISAN == DBT PM-KISAN == Ministry PM-KISAN
    - Distinct variant: PMAY-G != PMAY-U
    - Distinct provider: Government Loan != Private Bank Loan
    - Zero silent merges
    """

    def __init__(self):
        # identity_key -> primary ProgramCandidate
        self._identity_index: Dict[str, ProgramCandidate] = {}
        # canonical_url -> identity_key
        self._url_index: Dict[str, str] = {}
        # normalized_title -> List[identity_key]
        self._title_index: Dict[str, List[str]] = {}

    def resolve_candidate_identity(self, candidate: ProgramCandidate) -> Tuple[str, List[str]]:
        """
        Determines the deterministic identity key using layered priority:
        1. Official Program Code (if verified)
        2. Canonical provider category + normalized name + qualifier
        """
        canon_url = canonicalize_url(candidate.source_url)
        norm_title = normalize_program_title(candidate.official_name)
        official_code = extract_official_code(candidate.official_name, canon_url)

        if official_code:
            # High-confidence official code match (e.g. pm-kisan, pmay-g, pmay-u)
            discriminator = f"code:{official_code}"
        else:
            # Fallback to normalized title
            discriminator = f"title:{norm_title}"

        ident_key = generate_identity_key(candidate.provider_type, discriminator)
        possible_dups: List[str] = []

        # Check URL collision
        if canon_url in self._url_index:
            existing_key = self._url_index[canon_url]
            if existing_key != ident_key:
                existing_cand = self._identity_index.get(existing_key)
                if existing_cand:
                    possible_dups.append(existing_cand.candidate_id)

        # Check Title collision across differing keys
        if norm_title in self._title_index:
            for existing_key in self._title_index[norm_title]:
                if existing_key == ident_key:
                    continue
                existing_cand = self._identity_index.get(existing_key)
                if existing_cand:
                    possible_dups.append(existing_cand.candidate_id)

        return ident_key, possible_dups

    def process_and_deduplicate(
        self, candidates: List[ProgramCandidate]
    ) -> List[ProgramCandidate]:
        """
        Processes and deduplicates candidate programs:
        - Resolves layered identity keys
        - Merges provenances when identity matches identically
        - Preserves ambiguous candidates as separate records with possible_duplicate_of populated
        """
        processed_candidates: List[ProgramCandidate] = []
        seen_in_batch: Set[str] = set()

        for cand in candidates:
            canon_url = canonicalize_url(cand.source_url)
            norm_title = normalize_program_title(cand.official_name)

            ident_key, possible_dups = self.resolve_candidate_identity(cand)
            cand.identity_key = ident_key
            if possible_dups:
                cand.possible_duplicate_of = list(set(cand.possible_duplicate_of + possible_dups))

            # Exact match check
            if ident_key in self._identity_index:
                existing = self._identity_index[ident_key]
                existing.currentness_status = cand.currentness_status
                
                # Merge provenance into existing record
                sources = existing.raw_metadata.setdefault("source_references", [])
                new_ref = {
                    "source_id": cand.source_id,
                    "source_url": cand.source_url,
                    "discovery_method": cand.discovery_method,
                    "content_hash": cand.content_hash,
                    "authority_tier": cand.authority_tier,
                    "retrieved_at": cand.discovery_timestamp,
                }
                if new_ref not in sources:
                    sources.append(new_ref)

                if ident_key not in seen_in_batch:
                    seen_in_batch.add(ident_key)
                    processed_candidates.append(existing)
                continue

            seen_in_batch.add(ident_key)
            self._identity_index[ident_key] = cand
            if canon_url:
                self._url_index[canon_url] = ident_key
            if norm_title:
                self._title_index.setdefault(norm_title, []).append(ident_key)

            # Record initial source reference
            cand.raw_metadata.setdefault("source_references", [{
                "source_id": cand.source_id,
                "source_url": cand.source_url,
                "discovery_method": cand.discovery_method,
                "content_hash": cand.content_hash,
                "authority_tier": cand.authority_tier,
                "retrieved_at": cand.discovery_timestamp,
            }])

            processed_candidates.append(cand)

        return processed_candidates
