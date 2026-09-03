"""ByteTrack-based multi-object tracker (via Ultralytics)."""
import logging
from dataclasses import dataclass

import numpy as np

from app.cv.detection import VEHICLE_CLASSES, Detection
from app.cv.motion_roi import MotionROI

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TrackedDetection:
    """A detection associated with a stable track ID."""

    track_id: int
    detection: Detection

    @property
    def center(self) -> tuple[float, float]:
        return self.detection.center


class VehicleTracker:
    """Keeps stable IDs for vehicles across frames using ByteTrack."""

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence: float = 0.25,
        device: str | None = None,
        tracker: str = "bytetrack.yaml",
        imgsz: int = 640,
        per_class_conf: dict[int, float] | None = None,
    ) -> None:
        from ultralytics import YOLO

        self.confidence = confidence
        self.device = device
        self.imgsz = imgsz
        self.per_class_conf = per_class_conf or {}
        self._model = YOLO(model_path)
        self._tracker = tracker
        logger.info(
            "Tracker ready (%s, device=%s, imgsz=%d, per_class_conf=%s)",
            tracker, device or "auto", imgsz, self.per_class_conf,
        )

    def track(self, frame: np.ndarray) -> list[TrackedDetection]:
        """Detect + track vehicles in one frame (full frame)."""
        results = self._model.track(
            frame,
            persist=True,
            conf=self.confidence,
            device=self.device,
            tracker=self._tracker,
            imgsz=self.imgsz,
            classes=list(VEHICLE_CLASSES.keys()),
            verbose=False,
        )
        return self._to_tracked(results)

    def track_rois(self, frame: np.ndarray, rois: list[MotionROI]) -> list[TrackedDetection]:
        """Detect on ROIs only, then run ByteTrack on combined detections.

        More efficient when motion is localized to small regions.
        """
        all_detections = []
        for roi in rois:
            crop = frame[roi.y1:roi.y2, roi.x1:roi.x2]
            if crop.size == 0:
                continue
            results = self._model.predict(
                crop,
                conf=self.confidence,
                device=self.device,
                imgsz=self.imgsz,
                classes=list(VEHICLE_CLASSES.keys()),
                verbose=False,
            )
            dets = self._to_detections(results, roi.x1, roi.y1)
            all_detections.extend(dets)

        # Run ByteTrack on combined detections
        return self._track_detections(frame, all_detections)

    def _to_detections(self, results, offset_x: int, offset_y: int) -> list:
        """Convert ultralytics results to Detection objects with coordinate offset."""
        detections = []
        if not results or results[0].boxes is None:
            return detections
        for box in results[0].boxes:
            class_id = int(box.cls.item())
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            detections.append(
                Detection(
                    x1=x1 + offset_x,
                    y1=y1 + offset_y,
                    x2=x2 + offset_x,
                    y2=y2 + offset_y,
                    class_id=class_id,
                    label=VEHICLE_CLASSES.get(class_id, "unknown"),
                    confidence=round(float(box.conf.item()), 3),
                )
            )
        return detections

    def _track_detections(self, frame: np.ndarray, detections: list) -> list[TrackedDetection]:
        """Run ByteTrack on pre-computed detections."""
        # Build ultralytics Results-like object for tracker
        import torch
        from ultralytics.engine.results import Results

        if not detections:
            return []

        # Create boxes tensor
        boxes_xyxy = torch.tensor(
            [[d.x1, d.y1, d.x2, d.y2] for d in detections],
            dtype=torch.float32,
            device=self.device or "cpu",
        )
        cls = torch.tensor([d.class_id for d in detections], dtype=torch.int32)
        conf = torch.tensor([d.confidence for d in detections], dtype=torch.float32)

        # Create Results object
        results = Results(
            orig_img=frame,
            path="",
            names=VEHICLE_CLASSES,
            boxes=torch.cat([boxes_xyxy, conf.unsqueeze(1), cls.unsqueeze(1).float()], dim=1),
        )

        # Run tracker
        tracked_results = self._model.tracker.update(results, frame)
        return self._to_tracked_from_tracker(tracked_results)

    def _to_tracked_from_tracker(self, tracked_results) -> list[TrackedDetection]:
        tracked = []
        if tracked_results is None or len(tracked_results) == 0:
            return tracked
        for t in tracked_results:
            x1, y1, x2, y2, track_id, class_id, conf = t
            det = Detection(
                x1=int(x1), y1=int(y1), x2=int(x2), y2=int(y2),
                class_id=int(class_id),
                label=VEHICLE_CLASSES.get(int(class_id), "unknown"),
                confidence=round(float(conf), 3),
            )
            tracked.append(TrackedDetection(track_id=int(track_id), detection=det))
        return tracked

    @staticmethod
    def _to_tracked(results) -> list[TrackedDetection]:  # type: ignore[no-untyped-def]
        tracked: list[TrackedDetection] = []
        if not results or results[0].boxes is None:
            return tracked
        for box in results[0].boxes:
            if box.id is None:
                continue
            class_id = int(box.cls.item())
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            det = Detection(
                x1=x1, y1=y1, x2=x2, y2=y2,
                class_id=class_id,
                label=VEHICLE_CLASSES.get(class_id, "unknown"),
                confidence=round(float(box.conf.item()), 3),
            )
            tracked.append(
                TrackedDetection(track_id=int(box.id.item()), detection=det)
            )
        return tracked
