"""YOLO-based vehicle detector (detection only, no tracking/counting)."""
import logging

import numpy as np

from app.cv.detection import VEHICLE_CLASSES, Detection

logger = logging.getLogger(__name__)


class DetectorLoadError(Exception):
    """Raised when the YOLO model cannot be loaded."""


class VehicleDetector:
    """Detects vehicles in frames using Ultralytics YOLO."""

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence: float = 0.25,
        device: str | None = None,
    ) -> None:
        self.confidence = confidence
        self.device = self._resolve_device(device)
        self._model = self._load_model(model_path)

    @staticmethod
    def _resolve_device(device: str | None) -> str:
        """Use CUDA when available, otherwise CPU."""
        if device:
            return device
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _load_model(self, model_path: str):  # type: ignore[no-untyped-def]
        try:
            from ultralytics import YOLO

            logger.info(
                "Loading YOLO model '%s' on device '%s'", model_path, self.device
            )
            return YOLO(model_path)
        except Exception as exc:
            raise DetectorLoadError(
                f"Failed to load model '{model_path}': {exc}"
            ) from exc

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run detection on one frame; return vehicle detections only."""
        results = self._model.predict(
            frame,
            conf=self.confidence,
            device=self.device,
            classes=list(VEHICLE_CLASSES.keys()),
            verbose=False,
        )
        return self._to_detections(results)

    @staticmethod
    def _to_detections(results) -> list[Detection]:  # type: ignore[no-untyped-def]
        detections: list[Detection] = []
        if not results or results[0].boxes is None:
            return detections
        for box in results[0].boxes:
            class_id = int(box.cls.item())
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            detections.append(
                Detection(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    class_id=class_id,
                    label=VEHICLE_CLASSES.get(class_id, "unknown"),
                    confidence=round(float(box.conf.item()), 3),
                )
            )
        return detections
