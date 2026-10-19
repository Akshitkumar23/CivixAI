"""
Application Checklist & Status Tracker Service
Manages citizen scheme application lifecycle state machine, versioned official steps,
official .gov.in URL verification, required document checklists, event-driven local reminders,
and a safe offline autofill assistant (draft application data mapping without automated 3rd-party submissions).
"""
from __future__ import annotations
import json
import re
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.core.database.models import Scheme, SchemeVersion, DocumentRequirement

# ── 1. Application Lifecycle State Machine ───────────────────────────────────

class ApplicationLifecycleStatus(str, Enum):
    INTERESTED = "INTERESTED"
    PREPARING = "PREPARING"
    READY_TO_APPLY = "READY_TO_APPLY"
    REDIRECTED_TO_OFFICIAL_PORTAL = "REDIRECTED_TO_OFFICIAL_PORTAL"
    STARTED_EXTERNALLY = "STARTED_EXTERNALLY"
    SUBMITTED = "SUBMITTED"
    UNDER_VERIFICATION = "UNDER_VERIFICATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"
    UNKNOWN_EXTERNAL_STATUS = "UNKNOWN_EXTERNAL_STATUS"

# Valid state machine transitions
ALLOWED_TRANSITIONS: Dict[ApplicationLifecycleStatus, Set[ApplicationLifecycleStatus]] = {
    ApplicationLifecycleStatus.INTERESTED: {
        ApplicationLifecycleStatus.PREPARING,
        ApplicationLifecycleStatus.CLOSED
    },
    ApplicationLifecycleStatus.PREPARING: {
        ApplicationLifecycleStatus.READY_TO_APPLY,
        ApplicationLifecycleStatus.INTERESTED,
        ApplicationLifecycleStatus.CLOSED
    },
    ApplicationLifecycleStatus.READY_TO_APPLY: {
        ApplicationLifecycleStatus.REDIRECTED_TO_OFFICIAL_PORTAL,
        ApplicationLifecycleStatus.PREPARING,
        ApplicationLifecycleStatus.CLOSED
    },
    ApplicationLifecycleStatus.REDIRECTED_TO_OFFICIAL_PORTAL: {
        ApplicationLifecycleStatus.STARTED_EXTERNALLY,
        ApplicationLifecycleStatus.READY_TO_APPLY,
        ApplicationLifecycleStatus.UNKNOWN_EXTERNAL_STATUS,
        ApplicationLifecycleStatus.CLOSED
    },
    ApplicationLifecycleStatus.STARTED_EXTERNALLY: {
        ApplicationLifecycleStatus.SUBMITTED,
        ApplicationLifecycleStatus.UNKNOWN_EXTERNAL_STATUS,
        ApplicationLifecycleStatus.CLOSED
    },
    ApplicationLifecycleStatus.SUBMITTED: {
        ApplicationLifecycleStatus.UNDER_VERIFICATION,
        ApplicationLifecycleStatus.APPROVED,
        ApplicationLifecycleStatus.REJECTED,
        ApplicationLifecycleStatus.UNKNOWN_EXTERNAL_STATUS
    },
    ApplicationLifecycleStatus.UNDER_VERIFICATION: {
        ApplicationLifecycleStatus.APPROVED,
        ApplicationLifecycleStatus.REJECTED,
        ApplicationLifecycleStatus.UNKNOWN_EXTERNAL_STATUS
    },
    ApplicationLifecycleStatus.APPROVED: {
        ApplicationLifecycleStatus.CLOSED
    },
    ApplicationLifecycleStatus.REJECTED: {
        ApplicationLifecycleStatus.PREPARING,  # Re-apply / re-prepare with corrected documents
        ApplicationLifecycleStatus.CLOSED
    },
    ApplicationLifecycleStatus.UNKNOWN_EXTERNAL_STATUS: {
        ApplicationLifecycleStatus.SUBMITTED,
        ApplicationLifecycleStatus.UNDER_VERIFICATION,
        ApplicationLifecycleStatus.APPROVED,
        ApplicationLifecycleStatus.REJECTED,
        ApplicationLifecycleStatus.CLOSED
    },
    ApplicationLifecycleStatus.CLOSED: {
        ApplicationLifecycleStatus.INTERESTED  # Re-open or apply for new cycle
    }
}

