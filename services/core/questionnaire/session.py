"""
Questionnaire Session Manager
Handles household member scoping, distinct consent tracking, explicit answer editing,
privacy-preserving skip / prefer_not_to_say semantics, and state recalculation.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from services.core.database.models import ProfileSession, ProfileFact
from services.core.facts.registry import normalize_profile_to_facts
from services.core.facts.derivation import get_dependent_derived_facts
from .models import HouseholdMemberProfile, SubjectRelation

# Recognized relations and scopes
VALID_SUBJECT_RELATIONS: Tuple[str, ...] = (
    "myself",
    "parent",
    "child",
    "spouse",
    "other_household_member",
)

PREFER_NOT_TO_SAY_SENTINEL = "__PREFER_NOT_TO_SAY__"

def resolve_scope(subject_relation: str) -> str:
    """Normalizes subject_relation to database scope name."""
    rel = (subject_relation or "myself").lower().strip()
    if rel in ("myself", "applicant"):
        return "applicant"
    return rel

class QuestionnaireSessionManager:
    """
    Encapsulates persistence and scoping logic for questionnaire sessions.
    Guarantees strict data isolation between household members.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_session(self, session_id: Optional[str] = None) -> ProfileSession:
        if session_id:
            session_obj = self.db.query(ProfileSession).filter_by(id=session_id).first()
            if session_obj:
                return session_obj

        new_id = session_id or str(uuid.uuid4())
        session_obj = ProfileSession(id=new_id, is_anonymous=True)
        self.db.add(session_obj)
        self.db.commit()
        return session_obj

    def record_consent(
        self,
        session_id: str,
        subject_relation: str = "myself",
        member_index: int = 0,
        consent_given: bool = True,
        consent_type: str = "self_declaration"
    ) -> Dict[str, Any]:
        """
        Records or updates explicit consent for a household member profile.
        """
        scope = resolve_scope(subject_relation)
        consent_key = f"_consent.{scope}.{member_index}"
        now = datetime.now(timezone.utc)
        payload = {
            "consent_given": consent_given,
            "consent_type": consent_type,
            "consented_at": now.isoformat(),
            "subject_relation": subject_relation,
            "member_index": member_index
        }

        existing = self.db.query(ProfileFact).filter_by(
            session_id=session_id, fact_key=consent_key
        ).first()

        if existing:
            existing.fact_value = json.dumps(payload)
            existing.updated_at = now
        else:
            self.db.add(ProfileFact(
                id=str(uuid.uuid4()),
                session_id=session_id,
                fact_key=consent_key,
                fact_value=json.dumps(payload),
                is_skipped=False,
                is_unknown=False,
                source="consent_declaration",
                scope=scope,
                member_index=member_index,
                answered_at=now,
                updated_at=now
            ))
        self.db.commit()
        return payload

    def list_household_members(self, session_id: str) -> List[HouseholdMemberProfile]:
        """
        Lists all active household profiles registered in this session with consent state.
        Always includes 'myself' (primary applicant).
        """
        rows = self.db.query(ProfileFact.scope, ProfileFact.member_index).filter_by(
            session_id=session_id
        ).distinct().all()

        members_map: Dict[Tuple[str, int], Dict[str, Any]] = {
            ("applicant", 0): {
                "subject_relation": "myself",
                "member_index": 0,
                "display_name": "Primary Applicant",
                "consent_given": True,
                "consent_type": "self_declaration",
                "consented_at": None,
                "answered_count": 0
            }
        }

        consent_facts = self.db.query(ProfileFact).filter(
            ProfileFact.session_id == session_id,
            ProfileFact.fact_key.like("_consent.%")
        ).all()

        for cf in consent_facts:
            try:
                data = json.loads(cf.fact_value)
                sc = resolve_scope(data.get("subject_relation", "myself"))
                idx = int(data.get("member_index", 0))
                rel = data.get("subject_relation", "myself")
                members_map[(sc, idx)] = {
                    "subject_relation": rel,
                    "member_index": idx,
                    "display_name": f"{rel.replace('_', ' ').title()} #{idx}" if idx > 0 else rel.title(),
                    "consent_given": data.get("consent_given", True),
                    "consent_type": data.get("consent_type", "representative_declaration"),
                    "consented_at": data.get("consented_at"),
                    "answered_count": 0
                }
            except Exception:
                pass

        for sc, idx in rows:
            if not sc:
                sc = "applicant"
            idx = idx or 0
            if (sc, idx) not in members_map:
                rel = "myself" if sc in ("applicant", "myself") else sc
                members_map[(sc, idx)] = {
                    "subject_relation": rel,
                    "member_index": idx,
                    "display_name": f"{rel.replace('_', ' ').title()} #{idx}" if idx > 0 else rel.title(),
                    "consent_given": True,
                    "consent_type": "implicit_addition",
                    "consented_at": None,
                    "answered_count": 0
                }

        for (sc, idx), meta in members_map.items():
            filter_scopes = ["applicant", "myself"] if sc in ("applicant", "myself") else [sc]
            cnt = self.db.query(ProfileFact).filter(
                ProfileFact.session_id == session_id,
                ProfileFact.scope.in_(filter_scopes),
                ProfileFact.member_index == idx,
                ~ProfileFact.fact_key.like("_consent.%"),
                ProfileFact.is_skipped == False,
                ProfileFact.is_unknown == False
            ).count()
            meta["answered_count"] = cnt

        profiles = [HouseholdMemberProfile(**data) for data in members_map.values()]
        profiles.sort(key=lambda p: (0 if p.subject_relation == "myself" else 1, p.member_index))
        return profiles

    def get_member_facts(
        self,
        session_id: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieves scoped facts for a specific household member.
        Guarantees that a parent's or child's facts are NEVER mixed into applicant facts.
        """
        session_obj = self.get_or_create_session(session_id)
        scope = resolve_scope(subject_relation)
        filter_scopes = ["applicant", "myself"] if scope == "applicant" else [scope]

        query = self.db.query(ProfileFact).filter(
            ProfileFact.session_id == session_id,
            ProfileFact.scope.in_(filter_scopes),
            ProfileFact.member_index == member_index,
            ~ProfileFact.fact_key.like("_consent.%")
        )

        sorted_facts = sorted(
            query.all(),
            key=lambda x: x.answered_at or x.created_at or datetime.min
        )

        facts: Dict[str, Any] = {}
        skipped: Set[str] = set()
        unknowns: Set[str] = set()
        prefer_not_to_say: Set[str] = set()
        history: List[str] = []

        for f in sorted_facts:
            history.append(f.fact_key)
            if f.is_skipped:
                skipped.add(f.fact_key)
                try:
                    raw_val = json.loads(f.fact_value)
                    if raw_val == PREFER_NOT_TO_SAY_SENTINEL:
                        prefer_not_to_say.add(f.fact_key)
                except Exception:
                    pass
            elif f.is_unknown:
                unknowns.add(f.fact_key)
            else:
                try:
                    val = json.loads(f.fact_value)
                    if val == PREFER_NOT_TO_SAY_SENTINEL:
                        prefer_not_to_say.add(f.fact_key)
                        skipped.add(f.fact_key)
                    else:
                        facts[f.fact_key] = val
                except Exception:
                    facts[f.fact_key] = f.fact_value

        return {
            "session": session_obj,
            "facts": facts,
            "skipped": skipped,
            "unknowns": unknowns,
            "prefer_not_to_say": prefer_not_to_say,
            "history": history,
            "subject_relation": subject_relation,
            "member_index": member_index
        }

    def save_fact(
        self,
        session_id: str,
        fact_key: str,
        value: Any,
        subject_relation: str = "myself",
        member_index: int = 0,
        is_skipped: bool = False,
        is_unknown: bool = False,
        is_prefer_not_to_say: bool = False,
        source: str = "self_declared"
    ) -> ProfileFact:
        session_obj = self.get_or_create_session(session_id)
        scope = resolve_scope(subject_relation)
        filter_scopes = ["applicant", "myself"] if scope == "applicant" else [scope]

        existing = self.db.query(ProfileFact).filter(
            ProfileFact.session_id == session_id,
            ProfileFact.fact_key == fact_key,
            ProfileFact.scope.in_(filter_scopes),
            ProfileFact.member_index == member_index
        ).first()

        now = datetime.now(timezone.utc)
        if is_prefer_not_to_say:
            final_val = PREFER_NOT_TO_SAY_SENTINEL
            is_skipped = True
            is_unknown = False
        elif is_skipped or is_unknown:
            final_val = None
        else:
            normalized = normalize_profile_to_facts({fact_key: value})
            final_val = normalized.get(fact_key, value)

        if existing:
            existing.fact_value = json.dumps(final_val)
            existing.is_skipped = is_skipped
            existing.is_unknown = is_unknown
            existing.source = source
            existing.updated_at = now
            existing.answered_at = now
            fact_record = existing
        else:
            fact_record = ProfileFact(
                id=str(uuid.uuid4()),
                session_id=session_id,
                fact_key=fact_key,
                fact_value=json.dumps(final_val),
                is_skipped=is_skipped,
                is_unknown=is_unknown,
                source=source,
                scope=scope,
                member_index=member_index,
                answered_at=now,
                updated_at=now
            )
            self.db.add(fact_record)

        session_obj.updated_at = now
        self.db.commit()
        return fact_record

    def edit_fact(
        self,
        session_id: str,
        fact_key: str,
        new_value: Any,
        subject_relation: str = "myself",
        member_index: int = 0,
        source: str = "user_edited"
    ) -> ProfileFact:
        # Invalidate any dependent derived facts in session storage
        dep_facts = get_dependent_derived_facts(fact_key)
        if dep_facts:
            scope = resolve_scope(subject_relation)
            filter_scopes = ["applicant", "myself"] if scope == "applicant" else [scope]
            self.db.query(ProfileFact).filter(
                ProfileFact.session_id == session_id,
                ProfileFact.fact_key.in_(dep_facts),
                ProfileFact.scope.in_(filter_scopes),
                ProfileFact.member_index == member_index
            ).delete(synchronize_session=False)
            self.db.commit()

        return self.save_fact(
            session_id=session_id,
            fact_key=fact_key,
            value=new_value,
            subject_relation=subject_relation,
            member_index=member_index,
            is_skipped=False,
            is_unknown=False,
            is_prefer_not_to_say=False,
            source=source
        )

    def skip_fact(
        self,
        session_id: str,
        fact_key: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> ProfileFact:
        return self.save_fact(
            session_id=session_id,
            fact_key=fact_key,
            value=None,
            subject_relation=subject_relation,
            member_index=member_index,
            is_skipped=True,
            is_unknown=False,
            is_prefer_not_to_say=False
        )

    def prefer_not_to_say_fact(
        self,
        session_id: str,
        fact_key: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> ProfileFact:
        return self.save_fact(
            session_id=session_id,
            fact_key=fact_key,
            value=PREFER_NOT_TO_SAY_SENTINEL,
            subject_relation=subject_relation,
            member_index=member_index,
            is_skipped=True,
            is_unknown=False,
            is_prefer_not_to_say=True,
            source="privacy_prefer_not_to_say"
        )

    def mark_unknown_fact(
        self,
        session_id: str,
        fact_key: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> ProfileFact:
        return self.save_fact(
            session_id=session_id,
            fact_key=fact_key,
            value=None,
            subject_relation=subject_relation,
            member_index=member_index,
            is_skipped=False,
            is_unknown=True,
            is_prefer_not_to_say=False
        )

    def remove_last_history_fact(
        self,
        session_id: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> Optional[str]:
        data = self.get_member_facts(session_id, subject_relation, member_index)
        history = data["history"]
        if not history:
            return None

        last_fact = history[-1]
        scope = resolve_scope(subject_relation)
        filter_scopes = ["applicant", "myself"] if scope == "applicant" else [scope]

        self.db.query(ProfileFact).filter(
            ProfileFact.session_id == session_id,
            ProfileFact.fact_key == last_fact,
            ProfileFact.scope.in_(filter_scopes),
            ProfileFact.member_index == member_index
        ).delete(synchronize_session=False)

        dep_facts = get_dependent_derived_facts(last_fact)
        if dep_facts:
            self.db.query(ProfileFact).filter(
                ProfileFact.session_id == session_id,
                ProfileFact.fact_key.in_(dep_facts),
                ProfileFact.scope.in_(filter_scopes),
                ProfileFact.member_index == member_index
            ).delete(synchronize_session=False)

        self.db.commit()
        return last_fact