"""
EligibilityEngine — Stage 2 of the CivixAI Agent Pipeline
==========================================================
Responsibilities:
  - Runs hard deterministic rule-filters (pre-filter gate) via EligibilityService
  - Applies ML model scoring (CatBoost) to all schemes that pass hard rules
  - Applies RankingService to produce a final blended rank_score
  - Determines benefit_type (loan / insurance / scheme) via keyword heuristics
  - Returns only eligible, ranked schemes (sorted by rank_score desc)

This agent wraps the existing EligibilityService + RankingService so they
are orchestrated in a single, clean stage.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Benefit-type keyword heuristics ──────────────────────────────────────────
LOAN_KEYWORDS = [
    "loan", "credit", "mudra", "interest subvention",
    "rin", "kcc", "vidya lakshmi",
]
INSURANCE_KEYWORDS = [
    "jeevan jyoti bima", "suraksha bima yojana", "pmjjby", "pmsby",
    "life insurance", "term insurance", "health insurance", "fasal bima",
    "crop insurance", "aam aadmi bima", "pradhan mantri bima",
]


def _detect_benefit_type(scheme: Dict[str, Any]) -> str:
    """Heuristic: determine if a scheme is a loan, insurance or general scheme."""
    b_type = str(scheme.get("benefit_type", "scheme")).lower()

    # Trust the CSV value if it's explicitly set
    if b_type in ["loan", "insurance"]:
        return b_type

    combined = (
        str(scheme.get("scheme_name", "")).lower()
        + " "
        + str(scheme.get("benefit_description", "")).lower()
    )
    if any(kw in combined for kw in LOAN_KEYWORDS):
        return "loan"
    if any(kw in combined for kw in INSURANCE_KEYWORDS):
        return "insurance"
    return "scheme"


class EligibilityEngine:
    """
    Agent 2 — Eligibility Checking & ML Ranking

    Dependencies (injected at construction):
        eligibility_service : EligibilityService  (hard rules + rule-scoring)
        ranking_service     : RankingService       (multi-objective ranking)
        ml_model            : CatBoost model       (predict_proba)
        benefit_model       : CatBoost model       (predict)
        schemas             : dict                 (feature schema)
        build_features_fn   : callable             (rows → feature DataFrame)
        normalize_fn        : callable             (DataFrame → normalised DataFrame)
        schemes_df          : pd.DataFrame         (master scheme table)

    Usage:
        engine = EligibilityEngine(...)
        result = engine.run(clean_profile_dict)
        # result = {
        #   "eligible_schemes": [...],
        #   "total_considered": int,
        #   "total_eligible": int,
        # }
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
        top_k: int = 30,
    ):
        self.eligibility_service = eligibility_service
        self.ranking_service     = ranking_service
        self.benefit_service     = benefit_service
        self.ml_model            = ml_model
        self.benefit_model       = benefit_model
        self.schema              = schema
        self.build_features_fn   = build_features_fn
        self.normalize_fn        = normalize_fn
        self.schemes_df          = schemes_df
        self.top_k               = top_k

    # ──────────────────────────────────────────────────────────────────────────
    # Public entry-point
    # ──────────────────────────────────────────────────────────────────────────
    def run(self, clean_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full eligibility + ranking pipeline for one user profile.

        Parameters
        ----------
        clean_profile : dict
            Validated user profile from InputAgent.

        Returns
        -------
        dict
            {
                "eligible_schemes"  : List[dict],  # ranked, enriched scheme entries
                "total_considered"  : int,
                "total_eligible"    : int,
                "confidence_score"  : float,       # mean ML probability
            }
        """
        # 1. Build feature matrix (user × each scheme row)
        profile_obj = _DictProxy(clean_profile)  # lightweight duck-typed proxy
        feature_df  = self.build_features_fn(profile_obj, self.schemes_df)
        norm_df     = self.normalize_fn(feature_df, self.schema)

        # 2. ML inference — get eligibility probabilities + benefit scores
        from catboost import Pool
        cat_features  = list(self.schema.get("cat_features_eligibility", []))
        text_features = self.schema.get("text_features", ["benefit_description", "scheme_name"])
        if not text_features:
            text_features = ["benefit_description", "scheme_name"]

        pool = Pool(
            data=norm_df,
            cat_features=[c for c in cat_features if c in norm_df.columns],
            text_features=[c for c in text_features if c in norm_df.columns],
        )

        el_probs     = self.ml_model.predict_proba(pool)[:, 1]    # shape (N,)
        ben_scores   = self.benefit_model.predict(pool)           # shape (N,)

        total_considered = len(self.schemes_df)

        # 3. Hard pre-filter  +  per-scheme rule scoring  +  ML ranking
        eligible_schemes: List[Dict[str, Any]] = []

        for prob_idx, (_, row) in enumerate(self.schemes_df.iterrows()):
            scheme_dict = row.to_dict()

            # ── Gate A: Hard rule pre-filter ──────────────────────────────
            passes, rejection_reason = self.eligibility_service._passes_basic_filters(
                profile_obj, scheme_dict
            )
            if not passes:
                continue

            # ── Gate B: Full eligibility scoring (rules + ML) ─────────────
            el_result = self.eligibility_service.check_eligibility(
                profile_obj, scheme_dict, float(el_probs[prob_idx])
            )
            if not el_result.is_eligible:
                continue

            # ── Scoring: multi-objective rank ──────────────────────────────
            rank_score = self.ranking_service.score_scheme(
                profile_obj, scheme_dict, el_result, float(ben_scores[prob_idx])
            )

            # ── Benefit info ───────────────────────────────────────────────
            ben_est  = self.benefit_service.estimate_benefit(scheme_dict)
            b_type   = _detect_benefit_type(scheme_dict)
            confidence = (
                float(el_probs[prob_idx])
                if float(el_probs[prob_idx]) > 0.5
                else max(float(el_probs[prob_idx]), el_result.match_score)
            )

            entry: Dict[str, Any] = {
                # Identification
                "scheme_id":           scheme_dict.get("scheme_id"),
                "scheme_name":         scheme_dict.get("scheme_name", scheme_dict.get("scheme_id")),
                "type":                b_type,

                # Scores (used by RetrievalAgent & OutputAgent)
                "confidence":          confidence,
                "rank_score":          rank_score,
                "benefit_score":       float(ben_scores[prob_idx]),
                "match_score":         el_result.match_score,

                # Metadata
                "category":            scheme_dict.get("scheme_category", "General"),
                "ministry":            scheme_dict.get("ministry", "Government of India"),
                "level":               scheme_dict.get("scheme_level", "Central"),
                "url":                 scheme_dict.get("application_url", ""),
                "source_url":          scheme_dict.get("source_url", ""),
                "benefit_amount":      ben_est["summary"],
                "benefit_description": str(scheme_dict.get("benefit_description", "")),

                # Eligibility reasoning (passed to ReasoningAgent)
                "eligible":            True,
                "reasons":             el_result.reasons,
                "missing_criteria":    el_result.missing_criteria,
                "path_to_eligibility": el_result.path_to_eligibility,
                "hard_reject":         el_result.hard_reject,

                # Documents
                "documents_required":  [
                    d.strip()
                    for d in str(scheme_dict.get("documents_required", "")).split(",")
                    if d.strip()
                ],

                # Raw scheme dict (needed by ReasoningAgent)
                "_scheme_raw":         scheme_dict,
            }
            eligible_schemes.append(entry)

        # 4. Sort by rank_score desc, then surface loans/insurance first
        eligible_schemes.sort(key=lambda x: x["rank_score"], reverse=True)

        # 5. Enforce diversity: loans + insurance bubble up
        priority    = [s for s in eligible_schemes if s["type"] in ("loan", "insurance")]
        general     = [s for s in eligible_schemes if s["type"] not in ("loan", "insurance")]
        final_ranked = (priority + general)
        final_ranked.sort(key=lambda x: x["rank_score"], reverse=True)
        final_ranked = final_ranked[: self.top_k]

        conf_score = float(np.mean(el_probs)) if len(el_probs) else 0.0

        logger.info(
            "[EligibilityEngine] ✅ %d/%d schemes passed: top rank_score=%.3f",
            len(final_ranked), total_considered,
            final_ranked[0]["rank_score"] if final_ranked else 0.0,
        )

        return {
            "eligible_schemes":  final_ranked,
            "total_considered":  total_considered,
            "total_eligible":    len(final_ranked),
            "confidence_score":  conf_score,
        }


# ── Internal duck-type proxy so existing EligibilityService (which uses
#    `getattr(user, field)`) still works with a plain dict. ──────────────────
class _DictProxy:
    """Thin wrapper that exposes dict values as attributes."""
    def __init__(self, d: Dict[str, Any]):
        self._d = d

    def __getattr__(self, name: str):
        try:
            return self._d[name]
        except KeyError:
            return None

    def model_dump(self):
        return dict(self._d)

    @property
    def state(self):
        return self._d.get("state")
