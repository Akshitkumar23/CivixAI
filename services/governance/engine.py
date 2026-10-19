"""
CIVIXAI — HUMAN GOVERNANCE & CERTIFICATION STATE MACHINE ENGINE
================================================================
Implements the strict, deterministic state machine, append-only governance
logging, reviewer authentication, and certification gates.

State Progression:
STAGED -> COMPILED -> VALIDATED -> REVIEW_REQUIRED -> HUMAN_REVIEW_IN_PROGRESS -> HUMAN_APPROVED -> CERTIFIED -> PUBLISHED
Alternative Branches:
REQUEST_CORRECTION | REJECTED | ESCALATED | WITHDRAWN | SUPERSEDED

Immutable Invariants:
1. REVIEW_REQUIRED cannot directly become CERTIFIED (must pass HUMAN_APPROVED).
2. Synthetic, simulated, bot, or automated reviewers are rejected with UnauthorizedReviewerError.
3. Decisions are strictly: APPROVE, REQUEST_CORRECTION, REJECT, ESCALATE, WITHDRAW.
4. APPROVE transitions to HUMAN_APPROVED, NOT ELIGIBILITY_READY.
5. RecommendationEngine remains 100% isolated (CandidateService = 27).
"""

import sys
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PACKETS_DIR = PROJECT_ROOT / 'data' / 'governance' / 'review_packets'
RECORDS_LOG_PATH = PROJECT_ROOT / 'data' / 'governance' / 'governance_records.jsonl'

ALLOWED_DECISIONS = {
    "APPROVE", "REQUEST_CORRECTION", "REJECT", "ESCALATE", "WITHDRAW"
}

ALLOWED_ROLES = {
    "CHIEF_POLICY_OFFICER",
    "LEGAL_COMPLIANCE_DIRECTOR",
    "STATUTORY_SCHEME_AUDITOR",
    "GOVERNANCE_BOARD_MEMBER"
}

PROHIBITED_REVIEWERS = {
    "test", "synthetic", "bot", "ai", "llm", "automated", "mock", "script", "auto", "system", "admin"
}

VALID_STATE_TRANSITIONS = {
    "STAGED": {"COMPILED"},
    "COMPILED": {"VALIDATED"},
    "VALIDATED": {"REVIEW_REQUIRED"},
    "REVIEW_REQUIRED": {"HUMAN_REVIEW_IN_PROGRESS"},
    "CORRECTED_PENDING_GOVERNANCE": {"HUMAN_REVIEW_IN_PROGRESS"},
    "HUMAN_REVIEW_IN_PROGRESS": {
        "HUMAN_APPROVED", "REQUEST_CORRECTION", "REJECTED", "ESCALATED", "WITHDRAWN"
    },
    "HUMAN_APPROVED": {"CERTIFIED"},
    "CERTIFIED": {"PUBLISHED"},
    "REQUEST_CORRECTION": {"REVIEW_REQUIRED", "CORRECTED_PENDING_GOVERNANCE"},
    "ESCALATED": {"REVIEW_REQUIRED", "REJECTED"},
    "REJECTED": set(),
    "WITHDRAWN": set(),
    "PUBLISHED": {"SUPERSEDED"}
}

class GovernanceError(Exception):
    """Base exception for governance protocol violations."""
    pass

class UnauthorizedReviewerError(GovernanceError):
    """Raised when reviewer identity is invalid, synthetic, or unauthorized."""
    pass

class InvalidStateTransitionError(GovernanceError):
    """Raised when state transition attempts to skip states or bypass human review."""
    pass

class InvalidDecisionError(GovernanceError):
    """Raised when an unapproved decision verb is passed."""
    pass

class CertificationGateError(GovernanceError):
    """Raised when certification prerequisites are not met."""
    pass


