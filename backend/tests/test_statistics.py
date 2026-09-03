"""Tests for statistics aggregation."""
from app.cv.counting import CrossingEvent, Direction
from app.cv.statistics import StatsCollector


def test_stats_aggregation() -> None:
    collector = StatsCollector()
    collector.record(
        CrossingEvent(1, Direction.ENTERING), "car", 1.0
    )
    collector.record(
        CrossingEvent(2, Direction.EXITING), "truck", 2.5
    )
    collector.record(
        CrossingEvent(3, Direction.ENTERING), "motorcycle", 3.0
    )

    stats = collector.stats
    assert stats.total == 3
    assert stats.by_type == {"car": 1, "motorcycle": 1, "bus": 0, "truck": 1}
    assert stats.entering == 2
    assert stats.exiting == 1
    assert [(p.t, p.count) for p in stats.timeline] == [
        (1.0, 1), (2.5, 2), (3.0, 3)
    ]


def test_unknown_type_falls_back_to_car() -> None:
    collector = StatsCollector()
    collector.record(CrossingEvent(1, Direction.ENTERING), "unknown", 0.0)
    assert collector.stats.by_type["car"] == 1
