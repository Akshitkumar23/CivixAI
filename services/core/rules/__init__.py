from .schema import (
    RuleCondition, ConditionNode, AllNode, AnyNode, NotNode, RuleNode,
    RuleEvaluationResult, RuleState, SchemeEvaluationSummary, EvidenceCitation,
    DocumentProofState, DocumentReadinessItem
)
from .evaluator import evaluate_condition, evaluate_rule_node
from .validator import validate_rule_node, RuleValidationError
from .trace import build_scheme_evaluation
from .engine import EligibilityEngine

__all__ = [
    "RuleCondition", "ConditionNode", "AllNode", "AnyNode", "NotNode", "RuleNode",
    "RuleEvaluationResult", "RuleState", "SchemeEvaluationSummary", "EvidenceCitation",
    "DocumentProofState", "DocumentReadinessItem",
    "evaluate_condition", "evaluate_rule_node",
    "validate_rule_node", "RuleValidationError",
    "build_scheme_evaluation",
    "EligibilityEngine", "RuleDiffEngine"
]

def __getattr__(name: str):
    if name == "RuleDiffEngine":
        from services.core.ingestion.diff_engine import RuleDiffEngine
        return RuleDiffEngine
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

