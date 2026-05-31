# ─────────────────────────────────────────────────────────────────────────────
import pytest
from unittest.mock import MagicMock, patch
from requests.exceptions import HTTPError
import responses

from ingestion.cfbd_ingest.chalicelib.cfbd_client import CFBDClient


API_KEY = "test-api-key"


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    return CFBDClient(API_KEY)

def make_mock_response(json_data=None, status_code=200, raise_for_status=None):
    """Helper to build a mock requests.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or []
    if raise_for_status: # sets whether .raise_for_status() should raise or do nothing
        mock_resp.raise_for_status.side_effect = raise_for_status
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp


# ── Constructor ──────────────────────────────────────────────────────────────
class TestInit:
    def test_raises_if_no_api_key(self):
        with pytest.raises(ValueError, match="CFBD API key is required"):
            CFBDClient("")

    def test_raises_if_api_key_is_none(self):
        with pytest.raises(ValueError, match="CFBD API key is required"):
            CFBDClient(None)

    def test_auth_header_set_correctly(self, client):
        assert client.session.headers["Authorization"] == f"Bearer {API_KEY}"

    def test_retry_adapter_mounted(self, client):
        # Confirm an adapter is mounted for https:// (not just the default)
        adapter = client.session.get_adapter("https://example.com")
        assert adapter is not None
        assert adapter.max_retries.total == 5
        assert adapter.max_retries.backoff_factor == 1
        assert 429 in adapter.max_retries.status_forcelist


# ── _get ─────────────────────────────────────────────────────────────────────
class TestGet:
    def test_calls_correct_url(self, client):
        mock_resp = make_mock_response([{"id": 1}])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client._get("conferences")

        mock_get.assert_called_once()
        url_called = mock_get.call_args[0][0]
        assert url_called == f"{CFBDClient.BASE_URL}/conferences"

    def test_passes_params(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client._get("games", year=2024, week=1)

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"year": 2024, "week": 1}

    def test_returns_parsed_json(self, client):
        expected = [{"id": 1, "name": "SEC"}]
        mock_resp = make_mock_response(expected)

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client._get("conferences")

        assert result == expected

    def test_raises_on_http_error(self, client):
        mock_resp = make_mock_response(
            status_code=429,
            raise_for_status=HTTPError("429 Too Many Requests")
        )

        with patch.object(client.session, "get", return_value=mock_resp):
            with pytest.raises(HTTPError):
                client._get("conferences")

    def test_calls_raise_for_status(self, client):
        """Ensures raise_for_status is always called, not just on known error codes."""
        mock_resp = make_mock_response()

        with patch.object(client.session, "get", return_value=mock_resp):
            client._get("conferences")

        mock_resp.raise_for_status.assert_called_once()

    def test_timeout_is_set(self, client):
        mock_resp = make_mock_response()

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client._get("conferences")

        _, kwargs = mock_get.call_args
        assert kwargs["timeout"] == 30


# ── get_conferences ──────────────────────────────────────────────────────────
class TestGetConferences:
    def test_returns_parsed_json(self, client):
        expected = [{"id": 1, "name": "SEC"}]
        mock_resp = make_mock_response(expected)

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_conferences()

        assert result == expected

    def test_calls_correct_endpoint(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_conferences()

        url_called = mock_get.call_args[0][0]
        assert url_called == f"{CFBDClient.BASE_URL}/conferences"
    
    def test_params_is_empty(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_conferences()

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {}


# ── get_venues ───────────────────────────────────────────────────────────────
class TestGetVenues:
    def test_returns_parsed_json(self, client):
        expected = [{"id": 1, "name": "SEC"}]
        mock_resp = make_mock_response(expected)

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_venues()

        assert result == expected
    
    def test_calls_correct_endpoint(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_venues()

        url_called = mock_get.call_args[0][0]
        assert url_called == f"{CFBDClient.BASE_URL}/venues"
    
    def test_params_is_empty(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_venues()

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {}


# ── get_teams ────────────────────────────────────────────────────────────────
class TestGetTeams:
    def test_passes_year_when_season_provided(self, client):
        mock_resp = make_mock_response([{"id": 1}])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_teams(season=2024)

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"year": 2024}

    def test_omits_year_when_no_season(self, client):
        mock_resp = make_mock_response([{"id": 1}])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_teams()

        _, kwargs = mock_get.call_args
        assert "year" not in kwargs["params"]

    def test_injects_season_into_each_team(self, client):
        mock_resp = make_mock_response([{"id": 1}, {"id": 2}])

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_teams(season=2024)

        assert all(team["season"] == 2024 for team in result)

    def test_injects_current_season_when_none(self, client):
        mock_resp = make_mock_response([{"id": 1}])

        with patch("ingestion.cfbd_ingest.chalicelib.cfbd_client.current_season", return_value=2024):
            with patch.object(client.session, "get", return_value=mock_resp):
                result = client.get_teams()

        print(result)
        assert result[0]["season"] == 2024

    def test_does_not_overwrite_existing_team_data(self, client):
        mock_resp = make_mock_response([{"id": 1, "school": "Alabama"}])

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_teams(season=2024)

        assert result[0]["school"] == "Alabama"

    def test_returns_empty_list_when_no_teams(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_teams(season=2024)

        assert result == []

    def test_calls_correct_endpoint(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_teams(season=2024)

        url_called = mock_get.call_args[0][0]
        assert url_called == f"{CFBDClient.BASE_URL}/teams"


# ── get_games ────────────────────────────────────────────────────────────────
class TestGetGames:
    def test_returns_parsed_json(self, client):
        expected = [{"id": 1, "name": "SEC"}]
        mock_resp = make_mock_response(expected)

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_games(2024)

        assert result == expected

    def test_calls_correct_endpoint(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_games(2023)

        url_called = mock_get.call_args[0][0]
        assert url_called == f"{CFBDClient.BASE_URL}/games"
    
    def test_passes_params(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_games(year=2024, week=1)

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"year": 2024, "week": 1, "seasonType": "both"}
    
    def test_game_id_overrides_all_other_params(self, client):
        mock_resp = make_mock_response([{"id": 1}])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_games(year=2024, week=1, season_type="regular", game_id=999)

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"id": 999}  # strictly equal — no extra keys


# ── get_drives ───────────────────────────────────────────────────────────────
class TestGetDrives:
    def test_returns_parsed_json(self, client):
        expected = [{"id": 1, "drive": "first"}]
        mock_resp = make_mock_response(expected)

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_drives(2024)

        assert result == expected

    def test_calls_correct_endpoint(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_drives(2024)

        url_called = mock_get.call_args[0][0]
        assert url_called == f"{CFBDClient.BASE_URL}/drives"

    def test_passes_params(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_drives(year=2024, week=1)

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"year": 2024, "week": 1, "seasonType": "both"}

    def test_omits_week_when_not_provided(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_drives(year=2024)

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"year": 2024, "seasonType": "both"}


# ── get_plays ────────────────────────────────────────────────────────────────
class TestGetPlays:
    def test_returns_parsed_json(self, client):
        expected = [{"id": 1, "play": "touchdown"}]
        mock_resp = make_mock_response(expected)

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_plays(2024)

        assert result == expected

    def test_calls_correct_endpoint(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_plays(2024)

        url_called = mock_get.call_args[0][0]
        assert url_called == f"{CFBDClient.BASE_URL}/plays"

    def test_passes_params(self, client):
        mock_resp = make_mock_response([])

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            client.get_plays(year=2024, week=1)

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"year": 2024, "week": 1, "seasonType": "both"}


# ── get_advanced_box ─────────────────────────────────────────────────────────
class TestGetAdvancedBox:
    def test_injects_game_id_into_game_info(self, client):
        expected = {"gameInfo": {"id": 401234, "homeTeam": "Alabama"}}
        mock_resp = make_mock_response(expected)

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_advanced_box(game_id=1)

        assert result["gameInfo"]["game_id"] == 1

    def test_creates_game_info_if_missing(self, client):
        expected = {"someOtherKey": "value"}
        mock_resp = make_mock_response(expected)

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.get_advanced_box(game_id=1)

        assert result["gameInfo"] == {"game_id": 1}




