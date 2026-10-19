"""
CIVIXAI — GOVERNMENT PROGRAMME SOURCE ADAPTER INTERFACE
======================================================
Formal abstract interface for all discovery source adapters.
Ensures standardized lifecycle, security, health, identity, and document extraction.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import hashlib


class GovernmentProgrammeSource(ABC):
    """
    Standard interface for all tier-specific government discovery adapters.
    All methods must respect security policies, rate limits, and non-blocking failure semantics.
    """

    def __init__(self, source_id: str, config: Optional[Dict[str, Any]] = None):
        self.source_id = source_id
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.rate_limit_per_minute = self.config.get("rate_limit_per_minute", 60)
        self.portal_url = self.config.get("portal_url", "")
        self.api_endpoint = self.config.get("api_endpoint")
        self.authority = self.config.get("authority", "Government of India")
        self.jurisdiction = self.config.get("jurisdiction", "CENTRAL")
        self.state_or_ut = self.config.get("state_or_ut")

    @abstractmethod
    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discovers raw candidate records from the source.
        Returns list of raw discovery dictionaries.
        """
        pass

    @abstractmethod
    def fetch_detail(self, source_record_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches full canonical detail for a specific programme entity.
        """
        pass

    @abstractmethod
    def fetch_documents(self, source_record_id: str) -> List[Dict[str, Any]]:
        """
        Fetches official guidelines, gazette notifications, or scheme forms.
        """
        pass

    @abstractmethod
    def fetch_metadata(self) -> Dict[str, Any]:
        """
        Returns source metadata, tier, capabilities, and update frequency.
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Checks connectivity, latency, status code, and endpoint validity.
        """
        pass

    def get_identity(self) -> str:
        """
        Returns deterministic source identifier.
        """
        return self.source_id

    def get_currentness(self, source_record_id: str) -> str:
        """
        Determines currentness status (ACTIVE, INACTIVE, WITHDRAWN, SUPERSEDED, SUBSUMED, UNKNOWN).
        Default is ACTIVE unless source explicitly states otherwise.
        """
        return "ACTIVE"

    @staticmethod
    def compute_hash(payload: Any) -> str:
        """
        Computes SHA-256 hash of record payload for change detection.
        """
        import json
        if isinstance(payload, str):
            raw = payload.encode("utf-8")
        else:
            raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
