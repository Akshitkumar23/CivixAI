from typing import Any, Dict, List, Optional, Union
from .schema import (
    RuleNode, ConditionNode, AllNode, AnyNode, NotNode,
    RuleCondition, RuleEvaluationResult, RuleState
)
from services.core.facts.resolver import resolve_fact, FactResolution

def evaluate_condition(
    condition: ConditionNode,
    facts: Dict[str, Any],
    contract: Optional[Dict[str, Any]] = None
) -> RuleEvaluationResult:
    """Evaluates a single leaf ConditionNode against user profile facts using generic schema resolution."""
    fact_key = condition.fact
    operator = condition.operator
    expected = condition.value

    # Centralized generic schema-driven fact resolution
    resolution = resolve_fact(fact_key, facts, contract=contract)
    actual = resolution.value if resolution.is_resolved else None

    # 1. Handle missing/null facts (treat empty string as UNKNOWN for typed facts)
    if not resolution.is_resolved or actual is None or (isinstance(actual, str) and actual.strip() == "" and operator not in ("eq", "neq")):
        if operator == "exists":
            state: RuleState = "FAIL" if expected else "PASS"
            return RuleEvaluationResult(
                state=state,
                fact_key=fact_key,
                canonical_fact=resolution.canonical_key,
                resolution_source=resolution.resolution_source,
                operator=operator,
                expected_value=expected,
                actual_value=None,
                node_type="condition",
                reason_code=condition.reason_code or "FACT_MISSING",
                verification_status=condition.verification_status,
                source_fragment=condition.source_fragment,
                message=f"Missing fact: {fact_key}"
            )
        elif operator == "is_null":
            return RuleEvaluationResult(
                state="PASS",
                fact_key=fact_key,
                canonical_fact=resolution.canonical_key,
                resolution_source=resolution.resolution_source,
                operator=operator,
                expected_value=None,
                actual_value=None,
                node_type="condition",
                reason_code=condition.reason_code or "FACT_IS_NULL",
                verification_status=condition.verification_status,
                source_fragment=condition.source_fragment,
                message=f"{fact_key} is absent as required"
            )
        elif operator == "is_not_null":
            return RuleEvaluationResult(
                state="FAIL",
                fact_key=fact_key,
                canonical_fact=resolution.canonical_key,
                resolution_source=resolution.resolution_source,
                operator=operator,
                expected_value=None,
                actual_value=None,
                node_type="condition",
                reason_code=condition.reason_code or "FACT_IS_NULL",
                verification_status=condition.verification_status,
                source_fragment=condition.source_fragment,
                message=f"{fact_key} is required to be non-null"
            )

        return RuleEvaluationResult(
            state="UNKNOWN",
            fact_key=fact_key,
            canonical_fact=resolution.canonical_key,
            resolution_source=resolution.resolution_source,
            operator=operator,
            expected_value=expected,
            actual_value=None,
            node_type="condition",
            reason_code=condition.reason_code or "FACT_UNKNOWN",
            verification_status=condition.verification_status,
            source_fragment=condition.source_fragment,
            missing_facts=[fact_key],
            message=f"Required fact '{fact_key}' is not provided in profile"
        )

    # 2. Evaluate with actual value present
    state: RuleState = "FAIL"
    try:
        if operator == "eq":
            if isinstance(actual, bool) or (isinstance(expected, str) and expected.strip().lower() in ("true", "false")):
                norm_actual = str(actual).strip().lower() in ("true", "1", "yes") if isinstance(actual, (str, bool)) else actual
                norm_expected = str(expected).strip().lower() in ("true", "1", "yes") if isinstance(expected, (str, bool)) else expected
                state = "PASS" if norm_actual == norm_expected else "FAIL"
            elif isinstance(actual, str) and isinstance(expected, str):
                state = "PASS" if actual.strip().lower() == expected.strip().lower() else "FAIL"
            else:
                state = "PASS" if actual == expected else "FAIL"

        elif operator == "neq":
            if isinstance(actual, bool) or (isinstance(expected, str) and expected.strip().lower() in ("true", "false")):
                norm_actual = str(actual).strip().lower() in ("true", "1", "yes") if isinstance(actual, (str, bool)) else actual
                norm_expected = str(expected).strip().lower() in ("true", "1", "yes") if isinstance(expected, (str, bool)) else expected
                state = "PASS" if norm_actual != norm_expected else "FAIL"
            elif isinstance(actual, str) and isinstance(expected, str):
                state = "PASS" if actual.strip().lower() != expected.strip().lower() else "FAIL"
            else:
                state = "PASS" if actual != expected else "FAIL"

        elif operator == "gt":
            state = "PASS" if float(actual) > float(expected) else "FAIL"

        elif operator == "gte":
            state = "PASS" if float(actual) >= float(expected) else "FAIL"

        elif operator == "lt":
            state = "PASS" if float(actual) < float(expected) else "FAIL"

        elif operator == "lte":
            state = "PASS" if float(actual) <= float(expected) else "FAIL"

        elif operator == "between":
            if isinstance(expected, (list, tuple)) and len(expected) == 2:
                low, high = float(expected[0]), float(expected[1])
                state = "PASS" if (low <= float(actual) <= high) else "FAIL"
            else:
                state = "FAIL"

        elif operator == "in":
            if isinstance(expected, (list, tuple, set)):
                norm_expected = [str(x).strip().lower() for x in expected]
                if "all" in norm_expected:
                    state = "PASS"
                else:
                    state = "PASS" if str(actual).strip().lower() in norm_expected else "FAIL"
            elif isinstance(expected, str):
                state = "PASS" if str(actual).strip().lower() == expected.strip().lower() or expected.strip().lower() == "all" else "FAIL"
            else:
                state = "FAIL"

        elif operator == "not_in":
            if isinstance(expected, (list, tuple, set)):
                norm_expected = [str(x).strip().lower() for x in expected]
                state = "PASS" if str(actual).strip().lower() not in norm_expected else "FAIL"
            else:
                state = "PASS" if str(actual).strip().lower() != str(expected).strip().lower() else "FAIL"

        elif operator == "contains":
            if isinstance(actual, (list, tuple, set)):
                state = "PASS" if expected in actual else "FAIL"
            elif isinstance(actual, str):
                state = "PASS" if str(expected).lower() in actual.lower() else "FAIL"
            else:
                state = "FAIL"

        elif operator == "exists":
            state = "PASS" if expected else "FAIL"

        elif operator == "is_null":
            state = "PASS" if actual is None else "FAIL"

        elif operator == "is_not_null":
            state = "PASS" if actual is not None else "FAIL"

    except (ValueError, TypeError):
        state = "FAIL"

    message = ""
    if state == "PASS":
        message = f"{fact_key} ({actual}) satisfies condition ({operator} {expected})"
    elif state == "FAIL":
        message = f"{fact_key} ({actual}) does not satisfy condition ({operator} {expected})"
    else:
        message = f"{fact_key} is unknown"

    return RuleEvaluationResult(
        state=state,
        fact_key=fact_key,
        canonical_fact=resolution.canonical_key,
        resolution_source=resolution.resolution_source,
        operator=operator,
        expected_value=expected,
        actual_value=actual,
        node_type="condition",
        reason_code=condition.reason_code or f"{fact_key.upper()}_{state}",
        verification_status=condition.verification_status,
        source_fragment=condition.source_fragment,
        message=message
    )


