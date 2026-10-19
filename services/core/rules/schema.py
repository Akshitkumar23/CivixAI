from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union, Annotated
from pydantic import BaseModel, Field, ConfigDict

RuleState = Literal["PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE"]
RuleOperator = Literal[
    "eq", "neq", "gt", "gte", "lt", "lte",
    "between", "in", "not_in", "contains", "exists",
    "is_null", "is_not_null"
]

# ── 1. AST Node Models ────────────────────────────────────────────────────────

class ConditionNode(BaseModel):
    """Single atomic condition checking a profile fact against an expected value."""
    type: Literal["condition"] = "condition"
    fact: str
    operator: RuleOperator
    value: Any = None
    mandatory: bool = True
    reason_code: Optional[str] = None
    source_fragment: Optional[str] = None
    verification_status: str = "imported_unverified"

# For backwards compatibility with flat condition definitions
RuleCondition = ConditionNode


class AllNode(BaseModel):
    """Conjunction group: all child conditions must pass."""
    type: Literal["all"] = "all"
    all: List[RuleNode]
    reason_code: Optional[str] = None


class AnyNode(BaseModel):
    """Disjunction group: at least one child condition must pass."""
    type: Literal["any"] = "any"
    any: List[RuleNode]
    reason_code: Optional[str] = None


class NotNode(BaseModel):
    """Negation node: inverts the condition result."""
    model_config = ConfigDict(populate_by_name=True)
    type: Literal["not"] = "not"
    invert: RuleNode = Field(..., alias="not")
    reason_code: Optional[str] = None

    def __init__(self, **data):
        if "not_node" in data and "not" not in data and "invert" not in data:
            data["invert"] = data.pop("not_node")
        super().__init__(**data)


RuleNode = Annotated[
    Union[ConditionNode, AllNode, AnyNode, NotNode],
    Field(discriminator="type")
]

# Update forward references for recursive models
AllNode.model_rebuild()
AnyNode.model_rebuild()
NotNode.model_rebuild()


# ── 2. Evaluation Results & Decision Explanations ─────────────────────────────

class RuleEvaluationResult(BaseModel):
    state: RuleState
    fact_key: Optional[str] = None
    canonical_fact: Optional[str] = None
    resolution_source: Optional[str] = None
    operator: Optional[str] = None
    expected_value: Any = None
    actual_value: Any = None
    reason_code: Optional[str] = None
    message: str = ""
    node_type: str = "condition"
    verification_status: str = "imported_unverified"
    source_fragment: Optional[str] = None
    children: List[RuleEvaluationResult] = Field(default_factory=list)
    missing_facts: List[str] = Field(default_factory=list)


RuleEvaluationResult.model_rebuild()



class EvidenceCitation(BaseModel):
    source_url: str
    document_title: Optional[str] = None
    publisher: Optional[str] = None
    source_fragment: Optional[str] = None
    trust_level: str = "B"
    verification_status: str = "imported_unverified"
    verified_at: Optional[str] = None


DocumentProofState = Literal[
    "unknown_document",
    "user_declared_available",
    "uploaded_document",
    "machine_parsed_document",
    "verified_document",
    "expired_document",
    "rejected_document"
]

class DocumentReadinessItem(BaseModel):
    document_type: str
    is_mandatory: bool = True
    status: DocumentProofState = "unknown_document"
    weight_score: float = 0.0
    status_label: str = "Not Provided"
    notes: Optional[str] = None

class SchemeEvaluationSummary(BaseModel):
    scheme_id: str
    status: Literal["ELIGIBLE", "NEEDS_INFO", "NEEDS_VERIFICATION", "NOT_ELIGIBLE", "CONDITIONAL"]
    deterministic_result: Literal["ELIGIBLE", "NEEDS_INFO", "NEEDS_VERIFICATION", "NOT_ELIGIBLE", "CONDITIONAL"] = "NEEDS_INFO"
    authority_level: Literal["authoritative_source_verified", "tentative_unverified_rule"] = "tentative_unverified_rule"
    governance_notice: str = ""
    confidence_score: float = 1.0
    application_readiness: float = 1.0
    readiness_breakdown: List[DocumentReadinessItem] = Field(default_factory=list)
    readiness_disclaimer: str = "Application readiness score reflects document completeness only, never approval probability."
    matched_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    failed_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    unknown_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    unverified_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    missing_facts: List[str] = Field(default_factory=list)
    path_to_eligibility: List[str] = Field(default_factory=list)
    evidence: List[EvidenceCitation] = Field(default_factory=list)
