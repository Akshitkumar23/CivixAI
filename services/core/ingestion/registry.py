"""
Source Registry Service
Manages official government sources, trust levels, and authority policies.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc

from services.core.database.models import SourceRegistry

TRUST_POLICIES: Dict[str, Dict[str, Any]] = {
    "A": {
        "title": "Gazette & Statutory Rules",
        "description": "The Gazette of India, State Gazettes, Parliamentary Acts, and Statutory Notifications.",
        "freshness_policy_days": 180,
        "is_authoritative": True,
        "can_reject_authoritatively": True,
        "precedence_rank": 1
    },
    "B": {
        "title": "Official Ministry Guidelines & Portals",
        "description": "Central/State Ministry operational guidelines, myScheme official entries, and designated scheme portals.",
        "freshness_policy_days": 30,
        "is_authoritative": True,
        "can_reject_authoritatively": True,
        "precedence_rank": 2
    },
    "C": {
        "title": "Government Press Releases",
        "description": "PIB releases, Ministry announcements, and government press briefings. Supporting evidence only.",
        "freshness_policy_days": 14,
        "is_authoritative": False,
        "can_reject_authoritatively": False,
        "precedence_rank": 3
    },
    "D": {
        "title": "Secondary / Explanatory Sources",
        "description": "Third-party portals, news articles, and secondary aggregators. Strictly non-authoritative.",
        "freshness_policy_days": 7,
        "is_authoritative": False,
        "can_reject_authoritatively": False,
        "precedence_rank": 4
    }
}

class SourceRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def list_sources(
        self,
        trust_level: Optional[str] = None,
        freshness_status: Optional[str] = None,
        limit: int = 100
    ) -> List[SourceRegistry]:
        query = self.db.query(SourceRegistry)
        if trust_level:
            query = query.filter(SourceRegistry.trust_level == trust_level)
        if freshness_status:
            query = query.filter(SourceRegistry.freshness_status == freshness_status)
        return query.order_by(desc(SourceRegistry.last_checked_at)).limit(limit).all()

    def get_source(self, source_id: str) -> Optional[SourceRegistry]:
        return self.db.query(SourceRegistry).filter(SourceRegistry.id == source_id).first()

    def get_by_url(self, canonical_url: str) -> Optional[SourceRegistry]:
        return self.db.query(SourceRegistry).filter(SourceRegistry.canonical_url == canonical_url).first()

    def register_source(
        self,
        canonical_url: str,
        publisher: str,
        title: str,
        trust_level: str = "B",
        source_type: str = "official_guideline",
        jurisdiction: str = "Central",
        authority_id: Optional[str] = None,
        content_type: str = "text/html",
        freshness_policy_days: Optional[int] = None
    ) -> SourceRegistry:
        existing = self.get_by_url(canonical_url)
        if existing:
            return existing

        policy = TRUST_POLICIES.get(trust_level, TRUST_POLICIES["B"])
        days = freshness_policy_days or policy["freshness_policy_days"]

        source = SourceRegistry(
            id=f"src-{uuid.uuid4().hex[:12]}",
            canonical_url=canonical_url,
            final_url=canonical_url,
            publisher=publisher,
            authority_id=authority_id,
            jurisdiction=jurisdiction,
            source_type=source_type,
            trust_level=trust_level,
            title=title,
            content_type=content_type,
            freshness_policy_days=days,
            freshness_status="fresh",
            verification_status="imported_unverified"
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    @staticmethod
    def get_policy(trust_level: str) -> Dict[str, Any]:
        return TRUST_POLICIES.get(trust_level, TRUST_POLICIES["D"])
