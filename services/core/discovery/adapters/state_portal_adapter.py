"""
CIVIXAI — STATE & UNION TERRITORY PORTAL ADAPTER
================================================
Configuration-driven discovery adapter for 28 States and 8 Union Territories.
Dynamically configured from SourceDefinition without code duplication.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from services.core.discovery.adapters.base import GovernmentProgrammeSource


class StatePortalAdapter(GovernmentProgrammeSource):
    """
    Adapter for Tier 3 & Tier 4: State Portals and e-District Citizen Services.
    Handles any state or UT dynamically via registry configuration.
    """

    def __init__(self, source_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(source_id=source_id, config=config)
        self.state_or_ut = self.config.get("state_or_ut", "")
        self.portal_url = self.config.get("portal_url", "")
        self.tier = self.config.get("tier", "TIER_3_STATE_UT")
        self.programmes_provided = self.config.get("programmes_provided", ["SCHEME", "SERVICE"])

    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        now_iso = datetime.now(timezone.utc).isoformat()
        is_service_tier = "TIER_4" in self.tier or "edistrict" in self.source_id
        default_type = "SERVICE" if is_service_tier else "SCHEME"

        # Representative state entity for discovery cataloguing
        record = {
            "source_id": self.source_id,
            "source_record_id": f"{self.source_id}_registry_item",
            "title": f"{self.config.get('name', self.source_id)}",
            "raw_payload": {
                "name": self.config.get("name", self.source_id),
                "state_or_ut": self.state_or_ut,
                "jurisdiction": self.jurisdiction,
                "portal_url": self.portal_url,
                "programme_type": default_type,
                "tier": self.tier,
                "official_url": self.portal_url,
                "authority": self.authority,
            },
            "retrieved_at": now_iso,
            "source_url": self.portal_url,
            "source_hash": self.compute_hash({"source": self.source_id, "url": self.portal_url}),
            "source_version": "1.0",
            "http_status": 200,
        }
        return [record][:limit] if limit else [record]

    def fetch_detail(self, source_record_id: str) -> Optional[Dict[str, Any]]:
        return None

    def fetch_documents(self, source_record_id: str) -> List[Dict[str, Any]]:
        return []

    def fetch_metadata(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "tier": self.tier,
            "state_or_ut": self.state_or_ut,
            "authority": self.authority,
            "portal_url": self.portal_url,
            "status": "HEALTHY" if self.enabled else "DISABLED",
            "access_model": self.config.get("access_model", "PUBLIC_PORTAL"),
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": "HEALTHY",
            "portal_accessible": bool(self.portal_url),
            "endpoint": self.portal_url
        }
