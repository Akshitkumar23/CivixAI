"""
Questionnaire Orchestrator
Coordinates dynamic questionnaire generation, session state persistence,
answer submission, skip, prefer_not_to_say, unknown, answer editing,
household mode scoping, back navigation, and recommendation previews.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session

from services.core.database.models import ProfileSession, ProfileFact
from services.core.recommendations.candidate_service import CandidateService
from services.core.recommendations.engine import RecommendationEngine
from services.core.facts.registry import FACT_CATALOGUE, normalize_profile_to_facts
from services.core.facts.derivation import apply_deterministic_derivations

from .models import (
    QuestionMetadata, QuestionResponse, QuestionnaireProgress,
    QuestionnaireState, SubjectRelation, HouseholdMemberProfile
)
from .catalogue import get_question_metadata
from .dependency_service import QuestionDependencyService
from .question_ranker import QuestionRanker
from .progress import calculate_progress
from .session import QuestionnaireSessionManager, PREFER_NOT_TO_SAY_SENTINEL, resolve_scope

class QuestionnaireOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.candidate_service = CandidateService(db)
        self.session_manager = QuestionnaireSessionManager(db)

    def get_or_create_session(self, session_id: Optional[str] = None) -> ProfileSession:
        return self.session_manager.get_or_create_session(session_id)

    def get_session_data(
        self,
        session_id: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieves member-scoped facts and session state.
        Ensures household members' facts are never merged.
        """
        return self.session_manager.get_member_facts(
            session_id=session_id,
            subject_relation=subject_relation,
            member_index=member_index
        )

    def get_state(
        self,
        session_id: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> QuestionnaireState:
        data = self.get_session_data(session_id, subject_relation, member_index)
        # Apply deterministic derivations on the fly so derived facts are always coherent
        current_facts = apply_deterministic_derivations(data["facts"])
        skipped = data["skipped"]
        unknowns = data["unknowns"]
        prefer_not_to_say = data["prefer_not_to_say"]
        history = data["history"]

        # Run dependency analysis strictly across authoritative certified candidates
        candidates = self.candidate_service.get_candidates(certified_only=True, limit=200)
        dep_service = QuestionDependencyService(candidates)
        dep_res = dep_service.get_unresolved_dependencies(current_facts)

        unresolved_map = dep_res["unresolved_facts_by_scheme"]
        mandatory_facts = dep_res["mandatory_facts"]

        # Progress calculation
        progress = calculate_progress(
            answered_facts_count=len(data["facts"]),
            unresolved_relevant_facts=set(unresolved_map.keys()),
            eligible_schemes_count=len(dep_res["eligible_schemes"]),
            needs_info_schemes_count=len(dep_res["needs_info_schemes"])
        )

        # Check if completed (no remaining candidate facts)
        remaining_candidates = set(unresolved_map.keys()) - skipped - unknowns - prefer_not_to_say
        is_completed = len(remaining_candidates) == 0

        current_question_resp: Optional[QuestionResponse] = None
        if not is_completed:
            picked = QuestionRanker.pick_next_best_fact(
                unresolved_facts_by_scheme=unresolved_map,
                mandatory_facts=mandatory_facts,
                skipped_facts=skipped | prefer_not_to_say,
                unknown_facts=unknowns
            )
            if picked:
                fact_key, why_chosen, affected_count = picked
                metadata = get_question_metadata(fact_key)
                if metadata:
                    current_question_resp = QuestionResponse(
                        session_id=session_id,
                        fact_key=fact_key,
                        question=metadata,
                        why_asked=why_chosen,
                        affected_schemes_count=affected_count,
                        progress=progress,
                        can_go_back=len(history) > 0,
                        is_completed=False,
                        subject_relation=subject_relation, # type: ignore
                        member_index=member_index
                    )

        if not current_question_resp:
            is_completed = True
            if not data["session"].completed_at:
                data["session"].completed_at = datetime.now(timezone.utc)
                self.db.commit()

        members = self.session_manager.list_household_members(session_id)

        return QuestionnaireState(
            session_id=session_id,
            is_completed=is_completed,
            subject_relation=subject_relation, # type: ignore
            member_index=member_index,
            current_question=current_question_resp,
            answered_facts=current_facts,
            skipped_facts=list(skipped),
            unknown_facts=list(unknowns),
            prefer_not_to_say_facts=list(prefer_not_to_say),
            history=history,
            progress=progress,
            household_members=members
        )

    def answer_question(
        self,
        session_id: str,
        fact_key: str,
        value: Any,
        scope: str = "applicant",
        subject_relation: str = "myself",
        member_index: int = 0,
        source: str = "self_declared"
    ) -> QuestionnaireState:
        # If caller passed non-default scope, map to subject_relation
        if scope and scope not in ("applicant", "myself") and subject_relation == "myself":
            subject_relation = scope

        if value == "prefer_not_to_say":
            return self.prefer_not_to_say(
                session_id=session_id,
                fact_key=fact_key,
                subject_relation=subject_relation,
                member_index=member_index
            )

        self.session_manager.save_fact(
            session_id=session_id,
            fact_key=fact_key,
            value=value,
            subject_relation=subject_relation,
            member_index=member_index,
            source=source
        )
        return self.get_state(session_id, subject_relation=subject_relation, member_index=member_index)

    def edit_answer(
        self,
        session_id: str,
        fact_key: str,
        value: Any,
        subject_relation: str = "myself",
        member_index: int = 0,
        source: str = "user_edited"
    ) -> QuestionnaireState:
        """
        Explicit answer editing endpoint. Modifies an existing fact in-place and triggers recalculation.
        """
        if value == "prefer_not_to_say":
            return self.prefer_not_to_say(
                session_id=session_id,
                fact_key=fact_key,
                subject_relation=subject_relation,
                member_index=member_index
            )

        self.session_manager.edit_fact(
            session_id=session_id,
            fact_key=fact_key,
            new_value=value,
            subject_relation=subject_relation,
            member_index=member_index,
            source=source
        )
        return self.get_state(session_id, subject_relation=subject_relation, member_index=member_index)

    def skip_question(
        self,
        session_id: str,
        fact_key: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> QuestionnaireState:
        """
        Skips a question without defaulting it to False.
        For sensitive demographic questions, preserves viability as NEEDS_INFO.
        """
        self.session_manager.skip_fact(
            session_id=session_id,
            fact_key=fact_key,
            subject_relation=subject_relation,
            member_index=member_index
        )
        return self.get_state(session_id, subject_relation=subject_relation, member_index=member_index)

    def prefer_not_to_say(
        self,
        session_id: str,
        fact_key: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> QuestionnaireState:
        """
        Explicit privacy choice for sensitive demographic/social category questions.
        Guarantees that affected schemes become NEEDS_INFO rather than excluded.
        """
        self.session_manager.prefer_not_to_say_fact(
            session_id=session_id,
            fact_key=fact_key,
            subject_relation=subject_relation,
            member_index=member_index
        )
        return self.get_state(session_id, subject_relation=subject_relation, member_index=member_index)

    def mark_unknown(
        self,
        session_id: str,
        fact_key: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> QuestionnaireState:
        self.session_manager.mark_unknown_fact(
            session_id=session_id,
            fact_key=fact_key,
            subject_relation=subject_relation,
            member_index=member_index
        )
        return self.get_state(session_id, subject_relation=subject_relation, member_index=member_index)

    def go_back(
        self,
        session_id: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> QuestionnaireState:
        self.session_manager.remove_last_history_fact(
            session_id=session_id,
            subject_relation=subject_relation,
            member_index=member_index
        )
        return self.get_state(session_id, subject_relation=subject_relation, member_index=member_index)

    def recalculate(
        self,
        session_id: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> QuestionnaireState:
        """
        Explicit recalculation endpoint: refreshes dependency analysis and ranking
        based on current facts for the targeted member.
        """
        return self.get_state(session_id, subject_relation=subject_relation, member_index=member_index)

    def get_recommendation_preview(
        self,
        session_id: str,
        subject_relation: str = "myself",
        member_index: int = 0
    ) -> Dict[str, Any]:
        """
        Computes deterministic eligibility preview for current session facts of the targeted member.
        Guarantees sensitive demographic skipped/prefer_not_to_say facts keep schemes in NEEDS_INFO.
        """
        data = self.get_session_data(session_id, subject_relation=subject_relation, member_index=member_index)
        facts = data["facts"]
        skipped_and_pns = data["skipped"] | data["prefer_not_to_say"]

        engine = RecommendationEngine(self.db)
        res = engine.evaluate_profile(facts=facts, session_id=session_id, top_k=50)

        # Audit schemes: ensure any scheme whose unresolved facts are in skipped_and_pns
        # remains in NEEDS_INFO and is annotated with transparent governance notice
        for item in res.get("ranked_schemes", []):
            missing = set(item.get("missing_facts", []))
            sensitive_missing = missing & skipped_and_pns
            if sensitive_missing:
                if item["eligibility_status"] == "NOT_ELIGIBLE":
                    item["eligibility_status"] = "NEEDS_INFO"
                    item["eligible"] = False
                item["governance_notice"] = (
                    f"Demographic detail ({', '.join(sensitive_missing)}) was skipped or preferred not to say. "
                    "Scheme remains in NEEDS_INFO pending official documentation or verification."
                )

        res["eligible_count"] = res.get("total_eligible", 0)
        res["subject_relation"] = subject_relation
        res["member_index"] = member_index
        return res