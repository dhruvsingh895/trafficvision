"""Measure per-frame detection cost for different performance settings.

Usage (from the backend directory, with the venv active):
    python ../scripts/benchmark.py ../data/input/49bb89e244c9.mp4 [frames]

The OpenVINO variant triggers a one-time model export on its first run.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import cv2  # noqa: E402

from app.cv.model_loader import resolve_device, resolve_model  # noqa: E402
from app.cv.motion_roi import MotionROIExtractor  # noqa: E402
from app.cv.tracker import VehicleTracker  # noqa: E402

VARIANTS = [
    ("yolov8n 640 stride=1 (old baseline)", dict(model="yolov8n.pt", backend="torch", imgsz=640, stride=1, use_mog=False)),
    ("yolov8s 640 stride=2 (recommended)", dict(model="yolov8s.pt", backend="torch", imgsz=640, stride=2, use_mog=False)),
    ("yolov8s 640 stride=2 + MOG ROI", dict(model="yolov8s.pt", backend="torch", imgsz=640, stride=2, use_mog=True)),
    ("yolov8n 640 stride=2 + MOG ROI", dict(model="yolov8n.pt", backend="torch", imgsz=640, stride=2, use_mog=True)),
    ("yolov8n 480 stride=2 + MOG ROI", dict(model="yolov8n.pt", backend="torch", imgsz=480, stride=2, use_mog=True)),
]


def run(video: Path, tracker: VehicleTracker, frames: int, stride: int, mog_extractor=None) -> None:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {video}")
    done = 0
    try:
        while done < frames:
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            done += 1
            if (done - 1) % stride == 0:
                if mog_extractor:
                    rois = mog_extractor.update(frame)
                    if len(rois) == 1 and rois[0].x1 == 0 and rois[0].y1 == 0:
                        tracker.track(frame)
                    else:
                        tracker.track_rois(frame, rois)
                else:
                    tracker.track(frame)
    finally:
        cap.release()


def measure(video: Path, frames: int, model: str, backend: str, imgsz: int, stride: int, use_mog: bool):
    device = resolve_device(None)
    path = resolve_model(model, device, backend)
    tracker = VehicleTracker(model_path=path, device=device, imgsz=imgsz)
    mog_extractor = MotionROIExtractor() if use_mog else None
    run(video, tracker, min(20, frames), stride, mog_extractor)  # warmup
    start = time.perf_counter()
    run(video, tracker, frames, stride, mog_extractor)
    elapsed = time.perf_counter() - start
    return frames / elapsed, elapsed / frames * 1000


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: benchmark.py <video> [frames]")
    video = Path(sys.argv[1])
    frames = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    print(f"Video: {video} | {frames} frames per variant (detection only)\n")
    print(f"{'variant':<30} {'ms/frame':>9} {'FPS':>7}")
    for name, cfg in VARIANTS:
        fps, ms = measure(video, frames, **cfg)
        print(f"{name:<30} {ms:>9.1f} {fps:>7.1f}")


if __name__ == "__main__":
    main()
