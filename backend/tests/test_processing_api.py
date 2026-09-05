"""Tests for processing endpoints (YOLO mocked out)."""
import time
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

import app.services.processing_service as ps
from app.main import app

client = TestClient(app)


class FakeResult:
    """Mimics ProcessingResult without running YOLO."""

    def __init__(self, lines: int = 4) -> None:
        from app.cv.counting import CrossingEvent, Direction
        from app.cv.statistics import StatsCollector

        collector = StatsCollector()
        for i in range(lines):
            collector.record(CrossingEvent(i, Direction.ENTERING), "car", i)
        self.stats = collector.stats
        self.duration_s = 0.01
        self.fps = 10.0
        self.processing_fps = 50.0


class FakeProcessor:
    def __init__(self, config) -> None:
        import cv2

        self._cv2 = cv2

    def process(self, input_path, output_path, line, on_progress=None):
        out = np.zeros((48, 64, 3), dtype=np.uint8)
        writer = self._cv2.VideoWriter(
            str(output_path),
            self._cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 48),
        )
        writer.write(out)
        writer.release()
        if on_progress:
            on_progress(5, 5)
        return FakeResult()


def upload_video(sample_video: Path) -> str:
    with sample_video.open("rb") as f:
        r = client.post(
            "/api/videos", files={"file": ("traffic.mp4", f, "video/mp4")}
        )
    assert r.status_code == 200
    return r.json()["video_id"]


def wait_completed(video_id: str, timeout: float = 10.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"/api/videos/{video_id}/status").json()
        if status["status"] in ("completed", "failed"):
            return status
        time.sleep(0.05)
    raise TimeoutError("Job did not finish")


def test_full_processing_flow(
    sample_video: Path, monkeypatch
) -> None:
    monkeypatch.setattr(ps, "VideoProcessor", FakeProcessor)
    video_id = upload_video(sample_video)

    r = client.post(f"/api/videos/{video_id}/process",
                    json={"line_y_ratio": 0.5})
    assert r.status_code == 200
    assert r.json()["status"] == "processing"

    status = wait_completed(video_id)
    assert status["status"] == "completed"
    assert status["progress"] == 100

    results = client.get(f"/api/videos/{video_id}/results").json()
    assert results["total"] == 4
    assert results["by_type"]["car"] == 4
    assert results["entering"] == 4
    assert len(results["timeline"]) == 4
    assert results["processing_fps"] == 50.0

    out = client.get(f"/api/videos/{video_id}/output")
    assert out.status_code == 200
    assert out.headers["content-type"] == "video/mp4"


def test_status_before_processing(sample_video: Path) -> None:
    video_id = upload_video(sample_video)
    status = client.get(f"/api/videos/{video_id}/status").json()
    assert status["status"] == "uploaded"
    assert status["progress"] == 0


def test_status_unknown_video() -> None:
    assert client.get("/api/videos/nope/exists/status").status_code in (
        404, 422
    )
    assert client.get("/api/videos/doesnotexist/status").status_code == 404


def test_frame_endpoint(sample_video: Path) -> None:
    video_id = upload_video(sample_video)
    r = client.get(f"/api/videos/{video_id}/frame?n=0")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content.startswith(b"\xff\xd8")  # JPEG magic bytes


def test_results_before_completion(sample_video: Path) -> None:
    video_id = upload_video(sample_video)
    r = client.get(f"/api/videos/{video_id}/results")
    assert r.status_code == 404


def test_reprocessing_replaces_results(
    sample_video: Path, monkeypatch
) -> None:
    """Processing the same video twice must succeed, not crash on the
    results primary key."""
    monkeypatch.setattr(ps, "VideoProcessor", FakeProcessor)
    video_id = upload_video(sample_video)

    status = {}
    for _ in range(2):
        r = client.post(f"/api/videos/{video_id}/process", json={})
        assert r.status_code == 200
        status = wait_completed(video_id)

    assert status["status"] == "completed"
    assert status["error"] is None
    results = client.get(f"/api/videos/{video_id}/results").json()
    assert results["total"] == 4


def test_rejects_duplicate_processing_while_first_job_is_active(
    sample_video: Path, monkeypatch
) -> None:
    monkeypatch.setattr(ps, "VideoProcessor", FakeProcessor)
    video_id = upload_video(sample_video)
    original_run_job = ps._run_job

    def blocked_run_job(*args):
        time.sleep(0.2)
        original_run_job(*args)

    monkeypatch.setattr(ps, "_run_job", blocked_run_job)
    first = client.post(f"/api/videos/{video_id}/process", json={})
    assert first.status_code == 200

    duplicate = client.post(f"/api/videos/{video_id}/process", json={})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Video is already being processed."
    assert wait_completed(video_id)["status"] == "completed"
