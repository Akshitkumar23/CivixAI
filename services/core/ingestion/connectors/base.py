"""
Base Connector Interface for CivixAI Ingestion
Defines standard abstract interface for discovering, fetching metadata,
and staging discovery candidates.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

class BaseConnector(ABC):
    """
    Abstract base class for all scheme discovery connectors.
    Connectors discover external scheme metadata, fetch source snapshots,
    and produce candidate records. They NEVER directly insert certified rules.
    """

    def __init__(self, connector_id: str, authority_tier: str = "tier3_myscheme"):
        self.connector_id = connector_id
        self.authority_tier = authority_tier

    @abstractmethod
    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Executes discovery on the target portal.
        Returns a list of discovered candidate dictionaries.
        """
        pass

    @abstractmethod
    def fetch_source(self, candidate: Dict[str, Any]) -> Tuple[int, bytes, str]:
        """
        Fetches the primary source document for a candidate.
        Returns (http_status, content_bytes, content_type).
        """
        pass
