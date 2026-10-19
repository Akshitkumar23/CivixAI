"""
Corpus Coverage Service
Single Canonical Service for Scheme Source Resolution and Corpus Coverage Metrics.
Eliminates divergence between scheme maturity UNSOURCED status and corpus coverage counts.

Mathematical Invariant:
    A scheme is UNSOURCED if and only if total_sources_count == 0.
    Therefore, UNSOURCED maturity count is strictly identical to schemes_without_source count.
"""
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import or_

from services.core.database.models import (
    Scheme, SchemeVersion, SourceRegistry, SourceDocument, SourceSnapshot,
    EligibilityRule, Benefit, DocumentRequirement, SourceConflict, SchemeChangeSet
)

# Canonical critical citizen eligibility keys
CRITICAL_FACT_KEYS = {
    "household.annual_income",
    "household.monthly_income",
    "household.income",
    "person.income",
    "person.annual_income",
    "person.age",
    "person.gender",
    "person.caste_category",
    "person.category",
    "person.occupation",
    "person.marital_status",
    "person.disability",
    "person.disability_percentage",
    "location.state",
    "location.district",
    "location.area_type",
    "landholding.has_agricultural_land",
    "landholding.size_acres",
    "household.owns_pucca_house",
    "household.has_bpl_card",
    "household.has_ration_card"
}

