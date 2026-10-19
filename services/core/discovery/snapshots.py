"""
Durable Raw Source Snapshot & Content Hashing Store
===================================================
Manages immutable, reproducible raw document snapshots.
Enforces:
- content_sha256 computed strictly from actual raw response bytes
- Storage of raw byte payloads under data/snapshots/
- Conditional header handling (If-None-Match, If-Modified-Since)
- Change detection (UNCHANGED, MODIFIED, NEW, NOT_MODIFIED)
"""

import os
import hashlib
import json
import gzip
from pathlib import Path
from typing import Optional, Dict, Tuple, Any
from datetime import datetime, timezone

from services.core.discovery.models import (
    SourceSnapshotRecord,
    SnapshotChangeStatus,
)

SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_INDEX_FILE = SNAPSHOT_DIR / "snapshot_index.json"


def compute_raw_content_sha256(content: bytes) -> str:
    """
    Computes SHA-256 strictly over the raw content byte array.
    Guarantees: Two identical responses produce identical hashes.
    One-byte content change produces a different hash.
    """
    if not isinstance(content, bytes):
        raise TypeError(f"content must be bytes, got {type(content).__name__}")
    return hashlib.sha256(content).hexdigest()


class DurableSnapshotStore:
    """
    Durable storage engine for immutable raw web page and API response snapshots.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or SNAPSHOT_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.payloads_dir = self.base_dir / "raw_payloads"
        self.payloads_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_dir / "snapshot_index.json"
        self._index: Dict[str, Dict[str, Any]] = self._load_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self) -> None:
        temp_file = self.index_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)
        temp_file.replace(self.index_file)

    def get_latest_snapshot(self, canonical_url: str) -> Optional[SourceSnapshotRecord]:
        """
        Retrieves metadata of the most recent snapshot for a canonical URL.
        """
        data = self._index.get(canonical_url)
        if data:
            return SourceSnapshotRecord(**data)
        return None

    def detect_change(
        self,
        prev_snapshot: Optional[SourceSnapshotRecord],
        new_status_code: int,
        new_content: bytes,
        new_etag: Optional[str] = None,
    ) -> SnapshotChangeStatus:
        """
        Determines the change status comparing incoming HTTP response with previous snapshot.
        """
        if new_status_code == 304:
            return SnapshotChangeStatus.NOT_MODIFIED

        if prev_snapshot is None:
            return SnapshotChangeStatus.NEW

        # Check ETag match
        if new_etag and prev_snapshot.etag and new_etag == prev_snapshot.etag:
            return SnapshotChangeStatus.UNCHANGED

        # Check true content SHA-256
        new_hash = compute_raw_content_sha256(new_content)
        if new_hash == prev_snapshot.content_sha256:
            return SnapshotChangeStatus.UNCHANGED

        return SnapshotChangeStatus.MODIFIED

    def record_snapshot(
        self,
        source_id: str,
        url: str,
        canonical_url: str,
        http_status: int,
        content: bytes,
        content_type: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        response_headers: Optional[Dict[str, str]] = None,
        crawl_run_id: Optional[str] = None,
    ) -> SourceSnapshotRecord:
        """
        Persists a durable raw snapshot and indexes its content hash.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        prev_snapshot = self.get_latest_snapshot(canonical_url)

        change_status = self.detect_change(
            prev_snapshot, http_status, content, etag
        )

        content_hash = compute_raw_content_sha256(content)
        content_len = len(content)

        # Unique immutable snapshot ID based on source + hash + timestamp
        ts_slug = now_iso.replace(":", "").replace("-", "")[:15]
        snapshot_id = f"snap-{source_id[:12]}-{content_hash[:12]}-{ts_slug}"

        # Write raw bytes to compressed payload file
        storage_filename = f"{snapshot_id}.raw.gz"
        storage_path = self.payloads_dir / storage_filename
        with gzip.open(storage_path, "wb") as f_out:
            f_out.write(content)

        first_seen_at = prev_snapshot.first_seen_at if prev_snapshot and prev_snapshot.first_seen_at else now_iso
        last_seen_at = now_iso

        record = SourceSnapshotRecord(
            snapshot_id=snapshot_id,
            source_id=source_id,
            url=url,
            canonical_url=canonical_url,
            retrieved_at=now_iso,
            http_status=http_status,
            content_type=content_type,
            content_length=content_len,
            content_sha256=content_hash,
            etag=etag,
            last_modified=last_modified,
            response_headers=response_headers or {},
            storage_uri=str(storage_path),
            parser_version="2.0.0",
            crawl_run_id=crawl_run_id,
            previous_snapshot_id=prev_snapshot.snapshot_id if prev_snapshot else None,
            previous_content_sha256=prev_snapshot.content_sha256 if prev_snapshot else None,
            change_status=change_status.value,
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
        )

        # Update persistent index
        self._index[canonical_url] = record.to_dict()
        self._save_index()

        return record

    def generate_freshness_report(self, output_path: Path) -> Dict[str, Any]:
        """
        Generates a structured freshness and version change report across all tracked resources.
        """
        records = [SourceSnapshotRecord(**d) for d in self._index.values()]
        status_counts = {}
        for r in records:
            status_counts[r.change_status] = status_counts.get(r.change_status, 0) + 1

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_tracked_urls": len(records),
            "change_status_counts": status_counts,
            "items": [
                {
                    "url": r.url,
                    "canonical_url": r.canonical_url,
                    "snapshot_id": r.snapshot_id,
                    "content_sha256": r.content_sha256,
                    "previous_content_sha256": r.previous_content_sha256,
                    "change_status": r.change_status,
                    "first_seen_at": r.first_seen_at,
                    "last_seen_at": r.last_seen_at,
                    "http_status": r.http_status,
                    "etag": r.etag,
                }
                for r in records
            ],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    def load_raw_payload(self, snapshot_record: SourceSnapshotRecord) -> bytes:
        """
        Decompresses and returns the exact raw byte payload for verification.
        """
        if not snapshot_record.storage_uri:
            raise FileNotFoundError("Snapshot has no storage_uri recorded.")
        path = Path(snapshot_record.storage_uri)
        if not path.exists():
            raise FileNotFoundError(f"Snapshot storage file not found: {path}")
        with gzip.open(path, "rb") as f_in:
            return f_in.read()
