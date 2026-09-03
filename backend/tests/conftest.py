"""Shared pytest fixtures."""
from pathlib import Path

import cv2
import numpy as np
import pytest


@pytest.fixture()
def sample_video(tmp_path: Path) -> Path:
    """Create a small, valid test video file."""
    path = tmp_path / "traffic.mp4"
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10,
        (64, 48),
    )
    for _ in range(5):
        writer.write(np.zeros((48, 64, 3), dtype=np.uint8))
    writer.release()
    return path
