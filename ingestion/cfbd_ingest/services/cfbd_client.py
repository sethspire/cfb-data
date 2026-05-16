import os
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from glom import glom, PathAccessError

from .dates import current_season


CFBD_API_KEY = os.getenv('CFBD_API_KEY')
CFBD_BASE_URL = "https://apinext.collegefootballdata.com"

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CFBDClient:
    BASE_URL = "https://apinext.collegefootballdata.com"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("CFBD API key is required")

        self.session = requests.Session()

        retries = Retry(
            total=5,
            backoff_factor=1,
            respect_retry_after_header=True,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )

        self.session.mount(
            "https://",
            HTTPAdapter(max_retries=retries)
        )

        self.session.headers.update({
            "Authorization": f"Bearer {api_key}"
        })

    def _get(self, endpoint: str, **params) -> dict | list[dict]:
        log.info(
            "CFBD request",
            extra={
                "endpoint": endpoint,
                "params": params
            }
        )

        r = self.session.get(
            f"{self.BASE_URL}/{endpoint}",
            params=params,
            timeout=30
        )

        r.raise_for_status()

        return r.json()

    # Specific Getters
    def get_conferences(self) -> list[dict]:
        """Fetches all conferences from CFBD API
    
        Returns:
            list[dict]: List of conferences
        """
        return self._get("conferences")

    def get_venues(self) -> list[dict]:
        """Fetches all venues from CFBD API
    
        Returns:
            list[dict]: List of venues
        """
        return self._get("venues")

    def get_teams(self, season:int=None) -> list[dict]:
        """Fetches all teams from CFBD API. Returns current season if no season is provided 
    
        Args:
            season (int): Season to fetch. Defaults to None which defers to current season.

        Returns:
            list[dict]: List of teams
        """
        params = { "year": season } if season is not None else {}

        raw_teams = self._get("teams", **params)

        # include season for later parsing out of seasonal changes
        for team in raw_teams:
            team["season"] = season if season is not None else current_season()

        return raw_teams

    def get_games(self, year:int, week:int|None=None, season_type:str|None=None, game_id:int|None=None) -> list[dict]:
        """Fetches games from CFBD API. Automatically fetches for all classifications. Can fetch single game if game_id is provided
        
        Args:
            year (int): year to fetch
            week (int | None): optional week to fetch, optional, returns all weeks if not provided
            season_type (str | None): optional season type (regular, postseason, both, allstar, spring_regular, spring_postseason), defaults to None which defers to "both"
            game_id (int | None): optional game_id to fetch; if provided, other params are ignored and returns single game
            
        Returns:
            list[dict]: List of games
        """
        params = {
            "year": year,
            "week": week,
            "seasonType": season_type
        }

        params = {k: v for k, v in params.items() if v is not None}

        # if game_id is provided, override other params to just fetch that game
        if game_id is not None:
            params = {"id": game_id}

        return self._get("games", **params)

    def get_advanced_box(self, game_id:int) -> dict:
        """Fetches advanced box score from CFBD API
    
        Args:
            game_id (int): Game ID to fetch

        Returns:
            dict: Advanced box score
        """
        params = {
            "gameId": game_id
        }

        raw_advanced_box = self._get("game/box/advanced", **params)

        # include game_id for later matching on game_id PK
        if glom(raw_advanced_box, "gameInfo", default=None) is not None:
            raw_advanced_box["gameInfo"]["game_id"] = game_id
        else:
            raw_advanced_box["gameInfo"] = {"game_id": game_id}

        return raw_advanced_box 

    def get_drives(self, year:int, week:int|None=None, season_type:str|None=None) -> list[dict]:
        """Fetches drives from CFBD API. Automatically fetches for all classifications
        
        Args:
            year (int): year to fetch
            week (int | None): week to fetch, optional, returns all weeks if not provided
            season_type (str | None): optional season type (regular, postseason, both, allstar, spring_regular, spring_postseason), defaults to None which defers to "both"
            
        Returns:
            list[dict]: List of drives
        """
        params = {
            "year": year,
            "week": week,
            "seasonType": season_type
        }

        params = {k: v for k, v in params.items() if v is not None}

        return self._get("drives", **params)

    def get_plays(self, year:int, week:int|None=None, season_type:str|None=None) -> list[dict]:
        """Fetches plays from CFBD API. Automatically fetches for all classifications
        
        Args:
            year (int): year to fetch
            week (int | None): week to fetch, optional, returns all weeks if not provided
            season_type (str | None): optional season type (regular, postseason, both, allstar, spring_regular, spring_postseason), defaults to None which defers to "both"
            
        Returns:
            list[dict]: List of plays
        """
        params = {
            "year": year,
            "week": week,
            "seasonType": season_type
        }

        params = {k: v for k, v in params.items() if v is not None}

        return self._get("plays", **params)

