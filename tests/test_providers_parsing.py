from datetime import date

import pytest

from custom_components.energyua_poweroff.providers import BaseProvider
from custom_components.energyua_poweroff.providers.energy_ua import EnergyUAProvider


class TestExtractDate:
    def test_simple_title(self):
        assert (
            BaseProvider._extract_date_from_title("7 БЕРЕЗНЯ", today=date(2026, 3, 6))
            == "2026-03-07"
        )

    def test_case_insensitive(self):
        assert (
            BaseProvider._extract_date_from_title("7 березня", today=date(2026, 3, 6))
            == "2026-03-07"
        )

    def test_no_date(self):
        assert BaseProvider._extract_date_from_title("Графік") is None

    def test_december_schedule_with_january_date(self):
        assert (
            BaseProvider._extract_date_from_title("1 СІЧНЯ", today=date(2026, 12, 31))
            == "2027-01-01"
        )

    def test_january_schedule_with_december_date(self):
        assert (
            BaseProvider._extract_date_from_title("31 ГРУДНЯ", today=date(2027, 1, 1))
            == "2026-12-31"
        )

    def test_impossible_date(self):
        assert (
            BaseProvider._extract_date_from_title("31 ЛЮТОГО", today=date(2026, 2, 1))
            is None
        )

    def test_leap_day(self):
        assert (
            BaseProvider._extract_date_from_title("29 ЛЮТОГО", today=date(2028, 2, 28))
            == "2028-02-29"
        )


class TestExtractHours:
    def test_single_range(self):
        assert BaseProvider._extract_hours_for_group("1.2: 09:00 – 14:00", "1.2") == [
            "09:00-14:00"
        ]

    def test_multiple_ranges(self):
        content = "3.1: 00:00 – 00:30, 07:30 – 11:00"
        assert BaseProvider._extract_hours_for_group(content, "3.1") == [
            "00:00-00:30",
            "07:30-11:00",
        ]

    def test_does_not_match_inside_longer_group(self):
        content = "11.2: 01:00 – 03:00\n21.2: 04:00 – 06:00\n1.2: 09:00 – 14:00"
        assert BaseProvider._extract_hours_for_group(content, "1.2") == ["09:00-14:00"]

    def test_only_longer_group_present(self):
        assert BaseProvider._extract_hours_for_group("11.2: 01:00 – 03:00", "1.2") == []

    def test_all_occurrences_are_collected_without_duplicates(self):
        content = "1.2: 09:00 – 12:00\n...\n1.2: 09:00 – 12:00, 18:00 – 20:00"
        assert BaseProvider._extract_hours_for_group(content, "1.2") == [
            "09:00-12:00",
            "18:00-20:00",
        ]

    def test_hyphen_is_normalised(self):
        assert BaseProvider._extract_hours_for_group("1.1: 9:00 - 12:00", "1.1") == [
            "9:00-12:00"
        ]

    def test_missing_group(self):
        assert BaseProvider._extract_hours_for_group("2.1: 09:00 – 14:00", "1.2") == []


class TestEnergyUADates:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("07.03.2026", "2026-03-07"),
            ("7/3/2026", "2026-03-07"),
            ("31.02.2026", None),
            ("not a date", None),
        ],
    )
    def test_explicit_year(self, raw, expected):
        assert EnergyUAProvider._normalise_date(raw) == expected

    def test_without_year_uses_current_or_adjacent_year(self):
        result = EnergyUAProvider._normalise_date("15.06")
        assert result is not None
        assert result[5:] == "06-15"
