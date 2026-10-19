"""
Questionnaire Question Ranker
Mathematically ranks unresolved candidate facts to select the single highest-impact,
lowest-friction, privacy-respecting question for the user's next step.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
from .catalogue import get_question_metadata
from .models import QuestionMetadata

W_SCHEMES = 1.0
W_MANDATORY = 2.0
W_PRIVACY = 3.0
W_EFFORT = 1.0

PRIVACY_PENALTY = {
    "normal": 0.0,
    "financial": 1.0,
    "sensitive": 2.0
}

EFFORT_PENALTY = {
    "boolean": 0.2,
    "radio": 0.2,
    "select": 0.5,
    "number": 1.0,
    "text": 1.5,
    "range": 1.0
}

class QuestionRanker:
    """
    Ranks unresolved facts by:
    1. Scheme coverage (how many active viable schemes depend on this fact)
    2. Gating impact (how many schemes use this as an unconditionally mandatory condition)
    3. Privacy minimization (delays sensitive/financial questions until necessary)
    4. User cognitive friction (prioritizes low-effort boolean/choice over text/numbers)
    """
    @staticmethod
    def calculate_fact_score(
        fact_key: str,
        affected_schemes_count: int,
        is_mandatory: bool,
        metadata: Optional[QuestionMetadata] = None
    ) -> Tuple[float, str]:
        if not metadata:
            metadata = get_question_metadata(fact_key)

        privacy_cost = PRIVACY_PENALTY.get(metadata.sensitivity, 0.0) if metadata else 0.0
        effort_cost = EFFORT_PENALTY.get(metadata.component_type, 1.0) if metadata else 1.0

        score = (
            (W_SCHEMES * affected_schemes_count)
            + (W_MANDATORY * (2.0 if is_mandatory else 0.0))
            - (W_PRIVACY * privacy_cost)
            - (W_EFFORT * effort_cost)
        )

        # Generate transparent explanation
        mand_text = "mandatory criteria" if is_mandatory else "alternate criteria"
        why_chosen = (
            f"Determines qualification for {affected_schemes_count} active schemes ({mand_text}) "
            f"while minimizing privacy and typing effort."
        )
        return score, why_chosen

    @classmethod
    def pick_next_best_fact(
        cls,
        unresolved_facts_by_scheme: Dict[str, Set[str]],
        mandatory_facts: Set[str],
        skipped_facts: Set[str],
        unknown_facts: Set[str]
    ) -> Optional[Tuple[str, str, int]]:
        """
        Returns (fact_key, why_chosen, affected_schemes_count) for the top-ranked fact.
        Excludes already answered, skipped, or unknown facts.
        """
        candidate_facts = set(unresolved_facts_by_scheme.keys()) - skipped_facts - unknown_facts
        if not candidate_facts:
            return None

        scored_candidates: List[Tuple[float, str, str, int]] = []
        for fact_key in candidate_facts:
            metadata = get_question_metadata(fact_key)
            if not metadata:
                continue

            affected_count = len(unresolved_facts_by_scheme[fact_key])
            is_mand = fact_key in mandatory_facts

            score, why_chosen = cls.calculate_fact_score(
                fact_key=fact_key,
                affected_schemes_count=affected_count,
                is_mandatory=is_mand,
                metadata=metadata
            )
            scored_candidates.append((score, fact_key, why_chosen, affected_count))

        if not scored_candidates:
            return None

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top = scored_candidates[0]
        return top[1], top[2], top[3]
