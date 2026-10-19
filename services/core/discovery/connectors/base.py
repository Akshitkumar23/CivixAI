"""
Base Discovery Connector Interface
==================================
Defines standard abstract interface for all multi-source program discovery adapters.
Every connector outputs ProgramCandidate staging records and never mutates production DB.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any

from services.core.discovery.models import ProgramCandidate


class BaseDiscoveryConnector(ABC):
    """
    Abstract base class for all program discovery connectors.
    Connectors discover external scheme/product metadata, fetch raw source snapshots,
    and stage ProgramCandidate instances.
    """

    def __init__(self, source_id: str, authority_tier: str):
        self.source_id = source_id
        self.authority_tier = authority_tier

    @abstractmethod
    def discover(self, limit: Optional[int] = None) -> List[ProgramCandidate]:
        """
        Executes discovery on the target portal / endpoint.
        Returns a list of ProgramCandidate instances.
        """
        pass

    @abstractmethod
    def fetch_source(self, candidate: ProgramCandidate) -> Tuple[int, bytes, str]:
        """
        Fetches the primary source document for a candidate.
        Returns (http_status, content_bytes, content_type).
        """
        pass
