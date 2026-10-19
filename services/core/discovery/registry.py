"""
CIVIXAI — GOVERNMENT PROGRAMME SOURCE REGISTRY MANAGER
======================================================
Manages configurable source definitions across all 6 tiers:
Tier 1: National Portals (myScheme, API Setu, India.gov, GovServices, DBT Bharat, Data.gov)
Tier 2: Central Ministries & Departments
Tier 3: 28 States and 8 Union Territories
Tier 4: Government Services & e-District Portals
Tier 5: Official Datasets (Data.gov.in)
Tier 6: Official Document & Gazette Repositories

Strictly configuration-driven: NO hardcoded URLs inside crawler logic.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REGISTRY_FILE = PROJECT_ROOT / "data" / "source_registry" / "government_programme_sources.json"


class SourceDefinition(BaseModel):
    source_id: str
    name: str
    tier: str
    authority: str
    jurisdiction: str  # CENTRAL, STATE, UT
    state_or_ut: Optional[str] = None
    portal_url: str
    api_endpoint: Optional[str] = None
    adapter: str
    enabled: bool = True
    rate_limit_per_minute: int = 60
    access_model: str = "PUBLIC_PORTAL"  # PUBLIC_PORTAL, OFFICIAL_API, DATASET_DOWNLOAD, GOV_FEED
    programmes_provided: List[str] = Field(default_factory=lambda: ["SCHEME"])
    notes: Optional[str] = None


ALL_INDIAN_STATES = [
    {"name": "Andhra Pradesh", "code": "AP", "domain": "ap.gov.in", "portal": "https://www.ap.gov.in"},
    {"name": "Arunachal Pradesh", "code": "AR", "domain": "arunachalpradesh.gov.in", "portal": "https://arunachalpradesh.gov.in"},
    {"name": "Assam", "code": "AS", "domain": "assam.gov.in", "portal": "https://assam.gov.in"},
    {"name": "Bihar", "code": "BR", "domain": "state.bihar.gov.in", "portal": "https://state.bihar.gov.in"},
    {"name": "Chhattisgarh", "code": "CG", "domain": "cgstate.gov.in", "portal": "https://cgstate.gov.in"},
    {"name": "Goa", "code": "GA", "domain": "goa.gov.in", "portal": "https://www.goa.gov.in"},
    {"name": "Gujarat", "code": "GJ", "domain": "gujaratindia.gov.in", "portal": "https://gujaratindia.gov.in"},
    {"name": "Haryana", "code": "HR", "domain": "haryana.gov.in", "portal": "https://haryana.gov.in"},
    {"name": "Himachal Pradesh", "code": "HP", "domain": "himachal.nic.in", "portal": "https://himachal.nic.in"},
    {"name": "Jharkhand", "code": "JH", "domain": "jharkhand.gov.in", "portal": "https://www.jharkhand.gov.in"},
    {"name": "Karnataka", "code": "KA", "domain": "karnataka.gov.in", "portal": "https://karnataka.gov.in"},
    {"name": "Kerala", "code": "KL", "domain": "kerala.gov.in", "portal": "https://kerala.gov.in"},
    {"name": "Madhya Pradesh", "code": "MP", "domain": "mp.gov.in", "portal": "https://mp.gov.in"},
    {"name": "Maharashtra", "code": "MH", "domain": "maharashtra.gov.in", "portal": "https://www.maharashtra.gov.in"},
    {"name": "Manipur", "code": "MN", "domain": "manipur.gov.in", "portal": "https://manipur.gov.in"},
    {"name": "Meghalaya", "code": "ML", "domain": "meghalaya.gov.in", "portal": "https://meghalaya.gov.in"},
    {"name": "Mizoram", "code": "MZ", "domain": "mizoram.gov.in", "portal": "https://mizoram.gov.in"},
    {"name": "Nagaland", "code": "NL", "domain": "nagaland.gov.in", "portal": "https://nagaland.gov.in"},
    {"name": "Odisha", "code": "OD", "domain": "odisha.gov.in", "portal": "https://odisha.gov.in"},
    {"name": "Punjab", "code": "PB", "domain": "punjab.gov.in", "portal": "https://punjab.gov.in"},
    {"name": "Rajasthan", "code": "RJ", "domain": "rajasthan.gov.in", "portal": "https://rajasthan.gov.in"},
    {"name": "Sikkim", "code": "SK", "domain": "sikkim.gov.in", "portal": "https://sikkim.gov.in"},
    {"name": "Tamil Nadu", "code": "TN", "domain": "tn.gov.in", "portal": "https://www.tn.gov.in"},
    {"name": "Telangana", "code": "TG", "domain": "telangana.gov.in", "portal": "https://telangana.gov.in"},
    {"name": "Tripura", "code": "TR", "domain": "tripura.gov.in", "portal": "https://tripura.gov.in"},
    {"name": "Uttar Pradesh", "code": "UP", "domain": "up.gov.in", "portal": "https://up.gov.in"},
    {"name": "Uttarakhand", "code": "UK", "domain": "uk.gov.in", "portal": "https://uk.gov.in"},
    {"name": "West Bengal", "code": "WB", "domain": "wb.gov.in", "portal": "https://wb.gov.in"},
]

ALL_INDIAN_UTS = [
    {"name": "Andaman and Nicobar Islands", "code": "AN", "domain": "andaman.gov.in", "portal": "https://www.andaman.gov.in"},
    {"name": "Chandigarh", "code": "CH", "domain": "chandigarh.gov.in", "portal": "https://chandigarh.gov.in"},
    {"name": "Dadra and Nagar Haveli and Daman and Diu", "code": "DD", "domain": "ddd.gov.in", "portal": "https://ddd.gov.in"},
    {"name": "Delhi", "code": "DL", "domain": "delhi.gov.in", "portal": "https://delhi.gov.in"},
    {"name": "Jammu and Kashmir", "code": "JK", "domain": "jk.gov.in", "portal": "https://jk.gov.in"},
    {"name": "Ladakh", "code": "LA", "domain": "ladakh.gov.in", "portal": "https://ladakh.gov.in"},
    {"name": "Lakshadweep", "code": "LD", "domain": "lakshadweep.gov.in", "portal": "https://lakshadweep.gov.in"},
    {"name": "Puducherry", "code": "PY", "domain": "py.gov.in", "portal": "https://py.gov.in"},
]


class GovernmentProgrammeSourceRegistry:
    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or REGISTRY_FILE
        self._sources: Dict[str, SourceDefinition] = {}
        self.load_or_create()

    def load_or_create(self) -> None:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("sources", []):
                        src = SourceDefinition(**item)
                        self._sources[src.source_id] = src
                return
            except Exception:
                pass
        
        # Build initial comprehensive configuration
        self._sources = self._generate_comprehensive_registry()
        self.save()

    def get_source(self, source_id: str) -> Optional[SourceDefinition]:
        return self._sources.get(source_id)

    def list_sources(self, tier: Optional[str] = None, enabled_only: bool = False) -> List[SourceDefinition]:
        res = list(self._sources.values())
        if tier:
            res = [s for s in res if s.tier == tier]
        if enabled_only:
            res = [s for s in res if s.enabled]
        return res

    def save(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0",
            "description": "CivixAI Configurable Government Programme Source Registry",
            "total_sources": len(self._sources),
            "sources": [s.model_dump() for s in self._sources.values()]
        }
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def _generate_comprehensive_registry(self) -> Dict[str, SourceDefinition]:
        sources: Dict[str, SourceDefinition] = {}

        # ── TIER 1: NATIONAL DISCOVERY ─────────────────────────────────────────
        sources["myscheme_portal"] = SourceDefinition(
            source_id="myscheme_portal",
            name="myScheme National Portal",
            tier="TIER_1_NATIONAL",
            authority="National e-Governance Division (NeGD) / MeitY",
            jurisdiction="CENTRAL",
            portal_url="https://www.myscheme.gov.in",
            api_endpoint="https://api.myscheme.gov.in/public",
            adapter="MySchemeAdapter",
            enabled=True,
            access_model="PUBLIC_PORTAL",
            programmes_provided=["SCHEME", "SCHOLARSHIP", "PENSION", "SUBSIDY", "GRANT"],
            notes="Primary government citizen entitlement discovery portal."
        )

        sources["apisetu_myscheme"] = SourceDefinition(
            source_id="apisetu_myscheme",
            name="API Setu myScheme API Collection",
            tier="TIER_1_NATIONAL",
            authority="National Informatics Centre (NIC) / API Setu",
            jurisdiction="CENTRAL",
            portal_url="https://apisetu.gov.in",
            api_endpoint="https://api.apisetu.gov.in/myscheme/v1",
            adapter="APISetuMySchemeAdapter",
            enabled=False,  # Strictly false until legitimate credentials provided
            access_model="OFFICIAL_API",
            programmes_provided=["SCHEME", "SCHOLARSHIP", "PENSION", "SUBSIDY"],
            notes="MYSCHEME_API_ENABLED=false. Configured for legitimate authenticated use when granted."
        )

        sources["india_gov_schemes"] = SourceDefinition(
            source_id="india_gov_schemes",
            name="National Portal of India — Schemes Hub",
            tier="TIER_1_NATIONAL",
            authority="National Informatics Centre (NIC)",
            jurisdiction="CENTRAL",
            portal_url="https://www.india.gov.in/my-government/schemes",
            adapter="IndiaGovAdapter",
            enabled=True,
            access_model="PUBLIC_PORTAL",
            programmes_provided=["SCHEME", "PROGRAMME", "SERVICE"],
            notes="Comprehensive catalogue of central and state citizen programmes."
        )

        sources["gov_services_portal"] = SourceDefinition(
            source_id="gov_services_portal",
            name="National Government Services Portal",
            tier="TIER_4_GOV_SERVICES",
            authority="National Informatics Centre (NIC)",
            jurisdiction="CENTRAL",
            portal_url="https://services.india.gov.in",
            adapter="GovServicesAdapter",
            enabled=True,
            access_model="PUBLIC_PORTAL",
            programmes_provided=["SERVICE", "CERTIFICATE_SERVICE", "APPLICATION_SERVICE", "REGISTRATION_SERVICE"],
            notes="Statutory citizen delivery services (certificates, licences, registrations)."
        )

        sources["dbt_bharat"] = SourceDefinition(
            source_id="dbt_bharat",
            name="Direct Benefit Transfer (DBT) Bharat",
            tier="TIER_1_NATIONAL",
            authority="Cabinet Secretariat / DBT Mission",
            jurisdiction="CENTRAL",
            portal_url="https://dbtbharat.gov.in",
            adapter="DBTBharatAdapter",
            enabled=True,
            access_model="PUBLIC_PORTAL",
            programmes_provided=["SCHEME", "BENEFIT_PROGRAMME", "SCHOLARSHIP", "SUBSIDY"],
            notes="Authoritative registry of direct financial and in-kind transfer schemes."
        )

        sources["data_gov_in"] = SourceDefinition(
            source_id="data_gov_in",
            name="Open Government Data Platform India (data.gov.in)",
            tier="TIER_5_DATASETS",
            authority="NIC / Ministry of Electronics & IT",
            jurisdiction="CENTRAL",
            portal_url="https://data.gov.in",
            api_endpoint="https://api.data.gov.in/resource",
            adapter="DataGovAdapter",
            enabled=True,
            access_model="DATASET_DOWNLOAD",
            programmes_provided=["SCHEME", "PROGRAMME", "COMPONENT"],
            notes="Machine-readable open datasets and scheme catalogues."
        )

        # ── TIER 2: CENTRAL MINISTRIES & DEPARTMENTS ───────────────────────────
        central_ministries = [
            ("moa_fw", "Ministry of Agriculture and Farmers Welfare", "https://agricoop.nic.in", ["SUBSIDY", "CREDIT_PROGRAMME", "INSURANCE_PROGRAMME"]),
            ("moe", "Ministry of Education", "https://www.education.gov.in", ["SCHOLARSHIP", "GRANT", "PROGRAMME"]),
            ("mohfw", "Ministry of Health and Family Welfare", "https://mohfw.gov.in", ["INSURANCE_PROGRAMME", "BENEFIT_PROGRAMME"]),
            ("msje", "Ministry of Social Justice and Empowerment", "https://socialjustice.gov.in", ["SCHOLARSHIP", "PENSION", "GRANT"]),
            ("mohua", "Ministry of Housing and Urban Affairs", "https://mohua.gov.in", ["SUBSIDY", "CREDIT_PROGRAMME"]),
            ("mord", "Ministry of Rural Development", "https://rural.nic.in", ["EMPLOYMENT_PROGRAMME", "PENSION", "HOUSING"]),
            ("wcd", "Ministry of Women and Child Development", "https://wcd.nic.in", ["BENEFIT_PROGRAMME", "SCHEME"]),
            ("meity", "Ministry of Electronics and Information Technology", "https://www.meity.gov.in", ["SKILL_PROGRAMME", "SERVICE"]),
            ("msde", "Ministry of Skill Development and Entrepreneurship", "https://www.msde.gov.in", ["SKILL_PROGRAMME", "EMPLOYMENT_PROGRAMME"]),
            ("msme", "Ministry of Micro, Small and Medium Enterprises", "https://msme.gov.in", ["CREDIT_PROGRAMME", "SUBSIDY", "EMPLOYER_PROGRAMME"]),
            ("finmin", "Ministry of Finance", "https://finmin.nic.in", ["INSURANCE_PROGRAMME", "PENSION", "CREDIT_PROGRAMME"]),
            ("mole", "Ministry of Labour and Employment", "https://labour.gov.in", ["PENSION", "INSURANCE_PROGRAMME", "SERVICE"]),
            ("mota", "Ministry of Tribal Affairs", "https://tribal.nic.in", ["SCHOLARSHIP", "GRANT", "SUBSIDY"]),
            ("moma", "Ministry of Minority Affairs", "https://minorityaffairs.gov.in", ["SCHOLARSHIP", "SKILL_PROGRAMME", "CREDIT_PROGRAMME"]),
            ("mopng", "Ministry of Petroleum and Natural Gas", "https://mopng.gov.in", ["SUBSIDY", "BENEFIT_PROGRAMME"]),
            ("mnre", "Ministry of New and Renewable Energy", "https://mnre.gov.in", ["SUBSIDY", "GRANT"]),
            ("jal_shakti", "Ministry of Jal Shakti", "https://jalshakti-ddws.gov.in", ["PROGRAMME", "SERVICE"]),
            ("ayush", "Ministry of Ayush", "https://ayush.gov.in", ["BENEFIT_PROGRAMME", "GRANT"]),
            ("textiles", "Ministry of Textiles", "https://texmin.nic.in", ["SUBSIDY", "SKILL_PROGRAMME"]),
            ("youth_affairs", "Ministry of Youth Affairs and Sports", "https://yas.nic.in", ["SCHOLARSHIP", "GRANT"]),
            ("dairying", "Ministry of Fisheries, Animal Husbandry and Dairying", "https://dahd.nic.in", ["SUBSIDY", "CREDIT_PROGRAMME"]),
            ("panchayat", "Ministry of Panchayati Raj", "https://panchayat.gov.in", ["PROGRAMME", "GRANT"]),
            ("science_tech", "Ministry of Science and Technology", "https://dst.gov.in", ["GRANT", "SCHOLARSHIP"])
        ]

        for m_id, m_name, m_url, p_types in central_ministries:
            sources[f"min_{m_id}"] = SourceDefinition(
                source_id=f"min_{m_id}",
                name=m_name,
                tier="TIER_2_CENTRAL_MINISTRY",
                authority=m_name,
                jurisdiction="CENTRAL",
                portal_url=m_url,
                adapter="CentralMinistryAdapter",
                enabled=True,
                access_model="PUBLIC_PORTAL",
                programmes_provided=p_types,
                notes=f"Central ministry scheme guidelines and application portals for {m_name}."
            )

        # ── TIER 3: 28 STATES & 8 UNION TERRITORIES ───────────────────────────
        states_data = [
            ("Andhra Pradesh", "ap", "https://www.ap.gov.in", "https://meeseva.ap.gov.in"),
            ("Arunachal Pradesh", "ar", "https://arunachalpradesh.gov.in", "https://eservice.arunachal.gov.in"),
            ("Assam", "as", "https://assam.gov.in", "https://sewasetu.assam.gov.in"),
            ("Bihar", "br", "https://state.bihar.gov.in", "https://serviceonline.bihar.gov.in"),
            ("Chhattisgarh", "cg", "https://cgstate.gov.in", "https://edistrict.cgstate.gov.in"),
            ("Goa", "ga", "https://www.goa.gov.in", "https://goaonline.gov.in"),
            ("Gujarat", "gj", "https://gujaratindia.gov.in", "https://digitalgujarat.gov.in"),
            ("Haryana", "hr", "https://haryana.gov.in", "https://saralharyana.gov.in"),
            ("Himachal Pradesh", "hp", "https://himachal.nic.in", "https://edistrict.hp.gov.in"),
            ("Jharkhand", "jh", "https://www.jharkhand.gov.in", "https://jharsewa.jharkhand.gov.in"),
            ("Karnataka", "ka", "https://karnataka.gov.in", "https://sevasindhu.karnataka.gov.in"),
            ("Kerala", "kl", "https://kerala.gov.in", "https://edistrict.kerala.gov.in"),
            ("Madhya Pradesh", "mp", "https://mp.gov.in", "https://mpedistrict.gov.in"),
            ("Maharashtra", "mh", "https://www.maharashtra.gov.in", "https://aaplesarkar.mahaonline.gov.in"),
            ("Manipur", "mn", "https://manipur.gov.in", "https://eservicesmanipur.gov.in"),
            ("Meghalaya", "ml", "https://meghalaya.gov.in", "https://megedistrict.gov.in"),
            ("Mizoram", "mz", "https://mizoram.gov.in", "https://edistrict.mizoram.gov.in"),
            ("Nagaland", "nl", "https://nagaland.gov.in", "https://edistrict.nagaland.gov.in"),
            ("Odisha", "or", "https://odisha.gov.in", "https://edistrict.odisha.gov.in"),
            ("Punjab", "pb", "https://punjab.gov.in", "https://connect.punjab.gov.in"),
            ("Rajasthan", "rj", "https://rajasthan.gov.in", "https://sso.rajasthan.gov.in"),
            ("Sikkim", "sk", "https://sikkim.gov.in", "https://services.sikkim.gov.in"),
            ("Tamil Nadu", "tn", "https://www.tn.gov.in", "https://www.tnesevai.tn.gov.in"),
            ("Telangana", "tg", "https://telangana.gov.in", "https://tg.meeseva.gov.in"),
            ("Tripura", "tr", "https://tripura.gov.in", "https://edistrict.tripura.gov.in"),
            ("Uttar Pradesh", "up", "https://up.gov.in", "https://edistrict.up.gov.in"),
            ("Uttarakhand", "uk", "https://uk.gov.in", "https://eservices.uk.gov.in"),
            ("West Bengal", "wb", "https://wb.gov.in", "https://edistrict.wb.gov.in")
        ]

        uts_data = [
            ("Andaman and Nicobar Islands", "an", "https://www.andaman.gov.in", "https://edistrict.andaman.gov.in"),
            ("Chandigarh", "ch", "https://chandigarh.gov.in", "https://edistrict.chd.gov.in"),
            ("Dadra and Nagar Haveli and Daman and Diu", "dd", "https://ddd.gov.in", "https://serviceonline.gov.in"),
            ("Delhi", "dl", "https://delhi.gov.in", "https://edistrict.delhigovt.nic.in"),
            ("Jammu and Kashmir", "jk", "https://jk.gov.in", "https://jkeservices.gov.in"),
            ("Ladakh", "la", "https://ladakh.gov.in", "https://edistrict.ladakh.gov.in"),
            ("Lakshadweep", "ld", "https://lakshadweep.gov.in", "https://edistrict.lakshadweep.gov.in"),
            ("Puducherry", "py", "https://py.gov.in", "https://edistrict.py.gov.in")
        ]

        for s_name, s_code, s_portal, s_services in states_data:
            sources[f"state_{s_code}"] = SourceDefinition(
                source_id=f"state_{s_code}",
                name=f"Government of {s_name}",
                tier="TIER_3_STATE_UT",
                authority=f"State Government of {s_name}",
                jurisdiction="STATE",
                state_or_ut=s_name,
                portal_url=s_portal,
                adapter="StatePortalAdapter",
                enabled=True,
                access_model="PUBLIC_PORTAL",
                programmes_provided=["SCHEME", "PENSION", "SCHOLARSHIP", "SUBSIDY", "SERVICE"],
                notes=f"State portals and department programmes for {s_name}."
            )
            sources[f"edistrict_{s_code}"] = SourceDefinition(
                source_id=f"edistrict_{s_code}",
                name=f"{s_name} e-District & Citizen Services",
                tier="TIER_4_GOV_SERVICES",
                authority=f"State Citizen Service Delivery — {s_name}",
                jurisdiction="STATE",
                state_or_ut=s_name,
                portal_url=s_services,
                adapter="GovServicesAdapter",
                enabled=True,
                access_model="PUBLIC_PORTAL",
                programmes_provided=["SERVICE", "CERTIFICATE_SERVICE", "APPLICATION_SERVICE"],
                notes=f"State electronic service delivery portal for {s_name}."
            )

        for u_name, u_code, u_portal, u_services in uts_data:
            sources[f"ut_{u_code}"] = SourceDefinition(
                source_id=f"ut_{u_code}",
                name=f"Administration of {u_name}",
                tier="TIER_3_STATE_UT",
                authority=f"UT Administration of {u_name}",
                jurisdiction="UT",
                state_or_ut=u_name,
                portal_url=u_portal,
                adapter="StatePortalAdapter",
                enabled=True,
                access_model="PUBLIC_PORTAL",
                programmes_provided=["SCHEME", "PENSION", "SCHOLARSHIP", "SERVICE"],
                notes=f"Union Territory portal and citizen programmes for {u_name}."
            )
            sources[f"edistrict_{u_code}"] = SourceDefinition(
                source_id=f"edistrict_{u_code}",
                name=f"{u_name} e-District & Services",
                tier="TIER_4_GOV_SERVICES",
                authority=f"UT Citizen Service Delivery — {u_name}",
                jurisdiction="UT",
                state_or_ut=u_name,
                portal_url=u_services,
                adapter="GovServicesAdapter",
                enabled=True,
                access_model="PUBLIC_PORTAL",
                programmes_provided=["SERVICE", "CERTIFICATE_SERVICE", "APPLICATION_SERVICE"],
                notes=f"UT electronic service delivery portal for {u_name}."
            )

        # ── TIER 6: OFFICIAL DOCUMENTS ─────────────────────────────────────────
        sources["egazette_india"] = SourceDefinition(
            source_id="egazette_india",
            name="The Gazette of India (eGazette)",
            tier="TIER_6_DOCUMENTS",
            authority="Directorate of Printing / MoHUA",
            jurisdiction="CENTRAL",
            portal_url="https://egazette.gov.in",
            adapter="DataGovAdapter",
            enabled=True,
            access_model="PUBLIC_PORTAL",
            programmes_provided=["PROGRAMME", "INFORMATIONAL_PROGRAMME"],
            notes="Statutory gazette notifications, ministry orders, and operational amendments."
        )

        return sources

    @property
    def sources(self) -> Dict[str, SourceDefinition]:
        return self._sources

    def get_source(self, source_id: str) -> Optional[SourceDefinition]:
        return self._sources.get(source_id)

    def list_sources(self, tier: Optional[str] = None, enabled_only: bool = False) -> List[SourceDefinition]:
        results = list(self._sources.values())
        if tier:
            results = [s for s in results if s.tier == tier]
        if enabled_only:
            results = [s for s in results if s.enabled]
        return results


# Backward compatibility alias
DiscoverySourceRegistry = GovernmentProgrammeSourceRegistry
