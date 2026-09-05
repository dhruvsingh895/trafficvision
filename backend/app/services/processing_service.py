"""Runs video processing in background threads and persists state."""
import json
import logging
import threading
import uuid
from collections import defaultdict

from app.core.config import get_settings
from app.cv.detection import VEHICLE_CLASSES
from app.cv.processor import ProcessorConfig, VideoProcessor, default_line
from app.cv.statistics import TrafficStats
from app.db.models import JobRecord, ResultRecord, VideoRecord
from app.db.session import get_session
from app.services.video_service import VideoStorageService

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Raised when a processing job cannot be started."""

    def __init__(self, message: str, status_code: int = 409) -> None:
        super().__init__(message)
        self.status_code = status_code


_video_locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)

def create_job(video_id: str, line_y_ratio: float) -> str:
    """Create a job row and start a background thread."""
    settings = get_settings()
    storage = VideoStorageService(settings.input_path)
    input_path = storage.get_path(video_id)
    if input_path is None:
        raise ProcessingError("Video not found.", status_code=404)

    # The lock closes the check/create race for requests handled by this
    # process; the database check also protects against already-running jobs.
    with _video_locks[video_id]:
        with get_session() as s:
            active = (
                s.query(JobRecord)
                .filter(
                    JobRecord.video_id == video_id,
                    JobRecord.status.in_(("queued", "processing")),
                )
                .first()
            )
            if active is not None:
                raise ProcessingError(
                    "Video is already being processed.",
                    status_code=409,
                )

            job_id = uuid.uuid4().hex[:12]
            s.add(JobRecord(job_id=job_id, video_id=video_id, status="processing"))
            video = s.get(VideoRecord, video_id)
            if video:
                video.status = "processing"

        thread = threading.Thread(
            target=_run_job,
            args=(job_id, video_id, input_path, line_y_ratio),
            daemon=True,
        )
        try:
            thread.start()
        except RuntimeError as exc:
            _store_failure(job_id, video_id, str(exc))
            raise ProcessingError(
                "Unable to start processing job.", status_code=503
            ) from exc
    logger.info("Started job %s for video %s", job_id, video_id)
    return job_id


def _run_job(job_id: str, video_id: str, input_path, line_y_ratio: float):
    settings = get_settings()
    output_path = settings.output_path / f"{video_id}.mp4"

    def on_progress(done: int, total: int) -> None:
        with get_session() as s:
            job = s.get(JobRecord, job_id)
            if job:
                job.frames_processed, job.total_frames = done, total

    try:
        from app.services.inspection_service import VideoInspectionService

        info = VideoInspectionService().inspect(input_path)
        line = default_line(info.width, info.height, line_y_ratio)

        processor = VideoProcessor(
            ProcessorConfig(
                model_path=settings.model_path,
                confidence=settings.confidence,
                device=settings.device,
                imgsz=settings.imgsz,
                frame_stride=settings.frame_stride,
                inference_backend=settings.inference_backend,
                per_class_conf={
                    VEHICLE_CLASSES[2]: settings.conf_car,
                    VEHICLE_CLASSES[3]: settings.conf_motorcycle,
                    VEHICLE_CLASSES[5]: settings.conf_bus,
                    VEHICLE_CLASSES[7]: settings.conf_truck,
                },
                use_mog_roi=settings.use_mog_roi,
                mog_history=settings.mog_history,
                mog_var_threshold=settings.mog_var_threshold,
                mog_detect_shadows=settings.mog_detect_shadows,
                roi_padding=settings.roi_padding,
                max_roi_area_ratio=settings.max_roi_area_ratio,
            )
        )
        result = processor.process(
            input_path, output_path, line, on_progress=on_progress
        )
        _store_success(
            job_id, video_id, result.stats, result.duration_s,
            result.processing_fps,
        )
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _store_failure(job_id, video_id, str(exc))


def _store_success(
    job_id: str, video_id: str, stats: TrafficStats,
    duration_s: float, processing_fps: float,
) -> None:
    payload = json.dumps(
        {
            "total": stats.total,
            "by_type": stats.by_type,
            "entering": stats.entering,
            "exiting": stats.exiting,
            "timeline": [
                {"t": p.t, "count": p.count} for p in stats.timeline
            ],
        }
    )
    with get_session() as s:
        job = s.get(JobRecord, job_id)
        if job:
            job.status = "completed"
        video = s.get(VideoRecord, video_id)
        if video:
            video.status = "completed"
        # merge() upserts by primary key, so reprocessing a video
        # replaces its previous results instead of crashing.
        s.merge(
            ResultRecord(
                video_id=video_id, payload_json=payload,
                processing_time_s=duration_s, processing_fps=processing_fps,
            )
        )


def _store_failure(job_id: str, video_id: str, error: str) -> None:
    with get_session() as s:
        job = s.get(JobRecord, job_id)
        if job:
            job.status = "failed"
            job.error = error
        video = s.get(VideoRecord, video_id)
        if video:
            video.status = "failed"
