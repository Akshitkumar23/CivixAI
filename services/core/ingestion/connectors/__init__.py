"""
Connectors Package for CivixAI Ingestion
Provides standardized discovery connectors for official portals.

Static connectors (seed-list based):
  - MySchemeConnector       - 7 high-priority myScheme seeds
  - StatePortalsConnector   - 10 pilot state scheme seeds

Dynamic crawlers (live discovery):
  - MySchemeDiscoveryCrawler  - sitemap + listing page discovery for myscheme.gov.in
  - DBTBharatDiscoveryCrawler - listing page + sitemap discovery for dbtbharat.gov.in
"""
from .base import BaseConnector
from .myscheme import MySchemeConnector
from .state_portals import StatePortalsConnector
from .myscheme_crawler import MySchemeDiscoveryCrawler
from .dbtbharat_crawler import DBTBharatDiscoveryCrawler

__all__ = [
    "BaseConnector",
    "MySchemeConnector",
    "StatePortalsConnector",
    "MySchemeDiscoveryCrawler",
    "DBTBharatDiscoveryCrawler",
]
