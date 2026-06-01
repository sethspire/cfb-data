#!/usr/bin/env python3
"""One-time backfill script for historical CFB data. Runs everything on the local machine.

Usage:
    uv run python scripts/backfill.py --local-dir ./bronze_data
    uv run python scripts/backfill.py --bucket my-bucket
"""

import argparse
import json
import logging
import os
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.cfbd_ingest.chalicelib.bronze_ingestion import BronzeIngestion
from ingestion.cfbd_ingest.chalicelib.cfbd_client import CFBDClient
from ingestion.cfbd_ingest.chalicelib.dates import current_season
from ingestion.cfbd_ingest.chalicelib.s3_writer import BronzeWriter


CHECKPOINT_FILE = Path(__file__).parent / ".backfill_checkpoint.json"


def load_checkpoint(path: Path) -> dict | None:
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_checkpoint(path: Path, year: int):
    path.write_text(json.dumps({"last_year": year}))


def main():
    parser = argparse.ArgumentParser(description="Backfill historical CFB data")
    parser.add_argument("--bucket", help="S3 bucket name")
    parser.add_argument("--local-dir", help="Local directory for bronze data")
    parser.add_argument("--start-year", type=int, default=1876, help="Start year (default: 1876)")
    parser.add_argument("--api-key", help="CFBD API key (default: CFBD_API_KEY env var)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between years to avoid rate limits (default: 0.5)")
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_FILE), help="Checkpoint file path")
    parser.add_argument("--log-dir", default="./logs", help="Directory for local log files (default: ./logs)")
    parser.add_argument("--no-upload-logs", action="store_true", help="Skip uploading log to S3 at the end")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("CFBD_API_KEY")
    if not api_key:
        sys.exit("Error: CFBD_API_KEY must be provided via --api-key or env var")

    client = CFBDClient(api_key)
    writer = BronzeWriter(bucket=args.bucket, local_root=args.local_dir)
    ingestion = BronzeIngestion(client, writer)

    end = current_season()
    start = args.start_year
    checkpoint_path = Path(args.checkpoint_path)

    log_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_file = Path(args.log_dir) / f"backfill_{log_ts}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file)),
        ],
    )
    log = logging.getLogger("backfill")

    checkpoint = load_checkpoint(checkpoint_path)
    if checkpoint:
        start = max(start, checkpoint["last_year"] + 1)
        log.info("Resuming from year %d (checkpoint: %d)", start, checkpoint["last_year"])
    else:
        log.info("Starting fresh from year %d with no checkpoint", start)

    log.info("Ingesting static entities (conferences, venues) ...")
    ingestion.ingest_conferences()
    ingestion.ingest_venues()

    log.info("Ingesting historical data from %d to %d (teams, games, drives, plays) ...", start, end)
    for year in range(start, end + 1):
        log.info("Year %d ...", year)
        ingestion.ingest_teams(year)
        ingestion.ingest_games(year, season_type="both")
        ingestion.ingest_drives(year, season_type="both")

        calendar = client.get_calendar(year)
        if calendar:
            for entry in calendar:
                ingestion.ingest_plays(year, week=entry["week"], season_type=entry.get("seasonType", "both"))
        else:
            log.info("  No calendar data — skipping plays for %d", year)

        save_checkpoint(checkpoint_path, year)
        if args.delay:
            time.sleep(args.delay)

    if checkpoint_path.exists():
        checkpoint_path.unlink()
    log.info("Backfill complete!")

    if args.bucket and not args.no_upload_logs:
        import boto3
        s3 = boto3.client("s3")
        ingest_date = f"{log_ts[:4]}-{log_ts[4:6]}-{log_ts[6:8]}"
        s3_key = f"logs/backfill/ingest_date={ingest_date}/backfill_{log_ts}.log"
        s3.upload_file(str(log_file), args.bucket, s3_key)
        log.info("Log uploaded to s3://%s/%s", args.bucket, s3_key)


if __name__ == "__main__":
    main()
