"""Tests for the YOLO detection module (no real model required)."""
from typing import ClassVar

from app.cv.detection import VEHICLE_CLASSES, Detection
from app.cv.detector import VehicleDetector


def test_vehicle_classes_are_coco_ids() -> None:
    assert VEHICLE_CLASSES == {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


def test_detection_center() -> None:
    det = Detection(x1=10, y1=20, x2=30, y2=40, class_id=2,
                    label="car", confidence=0.9)
    assert det.center == (20.0, 30.0)


def test_device_resolution_fallback(monkeypatch) -> None:
    import sys
    from types import SimpleNamespace

    fake_torch = SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: False)
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    assert VehicleDetector._resolve_device(None) == "cpu"
    assert VehicleDetector._resolve_device("cuda") == "cuda"


def test_to_detections_with_fake_results() -> None:
    class FakeBox:
        def __init__(self, cls: float, conf: float, xyxy: list[float]):
            class T:
                def __init__(self, v: float):
                    self._v = v

                def item(self) -> float:
                    return self._v

            self.cls = T(cls)
            self.conf = T(conf)
            self.xyxy = [FakeTensorList(xyxy)]

    class FakeTensorList(list):
        def tolist(self) -> list[float]:
            return list(self)

    class FakeResult:
        boxes: ClassVar = [
            FakeBox(2, 0.91, [0, 0, 50, 60]),
            FakeBox(7, 0.8, [10, 10, 90, 90]),
        ]

    detections = VehicleDetector._to_detections([FakeResult()])
    assert len(detections) == 2
    assert detections[0].label == "car"
    assert detections[0].confidence == 0.91
    assert detections[1].label == "truck"
    assert (detections[0].x2, detections[0].y2) == (50, 60)


def test_to_detections_empty() -> None:
    assert VehicleDetector._to_detections([]) == []
