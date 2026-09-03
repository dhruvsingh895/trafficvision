# TrafficVision

Vehicle detection, tracking, counting and analytics for traffic videos.

Upload a traffic video, configure a counting line, and get vehicle counts
by type and direction, an annotated output video, and analytics charts.

## Architecture

```
React + TypeScript frontend
        │  HTTP /api
        ▼
FastAPI backend
        │
Application services (storage, inspection, processing jobs, queries)
        │
Computer Vision layer (app/cv)
   ├─ tracker.py    ByteTrack tracking (stable IDs)
   ├─ counting.py   line-crossing counting + direction (pure logic)
   ├─ statistics.py aggregation (types, entering/exiting, timeline)
   ├─ annotator.py  frame drawing
   └─ processor.py  read → track → count → annotate → write
        │
Infrastructure (SQLite via SQLAlchemy, file storage, config)
```

Constraints: every source file stays below 200 lines; one responsibility
per file. Vehicle counts come only from *track-ID line crossings* — never
from raw detections, so a vehicle visible in 100 frames counts once.

## Quick Start (local)

Backend:

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://localhost:8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Docker:

```bash
docker compose up                # frontend: http://localhost:8080
```

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/videos` | Upload video (.mp4/.avi/.mov/.mkv) |
| GET | `/api/videos/{id}/info` | Width/height/FPS/frames/duration |
| POST | `/api/videos/{id}/process` | Start processing (optional `line_y_ratio`) |
| GET | `/api/videos/{id}/status` | Real job progress (never faked) |
| GET | `/api/videos/{id}/results` | Counts, types, directions, timeline |
| GET | `/api/videos/{id}/output` | Annotated video (MP4) |
| GET | `/api/videos/{id}/frame?n=0` | JPEG frame (line configuration) |

## Counting Algorithm

```
Detection (YOLO, vehicle classes only)
  → ByteTrack track ID
  → track-position history
  → side-of-line transition detection (cross product)
  → count once per track ID ("entering"/"exiting" by crossing direction)
```

## Configuration

Environment variables (prefix `TV_`), see `.env.example`.
Notable: `TV_MODEL_PATH`, `TV_CONFIDENCE`, `TV_DEVICE` (empty = auto,
CUDA if available, otherwise CPU), `TV_DATABASE_URL`.

Performance tuning (CPU inference):
- `TV_IMGSZ` (default 640): YOLO inference resolution. Lower = faster, less accurate on small vehicles. Try 480 for ~1.4× speedup.
- `TV_FRAME_STRIDE` (default 1): Run detection every N frames. Stride 2 ≈ 2× faster with minimal accuracy loss on highway traffic.
- `TV_INFERENCE_BACKEND` (default `auto`): `torch` | `openvino` | `auto`. On Intel CPUs, `openvino` can be 2–3× faster; on AMD it may be slower (test with the benchmark script).
- `TV_USE_MOG_ROI` (default `false`): Enable motion-ROI filtering. Runs YOLO only on moving regions. **Only helps for sparse traffic / static cameras with large static areas.** On busy highways it adds overhead.
- `TV_MOG_HISTORY` (default 200), `TV_MOG_VAR_THRESHOLD` (default 16.0), `TV_MOG_DETECT_SHADOWS` (default `true`), `TV_ROI_PADDING` (default 20), `TV_MAX_ROI_AREA_RATIO` (default 0.5): MOG2 tuning.

Accuracy tuning (per-class confidence):
- `TV_CONF_CAR` (default 0.25)
- `TV_CONF_MOTORCYCLE` (default 0.15) — lower = more sensitive for small/fast vehicles
- `TV_CONF_BUS` (default 0.20)
- `TV_CONF_TRUCK` (default 0.20)

Recommended balanced config (good accuracy + ~25 FPS on Ryzen 7 5800H):
```bash
TV_MODEL_PATH=yolov8s.pt
TV_IMGSZ=640
TV_FRAME_STRIDE=2
TV_CONF_CAR=0.25
TV_CONF_MOTORCYCLE=0.15
TV_CONF_BUS=0.20
TV_CONF_TRUCK=0.20
```

## Testing

```bash
cd backend && pytest -q    # counting, direction, dedup, stats, API flow
```

The suite covers: line geometry, crossing-once semantics (a vehicle that
crosses then keeps moving is counted exactly once), direction detection,
statistics aggregation, upload validation, job lifecycle, and API errors.
YOLO is mocked in API tests so the suite runs fast without a model download.

## Performance

Processing FPS, total frames and wall-clock processing time are measured
per job and returned in `/results`. Absolute numbers depend on hardware
and video length — run a local video to obtain real measurements.

## Limitations

- Counting accuracy depends on YOLO/ByteTrack quality (occlusions,
  camera shake and night footage degrade IDs).
- Processing is single-threaded per job (one job per video at a time is
  not enforced yet).
- Browser H.264 playback of `mp4v` output may vary by browser.

## Future Improvements

- GPU-enabled Docker image, job queue (Celery/Redis) for scale-out,
  polygon counting zones, per-class confidence thresholds, auth.

## Deployment

### GitHub Actions CI/CD
Push to `main` runs:
- Backend: ruff + pytest
- Frontend: tsc + eslint + build
- Docker image builds (on main only)

### Production (Docker Compose)
```bash
docker compose -f docker-compose.prod.yml up -d
# Frontend: http://localhost:8080
```

Environment variables for production (set in `.env` or Docker env):
```bash
TV_MODEL_PATH=yolov8s.pt
TV_IMGSZ=640
TV_FRAME_STRIDE=2
TV_CONF_MOTORCYCLE=0.15
TV_CONF_BUS=0.20
TV_CONF_TRUCK=0.20
TV_DATABASE_URL=sqlite:////data/trafficvision.db
```

### Manual GitHub Deploy
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/trafficvision.git
git push -u origin main
```
Then enable GitHub Actions in repo settings.
