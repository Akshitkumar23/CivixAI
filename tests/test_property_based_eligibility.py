"""
Property-based and invariant tests for CivixAI deterministic rule engine.
Tests Kleene 3-valued logic (PASS, FAIL, UNKNOWN), composite nodes (All, Any, Not),
and handles missing or contradictory profile facts.
"""
import pytest
from hypothesis import given, strategies as st, settings

from services.core.rules.schema import ConditionNode, AllNode, AnyNode, NotNode, RuleEvaluationResult
from services.core.rules.evaluator import evaluate_condition, evaluate_rule_node


class TestRuleEngineBasics:
    """Deterministic validation of atomic condition evaluation."""

    def test_eq_condition_pass_and_fail(self):
        cond = ConditionNode(fact="person.age", operator="eq", value=25)
        # Match
        res = evaluate_condition(cond, {"person.age": 25})
        assert res.state == "PASS"
        assert res.missing_facts == []

        # Mismatch
        res_fail = evaluate_condition(cond, {"person.age": 30})
        assert res_fail.state == "FAIL"

    def test_missing_fact_yields_unknown(self):
        cond = ConditionNode(fact="household.annual_income", operator="lte", value=250000)
        res = evaluate_condition(cond, {})
        assert res.state == "UNKNOWN"
        assert "household.annual_income" in res.missing_facts
        assert res.reason_code in ("FACT_UNKNOWN", "FACT_MISSING")

    def test_empty_string_yields_unknown_for_numeric_conditions(self):
        cond = ConditionNode(fact="household.annual_income", operator="lte", value=100000)
        res = evaluate_condition(cond, {"household.annual_income": "   "})
        assert res.state == "UNKNOWN"
        assert "household.annual_income" in res.missing_facts

    def test_comparison_operators(self):
        gt_node = ConditionNode(fact="person.age", operator="gt", value=18)
        assert evaluate_condition(gt_node, {"person.age": 19}).state == "PASS"
        assert evaluate_condition(gt_node, {"person.age": 18}).state == "FAIL"
        assert evaluate_condition(gt_node, {"person.age": 17}).state == "FAIL"

        gte_node = ConditionNode(fact="person.age", operator="gte", value=18)
        assert evaluate_condition(gte_node, {"person.age": 18}).state == "PASS"

        lt_node = ConditionNode(fact="person.age", operator="lt", value=60)
        assert evaluate_condition(lt_node, {"person.age": 59}).state == "PASS"
        assert evaluate_condition(lt_node, {"person.age": 60}).state == "FAIL"

        lte_node = ConditionNode(fact="person.age", operator="lte", value=60)
        assert evaluate_condition(lte_node, {"person.age": 60}).state == "PASS"

    def test_in_operator(self):
        cond = ConditionNode(fact="location.state", operator="in", value=["Maharashtra", "Gujarat", "Karnataka"])
        assert evaluate_condition(cond, {"location.state": "Maharashtra"}).state == "PASS"
        assert evaluate_condition(cond, {"location.state": "Delhi"}).state == "FAIL"
        assert evaluate_condition(cond, {}).state == "UNKNOWN"

    def test_exists_and_is_null_operators(self):
        cond_exists = ConditionNode(fact="applicant.caste_certificate_number", operator="exists", value=True)
        assert evaluate_condition(cond_exists, {"applicant.caste_certificate_number": "ABC/123"}).state == "PASS"
        assert evaluate_condition(cond_exists, {}).state == "FAIL"

        cond_null = ConditionNode(fact="enterprise.gstin", operator="is_null", value=None)
        assert evaluate_condition(cond_null, {}).state == "PASS"
        assert evaluate_condition(cond_null, {"enterprise.gstin": "27AAPFU0939F1ZV"}).state == "FAIL"


