import pytest

from leth.display import format_journal_timestamp


@pytest.mark.parametrize("value, expected", [
    ("2026-10-20T13:44:37.538080+00:00", "20 Oct 2026 · 7:14 PM"),
    ("2026-10-20T19:14:37.538080+05:30", "20 Oct 2026 · 7:14 PM"),
    ("2026-10-20T09:44:37-04:00", "20 Oct 2026 · 7:14 PM"),
    ("2026-10-20T20:00:00+00:00", "21 Oct 2026 · 1:30 AM"),
    ("2026-10-20T18:30:00+00:00", "21 Oct 2026 · 12:00 AM"),
    ("2026-10-20T06:30:00+00:00", "20 Oct 2026 · 12:00 PM"),
])
def test_format_journal_timestamp(value, expected):
    assert format_journal_timestamp(value) == expected
