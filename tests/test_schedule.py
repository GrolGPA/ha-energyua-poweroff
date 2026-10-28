from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from custom_components.energyua_poweroff.schedule import merge_ranges, parse_time_range

TZ = ZoneInfo("Europe/Kyiv")


def dt(day, hour, minute=0):
    return datetime(2026, 3, day, hour, minute, tzinfo=TZ)


class TestParseTimeRange:
    def test_regular_range(self):
        assert parse_time_range("2026-03-07", "09:00-14:00", TZ) == (
            dt(7, 9),
            dt(7, 14),
        )

    def test_single_digit_hour(self):
        assert parse_time_range("2026-03-07", "9:00-14:00", TZ)[0] == dt(7, 9)

    def test_end_at_24_00_is_next_midnight(self):
        assert parse_time_range("2026-03-07", "22:00-24:00", TZ) == (
            dt(7, 22),
            dt(8, 0),
        )

    def test_crossing_midnight(self):
        assert parse_time_range("2026-03-07", "22:00-02:00", TZ) == (
            dt(7, 22),
            dt(8, 2),
        )

    def test_start_at_midnight(self):
        assert parse_time_range("2026-03-07", "00:00-00:30", TZ) == (
            dt(7, 0),
            dt(7, 0, 30),
        )

    @pytest.mark.parametrize(
        "hours",
        ["", "09:00", "24:00-02:00", "09:00-24:30", "09:00-25:00", "09:60-10:00", "a-b"],
    )
    def test_invalid_hours(self, hours):
        with pytest.raises(ValueError):
            parse_time_range("2026-03-07", hours, TZ)

    def test_invalid_day(self):
        with pytest.raises(ValueError):
            parse_time_range("2026-02-31", "09:00-10:00", TZ)


class TestMergeRanges:
    def test_sorts_ranges(self):
        a, b = (dt(7, 1), dt(7, 2)), (dt(7, 5), dt(7, 6))
        assert merge_ranges([b, a]) == [a, b]

    def test_merges_touching_ranges_across_midnight(self):
        first = parse_time_range("2026-03-07", "22:00-24:00", TZ)
        second = parse_time_range("2026-03-08", "00:00-02:00", TZ)
        assert merge_ranges([second, first]) == [(dt(7, 22), dt(8, 2))]

    def test_merges_overlapping_ranges(self):
        assert merge_ranges(
            [(dt(7, 1), dt(7, 5)), (dt(7, 3), dt(7, 4)), (dt(7, 4), dt(7, 8))]
        ) == [(dt(7, 1), dt(7, 8))]

    def test_keeps_separate_ranges(self):
        ranges = [(dt(7, 1), dt(7, 2)), (dt(7, 3), dt(7, 4))]
        assert merge_ranges(ranges) == ranges

    def test_empty(self):
        assert merge_ranges([]) == []
