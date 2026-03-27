from datetime import datetime, timezone, timedelta

from scripts.fetch_and_generate import compute_target_dates


JST = timezone(timedelta(hours=9))


def test_compute_target_dates_with_date_only():
    today = datetime(2026, 3, 27, 0, 0, tzinfo=JST)
    result = compute_target_dates(today=today, backfill_days=5, target_date_str="2026-03-23")
    assert [d.strftime("%Y-%m-%d") for d in result] == ["2026-03-23"]


def test_compute_target_dates_with_backfill_days():
    today = datetime(2026, 3, 27, 0, 0, tzinfo=JST)
    result = compute_target_dates(today=today, backfill_days=2, target_date_str=None)
    assert [d.strftime("%Y-%m-%d") for d in result] == [
        "2026-03-25",
        "2026-03-26",
        "2026-03-27",
    ]
