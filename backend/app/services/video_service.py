"""Service for storing uploaded videos on disk."""
import uuid
from pathlib import Path

from fastapi import UploadFile


class UploadTooLargeError(Exception):
    """Raised when an upload exceeds the configured size limit."""


class VideoStorageService:
    """Saves uploaded videos into the configured input directory."""

    def __init__(self, input_dir: Path) -> None:
        self._input_dir = input_dir
        self._input_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self, upload: UploadFile, max_bytes: int, chunk_size: int = 1024 * 1024
    ) -> tuple[str, Path, int]:
        """Stream the upload to disk in chunks, enforcing max_bytes.

        Returns (video_id, saved_path, size_bytes). The partial file is
        removed when the limit is exceeded.
        """
        video_id = uuid.uuid4().hex[:12]
        ext = Path(upload.filename or "video.mp4").suffix.lower()
        path = self._input_dir / f"{video_id}{ext}"
        size = 0
        over_limit = False
        with path.open("wb") as f:
            while chunk := await upload.read(chunk_size):
                size += len(chunk)
                if size > max_bytes:
                    over_limit = True
                    break
                f.write(chunk)
        if over_limit:
            path.unlink(missing_ok=True)
            raise UploadTooLargeError(f"Upload exceeds {max_bytes} bytes")
        return video_id, path, size

    def remove(self, path: Path) -> None:
        """Delete a stored video (e.g. on validation failure)."""
        path.unlink(missing_ok=True)

    def get_path(self, video_id: str) -> Path | None:
        """Find the stored file for a video ID, if any."""
        for p in self._input_dir.glob(f"{video_id}.*"):
            return p
        return None