class InvalidLifecycleTransitionError(Exception):
    """Raised when an illegal lifecycle transition is requested."""
    pass

# ── 2. Official URL Validation ────────────────────────────────────────────────

OFFICIAL_GOV_DOMAINS = (
    ".gov.in",
    ".nic.in",
    ".ac.in",
    ".edu.in",
    "myscheme.gov.in",
    "india.gov.in",
    "digitalindia.gov.in",
    "uidai.gov.in",
    "pmkisan.gov.in",
    "udyamregistration.gov.in",
    "mudra.org.in",
    "cgtmse.in",
    "pmjay.gov.in",
    "eshram.gov.in",
    "scholarships.gov.in"
)

def verify_official_gov_url(url: str) -> Dict[str, Any]:
    """
    Validates whether a URL points to an authentic government or statutory domain.
    Protects citizens from fraudulent phishing portals.
    """
    if not url:
        return {"is_official": False, "domain": "", "notice": "No application URL provided."}

    parsed = urlparse(url.strip())
    hostname = (parsed.hostname or "").lower()

    is_official = any(hostname.endswith(d) or hostname == d.lstrip(".") for d in OFFICIAL_GOV_DOMAINS)

    if is_official:
        return {
            "is_official": True,
            "domain": hostname,
            "notice": "Verified Official Government / Statutory Portal."
        }
    else:
        return {
            "is_official": False,
            "domain": hostname,
            "notice": "Caution: Domain does not end in standard .gov.in / official registry. Proceed with caution."
        }

# ── 3. Models ────────────────────────────────────────────────────────────────

class StatusHistoryEntry(BaseModel):
    timestamp: str
    from_status: str
    to_status: str
    notes: Optional[str] = None

class ApplicationTrackerItem(BaseModel):
    application_id: str
    session_id: str
    scheme_id: str
    scheme_name: str
    current_status: ApplicationLifecycleStatus
    official_portal_url: str
    is_official_url_verified: bool
    external_reference_number: Optional[str] = None
    created_at: str
    updated_at: str
    history: List[StatusHistoryEntry] = Field(default_factory=list)

class OfficialStep(BaseModel):
    step_number: int
    title: str
    instruction: str
    portal_action_type: str  # e.g., 'auth', 'form_fill', 'document_upload', 'payment', 'acknowledgment'
    estimated_minutes: int

class DocumentChecklistItem(BaseModel):
    document_type: str
    is_mandatory: bool
    stage: str
    user_status: str  # 'verified', 'uploaded', 'declared', 'missing'
    acceptable_formats: str
    guidance: str

class LocalReminder(BaseModel):
    reminder_id: str
    scheme_id: str
    title: str
    message: str
    trigger_days_from_now: int
    due_date: str
    priority: str  # 'high', 'medium', 'low'

class SafeAutofillDraft(BaseModel):
    scheme_id: str
    scheme_name: str
    mapped_fields: Dict[str, Any]
    missing_critical_fields: List[str]
    printable_checklist_markdown: str
    automated_submissions_prohibited: bool = True
    safety_notice: str

# ── 4. Checklist & Application Tracker Service ────────────────────────────────

