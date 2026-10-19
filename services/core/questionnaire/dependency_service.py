"""
Questionnaire Dependency Service
Traverses candidate schemes and their rule ASTs with Kleene short-circuiting to identify
strictly relevant unresolved facts for still-viable schemes.
Zero scheme-specific logic.
"""
from typing import Any, Dict, List, Set, Tuple
from services.core.rules.schema import (
    RuleNode, ConditionNode, AllNode, AnyNode, NotNode,
    RuleEvaluationResult
)
from services.core.rules.evaluator import evaluate_rule_node, evaluate_condition

def _analyze_ast_dependencies(
    node: RuleNode,
    facts: Dict[str, Any]
) -> Tuple[RuleEvaluationResult, Set[str], Set[str]]:
    """
    Evaluates an AST node against current facts and returns:
    - evaluation_result
    - mandatory_unresolved_facts (facts required to satisfy this viable node)
    - branch_unresolved_facts (facts from OR branches)

    Implements strict Kleene short-circuiting:
    - ALL: If any verified mandatory child fails, prunes remaining child facts.
    - ANY: If any child passes, prunes all alternative branch facts.
    """
    if isinstance(node, ConditionNode):
        eval_res = evaluate_condition(node, facts)
        if eval_res.state == "UNKNOWN":
            if node.mandatory:
                return eval_res, {node.fact}, set()
            else:
                return eval_res, set(), {node.fact}
        return eval_res, set(), set()

    elif isinstance(node, AllNode):
        child_results = []
        mandatory_unresolved: Set[str] = set()
        branch_unresolved: Set[str] = set()
        has_verified_fail = False
        has_unknown = False

        for child in node.all:
            res, mand, br = _analyze_ast_dependencies(child, facts)
            child_results.append(res)
            if res.state == "FAIL" and res.verification_status in ("source_verified", "human_reviewed"):
                has_verified_fail = True
            elif res.state == "UNKNOWN":
                has_unknown = True
                mandatory_unresolved.update(mand)
                branch_unresolved.update(br)

        # Short-circuit: If a verified mandatory condition failed, this ALL node cannot pass.
        # Prune all unresolved facts because this branch is dead.
        if has_verified_fail:
            eval_res = RuleEvaluationResult(
                state="FAIL",
                node_type="all",
                message="Disqualified by verified condition",
                children=child_results
            )
            return eval_res, set(), set()

        overall_state = "UNKNOWN" if has_unknown else ("FAIL" if any(r.state == "FAIL" for r in child_results) else "PASS")
        eval_res = RuleEvaluationResult(
            state=overall_state,
            node_type="all",
            children=child_results
        )
        return eval_res, mandatory_unresolved, branch_unresolved

    elif isinstance(node, AnyNode):
        child_results = []
        branch_unresolved: Set[str] = set()
        has_pass = False

        for child in node.any:
            res, mand, br = _analyze_ast_dependencies(child, facts)
            child_results.append(res)
            if res.state == "PASS":
                has_pass = True
            elif res.state == "UNKNOWN":
                branch_unresolved.update(mand)
                branch_unresolved.update(br)

        # Short-circuit: If any alternate branch has passed, this ANY node is satisfied.
        # Prune all unresolved facts from remaining alternate branches.
        if has_pass:
            eval_res = RuleEvaluationResult(
                state="PASS",
                node_type="any",
                message="Qualified via alternate branch",
                children=child_results
            )
            return eval_res, set(), set()

        all_fail = all(r.state == "FAIL" for r in child_results)
        overall_state = "FAIL" if all_fail else "UNKNOWN"
        eval_res = RuleEvaluationResult(
            state=overall_state,
            node_type="any",
            children=child_results
        )
        return eval_res, set(), branch_unresolved

    elif isinstance(node, NotNode):
        res, mand, br = _analyze_ast_dependencies(node.invert, facts)
        if res.state == "PASS":
            inv_state = "FAIL"
            # Disqualified by NOT node -> prune facts
            return RuleEvaluationResult(state="FAIL", node_type="not", children=[res]), set(), set()
        elif res.state == "FAIL":
            inv_state = "PASS"
            return RuleEvaluationResult(state="PASS", node_type="not", children=[res]), set(), set()
        else:
            return RuleEvaluationResult(state="UNKNOWN", node_type="not", children=[res]), mand, br

    return RuleEvaluationResult(state="UNKNOWN"), set(), set()


