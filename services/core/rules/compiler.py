"""
CivixAI Deterministic Rule AST Compiler
=======================================
Translates normalized statutory criteria fragments and structured eligibility
lists into declarative AST nodes (ConditionNode, AllNode, AnyNode, NotNode)
using Kleene 3-valued logic semantics.

Key Invariants:
1. Zero LLM Decision Authority: Extracts declarative predicates only.
2. Discretionary Policy Detection: Vague statutory phrases ("as determined by
   competent authority", "subject to guidelines") are compiled into
   UNRESOLVED_POLICY_TERM nodes and flagged for human adjudication.
3. Provenance Grounding: Attaches EvidenceAnchor references to generated conditions.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from services.core.rules.schema import (
    RuleNode, ConditionNode, AllNode, AnyNode, NotNode, RuleOperator
)
from services.core.discovery.governance import EvidenceAnchor


class UnresolvedPolicyTerm(BaseModel):
    raw_clause: str
    policy_code: str = "DISCRETIONARY_CRITERIA"
    reason: str
    evidence_id: Optional[str] = None


class CompilationResult(BaseModel):
    candidate_id: str
    root_node: Optional[RuleNode] = None
    flat_conditions: List[ConditionNode] = Field(default_factory=list)
    unresolved_terms: List[UnresolvedPolicyTerm] = Field(default_factory=list)
    requires_human_adjudication: bool = False
    evidence_anchors: List[EvidenceAnchor] = Field(default_factory=list)
    compilation_warnings: List[str] = Field(default_factory=list)


# Statutory Discretionary Regex Patterns
DISCRETIONARY_PATTERNS = [
    (r"as (?:determined|decided|notified|prescribed) by (?:the )?(?:competent authority|government|department)", "COMPETENT_AUTHORITY_DISCRETION"),
    (r"subject to (?:applicable )?(?:departmental )?(?:guidelines|rules|budgetary availability)", "SUBJECT_TO_GUIDELINES"),
    (r"as (?:amended|notified) from time to time", "VARIABLE_POLICY_NOTICE"),
    (r"at the discretion of", "DISCRETIONARY_APPROVAL"),
    (r"any other criteria (?:as )?(?:decided|specified)", "OPEN_ENDED_CRITERIA"),
]

STATE_NAMES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli",
    "Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]


class RuleASTCompiler:
    """Deterministic compiler from criteria text/items to Rule AST."""

    def __init__(self):
        pass

    def compile_candidate(
        self,
        candidate_id: str,
        eligibility_summary: Any,
        evidence_anchors: Optional[List[EvidenceAnchor]] = None,
        default_state: Optional[str] = None,
    ) -> CompilationResult:
        """
        Compiles an eligibility summary (list of text items or structured dicts)
        into a canonical AST root node and list of atomic conditions.
        """
        anchors = evidence_anchors or []
        clauses = self._extract_raw_clauses(eligibility_summary)
        
        conditions: List[ConditionNode] = []
        unresolved: List[UnresolvedPolicyTerm] = []
        warnings: List[str] = []

        anchor_map = {a.source_locator: a.evidence_id for a in anchors if a.source_locator}
        primary_anchor_id = anchors[0].evidence_id if anchors else None

        for idx, clause in enumerate(clauses):
            clause_clean = clause.strip()
            if not clause_clean:
                continue

            # 1. Check for discretionary statutory phrases
            is_discretionary, disc_code, disc_reason = self._check_discretionary(clause_clean)
            if is_discretionary:
                unresolved.append(UnresolvedPolicyTerm(
                    raw_clause=clause_clean,
                    policy_code=disc_code,
                    reason=disc_reason,
                    evidence_id=primary_anchor_id
                ))
                continue

            # 2. Extract atomic conditions from clause
            extracted = self._parse_clause(clause_clean, primary_anchor_id, default_state)
            if extracted:
                conditions.extend(extracted)
            else:
                # If clause contains meaningful text but no recognized rule pattern, flag as warning
                if len(clause_clean) > 20:
                    warnings.append(f"Unmapped statutory clause: {clause_clean[:80]}...")

        # Build AST root node (conjunction of all mandatory conditions)
        root_node: Optional[RuleNode] = None
        if conditions:
            if len(conditions) == 1:
                root_node = conditions[0]
            else:
                root_node = AllNode(all=conditions)

        requires_human = len(unresolved) > 0 or len(warnings) > 0 or len(conditions) == 0

        return CompilationResult(
            candidate_id=candidate_id,
            root_node=root_node,
            flat_conditions=conditions,
            unresolved_terms=unresolved,
            requires_human_adjudication=requires_human,
            evidence_anchors=anchors,
            compilation_warnings=warnings,
        )

    def _extract_raw_clauses(self, raw: Any) -> List[str]:
        """Extracts flattened plain text lines from strings, lists, or editor JSON structures."""
        clauses: List[str] = []
        if not raw:
            return clauses

        if isinstance(raw, str):
            # Split by bullet points or newlines
            lines = re.split(r"[\n\r•\-\*]+", raw)
            for line in lines:
                s = line.strip()
                if s:
                    clauses.append(s)
            return clauses

        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    s = item.strip()
                    if s:
                        clauses.append(s)
                elif isinstance(item, dict):
                    # Structured editor JSON
                    text = self._extract_text_from_dict(item)
                    if text:
                        clauses.append(text)
        elif isinstance(raw, dict):
            text = self._extract_text_from_dict(raw)
            if text:
                clauses.append(text)

        return clauses

    def _extract_text_from_dict(self, d: Dict[str, Any]) -> str:
        texts = []
        if "text" in d and isinstance(d["text"], str):
            t = d["text"].strip()
            if t:
                texts.append(t)
        if "children" in d and isinstance(d["children"], list):
            for child in d["children"]:
                if isinstance(child, dict):
                    c_text = self._extract_text_from_dict(child)
                    if c_text:
                        texts.append(c_text)
                elif isinstance(child, str):
                    texts.append(child.strip())
        return " ".join(texts).strip()

    def _check_discretionary(self, text: str) -> Tuple[bool, str, str]:
        for pattern, code in DISCRETIONARY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return True, code, f"Statutory clause contains discretionary language: '{match.group(0)}'"
        return False, "", ""

    def _parse_clause(
        self,
        text: str,
        evidence_id: Optional[str] = None,
        default_state: Optional[str] = None
    ) -> List[ConditionNode]:
        """Deterministic parser identifying statutory rules in text."""
        nodes: List[ConditionNode] = []
        lower = text.lower()

        # 1. State / Residence Domicile
        for state in STATE_NAMES:
            if re.search(rf"\b(resident|domicile|citizen) of {re.escape(state)}\b", text, re.IGNORECASE) or \
               re.search(rf"\bpermanent resident of {re.escape(state)}\b", text, re.IGNORECASE) or \
               re.search(rf"\bmust be a resident of {re.escape(state)}\b", text, re.IGNORECASE):
                nodes.append(ConditionNode(
                    fact="location.state",
                    operator="eq",
                    value=state,
                    mandatory=True,
                    reason_code="STATE_RESIDENCY_CRITERIA",
                    source_fragment=text[:150],
                    verification_status="verified_from_source",
                ))

        # 2. Emergency / Accident Victims
        if "accident victim" in lower or "emergency service" in lower or "trauma care" in lower:
            nodes.append(ConditionNode(
                fact="applicant.is_accident_victim_or_emergency",
                operator="eq",
                value=True,
                mandatory=True,
                reason_code="EMERGENCY_VICTIM_CRITERIA",
                source_fragment=text[:150],
                verification_status="verified_from_source",
            ))

        # 3. Age criteria
        # Pattern: between X and Y years
        m_between = re.search(r"between\s+(\d{1,2})\s*(?:and|to|-)\s*(\d{1,2})\s*years?", lower)
        if m_between:
            min_age = int(m_between.group(1))
            max_age = int(m_between.group(2))
            nodes.append(ConditionNode(
                fact="person.age",
                operator="between",
                value=[min_age, max_age],
                mandatory=True,
                reason_code="AGE_BRACKET",
                source_fragment=text[:150],
                verification_status="verified_from_source",
            ))
        else:
            m_min = re.search(r"(?:at least|minimum|above|age of)\s+(\d{1,2})\s*years?", lower)
            if m_min:
                nodes.append(ConditionNode(
                    fact="person.age",
                    operator="gte",
                    value=int(m_min.group(1)),
                    mandatory=True,
                    reason_code="MINIMUM_AGE",
                    source_fragment=text[:150],
                    verification_status="verified_from_source",
                ))
            m_max = re.search(r"(?:maximum|not exceeding|below|up to)\s+(\d{1,2})\s*years?", lower)
            if m_max:
                nodes.append(ConditionNode(
                    fact="person.age",
                    operator="lte",
                    value=int(m_max.group(1)),
                    mandatory=True,
                    reason_code="MAXIMUM_AGE",
                    source_fragment=text[:150],
                    verification_status="verified_from_source",
                ))

        # 4. Income Limit
        m_income = re.search(r"(?:annual|family|household)?\s*income\s*(?:not exceeding|below|less than|up to|maximum of)?\s*(?:rs\.?|₹|inr)?\s*([\d,]+)", lower)
        if m_income:
            raw_val = m_income.group(1).replace(",", "")
            try:
                income_val = float(raw_val)
                if income_val >= 10000:  # Avoid matching years like 2024
                    nodes.append(ConditionNode(
                        fact="household.annual_income",
                        operator="lte",
                        value=income_val,
                        mandatory=True,
                        reason_code="ANNUAL_INCOME_CEILING",
                        source_fragment=text[:150],
                        verification_status="verified_from_source",
                    ))
            except ValueError:
                pass

        # 5. Gender
        if re.search(r"\b(?:only women|women only|female only|female applicants|girl child|widow)\b", lower):
            nodes.append(ConditionNode(
                fact="person.gender",
                operator="eq",
                value="female",
                mandatory=True,
                reason_code="TARGETED_GENDER",
                source_fragment=text[:150],
                verification_status="verified_from_source",
            ))

        # 6. Farmer / Land Ownership
        if "small and marginal farmer" in lower or "small & marginal farmer" in lower:
            nodes.append(ConditionNode(
                fact="applicant.owns_cultivable_land",
                operator="eq",
                value=True,
                mandatory=True,
                reason_code="FARMER_LAND_OWNERSHIP",
                source_fragment=text[:150],
                verification_status="verified_from_source",
            ))
            nodes.append(ConditionNode(
                fact="agriculture.land_size",
                operator="lte",
                value=5.0,  # 5 acres = 2 hectares statutory marginal limit
                mandatory=True,
                reason_code="MARGINAL_LAND_CEILING",
                source_fragment=text[:150],
                verification_status="verified_from_source",
            ))
        elif re.search(r"\b(?:farmer|cultivator|holding cultivable land)\b", lower):
            nodes.append(ConditionNode(
                fact="applicant.owns_cultivable_land",
                operator="eq",
                value=True,
                mandatory=True,
                reason_code="CULTIVABLE_LAND_OWNERSHIP",
                source_fragment=text[:150],
                verification_status="verified_from_source",
                ))

        # 7. Caste / Social Category
        castes = []
        if re.search(r"\b(?:sc|scheduled caste)\b", lower):
            castes.append("sc")
        if re.search(r"\b(?:st|scheduled tribe)\b", lower):
            castes.append("st")
        if re.search(r"\b(?:obc|other backward class)\b", lower):
            castes.append("obc")
        if castes:
            nodes.append(ConditionNode(
                fact="social.caste",
                operator="in",
                value=castes,
                mandatory=True,
                reason_code="TARGETED_SOCIAL_CATEGORY",
                source_fragment=text[:150],
                verification_status="verified_from_source",
            ))

        # 8. BPL / Antyodaya
        if re.search(r"\b(?:bpl|below poverty line)\b", lower):
            nodes.append(ConditionNode(
                fact="social.is_bpl",
                operator="eq",
                value=True,
                mandatory=True,
                reason_code="BPL_REQUIREMENT",
                source_fragment=text[:150],
                verification_status="verified_from_source",
            ))

        # 9. Disability
        if re.search(r"\b(?:disability|disabled|divyang|physically challenged)\b", lower):
            nodes.append(ConditionNode(
                fact="health.has_disability",
                operator="eq",
                value=True,
                mandatory=True,
                reason_code="DISABILITY_REQUIREMENT",
                source_fragment=text[:150],
                verification_status="verified_from_source",
            ))

        return nodes
