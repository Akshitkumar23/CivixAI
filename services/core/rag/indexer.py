"""
RAG Indexing Pipeline
Phase 4: Verified-Only Hybrid Retrieval & Grounded RAG

Extracts, chunks, and indexes official source documents & guidelines for certified
citizen schemes. Enforces `is_rag_certified(version)` invariant before inserting chunks.
Synchronizes the SQLite FTS5 virtual table and in-memory dense vector representations.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from services.core.database.models import (
    Scheme, SchemeVersion, SourceDocument, SourceSnapshot,
    RagDocument, RagChunk, RagIndexRun, SchemeCertificationDossier
)
from services.core.ingestion.semantic import SemanticCertificationEngine
from services.core.rag.chunker import StructureAwareChunker
from services.core.rag.fts_manager import FtsManager


from services.core.rag.corpus import CERTIFIED_SCHEMES_OFFICIAL_CORPUS


class RagIndexingPipeline:
    """
    Builds and maintains the RAG index for certified citizen schemes with
    atomic generation lifecycle support and instant rollbacks.
    """

    def __init__(self, db: Session, fts_manager: FtsManager, retriever: Optional[Any] = None):
        self.db = db
        self.fts_manager = fts_manager
        self.retriever = retriever
        self.cert_engine = SemanticCertificationEngine(db)

    def get_active_generation_id(self) -> Optional[str]:
        """
        Returns the generation_id of currently active RagChunks, if any.
        """
        active_chunk = self.db.query(RagChunk).filter(RagChunk.is_active == True).first()
        return active_chunk.generation_id if active_chunk else None

    def get_generations(self) -> List[Dict[str, Any]]:
        """
        Returns an audit list of all known index generations and their status.
        """
        runs = self.db.query(RagIndexRun).order_by(RagIndexRun.started_at.desc()).all()
        result = []
        for r in runs:
            chunk_cnt = self.db.query(RagChunk).filter(RagChunk.generation_id == r.generation_id).count()
            result.append({
                "run_id": r.id,
                "generation_id": r.generation_id,
                "generation_status": r.generation_status,
                "status": r.status,
                "schemes_indexed": r.schemes_indexed,
                "chunks_created": r.chunks_created,
                "total_chunks_in_db": chunk_cnt,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            })
        return result

    def run_indexing(
        self,
        generation_id: Optional[str] = None,
        corpus: Optional[Dict[str, Any]] = None,
        fail_on_scheme_id: Optional[str] = None,
        raise_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Executes an atomic RAG indexing run:
        1. Allocates staging generation_id (e.g. gen-YYYYMMDD-HHMMSS-uuid).
        2. Creates new chunks and documents under staging generation with is_active=False.
        3. Populates SQLite FTS5 table with staging entries (is_active=0).
        4. Verifies RAG certification invariant for each candidate scheme.
        5. If indexing succeeds for all certified schemes, executes atomic swap:
           - Deactivates previous active generation (is_active=False, generation_status="superseded").
           - Activates new generation (is_active=True, generation_status="active").
           - Atomically activates SQLite FTS5 entries.
        6. If any failure occurs, immediately rolls back staging chunks and documents,
           leaving the prior active generation 100% untouched.
        """
        now_utc = datetime.now(timezone.utc)
        if not generation_id:
            gen_timestamp = now_utc.strftime("%Y%m%d-%H%M%S")
            generation_id = f"gen-{gen_timestamp}-{uuid.uuid4().hex[:6]}"

        run_id = f"idxrun-{uuid.uuid4().hex[:8]}"

        index_run = RagIndexRun(
            id=run_id,
            generation_id=generation_id,
            generation_status="staging",
            started_at=now_utc,
            status="running"
        )
        self.db.add(index_run)
        self.db.commit()

        # Ensure FTS5 table schema is ready (non-destructive)
        self.fts_manager.ensure_table()

        target_corpus = corpus or CERTIFIED_SCHEMES_OFFICIAL_CORPUS
        total_chunks_indexed = 0
        indexed_schemes: List[str] = []
        rejected_schemes: List[Any] = []
        staging_fts_records: List[Dict[str, Any]] = []

        try:
            for scheme_id, scheme_data in target_corpus.items():
                # Simulated failure hook for testing failure resilience
                if fail_on_scheme_id and scheme_id == fail_on_scheme_id:
                    raise RuntimeError(f"Simulated indexing failure on scheme '{scheme_id}'")

                scheme = self.db.query(Scheme).filter(Scheme.id == scheme_id).first()
                if not scheme:
                    rejected_schemes.append((scheme_id, "Scheme not found in database"))
                    continue

                latest_version = self.db.query(SchemeVersion).filter(
                    SchemeVersion.scheme_id == scheme_id,
                    SchemeVersion.status == "published"
                ).order_by(SchemeVersion.version_number.desc()).first()

                if not latest_version:
                    rejected_schemes.append((scheme_id, "No published SchemeVersion"))
                    continue

                # Strict Certification Gate
                is_cert, cert_reason = self.cert_engine.is_rag_certified(latest_version.id, allow_institutional=False)
                is_historical = scheme.lifecycle_status in ("WITHDRAWN", "SUBSUMED", "CLOSED", "HISTORICAL")
                
                if not is_cert and not is_historical:
                    rejected_schemes.append((scheme_id, f"Failed RAG certification: {cert_reason}"))
                    continue
                elif not is_cert and is_historical:
                    # Record rejection from current-policy RAG, but preserve historical archive chunks
                    rejected_schemes.append((scheme_id, f"Failed RAG certification: {cert_reason}"))

                policy_status = "HISTORICAL_POLICY" if is_historical else "CURRENT_POLICY"
                gen_status = "historical" if is_historical else "staging"

                # Create staging RagDocument
                doc_id = f"ragdoc-{scheme_id}-v{latest_version.version_number}-{generation_id}"
                content_concat = " ".join([s["content"] for s in scheme_data["sections"]])
                doc_hash = hashlib.sha256(content_concat.encode("utf-8")).hexdigest()

                rag_doc = RagDocument(
                    id=doc_id,
                    scheme_id=scheme_id,
                    scheme_version_id=latest_version.id,
                    source_url=scheme_data["source_url"],
                    document_title=scheme_data["doc_title"],
                    content_hash=doc_hash,
                    doc_type=scheme_data["doc_type"],
                    generation_id=generation_id,
                    generation_status=gen_status,
                    is_active=False,
                    created_at=now_utc
                )
                self.db.add(rag_doc)

                # Structure-aware chunking
                chunks_spec = StructureAwareChunker.chunk_official_scheme_corpus(
                    scheme_id=scheme_id,
                    scheme_name=scheme_data["scheme_name"],
                    scheme_version_id=latest_version.id,
                    document_id=doc_id,
                    raw_sections=scheme_data["sections"],
                    source_url=scheme_data["source_url"],
                    source_title=scheme_data["doc_title"],
                    effective_from=scheme_data.get("effective_from"),
                    effective_to=scheme_data.get("effective_to"),
                    currentness=scheme_data.get("currentness", "current")
                )

                for spec in chunks_spec:
                    chunk_id = f"{spec['id']}-{generation_id}"
                    chunk = RagChunk(
                        id=chunk_id,
                        document_id=doc_id,
                        scheme_id=scheme_id,
                        scheme_version_id=latest_version.id,
                        section_type=spec["section_type"],
                        heading_path=spec["heading_path"],
                        content=spec["content"],
                        char_length=spec["char_length"],
                        token_estimate=spec["token_estimate"],
                        chunk_hash=spec["chunk_hash"],
                        source_citation=spec["source_citation"],
                        source_url=spec["source_url"],
                        metadata_json=spec["metadata_json"],
                        generation_id=generation_id,
                        generation_status=gen_status,
                        policy_status=policy_status,
                        is_active=False,
                        created_at=now_utc
                    )
                    self.db.add(chunk)

                    # Only current-policy chunks enter active lexical FTS5 index
                    if not is_historical:
                        staging_fts_records.append({
                            "chunk_id": chunk_id,
                            "content": spec["content"],
                            "heading_path": spec["heading_path"],
                            "section_type": spec["section_type"],
                            "scheme_id": scheme_id,
                            "generation_id": generation_id,
                            "is_active": False
                        })

                if not is_historical:
                    total_chunks_indexed += len(chunks_spec)
                    indexed_schemes.append(scheme_data["scheme_name"])


            # Bulk insert staging entries into SQLite FTS5 table
            if staging_fts_records:
                self.fts_manager.bulk_insert_chunks(staging_fts_records)

            self.db.flush()

            # Atomic Swap: Deactivate previous generation and activate staging generation
            self._atomic_swap_generation(
                generation_id=generation_id,
                index_run=index_run,
                indexed_schemes=indexed_schemes,
                rejected_schemes=rejected_schemes,
                total_chunks_indexed=total_chunks_indexed
            )

        except Exception as exc:
            # Immediate rollback of staging chunks & documents
            self._rollback_staging(generation_id=generation_id, index_run=index_run, error_msg=str(exc))
            if raise_on_error:
                raise
            return {
                "run_id": run_id,
                "generation_id": generation_id,
                "status": "failed",
                "error": str(exc),
                "schemes_indexed_count": 0,
                "total_chunks_created": 0
            }

        return {
            "run_id": run_id,
            "generation_id": generation_id,
            "status": "completed",
            "schemes_indexed_count": len(indexed_schemes),
            "indexed_schemes": indexed_schemes,
            "rejected_schemes": rejected_schemes,
            "total_chunks_created": total_chunks_indexed
        }

    def _atomic_swap_generation(
        self,
        generation_id: str,
        index_run: RagIndexRun,
        indexed_schemes: List[str],
        rejected_schemes: List[Any],
        total_chunks_indexed: int
    ):
        """
        Atomically promotes staging generation to active and marks previous active as superseded.
        """
        from sqlalchemy import or_

        # 1. Deactivate currently active chunks and documents
        self.db.query(RagChunk).filter(
            RagChunk.is_active == True,
            or_(RagChunk.generation_id != generation_id, RagChunk.generation_id.is_(None))
        ).update({
            RagChunk.is_active: False,
            RagChunk.generation_status: "superseded"
        }, synchronize_session=False)

        self.db.query(RagDocument).filter(
            RagDocument.is_active == True,
            or_(RagDocument.generation_id != generation_id, RagDocument.generation_id.is_(None))
        ).update({
            RagDocument.is_active: False,
            RagDocument.generation_status: "superseded"
        }, synchronize_session=False)

        self.db.query(RagIndexRun).filter(
            RagIndexRun.generation_status == "active",
            RagIndexRun.id != index_run.id
        ).update({
            RagIndexRun.generation_status: "superseded"
        }, synchronize_session=False)

        # 2. Activate new generation chunks and documents (only CURRENT_POLICY)
        self.db.query(RagChunk).filter(
            RagChunk.generation_id == generation_id,
            RagChunk.policy_status == "CURRENT_POLICY"
        ).update({
            RagChunk.is_active: True,
            RagChunk.generation_status: "active"
        }, synchronize_session=False)

        self.db.query(RagDocument).filter(
            RagDocument.generation_id == generation_id,
            RagDocument.generation_status == "staging"
        ).update({
            RagDocument.is_active: True,
            RagDocument.generation_status: "active"
        }, synchronize_session=False)


        # 3. Update index run record
        now_utc = datetime.now(timezone.utc)
        index_run.completed_at = now_utc
        index_run.schemes_indexed = len(indexed_schemes)
        index_run.chunks_created = total_chunks_indexed
        index_run.status = "completed"
        index_run.generation_status = "active"
        index_run.run_log_json = json.dumps({
            "generation_id": generation_id,
            "indexed_schemes": indexed_schemes,
            "rejected_schemes": rejected_schemes,
            "total_chunks": total_chunks_indexed
        })
        self.db.commit()

        # 4. Atomically synchronize SQLite FTS5 table
        self.fts_manager.activate_generation(generation_id)

        # 5. Refresh dense index if retriever is attached
        if self.retriever and hasattr(self.retriever, "refresh_dense_index"):
            self.retriever.refresh_dense_index()

    def _rollback_staging(self, generation_id: str, index_run: Optional[RagIndexRun], error_msg: str):
        """
        Rolls back staging generation upon failure:
        - Rolls back uncommitted session changes
        - Deletes staging RagChunks and RagDocuments with generation_id
        - Deletes staging entries from SQLite FTS5 table
        - Updates index_run record to status="failed", generation_status="failed"
        - Leaves previous active generation 100% untouched
        """
        self.db.rollback()
        try:
            self.db.query(RagChunk).filter(RagChunk.generation_id == generation_id).delete(synchronize_session=False)
            self.db.query(RagDocument).filter(RagDocument.generation_id == generation_id).delete(synchronize_session=False)

            if index_run:
                failed_run = self.db.query(RagIndexRun).filter(RagIndexRun.id == index_run.id).first()
                if failed_run:
                    failed_run.status = "failed"
                    failed_run.generation_status = "failed"
                    failed_run.completed_at = datetime.now(timezone.utc)
                    failed_run.run_log_json = json.dumps({"error": error_msg})

            self.db.commit()
        except Exception:
            self.db.rollback()

        try:
            self.fts_manager.delete_generation(generation_id)
        except Exception:
            pass

    def rollback_to_generation(self, previous_generation_id: str) -> Dict[str, Any]:
        """
        Instantly rolls back the active index to a previous generation:
        1. Verifies that previous_generation_id exists and has chunks.
        2. Deactivates the currently active generation.
        3. Activates all RagChunks and RagDocuments for previous_generation_id.
        4. Synchronizes SQLite FTS5 table to activate previous_generation_id.
        5. Updates RagIndexRun statuses.
        6. Returns rollback audit summary.
        """
        total_gen_chunks = self.db.query(RagChunk).filter(RagChunk.generation_id == previous_generation_id).count()
        if total_gen_chunks == 0:
            raise ValueError(f"Target generation '{previous_generation_id}' has no indexed chunks or does not exist.")

        target_chunks_count = self.db.query(RagChunk).filter(
            RagChunk.generation_id == previous_generation_id,
            RagChunk.policy_status == "CURRENT_POLICY"
        ).count()

        # Identify current active generation
        current_active = self.db.query(RagChunk).filter(RagChunk.is_active == True).first()
        current_active_gen_id = current_active.generation_id if current_active else None

        # 1. Deactivate currently active generation in DB
        self.db.query(RagChunk).filter(RagChunk.is_active == True).update({
            RagChunk.is_active: False,
            RagChunk.generation_status: "superseded"
        }, synchronize_session=False)

        self.db.query(RagDocument).filter(RagDocument.is_active == True).update({
            RagDocument.is_active: False,
            RagDocument.generation_status: "superseded"
        }, synchronize_session=False)

        self.db.query(RagIndexRun).filter(RagIndexRun.generation_status == "active").update({
            RagIndexRun.generation_status: "superseded"
        }, synchronize_session=False)

        # 2. Activate target previous generation in DB (ONLY CURRENT_POLICY)
        self.db.query(RagChunk).filter(
            RagChunk.generation_id == previous_generation_id,
            RagChunk.policy_status == "CURRENT_POLICY"
        ).update({
            RagChunk.is_active: True,
            RagChunk.generation_status: "active"
        }, synchronize_session=False)

        self.db.query(RagDocument).filter(
            RagDocument.generation_id == previous_generation_id,
            RagDocument.generation_status != "historical"
        ).update({
            RagDocument.is_active: True,
            RagDocument.generation_status: "active"
        }, synchronize_session=False)

        prev_run = self.db.query(RagIndexRun).filter(RagIndexRun.generation_id == previous_generation_id).first()
        if prev_run:
            prev_run.generation_status = "active"

        self.db.commit()

        # 3. Synchronize SQLite FTS5 table
        self.fts_manager.rollback_to_generation(previous_generation_id)

        # 4. Refresh dense index if retriever is attached
        if self.retriever and hasattr(self.retriever, "refresh_dense_index"):
            self.retriever.refresh_dense_index()

        return {
            "status": "rolled_back",
            "previous_generation_id": previous_generation_id,
            "deactivated_generation_id": current_active_gen_id,
            "restored_chunks_count": target_chunks_count
        }