class ApplicationChecklistService:
    def __init__(self, db: Session):
        self.db = db
        # In-memory storage for test/session runtime persistence if not in DB table
        self._trackers: Dict[str, ApplicationTrackerItem] = {}

    def create_application_tracker(
        self,
        session_id: str,
        scheme_id: str,
        scheme_name: Optional[str] = None,
        initial_status: ApplicationLifecycleStatus = ApplicationLifecycleStatus.INTERESTED
    ) -> ApplicationTrackerItem:
        """
        Initializes an application tracker entry for a citizen scheme.
        """
        # Retrieve official portal URL from SchemeVersion
        scheme = self.db.query(Scheme).filter_by(id=scheme_id).first()
        portal_url = ""
        resolved_name = scheme_name or (scheme.canonical_name if scheme else scheme_id)

        if scheme:
            sv = self.db.query(SchemeVersion).filter_by(scheme_id=scheme_id, status="published").order_by(SchemeVersion.version_number.desc()).first()
            if sv:
                portal_url = sv.application_url or sv.source_url or ""

        url_check = verify_official_gov_url(portal_url)
        now_str = datetime.now(timezone.utc).isoformat()
        app_id = str(uuid.uuid4())

        tracker = ApplicationTrackerItem(
            application_id=app_id,
            session_id=session_id,
            scheme_id=scheme_id,
            scheme_name=resolved_name,
            current_status=initial_status,
            official_portal_url=portal_url,
            is_official_url_verified=url_check["is_official"],
            created_at=now_str,
            updated_at=now_str,
            history=[
                StatusHistoryEntry(
                    timestamp=now_str,
                    from_status="NONE",
                    to_status=initial_status.value,
                    notes="Application journey initiated."
                )
            ]
        )
        self._trackers[app_id] = tracker
        return tracker

    def transition_status(
        self,
        application_id: str,
        new_status: ApplicationLifecycleStatus,
        notes: Optional[str] = None,
        external_ref_number: Optional[str] = None
    ) -> ApplicationTrackerItem:
        """
        Transitions application tracker status through the strict state machine.
        Raises InvalidLifecycleTransitionError if transition is illegal.
        """
        tracker = self._trackers.get(application_id)
        if not tracker:
            raise KeyError(f"Application tracker not found: {application_id}")

        curr = tracker.current_status
        allowed = ALLOWED_TRANSITIONS.get(curr, set())

        if new_status not in allowed:
            allowed_str = ", ".join(s.value for s in allowed) if allowed else "None"
            raise InvalidLifecycleTransitionError(
                f"Illegal lifecycle transition from '{curr.value}' to '{new_status.value}'. "
                f"Valid next states are: [{allowed_str}]."
            )

        now_str = datetime.now(timezone.utc).isoformat()
        tracker.history.append(
            StatusHistoryEntry(
                timestamp=now_str,
                from_status=curr.value,
                to_status=new_status.value,
                notes=notes
            )
        )
        tracker.current_status = new_status
        tracker.updated_at = now_str

        if external_ref_number:
            tracker.external_reference_number = external_ref_number

        return tracker

    def get_official_steps(self, scheme_id: str, version_number: int = 1) -> List[OfficialStep]:
        """
        Exposes standardized, versioned official steps for applying to this scheme.
        """
        return [
            OfficialStep(
                step_number=1,
                title="Verify Official Portal & Identity Authentication",
                instruction="Access the official portal (.gov.in) and authenticate using Aadhaar OTP / DigiLocker.",
                portal_action_type="auth",
                estimated_minutes=5
            ),
            OfficialStep(
                step_number=2,
                title="Profile & Demographic Verification",
                instruction="Confirm auto-populated demographic details (Name, DOB, Address, Social Category) match official documents.",
                portal_action_type="form_fill",
                estimated_minutes=10
            ),
            OfficialStep(
                step_number=3,
                title="Upload Document Proofs",
                instruction="Upload clear PDF/JPEG copies of required mandatory documents as listed in your checklist.",
                portal_action_type="document_upload",
                estimated_minutes=15
            ),
            OfficialStep(
                step_number=4,
                title="Bank Account Linking & DBT Mandate",
                instruction="Provide active Aadhaar-seeded bank account details (IFSC, Account Number) for direct benefit transfer.",
                portal_action_type="form_fill",
                estimated_minutes=5
            ),
            OfficialStep(
                step_number=5,
                title="Final Declaration, Submission & Acknowledgment Receipt",
                instruction="Review entered data, submit application, and save the generated 14-to-16 digit Acknowledgment Number.",
                portal_action_type="acknowledgment",
                estimated_minutes=5
            )
        ]

    def get_document_checklist(
        self,
        scheme_id: str,
        user_facts: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChecklistItem]:
        """
        Builds required document checklist cross-referencing DB requirements with citizen facts.
        """
        user_facts = user_facts or {}
        declared_docs = set([d.strip().lower() for d in (user_facts.get("documents.available") or "").split(",") if d.strip()])
        uploaded_docs = set([d.strip().lower() for d in (user_facts.get("documents.uploaded") or "").split(",") if d.strip()])
        verified_docs = set([d.strip().lower() for d in (user_facts.get("documents.verified") or "").split(",") if d.strip()])

        # Query DB DocumentRequirements
        scheme = self.db.query(Scheme).filter_by(id=scheme_id).first()
        sv = None
        if scheme:
            sv = self.db.query(SchemeVersion).filter_by(scheme_id=scheme_id, status="published").order_by(SchemeVersion.version_number.desc()).first()

        db_docs = sv.documents if sv and sv.documents else []

        checklist: List[DocumentChecklistItem] = []

        if db_docs:
            for d in db_docs:
                doc_type = d.document_type
                dt_lower = doc_type.lower()
                status = "missing"
                if any(dt_lower in v or v in dt_lower for v in verified_docs):
                    status = "verified"
                elif any(dt_lower in u or u in dt_lower for u in uploaded_docs):
                    status = "uploaded"
                elif any(dt_lower in dec or dec in dt_lower for dec in declared_docs):
                    status = "declared"

                checklist.append(
                    DocumentChecklistItem(
                        document_type=doc_type,
                        is_mandatory=d.is_mandatory,
                        stage=d.requirement_stage or "application_stage",
                        user_status=status,
                        acceptable_formats="PDF or JPEG under 2MB",
                        guidance=f"Must match name on Aadhaar. Alternatives: {d.alternatives or 'None'}"
                    )
                )
        else:
            # Standard baseline documents if scheme has no explicit DB document rows
            standard_docs = [
                ("Aadhaar Card / Official ID", True, "PDF/JPEG under 2MB", "Mandatory primary photo and address identity."),
                ("Bank Passbook / Cancelled Cheque", True, "PDF under 1MB", "Must show printed Name, Account No, and IFSC code."),
                ("Income / Caste Certificate", False, "PDF under 2MB", "Required if applying under affirmative action or subsidized category.")
            ]
            for doc_name, is_m, fmt, guide in standard_docs:
                dn_lower = doc_name.lower()
                status = "missing"
                if any(k in dn_lower for k in ["aadhaar", "id"]) and user_facts.get("person.has_aadhaar"):
                    status = "declared"
                elif "bank" in dn_lower and user_facts.get("bank.has_account"):
                    status = "declared"

                checklist.append(
                    DocumentChecklistItem(
                        document_type=doc_name,
                        is_mandatory=is_m,
                        stage="application_stage",
                        user_status=status,
                        acceptable_formats=fmt,
                        guidance=guide
                    )
                )

        return checklist

    def generate_local_reminders(
        self,
        application_id: str
    ) -> List[LocalReminder]:
        """
        Generates local event-driven reminders based on the application's current lifecycle stage.
        """
        tracker = self._trackers.get(application_id)
        if not tracker:
            return []

        now = datetime.now(timezone.utc)
        status = tracker.current_status
        reminders: List[LocalReminder] = []

        if status == ApplicationLifecycleStatus.SUBMITTED:
            due = now + timedelta(days=14)
            reminders.append(
                LocalReminder(
                    reminder_id=str(uuid.uuid4()),
                    scheme_id=tracker.scheme_id,
                    title="Follow Up on Departmental Document Verification",
                    message=(
                        f"Your application (Ref: {tracker.external_reference_number or 'Pending'}) "
                        "was submitted. Check official portal if field verification is scheduled."
                    ),
                    trigger_days_from_now=14,
                    due_date=due.strftime("%Y-%m-%d"),
                    priority="high"
                )
            )
        elif status == ApplicationLifecycleStatus.REDIRECTED_TO_OFFICIAL_PORTAL:
            due = now + timedelta(days=1)
            reminders.append(
                LocalReminder(
                    reminder_id=str(uuid.uuid4()),
                    scheme_id=tracker.scheme_id,
                    title="Complete Official Application Form",
                    message="You visited the official portal. Did you complete and submit your application?",
                    trigger_days_from_now=1,
                    due_date=due.strftime("%Y-%m-%d"),
                    priority="medium"
                )
            )
        elif status == ApplicationLifecycleStatus.UNDER_VERIFICATION:
            due = now + timedelta(days=7)
            reminders.append(
                LocalReminder(
                    reminder_id=str(uuid.uuid4()),
                    scheme_id=tracker.scheme_id,
                    title="Check Official Portal Status & Grievance Window",
                    message="Verification is underway. Log in to ensure no defect or document re-upload request was raised.",
                    trigger_days_from_now=7,
                    due_date=due.strftime("%Y-%m-%d"),
                    priority="high"
                )
            )
        elif status == ApplicationLifecycleStatus.APPROVED:
            due = now + timedelta(days=3)
            reminders.append(
                LocalReminder(
                    reminder_id=str(uuid.uuid4()),
                    scheme_id=tracker.scheme_id,
                    title="Verify Bank Account Credit Mandate",
                    message="Your application was approved! Check bank SMS for direct benefit transfer disbursal.",
                    trigger_days_from_now=3,
                    due_date=due.strftime("%Y-%m-%d"),
                    priority="medium"
                )
            )

        return reminders

    def generate_safe_offline_autofill_draft(
        self,
        scheme_id: str,
        user_facts: Dict[str, Any]
    ) -> SafeAutofillDraft:
        """
        Creates a structured draft application data mapping and printable checklist.
        Strictly prohibits automated third-party web submissions.
        """
        scheme = self.db.query(Scheme).filter_by(id=scheme_id).first()
        scheme_name = scheme.canonical_name if scheme else scheme_id

        # Map canonical facts to standard government application fields
        mapped_fields: Dict[str, Any] = {
            "Applicant Full Name": user_facts.get("person.name") or "Self Declared Applicant",
            "Date of Birth / Age": f"{user_facts.get('person.age', 'Not Specified')} Years",
            "Gender": str(user_facts.get("person.gender", "Not Specified")).capitalize(),
            "Social Category / Caste": str(user_facts.get("social.caste", "General")).upper(),
            "State of Residence": user_facts.get("location.state", "Not Specified"),
            "District": user_facts.get("location.district", "Not Specified"),
            "Area Type": str(user_facts.get("location.urban_rural", "Rural")).capitalize(),
            "Annual Household Income (INR)": f"Rs. {user_facts.get('income.annual', 0):,}" if user_facts.get('income.annual') else "Self Declared",
            "Occupation / Sector": str(user_facts.get("person.occupation", "General")).title(),
            "Has Aadhaar Card": "Yes" if user_facts.get("person.has_aadhaar", True) else "No",
            "Has Active Bank Account": "Yes" if user_facts.get("bank.has_account", True) else "No",
            "Disability Status": "Yes" if user_facts.get("health.has_disability") else "No"
        }

        missing_critical = []
        if not user_facts.get("location.state"):
            missing_critical.append("State of Residence")
        if not user_facts.get("person.age"):
            missing_critical.append("Age / Date of Birth")

        # Format printable markdown checklist
        md_lines = [
            f"# Application Preparation & Data Slip: {scheme_name}",
            "**Safety Guarantee**: *CivixAI does NOT submit forms automatically to third-party government portals. Use this printable draft to guide manual form filling or to take to a CSC center.*\n",
            "---",
            "## 1. Verified Profile Data for Form Entry\n"
        ]
        for k, v in mapped_fields.items():
            md_lines.append(f"- **{k}**: `{v}`")

        md_lines.append("\n## 2. Document Physical Checklist (Keep Ready)")
        docs = self.get_document_checklist(scheme_id, user_facts)
        for d in docs:
            check_box = "[x]" if d.user_status in ("verified", "uploaded", "declared") else "[ ]"
            mand_tag = "(Mandatory)" if d.is_mandatory else "(Optional)"
            md_lines.append(f"- {check_box} **{d.document_type}** {mand_tag} - *{d.guidance}*")

        md_lines.append("\n## 3. Post-Submission Reference")
        md_lines.append("- [ ] Official Application Ref Number: ________________________")
        md_lines.append("- [ ] Date of Online Submission: ________________________")
        md_lines.append("- [ ] Acknowledgment Receipt PDF Downloaded: [ ] Yes  [ ] No")

        printable_md = "\n".join(md_lines)

        return SafeAutofillDraft(
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            mapped_fields=mapped_fields,
            missing_critical_fields=missing_critical,
            printable_checklist_markdown=printable_md,
            automated_submissions_prohibited=True,
            safety_notice="CivixAI strictly guarantees zero unauthorized automated headless submissions to government websites. Your privacy and consent are preserved."
        )