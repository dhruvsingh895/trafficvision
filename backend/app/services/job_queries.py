"""Read-side queries for jobs and results."""
import json

from app.db.models import JobRecord, ResultRecord
from app.db.session import get_session
from app.schemas.job import JobStatus, TimelinePointSchema, VideoResults


def latest_job(video_id: str) -> JobStatus | None:
    with get_session() as s:
        job = (
            s.query(JobRecord)
            .filter_by(video_id=video_id)
            .order_by(JobRecord.created_at.desc())
            .first()
        )
        if job is None:
            return None
        progress = (
            round(job.frames_processed / job.total_frames * 100)
            if job.total_frames
            else 0
        )
        return JobStatus(
            status=job.status,
            progress=min(progress, 100),
            frames_processed=job.frames_processed,
            total_frames=job.total_frames,
            error=job.error,
        )


def get_results(video_id: str, fps: float) -> VideoResults | None:
    with get_session() as s:
        record = s.get(ResultRecord, video_id)
        if record is None:
            return None
        payload_json = record.payload_json
        processing_time = record.processing_time_s
        processing_fps = record.processing_fps
    data = json.loads(payload_json)
    return VideoResults(
        video_id=video_id,
        total=data["total"],
        by_type=data["by_type"],
        entering=data["entering"],
        exiting=data["exiting"],
        processing_time_s=processing_time,
        fps=fps,
        processing_fps=processing_fps,
        timeline=[TimelinePointSchema(**p) for p in data["timeline"]],
    )
