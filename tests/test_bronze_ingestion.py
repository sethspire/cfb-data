import pytest
from unittest.mock import MagicMock

from ingestion.cfbd_ingest.services.bronze_ingestion import BronzeIngestion


class TestBronzeIngestion:
    @pytest.fixture
    def client(self):
        return MagicMock()

    @pytest.fixture
    def writer(self):
        return MagicMock()

    @pytest.fixture
    def ingestion(self, client, writer):
        return BronzeIngestion(client, writer)

    def test_ingest_conferences(self, ingestion, client, writer):
        client.get_conferences.return_value = [{"id": 1}]
        ingestion.ingest_conferences()
        client.get_conferences.assert_called_once()
        writer.write_entity.assert_called_once_with("conferences", [{"id": 1}], params=None)

    def test_ingest_venues(self, ingestion, client, writer):
        client.get_venues.return_value = [{"id": 1}]
        ingestion.ingest_venues()
        client.get_venues.assert_called_once()
        writer.write_entity.assert_called_once_with("venues", [{"id": 1}], params=None)

    def test_ingest_teams(self, ingestion, client, writer):
        client.get_teams.return_value = [{"id": 1}]
        ingestion.ingest_teams(2024)
        client.get_teams.assert_called_once_with(season=2024)
        writer.write_entity.assert_called_once_with("teams", [{"id": 1}], params={"year": 2024})

    def test_ingest_games(self, ingestion, client, writer):
        client.get_games.return_value = [{"id": 1}]
        ingestion.ingest_games(2024, week=1)
        client.get_games.assert_called_once_with(year=2024, week=1)
        writer.write_entity.assert_called_once_with(
            "games", [{"id": 1}], params={"year": 2024, "week": 1}
        )

    def test_ingest_games_no_kwargs(self, ingestion, client, writer):
        client.get_games.return_value = []
        ingestion.ingest_games(2024)
        client.get_games.assert_called_once_with(year=2024)
        writer.write_entity.assert_called_once_with(
            "games", [], params={"year": 2024}
        )

    def test_ingest_drives(self, ingestion, client, writer):
        client.get_drives.return_value = [{"id": 1}]
        ingestion.ingest_drives(2024, season_type="both")
        client.get_drives.assert_called_once_with(year=2024, season_type="both")
        writer.write_entity.assert_called_once_with(
            "drives", [{"id": 1}], params={"year": 2024, "season_type": "both"}
        )

    def test_ingest_plays(self, ingestion, client, writer):
        client.get_plays.return_value = [{"id": 1}]
        ingestion.ingest_plays(2024)
        client.get_plays.assert_called_once_with(year=2024)
        writer.write_entity.assert_called_once_with("plays", [{"id": 1}], params={"year": 2024})
