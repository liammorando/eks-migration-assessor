from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from assessor.storage import LocalStore, S3Store, get_store


class TestLocalStore:
    def test_save_returns_file_uris(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalStore()
            path = Path(tmpdir) / "test.txt"
            path.write_text("test content")

            uris = store.save([path], "test-session")

            assert len(uris) == 1
            assert uris[0].startswith("file://")
            assert "test.txt" in uris[0]


class TestS3Store:
    def test_init_with_bucket_and_prefix(self):
        store = S3Store(bucket="test-bucket", prefix="reports")
        assert store.bucket == "test-bucket"
        assert store.prefix == "reports"

    def test_init_with_default_prefix(self):
        store = S3Store(bucket="test-bucket")
        assert store.prefix == "reports"

    @patch("assessor.storage.boto3")
    def test_save_uploads_files(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        store = S3Store(bucket="test-bucket", prefix="reports")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("test content")

            uris = store.save([Path(tmpdir) / "test.txt"], "session-123")

            assert len(uris) == 1
            assert uris[0] == "s3://test-bucket/reports/session-123/test.txt"
            mock_client.upload_file.assert_called_once_with(
                str(Path(tmpdir) / "test.txt"),
                "test-bucket",
                "reports/session-123/test.txt",
                ExtraArgs={"ServerSideEncryption": "AES256"},
            )

    @patch("assessor.storage.boto3")
    def test_save_handles_upload_error(self, mock_boto3):
        mock_client = MagicMock()
        mock_client.upload_file.side_effect = Exception("Upload failed")
        mock_boto3.client.return_value = mock_client

        store = S3Store(bucket="test-bucket")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("test content")

            with pytest.raises(Exception, match="Upload failed"):
                store.save([Path(tmpdir) / "test.txt"], "session-123")


class TestGetStore:
    def test_returns_local_store_when_no_bucket(self):
        os.environ.pop("REPORTS_S3_BUCKET", None)
        store = get_store()
        assert isinstance(store, LocalStore)

    def test_returns_local_store_when_boto3_missing(self):
        with patch.dict(os.environ, {"REPORTS_S3_BUCKET": "test-bucket"}):
            with patch("assessor.storage.boto3", None):
                with pytest.warns(UserWarning, match="boto3 is not installed"):
                    store = get_store()
                    assert isinstance(store, LocalStore)

    def test_returns_s3_store_when_bucket_set_and_boto3_available(self):
        with patch.dict(os.environ, {"REPORTS_S3_BUCKET": "test-bucket"}):
            with patch("assessor.storage.boto3", MagicMock()):
                store = get_store()
                assert isinstance(store, S3Store)
                assert store.bucket == "test-bucket"

    def test_uses_custom_prefix(self):
        with patch.dict(os.environ, {"REPORTS_S3_BUCKET": "test-bucket", "REPORTS_S3_PREFIX": "custom"}):
            with patch("assessor.storage.boto3", MagicMock()):
                store = get_store()
                assert store.prefix == "custom"
