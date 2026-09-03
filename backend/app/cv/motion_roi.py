"""Motion ROI extraction using MOG2 background subtraction."""
import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MotionROI:
    """A region of interest where motion was detected."""
    x1: int
    y1: int
    x2: int
    y2: int


class MotionROIExtractor:
    """Extracts motion bounding boxes using MOG2 background subtraction."""

    def __init__(
        self,
        history: int = 200,
        var_threshold: float = 16.0,
        detect_shadows: bool = True,
        min_area: int = 500,
        padding: int = 20,
        max_roi_area_ratio: float = 0.5,
    ) -> None:
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=var_threshold,
            detectShadows=detect_shadows,
        )
        self._min_area = min_area
        self._padding = padding
        self._max_roi_area_ratio = max_roi_area_ratio
        self._frame_shape: tuple[int, int] | None = None

    def update(self, frame: np.ndarray) -> list[MotionROI]:
        """Return motion ROIs for the given frame."""
        if self._frame_shape is None:
            self._frame_shape = frame.shape[:2]

        h, w = self._frame_shape
        fg_mask = self._bg_subtractor.apply(frame)

        # Remove shadows (value 127 in MOG2 with detectShadows=True)
        if self._bg_subtractor.getDetectShadows():
            _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        rois: list[MotionROI] = []
        total_roi_area = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self._min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            # Add padding
            x1 = max(0, x - self._padding)
            y1 = max(0, y - self._padding)
            x2 = min(w, x + w + self._padding)
            y2 = min(h, y + h + self._padding)
            roi_area = (x2 - x1) * (y2 - y1)
            total_roi_area += roi_area
            rois.append(MotionROI(x1, y1, x2, y2))

        # If ROIs cover too much of frame, fall back to full-frame inference
        frame_area = w * h
        if total_roi_area / frame_area > self._max_roi_area_ratio:
            logger.debug("ROI coverage %.1f%% > threshold; using full frame", total_roi_area / frame_area * 100)
            return [MotionROI(0, 0, w, h)]

        # Merge overlapping ROIs
        return self._merge_overlapping(rois)

    @staticmethod
    def _merge_overlapping(rois: list[MotionROI]) -> list[MotionROI]:
        """Merge ROIs that overlap significantly (IoU > 0.3)."""
        if len(rois) <= 1:
            return rois
        merged = []
        used = [False] * len(rois)
        for i, roi in enumerate(rois):
            if used[i]:
                continue
            x1, y1, x2, y2 = roi.x1, roi.y1, roi.x2, roi.y2
            for j in range(i + 1, len(rois)):
                if used[j]:
                    continue
                o = rois[j]
                # Check overlap
                ix1 = max(x1, o.x1)
                iy1 = max(y1, o.y1)
                ix2 = min(x2, o.x2)
                iy2 = min(y2, o.y2)
                if ix2 > ix1 and iy2 > iy1:
                    inter = (ix2 - ix1) * (iy2 - iy1)
                    area1 = (x2 - x1) * (y2 - y1)
                    area2 = (o.x2 - o.x1) * (o.y2 - o.y1)
                    iou = inter / (area1 + area2 - inter)
                    if iou > 0.3:
                        x1 = min(x1, o.x1)
                        y1 = min(y1, o.y1)
                        x2 = max(x2, o.x2)
                        y2 = max(y2, o.y2)
                        used[j] = True
            merged.append(MotionROI(x1, y1, x2, y2))
        return merged