"""
Semantic Diff Engine
Computes structured, human-readable differences between active production SchemeVersion
and candidate machine-extracted drafts.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from services.core.database.models import SchemeVersion, EligibilityRule, Benefit, DocumentRequirement
from .extractor import CandidateExtraction

class StructuredDiff:
    def __init__(
        self,
        has_material_changes: bool,
        summary: str,
        rule_diffs: List[Dict[str, Any]],
        benefit_diffs: List[Dict[str, Any]],
        document_diffs: List[Dict[str, Any]]
    ):
        self.has_material_changes = has_material_changes
        self.summary = summary
        self.rule_diffs = rule_diffs
        self.benefit_diffs = benefit_diffs
        self.document_diffs = document_diffs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_material_changes": self.has_material_changes,
            "summary": self.summary,
            "rule_diffs": self.rule_diffs,
            "benefit_diffs": self.benefit_diffs,
            "document_diffs": self.document_diffs
        }

class DiffEngine:
    @staticmethod
    def compare(
        production_version: Optional[SchemeVersion],
        candidate: CandidateExtraction
    ) -> StructuredDiff:
        rule_diffs: List[Dict[str, Any]] = []
        benefit_diffs: List[Dict[str, Any]] = []
        document_diffs: List[Dict[str, Any]] = []
        changes_summary: List[str] = []

        if not production_version:
            # Brand new scheme candidate
            for r in candidate.rule_drafts:
                rule_diffs.append({
                    "fact_key": r["fact_key"],
                    "change_type": "added",
                    "old_value": None,
                    "new_value": f"{r['operator']} {r['expected_value']}",
                    "explanation": f"New rule added: {r['fact_key']} ({r['operator']} {r['expected_value']})",
                    "source_fragment": r.get("source_fragment")
                })
            for b in candidate.benefit_drafts:
                benefit_diffs.append({
                    "change_type": "added",
                    "old_value": None,
                    "new_value": f"₹{b.get('fixed_amount', 0):,.0f} ({b.get('frequency', 'yearly')})",
                    "explanation": f"New benefit: {b.get('description')}",
                    "source_fragment": b.get("source_fragment")
                })
            for d in candidate.document_drafts:
                document_diffs.append({
                    "change_type": "added",
                    "document_type": d["document_type"],
                    "explanation": f"New required document: {d['document_type']}",
                    "source_fragment": d.get("source_fragment")
                })

            return StructuredDiff(
                has_material_changes=True,
                summary=f"New scheme proposal with {len(candidate.rule_drafts)} rules and {len(candidate.document_drafts)} document requirements.",
                rule_diffs=rule_diffs,
                benefit_diffs=benefit_diffs,
                document_diffs=document_diffs
            )

        # Compare existing production rules
        prod_rules = {r.fact_key: r for r in production_version.rules}
        cand_rules = {r["fact_key"]: r for r in candidate.rule_drafts}

        # Check modified & unchanged & added
        for fkey, c_rule in cand_rules.items():
            if fkey in prod_rules:
                p_rule = prod_rules[fkey]
                p_val = f"{p_rule.operator} {p_rule.expected_value}"
                c_val = f"{c_rule['operator']} {c_rule['expected_value']}"

                if p_val != c_val:
                    explanation = f"{fkey} criteria changed from '{p_val}' to '{c_val}'"
                    rule_diffs.append({
                        "fact_key": fkey,
                        "change_type": "modified",
                        "old_value": p_val,
                        "new_value": c_val,
                        "explanation": explanation,
                        "source_fragment": c_rule.get("source_fragment")
                    })
                    changes_summary.append(explanation)
                else:
                    rule_diffs.append({
                        "fact_key": fkey,
                        "change_type": "unchanged",
                        "old_value": p_val,
                        "new_value": c_val,
                        "explanation": f"{fkey} criteria confirmed unchanged",
                        "source_fragment": c_rule.get("source_fragment")
                    })
            else:
                c_val = f"{c_rule['operator']} {c_rule['expected_value']}"
                explanation = f"Added new rule: {fkey} ({c_val})"
                rule_diffs.append({
                    "fact_key": fkey,
                    "change_type": "added",
                    "old_value": None,
                    "new_value": c_val,
                    "explanation": explanation,
                    "source_fragment": c_rule.get("source_fragment")
                })
                changes_summary.append(explanation)

        # Check removed rules
        for fkey, p_rule in prod_rules.items():
            if fkey not in cand_rules:
                p_val = f"{p_rule.operator} {p_rule.expected_value}"
                explanation = f"Existing rule '{fkey}' ({p_val}) not present in candidate"
                rule_diffs.append({
                    "fact_key": fkey,
                    "change_type": "removed",
                    "old_value": p_val,
                    "new_value": None,
                    "explanation": explanation,
                    "source_fragment": p_rule.source_fragment
                })
                changes_summary.append(explanation)

        # Compare Document Requirements
        prod_docs = {d.document_type: d for d in production_version.documents}
        cand_docs = {d["document_type"]: d for d in candidate.document_drafts}

        for dtype, c_doc in cand_docs.items():
            if dtype not in prod_docs:
                explanation = f"Added required document: {dtype}"
                document_diffs.append({
                    "change_type": "added",
                    "document_type": dtype,
                    "explanation": explanation,
                    "source_fragment": c_doc.get("source_fragment")
                })
                changes_summary.append(explanation)

        for dtype in prod_docs:
            if dtype not in cand_docs:
                explanation = f"Removed required document: {dtype}"
                document_diffs.append({
                    "change_type": "removed",
                    "document_type": dtype,
                    "explanation": explanation,
                    "source_fragment": None
                })
                changes_summary.append(explanation)

        has_changes = any(r["change_type"] in ("added", "modified", "removed") for r in rule_diffs) or \
                      any(d["change_type"] in ("added", "removed") for d in document_diffs)

        summary_text = "; ".join(changes_summary) if changes_summary else "No eligibility or document differences detected."

        return StructuredDiff(
            has_material_changes=has_changes,
            summary=summary_text,
            rule_diffs=rule_diffs,
            benefit_diffs=benefit_diffs,
            document_diffs=document_diffs
        )

# Alias for MCP and core services binding
RuleDiffEngine = DiffEngine

