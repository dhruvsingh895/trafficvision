"""Aggregates crossing events into traffic statistics."""
from dataclasses import dataclass, field

from app.cv.counting import CrossingEvent, Direction


@dataclass(slots=True)
class TimelinePoint:
    t: float  # seconds into the video
    count: int  # cumulative total vehicles


@dataclass(slots=True)
class TrafficStats:
    total: int = 0
    by_type: dict[str, int] = field(
        default_factory=lambda: {
            "car": 0, "motorcycle": 0, "bus": 0, "truck": 0
        }
    )
    entering: int = 0
    exiting: int = 0
    timeline: list[TimelinePoint] = field(default_factory=list)


class StatsCollector:
    """Collects per-crossing statistics; used by the processor only."""

    def __init__(self) -> None:
        self.stats = TrafficStats()

    def record(
        self, event: CrossingEvent, vehicle_type: str, timestamp: float
    ) -> None:
        s = self.stats
        s.total += 1
        vehicle_type = vehicle_type if vehicle_type in s.by_type else "car"
        s.by_type[vehicle_type] += 1
        if event.direction is Direction.ENTERING:
            s.entering += 1
        else:
            s.exiting += 1
        s.timeline.append(TimelinePoint(t=round(timestamp, 2), count=s.total))
