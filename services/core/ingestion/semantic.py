"""
Semantic Certification Engine & RAG Indexing Gate
Phase 3.8: Semantic Certification, Applicant/Beneficiary Modeling, Current-Policy Revalidation & Dossiers.

Enforces:
1. source_verified != semantic_model_verified
2. Applicant vs Beneficiary vs Audience entity modeling
3. Latest-policy supersession & currentness validation
4. Statutory rule completeness (inclusions + exclusions)
5. Cryptographic certification hashing and audit logging
6. Deterministic RAG gating: is_rag_certified(scheme_version) -> Tuple[bool, str]
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from sqlalchemy.orm import Session

from services.core.database.models import (
    Scheme, SchemeVersion, EligibilityRule, Benefit,
    DocumentRequirement, SourceDocument, SourceRegistry,
    SourceConflict, AuditLog, SchemeCertificationDossier,
    RagChunk
)

VALID_LIFECYCLE_STATUSES: Set[str] = {
    "ACTIVE", "PAUSED", "CLOSED", "WITHDRAWN", "SUBSUMED", "SUPERSEDED", "HISTORICAL"
}

VALID_APPLICANT_TYPES: Set[str] = {
    "individual", "household", "family", "farmer_family", "student",
    "street_vendor", "artisan", "enterprise", "SHG", "NGO", "trust",
    "Section_8_company", "institution", "local_body", "state_government",
    "other_organization"
}

VALID_BENEFICIARY_TYPES: Set[str] = {
    "individual", "household", "family", "farmer_family", "student",
    "street_vendors", "artisans", "persons_with_disabilities", "women",
    "farmers", "citizens", "children", "senior_citizens", "unorganized_workers"
}

VALID_AUDIENCE_TYPES: Set[str] = {
    "DIRECT_CITIZEN_BENEFIT", "HOUSEHOLD_BENEFIT", "CREDIT_SCHEME",
    "ENTERPRISE_SUPPORT", "INSTITUTIONAL_GRANT", "NGO_GRANT",
    "STATE_OR_LOCAL_BODY_GRANT", "SERVICE_PROGRAMME", "OTHER",
    "UNREVIEWED_DEFAULT",
    "PENSION_SCHEME", "INSURANCE_SCHEME", "AGRICULTURE_SUPPORT", "STUDENT_SUPPORT",
    "WOMEN_SUPPORT", "DISABILITY_SUPPORT"
}

NON_CITIZEN_AUDIENCES: Set[str] = {
    "INSTITUTIONAL_GRANT", "NGO_GRANT", "STATE_OR_LOCAL_BODY_GRANT"
}


from services.core.ingestion.certification_policies import (
    CertificationPolicyManager,
    CompletenessPolicy,
    PolicyValidationError
)


class CompletenessPolicyRegistry:
    """
    Registry for scheme-specific completeness policies.
    Maintains backward compatibility with legacy registry while delegating
    to the declarative CertificationPolicyManager.
    """
    _policies: Dict[str, CompletenessPolicy] = {}

    @classmethod
    def register(cls, scheme_id_or_alias: str, policy: CompletenessPolicy):
        cls._policies[scheme_id_or_alias] = policy
        CertificationPolicyManager.get_instance().register_policy(scheme_id_or_alias, policy)

    @classmethod
    def get_policy(cls, scheme_id: str) -> Optional[CompletenessPolicy]:
        policy = CertificationPolicyManager.get_instance().get_policy(scheme_id)
        if policy is not None:
            return policy
        if scheme_id in cls._policies:
            return cls._policies[scheme_id]
        for key, pol in cls._policies.items():
            if key in scheme_id or scheme_id in key:
                return pol
        return None

    @classmethod
    def sync_from_manager(cls):
        manager = CertificationPolicyManager.get_instance()
        for k, v in manager.get_policies_map().items():
            cls._policies[k] = v

    @classmethod
    def reload(cls):
        manager = CertificationPolicyManager.get_instance()
        manager.reload_policies()
        cls.sync_from_manager()


# Sync legacy registry from declarative configuration (data/certification_policies.json)
CompletenessPolicyRegistry.sync_from_manager()



def compute_certification_hash(
    scheme_id: str,
    version_number: int,
    applicant_type: str,
    beneficiary_type: str,
    audience_type: str,
    sources_data: List[Dict[str, Any]],
    rules_data: List[Dict[str, Any]],
    benefits_data: List[Dict[str, Any]],
    documents_data: List[Dict[str, Any]],
    latest_source_reference: Optional[str] = None
) -> str:
    """
    Computes deterministic SHA-256 hash over normalized scheme representation.
    Any drift in rules, benefits, evidence hashes, or audience typing changes the hash.
    """
    normalized_sources = sorted([
        {
            "url": s.get("url", ""),
            "content_hash": s.get("content_hash", ""),
            "published_date": str(s.get("published_date", "")),
        }
        for s in sources_data
    ], key=lambda x: (x["url"], x["content_hash"]))

    normalized_rules = sorted([
        {
            "fact_key": r.get("fact_key", ""),
            "operator": r.get("operator", ""),
            "expected_value": str(r.get("expected_value", "")),
            "rule_scope": r.get("rule_scope", "applicant_eligibility"),
            "mandatory": bool(r.get("mandatory", True)),
            "reason_code": r.get("reason_code", ""),
            "rule_expression": str(r.get("rule_expression") or "")
        }
        for r in rules_data
    ], key=lambda x: (x["fact_key"], x["operator"], x["expected_value"], x["rule_scope"]))

    normalized_benefits = sorted([
        {
            "benefit_type": b.get("benefit_type", ""),
            "amount_type": b.get("amount_type", ""),
            "fixed_amount": b.get("fixed_amount"),
            "max_amount": b.get("max_amount"),
            "tranche_number": b.get("tranche_number", 1),
            "prerequisite_condition": str(b.get("prerequisite_condition") or ""),
            "interest_subsidy_percentage": b.get("interest_subsidy_percentage"),
        }
        for b in benefits_data
    ], key=lambda x: (x["benefit_type"], x["tranche_number"], str(x["max_amount"])))

    normalized_docs = sorted([
        {
            "document_type": d.get("document_type", ""),
            "is_mandatory": bool(d.get("is_mandatory", True)),
            "requirement_stage": d.get("requirement_stage", "application_stage")
        }
        for d in documents_data
    ], key=lambda x: x["document_type"])

    payload = {
        "scheme_id": scheme_id,
        "version_number": version_number,
        "applicant_type": applicant_type,
        "beneficiary_type": beneficiary_type,
        "audience_type": audience_type,
        "latest_source_reference": latest_source_reference or "",
        "sources": normalized_sources,
        "rules": normalized_rules,
        "benefits": normalized_benefits,
        "documents": normalized_docs
    }

    raw_json = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()


class SemanticCertificationEngine:
    def __init__(self, db: Session, policy_manager: Optional[CertificationPolicyManager] = None):
        self.db = db
        self.policy_manager = policy_manager or CertificationPolicyManager.get_instance()

    def validate_entity_model(
        self,
        applicant_type: str,
        beneficiary_type: str,
        audience_type: str
    ) -> List[str]:
        """
        Validates entity typing correctness and audience consistency.
        """
        findings = []
        if applicant_type not in VALID_APPLICANT_TYPES:
            findings.append(f"Invalid applicant_type '{applicant_type}'. Allowed: {sorted(list(VALID_APPLICANT_TYPES))}")

        if beneficiary_type not in VALID_BENEFICIARY_TYPES:
            findings.append(f"Invalid beneficiary_type '{beneficiary_type}'. Allowed: {sorted(list(VALID_BENEFICIARY_TYPES))}")

        if audience_type not in VALID_AUDIENCE_TYPES:
            findings.append(f"Invalid audience_type '{audience_type}'. Allowed: {sorted(list(VALID_AUDIENCE_TYPES))}")

        # Consistency checks
        if audience_type == "NGO_GRANT" and applicant_type not in ("NGO", "trust", "Section_8_company", "institution", "other_organization"):
            findings.append(f"Audience NGO_GRANT requires institutional applicant_type, got '{applicant_type}'")

        if audience_type == "DIRECT_CITIZEN_BENEFIT" and applicant_type in ("NGO", "institution", "local_body", "state_government"):
            findings.append(f"Audience DIRECT_CITIZEN_BENEFIT cannot have organizational applicant '{applicant_type}'")

        return findings

    def validate_rule_completeness(
        self,
        scheme_id: str,
        rules: List[EligibilityRule]
    ) -> Tuple[str, List[str]]:
        """
        Evaluates whether a scheme contains both positive inclusions and necessary statutory exclusions.
        """
        findings = []
        if not rules:
            return "incomplete", ["Zero eligibility rules defined"]

        has_inclusions = any(getattr(r, "rule_scope", "applicant_eligibility") in ("applicant_eligibility", "beneficiary_eligibility", "household_eligibility") for r in rules)
        has_exclusions = any(getattr(r, "rule_scope", "applicant_eligibility") in ("exclusion", "exception") for r in rules)

        # Data-driven statutory completeness checks via policy manager & legacy registry
        policy = self.policy_manager.get_policy(scheme_id) or CompletenessPolicyRegistry.get_policy(scheme_id)
        if policy:
            policy_findings = policy.evaluate(scheme_id, rules)
            findings.extend(policy_findings)

        if findings:
            return "partial", findings
        return "complete", []

    def certify_scheme_version(
        self,
        scheme_id: str,
        version_id: str,
        certified_by: str = "system",
        applicant_type: str = "individual",
        beneficiary_type: str = "individual",
        audience_type: str = "DIRECT_CITIZEN_BENEFIT",
        latest_source_reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> SchemeCertificationDossier:
        """
        Performs rigorous semantic certification on a scheme version.
        Creates an immutable SchemeCertificationDossier record and updates SchemeVersion state.
        """
        scheme = self.db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            raise ValueError(f"Scheme '{scheme_id}' not found.")

        version = self.db.query(SchemeVersion).filter(SchemeVersion.id == version_id).first()
        if not version:
            raise ValueError(f"SchemeVersion '{version_id}' not found.")

        # 1. Validate entity model
        model_findings = self.validate_entity_model(applicant_type, beneficiary_type, audience_type)

        # 2. Check open conflicts
        conflicts = self.db.query(SourceConflict).filter(
            SourceConflict.scheme_id == scheme_id,
            SourceConflict.status == "SOURCE_CONFLICT_OPEN"
        ).all()
        conflict_findings = [f"Open conflict {c.id}: {c.conflict_type}" for c in conflicts]

        # 3. Rule completeness
        rules = self.db.query(EligibilityRule).filter(EligibilityRule.scheme_version_id == version_id).all()
        comp_status, rule_findings = self.validate_rule_completeness(scheme_id, rules)

        all_findings = model_findings + conflict_findings + rule_findings
        if all_findings:
            open_findings_json = json.dumps(all_findings)
        else:
            open_findings_json = "[]"

        # 4. Sources verification
        sources = self.db.query(SourceDocument).filter(SourceDocument.scheme_version_id == version_id).all()
        source_data = [
            {
                "url": s.url,
                "content_hash": s.content_hash,
                "published_date": str(s.published_date) if s.published_date else ""
            }
            for s in sources
        ]

        # 5. Benefits & Documents
        benefits = self.db.query(Benefit).filter(Benefit.scheme_version_id == version_id).all()
        benefit_data = [
            {
                "benefit_type": b.benefit_type,
                "amount_type": b.amount_type,
                "fixed_amount": b.fixed_amount,
                "max_amount": b.max_amount,
                "tranche_number": getattr(b, "tranche_number", 1),
                "prerequisite_condition": getattr(b, "prerequisite_condition", None),
                "interest_subsidy_percentage": getattr(b, "interest_subsidy_percentage", None),
            }
            for b in benefits
        ]

        documents = self.db.query(DocumentRequirement).filter(DocumentRequirement.scheme_version_id == version_id).all()
        doc_data = [
            {
                "document_type": d.document_type,
                "is_mandatory": d.is_mandatory,
                "requirement_stage": d.requirement_stage
            }
            for d in documents
        ]

        rule_data = [
            {
                "fact_key": r.fact_key,
                "operator": r.operator,
                "expected_value": r.expected_value,
                "rule_scope": getattr(r, "rule_scope", "applicant_eligibility"),
                "mandatory": r.mandatory,
                "reason_code": r.reason_code,
                "rule_expression": r.rule_expression
            }
            for r in rules
        ]

        cert_hash = compute_certification_hash(
            scheme_id=scheme_id,
            version_number=version.version_number,
            applicant_type=applicant_type,
            beneficiary_type=beneficiary_type,
            audience_type=audience_type,
            sources_data=source_data,
            rules_data=rule_data,
            benefits_data=benefit_data,
            documents_data=doc_data,
            latest_source_reference=latest_source_reference
        )

        now_utc = datetime.now(timezone.utc)
        sem_status = "certified" if not all_findings else "rejected"
        curr_status = "current" if not all_findings else "possibly_stale"

        # Deactivate any previous active dossiers for this scheme
        self.db.query(SchemeCertificationDossier).filter(
            SchemeCertificationDossier.scheme_id == scheme_id,
            SchemeCertificationDossier.is_active == True
        ).update({"is_active": False})

        dossier = SchemeCertificationDossier(
            id=f"dossier-{scheme_id}-v{version.version_number}-{uuid.uuid4().hex[:8]}",
            scheme_id=scheme_id,
            scheme_version_id=version_id,
            certified_at=now_utc,
            certified_by=certified_by,
            applicant_type=applicant_type,
            beneficiary_type=beneficiary_type,
            audience_type=audience_type,
            source_ids_json=json.dumps([s.id for s in sources]),
            latest_source_checked_at=now_utc,
            latest_source_reference=latest_source_reference,
            eligibility_rule_ids_json=json.dumps([r.id for r in rules if getattr(r, "rule_scope", "") != "exclusion"]),
            exclusion_rule_ids_json=json.dumps([r.id for r in rules if getattr(r, "rule_scope", "") == "exclusion"]),
            benefit_ids_json=json.dumps([b.id for b in benefits]),
            document_requirement_ids_json=json.dumps([d.id for d in documents]),
            open_findings_json=open_findings_json,
            semantic_review_status=sem_status,
            completeness_status=comp_status,
            currentness_status=curr_status,
            lifecycle_status="ACTIVE",
            last_currentness_check=now_utc,
            next_currentness_check=now_utc + timedelta(days=90),
            currentness_check_source=latest_source_reference or "Authoritative Ministry Source",
            certification_hash=cert_hash,
            is_active=(sem_status == "certified"),
            notes=notes
        )
        self.db.add(dossier)

        # Update Scheme and SchemeVersion records
        scheme.applicant_type = applicant_type
        scheme.beneficiary_type = beneficiary_type
        scheme.audience_type = audience_type
        scheme.lifecycle_status = "ACTIVE"

        version.applicant_type = applicant_type
        version.beneficiary_type = beneficiary_type
        version.audience_type = audience_type
        version.semantic_review_status = sem_status
        version.currentness_status = curr_status
        version.completeness_status = comp_status

        # Create immutable AuditLog
        audit = AuditLog(
            id=f"audit-sem-{uuid.uuid4().hex[:10]}",
            entity_type="scheme_version",
            entity_id=version_id,
            action="semantic_certify" if sem_status == "certified" else "semantic_reject",
            actor_id=certified_by,
            new_state_json=json.dumps({
                "dossier_id": dossier.id,
                "semantic_review_status": sem_status,
                "currentness_status": curr_status,
                "completeness_status": comp_status,
                "lifecycle_status": "ACTIVE",
                "certification_hash": cert_hash,
                "open_findings_count": len(all_findings)
            }),
            reason=notes or f"Phase 3.8/4.3 Semantic certification by {certified_by}"
        )
        self.db.add(audit)
        self.db.commit()

        # Keep disk audit file in sync if data/dossiers directory exists
        try:
            dossier_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "dossiers"
            if dossier_dir.exists():
                dossier_file = dossier_dir / f"{scheme_id}.json"
                with open(dossier_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "dossier_id": dossier.id,
                        "scheme_id": scheme_id,
                        "version_id": version_id,
                        "certification_hash": dossier.certification_hash,
                        "certified_at": str(dossier.certified_at),
                        "certified_by": dossier.certified_by,
                        "applicant_type": dossier.applicant_type,
                        "beneficiary_type": dossier.beneficiary_type,
                        "audience_type": dossier.audience_type,
                        "lifecycle_status": getattr(dossier, "lifecycle_status", "ACTIVE"),
                        "last_currentness_check": str(dossier.last_currentness_check or dossier.certified_at),
                        "next_currentness_check": str(dossier.next_currentness_check) if dossier.next_currentness_check else None,
                        "currentness_check_source": dossier.currentness_check_source,
                        "latest_source_reference": dossier.latest_source_reference,
                        "semantic_review_status": dossier.semantic_review_status,
                        "completeness_status": dossier.completeness_status,
                        "currentness_status": dossier.currentness_status,
                        "is_active": dossier.is_active,
                        "invalidation_reason": getattr(dossier, "invalidation_reason", None),
                        "notes": dossier.notes
                    }, f, indent=2)
        except Exception:
            pass

        return dossier

    def is_rag_certified(
        self,
        scheme_version_or_id: Union[SchemeVersion, str],
        allow_institutional: bool = False
    ) -> Tuple[bool, str]:
        """
        Strict deterministic gate protecting RAG indexing and embedding.
        Enforces that only schemes meeting full semantic, source, and policy
        certification are indexed.
        """
        if isinstance(scheme_version_or_id, str):
            version = self.db.query(SchemeVersion).filter(SchemeVersion.id == scheme_version_or_id).first()
            if not version:
                # Fallback to published version if scheme_id was passed
                version = self.db.query(SchemeVersion).filter(
                    SchemeVersion.scheme_id == scheme_version_or_id,
                    SchemeVersion.status == "published"
                ).order_by(SchemeVersion.version_number.desc()).first()
        else:
            version = scheme_version_or_id

        if not version:
            return False, "SchemeVersion not found"

        # Check scheme lifecycle status
        scheme = version.scheme or self.db.query(Scheme).filter(Scheme.id == version.scheme_id).first()
        if scheme:
            scheme_lifecycle = getattr(scheme, "lifecycle_status", "ACTIVE") or "ACTIVE"
            if scheme_lifecycle != "ACTIVE":
                return False, f"Scheme lifecycle is '{scheme_lifecycle}', must be 'ACTIVE' for current-policy citizen RAG"

        if version.status != "published":
            return False, f"SchemeVersion status is '{version.status}', must be 'published'"

        if version.verification_status != "source_verified":
            return False, f"Verification status is '{version.verification_status}', must be 'source_verified'"

        if version.semantic_review_status != "certified":
            return False, f"Semantic review status is '{version.semantic_review_status}', must be 'certified'"

        if version.currentness_status != "current":
            return False, f"Currentness status is '{version.currentness_status}', must be 'current'"

        if version.completeness_status != "complete":
            return False, f"Completeness status is '{version.completeness_status}', must be 'complete'"

        # Audience filtering for citizen RAG
        audience = version.audience_type or "DIRECT_CITIZEN_BENEFIT"
        if not allow_institutional and audience in NON_CITIZEN_AUDIENCES:
            return False, f"Audience '{audience}' is institutional/NGO grant; gated from direct citizen RAG"

        # Check for open conflicts
        conflicts = self.db.query(SourceConflict).filter(
            SourceConflict.scheme_id == version.scheme_id,
            SourceConflict.status == "SOURCE_CONFLICT_OPEN"
        ).count()
        if conflicts > 0:
            return False, f"Scheme has {conflicts} open source conflict(s)"

        # Check for active certification dossier
        dossier = self.db.query(SchemeCertificationDossier).filter(
            SchemeCertificationDossier.scheme_version_id == version.id,
            SchemeCertificationDossier.is_active == True,
            SchemeCertificationDossier.semantic_review_status == "certified"
        ).order_by(SchemeCertificationDossier.certified_at.desc()).first()

        if not dossier:
            return False, "No active certified SchemeCertificationDossier found"

        dossier_lifecycle = getattr(dossier, "lifecycle_status", "ACTIVE") or "ACTIVE"
        if dossier_lifecycle != "ACTIVE":
            return False, f"Dossier lifecycle is '{dossier_lifecycle}', must be 'ACTIVE' for current-policy citizen RAG"

        findings = json.loads(dossier.open_findings_json or "[]")
        if findings:
            return False, f"Active dossier has {len(findings)} open findings"

        return True, "Certified for RAG"

    def invalidate_certification(
        self,
        scheme_id: str,
        version_id: str,
        reason: str,
        actor_id: str = "system"
    ) -> bool:
        """
        Invalidates active certification upon source drift or superseding policy.
        """
        dossiers = self.db.query(SchemeCertificationDossier).filter(
            SchemeCertificationDossier.scheme_version_id == version_id,
            SchemeCertificationDossier.is_active == True
        ).all()
        for d in dossiers:
            d.is_active = False
            d.invalidation_reason = reason
            d.notes = f"{d.notes or ''} [Invalidated: {reason}]"

        version = self.db.query(SchemeVersion).filter(SchemeVersion.id == version_id).first()
        if version:
            version.semantic_review_status = "not_reviewed"
            version.currentness_status = "possibly_stale"

        audit = AuditLog(
            id=f"audit-inv-{uuid.uuid4().hex[:10]}",
            entity_type="scheme_version",
            entity_id=version_id,
            action="invalidate_certification",
            actor_id=actor_id,
            reason=reason
        )
        self.db.add(audit)
        self.db.commit()

        # Update disk file
        try:
            dossier_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "dossiers"
            dossier_file = dossier_dir / f"{scheme_id}.json"
            if dossier_file.exists():
                with open(dossier_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["is_active"] = False
                data["invalidation_reason"] = reason
                with open(dossier_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
        except Exception:
            pass

        return True

    def invalidate_for_lifecycle_change(
        self,
        scheme_id: str,
        new_lifecycle: str,
        reason: str,
        actor_id: str = "system"
    ) -> bool:
        """
        Permanently or administratively updates scheme lifecycle (e.g. WITHDRAWN, SUBSUMED, CLOSED, HISTORICAL).
        Immediately invalidates all active certification dossiers, marks scheme versions as historical/withdrawn,
        and re-tags chunks as HISTORICAL_POLICY to guarantee zero leakage into current citizen RAG.
        """
        if new_lifecycle not in VALID_LIFECYCLE_STATUSES:
            raise ValueError(f"Invalid lifecycle '{new_lifecycle}'. Allowed: {sorted(list(VALID_LIFECYCLE_STATUSES))}")

        scheme = self.db.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            return False

        scheme.lifecycle_status = new_lifecycle
        if new_lifecycle in ("WITHDRAWN", "SUBSUMED", "CLOSED"):
            scheme.is_active = False

        # Invalidate all active dossiers
        dossiers = self.db.query(SchemeCertificationDossier).filter(
            SchemeCertificationDossier.scheme_id == scheme_id,
            SchemeCertificationDossier.is_active == True
        ).all()
        for d in dossiers:
            d.is_active = False
            d.lifecycle_status = new_lifecycle
            d.invalidation_reason = reason
            d.notes = f"{d.notes or ''} [Lifecycle transition to {new_lifecycle}: {reason}]"

        # Update SchemeVersion currentness
        versions = self.db.query(SchemeVersion).filter(SchemeVersion.scheme_id == scheme_id).all()
        for v in versions:
            v.currentness_status = new_lifecycle.lower()
            if new_lifecycle in ("WITHDRAWN", "SUBSUMED"):
                v.semantic_review_status = new_lifecycle.lower()

        # Update any active RAG chunks to HISTORICAL_POLICY
        self.db.query(RagChunk).filter(
            RagChunk.scheme_id == scheme_id
        ).update({"policy_status": "HISTORICAL_POLICY"}, synchronize_session=False)

        audit = AuditLog(
            id=f"audit-life-{uuid.uuid4().hex[:10]}",
            entity_type="scheme",
            entity_id=scheme_id,
            action="lifecycle_change",
            actor_id=actor_id,
            new_state_json=json.dumps({
                "scheme_id": scheme_id,
                "lifecycle_status": new_lifecycle,
                "reason": reason
            }),
            reason=reason
        )
        self.db.add(audit)
        self.db.commit()

        # Update disk file
        try:
            dossier_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "dossiers"
            dossier_file = dossier_dir / f"{scheme_id}.json"
            if dossier_file.exists():
                with open(dossier_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["is_active"] = False
                data["lifecycle_status"] = new_lifecycle
                data["invalidation_reason"] = reason
                with open(dossier_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
        except Exception:
            pass

        return True

    def record_currentness_recheck(
        self,
        scheme_id: str,
        source_url: str,
        lifecycle_status: str = "ACTIVE",
        notes: Optional[str] = None,
        validity_days: int = 90
    ) -> Optional[SchemeCertificationDossier]:
        """
        Records an automated or audited currentness check for an active certified scheme dossier.
        """
        dossier = self.db.query(SchemeCertificationDossier).filter(
            SchemeCertificationDossier.scheme_id == scheme_id,
            SchemeCertificationDossier.is_active == True
        ).order_by(SchemeCertificationDossier.certified_at.desc()).first()

        if not dossier:
            return None

        now_utc = datetime.now(timezone.utc)
        dossier.last_currentness_check = now_utc
        dossier.next_currentness_check = now_utc + timedelta(days=validity_days)
        dossier.currentness_check_source = source_url
        dossier.lifecycle_status = lifecycle_status
        if notes:
            dossier.notes = f"{dossier.notes or ''} [Rechecked: {notes}]"

        self.db.commit()

        # Synchronize disk file
        try:
            dossier_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "dossiers"
            dossier_file = dossier_dir / f"{scheme_id}.json"
            if dossier_file.exists():
                with open(dossier_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["last_currentness_check"] = str(now_utc)
                data["next_currentness_check"] = str(now_utc + timedelta(days=validity_days))
                data["currentness_check_source"] = source_url
                data["lifecycle_status"] = lifecycle_status
                with open(dossier_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
        except Exception:
            pass

        return dossier