class GovernanceEngine:
    def __init__(self, packets_dir: Path = PACKETS_DIR, records_log: Path = RECORDS_LOG_PATH):
        self.packets_dir = packets_dir
        self.records_log = records_log
        self.records_log.parent.mkdir(parents=True, exist_ok=True)

    def load_packet(self, scheme_id: str) -> Dict[str, Any]:
        pkt_path = self.packets_dir / f"{scheme_id}.json"
        if not pkt_path.exists():
            raise FileNotFoundError(f"Review packet not found for scheme: {scheme_id}")
        with open(pkt_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_packet(self, scheme_id: str, packet: Dict[str, Any]):
        pkt_path = self.packets_dir / f"{scheme_id}.json"
        with open(pkt_path, 'w', encoding='utf-8') as f:
            json.dump(packet, f, indent=2)

    def validate_reviewer(self, reviewer_id: Optional[str], reviewer_role: Optional[str]):
        if not reviewer_id or not reviewer_id.strip():
            raise UnauthorizedReviewerError("Reviewer ID is mandatory.")
        
        rid_clean = reviewer_id.strip().lower()
        if any(bad in rid_clean for bad in PROHIBITED_REVIEWERS):
            raise UnauthorizedReviewerError(
                f"Synthetic, mock, or automated reviewer '{reviewer_id}' is strictly prohibited."
            )
        
        if not reviewer_role or reviewer_role.upper() not in ALLOWED_ROLES:
            raise UnauthorizedReviewerError(
                f"Role '{reviewer_role}' is unauthorized. Must be one of: {sorted(ALLOWED_ROLES)}"
            )

    def start_review(self, scheme_id: str, reviewer_id: str, reviewer_role: str) -> Dict[str, Any]:
        """Transitions scheme from REVIEW_REQUIRED / CORRECTED_PENDING_GOVERNANCE -> HUMAN_REVIEW_IN_PROGRESS."""
        self.validate_reviewer(reviewer_id, reviewer_role)
        packet = self.load_packet(scheme_id)
        current_state = packet.get("governance_status", "REVIEW_REQUIRED")

        if current_state not in ("REVIEW_REQUIRED", "CORRECTED_PENDING_GOVERNANCE"):
            raise InvalidStateTransitionError(
                f"Cannot start review from state '{current_state}'. Expected 'REVIEW_REQUIRED' or 'CORRECTED_PENDING_GOVERNANCE'."
            )

        new_state = "HUMAN_REVIEW_IN_PROGRESS"
        packet["governance_status"] = new_state
        self.save_packet(scheme_id, packet)

        self._append_record(
            scheme_id=scheme_id,
            scheme_version_id=packet["section_a_scheme_identity"].get("current_version", 1),
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            action="START_REVIEW",
            decision="IN_PROGRESS",
            previous_state=current_state,
            new_state=new_state,
            citation="Human Review Initiation",
            notes=f"Review initiated by authorized officer {reviewer_id}"
        )
        return packet

    def record_decision(
        self,
        scheme_id: str,
        decision: str,
        reviewer_id: str,
        reviewer_role: str,
        citation: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Executes a human governance decision.
        Allowed decisions: APPROVE, REQUEST_CORRECTION, REJECT, ESCALATE, WITHDRAW.
        """
        self.validate_reviewer(reviewer_id, reviewer_role)
        decision_upper = decision.upper().strip()
        if decision_upper not in ALLOWED_DECISIONS:
            raise InvalidDecisionError(
                f"Decision '{decision}' is not allowed. Must be one of: {sorted(ALLOWED_DECISIONS)}"
            )

        packet = self.load_packet(scheme_id)
        current_state = packet.get("governance_status", "REVIEW_REQUIRED")

        # Must be in review or auto-advance from review_required / corrected_pending_governance if reviewer is valid
        if current_state in ("REVIEW_REQUIRED", "CORRECTED_PENDING_GOVERNANCE"):
            current_state = "HUMAN_REVIEW_IN_PROGRESS"
            packet["governance_status"] = current_state

        if current_state != "HUMAN_REVIEW_IN_PROGRESS":
            raise InvalidStateTransitionError(
                f"Cannot apply decision from state '{current_state}'. Must be 'HUMAN_REVIEW_IN_PROGRESS'."
            )

        # Map decision to state
        if decision_upper == "APPROVE":
            new_state = "HUMAN_APPROVED"
        elif decision_upper == "REQUEST_CORRECTION":
            new_state = "REQUEST_CORRECTION"
        elif decision_upper == "REJECT":
            new_state = "REJECTED"
        elif decision_upper == "ESCALATE":
            new_state = "ESCALATED"
        elif decision_upper == "WITHDRAW":
            new_state = "WITHDRAWN"
        else:
            raise InvalidDecisionError(f"Unhandled decision: {decision_upper}")

        # Update decision section
        packet["governance_status"] = new_state
        packet["section_p_governance_decision"] = {
            "decision": decision_upper,
            "reviewer_id": reviewer_id,
            "reviewer_role": reviewer_role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "citation": citation,
            "reason": notes,
            "certified": False,  # APPROVE does NOT automatically certify!
            "eligibility_ready": False
        }

        self.save_packet(scheme_id, packet)

        self._append_record(
            scheme_id=scheme_id,
            scheme_version_id=packet["section_a_scheme_identity"].get("current_version", 1),
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            action="GOVERNANCE_DECISION",
            decision=decision_upper,
            previous_state=current_state,
            new_state=new_state,
            citation=citation,
            notes=notes
        )
        return packet

    def certify_scheme(self, scheme_id: str, reviewer_id: str, reviewer_role: str) -> Dict[str, Any]:
        """
        Applies the formal Certification Gate.
        Can ONLY be called if scheme is already HUMAN_APPROVED.
        """
        self.validate_reviewer(reviewer_id, reviewer_role)
        packet = self.load_packet(scheme_id)
        current_state = packet.get("governance_status")

        if current_state != "HUMAN_APPROVED":
            raise CertificationGateError(
                f"Scheme '{scheme_id}' cannot be certified from state '{current_state}'. Must be 'HUMAN_APPROVED'."
            )

        # Certification Gate Checklist
        dec_info = packet.get("section_p_governance_decision", {})
        if not dec_info.get("reviewer_id"):
            raise CertificationGateError("Human approval reviewer identity missing.")
        if len(packet["section_e_structured_criteria"]) < 1:
            raise CertificationGateError("Eligibility criteria missing.")
        if not packet["section_h_ast"] or not packet["section_h_ast"].get("conditions"):
            raise CertificationGateError("Rule AST is empty or invalid.")

        new_state = "CERTIFIED"
        packet["governance_status"] = new_state
        packet["section_p_governance_decision"]["certified"] = True

        self.save_packet(scheme_id, packet)

        self._append_record(
            scheme_id=scheme_id,
            scheme_version_id=packet["section_a_scheme_identity"].get("current_version", 1),
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            action="CERTIFY",
            decision="CERTIFIED",
            previous_state=current_state,
            new_state=new_state,
            citation="Statutory Certification Gate Passed",
            notes="Scheme certified under statutory compliance standards"
        )
        return packet

    def _append_record(
        self,
        scheme_id: str,
        scheme_version_id: int,
        reviewer_id: str,
        reviewer_role: str,
        action: str,
        decision: str,
        previous_state: str,
        new_state: str,
        citation: str,
        notes: str
    ):
        record = {
            "record_id": f"rec_{uuid.uuid4().hex[:12]}",
            "scheme_id": scheme_id,
            "scheme_version_id": scheme_version_id,
            "reviewer_id": reviewer_id,
            "reviewer_role": reviewer_role,
            "action": action,
            "decision": decision,
            "citation": citation,
            "evidence_anchor_ids": [f"anchor_{scheme_id}"],
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "previous_state": previous_state,
            "new_state": new_state
        }
        with open(self.records_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')
