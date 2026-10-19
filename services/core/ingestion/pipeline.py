"""
Ingestion Pipeline Orchestrator
Executes the full ingestion lifecycle:
Source Registry -> Rate-limited Fetch -> Content Hashing -> Snapshot Storage ->
Parser -> Extraction -> Structured Diff -> Data Quality Audit -> Staging ChangeSet.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from services.core.database.models import (
    SourceRegistry, SourceSnapshot, IngestionRun, SchemeChangeSet,
    RuleDraft, BenefitDraft, DocumentRequirementDraft, Scheme, SchemeVersion
)
from .fetcher import SourceFetcher
from .snapshot import SnapshotService
from .parser import DocumentParser
from .extractor import RuleExtractor
from .diff_engine import DiffEngine
from .quality import DataQualityEngine

class IngestionPipeline:
    def __init__(self, db: Session, fetcher: Optional[SourceFetcher] = None):
        self.db = db
        self.fetcher = fetcher or SourceFetcher()
        self.snapshot_service = SnapshotService(db)

    def run_for_source(
        self,
        source_id: str,
        mock_content: Optional[bytes] = None,
        ingestion_run_id: Optional[str] = None,
        scheme_id: Optional[str] = None
    ) -> Optional[SchemeChangeSet]:
        """
        Executes end-to-end ingestion for a single registered source.
        Returns newly created SchemeChangeSet if changes detected, else None.
        """
        source = self.db.query(SourceRegistry).filter(SourceRegistry.id == source_id).first()
        if not source:
            raise ValueError(f"Source '{source_id}' not found.")

        # 1. Fetch content (or use mock for testing)
        content: bytes
        content_type = source.content_type or "text/html"
        etag: Optional[str] = None
        last_modified: Optional[str] = None

        if mock_content is not None:
            content = mock_content
            http_status = 200
        else:
            fetch_res = self.fetcher.fetch(
                source.canonical_url,
                etag=None, # Fresh check
                last_modified=None
            )
            if not fetch_res.success:
                source.freshness_status = "unreachable"
                source.last_checked_at = datetime.now(timezone.utc)
                self.db.commit()
                return None

            content = fetch_res.content
            content_type = fetch_res.content_type
            etag = fetch_res.etag
            last_modified = fetch_res.last_modified
            http_status = fetch_res.status_code

        # 2. Immutable Snapshot creation & deduplication check
        snapshot, is_changed = self.snapshot_service.create_snapshot(
            source_registry_id=source.id,
            content=content,
            content_type=content_type,
            etag=etag,
            last_modified=last_modified,
            http_status=http_status
        )

        if not is_changed:
            # Content has not changed since last snapshot!
            return None

        # 3. Locate target scheme (e.g. by matching authority, or first associated scheme)
        scheme = None
        if scheme_id:
            scheme = self.db.query(Scheme).filter(Scheme.id == scheme_id).first()

        if not scheme:
            matching_ver = self.db.query(SchemeVersion).filter(
                (SchemeVersion.source_url == source.canonical_url) |
                (SchemeVersion.application_url == source.canonical_url)
            ).first()
            if matching_ver:
                scheme = self.db.query(Scheme).filter(Scheme.id == matching_ver.scheme_id).first()

        if not scheme and source.authority_id:
            scheme = self.db.query(Scheme).filter(Scheme.authority_id == source.authority_id).first()

        if not scheme:
            # Fallback: find any scheme or create candidate placeholder
            scheme = self.db.query(Scheme).first()

        if not scheme:
            return None

        # 4. Parse document
        parsed_doc = DocumentParser.parse(content, content_type=content_type, title=source.title)

        # 5. Extract candidate drafts
        candidate = RuleExtractor.extract_from_document(parsed_doc, source_snapshot_id=snapshot.id)

        # 6. Load current active production SchemeVersion
        active_version = self.db.query(SchemeVersion).filter(
            SchemeVersion.scheme_id == scheme.id,
            SchemeVersion.status == "published"
        ).order_by(SchemeVersion.version_number.desc()).first()

        # 7. Compute structured semantic diff
        diff = DiffEngine.compare(active_version, candidate)

        # 8. Create staging SchemeChangeSet (isolated from production!)
        changeset_id = f"cs-{uuid.uuid4().hex[:12]}"
        changeset = SchemeChangeSet(
            id=changeset_id,
            scheme_id=scheme.id,
            source_snapshot_id=snapshot.id,
            ingestion_run_id=ingestion_run_id,
            status="pending",
            change_summary=candidate.proposed_summary or diff.summary,
            structured_diff_json=json.dumps(diff.to_dict()),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(changeset)

        # 9. Create RuleDraft, BenefitDraft, and DocumentRequirementDraft items
        for r in candidate.rule_drafts:
            rule_draft = RuleDraft(
                id=f"rdraft-{uuid.uuid4().hex[:12]}",
                changeset_id=changeset_id,
                fact_key=r["fact_key"],
                operator=r["operator"],
                expected_value=r["expected_value"],
                rule_expression=r.get("rule_expression"),
                mandatory=r.get("mandatory", True),
                scope=r.get("scope", "applicant"),
                reason_code=r.get("reason_code", "INGESTION_EXTRACTED"),
                source_fragment=r.get("source_fragment"),
                change_type="added"
            )
            self.db.add(rule_draft)

        for b in candidate.benefit_drafts:
            ben_draft = BenefitDraft(
                id=f"bdraft-{uuid.uuid4().hex[:12]}",
                changeset_id=changeset_id,
                benefit_type=b.get("benefit_type", "cash_transfer"),
                amount_type=b.get("amount_type", "fixed"),
                fixed_amount=b.get("fixed_amount"),
                min_amount=b.get("min_amount"),
                max_amount=b.get("max_amount"),
                frequency=b.get("frequency", "yearly"),
                description=b.get("description"),
                source_fragment=b.get("source_fragment"),
                change_type="added"
            )
            self.db.add(ben_draft)

        for d in candidate.document_drafts:
            doc_draft = DocumentRequirementDraft(
                id=f"ddraft-{uuid.uuid4().hex[:12]}",
                changeset_id=changeset_id,
                document_type=d["document_type"],
                is_mandatory=d.get("is_mandatory", True),
                source_fragment=d.get("source_fragment"),
                change_type="added"
            )
            self.db.add(doc_draft)

        # 10. Audit against Data Quality Engine
        quality_report = DataQualityEngine.audit_changeset(changeset, source=source)
        changeset.quality_report_json = json.dumps(quality_report.to_dict())

        self.db.commit()
        self.db.refresh(changeset)
        return changeset

    def run_batch(self, source_ids: Optional[List[str]] = None) -> IngestionRun:
        """Executes batch ingestion over all or specified registered sources."""
        run = IngestionRun(
            id=f"run-{uuid.uuid4().hex[:12]}",
            started_at=datetime.now(timezone.utc),
            status="running",
            sources_checked=0,
            sources_changed=0,
            changesets_created=0
        )
        self.db.add(run)
        self.db.commit()

        sources = self.db.query(SourceRegistry)
        if source_ids:
            sources = sources.filter(SourceRegistry.id.in_(source_ids))
        all_sources = sources.all()

        changed_count = 0
        created_count = 0
        errors = []

        for src in all_sources:
            run.sources_checked += 1
            try:
                cs = self.run_for_source(src.id, ingestion_run_id=run.id)
                if cs:
                    changed_count += 1
                    created_count += 1
            except Exception as e:
                errors.append({"source_id": src.id, "error": str(e)})

        run.sources_changed = changed_count
        run.changesets_created = created_count
        run.completed_at = datetime.now(timezone.utc)
        run.status = "completed" if not errors else "completed_with_errors"
        run.errors_json = json.dumps(errors) if errors else None

        self.db.commit()
        self.db.refresh(run)
        return run
