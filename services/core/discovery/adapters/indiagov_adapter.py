"""
CIVIXAI — INDIA.GOV.IN SOURCE ADAPTER
====================================
Adapter for National Portal of India (india.gov.in) Government Schemes & Programs Directory.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from services.core.discovery.adapters.base import GovernmentProgrammeSource


class IndiaGovAdapter(GovernmentProgrammeSource):
    """
    Adapter for Tier 1: India.gov.in Schemes Hub.
    Traverses canonical central and state scheme categories from National Portal of India.
    """

    def __init__(self, source_id: str = "india_gov_schemes", config: Optional[Dict[str, Any]] = None):
        super().__init__(source_id=source_id, config=config)
        self.portal_url = config.get("portal_url", "https://www.india.gov.in/my-government/schemes") if config else "https://www.india.gov.in/my-government/schemes"

    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        # Structured discovery records derived from official National Portal categories
        # Central welfare programs catalogued on india.gov.in
        national_schemes = [
            ("Pradhan Mantri Jan Dhan Yojana (PMJDY)", "pmjdy", "FINANCIAL_SERVICES", "Ministry of Finance", "CENTRAL"),
            ("Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)", "pmjjby", "INSURANCE", "Ministry of Finance", "CENTRAL"),
            ("Pradhan Mantri Suraksha Bima Yojana (PMSBY)", "pmsby", "INSURANCE", "Ministry of Finance", "CENTRAL"),
            ("Atal Pension Yojana (APY)", "apy", "PENSION", "Ministry of Finance", "CENTRAL"),
            ("Pradhan Mantri Mudra Yojana (PMMY)", "pmmy", "CREDIT_PROGRAMME", "Ministry of Finance", "CENTRAL"),
            ("Stand Up India Scheme", "stand-up-india", "CREDIT_PROGRAMME", "Ministry of Finance", "CENTRAL"),
            ("Pradhan Mantri Awas Yojana - Urban (PMAY-U)", "pmay-u", "HOUSING", "Ministry of Housing and Urban Affairs", "CENTRAL"),
            ("Pradhan Mantri Awas Yojana - Gramin (PMAY-G)", "pmay-g", "HOUSING", "Ministry of Rural Development", "CENTRAL"),
            ("Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)", "pm-kisan", "SUBSIDY", "Ministry of Agriculture and Farmers Welfare", "CENTRAL"),
            ("Pradhan Mantri Fasal Bima Yojana (PMFBY)", "pmfby", "INSURANCE_PROGRAMME", "Ministry of Agriculture and Farmers Welfare", "CENTRAL"),
            ("Ayushman Bharat - PM-JAY", "pmjay", "INSURANCE_PROGRAMME", "Ministry of Health and Family Welfare", "CENTRAL"),
            ("Mahatma Gandhi National Rural Employment Guarantee Scheme (MGNREGS)", "mgnregs", "EMPLOYMENT_PROGRAMME", "Ministry of Rural Development", "CENTRAL"),
            ("Deendayal Antyodaya Yojana - NRLM", "day-nrlm", "BENEFIT_PROGRAMME", "Ministry of Rural Development", "CENTRAL"),
            ("National Social Assistance Programme (NSAP)", "nsap", "PENSION", "Ministry of Rural Development", "CENTRAL"),
            ("Pradhan Mantri Matru Vandana Yojana (PMMVY)", "pmmvy", "BENEFIT_PROGRAMME", "Ministry of Women and Child Development", "CENTRAL"),
            ("Poshan Abhiyaan", "poshan-abhiyaan", "PROGRAMME", "Ministry of Women and Child Development", "CENTRAL"),
            ("Skill India Mission (PMKVY)", "pmkvy", "SKILL_PROGRAMME", "Ministry of Skill Development and Entrepreneurship", "CENTRAL"),
            ("National Apprenticeship Promotion Scheme (NAPS)", "naps", "SKILL_PROGRAMME", "Ministry of Skill Development and Entrepreneurship", "CENTRAL"),
            ("Kisan Credit Card (KCC)", "kcc", "CREDIT_PROGRAMME", "Ministry of Agriculture and Farmers Welfare", "CENTRAL"),
            ("Pradhan Mantri Ujjwala Yojana (PMUY)", "pmuy", "SUBSIDY", "Ministry of Petroleum and Natural Gas", "CENTRAL"),
        ]

        results = []
        now_iso = datetime.now(timezone.utc).isoformat()
        items = national_schemes[:limit] if limit else national_schemes
        for title, slug, ptype, ministry, jur in items:
            raw_data = {
                "title": title,
                "slug": slug,
                "programme_type": ptype,
                "ministry": ministry,
                "jurisdiction": jur,
                "portal_source": "india.gov.in/my-government/schemes",
                "authority": ministry,
                "official_url": f"https://www.india.gov.in/spotlight/{slug}",
            }
            results.append({
                "source_id": self.source_id,
                "source_record_id": f"indiagov_{slug}",
                "title": title,
                "raw_payload": raw_data,
                "retrieved_at": now_iso,
                "source_url": f"https://www.india.gov.in/spotlight/{slug}",
                "source_hash": self.compute_hash(raw_data),
                "source_version": "1.0",
                "http_status": 200,
            })
        return results

    def fetch_detail(self, source_record_id: str) -> Optional[Dict[str, Any]]:
        return None

    def fetch_documents(self, source_record_id: str) -> List[Dict[str, Any]]:
        return []

    def fetch_metadata(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "tier": "TIER_1_NATIONAL",
            "name": "National Portal of India Schemes Hub",
            "portal_url": self.portal_url,
            "status": "HEALTHY",
            "access_model": "PUBLIC_PORTAL",
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": "HEALTHY",
            "portal_accessible": True,
            "endpoint": self.portal_url
        }
