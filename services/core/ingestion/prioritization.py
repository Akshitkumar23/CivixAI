"""
Deterministic Verification Prioritization Model
Calculates risk-weighted verification priority score for welfare schemes.

Formula:
  PriorityScore = (
      unresolved_critical_rules * 25.0 +
      unresolved_other_rules    * 10.0 +
      open_conflicts            * 50.0 +
      unverified_benefits       * 15.0 +
      unverified_documents      *  5.0 +
      quality_failures          * 30.0 +
      missing_official_source   * 40.0 +
      is_stale_source           * 15.0 +
      popularity_weight         *  2.0
  )

Weights prioritize citizen-facing legal risk:
- Open conflicts (50 pts) & missing sources (40 pts) represent maximum authority risk.
- Unresolved critical eligibility rules (25 pts each) directly affect citizen eligibility accuracy.
- Zero hardcoded scheme names.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from services.core.database.models import (
    Scheme, SchemeVersion, EligibilityRule, Benefit,
    DocumentRequirement, SourceRegistry, SourceConflict
)
from .maturity import CRITICAL_FACT_KEYS

class VerificationPrioritizationEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_scheme_priority(self, scheme: Scheme) -> Dict[str, Any]:
        """Calculates risk score and audit breakdown for a single scheme."""
        current_version = self.db.query(SchemeVersion).filter(
            SchemeVersion.scheme_id == scheme.id,
            SchemeVersion.status == "published"
        ).order_by(SchemeVersion.version_number.desc()).first()

        rules = current_version.rules if current_version else []
        benefits = current_version.benefits if current_version else []
        documents = current_version.documents if current_version else []

        unresolved_critical = sum(
            1 for r in rules
            if r.fact_key in CRITICAL_FACT_KEYS and r.verification_status == "imported_unverified"
        )
        unresolved_other = sum(
            1 for r in rules
            if r.fact_key not in CRITICAL_FACT_KEYS and r.verification_status == "imported_unverified"
        )

        open_conflicts = self.db.query(SourceConflict).filter(
            SourceConflict.scheme_id == scheme.id,
            SourceConflict.status == "SOURCE_CONFLICT_OPEN"
        ).count()

        unverified_benefits = sum(
            1 for b in benefits if b.verification_status == "imported_unverified"
        )
        unverified_documents = sum(
            1 for d in documents if d.verification_status == "imported_unverified"
        )

        # Sources audit
        sources = self.db.query(SourceRegistry).filter(
            SourceRegistry.title.ilike(f"%{scheme.canonical_name[:20]}%")
        ).all()

        missing_source = 1 if len(sources) == 0 else 0
        quality_failures = sum(
            1 for s in sources if s.parser_health in ("ocr_required", "failed")
        )
        is_stale = 1 if any(s.freshness_status in ("stale", "unreachable") for s in sources) else 0

        popularity = scheme.popularity_score or 5.0

        # Score computation
        score = (
            (unresolved_critical * 25.0) +
            (unresolved_other * 10.0) +
            (open_conflicts * 50.0) +
            (unverified_benefits * 15.0) +
            (unverified_documents * 5.0) +
            (quality_failures * 30.0) +
            (missing_source * 40.0) +
            (is_stale * 15.0) +
            (popularity * 2.0)
        )

        return {
            "scheme_id": scheme.id,
            "canonical_name": scheme.canonical_name,
            "priority_score": round(score, 2),
            "breakdown": {
                "unresolved_critical_rules": unresolved_critical,
                "unresolved_other_rules": unresolved_other,
                "open_conflicts": open_conflicts,
                "unverified_benefits": unverified_benefits,
                "unverified_documents": unverified_documents,
                "quality_failures": quality_failures,
                "missing_official_source": missing_source,
                "is_stale_source": is_stale,
                "popularity_score": popularity
            }
        }

    def get_ranked_schemes_for_verification(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns schemes ordered from highest verification urgency to lowest."""
        schemes = self.db.query(Scheme).filter(Scheme.is_active == True).all()
        ranked = [self.calculate_scheme_priority(s) for s in schemes]
        ranked.sort(key=lambda x: x["priority_score"], reverse=True)
        return ranked[:limit]
