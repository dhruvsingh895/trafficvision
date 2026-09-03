"""Unit tests for streaming upload storage."""
import asyncio
import io

import pytest
from starlette.datastructures import UploadFile

from app.services.video_service import (
    UploadTooLargeError,
    VideoStorageService,
)


def make_upload(data: bytes) -> UploadFile:
    return UploadFile(file=io.BytesIO(data), filename="clip.mp4")


def test_streams_across_multiple_chunks(tmp_path) -> None:
    service = VideoStorageService(tmp_path)
    video_id, path, size = asyncio.run(
        service.save(make_upload(b"a" * 2500), max_bytes=5000, chunk_size=1000)
    )
    assert size == 2500
    assert path.read_bytes() == b"a" * 2500
    assert path.name.startswith(video_id)


def test_over_limit_aborts_and_removes_partial_file(tmp_path) -> None:
    service = VideoStorageService(tmp_path)
    with pytest.raises(UploadTooLargeError):
        asyncio.run(
            service.save(
                make_upload(b"a" * 2500), max_bytes=1500, chunk_size=1000
            )
        )
    assert list(tmp_path.iterdir()) == []
