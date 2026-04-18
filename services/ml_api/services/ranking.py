from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel


class RankingResult(BaseModel):
    """Result model for scheme ranking calculations."""
    scheme_id: str
    rank_score: float
    blended_prob: float
    benefit_score: float
    doc_penalty: float
    pop_boost: float
    directive_boost: float


# ── Ranking Constants ────────────────────────────────────────────────────────
# Multi-objective optimization weights
MISSING_CRITERIA_PENALTY = 0.05
MISSING_CRITERIA_PENALTY_INELIGIBLE = 0.08
DOCUMENT_EFFORT_PENALTY_PER_DOC = 0.02
ELIGIBLE_BONUS_MULTIPLIER = 1.4
MIN_BASE_SCORE = 0.40
MAX_SCORE = 1.0
MIN_INELIGIBLE_SCORE = 0.10
MAX_INELIGIBLE_SCORE = 0.99


class RankingService:
    def __init__(self, directives: Optional[Dict[str, Any]] = None):
        self.directives = directives or {"active_directives": []}

    def score_scheme(self, 
                    user: Any, 
                    scheme: Dict[str, Any], 
                    eligibility: Any, 
                    ml_benefit_score: float) -> float:
        """
        Multi-objective Optimization: Max(Benefit) + Min(Effort) + Max(Confidence) + Max(Popularity)
        
        Returns a normalized score between 0 and ~1.5 (before capping).
        """
        # 1. Blended Score Logic
        blended_prob = self._calculate_blended_probability(eligibility)

        # 2. Effort / Documentation Penalty
        effort_penalty = self._calculate_effort_penalty(scheme)

        # 3. RL / Popularity Boost
        pop_multiplier = self._calculate_popularity_multiplier(scheme)

        # 4. AI Strategic Directives (from data/master/policy_directives.json)
        directive_boost = self._calculate_directive_boost(user, scheme)

        # 5. Synthesis - Protection against any NaN inputs
        m_benefit = float(ml_benefit_score) if not np.isnan(ml_benefit_score) else 0.5
        m_prob = float(blended_prob) if not np.isnan(blended_prob) else 0.5

        final_score = m_prob * m_benefit
        final_score *= (1.1 - min(0.3, effort_penalty)) 
        final_score *= pop_multiplier
        final_score *= directive_boost
        
        if eligibility.is_eligible:
            final_score *= ELIGIBLE_BONUS_MULTIPLIER
            
        return final_score

    def _calculate_blended_probability(self, eligibility: Any) -> float:
        """Calculate blended probability based on eligibility status."""
        if eligibility.is_eligible and not eligibility.hard_reject:
            penalty = len(eligibility.missing_criteria) * MISSING_CRITERIA_PENALTY
            base_score = max(MIN_BASE_SCORE, eligibility.match_score) - penalty
            return min(MAX_SCORE, float(base_score + (eligibility.ml_confidence * 0.10)))
        else:
            base = 0.50 if eligibility.path_to_eligibility else (0.20 + (eligibility.match_score * 0.4))
            blended_prob = float(base + (eligibility.ml_confidence * 0.3) - (len(eligibility.missing_criteria) * MISSING_CRITERIA_PENALTY_INELIGIBLE))
            return max(MIN_INELIGIBLE_SCORE, min(MAX_INELIGIBLE_SCORE, blended_prob))

    def _calculate_effort_penalty(self, scheme: Dict[str, Any]) -> float:
        """Calculate documentation effort penalty."""
        doc_list = str(scheme.get("documents_required", "")).split(",")
        doc_count = len([d for d in doc_list if d.strip()])
        return doc_count * DOCUMENT_EFFORT_PENALTY_PER_DOC

    def _calculate_popularity_multiplier(self, scheme: Dict[str, Any]) -> float:
        """Calculate popularity-based multiplier."""
        raw_pop = scheme.get("popularity_score", 5.0)
        try:
            pop_score = float(raw_pop)
            if np.isnan(pop_score):
                pop_score = 5.0
        except (ValueError, TypeError):
            pop_score = 5.0
        return 0.8 + (pop_score / 25.0)

    def _calculate_directive_boost(self, user: Any, scheme: Dict[str, Any]) -> float:
        """Calculate strategic directive boost based on policy directives."""
        directive_boost = 1.0
        for ad in self.directives.get("active_directives", []):
            state_match = self._check_state_match(user, ad)
            if state_match:
                keywords = [k.lower() for k in ad.get("keywords", [])]
                scheme_text = self._build_scheme_text(scheme)
                if any(k in scheme_text for k in keywords):
                    directive_boost = max(directive_boost, float(ad.get("boost_factor", 1.0)))
        return directive_boost

    def _check_state_match(self, user: Any, directive: Dict[str, Any]) -> bool:
        """Check if user's state matches directive target states."""
        target_states = [s.lower() for s in directive.get("target_states", [])]
        if "all" in target_states:
            return True
        if user.state:
            return user.state.lower() in target_states
        return False

    def _build_scheme_text(self, scheme: Dict[str, Any]) -> str:
        """Build searchable text from scheme metadata."""
        return f"{scheme.get('scheme_name', '')} {scheme.get('tags', '')} {scheme.get('scheme_category', '')}".lower()
