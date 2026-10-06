from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import Protocol, runtime_checkable

try:
    import boto3
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)


@runtime_checkable
class ReportStore(Protocol):
    """Protocol for report storage backends."""

    def save(self, local_paths: list[Path], session_id: str) -> list[str]:
        """Save report files and return their URIs.

        Args:
            local_paths: List of local file paths to store.
            session_id: Session identifier for organizing stored files.

        Returns:
            List of URIs where files were stored.
        """
        ...


class LocalStore:
    """Local filesystem storage - no-op that returns local paths as file:// URIs."""

    def save(self, local_paths: list[Path], session_id: str) -> list[str]:
        """Return file:// URIs for local paths."""
        uris = []
        for path in local_paths:
            resolved = path.resolve()
            uris.append(f"file://{resolved}")
        return uris


class S3Store:
    """S3 storage backend using boto3.

    Requires boto3 to be installed. Credentials are obtained from the default
    credential chain (EKS Pod Identity, IAM roles, environment variables, etc.).
    Never hardcode credentials in code.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "reports",
        client=None,
    ):
        """Initialize S3Store.

        Args:
            bucket: S3 bucket name.
            prefix: Prefix for stored objects (default: "reports").
            client: Optional boto3 S3 client (for testing).
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self._client = client

    def _get_client(self):
        """Get or create boto3 S3 client."""
        if self._client is not None:
            return self._client
        if boto3 is None:
            raise RuntimeError("boto3 is required for S3 storage. Install with: pip install boto3")
        self._client = boto3.client("s3")
        return self._client

    def save(self, local_paths: list[Path], session_id: str) -> list[str]:
        """Upload files to S3 and return their S3 URIs.

        Args:
            local_paths: List of local file paths to upload.
            session_id: Session identifier for organizing stored files.

        Returns:
            List of S3 URIs (s3://bucket/key).
        """
        client = self._get_client()
        uris = []

        for path in local_paths:
            filename = path.name
            key = f"{self.prefix}/{session_id}/{filename}"

            try:
                client = self._get_client()
                client.upload_file(
                    str(path),
                    self.bucket,
                    key,
                    ExtraArgs={"ServerSideEncryption": "AES256"},
                )
                uris.append(f"s3://{self.bucket}/{key}")
            except Exception as e:
                logger.warning(f"Failed to upload {path} to s3://{self.bucket}/{key}: {e}")
                raise

        return uris


def get_store() -> ReportStore:
    """Get the appropriate report store based on configuration.

    Returns S3Store if REPORTS_S3_BUCKET environment variable is set,
    otherwise returns LocalStore. If boto3 is missing when S3 is configured,
    logs a warning and falls back to LocalStore.

    Returns:
        ReportStore implementation (LocalStore or S3Store).
    """
    bucket = os.getenv("REPORTS_S3_BUCKET")
    if not bucket:
        return LocalStore()

    # Check if boto3 is available
    if boto3 is None:
        warnings.warn(
            "REPORTS_S3_BUCKET is set but boto3 is not installed. "
            "Falling back to local storage. Install boto3 to enable S3 storage.",
            UserWarning,
        )
        return LocalStore()

    prefix = os.getenv("REPORTS_S3_PREFIX", "reports")
    return S3Store(bucket=bucket, prefix=prefix)


