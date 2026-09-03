"""Tests for model resolution and frame-stride processing (no YOLO)."""
import logging
from pathlib import Path

from app.cv.model_loader import resolve_model
from app.cv.processor import ProcessorConfig, VideoProcessor, default_line


class FakeTracker:
    """Counts track() calls without running YOLO."""

    def __init__(self) -> None:
        self.calls = 0

    def track(self, frame) -> list:
        self.calls += 1
        return []


def process_with(tmp_path: Path, sample_video: Path, stride: int) -> int:
    tracker = FakeTracker()
    processor = VideoProcessor(
        ProcessorConfig(frame_stride=stride), tracker=tracker
    )
    processor.process(
        sample_video, tmp_path / "out.mp4", default_line(64, 48)
    )
    return tracker.calls


def test_stride_1_processes_every_frame(tmp_path, sample_video) -> None:
    assert process_with(tmp_path, sample_video, 1) == 5


def test_stride_2_processes_every_other_frame(tmp_path, sample_video) -> None:
    assert process_with(tmp_path, sample_video, 2) == 3  # frames 1, 3, 5


def test_resolve_model_torch_backend_keeps_weights() -> None:
    assert resolve_model("yolov8n.pt", "cpu", "torch") == "yolov8n.pt"


def test_resolve_model_skips_non_cpu() -> None:
    assert resolve_model("yolov8n.pt", "cuda", "auto") == "yolov8n.pt"


def test_resolve_model_skips_non_pt() -> None:
    assert resolve_model("model.onnx", "cpu", "auto") == "model.onnx"


def test_resolve_model_reuses_existing_export(tmp_path) -> None:
    weights = tmp_path / "m.pt"
    weights.write_bytes(b"fake")
    exported = tmp_path / "m_openvino_model"
    exported.mkdir()
    assert resolve_model(str(weights), "cpu", "openvino") == str(exported)


def test_resolve_model_falls_back_when_export_fails(
    tmp_path, monkeypatch, caplog
) -> None:
    import app.cv.model_loader as ml

    monkeypatch.setattr(
        ml, "_export_openvino",
        lambda *a: (_ for _ in ()).throw(RuntimeError("no openvino")),
    )
    weights = str(tmp_path / "m.pt")
    with caplog.at_level(logging.WARNING):
        assert resolve_model(weights, "cpu", "auto") == weights
    assert "OpenVINO export failed" in caplog.text
