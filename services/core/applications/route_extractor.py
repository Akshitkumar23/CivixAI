"""
CivixAI Application Route Extractor
==================================
Extracts verified government application delivery channels from staging data,
associates documentary prerequisites, and checks government domain security.

Supported Channel Types:
- ONLINE_PORTAL: Direct web application on official .gov.in portal.
- CSC_OFFLINE: Common Service Center (CSC), Village Level Entrepreneur (VLE).
- BANK_BRANCH: Commercial bank, RRB, or Post Office physical submission.
- DISTRICT_OFFICE: District Magistrate / Tehsildar / Block Development Office.
- TOLL_FREE_IVR: Emergency telephone dispatch (e.g. 108, 112, 104).
"""

from __future__ import annotations
import json
import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.core.security.ssrf import validate_government_url, OFFICIAL_GOV_DOMAINS
from services.core.discovery.governance import EvidenceAnchor


class ChannelType(str, Enum):
    ONLINE_PORTAL = "ONLINE_PORTAL"
    CSC_OFFLINE = "CSC_OFFLINE"
    BANK_BRANCH = "BANK_BRANCH"
    DISTRICT_OFFICE = "DISTRICT_OFFICE"
    DEPARTMENT_OFFICE = "DEPARTMENT_OFFICE"
    TOLL_FREE_IVR = "TOLL_FREE_IVR"
    OFFICIALLY_AUTHORIZED_THIRD_PARTY = "OFFICIALLY_AUTHORIZED_THIRD_PARTY"
    HYBRID = "HYBRID"
    UNKNOWN = "UNKNOWN"


# Registry of authoritative government-authorized external scheme endpoints
# Explicitly ties external non-gov domains to the official government evidence proving authorization.
OFFICIALLY_AUTHORIZED_EXTERNAL_ENDPOINTS: Dict[str, Dict[str, str]] = {
    "assamfinanceloans.in": {
        "candidate_id": "cand-src-myscheme-national-aaelss",
        "authority": "Finance Department, Government of Assam",
        "evidence": "Dedicated Assam State Loan Subsidy Portal verified via MeitY myScheme snapshot (myscheme_api_aaelss_499c989d8db3) and UMANG National Governance Directory.",
        "route_type": "OFFICIALLY_AUTHORIZED_THIRD_PARTY",
    }
}


class ApplicationRoute(BaseModel):
    route_id: str
    candidate_id: str
    channel_type: ChannelType
    official_url: Optional[str] = None
    is_url_gov_verified: bool = False
    is_officially_authorized_third_party: bool = False
    authorization_evidence_notes: Optional[str] = None
    toll_free_number: Optional[str] = None
    instructions_summary: str
    documents_required: List[str] = Field(default_factory=list)
    evidence_id: Optional[str] = None


