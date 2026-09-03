"""Processing, status, results, output and frame endpoints."""
import asyncio
import json
import threading
import time
from queue import Queue

import cv2
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse

from app.core.config import get_settings
from app.cv.detection import VEHICLE_CLASSES
from app.cv.processor import ProcessorConfig, VideoProcessor, default_line
from app.schemas.job import (
    JobStatus,
    ProcessRequest,
    ProcessResponse,
    VideoResults,
)
from app.services.inspection_service import VideoInspectionService
from app.services.job_queries import get_results, latest_job
from app.services.processing_service import ProcessingError, create_job
from app.services.video_service import VideoStorageService

router = APIRouter(prefix="/api/videos", tags=["processing"])


def _video_or_404(video_id: str):
    settings = get_settings()
    path = VideoStorageService(settings.input_path).get_path(video_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Video not found.")
    return path


@router.post("/{video_id}/process", response_model=ProcessResponse)
def start_processing(
    video_id: str, body: ProcessRequest | None = None
) -> ProcessResponse:
    _video_or_404(video_id)
    ratio = body.line_y_ratio if body else 0.5
    try:
        job_id = create_job(video_id, ratio)
    except ProcessingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProcessResponse(job_id=job_id, video_id=video_id)


@router.get("/{video_id}/status", response_model=JobStatus)
def job_status(video_id: str) -> JobStatus:
    _video_or_404(video_id)
    status = latest_job(video_id)
    if status is None:
        return JobStatus(status="uploaded")
    return status


@router.get("/{video_id}/results", response_model=VideoResults)
def video_results(video_id: str) -> VideoResults:
    path = _video_or_404(video_id)
    try:
        fps = VideoInspectionService().inspect(path).fps
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    results = get_results(video_id, fps)
    if results is None:
        raise HTTPException(status_code=404, detail="No results yet.")
    return results


@router.get("/{video_id}/output")
def output_video(video_id: str) -> FileResponse:
    _video_or_404(video_id)
    path = get_settings().output_path / f"{video_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No processed output.")
    return FileResponse(path, media_type="video/mp4")


@router.get("/{video_id}/frame")
def video_frame(video_id: str, n: int = 0) -> Response:
    """Return frame n as JPEG (for counting-line configuration)."""
    path = _video_or_404(video_id)
    cap = cv2.VideoCapture(str(path))
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(n, 0))
        ok, frame = cap.read()
    finally:
        cap.release()
    if not ok:
        raise HTTPException(status_code=422, detail="Frame not readable.")
    ok, buf = cv2.imencode(".jpg", frame)
    if not ok:
        raise HTTPException(status_code=500, detail="Encoding failed.")
    return Response(content=buf.tobytes(), media_type="image/jpeg")


def _sse_format(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _live_stream_generator(video_id: str, line_y_ratio: float) -> str:
    """Background processing with live SSE updates."""
    settings = get_settings()
    input_path = _video_or_404(video_id)
    output_path = settings.output_path / f"{video_id}.mp4"

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

    q: Queue = Queue()
    done = threading.Event()
    error: list[str] = []

    def worker():
        try:
            def on_live(jpeg: bytes, stats, frame_num: int, total: int):
                payload = {
                    "frame": frame_num,
                    "total": total,
                    "progress": round(frame_num / total * 100) if total else 0,
                    "stats": {
                        "total": stats.total,
                        "by_type": stats.by_type,
                        "entering": stats.entering,
                        "exiting": stats.exiting,
                    },
                    "jpeg_b64": __import__("base64").b64encode(jpeg).decode(),
                }
                q.put(("frame", payload))

            def on_progress(done_frames: int, total_frames: int):
                q.put(("progress", {"done": done_frames, "total": total_frames}))

            processor.process_live(
                input_path, output_path, line,
                on_progress=on_progress,
                on_live=on_live,
                live_every=max(1, settings.frame_stride),  # match inference rate
            )
        except Exception as exc:
            error.append(str(exc))
            q.put(("error", {"detail": str(exc)}))
        finally:
            done.set()
            q.put(("done", {}))

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    # Stream SSE events
    while not done.is_set() or not q.empty():
        try:
            event, payload = q.get(timeout=0.5)
            yield _sse_format(event, payload)
        except Exception:
            if done.is_set() and q.empty():
                break
            yield ": keepalive\n\n"
    t.join(timeout=1.0)


@router.get("/{video_id}/live")
def live_stream(video_id: str, line_y_ratio: float = 0.5):
    """Server-Sent Events: live annotated frames + stats during processing."""
    _video_or_404(video_id)

    return StreamingResponse(
        _live_stream_generator(video_id, line_y_ratio),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
