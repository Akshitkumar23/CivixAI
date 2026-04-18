"""
OutputAgent — Stage 5 (Final) of the CivixAI Agent Pipeline
============================================================
Responsibilities:
  - Collect the fully-enriched scheme list from all previous agents
  - Format and structure the final JSON response for the frontend
  - Build the `summary` counts (total loans / insurance / schemes)
  - Populate `why_not_eligible` information (schemes that were hard-rejected
    with explanations — passed in as an optional parameter)
  - Ensure all required frontend fields are present:
      scheme_id, scheme_name, match_score, why, benefits,
      eligibility_summary, apply_link, description, type,
      documents_required, tldr_bullets, how_to_apply

The OutputAgent is purely a formatting stage — NO external calls are made.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Fields the frontend expects for each scheme card
REQUIRED_SCHEME_KEYS = {
    "scheme_id", "scheme_name", "type", "match_score", "why",
    "description", "benefits", "eligibility_summary", "apply_link",
    "documents_required", "tldr_bullets", "how_to_apply",
    "ministry", "level", "category",
}


class OutputAgent:
    """
    Agent 5 — Final Response Formatter

    Usage:
        agent    = OutputAgent()
        response = agent.format(
            clean_profile,
            eligible_schemes,        # from ReasoningAgent
            rejected_reasons=[],     # optional: hard-rejected scheme reasons
            confidence_score=0.72,
        )
    """

    # ──────────────────────────────────────────────────────────────────────────
    # Public entry-point
    # ──────────────────────────────────────────────────────────────────────────
    def format(
        self,
        clean_profile: Dict[str, Any],
        eligible_schemes: List[Dict[str, Any]],
        rejected_reasons: Optional[List[Dict[str, Any]]] = None,
        confidence_score: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Build the final frontend-ready response dict.

        Parameters
        ----------
        clean_profile    : dict — validated user profile
        eligible_schemes : list — fully enriched schemes from all agents
        rejected_reasons : list[dict], optional — {scheme_name, reason}
        confidence_score : float — mean ML probability from EligibilityEngine

        Returns
        -------
        dict matching the RecommendationResponse / EligibilityResponse contract.
        """
        formatted_schemes = [
            self._format_scheme(s) for s in eligible_schemes
        ]

        # ── Summary counts ────────────────────────────────────────────────────
        summary = {
            "total":     len(formatted_schemes),
            "loans":     sum(1 for s in formatted_schemes if s["type"] == "loan"),
            "insurance": sum(1 for s in formatted_schemes if s["type"] == "insurance"),
            "schemes":   sum(1 for s in formatted_schemes if s["type"] == "scheme"),
        }

        # ── Why-not-eligible ──────────────────────────────────────────────────
        why_not = self._build_why_not(rejected_reasons)

        # ── Profile echo (helps frontend display) ─────────────────────────────
        profile_echo = {
            "age":        clean_profile.get("age"),
            "occupation": clean_profile.get("occupation"),
            "state":      clean_profile.get("state"),
            "caste":      clean_profile.get("caste"),
        }

        # ── Knowledge graph (related schemes by category) ─────────────────────
        knowledge_graph = self._build_knowledge_graph(formatted_schemes)

        response = {
            # Primary payload
            "recommended":       formatted_schemes,

            # Aliases for backward-compat with existing frontend API usage
            "ranked_schemes":    [self._to_ranked_entry(s) for s in formatted_schemes],
            "eligible_schemes":  [self._to_eligibility_entry(s) for s in formatted_schemes],

            # Metadata
            "summary":           summary,
            "why_not_eligible":  why_not,
            "confidence_score":  round(confidence_score, 4),
            "profile":           profile_echo,
            "knowledge_graph":   knowledge_graph,

            # Agent pipeline metadata
            "_pipeline": {
                "stages": [
                    "InputAgent",
                    "EligibilityEngine",
                    "RetrievalAgent",
                    "ReasoningAgent",
                    "OutputAgent",
                ],
                "total_eligible": len(formatted_schemes),
            },
        }

        logger.info(
            "[OutputAgent] ✅ Response built: %d schemes (loans=%d, insurance=%d, schemes=%d).",
            summary["total"], summary["loans"], summary["insurance"], summary["schemes"],
        )
        return response

    # ──────────────────────────────────────────────────────────────────────────
    # Per-scheme formatting
    # ──────────────────────────────────────────────────────────────────────────

    def _format_scheme(self, s: Dict[str, Any]) -> Dict[str, Any]:
        """Build a canonical, frontend-ready scheme dict."""
        return {
            # Identity
            "scheme_id":           self._clean(s.get("scheme_id")),
            "scheme_name":         self._clean(s.get("scheme_name")),
            "type":                self._clean(s.get("type"), fallback="scheme"),

            # Scores
            "match_score":         round(float(s.get("confidence", s.get("match_score", 0.5))), 4),
            "rank_score":          round(float(s.get("rank_score", 0.5)), 4),

            # Explanation fields (set by ReasoningAgent)
            "why":                 self._clean(s.get("why"),
                                               fallback="Your profile matches this scheme's eligibility criteria."),
            "description":         self._clean(s.get("description"),
                                               fallback=s.get("benefit_description", "")),
            "eligibility_summary": self._clean(s.get("eligibility_summary"),
                                               fallback="Eligible based on your profile."),

            # Benefits
            "benefits":            [self._clean(s.get("benefit_amount", "Benefit varies by criteria"))],
            "benefit_amount":      self._clean(s.get("benefit_amount")),

            # Application
            "apply_link":          self._clean(s.get("url") or s.get("source_url"), fallback=""),
            "documents_required":  s.get("documents_required", []),

            # Metadata
            "category":            self._clean(s.get("category"), fallback="General"),
            "ministry":            self._clean(s.get("ministry"), fallback="Government of India"),
            "level":               self._clean(s.get("level"), fallback="Central"),

            # Reasoning trail
            "reasons":             s.get("reasons", []),
            "missing_criteria":    s.get("missing_criteria", []),
            "path_to_eligibility": s.get("path_to_eligibility", []),

            # Structured helpers (set by ReasoningAgent)
            "tldr_bullets":        s.get("tldr_bullets", []),
            "how_to_apply":        s.get("how_to_apply", []),
        }

    def _to_ranked_entry(self, s: Dict[str, Any]) -> Dict[str, Any]:
        """Map to the legacy ranked_schemes response format."""
        return {
            "scheme_id":          s["scheme_id"],
            "name":               s["scheme_name"],
            "type":               s["type"],
            "eligible":           True,
            "confidence":         s["match_score"],
            "benefit_score":      s.get("rank_score", 0.5),
            "rank_score":         s["rank_score"],
            "category":           s["category"],
            "description":        s["description"],
            "ministry":           s["ministry"],
            "level":              s["level"],
            "url":                s["apply_link"],
            "documents":          s["documents_required"],
            "reasons":            s["reasons"],
            "missing":            s["missing_criteria"],
            "benefit_amount":     s["benefit_amount"],
            "path_to_eligibility": s["path_to_eligibility"],
        }

    def _to_eligibility_entry(self, s: Dict[str, Any]) -> Dict[str, Any]:
        """Map to the legacy eligible_schemes format (used by /api/check-eligibility)."""
        return {
            "scheme_id":    s["scheme_id"],
            "scheme_name":  s["scheme_name"],
            "eligible":     True,
            "confidence":   s["match_score"],
            "type":         s["type"],
            "description":  s["description"],
            "benefit_amount": s["benefit_amount"],
            "category":     s["category"],
            "ministry":     s["ministry"],
            "level":        s["level"],
            "url":          s["apply_link"],
            "source_url":   s["apply_link"],
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Knowledge graph
    # ──────────────────────────────────────────────────────────────────────────

    def _build_knowledge_graph(
        self, schemes: List[Dict[str, Any]], max_schemes: int = 20
    ) -> List[Dict[str, Any]]:
        """Link schemes to related schemes in the same category."""
        graph = []
        for s in schemes[:max_schemes]:
            related = [
                {"id": r["scheme_id"], "name": r["scheme_name"]}
                for r in schemes
                if r["scheme_id"] != s["scheme_id"] and r["category"] == s["category"]
            ][:3]
            graph.append({"scheme_id": s["scheme_id"], "related": related})
        return graph

    # ──────────────────────────────────────────────────────────────────────────
    # Why-not-eligible
    # ──────────────────────────────────────────────────────────────────────────

    def _build_why_not(
        self, rejected_reasons: Optional[List[Dict[str, Any]]]
    ) -> List[str]:
        if not rejected_reasons:
            return []
        messages = []
        for item in rejected_reasons[:10]:  # cap at 10
            name   = item.get("scheme_name", "Unknown scheme")
            reason = item.get("reason", "Does not meet eligibility criteria")
            messages.append(f"Not eligible for '{name}': {reason}")
        return messages

    # ──────────────────────────────────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _clean(val: Any, fallback: str = "") -> str:
        if val is None:
            return fallback
        s = str(val).strip()
        return s if s.lower() not in ("nan", "none", "") else fallback
