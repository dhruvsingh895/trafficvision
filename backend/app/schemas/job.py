"""Schemas for processing jobs and results."""
from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    """Optional body for starting processing."""

    line_y_ratio: float = Field(default=0.5, ge=0.0, le=1.0)


class ProcessResponse(BaseModel):
    job_id: str
    video_id: str
    status: str = "processing"


class JobStatus(BaseModel):
    status: str  # uploaded | processing | completed | failed
    progress: int = 0
    frames_processed: int = 0
    total_frames: int = 0
    error: str | None = None


class TimelinePointSchema(BaseModel):
    t: float
    count: int


class VideoResults(BaseModel):
    video_id: str
    total: int
    by_type: dict[str, int]
    entering: int
    exiting: int
    processing_time_s: float
    fps: float
    processing_fps: float = 0.0
    timeline: list[TimelinePointSchema]
