import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from ingestion.cfbd_ingest.chalicelib import dates


@pytest.fixture
def mock_datetime():
    with patch("ingestion.cfbd_ingest.chalicelib.dates.datetime") as mock_datetime:
        yield mock_datetime

def test_utc_now_iso(mock_datetime):
    mock_datetime.now.return_value = datetime(year=2023, month=6, day=13, hour=2, minute=34, second=5, tzinfo=timezone.utc)
    assert dates.utc_now_iso() == "2023-06-13T02-34-05Z"

def test_utc_today(mock_datetime):
    mock_datetime.now.return_value = datetime(year=2023, month=6, day=13, tzinfo=timezone.utc)
    assert dates.utc_today() == "2023-06-13"

def test_current_season(mock_datetime):
    mock_datetime.now.return_value = datetime(year=2024, month=1, day=1)
    assert dates.current_season() == 2023

    mock_datetime.now.return_value = datetime(year=2024, month=2, day=1)
    assert dates.current_season() == 2024

def test_current_season_uses_utc():
    with patch("ingestion.cfbd_ingest.chalicelib.dates.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2025, 6, 1, tzinfo=timezone.utc)
        result = dates.current_season()
        mock_dt.now.assert_called_once_with(timezone.utc)
        assert result == 2025
