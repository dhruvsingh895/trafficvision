"""Detection data structures shared by CV modules."""
from dataclasses import dataclass

# COCO class IDs for the vehicles we care about
VEHICLE_CLASSES: dict[int, str] = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


@dataclass(slots=True)
class Detection:
    """A single vehicle detection in one frame."""

    x1: int
    y1: int
    x2: int
    y2: int
    class_id: int
    label: str
    confidence: float

    @property
    def center(self) -> tuple[float, float]:
        """Bounding-box center point."""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
