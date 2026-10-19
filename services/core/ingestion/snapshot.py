"""
Source Snapshot Service
Handles immutable content snapshotting, SHA-256 hashing, and deduplication.
"""
import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session

from services.core.database.models import SourceSnapshot, SourceRegistry
from services.core.ingestion.storage import SnapshotStorage, get_default_storage, LocalFilesystemStorage

def compute_content_hash(content: bytes) -> str:
    """Computes deterministic SHA-256 hash of raw content bytes."""
    return hashlib.sha256(content).hexdigest()

class SnapshotService:
    def __init__(self, db: Session, storage: Optional[SnapshotStorage] = None, base_dir: Optional[Path] = None):
        self.db = db
        if storage:
            self.storage = storage
        elif base_dir:
            self.storage = LocalFilesystemStorage(base_dir=str(base_dir))
        else:
            self.storage = get_default_storage()

    def create_snapshot(
        self,
        source_registry_id: str,
        content: bytes,
        content_type: str = "text/html",
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        http_status: int = 200,
        parser_version: str = "1.0.0"
    ) -> Tuple[SourceSnapshot, bool]:
        """
        Creates or references an immutable content snapshot.
        Returns (SourceSnapshot, is_changed).
        If content has not changed compared to latest snapshot, returns (latest_snapshot, False).
        """
        content_hash = compute_content_hash(content)
        raw_size = len(content)

        # Check existing latest snapshot for this source
        latest_snapshot = self.db.query(SourceSnapshot).filter(
            SourceSnapshot.source_registry_id == source_registry_id
        ).order_by(SourceSnapshot.fetched_at.desc()).first()

        if latest_snapshot and latest_snapshot.content_hash == content_hash:
            # Content is identical to previous fetch - deduplicated!
            # Update source last_checked_at
            source = self.db.query(SourceRegistry).filter(SourceRegistry.id == source_registry_id).first()
            if source:
                source.last_checked_at = datetime.now(timezone.utc)
                self.db.commit()
            return latest_snapshot, False

        # Content has changed or this is the first snapshot
        storage_uri = self.storage.save(
            source_id=source_registry_id,
            content_hash=content_hash,
            data=content,
            content_type=content_type
        )

        snapshot = SourceSnapshot(
            id=f"snap-{uuid.uuid4().hex[:12]}",
            source_registry_id=source_registry_id,
            content_hash=content_hash,
            content_type=content_type,
            storage_path=storage_uri,
            etag=etag,
            last_modified=last_modified,
            http_status=http_status,
            fetched_at=datetime.now(timezone.utc),
            parser_version=parser_version,
            raw_size_bytes=raw_size,
            is_duplicate=False
        )
        self.db.add(snapshot)

        # Update SourceRegistry metadata
        source = self.db.query(SourceRegistry).filter(SourceRegistry.id == source_registry_id).first()
        if source:
            source.last_checked_at = datetime.now(timezone.utc)
            source.last_changed_at = datetime.now(timezone.utc)
            source.current_hash = content_hash
            source.freshness_status = "source_changed" if latest_snapshot else "fresh"

        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot, True

    def get_snapshot_content(self, snapshot: SourceSnapshot) -> Optional[bytes]:
        """Reads raw content bytes from storage."""
        if not snapshot.storage_path:
            return None
        try:
            return self.storage.load(snapshot.storage_path)
        except Exception:
            # Fallback to direct path read if legacy local path exists
            if os.path.exists(snapshot.storage_path):
                with open(snapshot.storage_path, "rb") as f:
                    return f.read()
            return None
