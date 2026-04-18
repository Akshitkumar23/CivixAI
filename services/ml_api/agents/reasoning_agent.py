"""
ReasoningAgent — Stage 4 of the CivixAI Agent Pipeline
=======================================================
Responsibilities:
  - For each eligible scheme, generate a personalized, human-readable explanation
    of WHY the user qualifies and what benefit it provides.
  - Uses the retrieved_context from RetrievalAgent as grounding information.
  - Wraps the existing PersonalizedGenAIService (Gemini) with graceful fallback
    to the rich rule-based description builder.
  - Adds structured output fields:
      • description      — personalized 2-3 sentence explanation
      • why              — key reasons the user qualifies (from eligibility rules)
      • eligibility_summary — a concise one-liner
      • tldr_bullets     — 3 action-oriented bullet points
      • how_to_apply     — 3-step application guide

This agent is the ONLY stage that interacts with an LLM (Gemini or another).
All other agents are deterministic or ML-based.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ReasoningAgent:
    """
    Agent 4 — Personalized Explanation & Reasoning

    Dependencies:
        genai_service : PersonalizedGenAIService

    Usage:
        agent   = ReasoningAgent(genai_service)
        schemes = agent.explain(clean_profile, eligible_schemes_with_context)
        # Each scheme dict now has: description, why, eligibility_summary,
        #   tldr_bullets, how_to_apply
    """

    def __init__(self, genai_service):
        self.genai = genai_service

    # ──────────────────────────────────────────────────────────────────────────
    # Public entry-point
    # ──────────────────────────────────────────────────────────────────────────
    def explain(
        self,
        clean_profile: Dict[str, Any],
        eligible_schemes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized reasoning for each eligible scheme.

        Parameters
        ----------
        clean_profile    : dict — validated user profile from InputAgent
        eligible_schemes : list — schemes with `retrieved_context` from RetrievalAgent

        Returns
        -------
        Same list, each scheme now has explanation fields populated.
        """
        if not eligible_schemes:
            return eligible_schemes

        # Build a compact user summary for prompt use (no LLM needed here)
        user_summary = self._build_user_summary(clean_profile)

        for scheme in eligible_schemes:
            scheme_raw = scheme.get("_scheme_raw", scheme)  # prefer raw CSV row

            # 1. Personalized description (Gemini or data-driven fallback)
            scheme["description"] = self.genai.generate_live_description(
                clean_profile,
                scheme_raw,
                scheme.get("rank_score", 0.5),
            )

            # 2. Why field — derive from eligibility reasons + retrieved context
            scheme["why"] = self._build_why(scheme, clean_profile)

            # 3. Eligibility summary — concise one-liner
            scheme["eligibility_summary"] = self._build_eligibility_summary(
                scheme, clean_profile
            )

            # 4. TL;DR bullets  (already handled by GenAI service)
            scheme["tldr_bullets"] = self.genai.generate_tldr(scheme_raw)

            # 5. How-to-apply steps (already handled by GenAI service)
            scheme["how_to_apply"] = self.genai.generate_application_steps(scheme_raw)

        logger.info(
            "[ReasoningAgent] ✅ Generated explanations for %d schemes.",
            len(eligible_schemes),
        )
        return eligible_schemes

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _build_user_summary(self, profile: Dict[str, Any]) -> str:
        age    = profile.get("age", "")
        occ    = str(profile.get("occupation", "citizen")).capitalize()
        state  = profile.get("state", "India")
        income = profile.get("annualIncome", 0)
        caste  = str(profile.get("caste", "")).upper()
        return (
            f"{age}-year-old {occ} from {state} "
            f"(Annual Income: ₹{income:,}, Category: {caste or 'General'})"
        )

    def _build_why(self, scheme: Dict[str, Any], profile: Dict[str, Any]) -> str:
        """
        Construct a detailed 'why you qualify' string.
        Combines eligibility rule reasons + retrieved context snippet.
        """
        reasons: List[str] = list(scheme.get("reasons", []))
        context : str       = scheme.get("retrieved_context", "")

        # Filter out empty/generic strings
        reasons = [r for r in reasons if r and "satisfies all" not in r.lower()]

        # Take top 3 reasons
        reason_text = " ".join(reasons[:3]) if reasons else ""

        # Optionally append a sentence from the retrieved context
        ctx_snippet = ""
        if context and len(context) > 40:
            # Take first meaningful sentence from context
            first_sentence = context.split(".")[0].strip()
            if first_sentence and first_sentence not in reason_text:
                ctx_snippet = first_sentence + "."

        why_parts = [p for p in [reason_text, ctx_snippet] if p]
        return " ".join(why_parts) or "Your profile matches the core eligibility criteria for this scheme."

    def _build_eligibility_summary(
        self, scheme: Dict[str, Any], profile: Dict[str, Any]
    ) -> str:
        """One-liner eligibility summary."""
        occ    = str(profile.get("occupation", "citizen")).capitalize()
        caste  = str(profile.get("caste", "")).upper()
        state  = profile.get("state", "India")
        income = profile.get("annualIncome", 0)
        b_type = scheme.get("type", "scheme")

        type_label = {
            "loan":      "loan scheme",
            "insurance": "insurance scheme",
            "scheme":    "government scheme",
        }.get(b_type, "scheme")

        income_str = f"income ₹{income:,}/yr" if income else ""
        parts = [
            f"{occ} from {state}",
            income_str,
            f"{caste} category" if caste else "",
        ]
        subject = ", ".join(p for p in parts if p)
        return f"Eligible as a {subject} for this {type_label}."
