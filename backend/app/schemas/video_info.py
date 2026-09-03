"""Video metadata schema."""
from pydantic import BaseModel


class VideoInfo(BaseModel):
    """Technical metadata extracted from a video file."""

    width: int
    height: int
    fps: float
    frame_count: int
    duration: float  # seconds
