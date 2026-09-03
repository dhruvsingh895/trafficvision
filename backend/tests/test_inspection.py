"""Tests for video inspection service and endpoint."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.inspection_service import (
    VideoInspectionError,
    VideoInspectionService,
)

client = TestClient(app)


def test_inspect_sample_video(sample_video: Path) -> None:
    info = VideoInspectionService().inspect(sample_video)
    assert info.width == 64
    assert info.height == 48
    assert info.fps == 10.0
    assert info.frame_count == 5
    assert info.duration == 0.5


def test_inspect_missing_file(tmp_path: Path) -> None:
    with pytest.raises(VideoInspectionError):
        VideoInspectionService().inspect(tmp_path / "nope.mp4")


def test_info_endpoint(sample_video: Path) -> None:
    with sample_video.open("rb") as f:
        r = client.post(
            "/api/videos", files={"file": ("traffic.mp4", f, "video/mp4")}
        )
    video_id = r.json()["video_id"]

    r = client.get(f"/api/videos/{video_id}/info")
    assert r.status_code == 200
    body = r.json()
    assert body["width"] == 64
    assert body["height"] == 48
    assert body["frame_count"] == 5


def test_info_endpoint_unknown_id() -> None:
    r = client.get("/api/videos/doesnotexist/info")
    assert r.status_code == 404
