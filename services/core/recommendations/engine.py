import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from services.core.rules import (
    evaluate_condition, evaluate_rule_node, build_scheme_evaluation,
    ConditionNode, EvidenceCitation
)
from services.core.benefits import format_benefit_summary
from services.core.database.models import RecommendationRun, RecommendationItem, SourceConflict
from .candidate_service import CandidateService
from .ranker import calculate_rank_score

def _parse_doc_list(val: Any) -> List[str]:
    if not val:
        return []
    if isinstance(val, str):
        return [d.strip().lower() for d in val.split(",") if d.strip()]
    if isinstance(val, list):
        return [str(d).strip().lower() for d in val if d]
    if isinstance(val, dict):
        return [str(k).strip().lower() for k in val.keys()]
    return []

def calculate_document_readiness(
    doc_requirements: List[Any],
    facts: Dict[str, Any]
) -> tuple[float, List[Dict[str, Any]], str]:
    """
    Computes rigorous 7-state document readiness.
    Explicitly decoupled from government approval probability.
    """
    if not doc_requirements:
        return 1.0, [], "No document requirements specified for this scheme."

    declared = _parse_doc_list(facts.get("documents.available") or facts.get("documents_available"))
    uploaded = _parse_doc_list(facts.get("documents.uploaded") or facts.get("documents_uploaded"))
    parsed = _parse_doc_list(facts.get("documents.machine_parsed"))
    verified = _parse_doc_list(facts.get("documents.verified"))
    expired = _parse_doc_list(facts.get("documents.expired"))
    rejected = _parse_doc_list(facts.get("documents.rejected"))

    breakdown: List[Dict[str, Any]] = []
    scores: List[float] = []

    for req in doc_requirements:
        doc_name = getattr(req, "document_type", str(req))
        is_mand = getattr(req, "is_mandatory", True)
        name_lower = doc_name.lower()

        def matches(doc_list: List[str]) -> bool:
            return any(name_lower in d or d in name_lower for d in doc_list)

        if matches(expired):
            status = "expired_document"
            score = 0.0
            label = "Expired"
            notes = "Document validity period has expired; re-issuance/renewal required."
        elif matches(rejected):
            status = "rejected_document"
            score = 0.0
            label = "Rejected"
            notes = "Document failed previous verification or administrative review."
        elif matches(verified):
            status = "verified_document"
            score = 1.0
            label = "Verified"
            notes = "Officially verified via DigiLocker, issuing authority, or gazette database."
        elif matches(parsed):
            status = "machine_parsed_document"
            score = 0.85
            label = "Machine-Parsed"
            notes = "Parsed via automated extraction; awaiting authoritative verification."
        elif matches(uploaded):
            status = "uploaded_document"
            score = 0.65
            label = "Uploaded"
            notes = "Document file uploaded to profile; verification pending."
        elif matches(declared):
            status = "user_declared_available"
            score = 0.35
            label = "Declared Available"
            notes = "Citizen self-declares possession. Not verified by official authority."
        else:
            status = "unknown_document"
            score = 0.0
            label = "Missing / Unknown"
            notes = "Citizen has not declared or provided this document."

        scores.append(score)
        breakdown.append({
            "document_type": doc_name,
            "is_mandatory": is_mand,
            "status": status,
            "weight_score": score,
            "status_label": label,
            "notes": notes
        })

    readiness = round(sum(scores) / max(1, len(scores)), 2)
    disclaimer = "Application readiness score reflects document completeness only, never government approval probability."
    return readiness, breakdown, disclaimer

from services.core.facts.derivation import apply_deterministic_derivations

