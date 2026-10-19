"""
State & UT Discovery Connector (Tier 4 State Sources)
Discovers official state & UT government schemes across ALL 28 States and 8 Union Territories.
Enforces strict TLS, evidence lineage, and boundary segregation.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .base import BaseConnector
from services.core.ingestion.fetcher import SourceFetcher

ALL_INDIA_JURISDICTION_CONFIGS = [
    # ── 28 STATES ──────────────────────────────────────────────────────────
    {
        "state_code": "AP",
        "state_name": "Andhra Pradesh",
        "jurisdiction": "STATE",
        "portal_url": "https://www.ap.gov.in",
        "fallback_url": "https://navasakam.ap.gov.in",
        "seeds": [
            {"name": "YSR Cheyutha", "department": "Department of Social Welfare", "url": "https://gramawardsachivalayam.ap.gov.in"},
            {"name": "YSR Rythu Bharosa", "department": "Department of Agriculture", "url": "https://ysrrythubharosa.ap.gov.in"},
            {"name": "YSR Pension Kanuka", "department": "Society for Elimination of Rural Poverty", "url": "https://sspensions.ap.gov.in"}
        ]
    },
    {
        "state_code": "AR",
        "state_name": "Arunachal Pradesh",
        "jurisdiction": "STATE",
        "portal_url": "https://arunachalpradesh.gov.in",
        "fallback_url": "https://cmstartup.arunachal.gov.in",
        "seeds": [
            {"name": "Deen Dayal Upadhyaya Swavalamban Yojana", "department": "Department of Planning and Investment", "url": "https://cmstartup.arunachal.gov.in"},
            {"name": "Chief Minister Arogya Arunachal Yojana", "department": "Health and Family Welfare Department", "url": "https://cmaay.com"}
        ]
    },
    {
        "state_code": "AS",
        "state_name": "Assam",
        "jurisdiction": "STATE",
        "portal_url": "https://assam.gov.in",
        "fallback_url": "https://sewasetu.assam.gov.in",
        "seeds": [
            {"name": "Orunodoi Scheme", "department": "Finance Department", "url": "https://orunodoi.assam.gov.in"},
            {"name": "Pragyan Bharati Scooty Scheme", "department": "Higher Education Department", "url": "https://directorateofhighereducation.assam.gov.in"}
        ]
    },
    {
        "state_code": "BR",
        "state_name": "Bihar",
        "jurisdiction": "STATE",
        "portal_url": "https://state.bihar.gov.in",
        "fallback_url": "https://serviceonline.bihar.gov.in",
        "seeds": [
            {"name": "Mukhyamantri Kanya Utthan Yojana", "department": "Social Welfare Department", "url": "https://medhasoft.bih.nic.in"},
            {"name": "Bihar Student Credit Card Scheme", "department": "Education Department", "url": "https://www.7nishchay-yuvaupmission.bihar.gov.in"}
        ]
    },
    {
        "state_code": "CG",
        "state_name": "Chhattisgarh",
        "jurisdiction": "STATE",
        "portal_url": "https://cgstate.gov.in",
        "fallback_url": "https://mahtarivandan.cgstate.gov.in",
        "seeds": [
            {"name": "Mahtari Vandan Yojana", "department": "Women and Child Development Department", "url": "https://mahtarivandan.cgstate.gov.in"},
            {"name": "Rajiv Gandhi Kisan Nyay Yojana", "department": "Agriculture Department", "url": "https://kisan.cg.nic.in"}
        ]
    },
    {
        "state_code": "GA",
        "state_name": "Goa",
        "jurisdiction": "STATE",
        "portal_url": "https://www.goa.gov.in",
        "fallback_url": "https://goaonline.gov.in",
        "seeds": [
            {"name": "Griha Aadhar Scheme", "department": "Directorate of Social Welfare", "url": "https://www.goa.gov.in/citizen/griha-aadhar-scheme/"},
            {"name": "Dayanand Social Security Scheme", "department": "Directorate of Social Welfare", "url": "https://socialwelfare.goa.gov.in"}
        ]
    },
    {
        "state_code": "GJ",
        "state_name": "Gujarat",
        "jurisdiction": "STATE",
        "portal_url": "https://gujaratindia.gov.in",
        "fallback_url": "https://digitalgujarat.gov.in",
        "seeds": [
            {"name": "Mukhyamantri Kisan Sahay Yojana", "department": "Agriculture, Farmers Welfare and Co-operation Department", "url": "https://ikhedut.gujarat.gov.in"},
            {"name": "Vhali Dikri Yojana", "department": "Women and Child Development Department", "url": "https://wcd.gujarat.gov.in"}
        ]
    },
    {
        "state_code": "HR",
        "state_name": "Haryana",
        "jurisdiction": "STATE",
        "portal_url": "https://haryana.gov.in",
        "fallback_url": "https://saralharyana.gov.in",
        "seeds": [
            {"name": "Mukhyamantri Parivar Samridhi Yojana", "department": "Social Justice and Empowerment", "url": "https://cm-psy.haryana.gov.in"},
            {"name": "Parivar Pehchan Patra Benefits", "department": "Citizen Resources Information Department", "url": "https://meraparivar.haryana.gov.in"}
        ]
    },
    {
        "state_code": "HP",
        "state_name": "Himachal Pradesh",
        "jurisdiction": "STATE",
        "portal_url": "https://himachal.nic.in",
        "fallback_url": "https://edistrict.hp.gov.in",
        "seeds": [
            {"name": "HIMCARE Health Scheme", "department": "Health and Family Welfare Department", "url": "https://www.hpsbys.in"},
            {"name": "Indira Gandhi Pyari Behna Sukh Samman Nidhi", "department": "Social Justice and Empowerment", "url": "https://himachal.nic.in"}
        ]
    },
    {
        "state_code": "JH",
        "state_name": "Jharkhand",
        "jurisdiction": "STATE",
        "portal_url": "https://jharkhand.gov.in",
        "fallback_url": "https://jharsewa.jharkhand.gov.in",
        "seeds": [
            {"name": "Jharkhand Mukhyamantri Maiyan Samman Yojana", "department": "Women, Child Development and Social Security", "url": "https://mmmsy.jharkhand.gov.in"},
            {"name": "Birsa Harit Gram Yojana", "department": "Rural Development Department", "url": "https://jharkhand.gov.in"}
        ]
    },
    {
        "state_code": "KA",
        "state_name": "Karnataka",
        "jurisdiction": "STATE",
        "portal_url": "https://karnataka.gov.in",
        "fallback_url": "https://sevasindhu.karnataka.gov.in",
        "seeds": [
            {"name": "Gruha Lakshmi Scheme", "department": "Women and Child Development Department", "url": "https://sevasindhu.karnataka.gov.in"},
            {"name": "Yuva Nidhi Scheme", "department": "Department of Skill Development", "url": "https://sevasindhu.karnataka.gov.in"},
            {"name": "Gruha Jyothi Scheme", "department": "Energy Department", "url": "https://sevasindhu.karnataka.gov.in"}
        ]
    },
    {
        "state_code": "KL",
        "state_name": "Kerala",
        "jurisdiction": "STATE",
        "portal_url": "https://kerala.gov.in",
        "fallback_url": "https://edistrict.kerala.gov.in",
        "seeds": [
            {"name": "Karunya Benevolent Fund", "department": "Health and Family Welfare Department", "url": "https://karunya.kerala.gov.in"},
            {"name": "Kerala Social Security Welfare Pension", "department": "Local Self Government Department", "url": "https://welfarepension.lsgkerala.gov.in"}
        ]
    },
    {
        "state_code": "MP",
        "state_name": "Madhya Pradesh",
        "jurisdiction": "STATE",
        "portal_url": "https://mp.gov.in",
        "fallback_url": "https://samagra.gov.in",
        "seeds": [
            {"name": "Mukhyamantri Ladli Behna Yojana", "department": "Women and Child Development Department", "url": "https://cmladlibahna.mp.gov.in"},
            {"name": "Ladli Laxmi Yojana", "department": "Women and Child Development Department", "url": "https://ladlilaxmi.mp.gov.in"}
        ]
    },
    {
        "state_code": "MH",
        "state_name": "Maharashtra",
        "jurisdiction": "STATE",
        "portal_url": "https://maharashtra.gov.in",
        "fallback_url": "https://aaplesarkar.mahaonline.gov.in",
        "seeds": [
            {"name": "Mukhyamantri Majhi Ladki Bahin Yojana", "department": "Women and Child Development Department", "url": "https://ladkibahin.maharashtra.gov.in"},
            {"name": "Sanjay Gandhi Niradhar Anudan Yojana", "department": "Social Justice and Special Assistance Department", "url": "https://sjsa.maharashtra.gov.in"}
        ]
    },
    {
        "state_code": "MN",
        "state_name": "Manipur",
        "jurisdiction": "STATE",
        "portal_url": "https://manipur.gov.in",
        "fallback_url": "https://cmhtmanipur.gov.in",
        "seeds": [
            {"name": "Chief Minister-gi Hakshelgi Tengbang", "department": "Health and Family Welfare Department", "url": "https://cmhtmanipur.gov.in"},
            {"name": "StartUp Manipur", "department": "Planning Department", "url": "https://startupmanipur.in"}
        ]
    },
    {
        "state_code": "ML",
        "state_name": "Meghalaya",
        "jurisdiction": "STATE",
        "portal_url": "https://meghalaya.gov.in",
        "fallback_url": "https://mhis.org.in",
        "seeds": [
            {"name": "Megha Health Insurance Scheme", "department": "Health and Family Welfare Department", "url": "https://mhis.org.in"},
            {"name": "FOCUS Scheme Meghalaya", "department": "Community and Rural Development Department", "url": "https://focus.meghalaya.gov.in"}
        ]
    },
    {
        "state_code": "MZ",
        "state_name": "Mizoram",
        "jurisdiction": "STATE",
        "portal_url": "https://mizoram.gov.in",
        "fallback_url": "https://sedp.mizoram.gov.in",
        "seeds": [
            {"name": "Mizoram Health Care Scheme", "department": "Health and Family Welfare Department", "url": "https://health.mizoram.gov.in"},
            {"name": "Socio-Economic Development Policy Grant", "department": "Planning and Programme Implementation", "url": "https://sedp.mizoram.gov.in"}
        ]
    },
    {
        "state_code": "NL",
        "state_name": "Nagaland",
        "jurisdiction": "STATE",
        "portal_url": "https://nagaland.gov.in",
        "fallback_url": "https://cmhis.nagaland.gov.in",
        "seeds": [
            {"name": "Chief Minister Health Insurance Scheme Nagaland", "department": "Health and Family Welfare Department", "url": "https://cmhis.nagaland.gov.in"},
            {"name": "Nagaland State Rural Livelihoods Mission", "department": "Rural Development Department", "url": "https://nsrlm.nagaland.gov.in"}
        ]
    },
    {
        "state_code": "OD",
        "state_name": "Odisha",
        "jurisdiction": "STATE",
        "portal_url": "https://odisha.gov.in",
        "fallback_url": "https://odishaone.gov.in",
        "seeds": [
            {"name": "Subhadra Yojana", "department": "Women and Child Development Department", "url": "https://subhadra.odisha.gov.in"},
            {"name": "Biju Swasthya Kalyan Yojana", "department": "Health and Family Welfare Department", "url": "https://bsky.odisha.gov.in"},
            {"name": "KALIA Scheme Odisha", "department": "Department of Agriculture and Farmers Empowerment", "url": "https://kalia.odisha.gov.in"}
        ]
    },
    {
        "state_code": "PB",
        "state_name": "Punjab",
        "jurisdiction": "STATE",
        "portal_url": "https://punjab.gov.in",
        "fallback_url": "https://sha.punjab.gov.in",
        "seeds": [
            {"name": "Mukh Mantri Sehat Bima Yojana", "department": "State Health Agency Punjab", "url": "https://sha.punjab.gov.in"},
            {"name": "Ashirwad Scheme Punjab", "department": "Social Justice, Empowerment and Minorities Department", "url": "https://socwel.punjab.gov.in"}
        ]
    },
    {
        "state_code": "RJ",
        "state_name": "Rajasthan",
        "jurisdiction": "STATE",
        "portal_url": "https://rajasthan.gov.in",
        "fallback_url": "https://jansoochna.rajasthan.gov.in",
        "seeds": [
            {"name": "Mukhyamantri Ayushman Arogya Yojana", "department": "Medical, Health and Family Welfare Department", "url": "https://health.rajasthan.gov.in"},
            {"name": "Indira Gandhi Rasoi Yojana", "department": "Local Self Government Department", "url": "https://nagarnigam.rajasthan.gov.in"}
        ]
    },
    {
        "state_code": "SK",
        "state_name": "Sikkim",
        "jurisdiction": "STATE",
        "portal_url": "https://sikkim.gov.in",
        "fallback_url": "https://sikkim.gov.in",
        "seeds": [
            {"name": "Aama Yojana Sikkim", "department": "Social Welfare Department", "url": "https://sikkim.gov.in"},
            {"name": "Sikkim Skilled Youth Startup Scheme", "department": "Commerce and Industries Department", "url": "https://sikkim.gov.in"}
        ]
    },
    {
        "state_code": "TN",
        "state_name": "Tamil Nadu",
        "jurisdiction": "STATE",
        "portal_url": "https://www.tn.gov.in",
        "fallback_url": "https://www.tnesevai.tn.gov.in",
        "seeds": [
            {"name": "Kalaignar Magalir Urimai Thittam", "department": "Special Programme Implementation Department", "url": "https://kmut.tn.gov.in"},
            {"name": "Moovalur Ramamirtham Ammaiyar Pudhumai Penn", "department": "Social Welfare and Women Empowerment Department", "url": "https://pudhumaipenn.tn.gov.in"}
        ]
    },
    {
        "state_code": "TG",
        "state_name": "Telangana",
        "jurisdiction": "STATE",
        "portal_url": "https://telangana.gov.in",
        "fallback_url": "https://meeseva.telangana.gov.in",
        "seeds": [
            {"name": "Rythu Bandhu Scheme", "department": "Department of Agriculture", "url": "https://rythubandhu.telangana.gov.in"},
            {"name": "Kalyan Lakshmi Shaadi Mubarak", "department": "Backward Classes Welfare Department", "url": "https://telanganaepass.cgg.gov.in"}
        ]
    },
    {
        "state_code": "TR",
        "state_name": "Tripura",
        "jurisdiction": "STATE",
        "portal_url": "https://tripura.gov.in",
        "fallback_url": "https://bms.tripura.gov.in",
        "seeds": [
            {"name": "Mukhyamantri Matru Pushti Uphaar", "department": "Social Welfare and Social Education Department", "url": "https://tripura.gov.in"},
            {"name": "Mukhyamantri Yuba Yogayog Yojana", "department": "Department of Information Technology", "url": "https://bms.tripura.gov.in"}
        ]
    },
    {
        "state_code": "UP",
        "state_name": "Uttar Pradesh",
        "jurisdiction": "STATE",
        "portal_url": "https://up.gov.in",
        "fallback_url": "https://sspy-up.gov.in",
        "seeds": [
            {"name": "Mukhyamantri Kanya Sumangala Yojana", "department": "Women and Child Development Department", "url": "https://mksy.up.gov.in"},
            {"name": "Uttar Pradesh Vridhavastha Pension Yojana", "department": "Social Welfare Department", "url": "https://sspy-up.gov.in"},
            {"name": "Uttar Pradesh Shadi Anudan Yojana", "department": "Social Welfare Department", "url": "https://shadianudan.upsdc.gov.in"}
        ]
    },
    {
        "state_code": "UK",
        "state_name": "Uttarakhand",
        "jurisdiction": "STATE",
        "portal_url": "https://uk.gov.in",
        "fallback_url": "https://eservices.uk.gov.in",
        "seeds": [
            {"name": "Atal Ayushman Uttarakhand Yojana", "department": "State Health Agency Uttarakhand", "url": "https://ayushmanuttarakhand.org"},
            {"name": "Gaura Devi Kanyadhan Yojana", "department": "Social Welfare Department", "url": "https://socialwelfare.uk.gov.in"}
        ]
    },
    {
        "state_code": "WB",
        "state_name": "West Bengal",
        "jurisdiction": "STATE",
        "portal_url": "https://wb.gov.in",
        "fallback_url": "https://bsk.wb.gov.in",
        "seeds": [
            {"name": "Lakshmir Bhandar", "department": "Women and Child Development and Social Welfare Department", "url": "https://socialwelfare.wb.gov.in"},
            {"name": "Kanyashree Prakalpa", "department": "Women and Child Development and Social Welfare Department", "url": "https://www.wbkanyashree.gov.in"},
            {"name": "Krishak Bandhu Scheme", "department": "Department of Agriculture", "url": "https://krishakbandhu.wb.gov.in"}
        ]
    },

    # ── 8 UNION TERRITORIES ────────────────────────────────────────────────
    {
        "state_code": "AN",
        "state_name": "Andaman & Nicobar Islands",
        "jurisdiction": "UT",
        "portal_url": "https://andaman.nic.in",
        "fallback_url": "https://andaman.gov.in",
        "seeds": [
            {"name": "Andaman Financial Assistance to Widows", "department": "Directorate of Social Welfare", "url": "https://andaman.nic.in"}
        ]
    },
    {
        "state_code": "CH",
        "state_name": "Chandigarh",
        "jurisdiction": "UT",
        "portal_url": "https://chandigarh.gov.in",
        "fallback_url": "https://chandigarh.nic.in",
        "seeds": [
            {"name": "Chandigarh Social Welfare Pension", "department": "Social Welfare Department Chandigarh Administration", "url": "https://chandigarh.gov.in"}
        ]
    },
    {
        "state_code": "DNHDD",
        "state_name": "Dadra & Nagar Haveli and Daman & Diu",
        "jurisdiction": "UT",
        "portal_url": "https://ddd.gov.in",
        "fallback_url": "https://ddd.gov.in",
        "seeds": [
            {"name": "Saraswati Vidya Yojana DNH&DD", "department": "Department of Education DNH&DD", "url": "https://ddd.gov.in"},
            {"name": "Dikri Samman Yojana DNH&DD", "department": "Social Welfare Department DNH&DD", "url": "https://ddd.gov.in"}
        ]
    },
    {
        "state_code": "DL",
        "state_name": "Delhi",
        "jurisdiction": "UT",
        "portal_url": "https://delhi.gov.in",
        "fallback_url": "https://edistrict.delhigovt.nic.in",
        "seeds": [
            {"name": "Delhi Financial Assistance to Senior Citizens", "department": "Department of Social Welfare GNCTD", "url": "https://edistrict.delhigovt.nic.in"},
            {"name": "Delhi Ladli Scheme", "department": "Department of Women and Child Development GNCTD", "url": "https://wcd.delhi.gov.in"}
        ]
    },
    {
        "state_code": "JK",
        "state_name": "Jammu & Kashmir",
        "jurisdiction": "UT",
        "portal_url": "https://jk.gov.in",
        "fallback_url": "https://eunnat.jk.gov.in",
        "seeds": [
            {"name": "Ladli Beti Scheme Jammu and Kashmir", "department": "Social Welfare Department J&K", "url": "https://jksocialwelfare.nic.in"},
            {"name": "Jammu and Kashmir Integrated Social Security Scheme", "department": "Social Welfare Department J&K", "url": "https://eunnat.jk.gov.in"}
        ]
    },
    {
        "state_code": "LA",
        "state_name": "Ladakh",
        "jurisdiction": "UT",
        "portal_url": "https://ladakh.gov.in",
        "fallback_url": "https://ladakh.gov.in",
        "seeds": [
            {"name": "Ladakh Social Security Pension Scheme", "department": "Social and Tribal Welfare Department Ladakh", "url": "https://ladakh.gov.in"},
            {"name": "Rewa Scheme Ladakh", "department": "Higher Education Department Ladakh", "url": "https://ladakh.gov.in"}
        ]
    },
    {
        "state_code": "LD",
        "state_name": "Lakshadweep",
        "jurisdiction": "UT",
        "portal_url": "https://lakshadweep.gov.in",
        "fallback_url": "https://lakshadweep.gov.in",
        "seeds": [
            {"name": "Lakshadweep Post Matric Scholarship", "department": "Department of Education UT of Lakshadweep", "url": "https://lakshadweep.gov.in"}
        ]
    },
    {
        "state_code": "PY",
        "state_name": "Puducherry",
        "jurisdiction": "UT",
        "portal_url": "https://py.gov.in",
        "fallback_url": "https://socwelfare.py.gov.in",
        "seeds": [
            {"name": "Puducherry Old Age Pension Scheme", "department": "Department of Social Welfare Government of Puducherry", "url": "https://socwelfare.py.gov.in"},
            {"name": "Perunthalaivar Kamarajar Financial Assistance", "department": "Directorate of Higher and Technical Education", "url": "https://py.gov.in"}
        ]
    }
]

# Backward compatibility alias
PILOT_STATE_CONFIGS = [c for c in ALL_INDIA_JURISDICTION_CONFIGS if c["state_code"] in ["UP", "MH", "BR", "KA", "WB"]]


class StatePortalsConnector(BaseConnector):
    def __init__(self, fetcher: Optional[SourceFetcher] = None):
        super().__init__(connector_id="state_portals", authority_tier="tier4_state")
        self.fetcher = fetcher or SourceFetcher(enforce_domain_allowlist=True)

    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discovers candidate schemes across ALL 28 States and 8 Union Territories.
        Never publishes directly to canonical scheme versions.
        """
        candidates: List[Dict[str, Any]] = []
        retrieved_at = datetime.now(timezone.utc).isoformat()

        for jur in ALL_INDIA_JURISDICTION_CONFIGS:
            for seed in jur["seeds"]:
                candidates.append({
                    "candidate_id": f"state-{jur['state_code'].lower()}-{seed['name'].lower().replace(' ', '-')[:28]}",
                    "official_name": seed["name"],
                    "state_code": jur["state_code"],
                    "state_name": jur["state_name"],
                    "jurisdiction": jur["jurisdiction"],
                    "authority": seed["department"],
                    "scheme_level": "State" if jur["jurisdiction"] == "STATE" else "UT",
                    "source_url": seed["url"],
                    "origin_domain": jur["portal_url"],
                    "fallback_domain": jur.get("fallback_url"),
                    "authority_tier": self.authority_tier,
                    "retrieved_at": retrieved_at,
                    "discovery_status": "discovery_staged"
                })
                if limit and len(candidates) >= limit:
                    return candidates

        return candidates

    def fetch_source(self, candidate: Dict[str, Any]) -> Tuple[int, bytes, str]:
        """Fetches candidate web page using SourceFetcher."""
        url = candidate.get("source_url", "")
        res = self.fetcher.fetch(url)
        return res.status_code, res.content, res.content_type
