"""
AgentPipeline — Orchestrator for the CivixAI 5-Agent Pipeline
==============================================================
Sequences the five agents in strict linear order (no recursion):

    1. InputAgent         → validate & clean user input
    2. EligibilityEngine  → hard rules + ML scoring
    3. RetrievalAgent     → contextual scheme retrieval
    4. ReasoningAgent     → personalised LLM explanations
    5. OutputAgent        → format final JSON

The pipeline is completely stateless per-request (thread-safe).
All agent instances are constructed once at app startup (in FastAPI startup
event) and reused across requests.

Usage (from main.py):
    pipeline = AgentPipeline(
        eligibility_service=...,
        ranking_service=...,
        benefit_service=...,
        ml_model=...,
        benefit_model=...,
        schema=...,
        build_features_fn=...,
        normalize_fn=...,
        schemes_df=...,
        genai_service=...,
    )
    result = pipeline.run(raw_user_profile)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from .input_agent        import InputAgent, InputValidationError
from .eligibility_engine import EligibilityEngine
from .retrieval_agent    import RetrievalAgent
from .reasoning_agent    import ReasoningAgent
from .output_agent       import OutputAgent

logger = logging.getLogger(__name__)


class AgentPipeline:
    """
    Linear 5-agent pipeline for CivixAI scheme recommendations.

    Parameters
    ----------
    eligibility_service : EligibilityService
    ranking_service     : RankingService
    benefit_service     : BenefitService
    ml_model            : CatBoost eligibility model
    benefit_model       : CatBoost benefit model
    schema              : dict — feature schema
    build_features_fn   : callable (profile_obj, schemes_df) → pd.DataFrame
    normalize_fn        : callable (df, schema) → pd.DataFrame
    schemes_df          : pd.DataFrame — master scheme table
    genai_service       : PersonalizedGenAIService
    faiss_index_path    : str, optional — path to FAISS index for RetrievalAgent
    top_k               : int — max schemes to return (default 30)
    """

    def __init__(
        self,
        eligibility_service,
        ranking_service,
        benefit_service,
        ml_model,
        benefit_model,
        schema: Dict[str, Any],
        build_features_fn,
        normalize_fn,
        schemes_df: pd.DataFrame,
        genai_service,
        faiss_index_path: Optional[str] = None,
        top_k: int = 30,
    ):
        # ── Stage 1 ───────────────────────────────────────────────────────────
        self.input_agent = InputAgent()

        # ── Stage 2 ───────────────────────────────────────────────────────────
        self.eligibility_engine = EligibilityEngine(
            eligibility_service=eligibility_service,
            ranking_service=ranking_service,
            benefit_service=benefit_service,
            ml_model=ml_model,
            benefit_model=benefit_model,
            schema=schema,
            build_features_fn=build_features_fn,
            normalize_fn=normalize_fn,
            schemes_df=schemes_df,
            top_k=top_k,
        )

        # ── Stage 3 ───────────────────────────────────────────────────────────
        # Build scheme texts for retrieval from the master CSV
        scheme_texts = (
            schemes_df["scheme_name"].fillna("").astype(str)
            + " "
            + schemes_df.get("benefit_description", pd.Series([""] * len(schemes_df))).fillna("").astype(str)
        ).tolist()
        scheme_ids = schemes_df["scheme_id"].astype(str).tolist()

        self.retrieval_agent = RetrievalAgent(
            all_scheme_texts=scheme_texts,
            all_scheme_ids=scheme_ids,
            index_path=faiss_index_path,
            top_k=min(top_k * 2, 50),
        )

        # ── Stage 4 ───────────────────────────────────────────────────────────
        self.reasoning_agent = ReasoningAgent(genai_service)

        # ── Stage 5 ───────────────────────────────────────────────────────────
        self.output_agent = OutputAgent()

        logger.info("[AgentPipeline] ✅ All 5 agents initialised (top_k=%d).", top_k)

    # ──────────────────────────────────────────────────────────────────────────
    # Main pipeline entry-point
    # ──────────────────────────────────────────────────────────────────────────
    def run(self, raw_user_input: Any) -> Dict[str, Any]:
        """
        Execute the full linear pipeline for one user request.

        Parameters
        ----------
        raw_user_input : Pydantic model | dict
            The raw user profile from the FastAPI endpoint.

        Returns
        -------
        dict — the final JSON-ready response for the frontend.

        Raises
        ------
        InputValidationError  — if required fields are missing / invalid.
        """
        t_start = time.perf_counter()
        timings: Dict[str, float] = {}

        # ── Stage 1: Input Validation ──────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            clean_profile = self.input_agent.process(raw_user_input)
        except InputValidationError as e:
            logger.error("[AgentPipeline] Stage 1 FAILED: %s", e)
            raise
        timings["input_agent"] = round(time.perf_counter() - t0, 4)
        logger.debug("[AgentPipeline] Stage 1 (InputAgent) done in %.3fs", timings["input_agent"])

        # ── Stage 2: Eligibility + Ranking ────────────────────────────────────
        t0 = time.perf_counter()
        el_result = self.eligibility_engine.run(clean_profile)
        eligible_schemes    = el_result["eligible_schemes"]
        confidence_score    = el_result["confidence_score"]
        timings["eligibility_engine"] = round(time.perf_counter() - t0, 4)
        logger.debug(
            "[AgentPipeline] Stage 2 (EligibilityEngine) done in %.3fs — %d eligible.",
            timings["eligibility_engine"], len(eligible_schemes),
        )

        # ── Stage 3: Retrieval ─────────────────────────────────────────────────
        t0 = time.perf_counter()
        eligible_schemes = self.retrieval_agent.retrieve(clean_profile, eligible_schemes)
        timings["retrieval_agent"] = round(time.perf_counter() - t0, 4)
        logger.debug("[AgentPipeline] Stage 3 (RetrievalAgent) done in %.3fs", timings["retrieval_agent"])

        # ── Stage 4: Reasoning (GenAI) ─────────────────────────────────────────
        t0 = time.perf_counter()
        eligible_schemes = self.reasoning_agent.explain(clean_profile, eligible_schemes)
        timings["reasoning_agent"] = round(time.perf_counter() - t0, 4)
        logger.debug("[AgentPipeline] Stage 4 (ReasoningAgent) done in %.3fs", timings["reasoning_agent"])

        # ── Stage 5: Output Formatting ─────────────────────────────────────────
        t0 = time.perf_counter()
        response = self.output_agent.format(
            clean_profile=clean_profile,
            eligible_schemes=eligible_schemes,
            rejected_reasons=None,     # TODO: collect rejected reasons from Stage 2
            confidence_score=confidence_score,
        )
        timings["output_agent"] = round(time.perf_counter() - t0, 4)

        total_time = round(time.perf_counter() - t_start, 4)
        response["_timings"] = {**timings, "total": total_time}

        logger.info(
            "[AgentPipeline] ✅ Pipeline complete in %.3fs — %d schemes returned.",
            total_time, len(eligible_schemes),
        )
        return response

    # ──────────────────────────────────────────────────────────────────────────
    # Convenience: run only up to eligibility (for /api/check-eligibility)
    # ──────────────────────────────────────────────────────────────────────────
    def run_eligibility_only(self, raw_user_input: Any) -> Dict[str, Any]:
        """
        Runs only Stages 1–2 (validate + eligibility) and returns the
        EligibilityResponse-compatible dict.  Used by /api/check-eligibility.
        """
        clean_profile = self.input_agent.process(raw_user_input)
        el_result     = self.eligibility_engine.run(clean_profile)
        schemes       = el_result["eligible_schemes"]

        # Legacy response format expected by /api/check-eligibility
        eligible_schemes_out = []
        eligibility_reasoning = []
        missing_criteria      = []

        for s in schemes:
            eligible_schemes_out.append({
                "scheme_id":     s.get("scheme_id"),
                "scheme_name":   s.get("scheme_name"),
                "eligible":      True,
                "confidence":    s.get("confidence", 0.5),
                "type":          s.get("type", "scheme"),
                "description":   s.get("benefit_description", ""),
                "benefit_amount":s.get("benefit_amount", ""),
                "category":      s.get("category", "General"),
                "ministry":      s.get("ministry", ""),
                "level":         s.get("level", ""),
                "url":           s.get("url", ""),
                "source_url":    s.get("source_url", ""),
            })
            eligibility_reasoning.append({
                "scheme_id":          s.get("scheme_id"),
                "reasons":            s.get("reasons", []),
                "path_to_eligibility":s.get("path_to_eligibility", []),
                "eligible_by_rules":  not s.get("hard_reject", False),
            })
            mc = s.get("missing_criteria", [])
            missing_criteria.append(
                {"scheme_id": s.get("scheme_id"), "missing": mc} if mc else {}
            )

        return {
            "eligible_schemes":      eligible_schemes_out,
            "eligibility_reasoning": eligibility_reasoning,
            "missing_criteria":      [m for m in missing_criteria if m],
            "confidence_score":      el_result["confidence_score"],
        }
