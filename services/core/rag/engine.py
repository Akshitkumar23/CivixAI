"""
Grounded Answer Engine & Deterministic Eligibility Explanation
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Synthesizes authoritative answers strictly grounded in official certified evidence.
Enforces:
1. Under NO circumstance does LLM calculate legal eligibility (routed to deterministic engine).
2. Strict bracketed citations with official URLs and snapshot hashes.
3. Zero unverified leakage (controlled fallback for unverified schemes).
4. No-evidence fallback for ungrounded inquiries.
5. Strict claim-to-chunk grounding enforcement via ClaimGroundingEngine.
6. Forensic audit tracing via RagQueryTrace with privacy PII redaction.
"""
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from services.core.database.models import RagQueryTrace, Scheme
from services.core.recommendations.engine import RecommendationEngine
from services.core.rag.normalizer import MultilingualQueryNormalizer
from services.core.rag.router import IntentRouter
from services.core.rag.retriever import HybridRetriever
from services.core.rag.grounding import ClaimGroundingEngine
from services.core.rag.privacy import QueryTracePrivacy


class GroundedAnswerEngine:
    """
    End-to-end question answering and eligibility explanation engine
    backed by deterministic rules and official verified evidence.
    """

    def __init__(
        self,
        db: Session,
        retriever: HybridRetriever,
        privacy: Optional[QueryTracePrivacy] = None
    ):
        self.db = db
        self.retriever = retriever
        self.rec_engine = RecommendationEngine(db)
        self.grounding_engine = ClaimGroundingEngine()
        self.privacy = privacy or QueryTracePrivacy(store_raw_query=False)

    def _redact_query(self, text: str) -> str:
        """
        Applies PII redaction from QueryTracePrivacy.
        """
        if self.privacy:
            return self.privacy.prepare_trace_query(text)
        return text

    def answer_query(
        self,
        raw_query: str,
        user_facts: Optional[Dict[str, Any]] = None,
        target_scheme_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes full grounded query lifecycle:
        1. Query normalization & Language detection
        2. Intent routing & Injection defense
        3. Deterministic execution (for eligibility) or Hybrid retrieval (for factual QA)
        4. Strict claim decomposition & evidence grounding
        5. Trace recording with privacy redaction
        6. Returns structured output response contract:
           answer, deterministic_status, claims, citations, missing_information,
           verification_needed, evidence_sufficiency.
        """
        start_time = time.perf_counter()

        # 1. Normalize Query
        norm = MultilingualQueryNormalizer.normalize_query(raw_query)
        detected_lang = norm["detected_language"]
        search_query = norm["search_query"]

        # 2. Classify Intent & Sanitize
        intent_payload = IntentRouter.classify_intent(norm)
        intent = intent_payload["intent"]
        effective_scheme_id = target_scheme_id or intent_payload.get("scheme_id") or norm.get("primary_scheme_id")

        if intent_payload.get("injection_detected"):
            search_query, _ = IntentRouter.sanitize_input(search_query)

        citations: List[Dict[str, Any]] = []
        response_text = ""
        eligibility_result: Optional[Dict[str, Any]] = None

        # Structured response contract fields
        deterministic_status: Optional[str] = None
        claims: List[Dict[str, Any]] = []
        missing_information: List[str] = []
        verification_needed: List[str] = []
        evidence_sufficiency: str = "SUFFICIENT"
        grounding_metrics: Dict[str, Any] = {}

        # ----------------------------------------------------------------------
        # CASE 1: OUT_OF_SCOPE
        # ----------------------------------------------------------------------
        if intent == "OUT_OF_SCOPE":
            response_text = (
                "CivixAI provides assistance strictly for verified Government of India public schemes and welfare programs. "
                "The submitted inquiry is outside the scope of public welfare and credit schemes."
            )
            deterministic_status = None
            evidence_sufficiency = "NO_EVIDENCE"
            claims = []
            grounding_metrics = {
                "citation_correctness": 1.0,
                "citation_completeness": 1.0,
                "claim_evidence_entailment": 1.0,
                "fabricated_citation_rate": 0.0,
                "wrong_scheme_citation_rate": 0.0,
                "missing_citation_rate": 0.0,
                "unsupported_claim_rate": 0.0,
                "total_claims": 0,
                "material_claims": 0,
                "supported_claims": 0,
                "pruned_claims": 0,
            }

        # ----------------------------------------------------------------------
        # CASE 2: UNVERIFIED_SCHEME_INQUIRY
        # ----------------------------------------------------------------------
        elif intent == "UNVERIFIED_SCHEME_INQUIRY":
            unv_name = intent_payload.get("unverified_scheme_name", "the requested scheme")
            reason = intent_payload.get("reason", "")
            if "institutional grant" in reason.lower() or "gated" in reason.lower():
                response_text = (
                    f"Notice: {reason} Under CivixAI governance rules, citizen guidance is strictly limited "
                    f"to verified direct citizen schemes with cryptographic audit dossiers."
                )
            else:
                response_text = (
                    f"Scheme '{unv_name}' is catalogued in CivixAI but is currently undergoing authoritative source verification "
                    f"and semantic certification. Under CivixAI governance rules, citizen guidance is strictly limited to verified schemes "
                    f"with cryptographic audit dossiers. No unverified guidance can be provided."
                )
            deterministic_status = None
            verification_needed.append("authoritative_source_verification")
            evidence_sufficiency = "NO_EVIDENCE"
            claims = []
            grounding_metrics = {
                "citation_correctness": 1.0,
                "citation_completeness": 1.0,
                "claim_evidence_entailment": 1.0,
                "fabricated_citation_rate": 0.0,
                "wrong_scheme_citation_rate": 0.0,
                "missing_citation_rate": 0.0,
                "unsupported_claim_rate": 0.0,
                "total_claims": 0,
                "material_claims": 0,
                "supported_claims": 0,
                "pruned_claims": 0,
            }

        # ----------------------------------------------------------------------
        # CASE 3: ELIGIBILITY_CHECK
        # ----------------------------------------------------------------------
        elif intent == "ELIGIBILITY_CHECK":
            # Rule: Deterministic engine evaluates, RAG retrieves statutory evidence.
            retrieved_chunks = self.retriever.retrieve(
                search_query=search_query,
                target_scheme_id=effective_scheme_id,
                section_hint="eligibility_criteria",
                top_k=4
            )

            # Build citations
            citations = self._build_citations(retrieved_chunks)

            if not retrieved_chunks:
                response_text = (
                    "No authoritative evidence was found in the verified Government of India guidelines for this inquiry."
                )
                deterministic_status = None
                evidence_sufficiency = "NO_EVIDENCE"
                claims = []
                grounding_metrics = {
                    "citation_correctness": 1.0,
                    "citation_completeness": 1.0,
                    "claim_evidence_entailment": 1.0,
                    "fabricated_citation_rate": 0.0,
                    "wrong_scheme_citation_rate": 0.0,
                    "missing_citation_rate": 0.0,
                    "unsupported_claim_rate": 0.0,
                    "total_claims": 0,
                    "material_claims": 0,
                    "supported_claims": 0,
                    "pruned_claims": 0,
                }
            elif effective_scheme_id and user_facts:
                # Deterministic AST Evaluation via Canonical Recommendation Engine
                # Deterministic eligibility status is strictly derived here and can NEVER be overridden.
                rec_output = self.rec_engine.evaluate_profile(facts=user_facts, top_k=150)
                evaluated_schemes = (
                    rec_output.get("ranked_schemes", []) +
                    rec_output.get("not_eligible_schemes", []) +
                    rec_output.get("needs_verification_schemes", []) +
                    rec_output.get("other_schemes", [])
                )
                target_eval = next((s for s in evaluated_schemes if s["scheme_id"] == effective_scheme_id), None)

                if target_eval:
                    eligibility_result = target_eval
                    # Strictly freeze deterministic eligibility status
                    deterministic_status = target_eval.get("eligibility_status", "UNKNOWN")
                    scheme_name = target_eval.get("scheme_name", effective_scheme_id)

                    if deterministic_status == "ELIGIBLE":
                        response_text = (
                            f"Based on deterministic evaluation of your provided details, you meet the eligibility criteria for {scheme_name}. "
                            f"Relevant official guidelines: {self._format_citation_mentions(citations)}. "
                            f"Note: Final approval is subject to mandatory document verification and eKYC."
                        )
                        verification_needed.append("Mandatory document verification and eKYC")
                    elif deterministic_status == "NOT_ELIGIBLE":
                        reasons = target_eval.get("reasons", [])
                        reasons_str = "; ".join(reasons) if reasons else "Statutory exclusion criteria apply"
                        response_text = (
                            f"Based on deterministic evaluation of official statutory rules for {scheme_name}, you do not currently qualify. "
                            f"Reason: {reasons_str}. "
                            f"Official statutory clause: {self._format_citation_mentions(citations)}."
                        )
                    elif deterministic_status == "NEEDS_INFO":
                        missing = target_eval.get("missing_facts", [])
                        missing_information.extend(missing)
                        missing_str = ", ".join(missing[:5]) if missing else "further applicant facts"
                        response_text = (
                            f"To determine your eligibility for {scheme_name}, the following details are required: {missing_str}. "
                            f"Official eligibility requirements: {self._format_citation_mentions(citations)}."
                        )
                    else:  # NEEDS_VERIFICATION
                        verification_needed.append("Official source verification of unverified baseline criteria")
                        response_text = (
                            f"Your application for {scheme_name} requires verification against official sources. "
                            f"Official guidelines: {self._format_citation_mentions(citations)}."
                        )
                else:
                    deterministic_status = "NOT_ELIGIBLE"
                    response_text = (
                        f"Scheme '{effective_scheme_id}' was not evaluated as an eligible candidate under current filters."
                    )
            else:
                # User asked eligibility generally without providing facts profile
                deterministic_status = None
                missing_information.append("Applicant profile facts (e.g. occupation, landholding, income) required for personal evaluation")
                evidence_summary = self._summarize_chunks(retrieved_chunks, max_chunks=3)
                scheme_mention = f" for {effective_scheme_id}" if effective_scheme_id else ""
                response_text = (
                    f"Official statutory eligibility criteria{scheme_mention}:\n\n"
                    f"{evidence_summary}\n\n"
                    f"To check your exact personal eligibility, please provide your profile details or complete the adaptive questionnaire."
                )

            # Enforce claim grounding on the answer text
            grounding_res = self.grounding_engine.enforce_grounding(
                text=response_text,
                retrieved_chunks=retrieved_chunks,
                expected_scheme_id=effective_scheme_id,
                strategy="prune"
            )
            response_text = grounding_res["grounded_text"]
            claims = grounding_res["claims"]
            evidence_sufficiency = grounding_res["evidence_sufficiency"]
            grounding_metrics = grounding_res["metrics"]

        # ----------------------------------------------------------------------
        # CASE 4: FACTUAL_QA
        # ----------------------------------------------------------------------
        else:
            retrieved_chunks = self.retriever.retrieve(
                search_query=search_query,
                target_scheme_id=effective_scheme_id,
                top_k=4
            )

            citations = self._build_citations(retrieved_chunks)
            deterministic_status = None

            if not retrieved_chunks:
                response_text = (
                    "No authoritative evidence was found in the verified Government of India guidelines for this inquiry."
                )
                evidence_sufficiency = "NO_EVIDENCE"
                claims = []
                grounding_metrics = {
                    "citation_correctness": 1.0,
                    "citation_completeness": 0.0,
                    "claim_evidence_entailment": 0.0,
                    "fabricated_citation_rate": 0.0,
                    "wrong_scheme_citation_rate": 0.0,
                    "missing_citation_rate": 0.0,
                    "unsupported_claim_rate": 0.0,
                    "total_claims": 0,
                    "material_claims": 0,
                    "supported_claims": 0,
                    "pruned_claims": 0,
                }
            else:
                evidence_text = self._summarize_chunks(retrieved_chunks, max_chunks=3)
                candidate_text = (
                    f"{evidence_text}\n\n"
                    f"Sources: {self._format_citation_mentions(citations)}"
                )
                grounding_res = self.grounding_engine.enforce_grounding(
                    text=candidate_text,
                    retrieved_chunks=retrieved_chunks,
                    expected_scheme_id=effective_scheme_id,
                    strategy="prune"
                )
                response_text = grounding_res["grounded_text"]
                claims = grounding_res["claims"]
                evidence_sufficiency = grounding_res["evidence_sufficiency"]
                grounding_metrics = grounding_res["metrics"]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Wire in query redaction from services.core.rag.privacy if present
        redacted_raw_query = self._redact_query(raw_query)
        redacted_norm_query = self._redact_query(norm["normalized_query"])

        # Record Query Trace in Database with Redacted Content
        trace_id = f"trace-{uuid.uuid4().hex[:10]}"
        trace = RagQueryTrace(
            id=trace_id,
            raw_query=redacted_raw_query,
            normalized_query=redacted_norm_query,
            detected_language=detected_lang,
            intent=intent,
            retrieved_chunk_ids_json=json.dumps([c["chunk_id"] for c in citations]),
            response_text=response_text,
            citations_json=json.dumps(citations),
            latency_ms=elapsed_ms,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(trace)
        self.db.commit()

        return {
            "trace_id": trace_id,
            "raw_query": raw_query,
            "normalized_query": norm["normalized_query"],
            "detected_language": detected_lang,
            "intent": intent,
            "scheme_id": effective_scheme_id,
            "answer": response_text,
            "response": response_text,  # backward compatibility with existing tests
            "deterministic_status": deterministic_status,
            "claims": claims,
            "citations": citations,
            "missing_information": missing_information,
            "verification_needed": verification_needed,
            "evidence_sufficiency": evidence_sufficiency,
            "eligibility_evaluation": eligibility_result,
            "grounding_metrics": grounding_metrics,
            "latency_ms": round(elapsed_ms, 2)
        }

    def _build_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        for c in chunks:
            raw_meta = c.get("metadata_json") or "{}"
            meta = json.loads(raw_meta) if isinstance(raw_meta, str) else (raw_meta or {})
            last_verified = meta.get("last_verified") or meta.get("published_date") or c.get("verified_at") or "2026-08-27"
            dossier_status = meta.get("dossier_status") or "certified_active"
            citations.append({
                "chunk_id": c["chunk_id"],
                "citation": c["source_citation"],
                "heading_path": c["heading_path"],
                "section_type": c["section_type"],
                "source_url": c["source_url"],
                "chunk_hash": c["chunk_hash"],
                "excerpt": c["content"],
                "metadata": meta,
                "last_verified": last_verified,
                "dossier_status": dossier_status
            })
        return citations

    def _format_citation_mentions(self, citations: List[Dict[str, Any]]) -> str:
        if not citations:
            return ""
        unique_citations = []
        seen = set()
        for c in citations:
            cit = c["citation"]
            if cit not in seen:
                seen.add(cit)
                unique_citations.append(f"[{cit}]")
        return ", ".join(unique_citations)

    def _summarize_chunks(self, chunks: List[Dict[str, Any]], max_chunks: int = 3) -> str:
        if not chunks:
            return "No official excerpts available."
        paragraphs = []
        for c in chunks[:max_chunks]:
            cit = c["source_citation"]
            paragraphs.append(f"• {c['content']} [{cit}]")
        return "\n\n".join(paragraphs)