def evaluate_rule_node(
    node: Union[RuleNode, Dict[str, Any]],
    facts: Dict[str, Any],
    contract: Optional[Dict[str, Any]] = None
) -> RuleEvaluationResult:
    """
    Recursively evaluates any RuleNode (ConditionNode, AllNode, AnyNode, NotNode)
    using deterministic 4-state Kleene multi-valued logic and generic schema resolution.
    """
    if isinstance(node, dict):
        node_type = node.get("type", "condition")
        if node_type == "condition":
            node = ConditionNode(**node)
        elif node_type == "all":
            node = AllNode(**node)
        elif node_type == "any":
            node = AnyNode(**node)
        elif node_type == "not":
            node = NotNode(**node)
        else:
            raise ValueError(f"Unrecognized node type: {node_type}")

    # 1. Atomic Condition
    if isinstance(node, ConditionNode):
        return evaluate_condition(node, facts, contract=contract)

    # 2. Conjunction (ALL)
    elif isinstance(node, AllNode):
        child_results: List[RuleEvaluationResult] = []
        missing_facts: List[str] = []
        has_fail = False
        has_unknown = False
        has_pass = False
        all_na = True

        for child in node.all:
            res = evaluate_rule_node(child, facts, contract=contract)
            child_results.append(res)
            if res.state == "FAIL":
                has_fail = True
            elif res.state == "UNKNOWN":
                has_unknown = True
            elif res.state == "PASS":
                has_pass = True

            if res.state != "NOT_APPLICABLE":
                all_na = False

            for mf in res.missing_facts:
                if mf not in missing_facts:
                    missing_facts.append(mf)


        if has_fail:
            overall_state: RuleState = "FAIL"
            msg = "One or more required conditions failed in 'all' conjunction"
        elif has_unknown:
            overall_state = "UNKNOWN"
            msg = "Information required for one or more conditions in 'all' conjunction"
        elif all_na:
            overall_state = "NOT_APPLICABLE"
            msg = "All conditions in 'all' conjunction are not applicable to applicant"
        else:
            overall_state = "PASS"
            msg = "All applicable conditions in 'all' conjunction satisfied"

        return RuleEvaluationResult(
            state=overall_state,
            node_type="all",
            reason_code=node.reason_code or f"ALL_{overall_state}",
            message=msg,
            children=child_results,
            missing_facts=missing_facts
        )

    # 3. Disjunction (ANY)
    # Kleene logic for OR with NOT_APPLICABLE:
    # - If ANY child is PASS -> PASS
    # - Else if ANY child is UNKNOWN -> UNKNOWN
    # - Else if ALL children are NOT_APPLICABLE -> NOT_APPLICABLE
    # - Else (all remaining are FAIL) -> FAIL
    elif isinstance(node, AnyNode):
        child_results = []
        missing_facts = []
        has_pass = False
        has_unknown = False
        all_na = True

        for child in node.any:
            res = evaluate_rule_node(child, facts, contract=contract)
            child_results.append(res)
            if res.state == "PASS":
                has_pass = True
            elif res.state == "UNKNOWN":
                has_unknown = True

            if res.state != "NOT_APPLICABLE":
                all_na = False

            for mf in res.missing_facts:
                if mf not in missing_facts:
                    missing_facts.append(mf)

        if has_pass:
            overall_state = "PASS"
            msg = "At least one qualifying condition satisfied in 'any' disjunction"
            missing_facts = []
        elif has_unknown:
            overall_state = "UNKNOWN"
            msg = "Needs additional information to check remaining alternate qualifying conditions"
        elif all_na:
            overall_state = "NOT_APPLICABLE"
            msg = "None of the alternate criteria in 'any' disjunction are applicable"
            missing_facts = []
        else:
            overall_state = "FAIL"
            msg = "None of the alternate conditions in 'any' disjunction were met"
            missing_facts = []

        return RuleEvaluationResult(
            state=overall_state,
            node_type="any",
            reason_code=node.reason_code or f"ANY_{overall_state}",
            message=msg,
            children=child_results,
            missing_facts=missing_facts
        )

    # 4. Negation (NOT)
    # Kleene logic for NOT:
    # - NOT PASS -> FAIL
    # - NOT FAIL -> PASS
    # - NOT UNKNOWN -> UNKNOWN
    # - NOT NOT_APPLICABLE -> NOT_APPLICABLE
    elif isinstance(node, NotNode):
        child_res = evaluate_rule_node(node.invert, facts, contract=contract)

        if child_res.state == "PASS":
            inv_state: RuleState = "FAIL"
            inv_msg = f"Disqualification criteria met: {child_res.message}"
        elif child_res.state == "FAIL":
            inv_state = "PASS"
            inv_msg = f"Passed negative condition: {child_res.message}"
        elif child_res.state == "UNKNOWN":
            inv_state = "UNKNOWN"
            inv_msg = f"Information needed to verify negative criteria: {child_res.message}"
        else:
            inv_state = "NOT_APPLICABLE"
            inv_msg = child_res.message

        return RuleEvaluationResult(
            state=inv_state,
            node_type="not",
            reason_code=node.reason_code or f"NOT_{inv_state}",
            message=inv_msg,
            children=[child_res],
            missing_facts=child_res.missing_facts
        )

    raise ValueError(f"Unknown node type: {type(node)}")
