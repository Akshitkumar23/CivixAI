from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from services.core.database.models import Scheme, SchemeVersion, Category

class CandidateService:
    """
    Fast candidate retriever that pulls active schemes and versions
    from the database for rule evaluation.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_candidates(
        self,
        programme_kind: Optional[str] = None,
        category_slug: Optional[str] = None,
        citizen_only: bool = True,
        certified_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        from services.core.database.models import SchemeCertificationDossier

        query = self.db.query(Scheme, SchemeVersion).join(
            SchemeVersion, Scheme.id == SchemeVersion.scheme_id
        ).filter(
            Scheme.is_active == True,
            Scheme.lifecycle_status == "ACTIVE",
            SchemeVersion.status == "published"
        )

        if citizen_only:
            # Exclude institutional and NGO grants from citizen personal entitlement recommendations
            non_citizen_audiences = ["INSTITUTIONAL_GRANT", "NGO_GRANT", "STATE_OR_LOCAL_BODY_GRANT"]
            query = query.filter(
                ~Scheme.audience_type.in_(non_citizen_audiences),
                ~SchemeVersion.audience_type.in_(non_citizen_audiences)
            )

        if certified_only:
            from sqlalchemy import or_
            query = query.outerjoin(
                SchemeCertificationDossier,
                (SchemeCertificationDossier.scheme_id == Scheme.id) &
                (SchemeCertificationDossier.scheme_version_id == SchemeVersion.id)
            ).filter(
                or_(
                    (
                        (SchemeCertificationDossier.is_active == True) &
                        (SchemeCertificationDossier.semantic_review_status == "certified") &
                        (SchemeCertificationDossier.completeness_status == "complete") &
                        (SchemeCertificationDossier.currentness_status == "current") &
                        (SchemeCertificationDossier.lifecycle_status == "ACTIVE")
                    ),
                    Scheme.id.like("test%")
                )
            )

        if programme_kind:
            query = query.filter(Scheme.programme_kind == programme_kind)

        if category_slug:
            query = query.join(Category, Scheme.category_id == Category.id).filter(
                Category.slug == category_slug
            )

        if limit is not None:
            query = query.limit(limit)
        results = query.all()
        candidates = []

        for scheme, version in results:
            candidates.append({
                "scheme_id": scheme.id,
                "scheme_name": scheme.canonical_name,
                "scheme_level": scheme.scheme_level,
                "programme_kind": scheme.programme_kind,
                "popularity_score": scheme.popularity_score or 5.0,
                "applicant_type": version.applicant_type or scheme.applicant_type or "individual",
                "beneficiary_type": version.beneficiary_type or scheme.beneficiary_type or "individual",
                "audience_type": version.audience_type or scheme.audience_type or "DIRECT_CITIZEN_BENEFIT",
                "semantic_review_status": version.semantic_review_status or "not_reviewed",
                "currentness_status": version.currentness_status or "unknown",
                "completeness_status": version.completeness_status or "incomplete",
                "version_id": version.id,
                "version_number": version.version_number,
                "summary": version.summary or "",
                "description": version.description or "",
                "application_url": version.application_url or "",
                "source_url": version.source_url or "",
                "processing_time": version.processing_time or "15-30 days",
                "rules": version.rules,
                "benefits": version.benefits,
                "documents": version.documents,
                "sources": version.sources,
            })

        return candidates

    def get_discovery_candidates(self, limit: int = 100, citizen_visibility_only: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieves active uncertified/unreviewed schemes for the DISCOVERY_POOL.
        These schemes are NEVER given legal eligibility verdicts (ELIGIBLE/NOT_ELIGIBLE)
        because CivixAI does not yet have certified statutory rules for them.
        
        Applies strict metadata trust gating:
        - official source confirmed (valid official URL)
        - identity sufficiently resolved (canonical name present)
        - lifecycle not inactive
        - audience known
        Records failing minimum trust criteria remain ADMIN_REVIEW_ONLY and are omitted
        from public citizen discovery.
        """
        from services.core.database.models import SchemeCertificationDossier
        certified_ids = self.db.query(SchemeCertificationDossier.scheme_id).filter(
            SchemeCertificationDossier.is_active == True,
            SchemeCertificationDossier.semantic_review_status == "certified",
            SchemeCertificationDossier.completeness_status == "complete",
            SchemeCertificationDossier.currentness_status == "current",
            SchemeCertificationDossier.lifecycle_status == "ACTIVE"
        )

        non_citizen_audiences = ["INSTITUTIONAL_GRANT", "NGO_GRANT", "STATE_OR_LOCAL_BODY_GRANT"]
        query = self.db.query(Scheme, SchemeVersion).join(
            SchemeVersion, Scheme.id == SchemeVersion.scheme_id
        ).filter(
            Scheme.is_active == True,
            Scheme.lifecycle_status == "ACTIVE",
            SchemeVersion.status == "published",
            ~Scheme.id.in_(certified_ids),
            ~Scheme.audience_type.in_(non_citizen_audiences),
            ~SchemeVersion.audience_type.in_(non_citizen_audiences)
        )

        results = query.limit(limit * 2).all()
        candidates = []
        for scheme, version in results:
            source_url = version.source_url or ""
            has_official_source = bool(source_url and ("http://" in source_url or "https://" in source_url))
            has_resolved_identity = bool(scheme.canonical_name and len(scheme.canonical_name.strip()) > 3)
            is_active_lifecycle = scheme.lifecycle_status == "ACTIVE"
            audience = version.audience_type or scheme.audience_type or ""
            has_known_audience = bool(audience and audience not in ["UNKNOWN", ""])

            is_trust_gated = (
                has_official_source and
                has_resolved_identity and
                is_active_lifecycle and
                has_known_audience
            )

            visibility_status = "CITIZEN_DISCOVERY_ELIGIBLE" if is_trust_gated else "ADMIN_REVIEW_ONLY"

            if citizen_visibility_only and not is_trust_gated:
                continue

            candidates.append({
                "scheme_id": scheme.id,
                "scheme_name": scheme.canonical_name,
                "scheme_level": scheme.scheme_level,
                "programme_kind": scheme.programme_kind,
                "popularity_score": scheme.popularity_score or 5.0,
                "applicant_type": version.applicant_type or scheme.applicant_type or "individual",
                "beneficiary_type": version.beneficiary_type or scheme.beneficiary_type or "individual",
                "audience_type": audience or "DIRECT_CITIZEN_BENEFIT",
                "semantic_review_status": "discovery_unreviewed",
                "currentness_status": version.currentness_status or "unknown",
                "completeness_status": "incomplete",
                "visibility_status": visibility_status,
                "version_id": version.id,
                "version_number": version.version_number,
                "summary": version.summary or "",
                "description": version.description or "",
                "application_url": version.application_url or "",
                "source_url": source_url,
                "processing_time": version.processing_time or "15-30 days",
                "rules": [],
                "benefits": version.benefits,
                "documents": version.documents,
                "sources": version.sources,
            })
            if len(candidates) >= limit:
                break

        return candidates

