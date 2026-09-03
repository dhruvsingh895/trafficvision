"""SQLAlchemy models for videos, jobs and results."""
from datetime import datetime
from datetime import timezone as tz

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class VideoRecord(Base):
    __tablename__ = "videos"

    video_id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String)
    size_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(tz.utc))


class JobRecord(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    video_id: Mapped[str] = mapped_column(
        String, ForeignKey("videos.video_id")
    )
    status: Mapped[str] = mapped_column(String, default="processing")
    frames_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_frames: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(tz.utc))


class ResultRecord(Base):
    __tablename__ = "results"

    video_id: Mapped[str] = mapped_column(String, primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text)
    processing_time_s: Mapped[float] = mapped_column(Float, default=0.0)
    processing_fps: Mapped[float] = mapped_column(Float, default=0.0)