class CorpusCoverageService:
    def __init__(self, db: Session):
        self.db = db

    def get_sources_for_scheme(self, scheme_id: str) -> Dict[str, Any]:
        """
        Canonically resolves all authoritative sources for a scheme.
        Combines direct foreign key links, title mappings, and version source documents.
        """
        scheme = self.db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            return {"scheme_id": scheme_id, "registered_sources": [], "version_sources": [], "total_count": 0}

        # 1. Registered sources: prefer explicit scheme_id association first
        reg_sources = self.db.query(SourceRegistry).filter(
            SourceRegistry.scheme_id == scheme_id
        ).all()

        if not reg_sources:
            clean_name = scheme.canonical_name.strip()
            search_term = clean_name[:30]
            reg_sources = self.db.query(SourceRegistry).filter(
                SourceRegistry.title.ilike(f"%{search_term}%"),
                SourceRegistry.scheme_id.is_(None)
            ).all()

        # Deduplicate registered sources by id
        reg_map = {s.id: s for s in reg_sources}
        unique_reg_sources = list(reg_map.values())

        # 2. Version source documents attached to published versions
        published_versions = self.db.query(SchemeVersion).filter(
            SchemeVersion.scheme_id == scheme_id,
            SchemeVersion.status == "published"
        ).order_by(SchemeVersion.version_number.desc()).all()

        version_sources = []
        for v in published_versions:
            for vs in v.sources:
                version_sources.append(vs)

        total_count = len(unique_reg_sources) + len(version_sources)
        return {
            "scheme_id": scheme_id,
            "canonical_name": scheme.canonical_name,
            "registered_sources": unique_reg_sources,
            "version_sources": version_sources,
            "total_count": total_count,
            "has_authoritative_source": any(
                s.trust_level in ("A", "B") for s in unique_reg_sources
            ) or any(
                vs.trust_level in ("A", "B") for vs in version_sources
            )
        }

    def is_scheme_sourced(self, scheme_id: str) -> bool:
        """Mathematical definition: True if and only if total_sources > 0."""
        coverage = self.get_sources_for_scheme(scheme_id)
        return coverage["total_count"] > 0

    def get_canonical_corpus_metrics(self) -> Dict[str, Any]:
        """
        Single canonical source of truth for all corpus statistics.
        Guarantees that UNSOURCED count == schemes_without_source count.
        """
        all_schemes = self.db.query(Scheme).filter(Scheme.is_active == True).all()
        all_sources = self.db.query(SourceRegistry).all()
        all_snapshots = self.db.query(SourceSnapshot).all()
        all_rules = self.db.query(EligibilityRule).all()
        all_benefits = self.db.query(Benefit).all()
        all_docs = self.db.query(DocumentRequirement).all()
        all_conflicts = self.db.query(SourceConflict).all()
        all_changesets = self.db.query(SchemeChangeSet).all()

        # Evaluate each scheme through canonical coverage
        schemes_with_source = 0
        schemes_without_source = 0
        schemes_with_auth = 0
        coverage_rows = []

        for s in all_schemes:
            cov = self.get_sources_for_scheme(s.id)
            if cov["total_count"] == 0:
                schemes_without_source += 1
            else:
                schemes_with_source += 1
                if cov["has_authoritative_source"]:
                    schemes_with_auth += 1

            coverage_rows.append({
                "scheme_id": s.id,
                "canonical_name": s.canonical_name,
                "sources_count": cov["total_count"],
                "has_sources": cov["total_count"] > 0,
                "has_authoritative": cov["has_authoritative_source"]
            })

        # Fetch status breakdown
        fetch_counter = Counter(s.last_fetch_status or "not_attempted" for s in all_sources)

        # Parser health breakdown with strict snapshot invariant:
        # A source cannot be 'complete' without an associated snapshot!
        parser_counter = Counter()
        snapshot_source_ids = {snap.source_registry_id for snap in all_snapshots}
        for s in all_sources:
            if s.id not in snapshot_source_ids or s.parser_health == "not_run":
                parser_counter["not_run"] += 1
            else:
                parser_counter[s.parser_health or "not_run"] += 1

        # Freshness breakdown
        freshness_counter = Counter(s.freshness_status or "fresh" for s in all_sources)

        # Rule breakdown
        rule_status_counter = Counter(r.verification_status for r in all_rules)
        critical_rules = [r for r in all_rules if r.fact_key in CRITICAL_FACT_KEYS]
        critical_status_counter = Counter(r.verification_status for r in critical_rules)

        # Benefits & Documents
        benefit_counter = Counter(b.verification_status for b in all_benefits)
        doc_counter = Counter(d.verification_status for d in all_docs)

        # Conflicts
        open_conflicts = sum(1 for c in all_conflicts if c.status == "SOURCE_CONFLICT_OPEN")
        resolved_conflicts = sum(1 for c in all_conflicts if c.status == "SOURCE_CONFLICT_RESOLVED")

        # Changesets
        cs_counter = Counter(cs.status for cs in all_changesets)

        return {
            "schemes": {
                "total_active": len(all_schemes),
                "with_source": schemes_with_source,
                "without_source": schemes_without_source,
                "with_authoritative_source": schemes_with_auth,
                "coverage_percentage": round((schemes_with_source / len(all_schemes) * 100) if all_schemes else 0, 1)
            },
            "sources": {
                "total_registered": len(all_sources),
                "total_snapshots": len(all_snapshots),
                "by_fetch_status": dict(fetch_counter),
                "by_parser_health": dict(parser_counter),
                "by_freshness": dict(freshness_counter),
                "stale_count": sum(1 for s in all_sources if s.freshness_status in ("stale", "unreachable")),
                "broken_count": sum(1 for s in all_sources if s.last_fetch_status in ("timeout", "unreachable", "failed", "dns_error", "404_not_found", "5xx_error"))
            },
            "rules": {
                "total": len(all_rules),
                "by_status": dict(rule_status_counter),
                "critical_total": len(critical_rules),
                "critical_by_status": dict(critical_status_counter)
            },
            "benefits": {
                "total": len(all_benefits),
                "by_status": dict(benefit_counter),
                "verified_count": benefit_counter.get("source_verified", 0) + benefit_counter.get("human_reviewed", 0)
            },
            "documents": {
                "total": len(all_docs),
                "by_status": dict(doc_counter),
                "verified_count": doc_counter.get("source_verified", 0) + doc_counter.get("human_reviewed", 0)
            },
            "conflicts": {
                "open": open_conflicts,
                "resolved": resolved_conflicts
            },
            "changesets": {
                "pending": cs_counter.get("pending", 0),
                "approved": cs_counter.get("approved", 0),
                "rejected": cs_counter.get("rejected", 0)
            }
        }
