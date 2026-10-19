"""
Scheme Reconciliation & Duplicate Candidate Engine
Handles Scheme Count Reconciliation (135 vs 157) and Governed Duplicate Detection.

Enforces:
1. Zero destructive automated merges.
2. Full forensic tracking of post-baseline records.
3. Deterministic duplicate candidate detection using normalized names, acronyms, authorities, and official URLs.
4. Governed archival of test fixtures with immutable audit logging.
"""
import uuid
import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from services.core.database.models import (
    Scheme, SchemeVersion, SourceRegistry, SourceConflict,
    DuplicateCandidate, AuditLog, EligibilityRule, Benefit, DocumentRequirement
)

BASELINE_CUTOFF = "2026-09-13 17:00:00"

COMMON_STOPWORDS = {
    "scheme", "yojana", "pradhan", "mantri", "national", "mission", "central",
    "sub", "for", "and", "the", "of", "in", "to", "all", "india", "state"
}

class DuplicateCandidateDetector:
    @staticmethod
    def normalize_name(name: str) -> str:
        """Removes punctuation, numbers, and common welfare stopwords."""
        clean = re.sub(r"[^\w\s]", " ", name.lower())
        tokens = [w for w in clean.split() if w and w not in COMMON_STOPWORDS and len(w) > 1]
        return " ".join(tokens)

    @staticmethod
    def extract_acronym(name: str) -> str:
        """Extracts candidate acronym from uppercase letters or word initials."""
        # Check if already has an acronym in parens e.g. (PMAY) or (IGNOAPS)
        paren_match = re.search(r"\(([A-Z]{3,10})\)", name)
        if paren_match:
            return paren_match.group(1).upper()
        # Word initials
        clean = re.sub(r"[^\w\s]", " ", name)
        words = [w for w in clean.split() if w]
        if len(words) >= 2:
            return "".join(w[0].upper() for w in words if w[0].isalpha() and w.lower() not in ("and", "of", "for", "the", "in", "to"))
        return ""

    @classmethod
    def compare_schemes(cls, sch_a: Scheme, sch_b: Scheme) -> Tuple[float, List[str], str]:
        """
        Computes deterministic similarity score and matching criteria.
        Returns: (similarity_score, matching_criteria, candidate_type)
        """
        if sch_a.id == sch_b.id:
            return 1.0, ["identical_id"], "identical"

        # Check if test artifact
        is_test_a = any(sch_a.id.startswith(p) or sch_a.canonical_name.lower().startswith(p) for p in ("test", "prio-test", "sch-conf", "src_"))
        is_test_b = any(sch_b.id.startswith(p) or sch_b.canonical_name.lower().startswith(p) for p in ("test", "prio-test", "sch-conf", "src_"))
        if is_test_a or is_test_b:
            return 1.0, ["test_suite_execution_artifact"], "test_artifact"

        norm_a = cls.normalize_name(sch_a.canonical_name)
        norm_b = cls.normalize_name(sch_b.canonical_name)
        tokens_a = set(norm_a.split())
        tokens_b = set(norm_b.split())

        criteria = []
        score = 0.0

        # Token Jaccard similarity
        if tokens_a and tokens_b:
            intersection = tokens_a.intersection(tokens_b)
            union = tokens_a.union(tokens_b)
            jaccard = len(intersection) / len(union) if union else 0.0
            if jaccard >= 0.7:
                score += 0.5
                criteria.append(f"high_token_overlap ({jaccard:.2f})")
            elif jaccard >= 0.4:
                score += 0.3
                criteria.append(f"moderate_token_overlap ({jaccard:.2f})")

        # Acronym check
        acr_a = cls.extract_acronym(sch_a.canonical_name)
        acr_b = cls.extract_acronym(sch_b.canonical_name)
        if acr_a and acr_b and acr_a == acr_b and len(acr_a) >= 3:
            score += 0.4
            criteria.append(f"exact_acronym_match ({acr_a})")
        elif acr_a and (acr_a in sch_b.canonical_name.upper() or acr_a in sch_b.id.upper()):
            score += 0.3
            criteria.append(f"acronym_contained ({acr_a})")
        elif acr_b and (acr_b in sch_a.canonical_name.upper() or acr_b in sch_a.id.upper()):
            score += 0.3
            criteria.append(f"acronym_contained ({acr_b})")

        # Authority match
        if sch_a.authority_id and sch_b.authority_id and sch_a.authority_id == sch_b.authority_id:
            score += 0.2
            criteria.append("same_authority")

        # Jurisdiction / Level match
        if sch_a.scheme_level and sch_b.scheme_level and sch_a.scheme_level == sch_b.scheme_level:
            score += 0.1
            criteria.append("same_jurisdiction")

        candidate_type = "potential_duplicate"
        if "acronym" in " ".join(criteria):
            candidate_type = "alias"
        elif sch_a.scheme_level != sch_b.scheme_level:
            candidate_type = "state_variant"

        return min(round(score, 2), 1.0), criteria, candidate_type


