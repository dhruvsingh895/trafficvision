"""Tests for line-crossing counting and direction detection."""
from app.cv.counting import CountingLine, Direction, VehicleCounter

LINE = CountingLine(0, 100, 200, 100)  # horizontal line at y=100


def test_vehicle_crosses_line_once() -> None:
    counter = VehicleCounter(LINE)
    assert counter.update(10, (50, 50)) is None  # above
    event = counter.update(10, (50, 150))  # crosses
    assert event is not None
    assert event.track_id == 10
    assert event.direction == Direction.EXITING


def test_vehicle_counted_only_once() -> None:
    counter = VehicleCounter(LINE)
    counter.update(10, (50, 50))
    assert counter.update(10, (50, 150)) is not None
    # continues moving below the line — no new crossing
    assert counter.update(10, (50, 180)) is None
    assert counter.update(10, (50, 200)) is None


def test_entering_direction() -> None:
    counter = VehicleCounter(LINE)
    counter.update(7, (50, 150))  # below
    event = counter.update(7, (50, 50))  # above
    assert event is not None
    assert event.direction == Direction.ENTERING


def test_multiple_vehicles_independent() -> None:
    counter = VehicleCounter(LINE)
    counter.update(1, (50, 50))
    counter.update(2, (60, 150))
    assert counter.update(1, (50, 150)) is not None
    assert counter.update(2, (60, 50)) is not None
    assert len(counter.counted_ids) == 2


def test_no_crossing_same_side() -> None:
    counter = VehicleCounter(LINE)
    counter.update(1, (50, 50))
    assert counter.update(1, (60, 55)) is None
    assert counter.update(1, (70, 40)) is None


def test_reset() -> None:
    counter = VehicleCounter(LINE)
    counter.update(1, (50, 50))
    counter.update(1, (50, 150))
    counter.reset()
    assert counter.counted_ids == set()
    counter.update(1, (50, 50))
    assert counter.update(1, (50, 150)) is not None
