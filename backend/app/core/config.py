"""Application configuration management."""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="TV_", extra="ignore"
    )

    app_name: str = "TrafficVision"
    debug: bool = False

    # Directories (relative to project root by default)
    input_dir: str = "data/input"
    output_dir: str = "data/output"

    # Upload constraints
    max_upload_size_mb: int = 500
    allowed_extensions: str = ".mp4,.avi,.mov,.mkv"

    # Detection settings
    model_path: str = "yolov8n.pt"
    confidence: float = 0.25
    device: str = ""  # empty = auto (cuda if available, else cpu)

    # Performance tuning
    imgsz: int = Field(default=640, ge=32)  # YOLO inference size
    frame_stride: int = Field(default=1, ge=1)  # detect every Nth frame
    inference_backend: str = "auto"  # auto | torch | openvino

    # Per-class confidence (lower = more sensitive for rare/small classes)
    conf_car: float = Field(default=0.25, ge=0.0, le=1.0)
    conf_motorcycle: float = Field(default=0.15, ge=0.0, le=1.0)
    conf_bus: float = Field(default=0.20, ge=0.0, le=1.0)
    conf_truck: float = Field(default=0.20, ge=0.0, le=1.0)

    # Motion ROI (run YOLO only on moving regions — 2-3× speedup on static cameras)
    use_mog_roi: bool = False
    mog_history: int = 200
    mog_var_threshold: float = 16.0
    mog_detect_shadows: bool = True
    roi_padding: int = 20
    max_roi_area_ratio: float = 0.5  # fallback to full frame if ROIs cover >50%

    # Database
    database_url: str = "sqlite:///./trafficvision.db"

    @property
    def input_path(self) -> Path:
        path = Path(self.input_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def output_path(self) -> Path:
        path = Path(self.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",")}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
