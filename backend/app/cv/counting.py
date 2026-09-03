"""Line-crossing vehicle counting (pure logic, no CV dependencies)."""
from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    ENTERING = "entering"
    EXITING = "exiting"


@dataclass(frozen=True, slots=True)
class CountingLine:
    """A line segment used for counting crossings."""

    x1: float
    y1: float
    x2: float
    y2: float

    def side_of(self, px: float, py: float) -> int:
        """Which side of the line is the point on? (-1, 0, +1)."""
        cross = (self.x2 - self.x1) * (py - self.y1) - (
            self.y2 - self.y1
        ) * (px - self.x1)
        if abs(cross) < 1e-9:
            return 0
        return 1 if cross > 0 else -1


@dataclass(slots=True)
class CrossingEvent:
    track_id: int
    direction: Direction


class VehicleCounter:
    """Counts vehicles when their track crosses the counting line once."""

    def __init__(self, line: CountingLine) -> None:
        self._line = line
        self._last_side: dict[int, int] = {}
        self._counted: set[int] = set()

    @property
    def counted_ids(self) -> set[int]:
        return set(self._counted)

    def update(
        self, track_id: int, position: tuple[float, float]
    ) -> CrossingEvent | None:
        """Update position for a track; return event if it crosses now."""
        side = self._line.side_of(*position)
        if side == 0 or track_id in self._counted:
            return None

        prev_side = self._last_side.get(track_id)
        self._last_side[track_id] = side

        if prev_side is None or prev_side == side:
            return None

        self._counted.add(track_id)
        # In image coordinates y grows downward; crossing downward = EXITING.
        direction = Direction.EXITING if side > prev_side else Direction.ENTERING
        return CrossingEvent(track_id=track_id, direction=direction)

    def reset(self) -> None:
        self._last_side.clear()
        self._counted.clear()
