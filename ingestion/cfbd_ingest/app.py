import logging
import os
from datetime import datetime, timezone

from chalice import Chalice

from .services.bronze_ingestion import BronzeIngestion
from .services.cfbd_client import CFBDClient
from .services.dates import current_season
from .services.s3_writer import BronzeWriter

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

app = Chalice(app_name="cfbd_ingest")


def _build_ingestion() -> BronzeIngestion:
    api_key = os.environ["CFBD_API_KEY"]
    bucket = os.environ["BRONZE_BUCKET"]
    client = CFBDClient(api_key)
    writer = BronzeWriter(bucket=bucket)
    return BronzeIngestion(client, writer)


@app.schedule("cron(0 9 ? 8-12,1 SUN *)")
def weekly_ingest(event):
    season = current_season()
    month = datetime.now(timezone.utc).month

    if 2 <= month <= 7:
        log.info("Skipping weekly ingest — off-season (month %d)", month)
        return

    log.info("Weekly ingest started for season %d", season)

    ingestion = _build_ingestion()
    ingestion.ingest_conferences()
    ingestion.ingest_venues()
    ingestion.ingest_teams(season)
    ingestion.ingest_games(season)
    ingestion.ingest_drives(season)
    ingestion.ingest_plays(season)

    log.info("Weekly ingest complete for season %d", season)


@app.route("/ingest/{entity}", methods=["POST"])
def ingest_entity(entity: str):
    secret = os.environ.get("INGESTION_API_SECRET")
    if secret:
        provided = app.current_request.headers.get("x-api-key", "")
        if provided != secret:
            log.warning("Rejected unauthorized request (403)")
            return {"error": "Forbidden"}, 403

    qp = app.current_request.query_params or {}
    season = int(qp["season"]) if "season" in qp else current_season()
    extra = {}
    if "week" in qp:
        extra["week"] = int(qp["week"])
    if "season_type" in qp:
        extra["season_type"] = qp["season_type"]

    log.info("Manual ingest: entity=%s, season=%s%s",
             entity, season, f", {extra}" if extra else "")

    ingestion = _build_ingestion()

    entity = entity.lower()
    if entity[-1] != "s":
        entity += "s"

    handlers = {
        "conferences": lambda: ingestion.ingest_conferences(),
        "venues": lambda: ingestion.ingest_venues(),
        "teams": lambda: ingestion.ingest_teams(season),
        "games": lambda: ingestion.ingest_games(season, **extra),
        "drives": lambda: ingestion.ingest_drives(season, **extra),
        "plays": lambda: ingestion.ingest_plays(season, **extra),
    }

    handler = handlers.get(entity)
    if handler is None:
        log.warning("Unknown entity requested: %s (400)", entity)
        return {"error": f"Unknown entity: {entity}"}, 400

    key = handler()
    return {"entity": entity, "key": key, "season": season, **extra}
