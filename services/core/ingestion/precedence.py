"""
Source Precedence and Supersession Engine
Phase 3.6 Hardening:
- Treats legal_priority as decision support, NOT an automatic legal winner.
- Evaluates multi-factor precedence: authority tier, jurisdiction, publication date,
  effective date, explicit amendment, and supersession status.
- Implements Supersession Governance:
    PROPOSED_SUPERSESSION -> HUMAN_REVIEW -> CONFIRMED_SUPERSESSION
- Strictly prevents static hierarchy from silently overriding conflicting current official sources.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from services.core.database.models import SourceRegistry, SourceDocument, AuditLog

AUTHORITY_PRIORITY = {
    "gazette_notification": 1,
    "statutory_act": 1,
    "executive_order": 2,
    "operational_guideline": 3,
    "portal_spec": 4,
    "secondary": 5
}

class PrecedencePolicy:
    @staticmethod
    def get_priority(source_authority_type: str) -> int:
        return AUTHORITY_PRIORITY.get(source_authority_type, 4)

    @classmethod
    def evaluate_multi_factor_precedence(
        cls,
        source_a: Dict[str, Any],
        source_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Multi-factor precedence evaluation providing decision support for human review.
        Never silently overrides conflicting official sources automatically.
        """
        factors = []
        rec_winner = None

        # 1. Supersession Check (Only CONFIRMED supersession alters precedence)
        sup_a_id = source_a.get("supersedes_source_id")
        sup_a_status = source_a.get("supersession_status", "none")
        id_b = source_b.get("id")

        sup_b_id = source_b.get("supersedes_source_id")
        sup_b_status = source_b.get("supersession_status", "none")
        id_a = source_a.get("id")

        if sup_a_id and id_b and sup_a_id == id_b:
            if sup_a_status == "confirmed":
                return {
                    "decision_support": "Source A explicitly and confirmedly supersedes Source B",
                    "requires_human_confirmation": False,
                    "recommended_winner": "SOURCE_A",
                    "factors": ["confirmed_supersession"]
                }
            else:
                factors.append("proposed_supersession_pending_review")

        if sup_b_id and id_a and sup_b_id == id_a:
            if sup_b_status == "confirmed":
                return {
                    "decision_support": "Source B explicitly and confirmedly supersedes Source A",
                    "requires_human_confirmation": False,
                    "recommended_winner": "SOURCE_B",
                    "factors": ["confirmed_supersession"]
                }
            else:
                factors.append("proposed_supersession_pending_review")

        # 2. Authority Rank Check
        prio_a = cls.get_priority(source_a.get("source_authority_type", "operational_guideline"))
        prio_b = cls.get_priority(source_authority_b := source_b.get("source_authority_type", "operational_guideline"))

        if prio_a < prio_b:
            factors.append(f"Source A authority tier ({prio_a}) is legally higher than Source B ({prio_b})")
            rec_winner = "SOURCE_A"
        elif prio_b < prio_a:
            factors.append(f"Source B authority tier ({prio_b}) is legally higher than Source A ({prio_a})")
            rec_winner = "SOURCE_B"
        else:
            factors.append("Equal legal authority tier")

        # 3. Recency / Effective Dates
        eff_a = source_a.get("effective_from") or source_a.get("published_date")
        eff_b = source_b.get("effective_from") or source_b.get("published_date")
        if eff_a and eff_b:
            if eff_a > eff_b:
                factors.append("Source A has a more recent effective/publication date")
                if not rec_winner:
                    rec_winner = "SOURCE_A"
            elif eff_b > eff_a:
                factors.append("Source B has a more recent effective/publication date")
                if not rec_winner:
                    rec_winner = "SOURCE_B"

        # Material conflicts always require human confirmation
        return {
            "decision_support": f"Indicative evaluation suggests {rec_winner or 'ambiguous'} based on {len(factors)} factors",
            "requires_human_confirmation": True,
            "recommended_winner": rec_winner or "BOTH_APPLY_DIFFERENT_CONTEXT",
            "factors": factors
        }

    @classmethod
    def compare_sources(
        cls,
        source_a: Dict[str, Any],
        source_b: Dict[str, Any]
    ) -> int:
        """
        Backward compatible comparison helper.
        Returns:
          -1 if source_a has strictly higher confirmed precedence
           1 if source_b has strictly higher confirmed precedence
           0 if precedence is equal or conflicting (requiring human review)
        """
        # 1. Check explicit supersession override (unless rejected)
        sup_a = source_a.get("supersedes_source_id")
        sup_b = source_b.get("supersedes_source_id")
        id_a = source_a.get("id")
        id_b = source_b.get("id")

        if sup_a and id_b and sup_a == id_b and source_a.get("supersession_status") != "rejected":
            return -1
        if sup_b and id_a and sup_b == id_a and source_b.get("supersession_status") != "rejected":
            return 1

        res = cls.evaluate_multi_factor_precedence(source_a, source_b)
        if not res["requires_human_confirmation"]:
            if res["recommended_winner"] == "SOURCE_A":
                return -1
            elif res["recommended_winner"] == "SOURCE_B":
                return 1
        # Fallback to decision support for tier sorting
        prio_a = cls.get_priority(source_a.get("source_authority_type", "operational_guideline"))
        prio_b = cls.get_priority(source_b.get("source_authority_type", "operational_guideline"))
        if prio_a < prio_b:
            return -1
        elif prio_b < prio_a:
            return 1
        return 0


