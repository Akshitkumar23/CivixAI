"""
Discovery Connectors Package
============================
Connectors and adapters for government and regulated private program discovery.
"""

from services.core.discovery.connectors.base import BaseDiscoveryConnector
from services.core.discovery.connectors.myscheme_adapter import MySchemeDiscoveryAdapter
from services.core.discovery.connectors.dbtbharat_adapter import DBTBharatDiscoveryAdapter
from services.core.discovery.connectors.state_portal_adapter import StatePortalsDiscoveryAdapter
from services.core.discovery.connectors.private_banking_adapter import RegulatedBankingDiscoveryAdapter
from services.core.discovery.connectors.private_insurance_adapter import RegulatedInsuranceDiscoveryAdapter
from services.core.discovery.connectors.data_gov_adapter import DataGovInDiscoveryAdapter
from services.core.discovery.connectors.jansamarth_adapter import JanSamarthDiscoveryAdapter

__all__ = [
    "BaseDiscoveryConnector",
    "MySchemeDiscoveryAdapter",
    "DBTBharatDiscoveryAdapter",
    "StatePortalsDiscoveryAdapter",
    "RegulatedBankingDiscoveryAdapter",
    "RegulatedInsuranceDiscoveryAdapter",
    "DataGovInDiscoveryAdapter",
    "JanSamarthDiscoveryAdapter",
]
