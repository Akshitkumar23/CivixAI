"""
Snapshot Storage Abstraction Layer
Provides a storage interface separating snapshot raw bytes from relational database metadata.
Supports LocalFilesystemStorage for local development and provides extensibility
for production object stores (S3, GCS, Azure Blob, MinIO).
"""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

class SnapshotStorage(ABC):
    """Abstract interface for storing and retrieving raw authoritative source snapshots."""

    @abstractmethod
    def save(self, source_id: str, content_hash: str, data: bytes, content_type: str = "text/html") -> str:
        """
        Saves raw snapshot bytes and returns a persistent storage URI.
        :param source_id: Unique identifier for the source registry entry.
        :param content_hash: Deterministic SHA-256 hash of the content.
        :param data: Raw byte payload of the source document.
        :param content_type: MIME type of the document.
        :return: Canonical storage URI (e.g. file://... or s3://...)
        """
        pass

    @abstractmethod
    def load(self, storage_uri: str) -> bytes:
        """
        Loads and returns raw snapshot bytes from the specified storage URI.
        :param storage_uri: Canonical storage URI returned by save().
        :return: Raw byte payload.
        """
        pass

    @abstractmethod
    def exists(self, storage_uri: str) -> bool:
        """
        Checks whether the snapshot exists at the specified URI.
        """
        pass


class LocalFilesystemStorage(SnapshotStorage):
    """
    Local filesystem implementation of SnapshotStorage.
    Stores immutable snapshots under base_dir/{source_id}/{content_hash}.bin.
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            self.base_dir = project_root / "data" / "snapshots"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, source_id: str, content_hash: str) -> Path:
        clean_source_id = "".join(c for c in source_id if c.isalnum() or c in ("-", "_"))
        source_folder = self.base_dir / clean_source_id
        source_folder.mkdir(parents=True, exist_ok=True)
        return source_folder / f"{content_hash}.bin"

    def save(self, source_id: str, content_hash: str, data: bytes, content_type: str = "text/html") -> str:
        target_file = self._resolve_path(source_id, content_hash)
        if not target_file.exists():
            target_file.write_bytes(data)
        # Return canonical storage URI
        return f"file://{target_file.resolve().as_posix()}"

    def load(self, storage_uri: str) -> bytes:
        if storage_uri.startswith("file://"):
            local_path = Path(storage_uri[7:])
        else:
            local_path = Path(storage_uri)

        if not local_path.exists():
            raise FileNotFoundError(f"Snapshot not found at URI: {storage_uri}")
        return local_path.read_bytes()

    def exists(self, storage_uri: str) -> bool:
        if storage_uri.startswith("file://"):
            local_path = Path(storage_uri[7:])
        else:
            local_path = Path(storage_uri)
        return local_path.exists()


class CloudObjectStorageStub(SnapshotStorage):
    """
    Cloud object storage adapter specification (for S3, GCS, MinIO, Azure Blob).
    Configurable via environment variables (e.g. S3_BUCKET_NAME, AWS_REGION).
    """

    def __init__(self, bucket_name: str, endpoint_url: Optional[str] = None):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url

    def save(self, source_id: str, content_hash: str, data: bytes, content_type: str = "text/html") -> str:
        # In cloud environments with boto3 / google-cloud-storage:
        # s3.put_object(Bucket=self.bucket_name, Key=f"{source_id}/{content_hash}.bin", Body=data, ContentType=content_type)
        return f"s3://{self.bucket_name}/{source_id}/{content_hash}.bin"

    def load(self, storage_uri: str) -> bytes:
        raise NotImplementedError("CloudObjectStorage requires configured S3/GCS credentials.")

    def exists(self, storage_uri: str) -> bool:
        return False


def get_default_storage() -> SnapshotStorage:
    """Factory function returning the configured snapshot storage engine."""
    cloud_bucket = os.getenv("CIVIX_SNAPSHOT_BUCKET")
    if cloud_bucket:
        return CloudObjectStorageStub(bucket_name=cloud_bucket)
    return LocalFilesystemStorage()
