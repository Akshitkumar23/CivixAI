"""
Source Discovery Engine
Discovers authoritative official sources for schemes lacking a verified source document.
Prioritizes Gazette notifications, Ministry scheme portals, and Departmental guidelines.
Never auto-verifies discovered sources.
"""
import uuid
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from services.core.database.models import Scheme, SchemeVersion, SourceRegistry

KNOWN_OFFICIAL_PORTALS: Dict[str, Dict[str, Any]] = {
    "pm-kisan": {
        "url": "https://pmkisan.gov.in/",
        "publisher": "Ministry of Agriculture and Farmers Welfare",
        "title": "PM Kisan Samman Nidhi Portal",
        "authority_type": "portal_spec",
        "trust_level": "B",
        "legal_priority": 4
    },
    "pmay-g": {
        "url": "https://pmayg.nic.in/",
        "publisher": "Ministry of Rural Development",
        "title": "Pradhan Mantri Awaas Yojana - Gramin Official Portal",
        "authority_type": "portal_spec",
        "trust_level": "B",
        "legal_priority": 4
    },
    "pmay-u": {
        "url": "https://pmay-urban.gov.in/",
        "publisher": "Ministry of Housing and Urban Affairs",
        "title": "Pradhan Mantri Awas Yojana - Urban Official Portal",
        "authority_type": "portal_spec",
        "trust_level": "B",
        "legal_priority": 4
    },
    "pmjay": {
        "url": "https://nha.gov.in/PM-JAY",
        "publisher": "National Health Authority",
        "title": "Ayushman Bharat PM-JAY Official Portal",
        "authority_type": "portal_spec",
        "trust_level": "B",
        "legal_priority": 4
    },
    "pm-matsya": {
        "url": "https://pmmsy.dof.gov.in/",
        "publisher": "Department of Fisheries",
        "title": "Pradhan Mantri Matsya Sampada Yojana",
        "authority_type": "portal_spec",
        "trust_level": "B",
        "legal_priority": 4
    },
    "national-pension": {
        "url": "https://enps.nsdl.com/",
        "publisher": "PFRDA",
        "title": "National Pension System Official Portal",
        "authority_type": "portal_spec",
        "trust_level": "B",
        "legal_priority": 4
    },
    "indira-gandhi-widow-pension": {
        "url": "https://nsap.nic.in/",
        "publisher": "Ministry of Rural Development",
        "title": "National Social Assistance Programme",
        "authority_type": "portal_spec",
        "trust_level": "B",
        "legal_priority": 4
    }
}

class SourceDiscoveryEngine:
    def __init__(self, db: Session):
        self.db = db

    def discover_sources_for_all_schemes(self) -> Dict[str, Any]:
        """
        Audits all schemes and creates candidate SourceRegistry records for schemes
        that lack an official specific source, without auto-verifying them.
        """
        schemes = self.db.query(Scheme).all()
        seen_urls = {r[0] for r in self.db.query(SourceRegistry.canonical_url).all() if r[0]}
        created_count = 0
        existing_count = 0
        skipped_count = 0

        for scheme in schemes:
            latest_version = self.db.query(SchemeVersion).filter(
                SchemeVersion.scheme_id == scheme.id
            ).order_by(SchemeVersion.version_number.desc()).first()

            if not latest_version:
                continue

            current_source_url = latest_version.source_url or ""
            current_app_url = latest_version.application_url or ""

            # Check if scheme already has a registered specific source (ignore generic central-scheme/list)
            is_generic = "central-scheme/list" in current_source_url
            existing_source = None
            if not is_generic and current_source_url:
                existing_source = self.db.query(SourceRegistry).filter(
                    SourceRegistry.canonical_url == current_source_url
                ).first()
            if not existing_source:
                existing_source = self.db.query(SourceRegistry).filter(
                    SourceRegistry.title.like(f"%{scheme.canonical_name}%")
                ).first()

            if existing_source:
                existing_count += 1
                continue

            target_url = None
            publisher = "Government of India" if scheme.scheme_level == "Central" else "State Government"
            title = f"Official Source for {scheme.canonical_name}"
            auth_type = "portal_spec"
            trust = "B"
            priority = 4

            # Check known curated portals
            for k, meta in KNOWN_OFFICIAL_PORTALS.items():
                if k in scheme.id or k in scheme.canonical_name.lower():
                    target_url = meta["url"]
                    publisher = meta["publisher"]
                    title = meta["title"]
                    auth_type = meta["authority_type"]
                    trust = meta["trust_level"]
                    priority = meta["legal_priority"]
                    break

            # Fallback to scheme-specific application_url if it is an official portal
            if not target_url and current_app_url and ("gov.in" in current_app_url or "nic.in" in current_app_url):
                target_url = current_app_url
                title = f"Application Portal for {scheme.canonical_name}"

            # Fallback to current_source_url if not generic
            if not target_url and current_source_url and "central-scheme/list" not in current_source_url:
                target_url = current_source_url

            if not target_url:
                # No specific authoritative source discovered yet; remains pending discovery
                skipped_count += 1
                continue

            # Ensure URL isn't already registered
            if target_url in seen_urls:
                existing_count += 1
                continue
            seen_urls.add(target_url)

            new_source = SourceRegistry(
                id=f"src-disc-{uuid.uuid4().hex[:10]}",
                scheme_id=scheme.id,
                canonical_url=target_url,
                final_url=target_url,
                publisher=publisher,
                authority_id=scheme.authority_id,
                jurisdiction=scheme.scheme_level,
                source_type="scheme_portal",
                source_authority_type=auth_type,
                trust_level=trust,
                legal_priority=priority,
                title=title,
                content_type="application/pdf" if target_url.endswith(".pdf") else "text/html",
                freshness_policy_days=30 if trust == "B" else 14,
                freshness_status="fresh",
                verification_status="imported_unverified",  # STRICTLY UNVERIFIED
                parser_health="not_run",
                last_fetch_status="not_attempted"
            )
            self.db.add(new_source)
            created_count += 1

        self.db.commit()
        return {
            "total_schemes": len(schemes),
            "sources_created": created_count,
            "existing_sources": existing_count,
            "pending_discovery": skipped_count
        }