class ApplicationRouteExtractor:
    """Extracts and validates official application access channels."""

    def __init__(self):
        pass

    def extract_route(
        self,
        candidate_id: str,
        application_method: Any,
        application_url: Optional[str] = None,
        official_contact: Optional[str] = None,
        evidence_anchor: Optional[EvidenceAnchor] = None,
    ) -> ApplicationRoute:
        evidence_id = evidence_anchor.evidence_id if evidence_anchor else None
        method_text = self._flatten(application_method)
        if (not method_text or method_text.strip() == "UNKNOWN") and evidence_anchor and evidence_anchor.extracted_text:
            method_text = self._flatten(evidence_anchor.extracted_text)

        lower_method = method_text.lower()
        contact_text = official_contact or ""

        # Extract embedded URLs if application_url is unknown or missing
        if (not application_url or "UNKNOWN" in application_url) and method_text:
            found_urls = re.findall(r"https?://[^\s\)\]\"\'>]+", method_text)
            if found_urls:
                application_url = found_urls[0].rstrip(".,;)\"']")

        # 1. Emergency Dial / IVR (e.g. 108, 112, 104)
        m_phone = re.search(r"\b(108|112|104|1905|1800[-\d]+)\b", contact_text + " " + method_text)
        if "108" in lower_method or (m_phone and m_phone.group(1) in ("108", "112", "104")):
            dial_num = m_phone.group(1) if m_phone else "108"
            return ApplicationRoute(
                route_id=f"route-{candidate_id}",
                candidate_id=candidate_id,
                channel_type=ChannelType.TOLL_FREE_IVR,
                toll_free_number=dial_num,
                is_url_gov_verified=True,
                instructions_summary=f"Dial toll-free emergency number {dial_num} from any telephone. 24x7 immediate dispatch.",
                documents_required=[],
                evidence_id=evidence_id,
            )

        # 2. Officially Authorized Third-Party Portals (e.g. dedicated state statutory schemes on non-gov domains)
        if application_url:
            for auth_domain, auth_info in OFFICIALLY_AUTHORIZED_EXTERNAL_ENDPOINTS.items():
                if auth_domain in application_url.lower():
                    return ApplicationRoute(
                        route_id=f"route-{candidate_id}",
                        candidate_id=candidate_id,
                        channel_type=ChannelType.OFFICIALLY_AUTHORIZED_THIRD_PARTY,
                        official_url=application_url,
                        is_url_gov_verified=False,
                        is_officially_authorized_third_party=True,
                        authorization_evidence_notes=auth_info["evidence"],
                        instructions_summary=f"Officially authorized third-party application portal: {application_url}. Authorized by {auth_info['authority']}.",
                        documents_required=self._extract_docs(method_text),
                        evidence_id=evidence_id,
                    )

        # 3. Online Portal URL Validation (.gov.in / .nic.in)
        is_gov_url = False
        if application_url:
            try:
                # SSRF allowlist validation
                validated = validate_government_url(application_url)
                is_gov_url = bool(validated)
            except Exception:
                is_gov_url = False

            if not is_gov_url:
                is_gov_url = any(domain in application_url.lower() for domain in [".gov.in", ".nic.in"])

        if is_gov_url:
            return ApplicationRoute(
                route_id=f"route-{candidate_id}",
                candidate_id=candidate_id,
                channel_type=ChannelType.ONLINE_PORTAL,
                official_url=application_url,
                is_url_gov_verified=True,
                is_officially_authorized_third_party=False,
                instructions_summary=f"Apply online through the official government portal: {application_url}",
                documents_required=self._extract_docs(method_text),
                evidence_id=evidence_id,
            )

        # Unverified Online Portal Attempt (e.g. third-party form lacking statutory authorization)
        if application_url and ("online" in lower_method or "UNKNOWN" not in application_url):
            return ApplicationRoute(
                route_id=f"route-{candidate_id}",
                candidate_id=candidate_id,
                channel_type=ChannelType.ONLINE_PORTAL,
                official_url=application_url,
                is_url_gov_verified=False,
                is_officially_authorized_third_party=False,
                instructions_summary=f"Unverified external route: {application_url} (Requires domain compliance verification)",
                documents_required=self._extract_docs(method_text),
                evidence_id=evidence_id,
            )

        # 4. Bank Branch / Auto-Debit mandate
        if "bank" in lower_method or "branch" in lower_method or "auto-debit" in lower_method or "auto debit" in lower_method:
            return ApplicationRoute(
                route_id=f"route-{candidate_id}",
                candidate_id=candidate_id,
                channel_type=ChannelType.BANK_BRANCH,
                official_url=application_url,
                instructions_summary="Visit your participating commercial bank or Post Office branch. Submit subscriber enrollment form with auto-debit consent.",
                documents_required=["Aadhaar Card", "Bank Passbook", "Identity Proof"],
                evidence_id=evidence_id,
            )

        # 5. CSC / Seva Kendra
        if "csc" in lower_method or "common service center" in lower_method or "kiosk" in lower_method:
            return ApplicationRoute(
                route_id=f"route-{candidate_id}",
                candidate_id=candidate_id,
                channel_type=ChannelType.CSC_OFFLINE,
                official_url=application_url,
                instructions_summary="Visit your nearest Common Service Center (CSC) or Village Level Entrepreneur (VLE) kiosk for assisted digital application.",
                documents_required=self._extract_docs(method_text),
                evidence_id=evidence_id,
            )

        # 5. Default Government District Office
        clean_instructions = method_text[:200] if method_text else "Contact the District Nodal Officer or Block Development Office."
        return ApplicationRoute(
            route_id=f"route-{candidate_id}",
            candidate_id=candidate_id,
            channel_type=ChannelType.DISTRICT_OFFICE,
            official_url=application_url,
            is_url_gov_verified=is_gov_url,
            instructions_summary=clean_instructions,
            documents_required=self._extract_docs(method_text),
            evidence_id=evidence_id,
        )

    def _extract_docs(self, text: str) -> List[str]:
        docs = []
        lower = text.lower()
        if "aadhaar" in lower:
            docs.append("Aadhaar Card")
        if "income" in lower:
            docs.append("Income Certificate")
        if "caste" in lower:
            docs.append("Caste Certificate")
        if "domicile" in lower or "residence" in lower:
            docs.append("Domicile Certificate")
        if "land" in lower or "khasra" in lower or "khatauni" in lower:
            docs.append("Land Ownership Record (RoR / Khasra)")
        if "bank" in lower or "passbook" in lower:
            docs.append("Bank Account Passbook / Cancelled Cheque")
        if not docs:
            docs = ["Aadhaar Card", "Bank Account Details", "Passport Size Photograph"]
        return docs

    def _flatten(self, raw: Any) -> str:
        if not raw:
            return ""
        if isinstance(raw, str):
            raw = raw.strip()
            if (raw.startswith("{") and raw.endswith("}")) or (raw.startswith("[") and raw.endswith("]")):
                try:
                    parsed = json.loads(raw)
                    return self._flatten(parsed)
                except Exception:
                    pass
            if '"text":' in raw or '"mode":' in raw or '"link":' in raw:
                # Extract text, mode, and link fields from JSON slate structure even if truncated
                extracted_pieces = re.findall(r'"(?:text|mode|link)":\s*"([^"\\]*(?:\\.[^"\\]*)*)"', raw)
                if extracted_pieces:
                    clean_pieces = [p.replace(r'\"', '"').replace(r'\n', ' ').strip() for p in extracted_pieces if p.strip()]
                    return " ".join(clean_pieces)
            return raw
        if isinstance(raw, list):
            res = [self._flatten(item) for item in raw if item]
            return " ".join(r for r in res if r).strip()
        if isinstance(raw, dict):
            parts = []
            if "mode" in raw and raw["mode"]:
                parts.append(str(raw["mode"]))
            if "text" in raw and raw["text"]:
                parts.append(str(raw["text"]))
            if "link" in raw and raw["link"]:
                parts.append(str(raw["link"]))
            if "process_md" in raw and raw["process_md"]:
                parts.append(str(raw["process_md"]))
            for k, v in raw.items():
                if k not in ("mode", "text", "link", "process_md", "type", "bold", "underline", "italic"):
                    sub = self._flatten(v)
                    if sub:
                        parts.append(sub)
            return " ".join(parts).strip()
        return str(raw).strip()
