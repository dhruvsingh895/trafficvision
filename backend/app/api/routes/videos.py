"""Video upload API routes."""
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.video import VideoUploadResponse
from app.schemas.video_info import VideoInfo
from app.services.inspection_service import (
    VideoInspectionError,
    VideoInspectionService,
)
from app.services.validators import is_readable_video, is_valid_extension
from app.services.video_service import (
    UploadTooLargeError,
    VideoStorageService,
)

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("", response_model=VideoUploadResponse)
async def upload_video(
    file: Annotated[UploadFile, File()],
) -> VideoUploadResponse:
    """Upload a traffic video for later processing."""
    settings = get_settings()

    if not file.filename or not is_valid_extension(
        file.filename, settings.allowed_extensions_set
    ):
        allowed = ", ".join(sorted(settings.allowed_extensions_set))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed}",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    storage = VideoStorageService(settings.input_path)
    try:
        video_id, path, size = await storage.save(file, max_bytes)
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit.",
        ) from exc

    if not is_readable_video(str(path)):
        storage.remove(path)
        raise HTTPException(
            status_code=400, detail="File is not a readable video."
        )

    from app.db.models import VideoRecord
    from app.db.session import get_session

    with get_session() as s:
        s.add(
            VideoRecord(
                video_id=video_id, filename=file.filename,
                size_bytes=size,
            )
        )

    return VideoUploadResponse(
        video_id=video_id, filename=file.filename, size_bytes=size
    )


@router.get("/{video_id}/info")
def get_video_info(video_id: str) -> VideoInfo:
    """Return technical metadata of an uploaded video."""
    settings = get_settings()
    storage = VideoStorageService(settings.input_path)
    path = storage.get_path(video_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Video not found.")
    try:
        return VideoInspectionService().inspect(path)
    except VideoInspectionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
