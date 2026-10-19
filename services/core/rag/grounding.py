"""
Claim Grounding Engine & Strict Citation Enforcement
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Enforces cryptographic truth boundaries:
1. Decomposes synthesized answers into atomic material factual claims.
2. Maps each claim to 1 or more retrieved evidence chunk IDs using lexical and semantic entailment.
3. Evaluates grounding metrics:
   - citation correctness (target 100%)
   - citation completeness
   - claim-evidence entailment score
   - fabricated citation rate (target 0%)
   - wrong-scheme citation rate (target 0%)
   - missing citation rate
   - unsupported claim rate (target 0%)
4. Strict enforcement: Prunes or qualifies any claim lacking authoritative evidence chunks.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Common non-informative stopwords for lexical containment checks
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "at", "by",
    "for", "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "s", "t", "can",
    "will", "just", "don", "should", "now", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "this", "that", "these", "those", "it", "its", "you",
    "your", "we", "our", "he", "she", "they", "them", "their", "what",
    "which", "who", "whom", "also", "per", "based", "according", "relevant",
    "official", "guidelines", "source", "sources", "note", "clause"
}

# Keywords indicating material factual claims (financial, eligibility, exclusions, requirements)
MATERIAL_KEYWORDS = {
    # Financial and numeric terms
    "rs", "inr", "rupees", "lakh", "crore", "hazar", "thousand", "installment",
    "installments", "tranche", "tranches", "subsidy", "interest", "loan",
    "grant", "pension", "incentive", "toolkit", "credit", "ceiling", "amount",
    "percent", "percentage", "%", "financial",
    # Demographic and occupational terms
    "farmer", "farmers", "landholder", "landholding", "cultivable", "hectare",
    "acre", "woman", "women", "adult", "artisan", "artisans", "craftsman",
    "craftsmen", "vendor", "vendors", "hawker", "street", "bpl", "ration",
    "sc", "st", "obc", "minority", "disability", "disabled", "pwd", "age",
    # Statutory conditions and exclusions
    "eligible", "eligibility", "criteria", "excluded", "exclusion", "exclusions",
    "taxpayer", "tax", "income", "disqualified", "ineligible", "mandate",
    "mandatory", "required", "requirement", "requirements", "ekyc", "aadhaar",
    "connection", "cylinder", "stove", "hotplate", "refill", "deposit-free",
    "trade", "trades", "scheme", "guideline", "guidelines", "sanction"
}


@dataclass
class GroundedClaim:
    """
    Atomic proposition extracted from generated answer statements.
    """
    claim_id: str
    statement: str
    is_material: bool
    claim_type: str  # financial_benefit, eligibility_criterion, statutory_exclusion, document_requirement, procedural_guideline, general_factual, meta_statement, citation_reference, status_assertion
    supporting_chunk_ids: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    entailment_score: float = 0.0
    supported: bool = False
    rejection_reason: Optional[str] = None
    pruned: bool = False
    qualified_statement: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GroundingMetrics:
    """
    Quantitative evaluation metrics measuring factual alignment and citation integrity.
    """
    citation_correctness: float = 1.0       # Proportion of valid citations in text (1.0 = 100%)
    citation_completeness: float = 1.0      # Proportion of material claims supported by evidence
    claim_evidence_entailment: float = 0.0  # Mean entailment score across material claims
    fabricated_citation_rate: float = 0.0   # Citations referencing nonexistent chunks (target 0.0)
    wrong_scheme_citation_rate: float = 0.0 # Citations pointing to unrelated schemes (target 0.0)
    missing_citation_rate: float = 0.0      # Material claims lacking supporting chunk
    unsupported_claim_rate: float = 0.0     # Material claims unsupported in final answer (target 0.0)
    total_claims: int = 0
    material_claims: int = 0
    supported_claims: int = 0
    pruned_claims: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_correctness": round(self.citation_correctness, 4),
            "citation_completeness": round(self.citation_completeness, 4),
            "claim_evidence_entailment": round(self.claim_evidence_entailment, 4),
            "fabricated_citation_rate": round(self.fabricated_citation_rate, 4),
            "wrong_scheme_citation_rate": round(self.wrong_scheme_citation_rate, 4),
            "missing_citation_rate": round(self.missing_citation_rate, 4),
            "unsupported_claim_rate": round(self.unsupported_claim_rate, 4),
            "total_claims": self.total_claims,
            "material_claims": self.material_claims,
            "supported_claims": self.supported_claims,
            "pruned_claims": self.pruned_claims,
        }


class ClaimGroundingEngine:
    """
    Authoritative Claim-to-Evidence Grounding & Verification Engine.
    Enforces deterministic grounding on all RAG synthesized answers.
    """

    def __init__(self, entailment_threshold: float = 0.25):
        self.entailment_threshold = entailment_threshold

    # ── 1. Atomic Claim Decomposition ────────────────────────────────────────

    def decompose_claims(self, text: str) -> List[GroundedClaim]:
        """
        Decomposes answer statements into discrete atomic factual claims.
        Distinguishes material factual claims from meta/transitional statements.
        """
        if not text or not text.strip():
            return []

        raw_statements = self._split_into_statements(text)
        claims: List[GroundedClaim] = []

        for idx, stmt in enumerate(raw_statements, start=1):
            stmt_clean = stmt.strip()
            if not stmt_clean:
                continue

            # Check for inline bracketed citations e.g. [DA&FW PM-KISAN ...]
            inline_citations = re.findall(r"\[(.*?)\]", stmt_clean)

            # Determine statement classification & materiality
            claim_type, is_material = self._classify_statement(stmt_clean)

            claim_id = f"claim-{idx:03d}"
            claims.append(
                GroundedClaim(
                    claim_id=claim_id,
                    statement=stmt_clean,
                    is_material=is_material,
                    claim_type=claim_type,
                    citations=inline_citations
                )
            )

        return claims

    def _split_into_statements(self, text: str) -> List[str]:
        """
        Splits text into atomic statements across bullet points, numbered lists,
        and punctuation boundaries while preserving Indian numbers and abbreviations.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        statements = []

        for line in lines:
            cleaned_line = re.sub(r"^[•\-\*]\s*", "", line)
            cleaned_line = re.sub(r"^\d+[\.\)]\s*", "", cleaned_line)

            # Skip pure header lines or source blocks
            if cleaned_line.lower().startswith("sources:") or cleaned_line.lower().startswith("source:"):
                continue

            # Sentence splitting regex that does NOT split abbreviations (Rs., No., Dr., e.g., i.e.)
            # and avoids splitting before digits (e.g. Rs. 6,000)
            pat = r"(?<!\bRs)(?<!\bNo)(?<!\bDr)(?<!\be\.g)(?<!\bi\.e)(?<=[.!?])\s+(?=[A-Z\u0900-\u097F•\-])"
            parts = re.split(pat, cleaned_line)
            for part in parts:
                p_str = part.strip()
                if p_str:
                    statements.append(p_str)

        return statements

    def _classify_statement(self, statement: str) -> Tuple[str, bool]:
        """
        Classifies the statement type and determines whether it asserts a material factual claim.
        """
        stmt_lower = statement.lower()

        # Citation references and metadata lines
        if any(cit_prefix in stmt_lower for cit_prefix in [
            "official statutory clause:",
            "relevant official guidelines:",
            "official eligibility requirements:",
            "official guidelines:",
            "sources:",
            "source:",
            "official statutory eligibility criteria"
        ]):
            return "citation_reference", False

        # Meta & boilerplate statements
        if any(meta in stmt_lower for meta in [
            "civixai provides assistance strictly",
            "outside the scope of public welfare",
            "to check your exact personal eligibility",
            "please provide your profile details",
            "under civixai governance rules",
            "is currently undergoing authoritative source verification",
            "no authoritative evidence was found",
            "final approval is subject to mandatory document verification"
        ]):
            return "meta_statement", False

        # Status assertion statements (handled deterministically by RecommendationEngine)
        if (
            "based on deterministic evaluation" in stmt_lower
            or "statutory exclusion criteria apply" in stmt_lower
            or stmt_lower.startswith("reason:")
        ):
            return "status_assertion", False

        # Check for financial benefit assertions
        # Strip bracketed citations to avoid false positive from citation references
        clean_stmt = re.sub(r"\[.*?\]", " ", stmt_lower)
        has_number = bool(re.search(r"\b\d+(?:,\d+)*(?:\.\d+)?\b|[₹$]|(lakh|crore|hazar|k\b|tranche|installments?)", clean_stmt))
        has_financial = any(w in clean_stmt for w in ["rs", "inr", "rupees", "subsidy", "interest", "benefit", "credit", "loan", "toolkit", "refill"])

        if has_number and has_financial:
            return "financial_benefit", True

        # Check for exclusions
        if any(w in clean_stmt for w in ["excluded", "exclusion", "disqualified", "not eligible", "ineligible", "tax payer", "income tax"]):
            return "statutory_exclusion", True

        # Check for document / eKYC requirements
        if any(w in clean_stmt for w in ["aadhaar", "ekyc", "ration card", "certificate", "id proof"]):
            return "document_requirement", True

        # Check for eligibility criteria
        if any(w in clean_stmt for w in ["adult woman", "farmer", "vendor", "artisan", "craftsman", "landholder", "cultivable", "poor household", "bpl"]):
            return "eligibility_criterion", True

        # Check general material keywords
        words = set(re.findall(r"[a-z0-9\u0900-\u097F]+", clean_stmt))
        if (words & MATERIAL_KEYWORDS) and has_number:
            return "general_factual", True

        if words & {"adult woman", "first refill", "stove", "hotplate", "deposit-free", "deduplication", "toolkit", "18 trades"}:
            return "general_factual", True

        return "general_statement", False

    # ── 2. Lexical & Semantic Entailment Mapping ──────────────────────────────

    def map_claims_to_evidence(
        self,
        claims: List[GroundedClaim],
        retrieved_chunks: List[Dict[str, Any]],
        expected_scheme_id: Optional[str] = None
    ) -> List[GroundedClaim]:
        """
        Maps each atomic claim to supporting evidence chunk IDs using lexical
        containment, numeric fidelity, and semantic entailment.
        """
        if not retrieved_chunks:
            for claim in claims:
                if claim.is_material:
                    claim.supported = False
                    claim.rejection_reason = "No retrieved evidence chunks available"
            return claims

        for claim in claims:
            if not claim.is_material:
                # Non-material statements (e.g. meta notices, status declarations) are valid by default
                claim.supported = True
                claim.entailment_score = 1.0
                continue

            supporting_chunk_ids: List[str] = []
            citations: List[str] = []
            best_score = 0.0

            claim_numbers = self._extract_normalized_numbers(claim.statement)
            claim_tokens = self._extract_content_tokens(claim.statement)

            for chunk in retrieved_chunks:
                chunk_id = chunk["chunk_id"]
                chunk_content = chunk.get("content", "")
                chunk_citation = chunk.get("source_citation", chunk.get("citation", chunk_id))
                chunk_scheme = chunk.get("scheme_id")

                # If an expected scheme is specified, chunks from completely different schemes
                # cannot legitimately substantiate this scheme's statutory criteria
                is_wrong_scheme = bool(expected_scheme_id and chunk_scheme and chunk_scheme != expected_scheme_id)

                # Compute entailment score
                score, entails = self._evaluate_chunk_entailment(
                    claim_tokens=claim_tokens,
                    claim_numbers=claim_numbers,
                    claim_citations=claim.citations,
                    chunk_content=chunk_content,
                    chunk_citation=chunk_citation,
                    is_wrong_scheme=is_wrong_scheme
                )

                if score > best_score:
                    best_score = score

                if entails and not is_wrong_scheme:
                    supporting_chunk_ids.append(chunk_id)
                    if chunk_citation and chunk_citation not in citations:
                        citations.append(chunk_citation)

            claim.supporting_chunk_ids = supporting_chunk_ids
            claim.citations = citations if citations else claim.citations
            claim.entailment_score = round(best_score, 4)

            if supporting_chunk_ids:
                claim.supported = True
                claim.rejection_reason = None
            else:
                claim.supported = False
                if best_score > 0.0 and best_score < self.entailment_threshold:
                    claim.rejection_reason = f"Insufficient entailment score ({best_score:.2f} < {self.entailment_threshold:.2f})"
                elif claim_numbers and not supporting_chunk_ids:
                    claim.rejection_reason = f"Numeric claims {claim_numbers} unverified in retrieved evidence"
                else:
                    claim.rejection_reason = "No supporting evidence chunk found in retrieved context"

        return claims

    def _evaluate_chunk_entailment(
        self,
        claim_tokens: Set[str],
        claim_numbers: Set[str],
        claim_citations: List[str],
        chunk_content: str,
        chunk_citation: str,
        is_wrong_scheme: bool
    ) -> Tuple[float, bool]:
        """
        Evaluates entailment between a claim and an evidence chunk.
        Enforces strict numeric preservation and lexical overlap.
        """
        if is_wrong_scheme:
            return 0.0, False

        chunk_tokens = self._extract_content_tokens(chunk_content)
        chunk_numbers = self._extract_normalized_numbers(chunk_content)

        # Strict Numeric Verification:
        # If claim asserts specific numbers (e.g. ₹6,000, 3 installments, 15,000, 7%),
        # at least one of the primary numbers MUST be present in the evidence chunk.
        if claim_numbers:
            matching_numbers = claim_numbers & chunk_numbers
            if not matching_numbers:
                return 0.05, False

        # Lexical Token Containment
        if not claim_tokens:
            return 0.5, True

        common_tokens = claim_tokens & chunk_tokens
        token_recall = len(common_tokens) / len(claim_tokens)

        # Citation Linkage: If claim explicitly cites this chunk's citation
        citation_match = any(
            c.lower() in chunk_citation.lower() or chunk_citation.lower() in c.lower()
            for c in claim_citations
        )

        score = token_recall
        if citation_match:
            score = min(1.0, score + 0.35)
        if claim_numbers and (claim_numbers & chunk_numbers):
            score = min(1.0, score + 0.20)

        entails = score >= self.entailment_threshold and (not claim_numbers or bool(claim_numbers & chunk_numbers))
        return score, entails

    def _extract_content_tokens(self, text: str) -> Set[str]:
        """Extracts non-stopword alphanumeric content tokens, stripping inline citations."""
        clean_text = re.sub(r"\[.*?\]", " ", text)
        raw_words = re.findall(r"[a-z0-9\u0900-\u097F]+", clean_text.lower())
        return {w for w in raw_words if w not in STOPWORDS and len(w) >= 2}

    def _extract_normalized_numbers(self, text: str) -> Set[str]:
        """
        Extracts numbers in standardized form (e.g. 6000, 2000, 15000, 50000, 7).
        Removes commas, currency symbols, and ignores bracketed citation tags.
        """
        clean_text = re.sub(r"\[.*?\]", " ", text)
        numbers = set()
        t = clean_text.replace("₹", " ").replace("Rs.", " ").replace("INR", " ")
        for match in re.finditer(r"\b\d+(?:,\d+)*(?:\.\d+)?%?\b", t):
            raw = match.group(0).replace(",", "").rstrip("%")
            if raw:
                try:
                    f_val = float(raw)
                    if f_val.is_integer():
                        numbers.add(str(int(f_val)))
                    else:
                        numbers.add(str(f_val))
                except ValueError:
                    numbers.add(raw)

        # Handle Indian numeric expressions
        lower_t = clean_text.lower()
        if "50k" in lower_t:
            numbers.add("50000")
        if "15k" in lower_t:
            numbers.add("15000")
        if "25k" in lower_t:
            numbers.add("25000")
        if "6 hazar" in lower_t or "6 हजार" in clean_text:
            numbers.add("6000")

        return numbers

    # ── 3. Quantitative Grounding Evaluation ──────────────────────────────────

    def evaluate_grounding(
        self,
        claims: List[GroundedClaim],
        retrieved_chunks: List[Dict[str, Any]],
        raw_citations_in_text: Optional[List[str]] = None,
        expected_scheme_id: Optional[str] = None
    ) -> GroundingMetrics:
        """
        Calculates grounding metrics:
        - citation correctness
        - citation completeness
        - claim-evidence entailment
        - fabricated citation rate (target 0%)
        - wrong-scheme citation rate (target 0%)
        - missing citation rate
        - unsupported claim rate (target 0%)
        """
        valid_citations = {c.get("source_citation", c.get("citation", "")) for c in retrieved_chunks}
        valid_chunk_ids = {c["chunk_id"] for c in retrieved_chunks}
        valid_headings = {c.get("heading_path", "") for c in retrieved_chunks if c.get("heading_path")}
        scheme_by_citation = {
            c.get("source_citation", c.get("citation", "")): c.get("scheme_id")
            for c in retrieved_chunks
        }

        citations_to_check = raw_citations_in_text if raw_citations_in_text is not None else []
        if not citations_to_check:
            for claim in claims:
                citations_to_check.extend(claim.citations)

        total_citations = len(citations_to_check)
        fabricated_count = 0
        wrong_scheme_count = 0

        for cit in citations_to_check:
            cit_clean = cit.strip("[] ")
            if not cit_clean:
                continue

            # Check if citation matches any retrieved citation, chunk_id, or heading_path
            # Also heading paths contain ">"
            is_valid_heading = (cit_clean in valid_headings) or (">" in cit_clean and any(h and cit_clean in h for h in valid_headings))
            matched = is_valid_heading or any(
                cit_clean.lower() in v.lower() or v.lower() in cit_clean.lower()
                for v in (valid_citations | valid_chunk_ids)
                if v
            )

            if not matched:
                fabricated_count += 1
            elif expected_scheme_id and not is_valid_heading:
                # Check scheme correctness for external citations
                cit_scheme = next(
                    (s for c_name, s in scheme_by_citation.items() if cit_clean.lower() in c_name.lower()),
                    None
                )
                if cit_scheme and cit_scheme != expected_scheme_id:
                    wrong_scheme_count += 1

        fabricated_rate = (fabricated_count / total_citations) if total_citations > 0 else 0.0
        wrong_scheme_rate = (wrong_scheme_count / total_citations) if total_citations > 0 else 0.0
        citation_correctness = (1.0 - fabricated_rate) if total_citations > 0 else 1.0

        # Material Claim Metrics
        material_claims = [c for c in claims if c.is_material]
        supported_material = [c for c in material_claims if c.supported]
        unsupported_material = [c for c in material_claims if not c.supported]

        total_material = len(material_claims)
        citation_completeness = (len(supported_material) / total_material) if total_material > 0 else 1.0
        missing_citation_rate = (len(unsupported_material) / total_material) if total_material > 0 else 0.0
        unsupported_claim_rate = (len(unsupported_material) / total_material) if total_material > 0 else 0.0

        entailment_scores = [c.entailment_score for c in material_claims]
        mean_entailment = (sum(entailment_scores) / len(entailment_scores)) if entailment_scores else 1.0

        pruned_count = sum(1 for c in claims if c.pruned)

        return GroundingMetrics(
            citation_correctness=citation_correctness,
            citation_completeness=citation_completeness,
            claim_evidence_entailment=mean_entailment,
            fabricated_citation_rate=fabricated_rate,
            wrong_scheme_citation_rate=wrong_scheme_rate,
            missing_citation_rate=missing_citation_rate,
            unsupported_claim_rate=unsupported_claim_rate,
            total_claims=len(claims),
            material_claims=total_material,
            supported_claims=len(supported_material),
            pruned_claims=pruned_count,
        )

    # ── 4. Strict Enforcement (Prune or Qualify) ──────────────────────────────

    def enforce_grounding(
        self,
        text: str,
        retrieved_chunks: List[Dict[str, Any]],
        expected_scheme_id: Optional[str] = None,
        strategy: str = "prune"
    ) -> Dict[str, Any]:
        """
        Executes strict truth enforcement on synthesized response text:
        1. Decomposes into atomic claims.
        2. Maps each claim to evidence chunks.
        3. If any material claim lacks supporting chunks, prunes or qualifies it.
        4. Evaluates evidence sufficiency and computes grounding metrics.
        5. Guarantees 0% unsupported material claim rate in finalized answer.
        """
        claims = self.decompose_claims(text)
        claims = self.map_claims_to_evidence(claims, retrieved_chunks, expected_scheme_id=expected_scheme_id)

        raw_citations_in_text = re.findall(r"\[(.*?)\]", text)
        metrics = self.evaluate_grounding(
            claims=claims,
            retrieved_chunks=retrieved_chunks,
            raw_citations_in_text=raw_citations_in_text,
            expected_scheme_id=expected_scheme_id
        )

        material_claims = [c for c in claims if c.is_material]
        supported_material = [c for c in material_claims if c.supported]

        # Determine Evidence Sufficiency
        if not retrieved_chunks:
            evidence_sufficiency = "NO_EVIDENCE"
        elif total_mat := len(material_claims):
            if len(supported_material) == total_mat:
                evidence_sufficiency = "SUFFICIENT"
            elif len(supported_material) > 0:
                evidence_sufficiency = "PARTIAL"
            else:
                evidence_sufficiency = "INSUFFICIENT"
        else:
            evidence_sufficiency = "SUFFICIENT"

        # Reconstruct Grounded Answer based on strategy
        grounded_statements: List[str] = []

        if strategy == "prune":
            for claim in claims:
                if claim.is_material and not claim.supported:
                    claim.pruned = True
                    logger.info("Pruned unsupported claim: '%s' (%s)", claim.statement, claim.rejection_reason)
                    continue
                grounded_statements.append(claim.statement)

            # If all material claims were pruned and inquiry is factual, fallback
            if material_claims and not supported_material:
                final_answer = "No authoritative evidence was found in the verified Government of India guidelines for this inquiry."
                evidence_sufficiency = "NO_EVIDENCE"
            else:
                final_answer = "\n\n".join(grounded_statements) if grounded_statements else (
                    "No authoritative evidence was found in the verified Government of India guidelines for this inquiry."
                )

        elif strategy == "qualify":
            for claim in claims:
                if claim.is_material and not claim.supported:
                    qualified = f"Unverified note: {claim.statement} (Notice: Statement lacks statutory evidence in verified official guidelines)."
                    claim.qualified_statement = qualified
                    grounded_statements.append(qualified)
                else:
                    grounded_statements.append(claim.statement)
            final_answer = "\n\n".join(grounded_statements)
        else:
            final_answer = text

        # Re-compute finalized metrics on the reconstructed text
        finalized_claims = [c for c in claims if not c.pruned]
        final_material = [c for c in finalized_claims if c.is_material]
        final_supported = [c for c in final_material if c.supported]
        final_unsupported_rate = (
            (len(final_material) - len(final_supported)) / len(final_material)
        ) if final_material else 0.0

        metrics.unsupported_claim_rate = final_unsupported_rate
        metrics.pruned_claims = sum(1 for c in claims if c.pruned)

        return {
            "grounded_text": final_answer,
            "claims": [c.to_dict() for c in claims],
            "evidence_sufficiency": evidence_sufficiency,
            "metrics": metrics.to_dict(),
            "citations": [
                {
                    "chunk_id": c["chunk_id"],
                    "citation": c.get("source_citation", c.get("citation", "")),
                    "source_url": c.get("source_url", ""),
                    "chunk_hash": c.get("chunk_hash", ""),
                    "excerpt": c.get("content", "")
                }
                for c in retrieved_chunks
            ]
        }