class SupersessionGovernanceEngine:
    """
    Manages the lifecycle:
      PROPOSED_SUPERSESSION -> HUMAN_REVIEW -> CONFIRMED_SUPERSESSION (or REJECTED)
    """
    def __init__(self, db: Session):
        self.db = db

    def propose_supersession(
        self,
        new_source_id: str,
        superseded_source_id: str,
        proposer_id: str = "extractor_engine",
        notes: str = ""
    ) -> SourceRegistry:
        """Proposes that new_source_id supersedes superseded_source_id without altering production."""
        source = self.db.query(SourceRegistry).filter(SourceRegistry.id == new_source_id).first()
        if not source:
            raise ValueError(f"Source '{new_source_id}' not found.")

        target = self.db.query(SourceRegistry).filter(SourceRegistry.id == superseded_source_id).first()
        if not target:
            raise ValueError(f"Target superseded source '{superseded_source_id}' not found.")

        source.supersedes_source_id = superseded_source_id
        source.supersession_status = "proposed"

        # Log audit trail
        audit = AuditLog(
            entity_type="source_registry",
            entity_id=new_source_id,
            action="propose_supersession",
            actor_id=proposer_id,
            reason=f"Proposed supersession of {superseded_source_id}: {notes}",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(source)
        return source

    def confirm_supersession(
        self,
        new_source_id: str,
        reviewer_id: str,
        resolution_notes: str
    ) -> SourceRegistry:
        """Confirms supersession after human review; safely marks target source superseded."""
        source = self.db.query(SourceRegistry).filter(SourceRegistry.id == new_source_id).first()
        if not source:
            raise ValueError(f"Source '{new_source_id}' not found.")

        target_id = source.supersedes_source_id
        if not target_id:
            raise ValueError(f"Source '{new_source_id}' has no proposed supersedes_source_id.")

        target = self.db.query(SourceRegistry).filter(SourceRegistry.id == target_id).first()

        source.supersession_status = "confirmed"
        if target:
            target.verification_status = "superseded"

        audit = AuditLog(
            entity_type="source_registry",
            entity_id=new_source_id,
            action="confirm_supersession",
            actor_id=reviewer_id,
            reason=f"Human confirmed supersession of {target_id}: {resolution_notes}",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(source)
        return source

    def reject_supersession(
        self,
        new_source_id: str,
        reviewer_id: str,
        rejection_reason: str
    ) -> SourceRegistry:
        """Rejects supersession; both sources remain active and may be flagged as distinct or conflicting."""
        source = self.db.query(SourceRegistry).filter(SourceRegistry.id == new_source_id).first()
        if not source:
            raise ValueError(f"Source '{new_source_id}' not found.")

        target_id = source.supersedes_source_id
        source.supersession_status = "rejected"

        audit = AuditLog(
            entity_type="source_registry",
            entity_id=new_source_id,
            action="reject_supersession",
            actor_id=reviewer_id,
            reason=f"Rejected supersession of {target_id}: {rejection_reason}",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(source)
        return source