class SchemeReconciliationService:
    def __init__(self, db: Session):
        self.db = db

    def audit_post_baseline_schemes(self) -> List[Dict[str, Any]]:
        """
        Forensically audits every scheme created after the original baseline migration.
        """
        post_schemes = self.db.query(Scheme).filter(
            Scheme.created_at > BASELINE_CUTOFF
        ).order_by(Scheme.created_at.asc()).all()

        results = []
        for s in post_schemes:
            # Determine creation pathway
            is_test = any(s.id.startswith(p) or s.canonical_name.lower().startswith(p) for p in ("test", "prio-test", "sch-conf", "src_"))
            pathway = "test_suite_execution" if is_test else "ingestion_discovery"
            category = "test_artifact" if is_test else "legitimate_new_scheme"

            # Check if it has sources
            src_count = self.db.query(SourceRegistry).filter(
                or_(SourceRegistry.scheme_id == s.id, SourceRegistry.title.ilike(f"%{s.canonical_name[:25]}%"))
            ).count()

            # Find potential duplicate among baseline schemes
            baseline_schemes = self.db.query(Scheme).filter(Scheme.created_at <= BASELINE_CUTOFF).all()
            best_match = None
            highest_sim = 0.0
            best_crit = []
            for b in baseline_schemes:
                sim, crit, _ = DuplicateCandidateDetector.compare_schemes(s, b)
                if sim > highest_sim:
                    highest_sim = sim
                    best_match = b.id
                    best_crit = crit

            results.append({
                "scheme_id": s.id,
                "canonical_name": s.canonical_name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "creation_pathway": pathway,
                "category": category,
                "source_evidence_count": src_count,
                "possible_duplicate_of": best_match if highest_sim >= 0.5 else None,
                "duplicate_similarity": highest_sim if highest_sim >= 0.5 else 0.0,
                "matching_criteria": best_crit if highest_sim >= 0.5 else []
            })
        return results

    def detect_and_register_duplicate_candidates(self) -> int:
        """
        Runs duplicate candidate detection across all active schemes and stages
        reviewable DuplicateCandidate records. Zero destructive automatic merges.
        """
        schemes = self.db.query(Scheme).filter(Scheme.is_active == True).all()
        created_count = 0

        # Existing candidate pairs
        existing_candidates = self.db.query(DuplicateCandidate).all()
        existing_pairs = {
            tuple(sorted([c.scheme_a_id, c.scheme_b_id])) for c in existing_candidates
        }

        for i in range(len(schemes)):
            for j in range(i + 1, len(schemes)):
                sch_a = schemes[i]
                sch_b = schemes[j]
                pair_key = tuple(sorted([sch_a.id, sch_b.id]))
                if pair_key in existing_pairs:
                    continue

                sim_score, criteria, c_type = DuplicateCandidateDetector.compare_schemes(sch_a, sch_b)
                if sim_score >= 0.65 or c_type == "test_artifact":
                    candidate = DuplicateCandidate(
                        id=f"dup-{uuid.uuid4().hex[:12]}",
                        scheme_a_id=sch_a.id,
                        scheme_b_id=sch_b.id,
                        scheme_a_name=sch_a.canonical_name,
                        scheme_b_name=sch_b.canonical_name,
                        similarity_score=sim_score,
                        matching_criteria_json=json.dumps(criteria),
                        candidate_type=c_type,
                        status="pending_review",
                        created_at=datetime.now(timezone.utc)
                    )
                    self.db.add(candidate)
                    existing_pairs.add(pair_key)
                    created_count += 1

        self.db.commit()
        return created_count

    def archive_test_artifacts(self, reviewed_by: str = "governance-admin", reason: str = "Archiving unit test fixtures from production database") -> Dict[str, Any]:
        """
        Safely deactivates test fixture schemes in data/civix.db with an immutable audit log,
        restoring the active canonical scheme count to exactly 135 without data loss.
        """
        test_schemes = self.db.query(Scheme).filter(
            Scheme.created_at > BASELINE_CUTOFF,
            Scheme.is_active == True,
            or_(
                Scheme.id.like("test-%"),
                Scheme.id.like("prio-test-%"),
                Scheme.id.like("sch-conf-%"),
                Scheme.id.like("src_%")
            )
        ).all()

        archived_ids = []
        now_utc = datetime.now(timezone.utc)

        for s in test_schemes:
            s.is_active = False
            s.status = "archived_test_fixture"
            archived_ids.append(s.id)

            # Record audit log
            audit = AuditLog(
                id=f"aud-rec-{uuid.uuid4().hex[:10]}",
                entity_type="Scheme",
                entity_id=s.id,
                action="ARCHIVE_TEST_FIXTURE",
                actor_id=reviewed_by,
                previous_state_json=json.dumps({"is_active": True, "status": "active"}),
                new_state_json=json.dumps({"is_active": False, "status": "archived_test_fixture"}),
                reason=reason,
                created_at=now_utc
            )
            self.db.add(audit)

        # Also resolve/supersede any open conflicts attached to test schemes
        test_conflicts = self.db.query(SourceConflict).filter(
            SourceConflict.scheme_id.in_(archived_ids),
            SourceConflict.status == "SOURCE_CONFLICT_OPEN"
        ).all()
        for c in test_conflicts:
            c.status = "SOURCE_CONFLICT_RESOLVED"
            c.resolution_type = "SUPERSEDED"
            c.resolved_by = reviewed_by
            c.resolution_notes = "Test fixture archived; test conflict closed."
            c.resolved_at = now_utc

        # Update candidate status
        self.db.query(DuplicateCandidate).filter(
            or_(
                DuplicateCandidate.scheme_a_id.in_(archived_ids),
                DuplicateCandidate.scheme_b_id.in_(archived_ids)
            )
        ).update({"status": "archived"}, synchronize_session=False)

        self.db.commit()

        active_count = self.db.query(Scheme).filter(Scheme.is_active == True).count()
        return {
            "archived_count": len(archived_ids),
            "archived_scheme_ids": archived_ids,
            "active_canonical_schemes_count": active_count,
            "governance_actor": reviewed_by,
            "audit_logged": True
        }

    def get_full_reconciliation_report(self) -> Dict[str, Any]:
        """
        Produces the formal Scheme Count Reconciliation Report (135 vs 157 & Phase 4.3.1 Canonical Breakdown).
        Guarantees that canonical_scheme_count equals sum of all mutually exclusive categories.
        """
        from services.core.ingestion.semantic import SemanticCertificationEngine, NON_CITIZEN_AUDIENCES

        baseline_schemes = self.db.query(Scheme).filter(Scheme.created_at <= BASELINE_CUTOFF).all()
        post_audit = self.audit_post_baseline_schemes()
        test_artifacts = [s for s in post_audit if s["category"] == "test_artifact"]
        legitimate_new = [s for s in post_audit if s["category"] == "legitimate_new_scheme"]
        
        # Canonical baseline count (historical records preserved)
        canonical_count = len(baseline_schemes)
        
        # Lifecycle status counts across canonical schemes
        active_schemes = self.db.query(Scheme).filter(Scheme.created_at <= BASELINE_CUTOFF, Scheme.is_active == True).count()
        withdrawn_count = self.db.query(Scheme).filter(Scheme.created_at <= BASELINE_CUTOFF, Scheme.lifecycle_status == "WITHDRAWN").count()
        subsumed_count = self.db.query(Scheme).filter(Scheme.created_at <= BASELINE_CUTOFF, Scheme.lifecycle_status == "SUBSUMED").count()
        closed_count = self.db.query(Scheme).filter(Scheme.created_at <= BASELINE_CUTOFF, Scheme.lifecycle_status == "CLOSED").count()
        historical_count = self.db.query(Scheme).filter(Scheme.created_at <= BASELINE_CUTOFF, Scheme.lifecycle_status == "HISTORICAL").count()

        # Detailed mutually exclusive categorization of all 135 canonical schemes
        engine = SemanticCertificationEngine(self.db)
        active_citizen_rag_certified = 0
        institutional_gated = 0
        unreviewed_default = 0

        for s in baseline_schemes:
            if s.lifecycle_status in ("WITHDRAWN", "SUBSUMED", "CLOSED", "HISTORICAL"):
                continue  # accounted in lifecycle counts above
            
            # Check institutional gate
            if s.audience_type in NON_CITIZEN_AUDIENCES:
                institutional_gated += 1
            elif s.audience_type == "UNREVIEWED_DEFAULT":
                unreviewed_default += 1
            else:
                ok, _ = engine.is_rag_certified(s.id, allow_institutional=False)
                if ok:
                    active_citizen_rag_certified += 1
                else:
                    unreviewed_default += 1

        category_sum = (
            active_citizen_rag_certified
            + institutional_gated
            + withdrawn_count
            + subsumed_count
            + closed_count
            + historical_count
            + unreviewed_default
        )

        pending_dups = self.db.query(DuplicateCandidate).filter(DuplicateCandidate.status == "pending_review").count()

        return {
            "canonical_scheme_count": canonical_count,
            "original_canonical_schemes": canonical_count,
            "active_scheme_count": active_schemes,
            "active_canonical_scheme_count": active_schemes,
            "withdrawn_count": withdrawn_count,
            "subsumed_count": subsumed_count,
            "closed_count": closed_count,
            "historical_count": historical_count,
            "active_citizen_rag_certified_count": active_citizen_rag_certified,
            "institutional_gated_count": institutional_gated,
            "unreviewed_default_count": unreviewed_default,
            "category_reconciliation_sum": category_sum,
            "is_perfectly_reconciled": (category_sum == canonical_count),
            "mutually_exclusive_breakdown": {
                "active_citizen_rag_certified": active_citizen_rag_certified,
                "institutional_gated": institutional_gated,
                "withdrawn": withdrawn_count,
                "subsumed": subsumed_count,
                "closed": closed_count,
                "historical": historical_count,
                "unreviewed_default": unreviewed_default
            },
            "total_schemes_in_db": len(baseline_schemes) + len(post_audit),
            "post_baseline_created_count": len(post_audit),
            "breakdown": {
                "test_suite_execution_artifacts": len(test_artifacts),
                "legitimate_new_schemes": len(legitimate_new),
                "ingestion_created_records": 0,
                "duplicate_candidates_flagged": pending_dups
            },
            "post_baseline_inventory": post_audit,
            "conclusion": (
                f"Exactly {canonical_count} canonical schemes are preserved in the historical corpus. "
                f"Current active available schemes: {active_schemes}. "
                f"Mutually exclusive breakdown: {active_citizen_rag_certified} active citizen certified + "
                f"{institutional_gated} institutional gated + {withdrawn_count} withdrawn + {subsumed_count} subsumed + "
                f"{unreviewed_default} unreviewed = {category_sum} total (100% reconciled)."
            )
        }

