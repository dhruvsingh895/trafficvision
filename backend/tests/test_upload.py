"""Tests for video upload endpoint."""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_valid_video(sample_video: Path) -> None:
    with sample_video.open("rb") as f:
        r = client.post(
            "/api/videos", files={"file": ("traffic.mp4", f, "video/mp4")}
        )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "uploaded"
    assert data["filename"] == "traffic.mp4"
    assert len(data["video_id"]) == 12
    assert data["size_bytes"] > 0


def test_upload_rejects_bad_extension() -> None:
    r = client.post(
        "/api/videos", files={"file": ("video.txt", b"data", "text/plain")}
    )
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]


def test_upload_rejects_corrupt_video(tmp_path: Path) -> None:
    fake = tmp_path / "fake.mp4"
    fake.write_bytes(b"not a video")
    with fake.open("rb") as f:
        r = client.post("/api/videos", files={"file": ("fake.mp4", f)})
    assert r.status_code == 400
    assert "readable" in r.json()["detail"]


def test_upload_rejects_oversize() -> None:
    import app.api.routes.videos as routes

    settings = routes.get_settings()
    original = settings.max_upload_size_mb
    settings.max_upload_size_mb = 0
    try:
        r = client.post(
            "/api/videos", files={"file": ("big.mp4", b"x" * 100, "video/mp4")}
        )
        assert r.status_code == 413
    finally:
        settings.max_upload_size_mb = original
