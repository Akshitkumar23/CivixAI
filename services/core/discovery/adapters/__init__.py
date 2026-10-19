"""
CIVIXAI — DISCOVERY SOURCE ADAPTERS
===================================
Exports all standardized government source adapters and provides factory function.
"""

from typing import Any, Dict, Optional
from services.core.discovery.adapters.base import GovernmentProgrammeSource
from services.core.discovery.adapters.myscheme_adapter import MySchemeAdapter
from services.core.discovery.adapters.apisetu_adapter import APISetuMySchemeAdapter
from services.core.discovery.adapters.indiagov_adapter import IndiaGovAdapter
from services.core.discovery.adapters.govservices_adapter import GovServicesAdapter
from services.core.discovery.adapters.dbtbharat_adapter import DBTBharatAdapter
from services.core.discovery.adapters.datagov_adapter import DataGovAdapter
from services.core.discovery.adapters.central_ministry_adapter import CentralMinistryAdapter
from services.core.discovery.adapters.state_portal_adapter import StatePortalAdapter

__all__ = [
    "GovernmentProgrammeSource",
    "MySchemeAdapter",
    "APISetuMySchemeAdapter",
    "IndiaGovAdapter",
    "GovServicesAdapter",
    "DBTBharatAdapter",
    "DataGovAdapter",
    "CentralMinistryAdapter",
    "StatePortalAdapter",
    "get_source_adapter",
]


def get_source_adapter(source_id: str, adapter_name: str, config: Optional[Dict[str, Any]] = None) -> GovernmentProgrammeSource:
    """
    Factory returning appropriate adapter instance according to registry configuration.
    """
    adapters = {
        "MySchemeAdapter": MySchemeAdapter,
        "APISetuMySchemeAdapter": APISetuMySchemeAdapter,
        "IndiaGovAdapter": IndiaGovAdapter,
        "GovServicesAdapter": GovServicesAdapter,
        "DBTBharatAdapter": DBTBharatAdapter,
        "DataGovAdapter": DataGovAdapter,
        "CentralMinistryAdapter": CentralMinistryAdapter,
        "StatePortalAdapter": StatePortalAdapter,
    }

    cls = adapters.get(adapter_name)
    if not cls:
        if "state" in source_id or "edistrict" in source_id:
            cls = StatePortalAdapter
        elif "min_" in source_id:
            cls = CentralMinistryAdapter
        else:
            cls = MySchemeAdapter

    return cls(source_id=source_id, config=config)
