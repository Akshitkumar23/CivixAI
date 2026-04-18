"""
RetrievalAgent — Stage 3 of the CivixAI Agent Pipeline
=======================================================
Responsibilities:
  - Given the list of eligible schemes from EligibilityEngine, retrieve the
    most contextually relevant scheme texts / metadata to enrich the set.
  - Implements two retrieval strategies:
      A) Keyword-based retrieval  — always available, zero setup
      B) FAISS semantic search    — activated if a FAISS index is on disk

  - The agent returns the same scheme list, optionally annotated with
    `retrieved_context` strings that the ReasoningAgent will use for
    personalized explanation.

Design notes:
  - No LLM is called here — this is a RETRIEVAL-only stage.
  - FAISS index is built lazily and cached in memory.
  - If FAISS is not available the agent gracefully falls back to keyword search.
  - The agent is completely stateless per-request (thread-safe).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Try to import FAISS (optional dependency) ─────────────────────────────────
try:
    import faiss  # type: ignore
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger.warning("[RetrievalAgent] FAISS not installed. Using keyword-only retrieval.")

# ── Try to import sentence-transformers (optional) ────────────────────────────
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    HAS_ST = True
except ImportError:
    HAS_ST = False
    logger.warning("[RetrievalAgent] sentence-transformers not installed. Using keyword-only retrieval.")

# ── Default embedding model (small, fast, multilingual-aware for Hindi words) ─
DEFAULT_EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# ── Relevance keywords mapped to user profile fields ─────────────────────────
PROFILE_KEYWORD_MAP = {
    "farmer":       ["farmer", "kisan", "agriculture", "krishi", "fasal", "land"],
    "student":      ["scholarship", "education", "vidya", "student", "academic"],
    "employed":     ["employment", "worker", "shramik", "esi", "epf"],
    "unemployed":   ["self employment", "skill", "rozgar", "startup", "mudra"],
    "retired":      ["pension", "senior", "retirement", "varishtha"],
    "female":       ["mahila", "women", "nari", "beti", "stree", "maternity"],
    "sc":           ["sc", "scheduled caste", "dalit", "ambedkar"],
    "st":           ["st", "scheduled tribe", "tribal", "adivasi", "van dhan"],
    "obc":          ["obc", "backward class", "backward communities"],
    "rural":        ["rural", "gramin", "village", "panchayat"],
    "urban":        ["urban", "city", "metro", "pm svanidhi"],
    "disability":   ["disability", "divyang", "handicapped", "pwds"],
    "bpl":          ["bpl", "below poverty", "antyodaya", "ration card"],
    "loan":         ["loan", "credit", "mudra", "interest subsidy"],
    "business":     ["startup", "entrepreneur", "msme", "stand-up india"],
    "health":       ["health", "insurance", "bima", "ayushman", "pmjay"],
}


class RetrievalAgent:
    """
    Agent 3 — Contextual Scheme Retrieval

    Usage:
        agent = RetrievalAgent(all_schemes_texts, index_path="data/schemes.index")
        results = agent.retrieve(clean_profile, eligible_schemes)
        # Returns eligible_schemes with `retrieved_context` field populated.
    """

    def __init__(
        self,
        all_scheme_texts: List[str],
        all_scheme_ids: List[str],
        index_path: Optional[str] = None,
        embed_model_name: str = DEFAULT_EMBED_MODEL,
        top_k: int = 5,
    ):
        self.all_scheme_texts  = all_scheme_texts
        self.all_scheme_ids    = all_scheme_ids
        self.index_path        = index_path
        self.top_k             = top_k
        self._faiss_index      = None
        self._embed_model      = None
        self._embeddings_cache: Optional[np.ndarray] = None

        # Try to load FAISS index + embedding model (lazy init)
        if HAS_FAISS and HAS_ST and index_path:
            self._try_load_faiss(index_path, embed_model_name)

    # ──────────────────────────────────────────────────────────────────────────
    # Public entry-point
    # ──────────────────────────────────────────────────────────────────────────
    def retrieve(
        self,
        clean_profile: Dict[str, Any],
        eligible_schemes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Retrieve contextual information and annotate each eligible scheme.

        Parameters
        ----------
        clean_profile    : dict — validated user profile from InputAgent
        eligible_schemes : list — schemes from EligibilityEngine

        Returns
        -------
        Same list, each scheme now has `retrieved_context: str` populated.
        """
        if not eligible_schemes:
            return eligible_schemes

        # Build a query string from the user's profile
        query = self._profile_to_query(clean_profile)

        # Choose retrieval strategy
        if self._faiss_index is not None and self._embed_model is not None:
            context_map = self._semantic_retrieve(query, eligible_schemes)
        else:
            context_map = self._keyword_retrieve(clean_profile, eligible_schemes)

        # Annotate eligible schemes
        for scheme in eligible_schemes:
            sid = scheme.get("scheme_id", "")
            scheme["retrieved_context"] = context_map.get(
                sid,
                self._build_fallback_context(scheme)
            )

        logger.info(
            "[RetrievalAgent] ✅ Annotated %d schemes with retrieved context.",
            len(eligible_schemes),
        )
        return eligible_schemes

    # ──────────────────────────────────────────────────────────────────────────
    # Strategy A — Keyword-based retrieval (always available)
    # ──────────────────────────────────────────────────────────────────────────
    def _keyword_retrieve(
        self,
        profile: Dict[str, Any],
        eligible_schemes: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        """Build context from the scheme's own benefit_description + matched keywords."""
        context_map: Dict[str, str] = {}

        # Collect profile-based relevant keywords
        relevant_kws: List[str] = []
        occ = str(profile.get("occupation", "")).lower()
        if occ in PROFILE_KEYWORD_MAP:
            relevant_kws.extend(PROFILE_KEYWORD_MAP[occ])

        gender = str(profile.get("gender", "")).lower()
        if gender in PROFILE_KEYWORD_MAP:
            relevant_kws.extend(PROFILE_KEYWORD_MAP[gender])

        caste = str(profile.get("caste", "")).lower()
        if caste in PROFILE_KEYWORD_MAP:
            relevant_kws.extend(PROFILE_KEYWORD_MAP[caste])

        if profile.get("isBPL"):
            relevant_kws.extend(PROFILE_KEYWORD_MAP["bpl"])
        if profile.get("hasDisability"):
            relevant_kws.extend(PROFILE_KEYWORD_MAP["disability"])

        loan_req = str(profile.get("loanRequirement", "none")).lower()
        if loan_req and loan_req != "none":
            relevant_kws.extend(PROFILE_KEYWORD_MAP.get(loan_req, []))
            relevant_kws.extend(PROFILE_KEYWORD_MAP["loan"])

        urban_rural = str(profile.get("urbanRural", "")).lower()
        if urban_rural in PROFILE_KEYWORD_MAP:
            relevant_kws.extend(PROFILE_KEYWORD_MAP[urban_rural])

        relevant_kws = list(set(relevant_kws))

        for scheme in eligible_schemes:
            sid = scheme.get("scheme_id", "")
            s_desc = str(scheme.get("benefit_description", ""))
            s_name = str(scheme.get("scheme_name", ""))
            txt    = f"{s_name} {s_desc}".lower()

            # Highlight matched keywords in the description
            matched = [kw for kw in relevant_kws if kw in txt]
            snippets: List[str] = []

            if s_desc and len(s_desc) > 30:
                snippets.append(s_desc[:300].rstrip("., ") + ".")

            if matched:
                snippets.append(
                    f"Relevant keywords matched: {', '.join(matched[:6])}."
                )

            if scheme.get("ministry"):
                snippets.append(f"Managed by: {scheme['ministry']}.")

            if scheme.get("benefit_amount"):
                snippets.append(f"Benefit: {scheme['benefit_amount']}.")

            context_map[sid] = " ".join(snippets) or self._build_fallback_context(scheme)

        return context_map

    # ──────────────────────────────────────────────────────────────────────────
    # Strategy B — FAISS semantic retrieval (optional)
    # ──────────────────────────────────────────────────────────────────────────
    def _semantic_retrieve(
        self,
        query: str,
        eligible_schemes: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        """Use FAISS to find semantically similar scheme descriptions."""
        context_map: Dict[str, str] = {}
        try:
            q_emb = self._embed_model.encode([query], convert_to_numpy=True)
            q_emb = q_emb.astype("float32")
            faiss.normalize_L2(q_emb)

            topk = min(self.top_k * 2, len(self.all_scheme_texts))
            _, indices = self._faiss_index.search(q_emb, topk)

            retrieved_ids = {
                self.all_scheme_ids[i]
                for i in indices[0]
                if 0 <= i < len(self.all_scheme_ids)
            }

            for scheme in eligible_schemes:
                sid = scheme.get("scheme_id", "")
                if sid in retrieved_ids:
                    # Build context from the retrieved text
                    try:
                        idx = self.all_scheme_ids.index(sid)
                        context_map[sid] = self.all_scheme_texts[idx][:400]
                    except ValueError:
                        context_map[sid] = self._build_fallback_context(scheme)
                else:
                    context_map[sid] = self._build_fallback_context(scheme)

        except Exception as e:
            logger.error("[RetrievalAgent] FAISS retrieval failed: %s — falling back to keyword.", e)
            return {}

        return context_map

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _profile_to_query(self, profile: Dict[str, Any]) -> str:
        """Convert user profile into a natural-language search query."""
        parts = []
        age   = profile.get("age", "")
        occ   = str(profile.get("occupation", "")).capitalize()
        income= profile.get("annualIncome", 0)
        state = str(profile.get("state", ""))
        caste = str(profile.get("caste", "")).upper()
        loan  = str(profile.get("loanRequirement", ""))

        parts.append(f"{age}-year-old {occ} from {state}")
        if income:
            parts.append(f"annual income {income}")
        if caste and caste not in ("GENERAL", ""):
            parts.append(f"caste {caste}")
        if profile.get("hasDisability"):
            parts.append("person with disability")
        if profile.get("isBPL"):
            parts.append("BPL family")
        if loan and loan != "none":
            parts.append(f"{loan} loan requirement")

        return " ".join(parts)

    def _build_fallback_context(self, scheme: Dict[str, Any]) -> str:
        """Minimal context if no retrieval result available."""
        name  = scheme.get("scheme_name", "This scheme")
        desc  = str(scheme.get("benefit_description", ""))[:200]
        ministry = scheme.get("ministry", "Government of India")
        return f"{name}: {desc} (by {ministry})." if desc else f"{name} by {ministry}."

    def _try_load_faiss(self, index_path: str, embed_model_name: str):
        """Attempt to load a cached FAISS index from disk."""
        try:
            path = Path(index_path)
            if path.exists():
                self._faiss_index = faiss.read_index(str(path))
                self._embed_model = SentenceTransformer(embed_model_name)
                logger.info("[RetrievalAgent] ✅ Loaded FAISS index from '%s'.", index_path)
            else:
                logger.info(
                    "[RetrievalAgent] No FAISS index at '%s'. Building now...", index_path
                )
                self._build_and_save_faiss(index_path, embed_model_name)
        except Exception as e:
            logger.error("[RetrievalAgent] Could not load FAISS index: %s", e)

    def _build_and_save_faiss(self, index_path: str, embed_model_name: str):
        """Build FAISS index from scheme texts and save to disk."""
        try:
            self._embed_model = SentenceTransformer(embed_model_name)
            embeddings = self._embed_model.encode(
                self.all_scheme_texts, convert_to_numpy=True, show_progress_bar=False
            ).astype("float32")

            faiss.normalize_L2(embeddings)
            dim = embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)  # Inner-product = cosine (after L2 norm)
            index.add(embeddings)

            Path(index_path).parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(index, str(index_path))
            self._faiss_index     = index
            self._embeddings_cache = embeddings
            logger.info("[RetrievalAgent] ✅ Built and saved FAISS index → '%s'.", index_path)
        except Exception as e:
            logger.error("[RetrievalAgent] Failed to build FAISS index: %s", e)

    # ── Class method: build index on demand (e.g. from a management script) ──
    @classmethod
    def build_index(
        cls,
        scheme_texts: List[str],
        scheme_ids: List[str],
        output_path: str,
        embed_model_name: str = DEFAULT_EMBED_MODEL,
    ) -> None:
        """
        Utility to pre-build and save the FAISS index from the master dataset.
        Run this once after updating schemes_master.csv.
        """
        agent = cls(scheme_texts, scheme_ids, index_path=None)
        agent._build_and_save_faiss(output_path, embed_model_name)