class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.candidate_service = CandidateService(db)

    def evaluate_profile(
        self,
        facts: Dict[str, Any],
        session_id: Optional[str] = None,
        programme_kind: Optional[str] = None,
        top_k: int = 50
    ) -> Dict[str, Any]:
        """
        Pure deterministic recommendation generation.
        Strictly segregates:
        - AUTHORITATIVE_ELIGIBILITY_POOL (certified citizen schemes)
        - DISCOVERY_POOL (uncertified schemes labeled DISCOVERED_NOT_EVALUATED)
        Zero LLM calls for legal eligibility decisions.
        """
        enriched_facts = apply_deterministic_derivations(facts)
        now_utc = datetime.now(timezone.utc)

        # ── 1. AUTHORITATIVE ELIGIBILITY POOL (Certified Schemes Only) ──────
        certified_candidates = self.candidate_service.get_candidates(
            programme_kind=programme_kind,
            certified_only=True,
            limit=None
        )
        evaluated_items: List[Dict[str, Any]] = []

        for candidate in certified_candidates:
            scheme_id = candidate["scheme_id"]
            db_rules = candidate["rules"]

            condition_evals = []
            for r in db_rules:
                # Exclude quarantined invalid bootstrap rules
                v_status = getattr(r, "verification_status", "")
                if v_status == "quarantined_invalid_bootstrap":
                    continue

                r_from = getattr(r, "effective_from", None)
                r_to = getattr(r, "effective_to", None)
                if r_from:
                    dt_from = r_from.replace(tzinfo=timezone.utc) if r_from.tzinfo is None else r_from
                    if dt_from > now_utc:
                        continue
                if r_to:
                    dt_to = r_to.replace(tzinfo=timezone.utc) if r_to.tzinfo is None else r_to
                    if dt_to < now_utc:
                        continue

                rule_expr = getattr(r, "rule_expression", None)
                if rule_expr:
                    try:
                        parsed_ast = json.loads(rule_expr) if isinstance(rule_expr, str) else rule_expr
                        eval_res = evaluate_rule_node(parsed_ast, enriched_facts)
                        condition_evals.append(eval_res)
                        continue
                    except Exception:
                        pass

                raw_val = r.expected_value
                parsed_val = raw_val
                if raw_val.startswith("[") and raw_val.endswith("]"):
                    try:
                        parsed_val = json.loads(raw_val.replace("'", '"'))
                    except Exception:
                        parsed_val = [x.strip().strip("'").strip('"') for x in raw_val[1:-1].split(",")]
                elif raw_val.lower() in ("true", "false"):
                    parsed_val = raw_val.lower() == "true"
                else:
                    try:
                        parsed_val = float(raw_val)
                    except ValueError:
                        parsed_val = raw_val

                cond = ConditionNode(
                    fact=r.fact_key,
                    operator=r.operator,
                    value=parsed_val,
                    mandatory=r.mandatory,
                    reason_code=r.reason_code,
                    verification_status=v_status or "imported_unverified",
                    source_fragment=getattr(r, "source_fragment", None)
                )
                eval_res = evaluate_condition(cond, enriched_facts)
                condition_evals.append(eval_res)

            evidence_citations: List[EvidenceCitation] = []
            for src in candidate.get("sources", []):
                evidence_citations.append(
                    EvidenceCitation(
                        source_url=src.url,
                        document_title=src.document_title or candidate["scheme_name"],
                        publisher=src.publisher or "Government of India",
                        source_fragment=src.source_fragment,
                        trust_level=src.trust_level or "B",
                        verification_status=src.verification_status or "imported_unverified",
                        verified_at=src.published_date.isoformat() if src.published_date else None
                    )
                )
            if not evidence_citations:
                default_url = candidate.get("source_url") or candidate.get("application_url", "")
                if default_url:
                    evidence_citations.append(
                        EvidenceCitation(
                            source_url=default_url,
                            document_title=candidate["scheme_name"],
                            publisher="Government of India",
                            source_fragment=None,
                            trust_level="B",
                            verification_status="imported_unverified"
                        )
                    )

            summary = build_scheme_evaluation(scheme_id, condition_evals, evidence=evidence_citations)

            doc_requirements = candidate.get("documents", [])
            doc_names = [d.document_type for d in doc_requirements] if doc_requirements else []
            readiness, readiness_breakdown, readiness_disclaimer = calculate_document_readiness(
                doc_requirements,
                enriched_facts
            )

            rank_score = calculate_rank_score(
                candidate,
                summary.status,
                readiness,
                enriched_facts
            )

            benefits = candidate.get("benefits", [])
            benefit_str = "Varies by eligibility"
            if benefits:
                b_dict = {
                    "benefit_type": candidate["programme_kind"],
                    "fixed_amount": getattr(benefits[0], "fixed_amount", None),
                    "description": getattr(benefits[0], "description", ""),
                }
                benefit_str = format_benefit_summary(b_dict)

            source_url = candidate.get("source_url") or candidate.get("application_url", "")

            open_conflicts = self.db.query(SourceConflict).filter(
                SourceConflict.scheme_id == scheme_id,
                SourceConflict.status == "SOURCE_CONFLICT_OPEN"
            ).all()

            eligibility_status = summary.status
            authority_lvl = summary.authority_level
            gov_notice = summary.governance_notice

            if open_conflicts:
                authority_lvl = "tentative_unverified_rule"
                if eligibility_status in ("ELIGIBLE", "NOT_ELIGIBLE"):
                    eligibility_status = "NEEDS_VERIFICATION"
                conflict_details = "; ".join(f"{c.conflict_type} on {c.disputed_fact_key}" for c in open_conflicts)
                gov_notice = f"Unresolved official source conflict ({conflict_details}). Decision is routed for human verification."

            matched_count = len(summary.matched_rules)
            total_rules_count = len(summary.matched_rules) + len(summary.unknown_rules) + len(summary.failed_rules) + len(summary.unverified_rules)
            criteria_progress_pct = round((matched_count / total_rules_count) * 100) if total_rules_count > 0 else 0

            item = {
                "scheme_id": scheme_id,
                "scheme_name": candidate["scheme_name"],
                "scheme_level": candidate["scheme_level"],
                "type": candidate["programme_kind"],
                "benefit_type": candidate["programme_kind"],
                "eligibility_status": eligibility_status,
                "deterministic_result": summary.deterministic_result,
                "authority_level": authority_lvl,
                "governance_notice": gov_notice,
                "eligible": eligibility_status == "ELIGIBLE",
                "confidence": int(summary.confidence_score * 100),
                "confidence_score": summary.confidence_score,
                "application_readiness": readiness,
                "readiness_breakdown": readiness_breakdown,
                "readiness_disclaimer": readiness_disclaimer,
                "rank_score": rank_score,
                "benefit_amount": benefit_str,
                "description": candidate["description"],
                "summary": candidate["summary"],
                "application_url": candidate["application_url"],
                "source_url": source_url,
                "documents_required": doc_names,
                "criteria_met_count": matched_count,
                "criteria_total_count": total_rules_count,
                "criteria_progress_pct": criteria_progress_pct,
                "reasons": summary.reasons if eligibility_status != "NOT_ELIGIBLE" else (summary.path_to_eligibility or [gov_notice]),
                "missing_facts": summary.missing_facts,
                "path_to_eligibility": summary.path_to_eligibility,
                "evidence": [e.model_dump() for e in summary.evidence],
                "pool": "AUTHORITATIVE_ELIGIBILITY_POOL"
            }
            evaluated_items.append(item)

        # Status grouping
        eligible_items = [x for x in evaluated_items if x["eligibility_status"] == "ELIGIBLE"]
        needs_info_items = [x for x in evaluated_items if x["eligibility_status"] == "NEEDS_INFO"]
        needs_verification_items = [x for x in evaluated_items if x["eligibility_status"] == "NEEDS_VERIFICATION"]
        not_eligible_items = [x for x in evaluated_items if x["eligibility_status"] in ("NOT_ELIGIBLE", "INELIGIBLE")]
        other_items = [x for x in evaluated_items if x["eligibility_status"] not in ("ELIGIBLE", "NEEDS_INFO")]

        # Sort within status groups by rank_score descending
        eligible_items.sort(key=lambda x: -x["rank_score"])
        needs_info_items.sort(key=lambda x: -x["rank_score"])
        needs_verification_items.sort(key=lambda x: -x["rank_score"])
        not_eligible_items.sort(key=lambda x: -x["rank_score"])

        # ── 2. DISCOVERY POOL (Uncertified Metadata-Only Schemes) ────────────
        discovery_candidates = self.candidate_service.get_discovery_candidates(limit=50)
        discovery_items: List[Dict[str, Any]] = []
        for dc in discovery_candidates:
            d_benefits = dc.get("benefits", [])
            d_b_str = "See official guidelines"
            if d_benefits:
                b_dict = {
                    "benefit_type": dc["programme_kind"],
                    "fixed_amount": getattr(d_benefits[0], "fixed_amount", None),
                    "description": getattr(d_benefits[0], "description", ""),
                }
                d_b_str = format_benefit_summary(b_dict)

            discovery_items.append({
                "scheme_id": dc["scheme_id"],
                "scheme_name": dc["scheme_name"],
                "scheme_level": dc["scheme_level"],
                "type": dc["programme_kind"],
                "benefit_type": dc["programme_kind"],
                "eligibility_status": "DISCOVERED_NOT_EVALUATED",
                "deterministic_result": "UNREVIEWED_DISCOVERY",
                "authority_level": "discovery_unreviewed",
                "governance_notice": "Official government scheme discovered from portal registries. Statutory eligibility rules pending human certification.",
                "eligible": False,
                "confidence": 0,
                "confidence_score": 0.0,
                "application_readiness": 0.0,
                "readiness_breakdown": [],
                "readiness_disclaimer": "Uncertified discovery record; document checklist not certified.",
                "rank_score": 0.01,
                "benefit_amount": d_b_str,
                "description": dc["description"],
                "summary": dc["summary"],
                "application_url": dc["application_url"],
                "source_url": dc["source_url"] or dc["application_url"],
                "documents_required": [],
                "reasons": ["Discovered from official portal; certified statutory rules pending."],
                "missing_facts": [],
                "path_to_eligibility": [],
                "evidence": [],
                "pool": "DISCOVERY_POOL"
            })

        # ── 3. TOP-K POLICY ─────────────────────────────────────────────────
        # All ELIGIBLE schemes are returned unconditionally (never truncated).
        # Remaining slots up to top_k are filled with highest-value NEEDS_INFO schemes.
        # Discovery schemes NEVER displace authoritative certified results.
        remaining_slots = max(0, top_k - len(eligible_items) - len(needs_verification_items))
        ranked_schemes = eligible_items + needs_verification_items + needs_info_items[:remaining_slots]

        # Persist snapshot if session_id is provided
        run_id = str(uuid.uuid4())
        if session_id:
            run_record = RecommendationRun(
                id=run_id,
                session_id=session_id,
                total_considered=len(certified_candidates),
                total_eligible=len(eligible_items),
                ranking_config="transparent_multi_factor_v2_authoritative_segregated"
            )
            self.db.add(run_record)
            for it in ranked_schemes:
                item_record = RecommendationItem(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    scheme_id=it["scheme_id"],
                    eligibility_status=it["eligibility_status"],
                    confidence_score=it["confidence_score"],
                    application_readiness=it["application_readiness"],
                    rank_score=it["rank_score"],
                    reasons_json=json.dumps(it["reasons"]),
                    missing_facts_json=json.dumps(it["missing_facts"])
                )
                self.db.add(item_record)
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()

        return {
            "run_id": run_id,
            "session_id": session_id,
            "total_considered": len(certified_candidates),
            "total_eligible": len(eligible_items),
            "authoritative_pool": {
                "eligible": eligible_items,
                "needs_info": needs_info_items,
                "needs_verification": needs_verification_items,
                "not_eligible": not_eligible_items,
            },
            "discovery_pool": discovery_items,
            "ranked_schemes": ranked_schemes,
            "eligible_schemes": eligible_items,
            "needs_info_schemes": needs_info_items,
            "needs_verification_schemes": needs_verification_items,
            "not_eligible_schemes": not_eligible_items,
            "discovery_schemes": discovery_items,
            "other_schemes": other_items,
        }
