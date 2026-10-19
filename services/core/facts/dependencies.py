"""
Fact Dependency Graph and Adaptive Questionnaire Prioritizer.
Extracts fact requirements from declarative rules, identifies mandatory vs branch facts,
and computes fact discrimination scores for optimal progressive profiling.
"""
from typing import Any, Dict, List, Set, Optional, Union
from services.core.facts.registry import FACT_CATALOGUE
from services.core.rules.schema import (
    RuleNode, ConditionNode, AllNode, AnyNode, NotNode
)

def extract_facts_from_ast(
    node: Union[RuleNode, Dict[str, Any]],
    in_disjunction: bool = False
) -> Dict[str, Set[str]]:
    """
    Recursively extracts facts from an AST node, categorizing them as:
    - mandatory: unconditionally required in conjunctions.
    - branch: conditionally relevant in disjunction (OR) alternatives.
    """
    mandatory: Set[str] = set()
    branch: Set[str] = set()

    if isinstance(node, dict):
        node_type = node.get("type", "condition")
        if node_type == "condition":
            fact = node.get("fact")
            if fact:
                if in_disjunction or not node.get("mandatory", True):
                    branch.add(fact)
                else:
                    mandatory.add(fact)
        elif node_type == "all":
            for child in node.get("all", []):
                sub = extract_facts_from_ast(child, in_disjunction=in_disjunction)
                mandatory.update(sub["mandatory"])
                branch.update(sub["branch"])
        elif node_type == "any":
            for child in node.get("any", []):
                sub = extract_facts_from_ast(child, in_disjunction=True)
                # In an OR branch, all child facts become branch facts
                branch.update(sub["mandatory"])
                branch.update(sub["branch"])
        elif node_type == "not":
            child = node.get("invert") or node.get("not")
            if child:
                sub = extract_facts_from_ast(child, in_disjunction=in_disjunction)
                mandatory.update(sub["mandatory"])
                branch.update(sub["branch"])
        return {"mandatory": mandatory, "branch": branch}

    if isinstance(node, ConditionNode):
        if in_disjunction or not node.mandatory:
            branch.add(node.fact)
        else:
            mandatory.add(node.fact)
    elif isinstance(node, AllNode):
        for child in node.all:
            sub = extract_facts_from_ast(child, in_disjunction=in_disjunction)
            mandatory.update(sub["mandatory"])
            branch.update(sub["branch"])
    elif isinstance(node, AnyNode):
        for child in node.any:
            sub = extract_facts_from_ast(child, in_disjunction=True)
            branch.update(sub["mandatory"])
            branch.update(sub["branch"])
    elif isinstance(node, NotNode):
        sub = extract_facts_from_ast(node.invert, in_disjunction=in_disjunction)
        mandatory.update(sub["mandatory"])
        branch.update(sub["branch"])

    return {"mandatory": mandatory, "branch": branch}


class FactDependencyEngine:
    """
    Builds inverted fact indices across all active schemes and recommends
    the highest-yield questions for progressive user profiling.
    """
    def __init__(self, schemes_metadata: List[Dict[str, Any]]):
        self.schemes_metadata = schemes_metadata
        self.fact_to_schemes: Dict[str, Set[str]] = {}
        self.mandatory_fact_to_schemes: Dict[str, Set[str]] = {}
        self._build_index()

    def _build_index(self):
        for s in self.schemes_metadata:
            scheme_id = s.get("scheme_id", "")
            rules = s.get("rules", [])
            for r in rules:
                rule_expr = getattr(r, "rule_expression", None)
                if rule_expr:
                    import json
                    try:
                        parsed = json.loads(rule_expr) if isinstance(rule_expr, str) else rule_expr
                        extracted = extract_facts_from_ast(parsed)
                        for f in extracted["mandatory"]:
                            self.fact_to_schemes.setdefault(f, set()).add(scheme_id)
                            self.mandatory_fact_to_schemes.setdefault(f, set()).add(scheme_id)
                        for f in extracted["branch"]:
                            self.fact_to_schemes.setdefault(f, set()).add(scheme_id)
                        continue
                    except Exception:
                        pass

                # If r is an AST node (ConditionNode, AllNode, AnyNode, NotNode)
                if isinstance(r, (ConditionNode, AllNode, AnyNode, NotNode)):
                    extracted = extract_facts_from_ast(r)
                    for f in extracted["mandatory"]:
                        self.fact_to_schemes.setdefault(f, set()).add(scheme_id)
                        self.mandatory_fact_to_schemes.setdefault(f, set()).add(scheme_id)
                    for f in extracted["branch"]:
                        self.fact_to_schemes.setdefault(f, set()).add(scheme_id)
                    continue

                # Fallback to standard flat rule (DB model or dict)
                fact_key = getattr(r, "fact", None) or getattr(r, "fact_key", None)
                if not fact_key and isinstance(r, dict):
                    fact_key = r.get("fact") or r.get("fact_key")

                if fact_key:
                    self.fact_to_schemes.setdefault(fact_key, set()).add(scheme_id)
                    is_mand = getattr(r, "mandatory", True) if not isinstance(r, dict) else r.get("mandatory", True)
                    if is_mand:
                        self.mandatory_fact_to_schemes.setdefault(fact_key, set()).add(scheme_id)

    def get_schemes_requiring_fact(self, fact_key: str) -> Set[str]:
        return self.fact_to_schemes.get(fact_key, set())

    def rank_missing_facts(
        self,
        current_facts: Dict[str, Any],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Ranks currently missing facts by discrimination power (how many schemes depend on them).
        """
        unanswered_facts = []
        for fact_key, scheme_set in self.fact_to_schemes.items():
            if fact_key not in current_facts or current_facts[fact_key] is None:
                fact_def = FACT_CATALOGUE.get(fact_key)
                unanswered_facts.append({
                    "fact_key": fact_key,
                    "dependent_schemes_count": len(scheme_set),
                    "mandatory_schemes_count": len(self.mandatory_fact_to_schemes.get(fact_key, set())),
                    "type": fact_def.type if fact_def else "string",
                    "description": fact_def.description if fact_def else "",
                    "sensitivity": fact_def.sensitivity if fact_def else "normal",
                    "allowed_values": fact_def.allowed_values if fact_def else None,
                    "unit": fact_def.unit if fact_def else None,
                })

        # Rank by: 1) mandatory schemes count desc, 2) total dependent schemes count desc
        unanswered_facts.sort(
            key=lambda x: (x["mandatory_schemes_count"], x["dependent_schemes_count"]),
            reverse=True
        )
        return unanswered_facts[:top_n]
