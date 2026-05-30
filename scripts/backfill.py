#!/usr/bin/env python3
"""One-time backfill script for historical CFB data.

Usage:
    uv run python scripts/backfill.py --local-dir ./bronze_data
    uv run python scripts/backfill.py --bucket my-bucket
"""

import argparse
import json
import os
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.cfbd_ingest.services.bronze_ingestion import BronzeIngestion
from ingestion.cfbd_ingest.services.cfbd_client import CFBDClient
from ingestion.cfbd_ingest.services.dates import current_season
from ingestion.cfbd_ingest.services.s3_writer import BronzeWriter


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

    checkpoint = load_checkpoint(checkpoint_path)
    if checkpoint:
        start = max(start, checkpoint["last_year"] + 1)
        print(f"Resuming from year {start} (checkpoint: {checkpoint['last_year']})")
    else:
        print(f"Starting fresh from year {start} with no checkpoint")

    print("Ingesting static entities (conferences, venues) ...")
    ingestion.ingest_conferences()
    ingestion.ingest_venues()

    print(f"Ingesting historical data from {start} to {end} (teams, games, drives, plays) ...")
    for year in range(start, end + 1):
        print(f"Year {year} ...")
        ingestion.ingest_teams(year)
        ingestion.ingest_games(year, season_type="both")
        ingestion.ingest_drives(year, season_type="both")
        ingestion.ingest_plays(year, season_type="both")
        save_checkpoint(checkpoint_path, year)
        if args.delay:
            time.sleep(args.delay)

    if checkpoint_path.exists():
        checkpoint_path.unlink()
    print("Backfill complete!")


if __name__ == "__main__":
    main()