class TestKleeneLogicInvariants:
    """Verifies Kleene 3-valued logic invariants for conjunctions and disjunctions."""

    def test_all_conjunction_pass(self):
        node = AllNode(all=[
            ConditionNode(fact="person.age", operator="gte", value=18),
            ConditionNode(fact="household.annual_income", operator="lte", value=300000)
        ])
        res = evaluate_rule_node(node, {"person.age": 22, "household.annual_income": 200000})
        assert res.state == "PASS"

    def test_all_conjunction_fail_dominates_unknown(self):
        # In Kleene logic: FALSE AND UNKNOWN is FALSE
        node = AllNode(all=[
            ConditionNode(fact="person.age", operator="gte", value=18),  # FAIL: age is 15
            ConditionNode(fact="missing.fact.key", operator="eq", value="required")  # UNKNOWN
        ])
        res = evaluate_rule_node(node, {"person.age": 15})
        assert res.state == "FAIL"

    def test_all_conjunction_unknown_when_no_fail(self):
        # PASS AND UNKNOWN is UNKNOWN
        node = AllNode(all=[
            ConditionNode(fact="person.age", operator="gte", value=18),  # PASS
            ConditionNode(fact="applicant.occupation", operator="eq", value="farmer")  # UNKNOWN
        ])
        res = evaluate_rule_node(node, {"person.age": 25})
        assert res.state == "UNKNOWN"
        assert "applicant.occupation" in res.missing_facts

    def test_any_disjunction_pass_dominates_unknown(self):
        # In Kleene logic: TRUE OR UNKNOWN is TRUE
        node = AnyNode(any=[
            ConditionNode(fact="person.age", operator="gte", value=60),  # PASS: age 65
            ConditionNode(fact="missing.income", operator="lte", value=50000)  # UNKNOWN
        ])
        res = evaluate_rule_node(node, {"person.age": 65})
        assert res.state == "PASS"

    def test_any_disjunction_unknown_when_no_pass(self):
        # FALSE OR UNKNOWN is UNKNOWN
        node = AnyNode(any=[
            ConditionNode(fact="person.age", operator="gte", value=60),  # FAIL: age 30
            ConditionNode(fact="person.disability_status", operator="eq", value=True)  # UNKNOWN
        ])
        res = evaluate_rule_node(node, {"person.age": 30})
        assert res.state == "UNKNOWN"
        assert "person.disability_status" in res.missing_facts

    def test_any_disjunction_all_fail(self):
        node = AnyNode(any=[
            ConditionNode(fact="person.age", operator="gte", value=60),
            ConditionNode(fact="person.age", operator="lte", value=10)
        ])
        res = evaluate_rule_node(node, {"person.age": 25})
        assert res.state == "FAIL"

    def test_not_negation_invariants(self):
        pass_cond = ConditionNode(fact="person.age", operator="gte", value=18)
        not_node = NotNode(invert=pass_cond)

        # NOT PASS -> FAIL
        assert evaluate_rule_node(not_node, {"person.age": 20}).state == "FAIL"

        # NOT FAIL -> PASS
        assert evaluate_rule_node(not_node, {"person.age": 15}).state == "PASS"

        # NOT UNKNOWN -> UNKNOWN
        assert evaluate_rule_node(not_node, {}).state == "UNKNOWN"


class TestPropertyBasedInvariants:
    """Hypothesis-driven generative invariant tests."""

    @given(st.integers(min_value=0, max_value=120), st.integers(min_value=18, max_value=60))
    @settings(max_examples=50)
    def test_age_threshold_monotonicity(self, applicant_age: int, threshold: int):
        gte_node = ConditionNode(fact="person.age", operator="gte", value=threshold)
        res = evaluate_condition(gte_node, {"person.age": applicant_age})

        if applicant_age >= threshold:
            assert res.state == "PASS"
        else:
            assert res.state == "FAIL"

    @given(st.dictionaries(keys=st.text(min_size=1, max_size=20), values=st.integers()))
    @settings(max_examples=30)
    def test_deterministic_evaluation(self, facts):
        node = ConditionNode(fact="person.age", operator="gte", value=21)
        res1 = evaluate_condition(node, facts)
        res2 = evaluate_condition(node, facts)
        assert res1.state == res2.state
        assert res1.missing_facts == res2.missing_facts

    @given(st.booleans(), st.booleans())
    def test_kleene_boolean_and_or_duality(self, a_val: bool, b_val: bool):
        facts = {"fact.a": a_val, "fact.b": b_val}
        cond_a = ConditionNode(fact="fact.a", operator="eq", value=True)
        cond_b = ConditionNode(fact="fact.b", operator="eq", value=True)

        all_node = AllNode(all=[cond_a, cond_b])
        res_all = evaluate_rule_node(all_node, facts)

        any_node = AnyNode(any=[cond_a, cond_b])
        res_any = evaluate_rule_node(any_node, facts)

        if a_val and b_val:
            assert res_all.state == "PASS"
            assert res_any.state == "PASS"
        elif not a_val and not b_val:
            assert res_all.state == "FAIL"
            assert res_any.state == "FAIL"
        else:
            assert res_all.state == "FAIL"
            assert res_any.state == "PASS"
