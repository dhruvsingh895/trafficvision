"""Extracts technical metadata from video files."""
from pathlib import Path

import cv2

from app.schemas.video_info import VideoInfo


class VideoInspectionError(Exception):
    """Raised when a video cannot be inspected."""


class VideoInspectionService:
    """Reads video properties via OpenCV."""

    def inspect(self, path: Path) -> VideoInfo:
        """Extract width/height/fps/frame count/duration from a video."""
        if not path.exists():
            raise VideoInspectionError(f"Video not found: {path}")

        cap = cv2.VideoCapture(str(path))
        try:
            if not cap.isOpened():
                raise VideoInspectionError(f"Cannot open video: {path}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0.0

            return VideoInfo(
                width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                fps=round(fps, 2),
                frame_count=frame_count,
                duration=round(duration, 2),
            )
        finally:
            cap.release()
