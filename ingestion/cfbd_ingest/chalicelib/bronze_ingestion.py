import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BronzeIngestion:
    def __init__(self, client, writer):
        self.client = client
        self.writer = writer

    def _ingest(self, entity: str, data: list | dict, params: dict | None = None) -> str:
        count = len(data) if isinstance(data, list) else 1
        key = self.writer.write_entity(entity, data, params=params)
        log.info("Ingested %s (%d records) → %s", entity, count, key)
        return key

    def ingest_conferences(self) -> str:
        data = self.client.get_conferences()
        return self._ingest("conferences", data)

    def ingest_venues(self) -> str:
        data = self.client.get_venues()
        return self._ingest("venues", data)

    def ingest_teams(self, year: int) -> str:
        data = self.client.get_teams(season=year)
        return self._ingest("teams", data, params={"year": year})

    def ingest_games(self, year: int, **kwargs) -> str:
        data = self.client.get_games(year=year, **kwargs)
        params = {"year": year} | kwargs
        return self._ingest("games", data, params=params)

    def ingest_drives(self, year: int, **kwargs) -> str:
        data = self.client.get_drives(year=year, **kwargs)
        params = {"year": year} | kwargs
        return self._ingest("drives", data, params=params)

    def ingest_plays(self, year: int, **kwargs) -> str:
        data = self.client.get_plays(year=year, **kwargs)
        params = {"year": year} | kwargs
        return self._ingest("plays", data, params=params)
