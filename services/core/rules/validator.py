"""
Rule Validator Engine
Validates rule condition ASTs against canonical fact catalogue, operator types,
range boundaries, and maximum tree recursion depth.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import ValidationError

from services.core.facts.registry import FACT_CATALOGUE
from .schema import (
    RuleNode, ConditionNode, AllNode, AnyNode, NotNode,
    RuleOperator
)

ALLOWED_OPERATORS = {
    "eq", "neq", "gt", "gte", "lt", "lte",
    "between", "in", "not_in", "contains", "exists",
    "is_null", "is_not_null"
}

NUMERIC_OPERATORS = {"gt", "gte", "lt", "lte", "between"}


class RuleValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_rule_node(
    node: Union[RuleNode, Dict[str, Any]],
    max_depth: int = 5,
    current_depth: int = 1,
    strict: bool = False
) -> List[str]:
    """
    Recursively validates a rule AST node.
    Returns a list of validation error messages.
    If strict=True and errors exist, raises RuleValidationError.
    """
    errors: List[str] = []

    if current_depth > max_depth:
        errors.append(f"Rule recursion depth {current_depth} exceeds maximum limit of {max_depth}")
        if strict and errors:
            raise RuleValidationError(errors)
        return errors

    # Convert dict to Pydantic model if dict is passed
    if isinstance(node, dict):
        node_type = node.get("type", "condition")
        try:
            if node_type == "condition":
                node = ConditionNode(**node)
            elif node_type == "all":
                node = AllNode(**node)
            elif node_type == "any":
                node = AnyNode(**node)
            elif node_type == "not":
                node = NotNode(**node)
            else:
                errors.append(f"Unrecognized node type '{node_type}' at depth {current_depth}")
                if strict:
                    raise RuleValidationError(errors)
                return errors
        except ValidationError as e:
            errors.append(f"Schema validation failed at depth {current_depth}: {e}")
            if strict:
                raise RuleValidationError(errors)
            return errors

    # 1. ConditionNode Validation
    if isinstance(node, ConditionNode):
        fact_key = node.fact
        operator = node.operator
        val = node.value

        # Check operator validity
        if operator not in ALLOWED_OPERATORS:
            errors.append(f"Unknown operator '{operator}' for fact '{fact_key}'")

        # Check fact existence in canonical catalogue
        if fact_key not in FACT_CATALOGUE:
            errors.append(f"Unknown fact key '{fact_key}' not registered in canonical FACT_CATALOGUE")
        else:
            fact_def = FACT_CATALOGUE[fact_key]
            # Operator type compatibility
            if operator in NUMERIC_OPERATORS and fact_def.type not in ("integer", "float"):
                errors.append(
                    f"Numeric operator '{operator}' cannot be applied to fact '{fact_key}' of type '{fact_def.type}'"
                )

            # Check between range validity
            if operator == "between":
                if not isinstance(val, (list, tuple)) or len(val) != 2:
                    errors.append(f"Operator 'between' requires a list/tuple of [min, max], got: {val}")
                else:
                    try:
                        low, high = float(val[0]), float(val[1])
                        if low > high:
                            errors.append(f"Invalid range for 'between': min ({low}) cannot be greater than max ({high})")
                    except (ValueError, TypeError):
                        errors.append(f"Operator 'between' boundaries must be numeric, got: {val}")

            # Check enum validity if allowed_values specified
            if fact_def.type == "enum" and fact_def.allowed_values and val is not None:
                allowed_norm = [str(x).strip().lower() for x in fact_def.allowed_values]
                if operator == "eq":
                    if str(val).strip().lower() not in allowed_norm and str(val).strip().lower() != "all":
                        errors.append(
                            f"Value '{val}' for enum fact '{fact_key}' is not in allowed values: {fact_def.allowed_values}"
                        )
                elif operator in ("in", "not_in"):
                    if isinstance(val, (list, tuple, set)):
                        for item in val:
                            if str(item).strip().lower() not in allowed_norm and str(item).strip().lower() != "all":
                                errors.append(
                                    f"Value '{item}' in list for enum fact '{fact_key}' is not in allowed values: {fact_def.allowed_values}"
                                )

    # 2. AllNode Validation
    elif isinstance(node, AllNode):
        if not node.all:
            errors.append(f"Conjunction group 'all' at depth {current_depth} must contain at least one condition")
        else:
            for child in node.all:
                child_errs = validate_rule_node(
                    child, max_depth=max_depth, current_depth=current_depth + 1, strict=False
                )
                errors.extend(child_errs)

    # 3. AnyNode Validation
    elif isinstance(node, AnyNode):
        if not node.any:
            errors.append(f"Disjunction group 'any' at depth {current_depth} must contain at least one condition")
        else:
            for child in node.any:
                child_errs = validate_rule_node(
                    child, max_depth=max_depth, current_depth=current_depth + 1, strict=False
                )
                errors.extend(child_errs)

    # 4. NotNode Validation
    elif isinstance(node, NotNode):
        child_errs = validate_rule_node(
            node.invert, max_depth=max_depth, current_depth=current_depth + 1, strict=False
        )
        errors.extend(child_errs)

    if strict and errors:
        raise RuleValidationError(errors)

    return errors
