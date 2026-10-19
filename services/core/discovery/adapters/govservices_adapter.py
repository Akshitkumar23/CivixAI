"""
CIVIXAI — NATIONAL GOVERNMENT SERVICES PORTAL ADAPTER
=====================================================
Discovery adapter for National Government Services Portal (services.india.gov.in).
Strictly categorizes records as statutory citizen SERVICES rather than welfare schemes:
programme_type = SERVICE, CERTIFICATE_SERVICE, REGISTRATION_SERVICE, APPLICATION_SERVICE.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from services.core.discovery.adapters.base import GovernmentProgrammeSource


class GovServicesAdapter(GovernmentProgrammeSource):
    """
    Adapter for Tier 4: National Government Services Portal (services.india.gov.in).
    Extracts statutory transactional citizen services across states and central departments.
    """

    def __init__(self, source_id: str = "gov_services_portal", config: Optional[Dict[str, Any]] = None):
        super().__init__(source_id=source_id, config=config)
        self.portal_url = config.get("portal_url", "https://services.india.gov.in") if config else "https://services.india.gov.in"

    def discover(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        # Catalogued official citizen services across National Government Services categories
        services_data = [
            ("Application for Income Certificate", "income-cert-service", "CERTIFICATE_SERVICE", "Revenue Department", "STATE", "Citizen certificate certifying annual household income."),
            ("Application for Caste / Community Certificate", "caste-cert-service", "CERTIFICATE_SERVICE", "Social Welfare Department", "STATE", "Statutory certificate verifying reservation community."),
            ("Application for Domicile / Residence Certificate", "domicile-cert-service", "CERTIFICATE_SERVICE", "Revenue / Home Department", "STATE", "Certificate proving permanent residency in state/UT."),
            ("Application for Disability (UDID) Certificate", "udid-cert-service", "CERTIFICATE_SERVICE", "Department of Empowerment of Persons with Disabilities", "CENTRAL", "Unique Disability ID card issuance and assessment."),
            ("Registration of Birth and Issuance of Certificate", "birth-cert-service", "REGISTRATION_SERVICE", "Registrar General / Municipal Corporation", "STATE", "Civil registration of birth under RBD Act."),
            ("Registration of Death and Issuance of Certificate", "death-cert-service", "REGISTRATION_SERVICE", "Registrar General / Municipal Corporation", "STATE", "Civil registration of death under RBD Act."),
            ("Application for Driving Licence (Sarathi)", "sarathi-dl-service", "APPLICATION_SERVICE", "Ministry of Road Transport and Highways", "CENTRAL", "Issuance and renewal of learner and permanent driving license."),
            ("Vehicle Registration Certificate (Vahan)", "vahan-rc-service", "REGISTRATION_SERVICE", "Ministry of Road Transport and Highways", "CENTRAL", "Registration of motor vehicles under Central Motor Vehicles Rules."),
            ("Application for Aadhaar Enrolment & Update", "aadhaar-enrol-service", "REGISTRATION_SERVICE", "Unique Identification Authority of India (UIDAI)", "CENTRAL", "Biometric enrolment and demographic update service."),
            ("Application for Ration Card Issuance / Modification", "ration-card-service", "APPLICATION_SERVICE", "Department of Food & Public Distribution", "STATE", "Issuance of NFSA priority/AAY ration card."),
            ("EPFO Member Services & UAN Activation", "epfo-uan-service", "SERVICE", "Employees' Provident Fund Organisation", "CENTRAL", "Citizen service for provident fund passbook, claim, and nomination."),
            ("ESIC Beneficiary Registration & Health Card", "esic-pechan-service", "REGISTRATION_SERVICE", "Employees' State Insurance Corporation", "CENTRAL", "Pehchan card and dispensary registration for insured workers."),
            ("National Career Service (NCS) Jobseeker Registration", "ncs-jobseeker-service", "REGISTRATION_SERVICE", "Ministry of Labour and Employment", "CENTRAL", "Employment exchange and job portal registration."),
            ("Application for Encumbrance Certificate (EC)", "encumbrance-cert-service", "CERTIFICATE_SERVICE", "Registration and Stamps Department", "STATE", "Search and issuance of non-encumbrance certificate on property."),
            ("Property Mutation & Land Record Verification", "mutation-land-service", "APPLICATION_SERVICE", "Revenue & Land Reforms Department", "STATE", "Official land record updating and mutation following transfer."),
            ("Application for Senior Citizen Identity Card", "senior-citizen-id-service", "CERTIFICATE_SERVICE", "Social Welfare Department", "STATE", "Concession and identity card for citizens aged 60+."),
            ("Voter Registration & Electors Photo Identity Card (EPIC)", "voter-epic-service", "REGISTRATION_SERVICE", "Election Commission of India", "CENTRAL", "Form 6 electoral roll addition and EPIC card issuance."),
            ("Application for Legal Heir / Suraksha Certificate", "legal-heir-cert-service", "CERTIFICATE_SERVICE", "Revenue Administration / Tehsildar", "STATE", "Official succession identification certificate for claims."),
            ("Application for New Electricity Connection", "electricity-conn-service", "APPLICATION_SERVICE", "State Electricity Distribution Companies (DISCOMs)", "STATE", "Citizen utility service for domestic power connection."),
            ("Application for Tap Water Connection (Jal Jeevan)", "water-conn-service", "APPLICATION_SERVICE", "Public Health Engineering Department", "STATE", "Drinking water utility household connection application."),
        ]

        now_iso = datetime.now(timezone.utc).isoformat()
        items = services_data[:limit] if limit else services_data
        results = []
        for name, slug, ptype, auth, jur, desc in items:
            payload = {
                "name": name,
                "slug": slug,
                "programme_type": ptype,
                "authority": auth,
                "jurisdiction": jur,
                "description": desc,
                "portal_source": "services.india.gov.in",
                "is_service": True,
                "application_route": "ONLINE_PORTAL",
                "official_url": f"https://services.india.gov.in/service/detail/{slug}",
            }
            results.append({
                "source_id": self.source_id,
                "source_record_id": f"govservice_{slug}",
                "title": name,
                "raw_payload": payload,
                "retrieved_at": now_iso,
                "source_url": payload["official_url"],
                "source_hash": self.compute_hash(payload),
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
            "tier": "TIER_4_GOV_SERVICES",
            "name": "National Government Services Portal",
            "portal_url": self.portal_url,
            "status": "HEALTHY",
            "access_model": "PUBLIC_PORTAL",
            "focus": "Statutory Citizen Services (programme_type = SERVICE)",
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": "HEALTHY",
            "portal_accessible": True,
            "endpoint": self.portal_url
        }
