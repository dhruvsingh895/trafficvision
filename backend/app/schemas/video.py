"""Pydantic schemas for video upload responses."""
from pydantic import BaseModel


class VideoUploadResponse(BaseModel):
    """Response returned after a successful video upload."""

    video_id: str
    filename: str
    status: str = "uploaded"
    size_bytes: int