class QuestionDependencyService:
    """
    Evaluates candidate schemes against current profile facts and extracts
    strictly relevant unresolved facts with full short-circuit pruning.
    """
    def __init__(self, candidates: List[Dict[str, Any]]):
        self.candidates = candidates

    def get_unresolved_dependencies(
        self,
        current_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        unresolved_fact_to_schemes: Dict[str, Set[str]] = {}
        mandatory_facts: Set[str] = set()
        branch_facts: Set[str] = set()

        eligible_schemes: List[str] = []
        needs_info_schemes: List[str] = []
        not_eligible_schemes: List[str] = []
        needs_verification_schemes: List[str] = []

        for candidate in self.candidates:
            scheme_id = candidate["scheme_id"]
            db_rules = candidate.get("rules", [])

            scheme_viable = True
            scheme_has_unknown = False
            scheme_has_unverified_fail = False

            scheme_mand_facts: Set[str] = set()
            scheme_branch_facts: Set[str] = set()

            for r in db_rules:
                # If r is already an AST Node
                if isinstance(r, (ConditionNode, AllNode, AnyNode, NotNode)):
                    eval_res, m_facts, b_facts = _analyze_ast_dependencies(r, current_facts)
                    if eval_res.state == "FAIL":
                        if r.verification_status in ("source_verified", "human_reviewed") or eval_res.verification_status in ("source_verified", "human_reviewed"):
                            scheme_viable = False
                            break
                        else:
                            scheme_has_unverified_fail = True
                    elif eval_res.state == "UNKNOWN":
                        scheme_has_unknown = True
                        scheme_mand_facts.update(m_facts)
                        scheme_branch_facts.update(b_facts)
                    continue

                rule_expr = getattr(r, "rule_expression", None)
                if rule_expr:
                    import json
                    try:
                        parsed_node = json.loads(rule_expr) if isinstance(rule_expr, str) else rule_expr
                        eval_res, m_facts, b_facts = _analyze_ast_dependencies(parsed_node, current_facts)
                        if eval_res.state == "FAIL":
                            if eval_res.verification_status in ("source_verified", "human_reviewed"):
                                scheme_viable = False
                                break
                            else:
                                scheme_has_unverified_fail = True
                        elif eval_res.state == "UNKNOWN":
                            scheme_has_unknown = True
                            scheme_mand_facts.update(m_facts)
                            scheme_branch_facts.update(b_facts)
                        continue
                    except Exception:
                        pass

                # Flat rule evaluation
                fact_key = getattr(r, "fact", None) or getattr(r, "fact_key", None)
                if not fact_key:
                    continue

                raw_val = getattr(r, "value", None) if getattr(r, "value", None) is not None else getattr(r, "expected_value", None)
                parsed_val = raw_val
                if isinstance(raw_val, str) and raw_val.startswith("[") and raw_val.endswith("]"):
                    import json
                    try:
                        parsed_val = json.loads(raw_val.replace("'", '"'))
                    except Exception:
                        parsed_val = [x.strip().strip("'").strip('"') for x in raw_val[1:-1].split(",")]

                cond = ConditionNode(
                    fact=fact_key,
                    operator=getattr(r, "operator", "eq"),
                    value=parsed_val,
                    mandatory=getattr(r, "mandatory", True),
                    verification_status=getattr(r, "verification_status", "imported_unverified") or "imported_unverified"
                )
                res, m_facts, b_facts = _analyze_ast_dependencies(cond, current_facts)
                if res.state == "FAIL":
                    if cond.verification_status in ("source_verified", "human_reviewed"):
                        scheme_viable = False
                        break
                    else:
                        scheme_has_unverified_fail = True
                elif res.state == "UNKNOWN":
                    scheme_has_unknown = True
                    scheme_mand_facts.update(m_facts)
                    scheme_branch_facts.update(b_facts)

            if not scheme_viable:
                not_eligible_schemes.append(scheme_id)
            elif scheme_has_unknown:
                needs_info_schemes.append(scheme_id)
                # Only record facts for VIABLE schemes!
                for f in scheme_mand_facts:
                    unresolved_fact_to_schemes.setdefault(f, set()).add(scheme_id)
                    mandatory_facts.add(f)
                for f in scheme_branch_facts:
                    unresolved_fact_to_schemes.setdefault(f, set()).add(scheme_id)
                    branch_facts.add(f)
            elif scheme_has_unverified_fail:
                needs_verification_schemes.append(scheme_id)
            else:
                eligible_schemes.append(scheme_id)

        # Remove facts that are already answered in current_facts
        filtered_unresolved: Dict[str, Set[str]] = {
            f: schemes
            for f, schemes in unresolved_fact_to_schemes.items()
            if f not in current_facts or current_facts[f] is None
        }

        return {
            "unresolved_facts_by_scheme": filtered_unresolved,
            "mandatory_facts": mandatory_facts - set(current_facts.keys()),
            "branch_facts": branch_facts - set(current_facts.keys()),
            "eligible_schemes": eligible_schemes,
            "needs_info_schemes": needs_info_schemes,
            "not_eligible_schemes": not_eligible_schemes,
            "needs_verification_schemes": needs_verification_schemes,
            "total_viable_schemes": len(eligible_schemes) + len(needs_info_schemes) + len(needs_verification_schemes)
        }
