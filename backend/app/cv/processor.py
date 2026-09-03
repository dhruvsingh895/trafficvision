"""Full video processing pipeline: track -> count -> annotate -> write."""
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2

from app.cv.annotator import draw_line, draw_stats, draw_tracked_box
from app.cv.counting import CountingLine, VehicleCounter
from app.cv.model_loader import resolve_device, resolve_model
from app.cv.motion_roi import MotionROIExtractor
from app.cv.statistics import StatsCollector, TrafficStats
from app.cv.tracker import TrackedDetection, VehicleTracker

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]
LiveCallback = Callable[[bytes, TrafficStats, int, int], None]  # jpeg_bytes, stats, frame_num, total


@dataclass(slots=True)
class ProcessingResult:
    stats: TrafficStats
    frames_processed: int
    total_frames: int
    fps: float
    duration_s: float
    processing_fps: float


@dataclass(slots=True)
class ProcessorConfig:
    model_path: str = "yolov8n.pt"
    confidence: float = 0.25
    device: str = ""
    imgsz: int = 640
    frame_stride: int = 1  # detect every Nth frame (positions interpolate)
    inference_backend: str = "auto"  # auto | torch | openvino
    per_class_conf: dict[int, float] | None = None

    # Motion ROI (MOG2 background subtraction)
    use_mog_roi: bool = False
    mog_history: int = 200
    mog_var_threshold: float = 16.0
    mog_detect_shadows: bool = True
    roi_padding: int = 20
    max_roi_area_ratio: float = 0.5


def default_line(width: int, height: int, y_ratio: float = 0.5) -> CountingLine:
    """Horizontal counting line across the frame."""
    return CountingLine(0, height * y_ratio, float(width), height * y_ratio)


class VideoProcessor:
    """End-to-end: reads a video, processes it, writes annotated output."""

    def __init__(
        self, config: ProcessorConfig, tracker: VehicleTracker | None = None
    ) -> None:
        self._config = config
        if tracker is not None:
            self._tracker = tracker
        else:
            device = resolve_device(config.device or None)
            self._tracker = VehicleTracker(
                model_path=resolve_model(
                    config.model_path, device, config.inference_backend
                ),
                confidence=config.confidence,
                device=device,
                imgsz=config.imgsz,
                per_class_conf=config.per_class_conf,
            )
        self._motion_extractor = None
        if config.use_mog_roi:
            self._motion_extractor = MotionROIExtractor(
                history=config.mog_history,
                var_threshold=config.mog_var_threshold,
                detect_shadows=config.mog_detect_shadows,
                padding=config.roi_padding,
                max_roi_area_ratio=config.max_roi_area_ratio,
            )

    def process(
        self,
        input_path: Path,
        output_path: Path,
        line: CountingLine,
        on_progress: ProgressCallback | None = None,
    ) -> ProcessingResult:
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {input_path}")

        try:
            return self._run(cap, output_path, line, on_progress, None)
        finally:
            cap.release()

    def process_live(
        self,
        input_path: Path,
        output_path: Path,
        line: CountingLine,
        on_progress: ProgressCallback | None = None,
        on_live: LiveCallback | None = None,
        live_every: int = 1,
    ) -> ProcessingResult:
        """Process video and invoke on_live with (jpeg_bytes, stats, frame_num, total)"""
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {input_path}")

        try:
            return self._run(cap, output_path, line, on_progress, on_live, live_every)
        finally:
            cap.release()

    def _run(
        self,
        cap: cv2.VideoCapture,
        output_path: Path,
        line: CountingLine,
        on_progress: ProgressCallback | None,
        on_live: LiveCallback | None,
        live_every: int = 1,
    ) -> ProcessingResult:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps,
            (width, height),
        )

        counter = VehicleCounter(line)
        collector = StatsCollector()
        start = time.perf_counter()
        processed = 0
        stride = max(1, self._config.frame_stride)
        tracked: list[TrackedDetection] = []
        last_progress = 0.0

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                processed += 1

                # Motion ROI extraction (if enabled)
                rois = None
                if self._motion_extractor is not None:
                    rois = self._motion_extractor.update(frame)

                if (processed - 1) % stride == 0:
                    if rois is not None and len(rois) > 0 and not (len(rois) == 1 and rois[0].x1 == 0 and rois[0].y1 == 0 and rois[0].x2 == frame.shape[1] and rois[0].y2 == frame.shape[0]):
                        tracked = self._tracker.track_rois(frame, rois)
                    else:
                        tracked = self._tracker.track(frame)
                for td in tracked:
                    event = counter.update(td.track_id, td.center)
                    if event:
                        collector.record(
                            event, td.detection.label, processed / fps
                        )
                    draw_tracked_box(frame, td)

                draw_line(frame, line)
                draw_stats(frame, collector.stats)
                writer.write(frame)

                if on_live and (processed - 1) % live_every == 0:
                    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ok:
                        on_live(buf.tobytes(), collector.stats, processed, total)

                if on_progress:
                    now = time.perf_counter()
                    if now - last_progress >= 1.0:
                        last_progress = now
                        on_progress(processed, total)
        finally:
            writer.release()

        if on_progress:
            on_progress(processed, total)
        duration = time.perf_counter() - start
        logger.info(
            "Processed %d/%d frames in %.1fs (%s)", processed, total, duration,
            output_path,
        )
        return ProcessingResult(
            stats=collector.stats,
            frames_processed=processed,
            total_frames=total,
            fps=fps,
            duration_s=round(duration, 2),
            processing_fps=round(processed / duration, 2) if duration else 0.0,
        )
