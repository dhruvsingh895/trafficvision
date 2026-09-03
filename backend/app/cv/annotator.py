"""Draws detections, tracking IDs and stats onto frames."""
import cv2
import numpy as np

from app.cv.counting import CountingLine
from app.cv.statistics import TrafficStats
from app.cv.tracker import TrackedDetection

_BOX_COLOR = (60, 200, 80)
_COUNT_COLOR = (0, 200, 255)
_LINE_COLOR = (0, 0, 255)
_FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_tracked_box(frame: np.ndarray, td: TrackedDetection) -> None:
    """Draw bounding box with label, confidence and track ID."""
    d = td.detection
    label = f"{d.label.capitalize()} {d.confidence:.2f} ID:{td.track_id}"
    cv2.rectangle(frame, (d.x1, d.y1), (d.x2, d.y2), _BOX_COLOR, 2)
    (tw, th), _ = cv2.getTextSize(label, _FONT, 0.5, 1)
    cv2.rectangle(
        frame, (d.x1, d.y1 - th - 8), (d.x1 + tw, d.y1), _BOX_COLOR, -1
    )
    cv2.putText(
        frame, label, (d.x1, d.y1 - 4), _FONT, 0.5, (0, 0, 0), 1, cv2.LINE_AA
    )


def draw_line(frame: np.ndarray, line: CountingLine) -> None:
    cv2.line(
        frame,
        (int(line.x1), int(line.y1)),
        (int(line.x2), int(line.y2)),
        _LINE_COLOR,
        2,
    )
    cv2.putText(
        frame, "COUNTING LINE",
        (int(line.x1) + 5, int(line.y1) - 8),
        _FONT, 0.6, _LINE_COLOR, 2, cv2.LINE_AA,
    )


def draw_stats(frame: np.ndarray, stats: TrafficStats) -> None:
    lines = [
        f"Total: {stats.total}",
        f"Cars: {stats.by_type['car']}  Motorcycles: {stats.by_type['motorcycle']}",
        f"Buses: {stats.by_type['bus']}  Trucks: {stats.by_type['truck']}",
        f"Entering: {stats.entering}  Exiting: {stats.exiting}",
    ]
    y = 30
    for text in lines:
        cv2.putText(
            frame, text, (10, y), _FONT, 0.7, _COUNT_COLOR, 2, cv2.LINE_AA
        )
        y += 28
